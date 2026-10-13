import sys,unittest,threading
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import preflight_guard_identity_v1 as m
import flat_current_queue_native_diagnostic_runtime_v16 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(155)

    def fake(self,error=False):
        class Original:
            def __init__(self):self.calls=[];self.samples=[dict(system_cpu_percent=20.)]
            def check(self,force=False):
                self.calls.append(force)
                if error:raise ValueError("ORIGINAL_HARD_ERROR")
                return 7
        return Original

    def test_stable_same_original_code_self_and_force_argument(self):
        old=self.fake();New=m.guard_type(old);g=New()
        a=g.check;b=g.check
        self.assertIs(a,b);self.assertIs(a.__func__,old.check);self.assertIs(a.__self__,g)
        self.assertEqual(a(force=True),7);self.assertEqual(g.calls,[True])
        self.assertIsNot(old().check,old().check)

    def test_errors_and_other_guard_instances_not_changed(self):
        old=self.fake(error=True);g=m.guard_type(old)()
        with self.assertRaisesRegex(ValueError,"ORIGINAL_HARD_ERROR"):g.check()
        self.assertEqual(g.calls,[False])
        ordinary=old();self.assertIsNot(ordinary.check,ordinary.check)
        self.assertEqual(ordinary.calls,[])

    def actual_projection(self):
        pin=v.M.source.prior.prior.prior.METADATA_PIN
        data=(v.M.c.ROOT/pin["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        fn=v.preflight_projection(data,leaf)
        return fn,m.projection(fn,(v.M.c.ROOT/v.DEDUP.ORIGINAL).read_bytes(),v.DEDUP)

    def test_all_original_preflight_code_only_destination_metadata(self):
        old,(fn,proof)=self.actual_projection()
        self.assertEqual(fn.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIs(fn.__defaults__,old.__defaults__);self.assertIs(fn.__closure__,old.__closure__)
        for k,x in old.__globals__.items():
            if k not in ("a","MetadataCheckpoint"):self.assertIs(fn.__globals__[k],x)
        self.assertTrue(proof["original_preflight_code_defaults_closure_and_test10_retained"])

    def test_two_original_preflight_attribute_reads_dedup_once_and_restore(self):
        old,(fn,_)=self.actual_projection();Original=self.fake();Guard=m.guard_type(Original);g=Guard()
        reader=NS(checkpoint=g.check)
        owner=NS(checkpoint_io=g.check,samples=g.samples,lock=threading.Lock())
        b=fn.__globals__["MetadataCheckpoint"](reader,owner);b()
        self.assertEqual(g.calls,[False]);self.assertEqual(b.identity_duplicates_avoided,1)
        b.restore();self.assertIs(reader.checkpoint,g.check)

    def test_warning_latch_original_criteria_and_no_automatic_resume(self):
        _,(fn,_)=self.actual_projection();g=m.guard_type(self.fake())()
        g.samples[-1]["system_cpu_percent"]=90.
        reader=NS(checkpoint=g.check);b=fn.__globals__["MetadataCheckpoint"](reader,
          NS(checkpoint_io=g.check,samples=g.samples,lock=threading.Lock()))
        with self.assertRaisesRegex(ValueError,"STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME"):b()
        with self.assertRaisesRegex(ValueError,"STOP_LATCHED_METADATA_PRESSURE"):b()
        self.assertEqual(g.calls,[False]);b.restore()
        self.assertIs(reader.checkpoint,g.check)

    def test_unexpected_destination_rejected_and_engine_template_unchanged(self):
        old,(fn,_)=self.actual_projection()
        self.assertIs(fn.__globals__["template"],v.template)
        bad=FunctionType(old.__code__.replace(co_consts=tuple("other" if type(x) is str and
          x=="-native-diagnostic-preflight016.v1.json" else x for x in old.__code__.co_consts)),old.__globals__)
        with self.assertRaises(ValueError):m.projection(bad,(v.M.c.ROOT/v.DEDUP.ORIGINAL).read_bytes(),v.DEDUP)

if __name__=="__main__":unittest.main()
