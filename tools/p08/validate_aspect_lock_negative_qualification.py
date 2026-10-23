from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-21-aspect-lock-negative-qualification.current-2020.v1.json"
)
SOURCE_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-17-object-remainder-hwpx-source-qualification.current-2020.v1.json"
)

DIGEST = re.compile(r"[0-9a-f]{64}")
TARGET = {
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_relative_to_program_files_x86": "HNC/Office 2020/HOffice110/Bin/Hwp.exe",
    "executable_byte_len": 2321432,
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}
MODEL_FILES = [
    {
        "path": "OWPML/Class/Para/AbstractShapeObjectType.h",
        "byte_len": 3235,
        "sha256": "413b55dec690e87f944c5076d83a769071425ecf4f2344dc128e25af7b748839",
    },
    {
        "path": "OWPML/Class/Para/AbstractShapeObjectType.cpp",
        "byte_len": 4905,
        "sha256": "16c4a18de9c05de64ed1fe25b57b8a1fb4f81ffd9da9cb523aa5a109fbe9d45a",
    },
    {
        "path": "OWPML/Class/Para/sz.h",
        "byte_len": 2138,
        "sha256": "78f3c84b91ddbd10f7bde248577aec8c41f7faeb4f962a013b6d6a2d15d8e433",
    },
    {
        "path": "OWPML/Class/Para/sz.cpp",
        "byte_len": 2579,
        "sha256": "1deee5880faff29b983059b1e2e3d679ba0a08451761a65fbac30e5fc3396f30",
    },
]
AUTOMATION_DOCUMENTS = [
    {
        "path": "hwp-automation/ActionTable_2504.pdf",
        "sha256": "bb876a95ea4e0f4b052c94188a1390b5f981161223759f59f52fc324c8130a87",
        "strong_aspect_lock_token_hits": 0,
        "protect_size_token_hits": 1,
    },
    {
        "path": "hwp-automation/ParameterSetTable_2504.pdf",
        "sha256": "6fa10e0ae69711af99a03e54c321c6c922796bd943badf8c21b2c7dfb780ad6e",
        "strong_aspect_lock_token_hits": 0,
        "protect_size_token_hits": 2,
    },
    {
        "path": "hwp-automation/ParameterSetObject.pdf",
        "sha256": "7cbf536a8814cf8165a1614edfd9816173bb1bd7c9e585821d776563e2bdb674",
        "strong_aspect_lock_token_hits": 0,
        "protect_size_token_hits": 3,
    },
    {
        "path": "hwp-automation/HwpAutomation_2504.pdf",
        "sha256": "917142de2704ae037b0132f5a344ce5331b1fd96cc19dd574666aaacfbf0268c",
        "strong_aspect_lock_token_hits": 0,
        "protect_size_token_hits": 0,
    },
]
INSTALLED_SURFACE = {
    "relative_to_program_files_x86": (
        "HNC/Office 2020/HOffice110/Bin/UxXml/Hancom2016/Hwp/Dlg/ko-KR/"
        "hwp_object_property_tabitem_basic.xml"
    ),
    "byte_len": 13566,
    "sha256": "272cb78a1bdc21a09b84b038470d410777243477be2d9ca7a5f6a2413365556e",
    "protect_size_control_id_hits": 1,
    "protect_size_caption_hits": 1,
    "aspect_ratio_control_token_hits": 0,
}


class QualificationError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise QualificationError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def _load(path: Path, *, root: Path = ROOT) -> dict[str, Any]:
    data = (root / path).read_bytes()
    if not data or len(data) > 1024 * 1024:
        raise QualificationError(f"qualification_size:{path.as_posix()}")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"qualification_json:{path.as_posix()}") from error
    if not isinstance(value, dict):
        raise QualificationError(f"qualification_shape:{path.as_posix()}")
    return value


def load(path: Path = QUALIFICATION, *, root: Path = ROOT) -> dict[str, Any]:
    return _load(path, root=root)


def _exact_keys(value: Any, expected: set[str], context: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise QualificationError(f"shape_drift:{context}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _program_files_x86() -> Path:
    value = os.environ.get("ProgramFiles(x86)")
    if not value:
        raise QualificationError("program_files_x86_unavailable")
    return Path(value)


def _validate_source_qualification(*, root: Path = ROOT) -> None:
    source = _load(SOURCE_QUALIFICATION, root=root)
    official = source.get("official_sources")
    if not isinstance(official, dict):
        raise QualificationError("source_qualification_official_sources")
    model = official.get("owpml_model")
    archive = official.get("automation_archive")
    if not isinstance(model, dict) or (
        model.get("repository") != "https://github.com/hancom-io/hwpx-owpml-model"
        or model.get("commit") != "1453388472c703a4b299a0834f425cdac16644b9"
    ):
        raise QualificationError("source_qualification_model")
    expected_documents = [
        {"path": item["path"], "sha256": item["sha256"]}
        for item in AUTOMATION_DOCUMENTS
    ]
    if not isinstance(archive, dict) or (
        archive.get("repository") != "https://github.com/hancom-io/devcenter-archive"
        or archive.get("commit") != "213c7faad552b4853b525887e36accb6025e837b"
        or archive.get("documents") != expected_documents
    ):
        raise QualificationError("source_qualification_automation")
    if source.get("native_map", {}).get("OBJ-044") != (
        "CAPABILITY_UNAVAILABLE_FOR_TARGET:protect_size_is_not_aspect_lock"
    ):
        raise QualificationError("source_qualification_obj044")


def _validate_installed(value: dict[str, Any]) -> None:
    base = _program_files_x86()
    executable = base / Path(TARGET["executable_relative_to_program_files_x86"])
    surface = base / Path(INSTALLED_SURFACE["relative_to_program_files_x86"])
    if not executable.is_file() or executable.stat().st_size != TARGET["executable_byte_len"]:
        raise QualificationError("installed_executable_identity")
    if _sha256(executable) != TARGET["executable_sha256"]:
        raise QualificationError("installed_executable_hash")
    if not surface.is_file() or surface.stat().st_size != INSTALLED_SURFACE["byte_len"]:
        raise QualificationError("installed_surface_identity")
    if _sha256(surface) != INSTALLED_SURFACE["sha256"]:
        raise QualificationError("installed_surface_hash")
    text = surface.read_text(encoding="utf-8-sig")
    if text.count("IDC_CHECK_PROTECT_SIZE") != 1 or text.count("IDS_FixSize") != 1:
        raise QualificationError("installed_protect_size_surface")
    lowered = text.casefold()
    if sum(lowered.count(token) for token in ("aspect", "ratio", "proportion")) != 0:
        raise QualificationError("installed_aspect_surface")
    if value["installed_surface"] != INSTALLED_SURFACE:
        raise QualificationError("installed_surface_contract")


def validate(
    qualification_override: dict[str, Any] | None = None,
    *,
    verify_installed: bool = True,
    verify_source_qualification: bool = True,
) -> dict[str, Any]:
    value = qualification_override if qualification_override is not None else load()
    _exact_keys(
        value,
        {
            "schema_version", "task", "recorded_date", "feature_id", "target",
            "official_model", "official_automation", "installed_surface", "decision",
            "execution", "privacy", "claims",
        },
        "root",
    )
    if (
        value["schema_version"] != "hwpx-agent.p08-aspect-lock-negative-qualification/v1"
        or value["task"] != "P08-21"
        or value["recorded_date"] != "2026-09-15"
        or value["feature_id"] != "OBJ-044"
    ):
        raise QualificationError("identity")
    if value["target"] != TARGET:
        raise QualificationError("target")
    model = value["official_model"]
    _exact_keys(
        model,
        {
            "repository", "commit", "files", "reviewed_fields",
            "aspect_lock_field_count", "rectangle_ratio_rejected_as_equivalent",
        },
        "official_model",
    )
    if model != {
        "repository": "https://github.com/hancom-io/hwpx-owpml-model",
        "commit": "1453388472c703a4b299a0834f425cdac16644b9",
        "files": MODEL_FILES,
        "reviewed_fields": {
            "AbstractShapeObjectType.attributes": [
                "id", "zOrder", "numberingType", "textWrap", "textFlow", "lock", "dropcapstyle",
            ],
            "sz.attributes": ["width", "widthRelTo", "height", "heightRelTo", "protect"],
        },
        "aspect_lock_field_count": 0,
        "rectangle_ratio_rejected_as_equivalent": True,
    }:
        raise QualificationError("official_model")
    automation = value["official_automation"]
    if automation != {
        "repository": "https://github.com/hancom-io/devcenter-archive",
        "commit": "213c7faad552b4853b525887e36accb6025e837b",
        "documents": AUTOMATION_DOCUMENTS,
        "strong_aspect_lock_tokens": ["AspectLock", "KeepRatio", "AspectRatio", "LockAspect"],
        "exact_binding_found": False,
    }:
        raise QualificationError("official_automation")
    if any(not DIGEST.fullmatch(item["sha256"]) for item in MODEL_FILES + AUTOMATION_DOCUMENTS):
        raise QualificationError("official_digest")
    if value["installed_surface"] != INSTALLED_SURFACE:
        raise QualificationError("installed_surface")
    if value["decision"] != {
        "status": "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        "reason": "no_persistent_native_or_exact_automation_aspect_lock_surface",
        "non_equivalent_surface": "ProtectSize",
        "non_equivalent_reason": "fixed_size_is_not_aspect_ratio_lock_for_future_resize",
        "direct_lowering": "fail_closed",
        "automation_binding": "unavailable_with_reason",
        "catalog_contract_retained": True,
    }:
        raise QualificationError("decision")
    if value["execution"] != {
        "hwp_launched": False,
        "action_executed": False,
        "document_created_or_opened": False,
        "document_mutated": False,
        "network_used_for_target_runtime": False,
    }:
        raise QualificationError("execution")
    if value["privacy"] != {
        "user_document_scanned": False,
        "document_content_present": False,
        "private_absolute_paths_present": False,
        "secret_present": False,
    }:
        raise QualificationError("privacy")
    if value["claims"] != {
        "exact_official_source_negative_qualification": True,
        "exact_installed_surface_negative_qualification": True,
        "actual_target_runtime": False,
        "direct_hwpx_mapping": False,
        "automation_runtime_binding": False,
        "differential": False,
        "row_green": False,
        "p08_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        raise QualificationError("claims")
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if ":\\" in serialized or "D:/" in serialized or "D:\\" in serialized:
        raise QualificationError("private_path_leak")
    if verify_source_qualification:
        _validate_source_qualification()
    if verify_installed:
        _validate_installed(value)
    return {
        "schema_version": "hwpx-agent.p08-aspect-lock-negative-qualification-validation/v1",
        "state": "pass",
        "task": "P08-21",
        "feature_id": "OBJ-044",
        "decision": "CAPABILITY_UNAVAILABLE_FOR_TARGET",
        "exact_official_source_negative_qualification": True,
        "exact_installed_surface_negative_qualification": True,
        "actual_target_runtime": "not_run",
        "direct_hwpx_mapping": "unavailable",
        "automation_binding": "unavailable_with_reason",
        "row": "non_green",
        "p08": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    try:
        result = validate()
    except (QualificationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
