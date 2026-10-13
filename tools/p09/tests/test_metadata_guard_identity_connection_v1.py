import sys,unittest,threading,copy
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import metadata_guard_identity_connection_v1 as m
import flat_current_queue_native_diagnostic_runtime_v14 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(154)
        cls.raw=(v.M.c.ROOT/m.optimization.ORIGINAL).read_bytes()

    def test_actual_full_engine_connection_three_summary_bodies_unchanged(self):
        e,_=v.template();code=e.run_owned.__code__;worker=e.worker
        before=e.run_owned.__globals__["build"];old=before.pressure.PreSaturationReadCheckpoint
        proof=m.connect(e,self.raw);after=e.run_owned.__globals__["build"]
        self.assertIs(e.run_owned.__code__,code);self.assertIs(e.worker,worker)
        self.assertIs(before.pressure.PreSaturationReadCheckpoint,old)
        self.assertIsNot(after.pressure.PreSaturationReadCheckpoint,old)
        self.assertEqual(proof["summary_projection"]["type_dependency_changes"],1)
        self.assertEqual(len(proof["summary_projection"]["functions"]),3)
        self.assertEqual(proof["summary_projection"]["closure_links"],2)
        self.assertIs(after.BuildReader,before.BuildReader)

    def test_actual_full_summary_type_predicate_and_identity_guard_once(self):
        e,_=v.template();m.connect(e,self.raw);build=e.run_owned.__globals__["build"]
        seen=[]
        def hard():seen.append(1)
        r=build.BuildReader(v.M.c.ROOT,hard)
        b=build.pressure.PreSaturationReadCheckpoint(r,NS(checkpoint_io=hard,lock=threading.Lock(),
          samples=[dict(system_cpu_percent=20.)]))
        b();self.assertEqual(seen,[1])
        row=build.pressure_summary(b)
        self.assertEqual(row["metadata_failfast_connection"]["identity_duplicate_guard"]["calls_avoided"],1)
        self.assertFalse(row["source_reads_hashes_or_path_checks_skipped"])
        self.assertIn("reusable_chunk_metadata_reader",row)
        self.assertIn("single_snapshot_metadata_source",row)
        self.assertIn("single_snapshot_ancestor_source",row)
        b.restore();self.assertTrue(build.pressure_summary(b)["original_checkpoint_restored"])

    def test_actual_summary_warning_latch_restore_and_no_retry(self):
        e,_=v.template();m.connect(e,self.raw);build=e.run_owned.__globals__["build"]
        def hard():pass
        r=build.BuildReader(v.M.c.ROOT,hard)
        b=build.pressure.PreSaturationReadCheckpoint(r,NS(checkpoint_io=hard,lock=threading.Lock(),
          samples=[dict(system_cpu_percent=80.)]))
        with self.assertRaisesRegex(ValueError,"STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME"):b()
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED_METADATA_PRESSURE"):b()
        b.restore();s=build.pressure_summary(b)["metadata_failfast_connection"]
        self.assertEqual(s["warning_stops"],1);self.assertTrue(s["latched"])
        self.assertTrue(s["original_checkpoint_restored"]);self.assertFalse(s["automatic_retry_or_resume"])

    def test_distinct_callback_summary_zero_dedup_original_order(self):
        e,_=v.template();m.connect(e,self.raw);build=e.run_owned.__globals__["build"]
        seen=[]
        def original():seen.append("original")
        def hard():seen.append("hard")
        r=build.BuildReader(v.M.c.ROOT,original)
        b=build.pressure.PreSaturationReadCheckpoint(r,NS(checkpoint_io=hard,lock=threading.Lock(),
          samples=[dict(system_cpu_percent=20.)]))
        b();self.assertEqual(seen,["hard","original"])
        self.assertEqual(build.pressure_summary(b)["metadata_failfast_connection"]["identity_duplicate_guard"]["calls_avoided"],0)
        b.restore()

    def test_missing_type_or_unrelated_summary_function_closed_rejected(self):
        def other(guard):return {}
        with self.assertRaises(ValueError):m.summary_projection(other,object(),object())
        def pressure_summary(guard):return {}
        with self.assertRaises(ValueError):m.summary_projection(pressure_summary,object(),object())
        e,_=v.template()
        with self.assertRaises(ValueError):m.connect(e,self.raw.replace(b"self.original()",b"self.hard()"))

    def test_original_guard_code_and_other_dependencies_preserved(self):
        e,_=v.template();before=dict(e.run_owned.__globals__);worker=e.worker
        m.connect(e,self.raw);after=e.run_owned.__globals__
        self.assertEqual(set(after),set(before))
        for k,x in before.items():
            if k!="build":self.assertIs(after[k],x)
        self.assertIs(e.worker,worker)
        self.assertIs(after["native"],v.NATIVE)
        self.assertIs(after["build"].QueryPacer,before["build"].QueryPacer)
        self.assertIs(after["build"].BuildReader,before["build"].BuildReader)

if __name__=="__main__":unittest.main()
