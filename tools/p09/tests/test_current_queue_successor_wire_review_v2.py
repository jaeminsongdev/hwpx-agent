"""Frozen source pins and explicit review/acceptance boundaries."""
import ast
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_wire_review_v2 as m


class Tests(unittest.TestCase):
    def test_frozen_review_and_acceptance_sources_are_explicit(self):
        self.assertEqual(len(m.PINS),2)
        self.assertEqual({p["path"] for p in m.PINS},{"tools/p09/review_current_queue_successor.py","tools/p09/accept_current_queue_successor.py"})
        self.assertTrue(all(len(p["sha256"])==64 and 0<p["bytes"]<=65536 for p in m.PINS))
    def test_no_worker_or_Native_entry_provided(self):
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ("run_owned","worker","owned_worker_entry") for n in calls))


if __name__=="__main__":unittest.main()
