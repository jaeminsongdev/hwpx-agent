#!/usr/bin/env python3
"""Fail-closed P08 Hangul 2020 object batch postprocessing oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree

from PIL import Image, ImageChops


MANIFEST_SCHEMA = "hwpx-agent.p08-19-object-target-bundle/v1"
TRACE_SCHEMA = "hwpx-agent.p08-20-object-target-batch-engine/v1"
RECEIPT_SCHEMA = "hwpx-agent.p08-20-object-target-batch-runtime-receipt/v1"
OUTPUT_SCHEMA = "hwpx-agent.p08-20-object-target-oracle/v1"
TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}
EXPECTED_CASES = 41
REPRESENTATIVE_RETRIES = {"OBJ-002", "OBJ-024", "OBJ-010"}
COMMON_CHILDREN = ("offset", "orgSz", "sz", "pos", "outMargin")
CORE_NS = "http://www.hancom.co.kr/hwpml/2011/core"
OPF_NS = "http://www.idpf.org/2007/opf/"
SHAPE_TAGS = {
    "container",
    "line",
    "rect",
    "ellipse",
    "arc",
    "polygon",
    "curve",
    "connectLine",
    "pic",
    "ole",
    "chart",
}
FEATURE_SUBTREES = {
    "OBJ-001": ("lineShape", "shadow", "pt0", "pt1", "pt2", "pt3"),
    "OBJ-003": ("lineShape", "shadow", "pt0", "pt1", "pt2", "pt3"),
    "OBJ-002": ("imgRect", "imgClip", "inMargin", "imgDim", "img"),
    "OBJ-007": ("textMargin",),
    "OBJ-042": ("pt",),
    "OBJ-032": ("rotationInfo",),
    "OBJ-033": ("flip",),
    "OBJ-020": ("lineShape",),
    "OBJ-021": ("winBrush",),
    "OBJ-022": ("gradation",),
    "OBJ-023": ("winBrush",),
    "OBJ-024": ("imgBrush",),
    "OBJ-026": ("shadow",),
    "OBJ-027": ("reflection",),
    "OBJ-028": ("glow",),
    "OBJ-029": ("softEdge",),
    "OBJ-034": ("lineShape",),
    "OBJ-035": ("img",),
    "OBJ-019": ("caption",),
    "OBJ-025": ("textMargin",),
    "OBJ-030": ("imgRect", "imgClip", "inMargin", "imgDim", "img"),
    "OBJ-043": ("pt",),
    "OBJ-013": ("caption",),
    "OBJ-014": ("winBrush",),
    "OBJ-047": ("shapeComment",),
    "OBJ-031": ("imgRect", "imgClip", "inMargin", "imgDim", "img"),
}
ATTRIBUTE_EXCLUSIONS = {
    "img": {"binaryItemIDRef"},
    "caption": {"lastWidth"},
    "drawText": {"lastWidth"},
}
FORM_TARGET_OMITTED_ATTRIBUTES = {
    "id",
    "zOrder",
    "numberingType",
    "textWrap",
    "textFlow",
    "lock",
    "dropcapstyle",
    "href",
    "groupLevel",
    "instid",
}
FORM_TARGET_CHILDREN = {"sz", "pos", "outMargin", "formCharPr", "text"}
CONNECTOR_TARGET_CONTROL_POINTS = (
    (("type", "3"), ("x", "7200"), ("y", "-12600")),
    (("type", "26"), ("x", "3600"), ("y", "-7200")),
)
RESOURCE_TARGET_PROFILE = "hancom-2020-single-embedded-image-canonical-v1"
RENDER_TARGET_PROFILE = "hancom-2020-object-affected-region-calibrated-v1"
RENDER_CALIBRATIONS = {
    "OBJ-020": {"affected_bbox": (135, 166, 274, 242), "changed_pixels_max": 208, "channel_delta_max": 40, "channel_delta_sum_max": 3272},
    "OBJ-021": {"affected_bbox": (130, 170, 270, 243), "changed_pixels_max": 2425, "channel_delta_max": 47, "channel_delta_sum_max": 50525},
    "OBJ-022": {"affected_bbox": (130, 170, 270, 238), "changed_pixels_max": 3100, "channel_delta_max": 51, "channel_delta_sum_max": 52050},
    "OBJ-023": {"affected_bbox": (130, 170, 270, 238), "changed_pixels_max": 2077, "channel_delta_max": 45, "channel_delta_sum_max": 18070},
    "OBJ-024": {"affected_bbox": (165, 170, 236, 243), "changed_pixels_max": 1628, "channel_delta_max": 49, "channel_delta_sum_max": 31792},
    "OBJ-026": {"affected_bbox": (139, 250, 346, 323), "changed_pixels_max": 228, "channel_delta_max": 26, "channel_delta_sum_max": 1881},
    "OBJ-034": {"affected_bbox": (135, 166, 274, 242), "changed_pixels_max": 224, "channel_delta_max": 57, "channel_delta_sum_max": 5354},
}
MEDIA_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
}
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_ZIP_ENTRIES = 4096
MAX_ZIP_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ZIP_TOTAL_BYTES = 256 * 1024 * 1024
MAX_XML_BYTES = 32 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class OracleError(RuntimeError):
    """Expected, redacted oracle failure."""


def fail(code: str) -> None:
    raise OracleError(code)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bounded(path: Path, limit: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        fail("invalid_input_file")
    size = path.stat().st_size
    if size <= 0 or size > limit:
        fail("input_size_limit")
    data = path.read_bytes()
    if len(data) != size:
        fail("input_size_drift")
    return data


def load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    data = read_bounded(path, MAX_JSON_BYTES)
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("invalid_json")
    if not isinstance(value, dict):
        fail("invalid_json_shape")
    return value, data


def absolute_existing_directory(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        fail("invalid_absolute_directory")
    return path.resolve(strict=True)


def absolute_existing_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        fail("invalid_absolute_file")
    return path.resolve(strict=True)


def absolute_new_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.exists() or path.is_symlink():
        fail("invalid_new_output")
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir() or parent.is_symlink():
        fail("invalid_output_parent")
    return parent / path.name


def ensure_child(root: Path, child: Path) -> Path:
    resolved = child.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError:
        fail("path_escape")
    if child.is_symlink():
        fail("symlink_refused")
    return resolved


def local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def parse_xml(data: bytes) -> ElementTree.Element:
    if len(data) > MAX_XML_BYTES or b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        fail("unsafe_xml")
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError:
        fail("invalid_xml")


class SafeZip:
    def __init__(self, path: Path):
        self.path = path
        self._archive: zipfile.ZipFile | None = None
        self.names: set[str] = set()

    def __enter__(self) -> "SafeZip":
        read_bounded(self.path, MAX_PACKAGE_BYTES)
        try:
            self._archive = zipfile.ZipFile(self.path, "r")
            members = self._archive.infolist()
        except (OSError, zipfile.BadZipFile):
            fail("invalid_zip")
        if not members or len(members) > MAX_ZIP_ENTRIES:
            fail("zip_entry_limit")
        total = 0
        normalized: set[str] = set()
        windows_aliases: set[str] = set()
        for member in members:
            name = member.filename
            pure = PurePosixPath(name)
            if (
                not name
                or "\\" in name
                or pure.is_absolute()
                or any(part in {"", ".", ".."} for part in pure.parts)
                or member.file_size < 0
                or member.file_size > MAX_ZIP_MEMBER_BYTES
                or member.compress_size < 0
            ):
                fail("unsafe_zip_member")
            canonical = pure.as_posix()
            if canonical in normalized:
                fail("duplicate_zip_member")
            windows_alias = unicodedata.normalize("NFC", canonical).casefold()
            if windows_alias in windows_aliases:
                fail("ambiguous_zip_member")
            normalized.add(canonical)
            windows_aliases.add(windows_alias)
            total += member.file_size
            if total > MAX_ZIP_TOTAL_BYTES:
                fail("zip_total_limit")
        self.names = normalized
        return self

    def __exit__(self, *_: object) -> None:
        if self._archive is not None:
            self._archive.close()

    def read(self, name: str, *, limit: int = MAX_ZIP_MEMBER_BYTES) -> bytes:
        if self._archive is None or name not in self.names:
            fail("missing_zip_member")
        info = self._archive.getinfo(name)
        if info.file_size > limit:
            fail("zip_member_limit")
        try:
            data = self._archive.read(info)
        except (OSError, RuntimeError, zipfile.BadZipFile):
            fail("invalid_zip_member")
        if len(data) != info.file_size:
            fail("zip_member_size_drift")
        return data


def validate_manifest(manifest: dict[str, Any], data: bytes, expected_sha256: str) -> list[dict[str, Any]]:
    if not SHA256_RE.fullmatch(expected_sha256) or sha256_bytes(data) != expected_sha256:
        fail("manifest_sha256_mismatch")
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        fail("manifest_schema_mismatch")
    if manifest.get("target_profile") != TARGET:
        fail("manifest_target_mismatch")
    cases = manifest.get("cases")
    if (
        not isinstance(cases, list)
        or len(cases) != EXPECTED_CASES
        or manifest.get("direct_feature_count") != EXPECTED_CASES
    ):
        fail("manifest_case_count_mismatch")
    if manifest.get("actual_hangul_2020") is not False:
        fail("fixture_claim_boundary_mismatch")
    for field in (
        "save_reopen",
        "resource_integrity",
        "object_bounds",
        "render",
        "differential",
        "rollback_or_retry",
    ):
        if manifest.get(field) != "not_run":
            fail("fixture_claim_boundary_mismatch")
    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            fail("invalid_manifest_case")
        feature = case.get("feature_id")
        file_name = case.get("file")
        digest = case.get("package_sha256")
        if (
            not isinstance(feature, str)
            or feature in seen_ids
            or not isinstance(file_name, str)
            or file_name in seen_files
            or PurePosixPath(file_name).name != file_name
            or not file_name.endswith(".hwpx")
            or not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or not isinstance(case.get("package_bytes"), int)
            or case["package_bytes"] <= 0
        ):
            fail("invalid_manifest_case")
        seen_ids.add(feature)
        seen_files.add(file_name)
    return cases


def exact_target(value: Any, *, build_key: str = "build") -> bool:
    if not isinstance(value, dict):
        return False
    return all(
        value.get(build_key if key == "build" else key) == expected
        for key, expected in TARGET.items()
    )


def verify_runtime(
    run_root: Path,
    expected_manifest_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    trace, trace_bytes = load_json(ensure_child(run_root, run_root / "engine-trace.json"))
    receipt, receipt_bytes = load_json(ensure_child(run_root, run_root / "runtime-receipt.json"))
    progress_path = ensure_child(run_root, run_root / "progress.jsonl")
    progress_bytes = read_bounded(progress_path, MAX_JSON_BYTES)
    if trace.get("schema_version") != TRACE_SCHEMA or receipt.get("schema_version") != RECEIPT_SCHEMA:
        fail("runtime_schema_mismatch")
    if trace.get("state") != "pass" or receipt.get("state") != "pass":
        fail("runtime_not_pass")
    if trace.get("fixture_manifest_sha256") != expected_manifest_sha256 or receipt.get(
        "fixture_manifest_sha256"
    ) != expected_manifest_sha256:
        fail("runtime_manifest_mismatch")
    if not exact_target(trace.get("target"), build_key="file_version") or not exact_target(
        receipt.get("target")
    ):
        fail("runtime_target_mismatch")
    if receipt.get("engine_trace_sha256") != sha256_bytes(trace_bytes) or receipt.get(
        "progress_sha256"
    ) != sha256_bytes(progress_bytes):
        fail("runtime_artifact_sha256_mismatch")
    if any(
        receipt.get(field) is not False
        for field in (
            "raw_document_text_present",
            "user_document_scanned",
            "external_network_invoked",
            "registry_or_system_setting_changed",
            "computer_use_click_or_type_invoked",
        )
    ):
        fail("runtime_scope_violation")
    watchdog = receipt.get("watchdog")
    if (
        not isinstance(watchdog, dict)
        or watchdog.get("timed_out") is not False
        or watchdog.get("child_exit_code") != 0
        or watchdog.get("output_drained") is not True
        or watchdog.get("remaining_hwp_process_count") != 0
        or watchdog.get("cleanup_refused_count") != 0
        or watchdog.get("cleanup_error_count") != 0
        or watchdog.get("stalled_hwp_cleanup_refused_count") != 0
        or watchdog.get("stalled_hwp_cleanup_error_count") != 0
    ):
        fail("watchdog_not_clean")
    return trace, receipt, trace_bytes, receipt_bytes


def valid_case_row(row: dict[str, Any], manifest_case: dict[str, Any], attempt: str) -> None:
    if (
        row.get("case_id") != manifest_case.get("case_id")
        or row.get("feature_id") != manifest_case.get("feature_id")
        or row.get("capability_id") != manifest_case.get("capability_id")
        or row.get("attempt") != attempt
        or row.get("input_sha256") != manifest_case.get("package_sha256")
        or row.get("input_bytes") != manifest_case.get("package_bytes")
        or row.get("input_unchanged") is not True
    ):
        fail("runtime_case_binding_mismatch")


def choose_effective_cases(
    trace: dict[str, Any],
    receipt: dict[str, Any],
    manifest_cases: list[dict[str, Any]],
) -> tuple[list[tuple[dict[str, Any], str]], list[dict[str, Any]]]:
    primaries = trace.get("cases")
    retries = trace.get("retries")
    if not isinstance(primaries, list) or not isinstance(retries, list) or len(primaries) != EXPECTED_CASES:
        fail("runtime_case_shape_mismatch")
    by_feature = {case["feature_id"]: case for case in manifest_cases}
    if [row.get("feature_id") for row in primaries] != [case["feature_id"] for case in manifest_cases]:
        fail("runtime_case_order_mismatch")
    retry_by_feature: dict[str, dict[str, Any]] = {}
    for row in retries:
        if not isinstance(row, dict) or row.get("feature_id") in retry_by_feature:
            fail("invalid_retry_set")
        feature = row.get("feature_id")
        if feature not in by_feature:
            fail("invalid_retry_set")
        valid_case_row(row, by_feature[feature], "retry")
        if row.get("state") != "pass":
            fail("retry_not_pass")
        retry_by_feature[feature] = row
    if not REPRESENTATIVE_RETRIES.issubset(retry_by_feature):
        fail("representative_retry_missing")
    effective: list[tuple[dict[str, Any], str]] = []
    primary_failures = 0
    for row, case in zip(primaries, manifest_cases, strict=True):
        if not isinstance(row, dict):
            fail("invalid_primary_case")
        valid_case_row(row, case, "primary")
        if row.get("state") == "pass":
            effective.append((row, ""))
        else:
            primary_failures += 1
            retry = retry_by_feature.get(case["feature_id"])
            if retry is None:
                fail("unrecovered_primary_failure")
            effective.append((retry, "-retry"))
    if (
        trace.get("case_count") != EXPECTED_CASES
        or trace.get("effective_completed_case_count") != EXPECTED_CASES
        or receipt.get("effective_completed_case_count") != EXPECTED_CASES
        or trace.get("recovered_case_count") != primary_failures
        or receipt.get("recovered_case_count") != primary_failures
        or trace.get("retry_case_count") != len(retries)
        or receipt.get("retry_case_count") != len(retries)
        or trace.get("retry_completed_case_count") != len(retries)
        or receipt.get("retry_completed_case_count") != len(retries)
    ):
        fail("runtime_case_accounting_mismatch")
    return effective, retries


def artifact_paths(run_root: Path, manifest_case: dict[str, Any], suffix: str) -> tuple[Path, Path, Path]:
    stem = Path(manifest_case["file"]).stem
    prefix = f"{stem}.hancom-2020{suffix}"
    return (
        ensure_child(run_root, run_root / f"{prefix}-readback.hwpx"),
        ensure_child(run_root, run_root / f"{prefix}-before.pdf"),
        ensure_child(run_root, run_root / f"{prefix}-after.pdf"),
    )


def verify_case_artifacts(
    run_root: Path,
    manifest_case: dict[str, Any],
    row: dict[str, Any],
    suffix: str,
) -> tuple[Path, Path, Path]:
    if (
        row.get("state") != "pass"
        or row.get("output_saved") is not True
        or row.get("input_unchanged") is not True
        or row.get("text_preserved") is not True
        or row.get("pdf_signatures_valid") is not True
        or row.get("error_code") is not None
        or row.get("failed_phase") is not None
    ):
        fail("case_not_pass")
    phases = row.get("phases")
    required_phases = {
        "open_input",
        "read_input",
        "export_before_pdf",
        "save_as_hwpx",
        "close_input",
        "reopen_output",
        "read_output",
        "export_after_pdf",
        "close_output",
    }
    if not isinstance(phases, dict) or set(phases) != required_phases or any(
        phases[name] != "pass" for name in required_phases
    ):
        fail("case_phase_not_pass")
    readback, before_pdf, after_pdf = artifact_paths(run_root, manifest_case, suffix)
    values = (
        (readback, "output_sha256", "output_bytes"),
        (before_pdf, "before_pdf_sha256", "before_pdf_bytes"),
        (after_pdf, "after_pdf_sha256", "after_pdf_bytes"),
    )
    for path, digest_key, size_key in values:
        data = read_bounded(path, MAX_PACKAGE_BYTES)
        if sha256_bytes(data) != row.get(digest_key) or len(data) != row.get(size_key):
            fail("case_artifact_mismatch")
    if read_bounded(before_pdf, MAX_PACKAGE_BYTES)[:5] != b"%PDF-" or read_bounded(
        after_pdf, MAX_PACKAGE_BYTES
    )[:5] != b"%PDF-":
        fail("invalid_pdf_signature")
    return readback, before_pdf, after_pdf


def load_section(path: Path) -> tuple[ElementTree.Element, dict[str, bytes], ElementTree.Element]:
    with SafeZip(path) as package:
        section_data = package.read("Contents/section0.xml", limit=MAX_XML_BYTES)
        content_data = package.read("Contents/content.hpf", limit=MAX_XML_BYTES)
        entries = {name: package.read(name) for name in package.names if name.startswith("BinData/")}
    return parse_xml(section_data), entries, parse_xml(content_data)


def descendants(root: ElementTree.Element, name: str) -> list[ElementTree.Element]:
    return [element for element in root.iter() if local_name(element.tag) == name]


def direct_child(root: ElementTree.Element, name: str) -> ElementTree.Element | None:
    matches = [child for child in root if local_name(child.tag) == name]
    if len(matches) > 1:
        fail("duplicate_common_child")
    return matches[0] if matches else None


def semantic_attributes(element: ElementTree.Element, excluded: Iterable[str] = ()) -> tuple[tuple[str, str], ...]:
    exclusions = set(excluded)
    return tuple(
        sorted(
            (key, value)
            for key, value in element.attrib.items()
            if local_name(key) not in exclusions
        )
    )


def node_signature(element: ElementTree.Element) -> tuple[Any, ...]:
    name = local_name(element.tag)
    excluded = ATTRIBUTE_EXCLUSIONS.get(name, set())
    return (
        element.tag,
        semantic_attributes(element, excluded),
        (element.text or "").strip(),
        tuple(node_signature(child) for child in element),
    )


def compare_named_subtrees(source: ElementTree.Element, target: ElementTree.Element, names: Iterable[str]) -> None:
    for name in names:
        source_nodes = descendants(source, name)
        target_nodes = descendants(target, name)
        if name == "rotationInfo":
            source_values = [node.attrib.get("angle") for node in source_nodes]
            target_values = [node.attrib.get("angle") for node in target_nodes]
        elif name in {"caption", "drawText"}:
            source_values = [semantic_attributes(node, ATTRIBUTE_EXCLUSIONS[name]) for node in source_nodes]
            target_values = [semantic_attributes(node, ATTRIBUTE_EXCLUSIONS[name]) for node in target_nodes]
        else:
            source_values = [node_signature(node) for node in source_nodes]
            target_values = [node_signature(node) for node in target_nodes]
        if source_values != target_values:
            fail(f"semantic_subtree_mismatch:{name}")


def object_map(root: ElementTree.Element) -> dict[str, ElementTree.Element]:
    result: dict[str, ElementTree.Element] = {}
    for element in root.iter():
        instance = element.attrib.get("instid")
        if instance is None or local_name(element.tag) not in SHAPE_TAGS:
            continue
        native_u32(element, "instid")
        if instance in result:
            fail("duplicate_instance_id")
        result[instance] = element
    return result


def native_u32(element: ElementTree.Element, name: str) -> int:
    value = element.attrib.get(name)
    if value is None or not value.isascii() or not value.isdecimal():
        fail(f"invalid_native_attribute:{name}")
    parsed = int(value)
    if parsed > 0xFFFF_FFFF:
        fail(f"invalid_native_attribute:{name}")
    return parsed


def object_structure(root: ElementTree.Element) -> tuple[tuple[str, str | None], ...]:
    result: list[tuple[str, str | None]] = []

    def walk(element: ElementTree.Element, parent_instance: str | None) -> None:
        for child in element:
            if local_name(child.tag) in SHAPE_TAGS:
                instance = child.attrib.get("instid")
                if instance is None:
                    fail("object_instance_missing")
                result.append((instance, parent_instance))
                walk(child, instance)
            else:
                walk(child, parent_instance)

    walk(root, None)
    return tuple(result)


def connector_control_points(
    element: ElementTree.Element,
) -> tuple[tuple[tuple[str, str], ...], ...]:
    controls = descendants(element, "controlPoints")
    if len(controls) > 1:
        fail("semantic_subtree_mismatch:controlPoints")
    if not controls:
        return ()
    wrapper = controls[0]
    if semantic_attributes(wrapper) or (wrapper.text or "").strip():
        fail("semantic_subtree_mismatch:controlPoints")
    if any(local_name(child.tag) != "point" for child in wrapper):
        fail("semantic_subtree_mismatch:controlPoints")
    if any(child.text and child.text.strip() or len(child) for child in wrapper):
        fail("semantic_subtree_mismatch:controlPoints")
    return tuple(semantic_attributes(child) for child in wrapper)


def compare_common_object(
    feature: str,
    source: ElementTree.Element,
    target: ElementTree.Element,
) -> None:
    if source.tag != target.tag:
        fail("object_tag_mismatch")
    for element in (source, target):
        for name in ("id", "instid", "zOrder", "groupLevel"):
            native_u32(element, name)
    nested = source.attrib.get("groupLevel") not in {None, "0"}
    exclusions = {"id", "zOrder"}
    if (
        nested
        and feature in {"OBJ-010", "OBJ-031"}
        and local_name(source.tag) == "pic"
        and source.attrib.get("numberingType") == "PICTURE"
        and target.attrib.get("numberingType") == "NONE"
    ):
        exclusions.add("numberingType")
    if feature == "OBJ-048" and not nested:
        source_href = source.attrib.get("href")
        if not source_href or ";" in source_href or target.attrib.get("href") != f"{source_href};0;0;0;":
            fail("object_attribute_mismatch:href")
        exclusions.add("href")
    if semantic_attributes(source, exclusions) != semantic_attributes(target, exclusions):
        fail("object_attribute_mismatch:root")
    if nested:
        if target.attrib.get("zOrder") != "0":
            fail("object_attribute_mismatch:zOrder")
    elif source.attrib.get("zOrder") != target.attrib.get("zOrder"):
        fail("object_attribute_mismatch:zOrder")
    if not nested and source.attrib.get("id") != target.attrib.get("id"):
        fail("object_attribute_mismatch:id")
    for name in COMMON_CHILDREN:
        source_child = direct_child(source, name)
        target_child = direct_child(target, name)
        if source_child is None:
            if target_child is not None:
                fail(f"unexpected_common_child:{name}")
            continue
        if target_child is None and nested and name in {"sz", "pos", "outMargin"}:
            continue
        if target_child is None or node_signature(source_child) != node_signature(target_child):
            fail(f"common_child_mismatch:{name}")


def validate_semantics(
    feature: str,
    native_instance_id: int,
    source_root: ElementTree.Element,
    target_root: ElementTree.Element,
) -> None:
    if feature in {"OBJ-012", "OBJ-046"}:
        source_forms = [e for e in source_root.iter() if local_name(e.tag) == "edit" and e.attrib.get("name") == "p08field"]
        target_forms = [e for e in target_root.iter() if local_name(e.tag) == "edit" and e.attrib.get("name") == "p08field"]
        if len(source_forms) != 1 or len(target_forms) != 1:
            fail("form_target_mismatch")
        source, target = source_forms[0], target_forms[0]
        for name in ("id", "instid", "zOrder", "groupLevel"):
            native_u32(source, name)
        if source.attrib.get("instid") != str(native_instance_id):
            fail("semantic_target_missing")
        if source.tag != target.tag:
            fail("form_target_mismatch")
        if any(name in target.attrib for name in FORM_TARGET_OMITTED_ATTRIBUTES):
            fail("form_attribute_mismatch:root")
        expected_attributes = {
            name: value
            for name, value in source.attrib.items()
            if name not in FORM_TARGET_OMITTED_ATTRIBUTES
        }
        if expected_attributes.get("tabOrder") != "0":
            fail("form_attribute_mismatch:tabOrder")
        expected_attributes["tabOrder"] = "1"
        if semantic_attributes(target) != tuple(sorted(expected_attributes.items())):
            fail("form_attribute_mismatch:root")
        source_children = {local_name(child.tag): child for child in source}
        target_children = {local_name(child.tag): child for child in target}
        if (
            set(source_children) != FORM_TARGET_CHILDREN
            or set(target_children) != FORM_TARGET_CHILDREN
            or len(source_children) != len(source)
            or len(target_children) != len(target)
            or any(
                node_signature(source_children[name]) != node_signature(target_children[name])
                for name in FORM_TARGET_CHILDREN
            )
        ):
            fail("form_subtree_mismatch")
        return
    source_objects = object_map(source_root)
    target_objects = object_map(target_root)
    if set(source_objects) != set(target_objects):
        fail("object_instance_set_mismatch")
    if object_structure(source_root) != object_structure(target_root):
        fail("object_structure_mismatch")
    for instance, source in source_objects.items():
        compare_common_object(feature, source, target_objects[instance])
    instance = str(native_instance_id)
    if instance not in source_objects or instance not in target_objects:
        fail("semantic_target_missing")
    source = source_objects[instance]
    target = target_objects[instance]
    compare_named_subtrees(source, target, FEATURE_SUBTREES.get(feature, ()))
    if feature == "OBJ-007" or feature == "OBJ-025":
        source_draw = descendants(source, "drawText")
        target_draw = descendants(target, "drawText")
        if [semantic_attributes(x, {"lastWidth"}) for x in source_draw] != [
            semantic_attributes(x, {"lastWidth"}) for x in target_draw
        ]:
            fail("draw_text_attribute_mismatch")
    if feature == "OBJ-041":
        compare_named_subtrees(source, target, ("startPt", "endPt"))
        source_controls = connector_control_points(source)
        target_controls = connector_control_points(target)
        if source_controls != target_controls and not (
            not source_controls and target_controls == CONNECTOR_TARGET_CONTROL_POINTS
        ):
            fail("semantic_subtree_mismatch:controlPoints")


def resource_projection(
    section: ElementTree.Element,
    entries: dict[str, bytes],
    content: ElementTree.Element,
) -> tuple[Counter[tuple[str, str, str, int]], Counter[tuple[str, str, str, int]]]:
    items: dict[str, tuple[str, str, str]] = {}
    hrefs: set[str] = set()
    for element in content.iter():
        if local_name(element.tag) != "item":
            continue
        item_id = element.attrib.get("id")
        href = element.attrib.get("href")
        media = element.attrib.get("media-type")
        embedded = element.attrib.get("isEmbeded")
        if item_id and href and media and href.startswith("BinData/"):
            if (
                element.tag != f"{{{OPF_NS}}}item"
                or item_id in items
                or href in hrefs
                or PurePosixPath(href).as_posix() != href
                or ".." in PurePosixPath(href).parts
            ):
                fail("invalid_resource_manifest")
            items[item_id] = (href, media, embedded or "")
            hrefs.add(href)
    if hrefs != set(entries):
        fail("resource_inventory_mismatch")
    inventory: Counter[tuple[str, str, str, int]] = Counter()
    for href, media, embedded in items.values():
        payload = entries.get(href)
        if payload is None or not payload or embedded != "1":
            fail("resource_not_embedded")
        inventory[(href, media, sha256_bytes(payload), len(payload))] += 1
    referenced = []
    for element in section.iter():
        value = element.attrib.get("binaryItemIDRef")
        if value:
            if element.tag != f"{{{CORE_NS}}}img":
                fail("invalid_resource_reference")
            referenced.append(value)
    projection: Counter[tuple[str, str, str, int]] = Counter()
    for item_id in referenced:
        if item_id not in items:
            fail("dangling_resource_reference")
        href, media, embedded = items[item_id]
        payload = entries.get(href)
        if payload is None or not payload:
            fail("missing_resource_payload")
        if embedded != "1":
            fail("resource_not_embedded")
        projection[(href, media, sha256_bytes(payload), len(payload))] += 1
    return projection, inventory


def validate_resources(
    expected: bool,
    source: tuple[ElementTree.Element, dict[str, bytes], ElementTree.Element],
    target: tuple[ElementTree.Element, dict[str, bytes], ElementTree.Element],
    context: str = "",
) -> int:
    suffix = f":{context}" if context else ""
    source_projection, source_inventory = resource_projection(*source)
    target_projection, target_inventory = resource_projection(*target)
    if expected:
        if not source_projection:
            fail(f"resource_projection_mismatch{suffix}")
        if source_projection != target_projection or source_inventory != target_inventory:
            source_payloads = Counter(
                {
                    (media, digest, length): count
                    for (_, media, digest, length), count in source_projection.items()
                }
            )
            target_payloads = Counter(
                {
                    (media, digest, length): count
                    for (_, media, digest, length), count in target_projection.items()
                }
            )
            source_inventory_payloads = Counter(
                {
                    (media, digest, length): count
                    for (_, media, digest, length), count in source_inventory.items()
                }
            )
            target_inventory_payloads = Counter(
                {
                    (media, digest, length): count
                    for (_, media, digest, length), count in target_inventory.items()
                }
            )
            if (
                source_payloads != target_payloads
                or source_inventory_payloads != target_inventory_payloads
                or sum(source_inventory.values()) != 1
                or sum(target_inventory.values()) != 1
            ):
                fail(f"resource_projection_mismatch{suffix}")
            source_href, media, digest, _ = next(iter(source_inventory))
            target_href, target_media, target_digest, _ = next(iter(target_inventory))
            extension = MEDIA_EXTENSIONS.get(media)
            if (
                extension is None
                or target_media != media
                or target_digest != digest
                or source_href != f"BinData/p08-{digest}.{extension}"
                or target_href != f"BinData/image1.{extension}"
            ):
                fail(f"resource_projection_mismatch{suffix}")
            target_items = [
                element
                for element in target[2].iter()
                if local_name(element.tag) == "item"
                and element.attrib.get("href", "").startswith("BinData/")
            ]
            if len(target_items) != 1 or target_items[0].attrib.get("id") != "image1":
                fail(f"resource_projection_mismatch{suffix}")
    if not expected and (
        source_projection
        or target_projection
        or source_inventory
        or target_inventory
    ):
        fail(f"unexpected_resource_projection{suffix}")
    return sum(source_projection.values())


def pdf_page_count(pdfinfo: Path, path: Path) -> int:
    result = subprocess.run(
        [str(pdfinfo), str(path)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode != 0:
        fail("pdfinfo_failed")
    match = re.search(r"(?m)^Pages:\s+(\d+)\s*$", result.stdout)
    if match is None:
        fail("pdf_page_count_missing")
    pages = int(match.group(1))
    if pages <= 0 or pages > 100:
        fail("pdf_page_count_limit")
    return pages


def render_pdf(pdftoppm: Path, path: Path, directory: Path, prefix: str) -> list[Path]:
    output = directory / prefix
    result = subprocess.run(
        [str(pdftoppm), "-png", "-r", "96", str(path), str(output)],
        check=False,
        capture_output=True,
        timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    if result.returncode != 0:
        fail("pdf_render_failed")
    pages = sorted(directory.glob(f"{prefix}-*.png"))
    if not pages:
        fail("pdf_render_missing")
    return pages


def compare_image_files(
    before: Path,
    after: Path,
    feature: str = "",
    context: str = "",
) -> dict[str, Any]:
    suffix = f":{context}" if context else ""
    with Image.open(before) as left_source, Image.open(after) as right_source:
        left = left_source.convert("RGB")
        right = right_source.convert("RGB")
        if left.size != right.size:
            fail(f"render_size_mismatch{suffix}")
        nonwhite = ImageChops.difference(left, Image.new("RGB", left.size, "white")).getbbox()
        target_nonwhite = ImageChops.difference(
            right, Image.new("RGB", right.size, "white")
        ).getbbox()
        if nonwhite is None or target_nonwhite is None:
            fail(f"render_empty_page{suffix}")
        if nonwhite != target_nonwhite:
            fail(f"render_bounds_mismatch{suffix}")
        x0, y0, x1, y1 = nonwhite
        if x0 < 0 or y0 < 0 or x1 > left.width or y1 > left.height or x0 >= x1 or y0 >= y1:
            fail(f"render_bounds_invalid{suffix}")
        difference = ImageChops.difference(left, right)
        difference_box = difference.getbbox()
        changed_pixels = 0
        channel_delta_max = 0
        channel_delta_sum = 0
        if difference_box is not None:
            for left_pixel, right_pixel in zip(
                left.get_flattened_data(), right.get_flattened_data(), strict=True
            ):
                if left_pixel == right_pixel:
                    continue
                changed_pixels += 1
                channel_delta = max(
                    abs(left_pixel[channel] - right_pixel[channel]) for channel in range(3)
                )
                channel_delta_max = max(channel_delta_max, channel_delta)
                channel_delta_sum += channel_delta
            calibration = RENDER_CALIBRATIONS.get(feature)
            if calibration is None:
                fail(f"render_pixel_mismatch{suffix}")
            allowed = calibration["affected_bbox"]
            if (
                difference_box[0] < allowed[0]
                or difference_box[1] < allowed[1]
                or difference_box[2] > allowed[2]
                or difference_box[3] > allowed[3]
                or changed_pixels > calibration["changed_pixels_max"]
                or channel_delta_max > calibration["channel_delta_max"]
                or channel_delta_sum > calibration["channel_delta_sum_max"]
            ):
                fail(f"render_calibration_exceeded{suffix}")
        return {
            "width": left.width,
            "height": left.height,
            "nonwhite_bbox": list(nonwhite),
            "changed_pixels": changed_pixels,
            "difference_bbox": list(difference_box) if difference_box else None,
            "channel_delta_max": channel_delta_max,
            "channel_delta_sum": channel_delta_sum,
        }


def validate_pdf_pair(
    pdfinfo: Path,
    pdftoppm: Path,
    before: Path,
    after: Path,
    feature: str,
) -> dict[str, Any]:
    before_pages = pdf_page_count(pdfinfo, before)
    after_pages = pdf_page_count(pdfinfo, after)
    if before_pages != after_pages:
        fail("pdf_page_count_mismatch")
    with tempfile.TemporaryDirectory(prefix="p08-object-oracle-") as temporary:
        root = Path(temporary)
        left = render_pdf(pdftoppm, before, root, "before")
        right = render_pdf(pdftoppm, after, root, "after")
        if len(left) != before_pages or len(right) != after_pages:
            fail("pdf_render_page_count_mismatch")
        pages = []
        for page_number, (left_page, right_page) in enumerate(
            zip(left, right, strict=True), start=1
        ):
            page = compare_image_files(
                left_page,
                right_page,
                feature,
                f"{before.stem}:page-{page_number}",
            )
            pages.append(page)
    return {
        "page_count": before_pages,
        "pages": pages,
        "changed_pixels": sum(page["changed_pixels"] for page in pages),
    }


def run_oracle(arguments: argparse.Namespace) -> dict[str, Any]:
    fixture_root = absolute_existing_directory(arguments.fixture_directory)
    run_root = absolute_existing_directory(arguments.run_directory)
    pdfinfo = absolute_existing_file(arguments.pdfinfo)
    pdftoppm = absolute_existing_file(arguments.pdftoppm)
    output = absolute_new_file(arguments.output)
    manifest_path = ensure_child(fixture_root, fixture_root / "fixture-manifest.json")
    manifest, manifest_bytes = load_json(manifest_path)
    cases = validate_manifest(manifest, manifest_bytes, arguments.expected_manifest_sha256)
    trace, receipt, trace_bytes, receipt_bytes = verify_runtime(run_root, arguments.expected_manifest_sha256)
    effective, retries = choose_effective_cases(trace, receipt, cases)
    results = []
    retry_by_feature = {row["feature_id"]: row for row in retries}
    for case, (row, suffix) in zip(cases, effective, strict=True):
        fixture_path = ensure_child(fixture_root, fixture_root / case["file"])
        fixture_bytes = read_bounded(fixture_path, MAX_PACKAGE_BYTES)
        if sha256_bytes(fixture_bytes) != case["package_sha256"] or len(fixture_bytes) != case["package_bytes"]:
            fail("fixture_package_mismatch")
        readback, before_pdf, after_pdf = verify_case_artifacts(run_root, case, row, suffix)
        source_package = load_section(fixture_path)
        target_package = load_section(readback)
        validate_semantics(
            case["feature_id"],
            case["native_instance_id"],
            source_package[0],
            target_package[0],
        )
        resources = validate_resources(
            bool(case["resource_integrity_expected"]),
            source_package,
            target_package,
            case["feature_id"],
        )
        render = validate_pdf_pair(
            pdfinfo, pdftoppm, before_pdf, after_pdf, case["feature_id"]
        )
        retry_row = retry_by_feature.get(case["feature_id"])
        if retry_row is not None and retry_row is not row:
            retry_readback, retry_before, retry_after = verify_case_artifacts(run_root, case, retry_row, "-retry")
            retry_package = load_section(retry_readback)
            validate_semantics(
                case["feature_id"],
                case["native_instance_id"],
                source_package[0],
                retry_package[0],
            )
            validate_resources(
                bool(case["resource_integrity_expected"]),
                source_package,
                retry_package,
                f"{case['feature_id']}:retry",
            )
            validate_pdf_pair(
                pdfinfo,
                pdftoppm,
                retry_before,
                retry_after,
                case["feature_id"],
            )
        results.append(
            {
                "case_id": case["case_id"],
                "feature_id": case["feature_id"],
                "attempt": row["attempt"],
                "semantic_reopen": "pass",
                "resource_integrity": "pass" if case["resource_integrity_expected"] else "not_applicable",
                "resource_reference_count": resources,
                "object_bounds": "pass",
                "render": "pass",
                "render_evidence": render,
            }
        )
    result = {
        "schema_version": OUTPUT_SCHEMA,
        "state": "pass",
        "target": TARGET,
        "fixture_manifest_sha256": arguments.expected_manifest_sha256,
        "engine_trace_sha256": sha256_bytes(trace_bytes),
        "runtime_receipt_sha256": sha256_bytes(receipt_bytes),
        "case_count": len(results),
        "semantic_reopen_passed": len(results),
        "resource_integrity_passed": sum(bool(case["resource_integrity_expected"]) for case in cases),
        "object_bounds_passed": len(results),
        "render_passed": len(results),
        "resource_threshold": {
            "profile_id": RESOURCE_TARGET_PROFILE,
            "payload_media_length_and_reference_multiplicity_exact": True,
            "arbitrary_path_remap_allowed": False,
        },
        "render_threshold": {
            "profile_id": RENDER_TARGET_PROFILE,
            "dpi": 96,
            "unchanged_region_changed_pixels_max": 0,
            "calibrated_feature_count": len(RENDER_CALIBRATIONS),
        },
        "rollback_or_retry": "pass",
        "representative_retry_features": sorted(REPRESENTATIVE_RETRIES),
        "cases": results,
        "raw_document_text_present": False,
    }
    encoded = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with output.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        fail("output_exists")
    return {"state": "pass", "case_count": len(results), "output_sha256": sha256_bytes(encoded)}


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-directory", required=True)
    parser.add_argument("--run-directory", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--pdfinfo", required=True)
    parser.add_argument("--pdftoppm", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        result = run_oracle(parse_arguments(sys.argv[1:] if argv is None else argv))
    except (OracleError, OSError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, OracleError) else "oracle_runtime_error"
        print(json.dumps({"state": "failed", "error_code": code}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
