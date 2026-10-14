from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));sys.path.insert(0,str(Path(__file__).resolve().parent))
import successor_runtime_graph_v7 as m
from test_successor_runtime_graph_v6 import base,Binding
class Tests(unittest.TestCase):
    def test_all_original_connector_code_metadata_inverse(self):self.assertEqual(m.connect.__code__.replace(co_consts=m.fn.__code__.co_consts),m.fn.__code__)
    def test34_original_objects_retained(self):
        b=base();bound=Binding();bound.descriptors=lambda:[{}]*34
        g,p=m.connect(b,bound);self.assertIs(g.parent,b.parent);self.assertIs(g.full_oracle,b.full_oracle)
        self.assertFalse(p["actual_run004_engine_worker_Native_or_GO_qualified"])
    def test32_subset_rejected(self):
        with self.assertRaises(ValueError):m.connect(base(),Binding())
    def test_existing_compact_interface_reused_once(self):
        b=base();old=m.original.connect(b,Binding())[0]
        bound=Binding();bound.descriptors=lambda:[{}]*34
        graph,proof=m.connect(old,bound)
        self.assertIs(graph.worker.encode,old.worker.encode)
        self.assertTrue(proof["compact_wire_connection"]["exact_existing_compact_interface_reused_not_stacked"])
    def test_half_compact_interface_rejected(self):
        b=base();old=m.original.connect(b,Binding())[0]
        old.worker.decode=b.worker.decode
        bound=Binding();bound.descriptors=lambda:[{}]*34
        with self.assertRaises(ValueError):m.connect(old,bound)
if __name__=="__main__":unittest.main()
