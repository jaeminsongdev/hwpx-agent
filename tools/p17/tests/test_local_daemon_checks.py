from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_local_daemon_checks as checks  # noqa: E402


class LocalDaemonChecksTests(unittest.TestCase):
    def test_sources_are_unique_present_and_cover_the_boundary(self) -> None:
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)
        for required in (
            "crates/local-companion-daemon/src/lib.rs",
            "crates/local-companion-daemon/src/main.rs",
            "crates/local-companion-daemon/tests/sandbox.rs",
            "protocol/private/p17-local-daemon-v1.json",
        ):
            self.assertIn(required, checks.SOURCES)

    def test_checks_keep_actual_hangul_plugin_and_network_separate(self) -> None:
        source = (checks.ROOT / "tools/p17/run_local_daemon_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"actual_codex_plugin": False', source)
        self.assertIn('"network_used": False', source)
        self.assertNotIn("shell=True", source)

    def test_receipt_writer_preserves_canonical_lf_bytes(self) -> None:
        source = (checks.ROOT / "tools/p17/run_local_daemon_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('(canonical(receipt) + "\\n").encode("utf-8")', source)
        self.assertNotIn('(run_dir / "receipt.json").write_text', source)

    def test_response_validator_requires_exact_success_and_error_shapes(self) -> None:
        success = {
            "protocol_version": checks.PROTOCOL_VERSION,
            "request_id": "one",
            "ok": True,
            "result": {},
        }
        self.assertEqual(checks.validate_response(success, "one", True), success)
        with self.assertRaises(checks.AcceptanceError):
            checks.validate_response({**success, "extra": True}, "one", True)
        failure = {
            "protocol_version": checks.PROTOCOL_VERSION,
            "request_id": "two",
            "ok": False,
            "error": "request_rejected",
        }
        self.assertEqual(checks.validate_response(failure, "two", False), failure)


if __name__ == "__main__":
    unittest.main()
