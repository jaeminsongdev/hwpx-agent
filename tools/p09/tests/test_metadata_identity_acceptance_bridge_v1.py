import sys,unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import metadata_identity_acceptance_bridge_v1 as m
import flat_current_queue_native_diagnostic_runtime_v15 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(154)

    def fixture(self,error=False):
        seen=[]
        def original(q,row,listing,oldbody,fresh,ctx,flat=True):
            seen.append(("original",validator))
            if error:raise ValueError("ORIGINAL_FULL_ERROR")
            return "all-original-body",dict(original=True)
        old=FunctionType(original.__code__,dict(validator="OLD_FIXED"),argdefs=original.__defaults__,closure=original.__closure__)
        def identity(row):seen.append(("identity",row));return dict(actual_identity=True)
        fn=FunctionType(m.validate_candidate.__code__,
          dict(m.validate_candidate.__globals__,original_source=NS(validate_candidate=old),
            validator="REAL_INHERITED_SCOPED",identity_evidence=identity),argdefs=m.validate_candidate.__defaults__,closure=m.validate_candidate.__closure__)
        return fn,seen,old

    def test_supplied_scoped_validator_reaches_original_not_fixed_parent(self):
        fn,seen,old=self.fixture();result,proof=fn(None,{"current":True},None,None,None,None)
        self.assertEqual(result,"all-original-body")
        self.assertEqual(seen[0],("original","REAL_INHERITED_SCOPED"))
        self.assertTrue(proof["original"]);self.assertTrue(proof["actual_identity"])
        self.assertEqual(old.__globals__["validator"],"OLD_FIXED")

    def test_full_original_failure_propagates_before_added_evidence(self):
        fn,seen,_=self.fixture(error=True)
        with self.assertRaisesRegex(ValueError,"ORIGINAL_FULL_ERROR"):fn(None,{},None,None,None,None)
        self.assertEqual(seen,[("original","REAL_INHERITED_SCOPED")])

    def test_actual_full_prepare_native_scope_and_task_code_unchanged(self):
        runtime,proof=m.connect(v);full=runtime.API.prepare.__globals__["_full_prepare"]
        self.assertIs(full.__code__,v._full_prepare.__code__)
        self.assertIs(runtime.API.prepare.__code__,v.prepare.__code__)
        self.assertIs(runtime.API.prepare.__globals__["native_scope"],v.native_scope)
        self.assertIs(runtime.API.prepare.__globals__["RETRY"],v.RETRY)
        self.assertTrue(proof["original_full_prepare_Native_scope_and_physical_task_checks_retained"])

    def test_private_dependencies_no_historical_source_mutation(self):
        before=v.CURRENT_SOURCE.validate_candidate;original=v._full_prepare.__globals__["source"]
        runtime,_=m.connect(v)
        self.assertIs(v.CURRENT_SOURCE.validate_candidate,before)
        self.assertIs(v._full_prepare.__globals__["source"],original)
        self.assertIs(runtime.source.validate_candidate.__globals__["original_source"],v._original_source)
        self.assertIs(runtime.source.validate_candidate.__globals__["identity_evidence"],v.metadata_identity_evidence)
        for k,x in vars(v.CURRENT_SOURCE).items():
            if k!="validate_candidate":self.assertIs(getattr(runtime.source,k),x)

    def test_original_defaults_closure_signature_and_full_body_retained(self):
        runtime,_=m.connect(v);fn=runtime.source.validate_candidate
        original=fn.__globals__["original_source"].validate_candidate
        self.assertIs(original,v._original_source.validate_candidate)
        self.assertEqual(fn.__defaults__,m.validate_candidate.__defaults__)
        self.assertIs(runtime.context,v.context);self.assertIs(runtime.own_inputs,v.own_inputs)

    def test_no_child_or_source_write_and_original_runtime_identity(self):
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),\
          patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):runtime,proof=m.connect(v)
        self.assertEqual(runtime.SELF,v.SELF);self.assertEqual(runtime.TEST,v.TEST)
        self.assertTrue(proof["Native_or_product_reexecuted"] is False)
        self.assertTrue(proof["acceptance_witness_not_retroactive_Native_input"])

if __name__=="__main__":unittest.main()
