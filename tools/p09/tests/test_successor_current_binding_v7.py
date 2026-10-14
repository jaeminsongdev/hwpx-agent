from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import successor_current_binding_v7 as m
from test_review_failed_run003_v1 import exact
def binding(n=34):return NS(descriptors=lambda:[dict(index=i) for i in range(n)],manifest_pin=dict(path="manifest030",bytes=1,sha256="a"*64))
class Tests(unittest.TestCase):
    def test_all34_equal(self):m.same_graph(NS(exact=exact),binding(),binding())
    def test32_subset_denied(self):
        with self.assertRaises(ValueError):m.same_graph(NS(exact=exact),binding(),binding(32))
    def test_old_manifest_denied(self):
        b=binding();b.manifest_pin["path"]="manifest029"
        with self.assertRaises(ValueError):m.same_graph(NS(exact=exact),binding(),b)
if __name__=="__main__":unittest.main()
