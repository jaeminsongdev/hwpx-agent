from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_vs0_actual import VerificationError, verify_bundle  # noqa: E402


TEXT = "HWPX Agent VS-0 한글 2020 실제 열기 검증"


class Vs0ActualVerifierTests(unittest.TestCase):
    def make_bundle(self, root: Path) -> tuple[Path, Path, Path, Path]:
        request = {
            "schema_version": "hwpx-agent.vs0-create-request/v1",
            "idempotency_key": "test-key",
            "project_id": "test-project",
            "document_id": "test-document",
            "base_revision": "test-revision",
            "expected_head_generation": 1,
            "page_preset": "a4_portrait",
            "style": "default",
            "text": TEXT,
        }
        request_path = root / "request.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")

        temporary_artifact = root / "temporary.hwpx"
        entries = [
            ("mimetype", b"application/hwp+zip", zipfile.ZIP_STORED),
            ("version.xml", b"<version/>", zipfile.ZIP_STORED),
            ("Contents/header.xml", b"<header/>", zipfile.ZIP_DEFLATED),
            (
                "Contents/section0.xml",
                (
                    '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
                    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
                    f"<hp:p><hp:run><hp:t>{TEXT}</hp:t></hp:run></hp:p></hs:sec>"
                ).encode("utf-8"),
                zipfile.ZIP_DEFLATED,
            ),
            (
                "Preview/PrvText.txt",
                f"HWPX Agent VS-0\r\n{TEXT}".encode("utf-8"),
                zipfile.ZIP_DEFLATED,
            ),
            ("settings.xml", b"<settings/>", zipfile.ZIP_DEFLATED),
            ("Preview/PrvImage.png", b"\x89PNG\r\n\x1a\nfixture", zipfile.ZIP_STORED),
            ("META-INF/container.rdf", b"<rdf/>", zipfile.ZIP_DEFLATED),
            ("Contents/content.hpf", b"<package/>", zipfile.ZIP_DEFLATED),
            ("META-INF/container.xml", b"<container/>", zipfile.ZIP_DEFLATED),
            ("META-INF/manifest.xml", b"<manifest/>", zipfile.ZIP_DEFLATED),
        ]
        with zipfile.ZipFile(temporary_artifact, "w") as archive:
            for name, value, method in entries:
                archive.writestr(name, value, compress_type=method)
        artifact_sha256 = hashlib.sha256(temporary_artifact.read_bytes()).hexdigest()
        artifact_path = root / f"{artifact_sha256}.hwpx"
        temporary_artifact.rename(artifact_path)

        text_bytes = TEXT.encode("utf-8")
        trace = {
            "schema_version": "hwpx-agent.hancom-2020-roundtrip-trace/v1",
            "state": "pass",
            "fixture_ordinal": 0,
            "mode": "normalized",
            "input_sha256": artifact_sha256,
            "input_size": artifact_path.stat().st_size,
            "input_identity_subphase": "pass",
            "apartment_state": "STA",
            "automation_version_normalized": "11.0.0.9136",
            "text_sha256": hashlib.sha256(text_bytes).hexdigest(),
            "text_utf8_length": len(text_bytes),
            "expected_single_paragraph_match": True,
            "phases": {
                phase: "pass"
                for phase in (
                    "input_identity",
                    "com_create",
                    "version_check",
                    "document_add",
                    "document_open",
                    "text_read",
                    "document_close",
                    "quit",
                )
            },
            "error_code": None,
            "failed_phase": None,
            "exception_type": None,
            "exception_hresult": None,
            "exception_message_sha256": None,
            "quit_invoked": True,
            "input_modified": False,
            "output_saved": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
        }
        trace_path = root / "trace.json"
        trace_path.write_text(json.dumps(trace), encoding="utf-8")
        progress = {
            "schema_version": "hwpx-agent.hancom-roundtrip-progress/v1",
            "sequence": 17,
            "observed_utc": "2026-09-03T00:00:00Z",
            "process_id": 100,
            "apartment_state": "STA",
            "phase": "final_trace",
            "state": "complete",
        }
        progress_path = root / "progress.json"
        progress_path.write_text(json.dumps(progress), encoding="utf-8")
        return request_path, artifact_path, trace_path, progress_path

    def test_valid_bundle_passes_without_paths_or_text_in_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.make_bundle(Path(directory))
            result = verify_bundle(*paths)
            public = json.dumps(result, ensure_ascii=False)
            self.assertEqual(result["state"], "pass")
            self.assertNotIn(TEXT, public)
            self.assertNotIn(directory, public)

    def test_artifact_tamper_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.make_bundle(Path(directory))
            paths[1].write_bytes(paths[1].read_bytes() + b"tamper")
            with self.assertRaises(VerificationError):
                verify_bundle(*paths)

    def test_trace_text_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.make_bundle(Path(directory))
            trace = json.loads(paths[2].read_text(encoding="utf-8"))
            trace["expected_single_paragraph_match"] = False
            paths[2].write_text(json.dumps(trace), encoding="utf-8")
            with self.assertRaises(VerificationError):
                verify_bundle(*paths)

    def test_unknown_request_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.make_bundle(Path(directory))
            request = json.loads(paths[0].read_text(encoding="utf-8"))
            request["extra"] = True
            paths[0].write_text(json.dumps(request), encoding="utf-8")
            with self.assertRaises(VerificationError):
                verify_bundle(*paths)

    def test_duplicate_request_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.make_bundle(Path(directory))
            paths[0].write_text(
                '{"schema_version":"hwpx-agent.vs0-create-request/v1",'
                '"schema_version":"hwpx-agent.vs0-create-request/v1"}',
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                verify_bundle(*paths)


if __name__ == "__main__":
    unittest.main()
