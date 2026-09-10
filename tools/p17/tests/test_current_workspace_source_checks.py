from __future__ import annotations

from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch


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
        self.assertIn("crates/retention-sync-service/src/lib.rs", expectations)
        self.assertIn(checks.RETENTION_CONTRACT, checks.PINNED_CONTRACTS)
        self.assertIn(checks.P15_AUTH_CONTRACT, checks.PINNED_CONTRACTS)
        self.assertIn("tools/p14/validate_retention_local_mirror.py", expectations)
        self.assertEqual(
            checks.PINNED_AMBIGUOUS_BASELINES,
            {
                "Cargo.toml": (
                    "f8281c9c13ea981ab8652819f1e3946ea942bca2d952f68b05ee61f3a3179c03"
                ),
                "tools/p14/validate_retention_local_mirror.py": (
                    "11b87d37cfb76b523c29ee9dfb28500b4f57e2cb38d61f21e08f2fcc46b24676"
                ),
                "tools/p14/validate_cancel_cleanup.py": (
                    "0e55cd4b00a1d670b1c31238fc69e9933db68e52c95a41ec18bb709c0be128c0"
                ),
                "tools/p15/validate_auth_tenant.py": (
                    "c805d097d92c6e41d8434de8d62aed3fd88bf95cfc81a2fab4cc3d389ccfb86a"
                ),
                "tools/p15/validate_inspector_staging_contract.py": (
                    "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3"
                )
            },
        )
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
        inspector = next(
            entry
            for entry in entries
            if entry["path"] == "tools/p15/validate_inspector_staging_contract.py"
        )
        self.assertEqual(
            inspector["accepted_predecessor_sha256s"],
            [
                "d4370aabc28cc26ac931caaa5ec7172d7a3455e05732026018bec704e684a937",
                "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3",
            ],
        )
        self.assertEqual(
            inspector["composition_predecessor_sha256"],
            "d9869d7a01b2cea5eeeb0a9d5f64dae79cccf523dbdec8811f812551ef16d7d3",
        )

    def test_unknown_ambiguous_predecessors_remain_rejected(self) -> None:
        relative = "tools/p16/validate_widget_shell_successor.py"
        with (
            patch.object(checks, "load_pinned_contracts", return_value={}),
            patch.object(
                checks,
                "source_expectations",
                return_value=({relative: {"0" * 64, "1" * 64}}, {}),
            ),
        ):
            with self.assertRaisesRegex(checks.AcceptanceError, "predecessor.ambiguous"):
                checks.current_source_entries(checks.ROOT, checks.tracked_identity(checks.ROOT)[0])

    def test_pinned_ambiguous_baseline_must_come_from_exact_contracts(self) -> None:
        contracts = checks.load_pinned_contracts(checks.ROOT)
        with patch.dict(
            checks.PINNED_AMBIGUOUS_BASELINES,
            {"tools/p15/validate_inspector_staging_contract.py": "0" * 64},
            clear=True,
        ):
            with self.assertRaisesRegex(
                checks.AcceptanceError, "predecessor.pinned_baseline"
            ):
                checks.source_expectations(contracts)

    def test_acceptance_claims_are_bounded(self) -> None:
        source = (checks.ROOT / "tools/p17/run_current_workspace_source_checks.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"actual_hangul": False', source)
        self.assertIn('"registered_host": False', source)
        self.assertIn('"production": False', source)
        self.assertIn('"phase_complete": False', source)
        self.assertNotIn("shell=True", source)

    def test_hwpx_font_metric_dependencies_are_product_only(self) -> None:
        manifest = tomllib.loads(
            (checks.ROOT / "crates/hwpx-package/Cargo.toml").read_text(encoding="utf-8")
        )
        dependencies = manifest["dependencies"]
        development = manifest["dev-dependencies"]
        self.assertEqual(dependencies["serde"], {"workspace": True})
        self.assertEqual(dependencies["serde_json"], {"workspace": True})
        self.assertNotIn("serde", development)
        self.assertNotIn("serde_json", development)
        self.assertIn(
            "hwpx_package_font_metric_product_edges_exact",
            checks.CHECKS,
        )


if __name__ == "__main__":
    unittest.main()
