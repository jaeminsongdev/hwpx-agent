from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import successor_current_binding_v6 as m
from test_review_failed_run003_v1 import exact
API=NS(exact=exact)
def binding(n=32):return NS(descriptors=lambda:[dict(index=i) for i in range(n)],manifest_pin=dict(path="manifest029",bytes=1,sha256="a"*64))
class Tests(unittest.TestCase):
    def test_all32_same_declaration(self):m.same_graph(API,binding(),binding())
    def test_worker_missing_descriptor_rejected(self):
        with self.assertRaises(ValueError):m.same_graph(API,binding(),binding(31))
    def test_different_manifest_rejected(self):
        b=binding();b.manifest_pin["sha256"]="b"*64
        with self.assertRaises(ValueError):m.same_graph(API,binding(),b)
    def test_bool_descriptor_metadata_rejected(self):
        b=binding();b.descriptors=lambda:[dict(index=True)]+[dict(index=i) for i in range(1,32)]
        with self.assertRaises(ValueError):m.same_graph(API,binding(),b)
if __name__=="__main__":unittest.main()
