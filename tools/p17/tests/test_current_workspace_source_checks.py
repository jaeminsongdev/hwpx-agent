from __future__ import annotations

from pathlib import Path
import sys
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import run_current_workspace_source_checks as checks  # noqa: E402


class CurrentWorkspaceSourceChecksTests(unittest.TestCase):
    def test_pinned_contracts_and_source_inventory_are_exact(self) -> None:
        contracts = checks.load_pinned_contracts(checks.ROOT)
        self.assertEqual(set(contracts), set(checks.PINNED_CONTRACTS))
        expectations, main = checks.source_expectations(contracts)
        self.assertIn("Cargo.lock", expectations)
        self.assertIn("Cargo.lock", main)
        self.assertIn("tools/p16/integrated_source_qualification.py", expectations)
        self.assertEqual(len(checks.SOURCES), len(set(checks.SOURCES)))
        for relative in checks.SOURCES:
            self.assertTrue((checks.ROOT / relative).is_file(), relative)

    def test_current_successors_are_bounded_and_commit_exact(self) -> None:
        commit, _ = checks.tracked_identity(checks.ROOT)
        entries = checks.current_source_entries(checks.ROOT, commit)
        self.assertGreater(len(entries), 0)
        self.assertEqual(len(entries), len({entry["path"] for entry in entries}))
        for entry in entries:
            self.assertIn(
                entry["composition_predecessor_sha256"],
                entry["accepted_predecessor_sha256s"],
            )
            self.assertEqual(
                checks.digest(checks.bounded_file(checks.ROOT, entry["path"])),
                entry["current_sha256"],
            )

    def test_acceptance_claims_are_bounded(self) -> None:
        source = (checks.ROOT / "tools/p17/run_current_workspace_source_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"registered_host": False', source)
        self.assertIn('"production": False', source)
        self.assertIn('"phase_complete": False', source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
