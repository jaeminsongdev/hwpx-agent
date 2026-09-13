#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


MAX_INPUT_BYTES = 8_000_000
MAX_PIXELS = 4_000_000
MAX_JSON_BYTES = 256_000
FROZEN_PROFILE_SHA256 = (
    "701248eec6ef0b5fd1524a718d7b18dd2e2077009e74cdacb0fdba34c2a5ba0b"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_INPUT_BYTES:
                raise ValueError("input exceeds byte bound")
            digest.update(chunk)
    return digest.hexdigest()


def artifact_identity(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size <= 0 or size > MAX_INPUT_BYTES:
        raise ValueError("invalid artifact size")
    return {"bytes": size, "sha256": sha256_file(path)}


def _ppm_token(data: bytes, offset: int) -> tuple[bytes, int]:
    length = len(data)
    while offset < length:
        if data[offset] == 35:
            newline = data.find(b"\n", offset)
            if newline < 0:
                raise ValueError("unterminated PPM comment")
            offset = newline + 1
        elif data[offset] in b" \t\r\n":
            offset += 1
        else:
            break
    start = offset
    while offset < length and data[offset] not in b" \t\r\n#":
        offset += 1
    if start == offset:
        raise ValueError("missing PPM token")
    return data[start:offset], offset


def read_ppm(path: Path) -> tuple[int, int, bytes]:
    data = path.read_bytes()
    magic, offset = _ppm_token(data, 0)
    width_raw, offset = _ppm_token(data, offset)
    height_raw, offset = _ppm_token(data, offset)
    maximum_raw, offset = _ppm_token(data, offset)
    if magic != b"P6" or maximum_raw != b"255":
        raise ValueError("unsupported PPM encoding")
    width = int(width_raw)
    height = int(height_raw)
    if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
        raise ValueError("invalid PPM dimensions")
    if offset >= len(data) or data[offset] not in b" \t\r\n":
        raise ValueError("missing PPM pixel separator")
    if data[offset:offset + 2] == b"\r\n":
        offset += 2
    else:
        offset += 1
    pixels = data[offset:]
    if len(pixels) != width * height * 3:
        raise ValueError("invalid PPM pixel byte count")
    return width, height, pixels


def _bbox_update(
    bbox: list[int] | None,
    x: int,
    y: int,
) -> list[int]:
    if bbox is None:
        return [x, y, x + 1, y + 1]
    bbox[0] = min(bbox[0], x)
    bbox[1] = min(bbox[1], y)
    bbox[2] = max(bbox[2], x + 1)
    bbox[3] = max(bbox[3], y + 1)
    return bbox


def raster_metrics(
    native_ppm: Path,
    product_ppm: Path,
    *,
    ink_threshold: int,
    allowed_diff_box: list[int],
) -> dict[str, Any]:
    native_width, native_height, native = read_ppm(native_ppm)
    product_width, product_height, product = read_ppm(product_ppm)
    if (native_width, native_height) != (product_width, product_height):
        raise ValueError("render dimensions differ")
    if not 0 <= ink_threshold <= 255 or len(allowed_diff_box) != 4:
        raise ValueError("invalid raster profile")

    differing_pixels = 0
    outside_allowed = 0
    total_absolute_delta = 0
    maximum_delta = 0
    diff_bbox: list[int] | None = None
    native_ink_bbox: list[int] | None = None
    product_ink_bbox: list[int] | None = None
    native_ink_pixels = 0
    product_ink_pixels = 0
    x0, y0, x1, y1 = allowed_diff_box

    for pixel_index in range(native_width * native_height):
        offset = pixel_index * 3
        native_rgb = native[offset:offset + 3]
        product_rgb = product[offset:offset + 3]
        x = pixel_index % native_width
        y = pixel_index // native_width
        deltas = [abs(left - right) for left, right in zip(native_rgb, product_rgb)]
        total_absolute_delta += sum(deltas)
        maximum_delta = max(maximum_delta, *deltas)
        if any(deltas):
            differing_pixels += 1
            diff_bbox = _bbox_update(diff_bbox, x, y)
            if not (x0 <= x < x1 and y0 <= y < y1):
                outside_allowed += 1
        if min(native_rgb) < ink_threshold:
            native_ink_pixels += 1
            native_ink_bbox = _bbox_update(native_ink_bbox, x, y)
        if min(product_rgb) < ink_threshold:
            product_ink_pixels += 1
            product_ink_bbox = _bbox_update(product_ink_bbox, x, y)

    pixel_count = native_width * native_height
    return {
        "render_size": [native_width, native_height],
        "differing_pixels": differing_pixels,
        "differing_pixel_ratio": differing_pixels / pixel_count,
        "mean_absolute_channel_delta": total_absolute_delta / (pixel_count * 3),
        "maximum_channel_delta": maximum_delta,
        "diff_bbox": diff_bbox,
        "outside_allowed_diff_box_pixels": outside_allowed,
        "native_ink_bbox": native_ink_bbox,
        "product_ink_bbox": product_ink_bbox,
        "native_ink_pixels": native_ink_pixels,
        "product_ink_pixels": product_ink_pixels,
        "ink_pixel_delta": abs(native_ink_pixels - product_ink_pixels),
    }


def _run_tool(arguments: list[str], *, timeout: int = 30) -> str:
    completed = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise ValueError("external PDF tool failed")
    return completed.stdout


def pdf_identity(pdfinfo: Path, pdf: Path) -> dict[str, Any]:
    output = _run_tool([str(pdfinfo), str(pdf)])
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    required = ("Creator", "Producer", "Pages", "Page size", "Page rot", "Encrypted")
    if any(key not in fields for key in required):
        raise ValueError("incomplete pdfinfo output")
    return {
        "creator": fields["Creator"],
        "producer": fields["Producer"],
        "pages": int(fields["Pages"]),
        "page_size": fields["Page size"],
        "page_rotation": int(fields["Page rot"]),
        "encrypted": fields["Encrypted"],
    }


def render_first_page(pdftoppm: Path, pdf: Path, output_prefix: Path, dpi: int) -> Path:
    if not 72 <= dpi <= 600:
        raise ValueError("invalid render DPI")
    _run_tool(
        [
            str(pdftoppm),
            "-f", "1",
            "-l", "1",
            "-singlefile",
            "-r", str(dpi),
            str(pdf),
            str(output_prefix),
        ],
        timeout=60,
    )
    output = output_prefix.with_suffix(".ppm")
    if not output.is_file():
        raise ValueError("PDF render output missing")
    return output


def extract_words(pdf: Path) -> list[dict[str, Any]]:
    try:
        import pdfplumber  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise ValueError("pdfplumber is required for exact word geometry") from error
    with pdfplumber.open(pdf) as document:
        if len(document.pages) != 1:
            raise ValueError("expected one PDF page")
        words = document.pages[0].extract_words()
    return [
        {
            "text": word["text"],
            "bbox": [
                round(float(word["x0"]), 6),
                round(float(word["top"]), 6),
                round(float(word["x1"]), 6),
                round(float(word["bottom"]), 6),
            ],
        }
        for word in words
    ]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def chart_package_semantics(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("HWPX exceeds byte bound")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate HWPX archive path")
        section_names = sorted(
            name for name in names if re.fullmatch(r"Contents/section\d+\.xml", name)
        )
        chart_names = sorted(
            name for name in names if re.fullmatch(r"Chart/chart\d+\.xml", name)
        )
        if len(section_names) != 1 or len(chart_names) != 1:
            raise ValueError("unexpected HWPX chart cardinality")
        section = ET.fromstring(archive.read(section_names[0]))
        chart = ET.fromstring(archive.read(chart_names[0]))

    anchors = [node for node in section.iter() if _local_name(node.tag) == "chart"]
    if len(anchors) != 1:
        raise ValueError("unexpected chart anchor cardinality")
    anchor = anchors[0]
    children = {_local_name(node.tag): node for node in anchor}
    if not {"sz", "pos", "outMargin"}.issubset(children):
        raise ValueError("incomplete chart anchor")
    title_nodes = [node for node in chart.iter() if _local_name(node.tag) == "title"]
    explicit_title_text: list[str] = []
    for title in title_nodes:
        explicit_title_text.extend(
            (node.text or "").strip()
            for node in title.iter()
            if _local_name(node.tag) in {"t", "v"} and (node.text or "").strip()
        )
    root_attributes = dict(anchor.attrib)
    root_attributes.pop("id", None)
    root_attributes["chartIDRef"] = Path(root_attributes.get("chartIDRef", "")).name
    return {
        "table_count": sum(1 for node in section.iter() if _local_name(node.tag) == "tbl"),
        "cell_count": sum(1 for node in section.iter() if _local_name(node.tag) == "tc"),
        "chart_anchor_count": len(anchors),
        "chart_part_count": len(chart_names),
        "bar_3d_count": sum(
            1 for node in chart.iter() if _local_name(node.tag) == "bar3DChart"
        ),
        "bar_directions": [
            node.attrib.get("val")
            for node in chart.iter()
            if _local_name(node.tag) == "barDir"
        ],
        "series_count": sum(1 for node in chart.iter() if _local_name(node.tag) == "ser"),
        "ordered_cache_values": [
            (node.text or "").strip()
            for node in chart.iter()
            if _local_name(node.tag) == "v" and (node.text or "").strip()
        ],
        "explicit_title_text": explicit_title_text,
        "anchor": {
            "root": root_attributes,
            "size": dict(children["sz"].attrib),
            "position": dict(children["pos"].attrib),
            "margin": dict(children["outMargin"].attrib),
        },
    }


def _bbox_delta(left: list[float], right: list[float]) -> float:
    if len(left) != 4 or len(right) != 4:
        raise ValueError("bounding boxes require four coordinates")
    return max(abs(a - b) for a, b in zip(left, right))


def validate_observation(observation: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    native_pdf = observation.get("native_pdf_identity")
    product_pdf = observation.get("product_pdf_identity")
    expected_pdf = profile.get("pdf_identity")
    if native_pdf != expected_pdf or product_pdf != expected_pdf:
        errors.append("pdf_identity")

    native_words = observation.get("native_words")
    product_words = observation.get("product_words")
    expected_words = profile.get("expected_words")
    if not isinstance(native_words, list) or not isinstance(product_words, list):
        errors.append("word_geometry")
    elif [word.get("text") for word in native_words] != expected_words or [
        word.get("text") for word in product_words
    ] != expected_words:
        errors.append("word_text")
    else:
        expected_boxes = profile.get("expected_word_boxes")
        tolerance = profile.get("word_bbox_tolerance_points")
        if not isinstance(expected_boxes, list) or not isinstance(tolerance, (int, float)):
            errors.append("word_profile")
        else:
            try:
                deltas = [
                    _bbox_delta(native_words[index]["bbox"], expected_boxes[index])
                    for index in range(len(expected_words))
                ] + [
                    _bbox_delta(product_words[index]["bbox"], expected_boxes[index])
                    for index in range(len(expected_words))
                ] + [
                    _bbox_delta(native_words[index]["bbox"], product_words[index]["bbox"])
                    for index in range(len(expected_words))
                ]
                if max(deltas, default=0.0) > tolerance:
                    errors.append("word_bbox")
            except (IndexError, KeyError, TypeError, ValueError):
                errors.append("word_geometry")

    raster = observation.get("raster")
    if not isinstance(raster, dict):
        errors.append("raster_metrics")
    else:
        if raster.get("render_size") != profile.get("render_size"):
            errors.append("raster_dimensions")
        if raster.get("outside_allowed_diff_box_pixels") != 0:
            errors.append("raster_diff_region")
        try:
            if raster["differing_pixel_ratio"] > profile["maximum_differing_pixel_ratio"]:
                errors.append("raster_diff_ratio")
            if raster["mean_absolute_channel_delta"] > profile["maximum_mean_absolute_channel_delta"]:
                errors.append("raster_mean_delta")
            if raster["maximum_channel_delta"] > profile["maximum_channel_delta"]:
                errors.append("raster_max_delta")
            if (
                raster["native_ink_bbox"] != profile["expected_ink_bbox"]
                or raster["product_ink_bbox"] != profile["expected_ink_bbox"]
            ):
                errors.append("ink_bbox")
            if raster["ink_pixel_delta"] > profile["maximum_ink_pixel_delta"]:
                errors.append("ink_pixel_delta")
        except (KeyError, TypeError):
            errors.append("raster_metrics")

    native_semantics = observation.get("native_hwpx_semantics")
    product_semantics = observation.get("product_hwpx_semantics")
    expected_semantics = profile.get("hwpx_semantics")
    if native_semantics != expected_semantics or product_semantics != expected_semantics:
        errors.append("hwpx_semantics")
    return sorted(set(errors))


def observe(
    *,
    native_pdf: Path,
    product_pdf: Path,
    native_hwpx: Path,
    product_hwpx: Path,
    pdfinfo: Path,
    pdftoppm: Path,
    profile: dict[str, Any],
) -> dict[str, Any]:
    for path in (native_pdf, product_pdf, native_hwpx, product_hwpx, pdfinfo, pdftoppm):
        if not path.is_file():
            raise ValueError("required input is not a file")
    with tempfile.TemporaryDirectory(prefix="p06-table-chart-render-diff-") as directory:
        temporary = Path(directory)
        native_ppm = render_first_page(
            pdftoppm, native_pdf, temporary / "native", int(profile["render_dpi"])
        )
        product_ppm = render_first_page(
            pdftoppm, product_pdf, temporary / "product", int(profile["render_dpi"])
        )
        raster = raster_metrics(
            native_ppm,
            product_ppm,
            ink_threshold=int(profile["ink_threshold"]),
            allowed_diff_box=list(profile["allowed_default_title_diff_box"]),
        )
    return {
        "schema_version": "hwpx-agent.table-chart-render-diff-observation/v1",
        "artifacts": {
            "native_pdf": artifact_identity(native_pdf),
            "product_pdf": artifact_identity(product_pdf),
            "native_hwpx": artifact_identity(native_hwpx),
            "product_hwpx": artifact_identity(product_hwpx),
        },
        "native_pdf_identity": pdf_identity(pdfinfo, native_pdf),
        "product_pdf_identity": pdf_identity(pdfinfo, product_pdf),
        "native_words": extract_words(native_pdf),
        "product_words": extract_words(product_pdf),
        "raster": raster,
        "native_hwpx_semantics": chart_package_semantics(native_hwpx),
        "product_hwpx_semantics": chart_package_semantics(product_hwpx),
    }


def load_profile(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("profile exceeds byte bound")
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate profile key")
            result[key] = value
        return result

    contract = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    if (
        not isinstance(contract, dict)
        or contract.get("schema_version")
        != "hwpx-agent.table-chart-render-diff-contract/v1"
    ):
        raise ValueError("invalid profile contract")
    profile = contract.get("frozen_profile")
    if not isinstance(profile, dict):
        raise ValueError("missing frozen profile")
    encoded = json.dumps(
        profile,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != FROZEN_PROFILE_SHA256:
        raise ValueError("frozen profile digest mismatch")
    return profile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-pdf", type=Path, required=True)
    parser.add_argument("--product-pdf", type=Path, required=True)
    parser.add_argument("--native-hwpx", type=Path, required=True)
    parser.add_argument("--product-hwpx", type=Path, required=True)
    parser.add_argument("--pdfinfo", type=Path, required=True)
    parser.add_argument("--pdftoppm", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile)
        observation = observe(
            native_pdf=args.native_pdf,
            product_pdf=args.product_pdf,
            native_hwpx=args.native_hwpx,
            product_hwpx=args.product_hwpx,
            pdfinfo=args.pdfinfo,
            pdftoppm=args.pdftoppm,
            profile=profile,
        )
        errors = validate_observation(observation, profile)
        result = {**observation, "state": "pass" if not errors else "fail", "errors": errors}
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as error:
        result = {
            "schema_version": "hwpx-agent.table-chart-render-diff-observation/v1",
            "state": "fail",
            "errors": ["observation_failed"],
            "detail": type(error).__name__,
        }
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_JSON_BYTES:
        raise SystemExit("bounded result exceeded")
    print(encoded.decode("utf-8"))
    return 0 if result["state"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
