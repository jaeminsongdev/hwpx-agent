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


builder = load_module("p15_handler_builder", "tools/p15/build_handler_contract.py")
validator = load_module("p15_handler_validator", "tools/p15/validate_handler_contract.py")


class HandlerContractTests(unittest.TestCase):
    def test_generated_contract_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/p15/build_handler_contract.py", "--check"],
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
            (ROOT / "implementation/p15/p15-handler-contract-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(set(contract), validator.EXPECTED_KEYS)
        self.assertEqual(contract["handler_sequence"], validator.EXPECTED_SEQUENCE)
        self.assertEqual(contract["limits"]["public_tools"], 18)
        self.assertEqual(contract["rust_contract_tests"], 16)

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
                (ROOT / "implementation/p15/p15-handler-contract-v1.json").read_text(
                    encoding="utf-8"
                )
            )
            required = {
                "implementation/p15/p15-handler-contract-v1.json",
                "protocol/mcp/p15-public-tools-v1.json",
                "crates/mcp-control-plane/src/handler.rs",
                "crates/mcp-control-plane/src/strict_json.rs",
                "crates/mcp-control-plane/Cargo.toml",
                "Cargo.toml",
                "crates/mcp-control-plane/tests/handler_contract.rs",
            }
            required.update(entry["path"] for entry in contract["source_locks"])
            for relative in required:
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            with (clone / "crates/mcp-control-plane/src/handler.rs").open(
                "a", encoding="utf-8"
            ) as stream:
                stream.write("\n// drift\n")
            self.assertIn("source_lock[9].digest", validator.validate(clone))

    def test_dispatch_is_singular_and_after_authorization(self) -> None:
        source = (ROOT / "crates/mcp-control-plane/src/handler.rs").read_text(
            encoding="utf-8"
        )
        self.assertEqual(source.count("self.gateway.dispatch(call)"), 1)
        self.assertLess(source.index(".policy.authorize("), source.index(".gateway.dispatch("))
        self.assertLess(source.index(".gateway.dispatch("), source.index("output_is_valid("))

    def test_transport_and_backend_execution_are_outside_handler(self) -> None:
        source = (ROOT / "crates/mcp-control-plane/src/handler.rs").read_text(
            encoding="utf-8"
        )
        for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
