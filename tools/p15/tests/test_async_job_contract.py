from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, relative: str):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


builder = load_module("p15_async_job_builder", "tools/p15/build_async_job_contract.py")
validator = load_module("p15_async_job_validator", "tools/p15/validate_async_job_contract.py")


class AsyncJobContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_async_job_contract.py", "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_passes_repository(self) -> None:
        self.assertEqual(validator.validate(ROOT), [])

    def test_contract_has_exact_closed_shape(self) -> None:
        contract = json.loads(
            (
                ROOT / "implementation/p15/p15-async-job-contract-v1.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(
            contract["async_submission_tools"], validator.EXPECTED_ASYNC_TOOLS
        )
        self.assertEqual(
            contract["required_behaviors"], validator.EXPECTED_BEHAVIORS
        )
        self.assertEqual(contract["rust_async_job_tests"], 11)

    def test_catalog_digest_remains_the_p15_02_value(self) -> None:
        contract = builder.build_contract(ROOT)
        self.assertEqual(
            contract["catalog_sha256"],
            "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001",
        )

    def test_source_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            clone = Path(temporary)
            contract = json.loads(
                (
                    ROOT / "implementation/p15/p15-async-job-contract-v1.json"
                ).read_text(encoding="utf-8")
            )
            required = {
                "implementation/p15/p15-async-job-contract-v1.json",
                "protocol/mcp/p15-public-tools-v1.json",
                "crates/mcp-control-plane/src/async_jobs.rs",
                "crates/mcp-control-plane/src/handler.rs",
                "crates/mcp-control-plane/tests/async_job_ux.rs",
            }
            required.update(entry["path"] for entry in contract["source_locks"])
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            with (clone / "crates/mcp-control-plane/src/async_jobs.rs").open(
                "a", encoding="utf-8"
            ) as stream:
                stream.write("\n// drift\n")
            self.assertIn("source_lock[14].digest", validator.validate(clone))

    def test_limits_match_rust_constants(self) -> None:
        source = (ROOT / "crates/mcp-control-plane/src/async_jobs.rs").read_text(
            encoding="utf-8"
        )
        for token in [
            "const MAX_JOBS: usize = 4_096;",
            "const MAX_JOURNAL_ENTRIES: u64 = 65_536;",
            "const MAX_JOURNAL_BYTES: u64 = 67_108_864;",
            "const MAX_EVENTS_PER_JOB: usize = 256;",
            "const MAX_EVENT_PAGE: usize = 200;",
        ]:
            self.assertIn(token, source)

    def test_old_catalog_and_handler_contract_are_not_rewritten(self) -> None:
        contract = builder.build_contract(ROOT)
        locks = {entry["path"]: entry["sha256"] for entry in contract["source_locks"]}
        self.assertEqual(
            locks["implementation/p15/p15-public-tool-schema-contract-v1.json"],
            "9e7099535bceced5295ce347afb4b9cc9a6dfa71db1f10d633ed9247d126681e",
        )
        self.assertEqual(
            locks["implementation/p15/p15-handler-contract-v1.json"],
            "f79dfeac599b11a122569e1796d428298f341f53f91d3893460c6d7c1d704f0a",
        )


if __name__ == "__main__":
    unittest.main()
