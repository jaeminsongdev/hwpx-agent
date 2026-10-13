import sys,unittest,threading
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import acceptance_metadata_guard_identity_v1 as m
import flat_current_queue_native_diagnostic_runtime_v16 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(155)
        cls.raw=(v.M.c.ROOT/v.DEDUP.ORIGINAL).read_bytes()
    def runtime(self):
        return NS(**{**vars(v.M),"source":v.CURRENT_SOURCE,"API":v.API})

    def test_actual_nested_acceptance_factory_only_private_class_changed(self):
        old=self.runtime();original=old.source.prior.prior.metadata.MetadataCheckpoint
        new,proof=m.connect(old,self.raw,v.DEDUP)
        self.assertIs(old.source.prior.prior.metadata.MetadataCheckpoint,original)
        self.assertIsNot(new.source.prior.prior.metadata.MetadataCheckpoint,original)
        self.assertIs(new.API,old.API);self.assertIs(new.a,old.a)
        self.assertTrue(proof["all_original_acceptor_prepare_Native_scope_and_metadata_identity_checks_retained"])

    def binding(self,cpu=20.,distinct=False):
        new,_=m.connect(self.runtime(),self.raw,v.DEDUP);seen=[]
        def hard():seen.append("hard")
        def original():seen.append("original")
        callback=original if distinct else hard
        r=NS(checkpoint=callback)
        b=new.source.prior.prior.metadata.MetadataCheckpoint(r,NS(checkpoint_io=hard,
          lock=threading.Lock(),samples=[dict(system_cpu_percent=cpu)]))
        return b,r,seen

    def test_same_acceptance_callback_once_and_restored(self):
        b,r,seen=self.binding();b()
        self.assertEqual(seen,["hard"]);self.assertEqual(b.identity_duplicates_avoided,1)
        b.restore();self.assertIs(r.checkpoint,b.original)

    def test_warning_latch_hard_first_and_no_retry(self):
        b,r,seen=self.binding(cpu=85)
        with self.assertRaisesRegex(ValueError,"STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME"):b()
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED_METADATA_PRESSURE"):b()
        self.assertEqual(seen,["hard"]);b.restore()
        self.assertTrue(b.summary()["original_checkpoint_restored"])

    def test_distinct_callbacks_keep_both_original_calls(self):
        b,_,seen=self.binding(distinct=True);b()
        self.assertEqual(seen,["hard","original"]);self.assertEqual(b.identity_duplicates_avoided,0)
        b.restore()

    def test_all_other_source_and_metadata_values_retained(self):
        old=self.runtime();new,_=m.connect(old,self.raw,v.DEDUP)
        for k,x in vars(old.source).items():
            if k!="prior":self.assertIs(getattr(new.source,k),x)
        for k,x in vars(old.source.prior.prior.metadata).items():
            if k!="MetadataCheckpoint":self.assertIs(getattr(new.source.prior.prior.metadata,k),x)
        self.assertIs(new.source.prior.prior.metadata.MetadataCheckpoint.restore,
          old.source.prior.prior.metadata.MetadataCheckpoint.restore)

    def test_unexpected_original_code_rejected_no_source_scope_or_guard_substitute(self):
        with self.assertRaises(ValueError):m.connect(self.runtime(),self.raw.replace(b"self.original()",b"self.hard()"),v.DEDUP)
        new,_=m.connect(self.runtime(),self.raw,v.DEDUP)
        self.assertIs(new.source.validate_candidate,v.CURRENT_SOURCE.validate_candidate)
        self.assertIs(new.source.root_path,v.CURRENT_SOURCE.root_path)

if __name__=="__main__":unittest.main()
