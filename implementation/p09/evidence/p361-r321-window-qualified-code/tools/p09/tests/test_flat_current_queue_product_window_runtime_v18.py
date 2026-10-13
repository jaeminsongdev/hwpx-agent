import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_product_window_runtime_v18 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(157)
    def test_exact_namespaces_and_historical156_context_preserved(self):
        for name in ("flat_current_queue_native_pressure_runtime_v17","strict_product_window_v1","strict_product_window_model_v1","strict_product_window_connection_v1"):
            self.assertNotIn(name,sys.modules)
        self.assertIs(v._full_prepare.__code__,v.OLD17._full_prepare.__code__)
        self.assertIs(v.BACKEND,v.OLD17.BACKEND);self.assertIs(v.CONNECTION,v.OLD17.CONNECTION)
        self.assertIs(v.NATIVE.load,v.OLD17.NATIVE.load)
        fn=v.previous_function(156);old=v.OLD17.previous_function(156)
        self.assertIs(fn.__code__,old.__code__);self.assertIs(fn.__globals__["source"],old.__globals__["source"])
    def test_closed_data018_and_only157_no_replay(self):
        p=lambda name:dict(path=name,bytes=1,sha256="0"*64)
        step=NS(index=157,before=150,pin=p("step"))
        row=dict(schema_version="hwpx-agent.p09-product-window-controller/v18",index=157,before=150,
            qualification_run=1,physical_product_run=1,base_step_pin=step.pin,
            prior_v17_data_pin=p(v.OLD17.data_path(157)),qualification_pin=p(v.QUAL_PATH),
            controller_code_pins=[p(v.SELF),p(v.TEST)],component_pins=v.COMPONENT_PINS,
            component_qualification_pins=v.COMPONENT_QUAL_PINS,actual155_pin=v.ACTUAL155_PIN,
            actual149_pin=v.ACTUAL149_PIN,failed_preflight_pin=v.FAILED_PREFLIGHT_PIN,
            actual156_pin=v.ACTUAL156_PIN,actual150_pin=v.ACTUAL150_PIN)
        self.assertIs(v.validate_data(row,step),row)
        for key,value in (("physical_product_run",2),("qualification_run",True),("actual150_pin",None),("component_pins",[])):
            with self.assertRaises(ValueError):v.validate_data(dict(row,**{key:value}),step)
        for index in (156,158,True):
            with self.assertRaises(ValueError):v.data_path(index)
    def test_original_engine_worker_and_one_actual_window_binding_not_executed(self):
        old,_=v.OLD17.template();engine,proof=v.template();state=v.WINDOW_STATES[-1]
        self.assertIs(state.original_engine_code,old.run_owned.__code__)
        self.assertEqual(engine.worker.__code__,old.worker.__code__)
        self.assertIs(engine.run_owned.__globals__["native"],v.NATIVE)
        self.assertIs(engine.run_owned.__globals__["runtime_budget"],v.DIRECT.runtime_budget)
        self.assertEqual(state.calls,[]);self.assertEqual(state.states,[])
        self.assertEqual(v.ATTEMPT_STATES[-1].actual_engine_calls,0)
        self.assertTrue(proof["no_additional_physical_adapter"])
    def test_new_full_validator_only157_original156_cost_preserved(self):
        pin=v.original_candidate.ACCEPTOR_PIN;raw=(v.M.c.ROOT/pin["path"]).read_bytes()
        ctx=v.context(v.M.base.CONFIG);fn,proof=v.validator(raw,ctx)
        self.assertIs(fn.__globals__["ORACLE_SCOPE"].cost,v.DIRECT.cost)
        self.assertIn(v.SELF,fn.__globals__["CONTROLLERS"])
        oldctx=NS(**{**vars(ctx),"INDEX":156})
        old,_=v.OLD17.validator(raw,oldctx);hist,_=v.validator(raw,oldctx)
        self.assertIs(hist.__globals__["ORACLE_SCOPE"].cost,old.__globals__["ORACLE_SCOPE"].cost)
        self.assertNotIn(v.SELF,hist.__globals__["CONTROLLERS"])
        self.assertIs(v.linked.__code__,v.OLD17.linked.__code__)
    def test_full_preflight_original10_code_new_complete_budget(self):
        p=v.M.source.prior.prior.prior.METADATA_PIN;raw=(v.M.c.ROOT/p["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        old=v.OLD17.preflight_projection(raw,leaf);new=v.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIn("-product-window-preflight019.v1.json",new.__code__.co_consts)
        self.assertIs(new.__globals__["base"].native,v.NATIVE)
        self.assertIs(new.__globals__["base"].stable.runtime_budget,v.DIRECT.runtime_budget)
        row=dict(qualification_run=1,physical_product_run=1)
        with patch.object(v,"own_inputs",return_value=row):result=new.__globals__["connection_data"](None)
        self.assertEqual(result,dict(row,run=1));self.assertNotIn("run",row)
    def test_outer_entry_one_original_physical_adapter_no_child(self):
        seen=[]
        def run(run):seen.append(("engine",run,binding(None)));return 0
        fn=FunctionType(run.__code__,dict(binding=lambda q:"stale"),closure=run.__closure__)
        connected,state,_=v.RETRY.connect_engine(NS(run_owned=fn,worker=lambda task:0),157)
        api,_=v.M.base.entry()
        class Factory:
            @staticmethod
            def windows_type(old,objects):return old
            @staticmethod
            def close(objects):return True
            @staticmethod
            def summary(objects):return {}
        def binding_attempt(q,run):seen.append(("binding",run));return "WHOLE_ORIGINAL_BINDING"
        call=FunctionType(api.run_owned.__code__,dict(api.run_owned.__globals__,template=lambda:(connected,{}),
            binding_attempt=binding_attempt,attribution=Factory),argdefs=api.run_owned.__defaults__,closure=api.run_owned.__closure__)
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(call(1),0)
        self.assertEqual(seen,[("binding",1),("engine",1,"WHOLE_ORIGINAL_BINDING")]);self.assertEqual(state.actual_engine_calls,1)

if __name__=="__main__":unittest.main()
