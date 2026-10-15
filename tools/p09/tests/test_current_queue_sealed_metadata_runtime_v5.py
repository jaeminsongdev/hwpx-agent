"""New metadata paths and mandatory source proof; no product fixtures."""
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import current_queue_sealed_metadata_runtime_v5 as m


class Tests(unittest.TestCase):
    def test_closed_parameterized_source_qualification(self):
        self.assertIn("case165-sealed-metadata-code001",m.source_qualification(165,1))
        self.assertIn("case249-sealed-metadata-code008",m.source_qualification(249,8))
        for args in ((164,1),(250,1),(True,1),(165,0),(165,True)):
            with self.assertRaises(ValueError):m.source_qualification(*args)
    def test_v4_retry_namespace_inverse_retains_closed_native_branch(self):
        import current_queue_successor_retry_runtime_v3 as retry
        import current_queue_successor_lossless_runtime_v4 as v4
        from types import FunctionType
        env=dict(retry.previous_stops.__globals__,__name__="p09_exact_retry_fixture")
        ns=NS(previous_stops=FunctionType(retry.previous_stops.__code__,env))
        raw=(Path(__file__).resolve().parents[3]/v4.PINS[0]["path"]).read_bytes()
        m.retry_paths(raw,ns,v4.PINS[0])
        calls=[];env["absent"]=lambda *args:True;env["failed_graph"]=lambda *args:None
        ns.previous_stops(NS(json=lambda name:calls.append(name)),NS(index=165,run=3),NS(require=lambda ok,label:self.assertTrue(ok)),NS())
        self.assertEqual(calls,["implementation/p09/evidence/p09-361-case165-successor-connections002.v4.json"])
        env["absent"]=lambda *args:False;calls.clear()
        ns.previous_stops(NS(json=lambda name:name),NS(index=165,run=3),NS(),NS(closed_prebody_stop=lambda *args:calls.append(args)))
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][1:3],(165,2))
    def test_retry_source_drift_rejected(self):
        with self.assertRaises(ValueError):m.retry_paths(b"drift",NS(),dict(bytes=5,sha256="0"*64))
    def test_real_reader_requires_new_qualification_and_sources(self):
        calls=[]
        class Base:
            def __init__(self,*args):pass
            def pin(self,name):calls.append(name);return next((p for p in m.PINS if p["path"]==name),{})
            def json(self,name):raise ValueError("MISSING_CURRENT_QUALIFICATION")
        api=NS(AcceptanceReader=Base,exact=lambda left,right,label:self.assertEqual(left,right))
        with self.assertRaises(ValueError):m.witness_api(api,"missing").AcceptanceReader(None,None)
        self.assertEqual(calls[:2],[m.SELF,m.TEST]);self.assertTrue(all(p["path"] in calls for p in m.PINS))


if __name__=="__main__":unittest.main()
