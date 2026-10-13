import sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_pressure_runtime_v17 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(156)
    def test_exact_namespaces_and_historical155_context_preserved(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v16","native_pressure_failfast_v1","native_pressure_full_connection_v1"):
            self.assertNotIn(name,sys.modules)
        self.assertIs(v._full_prepare.__code__,v.OLD16._full_prepare.__code__)
        self.assertIs(v._full_prepare.__globals__["data_path"],v.M.data_path)
        fn=v.previous_function(155);old=v.OLD16.previous_function(155)
        self.assertIs(fn.__code__,old.__code__);self.assertIs(fn.__globals__["source"],old.__globals__["source"])
        self.assertIs(fn.__globals__["context"],old.__globals__["context"])
        self.assertIs(v.CONNECTION,v.OLD16.CONNECTION);self.assertIs(v.BACKEND,v.OLD16.BACKEND)
    def test_closed_data017_exactcutover_and_no_replay(self):
        p=lambda name:dict(path=name,bytes=1,sha256="0"*64)
        step=NS(index=156,before=149,pin=p("step"))
        row=dict(schema_version="hwpx-agent.p09-native-pressure-controller/v17",index=156,before=149,
            qualification_run=1,physical_product_run=1,base_step_pin=step.pin,
            prior_v16_data_pin=p(v.OLD16.data_path(156)),qualification_pin=p(v.QUAL_PATH),
            controller_code_pins=[p(v.SELF),p(v.TEST)],component_pins=v.COMPONENT_PINS,
            component_qualification_pins=v.COMPONENT_QUAL_PINS,actual155_pin=v.ACTUAL155_PIN,
            actual149_pin=v.ACTUAL149_PIN,failed_preflight_pin=v.FAILED_PREFLIGHT_PIN)
        self.assertIs(v.validate_data(row,step),row)
        for key,value in (("physical_product_run",2),("qualification_run",True),("failed_preflight_pin",None),("component_pins",[])):
            with self.assertRaises(ValueError):v.validate_data(dict(row,**{key:value}),step)
        for index in (155,True,250):
            with self.assertRaises(ValueError):v.data_path(index)
        with self.assertRaises(ValueError):v.run_owned(2)
    def test_whole_engine_worker_codes_one_adapter_new_native_and_budget(self):
        old,_=v.OLD16.template();engine,proof=v.template()
        oldstate=v.OLD16.ATTEMPT_STATES[-1];state=v.ATTEMPT_STATES[-1]
        self.assertEqual(state.original_engine_code,oldstate.original_engine_code)
        self.assertIs(engine.worker.__code__,old.worker.__code__)
        self.assertIs(engine.run_owned.__globals__["native"],v.NATIVE)
        self.assertIs(engine.worker.__globals__["native"],v.NATIVE)
        self.assertIs(engine.run_owned.__globals__["runtime_budget"],v.DIRECT.runtime_budget)
        self.assertEqual(state.actual_engine_calls,0);self.assertEqual(state.physical_product_run,1)
        self.assertTrue(proof["no_additional_physical_adapter"])
    def test_new_validator_only156_plus_and_all_original_product_checks_retained(self):
        pin=v.original_candidate.ACCEPTOR_PIN;raw=(v.M.c.ROOT/pin["path"]).read_bytes()
        fn,proof=v.validator(raw,v.context(v.M.base.CONFIG))
        self.assertIs(fn.__globals__["ORACLE_SCOPE"].cost,v.DIRECT.cost)
        self.assertIn(v.SELF,fn.__globals__["CONTROLLERS"])
        ctx=NS(**{**vars(v.context(v.M.base.CONFIG)),"INDEX":155})
        old,_=v.OLD16.validator(raw,ctx);historical,p=v.validator(raw,ctx)
        self.assertIs(historical.__globals__["ORACLE_SCOPE"].cost,old.__globals__["ORACLE_SCOPE"].cost)
        self.assertNotIn(v.SELF,historical.__globals__["CONTROLLERS"])
        self.assertIs(v.linked.__code__,v.OLD16._original_source.validate_candidate.__code__)
        self.assertFalse(p["explicit_terminal_pressure_context"])
    def test_full_preflight_original10_code_ephemeral_alias_and_complete_cost(self):
        p=v.M.source.prior.prior.prior.METADATA_PIN
        raw=(v.M.c.ROOT/p["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        old=v.OLD16.preflight_projection(raw,leaf);new=v.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIn("-native-pressure-preflight018.v1.json",new.__code__.co_consts)
        self.assertIs(new.__globals__["base"].native,v.NATIVE)
        self.assertIs(new.__globals__["base"].stable.runtime_budget,v.DIRECT.runtime_budget)
        row=dict(qualification_run=1,physical_product_run=1)
        with patch.object(v,"own_inputs",return_value=row):result=new.__globals__["connection_data"](None)
        self.assertEqual(result,dict(row,run=1));self.assertNotIn("run",row)
    def test_outer_entry_one_physical_run_one_binding_no_children(self):
        seen=[]
        def engine_run(run):seen.append(("engine",run,binding(None)));return 0
        fn=FunctionType(engine_run.__code__,dict(binding=lambda q:"stale"),closure=engine_run.__closure__)
        connected,state,_=v.RETRY.connect_engine(NS(run_owned=fn,worker=lambda task:0),156)
        api,_=v.M.base.entry()
        class Factory:
            @staticmethod
            def windows_type(old,objects):return old
            @staticmethod
            def close(objects):return True
            @staticmethod
            def summary(objects):return {}
        def binding_attempt(q,run):seen.append(("binding",run));return "WHOLE_ORIGINAL_BINDING"
        call=FunctionType(api.run_owned.__code__,dict(api.run_owned.__globals__,
            template=lambda:(connected,{}),binding_attempt=binding_attempt,attribution=Factory),
            argdefs=api.run_owned.__defaults__,closure=api.run_owned.__closure__)
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(call(1),0)
        self.assertEqual(seen,[("binding",1),("engine",1,"WHOLE_ORIGINAL_BINDING")]);self.assertEqual(state.actual_engine_calls,1)

if __name__=="__main__":unittest.main()
