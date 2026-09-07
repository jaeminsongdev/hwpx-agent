#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RUN_ROOT = ROOT / "artifacts/p06/font-metric-runs"
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_HWP_SHA256 = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
EXPECTED_FONT_SHA256 = "0dbeb7b129fcec63f8d6b7f1d3b5bb991c1d599e725286518ccc598de643f014"
EXPECTED_MEASUREMENT_SET_SHA256 = (
    "96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9"
)
EXPECTED_TEXT_SHA256 = {
    "cell-a": "df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98",
    "cell-b": "b81461d5ac0a8865284ef84c147e0743da482750e1a499d80126e31c7324ee7b",
    "cell-c": "25dfcb4b0c5e694cf7bf977f1870cd2025fa363bfa2a26118ea00f305a3afdd3",
    "cell-d": "d932f7dee69be5f5763a0647e1ed14067e5231e783b4039a9aabbf8387405845",
}
RAW_TEXT_MARKERS = ("P06-05 A", "한글 표 자동 맞춤", "WIDE-CONTENT-1234567890", "병합 셀")


class VerificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise VerificationError(code)


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "json.duplicate")
        result[key] = value
    return result


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def resolve_receipt(value: str) -> Path:
    path = Path(value).resolve(strict=True)
    root = RUN_ROOT.resolve(strict=True)
    require(root in path.parents and path.parent.parent == root, "receipt.boundary")
    require(HEX32.fullmatch(path.parent.name) is not None, "receipt.run_id")
    require(path.name == "receipt.json" and path.is_file() and not path.is_symlink(), "receipt.path")
    require(0 < path.stat().st_size <= 262_144, "receipt.size")
    return path


def expected_hwp_path() -> Path:
    base = os.environ.get("ProgramFiles(x86)")
    require(isinstance(base, str) and bool(base), "environment.program_files_x86")
    return Path(base) / "HNC/Office 2020/HOffice110/bin/hwp.exe"


def expected_font_path() -> Path:
    base = os.environ.get("WINDIR")
    require(isinstance(base, str) and bool(base), "environment.windows")
    return Path(base) / "Fonts/HANBatang.ttf"


def validate(receipt_path: Path) -> dict[str, Any]:
    raw = receipt_path.read_bytes()
    try:
        text = raw.decode("utf-8")
        receipt = json.loads(text, object_pairs_hook=duplicate_guard)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VerificationError("receipt.json") from error
    require(isinstance(receipt, dict), "receipt.object")
    for marker in RAW_TEXT_MARKERS:
        require(marker not in text, "receipt.raw_text")
    require(
        set(receipt)
        == {
            "schema_version", "run_id", "scope", "state", "profile_id", "target",
            "measurement", "cells", "measurement_set_sha256", "visible_text_present",
            "user_document_opened", "hwp_process_created", "external_network_invoked",
            "registry_or_system_setting_changed", "computer_use_click_or_type_invoked",
            "actual_hangul_renderer", "other_pc_or_version", "product_complete",
        },
        "receipt.keys",
    )
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p06-05-current-font-metric-receipt/v1",
        "receipt.schema",
    )
    require(receipt.get("run_id") == receipt_path.parent.name, "receipt.run")
    require(receipt.get("scope") == "current_pc_named_synthetic_fixture_only", "receipt.scope")
    require(receipt.get("state") == "pass", "receipt.state")
    require(
        receipt.get("profile_id") == "hwpx-agent.font-metric.gdiplus-typographic-96dpi/1",
        "receipt.profile",
    )
    for claim in (
        "visible_text_present", "user_document_opened", "hwp_process_created",
        "external_network_invoked", "registry_or_system_setting_changed",
        "computer_use_click_or_type_invoked", "actual_hangul_renderer",
        "other_pc_or_version", "product_complete",
    ):
        require(receipt.get(claim) is False, f"receipt.{claim}")

    target = receipt.get("target")
    require(isinstance(target, dict), "target.object")
    require(
        target
        == {
            "hangul_build": "11.0.0.9136",
            "architecture": "x86",
            "executable_sha256": EXPECTED_HWP_SHA256,
            "font_file_name": "HANBatang.ttf",
            "font_file_bytes": 28_412_796,
            "font_file_sha256": EXPECTED_FONT_SHA256,
            "font_family": "함초롬바탕",
        },
        "target.identity",
    )
    hwp = expected_hwp_path().resolve(strict=True)
    font = expected_font_path().resolve(strict=True)
    require(hwp.is_file() and digest(hwp) == EXPECTED_HWP_SHA256, "target.hwp")
    require(
        font.is_file()
        and font.stat().st_size == 28_412_796
        and digest(font) == EXPECTED_FONT_SHA256,
        "target.font",
    )

    require(
        receipt.get("measurement")
        == {
            "provider": "System.Drawing.GDIPlus.GenericTypographic/1",
            "dpi": 96,
            "font_size_millipoints": 10_000,
            "repeat_count": 2,
            "conversion": "micrometers=round_away_from_zero(pixels*25400/96)",
        },
        "measurement.identity",
    )
    cells = receipt.get("cells")
    require(isinstance(cells, list) and len(cells) == 4, "cells.count")
    normalized: list[dict[str, Any]] = []
    for cell in cells:
        require(
            isinstance(cell, dict)
            and set(cell)
            == {
                "cell_id", "text_sha256", "minimum_content_width_micrometers",
                "preferred_content_width_micrometers", "line_height_micrometers",
            },
            "cell.shape",
        )
        cell_id = cell.get("cell_id")
        text_sha256 = cell.get("text_sha256")
        minimum = cell.get("minimum_content_width_micrometers")
        preferred = cell.get("preferred_content_width_micrometers")
        line_height = cell.get("line_height_micrometers")
        require(
            isinstance(cell_id, str)
            and cell_id in EXPECTED_TEXT_SHA256
            and text_sha256 == EXPECTED_TEXT_SHA256[cell_id]
            and HEX64.fullmatch(text_sha256) is not None,
            "cell.identity",
        )
        require(
            type(minimum) is int
            and type(preferred) is int
            and type(line_height) is int
            and 0 < minimum <= preferred <= 1_000_000_000
            and 0 < line_height <= 1_000_000_000,
            "cell.metric",
        )
        normalized.append(
            {
                "cell_id": cell_id,
                "text_sha256": text_sha256,
                "minimum_content_width_micrometers": minimum,
                "preferred_content_width_micrometers": preferred,
                "line_height_micrometers": line_height,
            }
        )
    require([cell["cell_id"] for cell in normalized] == sorted(EXPECTED_TEXT_SHA256), "cells.order")
    canonical = json.dumps(
        normalized, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    measurement_digest = hashlib.sha256(canonical).hexdigest()
    require(
        receipt.get("measurement_set_sha256")
        == measurement_digest
        == EXPECTED_MEASUREMENT_SET_SHA256,
        "measurement.digest",
    )
    return {
        "schema_version": "hwpx-agent.p06-05-current-font-metric-verification/v1",
        "state": "pass",
        "run_id": receipt["run_id"],
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "measurement_set_sha256": measurement_digest,
        "cell_count": len(normalized),
        "actual_hangul_renderer": False,
        "product_complete": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    arguments = parser.parse_args()
    try:
        path = resolve_receipt(arguments.receipt)
        result = validate(path)
    except (OSError, VerificationError) as error:
        code = str(error) if isinstance(error, VerificationError) else "verification.unavailable"
        print(json.dumps({"state": "fail", "code": code}, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
