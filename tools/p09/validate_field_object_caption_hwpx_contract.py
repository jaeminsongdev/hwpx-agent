#!/usr/bin/env python3
"""Pin the caption composition profile without promoting synthetic evidence."""
from __future__ import annotations

import copy
import base64
import hashlib
import json
from pathlib import Path
import stat
from typing import Any

if __package__:
    from . import validate_field_auto_number_hwpx_contract as numeric
else:
    import validate_field_auto_number_hwpx_contract as numeric

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-field-object-caption-hwpx-v2.json"
QUALIFICATION = "implementation/p09/evidence/p09-18-field-object-caption-hwpx-source-qualification.20261002-r02.v2.json"
POLICY = "implementation/p09/P09-18_FIELD_OBJECT_CAPTION_HWPX_POLICY.v2.md"
REPORT = "implementation/p09/P09-18_FIELD_OBJECT_CAPTION_HWPX_REPORT.v2.md"
MIGRATION = "protocol/migrations/p09-field-object-caption-hwpx-v1-to-v2.md"
SNAPSHOT = "implementation/p09/evidence/p09-18-object-caption-source.20261002-r01.snapshot.json"
SNAPSHOT_SHA256 = "df4910ae5a54194425f32e67efd6bfa94215aee99cf756b89a325207cc1f6a9e"
PROFILE = "hwpx-agent.field-object-caption-hwpx.hwpml-2011-digit/v1"
OFFICIAL_BASE = "fixtures/target-build/official-source-cache/hwpx-owpml-model-145338"
SOURCE_SHA256 = dict(numeric.SOURCE_SHA256)
IMPLEMENTATION_SHA256 = {
    "crates/hwpx-package/src/field_object_caption_hwpx.rs": "2dd63a557787ffe1f84a0c9f49c7d0ace89af22037ade6ee8d51db380835adda",
    "crates/hwpx-package/tests/field_object_caption_hwpx.rs": "589e4d08b4045abd85ccb89f8ac4b7d624e5cc5f2327953779ba42288bae23d9",
    **numeric.IMPLEMENTATION_SHA256,
}
OFFICIAL_SHA256 = {
    "OWPML/Class/enumdef.h": "1c86392c934ac85f7ddd85c710b76be7649403a8404bce146db52558a0b95457",
    "OWPML/Class/Para/AbstractShapeObjectType.cpp": "16c4a18de9c05de64ed1fe25b57b8a1fb4f81ffd9da9cb523aa5a109fbe9d45a",
    "OWPML/Class/Para/caption.cpp": "8805053557991e1a48b9ecb6a5a831f40ed110207473e07233a15939814cdac6",
    "OWPML/Class/Para/AutoNumNewNumType.cpp": "58dd79b1e927b832868cf77c4ff089a3cab269c327a23e0a5aac0e21ecefbcf8",
    "OWPML/Class/Para/AutoNumFormatType.cpp": "86752d873fe366e3f72d8e9f50a71d8e29cfec712663fbaf4079d7a664c67a2c",
    "OWPML/Class/Para/PictureType.cpp": "07475a21f4895f9f6f6d3c566155aedf494a3782976a6ce399bcc4e056b8babe",
    "OWPML/Class/Para/TableType.cpp": "d309be141175faf18bb922b9bddb2344bbb018bfd5764fc025c1323960d4911d",
    "OWPML/Class/Para/EquationType.cpp": "b7b446ce33172106b9f94de024094804db562cd522ab3e52e7b92c398d16bbf7",
    "OWPML/Class/Para/RectangleType.cpp": "7c9ec1256fa01482afc2d0519f26ac680987ff466c693e7f7022650a7d339dc4",
    "OWPML/Class/Para/EllipseType.cpp": "511a51b77ba63a5b68c15c55d69d4bbad8b0c25e7a5cc5d316c8c26c994f2ce0",
    "OWPML/Class/Para/LineType.cpp": "4611bf677bc1367a41300ff3eb447c62fb4ca1e1fbda6cae62bf68cc032cb732",
    "OWPML/Class/Para/ArcType.cpp": "83670263bafa76656b6b6ea0cce9fb3d232d6d6756e18288c999948a7bef0f6a",
    "OWPML/Class/Para/PolygonType.cpp": "c08cc1c0f7581b02e00e3354eb411fe870510344914d26abb806567cda69a8bf",
    "OWPML/Class/Para/CurveType.cpp": "f80eb27d2f4c177790eb759766fd38396c6e468529fe2db5d3e397415481b3d5",
    "OWPML/Class/Para/ConnectLineType.cpp": "06591aa904936c19cabb0f5d64d64f3b26695c5adce9c9ed8feb16c1c0e7de24",
}
PUBLIC_EXPORT = {
    "path": "crates/hwpx-package/src/lib.rs",
    "markers": ["mod field_object_caption_hwpx;", "pub use field_object_caption_hwpx::{"],
}
BOUNDARY = {
    "static_caption_composition": True,
    "synthetic_object_shell_tests": True,
    "typed_projection_readback": True,
    "outside_caption_byte_preserved": True,
    "application_owned_sequence_derivation": False,
    "complete_native_objects": False,
    "complete_package_hwpx": False,
    "actual_hangul": False,
    "semantic_save_reopen": False,
    "render": False,
    "differential": False,
    "green_rows": 0,
    "p09_complete": False,
    "product_complete": False,
}
ADMITTED = {
    "scope": "one_existing_caption_one_digit_object_field",
    "object_selector": "unique_native_u32_id_direct_run_child_and_kind",
    "picture_names": ["pic", "rect", "ellipse", "line", "arc", "polygon", "curve", "connectLine"],
    "table_name": "tbl",
    "equation_name": "equation",
    "numbering_types": ["PICTURE", "TABLE", "EQUATION"],
    "lock": "0",
    "caption": "one_direct_caption_one_direct_subList_complete_paragraph_map",
    "namespace": "root_inherited_with_only_exact_redundant_ancestor_declarations",
    "instid_required": False,
    "composition": "reuse_sealed_field_auto_number_plan_on_exact_caption_view",
    "binding": "full_section_object_caption_selector_state_flow_map_and_two_plan_hashes",
    "preservation": "only_legacy_verified_caption_delta_every_other_byte_exact",
    "limits": "inherited_finite_field_auto_number_and_state_limits",
    "fallback": "none_fail_closed_no_partial_output",
}


def expected_contract() -> dict[str, Any]:
    return copy.deepcopy({
        "schema_version": "hwpx-agent.p09-field-object-caption-hwpx-contract/v2",
        "task": "P09-18", "profile": PROFILE,
        "policy": POLICY, "report": REPORT, "migration": MIGRATION,
        "qualification": QUALIFICATION,
        "predecessor_source_snapshot": {"path": SNAPSHOT, "sha256": SNAPSHOT_SHA256},
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_sha256": SOURCE_SHA256,
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "public_export": PUBLIC_EXPORT,
        "admitted_profile": ADMITTED,
        "evidence_boundary": BOUNDARY,
        "matrix_effect": "none_REF_008_and_REF_009_remain_static_integration_non_green",
    })


def expected_qualification() -> dict[str, Any]:
    return copy.deepcopy({
        "schema_version": "hwpx-agent.p09-field-object-caption-hwpx-source-qualification/v2",
        "task": "P09-18", "profile": PROFILE, "base_commit": numeric.BASE_COMMIT,
        "official_source": {
            "repository": numeric.OFFICIAL_REPOSITORY,
            "commit": numeric.OFFICIAL_COMMIT,
            "reviewed_sha256": OFFICIAL_SHA256,
        },
        "implementation_sha256": IMPLEMENTATION_SHA256,
        "public_export": PUBLIC_EXPORT,
        "tests": {"caption_public": "9/9 PASS", "caption_private_tamper": "1/1 PASS", "focused_clippy": "PASS"},
        "claims": BOUNDARY,
    })


def bounded_file(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or path.drive or ".." in path.parts:
        raise ValueError("invalid_path")
    cursor = root.resolve()
    for part in path.parts:
        cursor = cursor / part
        info = cursor.lstat()
        if cursor.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("linked_path")
    if not cursor.is_file() or not 0 < cursor.stat().st_size <= 8 * 1024 * 1024:
        raise ValueError("invalid_file")
    return cursor


def load(root: Path, relative: str) -> Any:
    return json.loads(bounded_file(root, relative).read_text(encoding="utf-8"), object_pairs_hook=numeric.duplicate_guard)


def exact_json(value: Any, expected: Any) -> bool:
    # Python's True == 1 is not a schema-equivalent boolean claim.
    return json.dumps(value, sort_keys=True, allow_nan=False) == json.dumps(expected, sort_keys=True, allow_nan=False)


def check_hashes(root: Path, expected: dict[str, str], error: str, errors: list[str], *, canonical: bool = False) -> None:
    for relative, digest in expected.items():
        try:
            data = bounded_file(root, relative).read_bytes()
            if canonical:
                data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            if hashlib.sha256(data).hexdigest() != digest:
                errors.append(error)
        except (OSError, ValueError):
            errors.append(error)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        # Exact schemas prevent weakened profiles, unexpected keys and claim promotion.
        if not exact_json(load(root, CONTRACT), expected_contract()):
            errors.append("contract_mismatch")
        if not exact_json(load(root, QUALIFICATION), expected_qualification()):
            errors.append("qualification_mismatch")
    except (OSError, ValueError, UnicodeError):
        errors.append("contract_or_qualification_json")
    check_hashes(root, SOURCE_SHA256, "source_lock_digest", errors, canonical=True)
    check_hashes(root, IMPLEMENTATION_SHA256, "implementation_digest", errors)
    check_hashes(root, {SNAPSHOT: SNAPSHOT_SHA256}, "predecessor_snapshot_digest", errors)
    try:
        snapshot = load(root, SNAPSHOT)
        files = snapshot["files"]
        if snapshot["schema_version"] != "hwpx-agent.p09-18-immutable-source-snapshot/v1" or len(files) != 3:
            errors.append("predecessor_snapshot_shape")
        for item in files:
            if item["encoding"] != "base64" or hashlib.sha256(base64.b64decode(item["bytes"], validate=True)).hexdigest() != item["sha256"]:
                errors.append("predecessor_snapshot_payload")
    except (OSError, ValueError, UnicodeError, KeyError, TypeError):
        errors.append("predecessor_snapshot_payload")
    check_hashes(root, {f"{OFFICIAL_BASE}/{path}": digest for path, digest in OFFICIAL_SHA256.items()}, "official_source_digest", errors)
    try:
        source = bounded_file(root, PUBLIC_EXPORT["path"]).read_text(encoding="utf-8")
        if any(marker not in source for marker in PUBLIC_EXPORT["markers"]):
            errors.append("public_export")
    except (OSError, ValueError, UnicodeError):
        errors.append("public_export")
    for relative, markers in {
        POLICY: ("existing caption", "actual_hangul=false", "product_complete=false"),
        REPORT: ("9/9 PASS", "green_rows=0", "synthetic object shells"),
        MIGRATION: ("v1 predecessor preserved", "fail closed", "P09-16"),
    }.items():
        try:
            document = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(marker not in document for marker in markers):
                errors.append("document_marker")
        except (OSError, ValueError, UnicodeError):
            errors.append("document_path")
    return {
        "schema_version": "hwpx-agent.p09-field-object-caption-hwpx-validation/v1",
        "state": "fail" if errors else "pass", "errors": sorted(set(errors)),
        "implementation_locks": len(IMPLEMENTATION_SHA256),
        "official_locks": len(OFFICIAL_SHA256), "source_locks": len(SOURCE_SHA256),
        "actual_hangul": "not_run", "semantic_save_reopen": "not_run",
        "render": "not_run", "differential": "not_run",
        "green_rows": 0, "p09": "in_progress", "product_complete": False,
    }


def main() -> int:
    response = validate()
    print(json.dumps(response, sort_keys=True, separators=(",", ":")))
    return 0 if response["state"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
