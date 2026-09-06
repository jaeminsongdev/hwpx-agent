from __future__ import annotations

import ast
from pathlib import Path
import unittest


VALIDATOR = Path(__file__).parents[2] / "design-validation" / "validate_design.py"


class DesignValidationScopeTests(unittest.TestCase):
    def test_generated_and_private_trees_are_excluded_from_source_scans(self) -> None:
        module = ast.parse(VALIDATOR.read_text(encoding="utf-8"))
        excluded: set[str] | None = None
        for statement in module.body:
            if not isinstance(statement, ast.Assign):
                continue
            if any(
                isinstance(target, ast.Name)
                and target.id == "EXCLUDED_TREE_PARTS"
                for target in statement.targets
            ):
                excluded = ast.literal_eval(statement.value)
                break

        self.assertIsNotNone(excluded)
        self.assertTrue(
            {"artifacts", "licensed-private", "target-build"}.issubset(excluded)
        )


if __name__ == "__main__":
    unittest.main()
