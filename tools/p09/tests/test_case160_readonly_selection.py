"""Closed read-only routing; no controller imports or product dispatch."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).parents[1]/"qualify_case160_run004_readonly.py"
spec = importlib.util.spec_from_file_location("case160_readonly_selection", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Tests(unittest.TestCase):
    def test_original_default_paths_are_preserved(self):
        self.assertEqual(module.selection(4, 1), (module.ROOT["path"], module.OUTPUT))

    def test_runtime_and_report_paths_are_distinct_and_closed(self):
        seen = set()
        for run in range(7, 15):
            for attempt in range(1, 9):
                root, output = module.selection(run, attempt)
                self.assertTrue(root.endswith(f"run{run:03}.v1.json"))
                self.assertTrue(output.endswith(f"attempt{attempt:03}.v1.json"))
                self.assertNotIn(output, seen)
                seen.add(output)

    def test_invalid_or_bool_identity_is_rejected(self):
        for run in (True, 1, 5, 6, 15, "10", 10.0):
            with self.assertRaises(ValueError): module.selection(run, 1)
        for attempt in (False, 0, 9, "1", 1.0):
            with self.assertRaises(ValueError): module.selection(10, attempt)


if __name__ == "__main__": unittest.main()
