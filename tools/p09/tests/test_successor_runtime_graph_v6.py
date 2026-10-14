import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import successor_runtime_graph_v6 as m
def encode(*args):return json.dumps({})
def decode(*args):return json.loads("{}")
def connect_worker(*args):return TASK,args
class Binding:
    next_case=160
    def descriptors(self):return [{}]*32
def base():
    module=NS(Binding=Binding)
    worker=NS(MAX_BYTES=16384,encode=encode,decode=decode,connect_worker=connect_worker,
        source=module,raw_policy=NS(source=module),TASK="case160-current-r003-tests")
    parent=NS(access=NS(source=module),original=NS(frames=NS(binding_module=module)))
    return NS(binding_module=module,worker=worker,parent=parent,full_oracle=NS(binding_module=module))
class Tests(unittest.TestCase):
    def test_original_graph_objects_retained(self):
        b=base();graph,proof=m.connect(b,Binding())
        self.assertIs(graph.parent,b.parent);self.assertIs(graph.full_oracle,b.full_oracle)
        self.assertIs(graph.worker.connect_worker.__code__,b.worker.connect_worker.__code__)
        self.assertFalse(proof["actual_run004_engine_worker_Native_or_GO_qualified"])
    def test_task_change_private_only(self):
        b=base();graph,_=m.connect(b,Binding())
        self.assertEqual(graph.worker.connect_worker()[0],m.TASK)
        self.assertEqual(b.worker.TASK,"case160-current-r003-tests")
    def test_wrong_pair_count_rejected(self):
        b=base();bound=Binding();bound.descriptors=lambda:[{}]*31
        with self.assertRaises(ValueError):m.connect(b,bound)
    def test_other_module_not_silently_shared(self):
        b=base();b.parent.access.source=NS()
        with self.assertRaises(ValueError):m.connect(b,Binding())
if __name__=="__main__":unittest.main()
