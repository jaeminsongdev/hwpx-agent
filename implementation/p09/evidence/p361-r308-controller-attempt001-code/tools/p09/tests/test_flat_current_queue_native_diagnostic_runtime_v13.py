import copy,sys,unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v13 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(153)

    def test_exact_namespaces_and_all_full_native_source_bodies(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v12","native_process_cpu_attribution_v4",
          "native_diagnostic_connection_v4","native_diagnostic_oracle_connection_v3","reviewed_runtime_attempt_v1"):
            self.assertNotIn(name,sys.modules)
        self.assertEqual(v.BACKEND.BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V4")
        self.assertEqual(len(v.ORACLE_PROOF["additional"]["cloned_functions"]),6)
        self.assertTrue(v.ORACLE_PROOF["all_original_full_candidate_code_retained"])
        self.assertIs(v.NATIVE,v.OLD12.NATIVE)
        self.assertIs(v._full_prepare.__code__,v.OLD12._full_prepare.__code__)
        self.assertIs(v._full_prepare.__globals__["data_path"],v.M.data_path)
        self.assertIs(v.CURRENT_SOURCE.prepare.__code__,v.OLD12.CURRENT_SOURCE.prepare.__code__)
        self.assertIs(v.CURRENT_SOURCE.prepare_projection.__code__,v.OLD12.CURRENT_SOURCE.prepare_projection.__code__)
        self.assertIs(v.CURRENT_SOURCE.prepare_projection.__globals__["root_path"],v.RETRY.root_path)

    def test_executed152_context_and_scratch_historical_dispatch_unchanged(self):
        fn=v.previous_function(152)
        self.assertIs(fn.__globals__["context"],v.OLD12.context)
        self.assertIs(fn.__globals__["validator"],v.OLD12.validator)
        self.assertIs(fn.__globals__["source"],v.OLD12.CURRENT_SOURCE)
        self.assertIs(v.CONNECTION.validate_historical_v3,v.OLD12.CONNECTION.validate)
        self.assertIs(v.ORACLE.for_index(152).validate,v.OLD12.CONNECTION.validate)
        self.assertIs(v.ORACLE.for_index(153),v.CONNECTION)
        self.assertEqual(v.ORACLE.for_index(148).BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V2")
        self.assertIs(v.previous_function(153).__globals__["context"],v.context)

    def test_closed_data_explicit_logical_one_physical_two_and_no_replay(self):
        pin=lambda p:dict(path=p,bytes=1,sha256="0"*64)
        step=NS(index=153,before=146,pin=pin("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v13",index=153,before=146,
          qualification_run=1,physical_product_run=2,base_step_pin=step.pin,
          prior_v12_data_pin=pin(v.OLD12.data_path(153)),qualification_pin=pin(v.QUAL_PATH),
          controller_code_pins=[pin(v.SELF),pin(v.TEST)],component_pins=v.COMPONENT_PINS,
          component_qualification_pins=v.COMPONENT_QUAL_PINS,actual152_pin=v.ACTUAL152_PIN,
          actual146_pin=v.ACTUAL146_PIN,reviewed_failure_pins=[v.RETRY.STOPPED,v.RETRY.REVIEW])
        self.assertIs(v.validate_data(row,step),row)
        for key,value in (("physical_product_run",1),("qualification_run",2),("actual146_pin",pin("wrong"))):
            wrong=dict(row,**{key:value})
            with self.assertRaises(ValueError):v.validate_data(wrong,step)
        for index in (152,250,True):
            with self.assertRaises(ValueError):v.data_path(index)
        with self.assertRaises(ValueError):v.run_owned(1)
        with self.assertRaises(ValueError):v.run_owned(3)

    def test_actual_five_wrapper_native4_leaf_exact_original_no_child(self):
        def stop(run):return 0
        entry=NS(run_owned=FunctionType(stop.__code__,{}));seen=[]
        def called(api,raw,old,backend,state):
            self.assertIs(api,entry);self.assertIs(backend,v.BACKEND)
            self.assertTrue(raw);seen.append(1);state["actual_local_bindings"]+=1
        with patch.object(v.M.base,"entry",return_value=(entry,{})),\
             patch.dict(v.RAW_CONNECTION.connect_run.__globals__["prior"].prior.connect_run.__globals__,connect_entry=called),\
             patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),\
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            # NativeV4 connect_run copies this prior code and replaces connect_entry;
            # isolate its actual private entry function rather than that overwritten global.
            original=v.RAW_CONNECTION.connect_run.__globals__["connect_entry"]
            v.RAW_CONNECTION.connect_run.__globals__["connect_entry"]=called
            try:fn,state=v.CONNECTION.connect_run(v.API.original_run_owned,v.BACKEND);self.assertEqual(fn(1),0)
            finally:v.RAW_CONNECTION.connect_run.__globals__["connect_entry"]=original
        self.assertEqual(seen,[1]);self.assertEqual(state["actual_local_bindings"],1)
        self.assertEqual(len(state["cloned_functions"]),5)

    def test_entire_preflight10_code_and_same_binding_environment_for_engine(self):
        pin=v.M.source.prior.prior.prior.METADATA_PIN
        raw=(v.M.c.ROOT/pin["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        old=v.OLD12.preflight_projection(raw,leaf);new=v.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIs(new.__globals__["base"].native,v.NATIVE)
        oldengine,_=v.OLD12.template()
        engine,proof=v.template();state=v.ATTEMPT_STATES[-1]
        self.assertEqual(state.original_engine_code,oldengine.run_owned.__code__)
        self.assertIs(engine.worker.__code__,oldengine.worker.__code__)
        self.assertIs(engine.run_owned.__globals__["native"],v.NATIVE)
        self.assertTrue(proof["reviewed_physical_attempt"]["original_private_binding_environment_shared"])
        self.assertEqual(state.physical_product_run,2);self.assertEqual(state.actual_engine_calls,0)
        self.assertIs(engine.worker.__globals__["native"],v.NATIVE)

    def test_real_outer_entry_to_original_physical_engine_two_and_binding_one(self):
        seen=[]
        def engine_run(run):seen.append(("engine",run,binding(None)));return 0
        def worker(task):return task
        actual=FunctionType(engine_run.__code__,dict(binding=lambda q:"stale"),closure=engine_run.__closure__)
        fake=NS(run_owned=actual,worker=worker)
        connected,state,_=v.RETRY.connect_engine(fake,153)
        api,_=v.M.base.entry()
        # Execute the FULL original sole-observer entry, replacing ONLY OS observer
        # factory/patch context with inert fixtures. Never spawn a product.
        class Factory:
            @staticmethod
            def windows_type(old,objects):return old
            @staticmethod
            def close(objects):return True
            @staticmethod
            def summary(objects):return {}
        def binding_attempt(q,run):seen.append(("binding",run));return "FULL_BINDING_ONE"
        fn=FunctionType(api.run_owned.__code__,dict(api.run_owned.__globals__,
          template=lambda:(connected,{}),binding_attempt=binding_attempt,attribution=Factory),
          argdefs=api.run_owned.__defaults__,closure=api.run_owned.__closure__)
        with patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")),\
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(fn(1),0)
        self.assertEqual(seen,[("binding",1),("engine",2,"FULL_BINDING_ONE")])
        self.assertEqual(state.actual_engine_calls,1)

if __name__=="__main__":unittest.main()
