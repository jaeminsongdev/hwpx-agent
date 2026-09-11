from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.dev import p17_fast, validate


ROOT = Path(__file__).resolve().parents[3]


class ValidationProfileTests(unittest.TestCase):
    def test_profiles_separate_development_feedback_from_closure(self) -> None:
        catalog = validate.catalog()
        self.assertEqual(
            catalog["profiles"]["p17-fast"]["authority"],
            "development_feedback_only",
        )
        self.assertEqual(
            catalog["profiles"]["p17-full"]["authority"], "closure_validation"
        )
        self.assertIn("--all-targets", validate.PROFILES["rust-full"].commands[0])
        self.assertIn("--all-features", validate.PROFILES["rust-full"].commands[0])
        self.assertIn("--locked", validate.PROFILES["rust-full"].commands[0])
        self.assertIn("--offline", validate.PROFILES["rust-full"].commands[0])

    def test_p17_fast_plan_defers_exactly_the_expensive_lineage(self) -> None:
        fast, deferred = p17_fast.classify()
        fast_names = {path.name for path in fast}
        deferred_names = {path.name for path in deferred}
        self.assertEqual(len(fast) + len(deferred), 94)
        self.assertIn("test_remote_credential_issuer_contract.py", fast_names)
        self.assertIn("test_current_workspace_source_qualification_v48.py", deferred_names)
        self.assertIn("test_frozen_current_source_v48_contract.py", deferred_names)
        self.assertIn("test_current_workspace_source_qualification_v21.py", deferred_names)
        self.assertNotIn("test_remote_credential_issuer_contract.py", deferred_names)
        self.assertGreater(len(deferred), 50)
        plan = p17_fast.plan()
        self.assertEqual(plan["authority"], "development_feedback_only")
        self.assertIn("test_*.py", plan["full_closure_command"])
        self.assertLess(len(json.dumps(plan)), 2_000)


if __name__ == "__main__":
    unittest.main()
