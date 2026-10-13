import sys,unittest,copy
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v16 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(155)

    def test_exact_namespaces_prior153_context_and_full_prepare_unchanged(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v14","metadata_guard_identity_dedup_v1",
          "metadata_guard_identity_connection_v1","reviewed_runtime_attempt_v2"):
            self.assertNotIn(name,sys.modules)
        self.assertIs(v._full_prepare.__code__,v.OLD15._full_prepare.__code__)
        self.assertIs(v._full_prepare.__globals__["data_path"],v.M.data_path)
        fn=v.previous_function(154)
        self.assertIs(fn.__globals__["context"],v.OLD15.context)
        self.assertIs(fn.__globals__["source"],v.PRIOR154.source)
        self.assertIs(fn.__globals__["validator"],v.OLD15.validator)
        self.assertIs(v.NATIVE,v.OLD15.NATIVE)
        self.assertIs(v.CONNECTION,v.OLD15.CONNECTION)

    def test_scoped_validator_forwarding_into_full_original_code(self):
        seen=[]
        def full(q,row,listing,oldbody,fresh,ctx,flat=True):
            seen.append(validator);return "FULL_ORIGINAL",dict(full=True)
        original=FunctionType(full.__code__,dict(validator="OLD_FIXED"),argdefs=full.__defaults__,closure=full.__closure__)
        fn=FunctionType(v.validate_candidate.__code__,dict(v.validate_candidate.__globals__,
          _original_source=NS(validate_candidate=original),validator="ACTUAL_INHERITED_SCOPE",
          metadata_identity_evidence=lambda row:dict(actual_metadata_identity_duplicate_calls_avoided=20)),
          argdefs=v.validate_candidate.__defaults__,closure=v.validate_candidate.__closure__)
        result,proof=fn(None,{},None,None,None,None)
        self.assertEqual(seen,["ACTUAL_INHERITED_SCOPE"])
        self.assertEqual(result,"FULL_ORIGINAL");self.assertTrue(proof["full"])
        self.assertEqual(proof["actual_metadata_identity_duplicate_calls_avoided"],20)
        self.assertEqual(original.__globals__["validator"],"OLD_FIXED")

    def test_closed_new_data_historical_run1_current_physical2(self):
        p=lambda name:dict(path=name,bytes=1,sha256="0"*64)
        step=NS(index=155,before=148,pin=p("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v16",index=155,before=148,
          qualification_run=1,physical_product_run=1,base_step_pin=step.pin,
          prior_v15_data_pin=p(v.OLD15.data_path(155)),qualification_pin=p(v.QUAL_PATH),
          controller_code_pins=[p(v.SELF),p(v.TEST)],component_pins=v.COMPONENT_PINS,
          component_qualification_pins=v.COMPONENT_QUAL_PINS,actual154_pin=v.ACTUAL154_PIN,
          actual148_pin=v.ACTUAL148_PIN,reviewed_failure_pins=v.RETRY.HISTORY)
        self.assertIs(v.validate_data(row,step),row)
        for key,value in (("physical_product_run",2),("qualification_run",2),("reviewed_failure_pins",[])):
            with self.assertRaises(ValueError):v.validate_data(dict(row,**{key:value}),step)
        for index in (154,True,250):
            with self.assertRaises(ValueError):v.data_path(index)
        with self.assertRaises(ValueError):v.run_owned(2)

    def test_original_engine_one_adapter_and_original_summary_code(self):
        old,_=v.OLD15.template();oldstate=v.OLD15.ATTEMPT_STATES[-1]
        engine,proof=v.template();state=v.ATTEMPT_STATES[-1]
        self.assertEqual(state.original_engine_code,oldstate.original_engine_code)
        self.assertEqual(engine.worker.__code__,old.worker.__code__)
        self.assertTrue(proof["qualified_metadata_and_one_physical_adapter_reused"])
        self.assertEqual(state.physical_product_run,1);self.assertEqual(state.actual_engine_calls,0)
        summary=proof["metadata_identity_connection"]["summary_projection"]
        self.assertEqual(summary["type_dependency_changes"],1);self.assertEqual(len(summary["functions"]),3)
        self.assertIs(engine.run_owned.__globals__["native"],v.NATIVE)
        self.assertIs(engine.worker.__globals__["native"],v.NATIVE)

    def test_full_preflight10_original_code_and_ephemeral_alias_not_data_rewrite(self):
        p=v.M.source.prior.prior.prior.METADATA_PIN
        raw=(v.M.c.ROOT/p["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        old=v.OLD15.preflight_projection(raw,leaf);new=v.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        row=dict(qualification_run=1,physical_product_run=2)
        with patch.object(v,"own_inputs",return_value=row):view=new.__globals__["connection_data"](None)
        self.assertEqual(view,dict(row,run=1));self.assertNotIn("run",row)
        self.assertIs(new.__globals__["base"].native,v.NATIVE)

    def test_actual_outer_entry_single_physical_two_binding_one_no_product(self):
        seen=[]
        def engine_run(run):seen.append(("engine",run,binding(None)));return 0
        fn=FunctionType(engine_run.__code__,dict(binding=lambda q:"stale"),closure=engine_run.__closure__)
        connected,state,_=v.RETRY.connect_engine(NS(run_owned=fn,worker=lambda task:0),155)
        api,_=v.M.base.entry()
        class Factory:
            @staticmethod
            def windows_type(old,objects):return old
            @staticmethod
            def close(objects):return True
            @staticmethod
            def summary(objects):return {}
        def binding_attempt(q,run):seen.append(("binding",run));return "FULL_BINDING"
        call=FunctionType(api.run_owned.__code__,dict(api.run_owned.__globals__,
          template=lambda:(connected,{}),binding_attempt=binding_attempt,attribution=Factory),
          argdefs=api.run_owned.__defaults__,closure=api.run_owned.__closure__)
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),\
          patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):self.assertEqual(call(1),0)
        self.assertEqual(seen,[("binding",1),("engine",1,"FULL_BINDING")])
        self.assertEqual(state.actual_engine_calls,1)

if __name__=="__main__":unittest.main()
