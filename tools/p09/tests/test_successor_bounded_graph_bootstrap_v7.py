from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import successor_bounded_graph_bootstrap_v7 as m
class Tests(unittest.TestCase):
    def test_only_three_extra_bounded_inputs(self):
        self.assertEqual(len(m.EXTRA_PINS),3);self.assertTrue(all(0<p["bytes"]<=16384 for p in m.EXTRA_PINS))
    def test_original_declarations_remain_original_files(self):
        self.assertNotEqual(m.MANIFEST,m.original.MANIFEST);self.assertNotEqual(m.CAPSULE,m.original.CAPSULE)
        self.assertEqual(m.original.MANIFEST["path"],"implementation/p09/evidence/p09-361-case160-source-manifest029.v7.json")
if __name__=="__main__":unittest.main()
