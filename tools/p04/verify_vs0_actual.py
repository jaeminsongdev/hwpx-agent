from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree


REQUEST_SCHEMA = "hwpx-agent.vs0-create-request/v1"
TRACE_SCHEMA = "hwpx-agent.hancom-2020-roundtrip-trace/v1"
PROGRESS_SCHEMA = "hwpx-agent.hancom-roundtrip-progress/v1"
RESULT_SCHEMA = "hwpx-agent.vs0-actual-verification/v1"
EXPECTED_BUILD = "11.0.0.9136"
MAX_JSON_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 1024 * 1024
MAX_EXPANDED_ENTRY_BYTES = 1024 * 1024
MAX_TOTAL_EXPANDED_BYTES = 2 * 1024 * 1024
MAX_IDENTIFIER_BYTES = 256
EXPECTED_ENTRIES = [
    "mimetype",
    "version.xml",
    "Contents/header.xml",
    "Contents/section0.xml",
    "Preview/PrvText.txt",
    "settings.xml",
    "Preview/PrvImage.png",
    "META-INF/container.rdf",
    "Contents/content.hpf",
    "META-INF/container.xml",
    "META-INF/manifest.xml",
]
EXPECTED_PHASES = {
    "input_identity",
    "com_create",
    "version_check",
    "document_add",
    "document_open",
    "text_read",
    "document_close",
    "quit",
}
REQUEST_FIELDS = {
    "schema_version",
    "idempotency_key",
    "project_id",
    "document_id",
    "base_revision",
    "expected_head_generation",
    "page_preset",
    "style",
    "text",
}
TRACE_FIELDS = {
    "schema_version",
    "state",
    "fixture_ordinal",
    "mode",
    "input_sha256",
    "input_size",
    "input_identity_subphase",
    "apartment_state",
    "automation_version_normalized",
    "text_sha256",
    "text_utf8_length",
    "expected_single_paragraph_match",
    "phases",
    "error_code",
    "failed_phase",
    "exception_type",
    "exception_hresult",
    "exception_message_sha256",
    "quit_invoked",
    "input_modified",
    "output_saved",
    "external_network_invoked",
    "registry_or_system_setting_changed",
}
PROGRESS_FIELDS = {
    "schema_version",
    "sequence",
    "observed_utc",
    "process_id",
    "apartment_state",
    "phase",
    "state",
}


class VerificationError(ValueError):
    pass


def fail(code: str) -> None:
    raise VerificationError(code)


def read_bounded(path: Path, maximum: int, code: str) -> bytes:
    try:
        size = path.stat().st_size
    except OSError:
        fail(code)
    if size <= 0 or size > maximum:
        fail(code)
    try:
        value = path.read_bytes()
    except OSError:
        fail(code)
    if len(value) != size:
        fail(code)
    return value


def read_json(path: Path, code: str) -> tuple[bytes, dict[str, object]]:
    raw = read_bounded(path, MAX_JSON_BYTES, code)

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                fail(code)
            result[key] = value
        return result

    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail(code)
    if not isinstance(value, dict):
        fail(code)
    return raw, value


def require_exact_fields(value: dict[str, object], expected: set[str], code: str) -> None:
    if set(value) != expected:
        fail(code)


def verify_request(request: dict[str, object]) -> tuple[str, str]:
    require_exact_fields(request, REQUEST_FIELDS, "VS0_ACTUAL_REQUEST_FIELDS_INVALID")
    text = request.get("text")
    identifier_fields = (
        "idempotency_key",
        "project_id",
        "document_id",
        "base_revision",
    )
    if (
        request.get("schema_version") != REQUEST_SCHEMA
        or any(
            not isinstance(request.get(field), str)
            or not request[field]
            or len(str(request[field]).encode("utf-8")) > MAX_IDENTIFIER_BYTES
            for field in identifier_fields
        )
        or type(request.get("expected_head_generation")) is not int
        or request.get("expected_head_generation") != 1
        or request.get("page_preset") != "a4_portrait"
        or request.get("style") != "default"
        or not isinstance(text, str)
        or not text
        or len(text.encode("utf-8")) > 4096
        or any(
            unicodedata.category(character) == "Cc"
            or (ord(character) & 0xFFFF) in (0xFFFE, 0xFFFF)
            for character in text
        )
    ):
        fail("VS0_ACTUAL_REQUEST_INVALID")
    canonical_text = unicodedata.normalize("NFC", text)
    return canonical_text, hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def verify_artifact(path: Path, expected_text: str) -> tuple[bytes, str]:
    raw = read_bounded(path, MAX_ARTIFACT_BYTES, "VS0_ACTUAL_ARTIFACT_INVALID")
    digest = hashlib.sha256(raw).hexdigest()
    if path.name != f"{digest}.hwpx":
        fail("VS0_ACTUAL_ARTIFACT_NAME_MISMATCH")
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.namelist() != EXPECTED_ENTRIES or archive.testzip() is not None:
                fail("VS0_ACTUAL_ARCHIVE_SHAPE_INVALID")
            infos = archive.infolist()
            if (
                any(
                    info.file_size <= 0 or info.file_size > MAX_EXPANDED_ENTRY_BYTES
                    for info in infos
                )
                or sum(info.file_size for info in infos) > MAX_TOTAL_EXPANDED_BYTES
            ):
                fail("VS0_ACTUAL_ARCHIVE_LIMIT_EXCEEDED")
            if (
                archive.getinfo("mimetype").compress_type != zipfile.ZIP_STORED
                or archive.read("mimetype") != b"application/hwp+zip"
                or archive.getinfo("version.xml").compress_type != zipfile.ZIP_STORED
                or not archive.read("Preview/PrvImage.png").startswith(b"\x89PNG\r\n\x1a\n")
            ):
                fail("VS0_ACTUAL_ARCHIVE_ENCODING_INVALID")
            xml_parts = [
                "version.xml",
                "Contents/header.xml",
                "Contents/section0.xml",
                "settings.xml",
                "META-INF/container.rdf",
                "Contents/content.hpf",
                "META-INF/container.xml",
                "META-INF/manifest.xml",
            ]
            parsed = {
                name: ElementTree.fromstring(archive.read(name)) for name in xml_parts
            }
            section = parsed["Contents/section0.xml"]
            paragraphs = section.findall(
                ".//{http://www.hancom.co.kr/hwpml/2011/paragraph}p"
            )
            text_nodes = section.findall(
                ".//{http://www.hancom.co.kr/hwpml/2011/paragraph}t"
            )
            if (
                len(paragraphs) != 1
                or len(text_nodes) != 1
                or unicodedata.normalize("NFC", text_nodes[0].text or "") != expected_text
                or unicodedata.normalize(
                    "NFC", archive.read("Preview/PrvText.txt").decode("utf-8")
                )
                != f"HWPX Agent VS-0\r\n{expected_text}"
            ):
                fail("VS0_ACTUAL_SEMANTIC_CONTENT_MISMATCH")
            package_text = "\n".join(
                archive.read(name).decode("utf-8") for name in xml_parts
            ).casefold()
            if any(
                token in package_text
                for token in ("creator", "lastsaveby", "createddate", "modifieddate")
            ):
                fail("VS0_ACTUAL_PERSONAL_METADATA_PRESENT")
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile, ElementTree.ParseError):
        fail("VS0_ACTUAL_ARCHIVE_INVALID")
    return raw, digest


def verify_trace(
    trace: dict[str, object], artifact_sha256: str, artifact_size: int, text_sha256: str, text_size: int
) -> None:
    require_exact_fields(trace, TRACE_FIELDS, "VS0_ACTUAL_TRACE_FIELDS_INVALID")
    phases = trace.get("phases")
    if not isinstance(phases, dict) or set(phases) != EXPECTED_PHASES:
        fail("VS0_ACTUAL_TRACE_PHASES_INVALID")
    if (
        trace.get("schema_version") != TRACE_SCHEMA
        or trace.get("state") != "pass"
        or type(trace.get("fixture_ordinal")) is not int
        or trace.get("fixture_ordinal") != 0
        or trace.get("mode") != "normalized"
        or trace.get("input_sha256") != artifact_sha256
        or type(trace.get("input_size")) is not int
        or trace.get("input_size") != artifact_size
        or trace.get("input_identity_subphase") != "pass"
        or trace.get("apartment_state") != "STA"
        or trace.get("automation_version_normalized") != EXPECTED_BUILD
        or trace.get("text_sha256") != text_sha256
        or type(trace.get("text_utf8_length")) is not int
        or trace.get("text_utf8_length") != text_size
        or trace.get("expected_single_paragraph_match") is not True
        or any(state != "pass" for state in phases.values())
        or trace.get("quit_invoked") is not True
        or trace.get("input_modified") is not False
        or trace.get("output_saved") is not False
        or trace.get("external_network_invoked") is not False
        or trace.get("registry_or_system_setting_changed") is not False
        or any(
            trace.get(field) is not None
            for field in (
                "error_code",
                "failed_phase",
                "exception_type",
                "exception_hresult",
                "exception_message_sha256",
            )
        )
    ):
        fail("VS0_ACTUAL_TRACE_MISMATCH")


def verify_progress(progress: dict[str, object]) -> None:
    require_exact_fields(progress, PROGRESS_FIELDS, "VS0_ACTUAL_PROGRESS_FIELDS_INVALID")
    if (
        progress.get("schema_version") != PROGRESS_SCHEMA
        or type(progress.get("sequence")) is not int
        or int(progress["sequence"]) < 17
        or type(progress.get("process_id")) is not int
        or int(progress["process_id"]) <= 0
        or progress.get("apartment_state") != "STA"
        or progress.get("phase") != "final_trace"
        or progress.get("state") != "complete"
    ):
        fail("VS0_ACTUAL_PROGRESS_MISMATCH")


def verify_bundle(
    request_path: Path, artifact_path: Path, trace_path: Path, progress_path: Path
) -> dict[str, object]:
    request_raw, request = read_json(request_path, "VS0_ACTUAL_REQUEST_READ_FAILED")
    trace_raw, trace = read_json(trace_path, "VS0_ACTUAL_TRACE_READ_FAILED")
    progress_raw, progress = read_json(progress_path, "VS0_ACTUAL_PROGRESS_READ_FAILED")
    expected_text, text_sha256 = verify_request(request)
    artifact_raw, artifact_sha256 = verify_artifact(artifact_path, expected_text)
    verify_trace(
        trace,
        artifact_sha256,
        len(artifact_raw),
        text_sha256,
        len(expected_text.encode("utf-8")),
    )
    verify_progress(progress)
    correlation = hashlib.sha256(
        b"\0".join(
            hashlib.sha256(value).digest()
            for value in (request_raw, artifact_raw, trace_raw, progress_raw)
        )
    ).hexdigest()
    return {
        "schema_version": RESULT_SCHEMA,
        "state": "pass",
        "target_profile_id": "hancom-hangul-2020-secondary",
        "exact_build": EXPECTED_BUILD,
        "artifact_sha256": artifact_sha256,
        "artifact_size": len(artifact_raw),
        "text_sha256": text_sha256,
        "text_utf8_length": len(expected_text.encode("utf-8")),
        "all_phases_passed": True,
        "input_modified": False,
        "output_saved": False,
        "bundle_correlation_sha256": correlation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--progress", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify_bundle(args.request, args.artifact, args.trace, args.progress)
    except VerificationError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
