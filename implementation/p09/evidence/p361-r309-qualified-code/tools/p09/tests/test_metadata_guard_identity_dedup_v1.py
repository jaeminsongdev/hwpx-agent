import sys,unittest,threading,copy
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import metadata_guard_identity_dedup_v1 as m
import metadata_pressure_failfast as old

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(Path(__file__).resolve().parents[1]/"metadata_pressure_failfast.py").read_bytes()
        cls.New,cls.proof=m.checkpoint_type(old.Checkpoint,cls.raw)

    def binding(self,cpu=20,distinct=False,error=False):
        seen=[]
        def hard():
            seen.append("hard")
            if error:raise ValueError("ORIGINAL_HARD_STOP")
        def original():seen.append("original")
        callback=original if distinct else hard
        reader=NS(checkpoint=callback)
        owner=NS(checkpoint_io=hard,lock=threading.Lock(),samples=[dict(system_cpu_percent=cpu)])
        binding=self.New(reader,owner)
        return binding,reader,seen

    def test_same_callback_once_first_all_original_fields_and_restore(self):
        b,r,seen=self.binding();b()
        self.assertEqual(seen,["hard"]);self.assertEqual(b.checks,1)
        self.assertEqual(b.identity_duplicates_avoided,1)
        before=copy.deepcopy(old.Checkpoint.summary(b))
        now=b.summary()
        for k,v in before.items():self.assertEqual(now[k],v)
        self.assertTrue(now["identity_duplicate_guard"]["original_callback_is_hard"])
        b.restore();self.assertIs(r.checkpoint,b.original);self.assertTrue(b.restored)
        with self.assertRaises(ValueError):b()
        self.assertEqual(seen,["hard"])

    def test_distinct_callbacks_keep_original_order_and_no_dedup(self):
        b,_,seen=self.binding(distinct=True);b()
        self.assertEqual(seen,["hard","original"])
        self.assertEqual(b.identity_duplicates_avoided,0)
        self.assertTrue(self.proof["distinct_callbacks_keep_both_original_calls"])
        b.restore()

    def test_warning_stop_latched_no_original_resume_no_sampling_added(self):
        for distinct in (False,True):
            b,r,seen=self.binding(cpu=75,distinct=distinct)
            with self.assertRaisesRegex(ValueError,"STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME"):b()
            self.assertEqual(seen,["hard"]);self.assertTrue(b.latched)
            self.assertEqual(b.warning_stops,1);self.assertEqual(b.identity_duplicates_avoided,0)
            with self.assertRaisesRegex(ValueError,"STOP_LATCHED_METADATA_PRESSURE"):b()
            self.assertEqual(seen,["hard"])
            b.restore();self.assertIs(r.checkpoint,b.original)

    def test_hard_error_precedence_and_counts_unchanged(self):
        b,_,seen=self.binding(cpu=99,error=True)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_HARD_STOP"):b()
        self.assertEqual(seen,["hard"]);self.assertEqual(b.checks,0)
        self.assertEqual(b.warning_stops,0);self.assertFalse(b.latched)
        b.restore()

    def test_invalid_cpu_or_missing_owner_sample_rejected_after_hard(self):
        for cpu in (True,None,-1,float("nan"),101):
            b,_,seen=self.binding(cpu=cpu)
            with self.assertRaisesRegex(ValueError,"SAMPLE_INVALID"):b()
            self.assertEqual(seen,["hard"]);self.assertEqual(b.identity_duplicates_avoided,0)
            b.restore()
        b,_,seen=self.binding();b.owner.samples.clear()
        with self.assertRaisesRegex(ValueError,"SAMPLE_MISSING"):b()
        self.assertEqual(seen,["hard"]);b.restore()

    def test_exact_source_projection_no_unrelated_callback_or_multiple_leaf(self):
        self.assertTrue(self.proof["all_original_statements_restored_by_independent_undo"])
        with self.assertRaises(ValueError):m.checkpoint_type(old.Checkpoint,self.raw.replace(b"self.original()",b"self.hard()"))
        with self.assertRaises(ValueError):m.checkpoint_type(old.Checkpoint,self.raw.replace(b"self.original()",b"self.original(); self.original()"))
        class Wrong(old.Checkpoint):
            def __call__(self):return None
        with self.assertRaises(ValueError):m.checkpoint_type(Wrong,self.raw)

if __name__=="__main__":unittest.main()
