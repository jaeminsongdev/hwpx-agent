import sys,unittest,copy
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v15 as v

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v.M.base.CONFIG is None:v.M.base.configure(154)

    def test_exact_namespaces_prior153_context_and_full_prepare_unchanged(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v14","metadata_guard_identity_dedup_v1",
          "metadata_guard_identity_connection_v1","reviewed_runtime_attempt_v2"):
            self.assertNotIn(name,sys.modules)
        self.assertIs(v._full_prepare.__code__,v.OLD14._full_prepare.__code__)
        self.assertIs(v._full_prepare.__globals__["data_path"],v.M.data_path)
        fn=v.previous_function(153)
        self.assertIs(fn.__globals__["context"],v.OLD14.context)
        self.assertIs(fn.__globals__["source"],v.OLD14.CURRENT_SOURCE)
        self.assertIs(fn.__globals__["validator"],v.OLD14.validator)
        self.assertIs(v.NATIVE,v.OLD14.NATIVE)
        self.assertIs(v.CONNECTION,v.OLD14.CONNECTION)

    def test_strict_identity_evidence_no_zero_count_or_guard_relaxation(self):
        d=dict(source=v.DEDUP.SELF,original_callback_is_hard=True,calls_avoided=20,
          original_hard_guard_called_first=True,distinct_callback_path_unchanged=True,
          original_warning_latch_validation_and_restore_retained=True,
          source_reads_rates_deadlines_or_guards_weakened=False,added_sampler_thread_or_native_query=False,
          PC_freeze_resolved=False)
        f=dict(checks=20,active=False,original_checkpoint_restored=True,warning_stops=0,latched=False,
          automatic_retry_or_resume=False,complete_source_reads_or_deadlines_weakened=False,identity_duplicate_guard=d)
        row=dict(selected_test_index=154,bootstrap_metadata=dict(early_pressure=dict(metadata_failfast_connection=f)))
        before=copy.deepcopy(row)
        self.assertEqual(v.metadata_identity_evidence(row)["actual_metadata_identity_duplicate_calls_avoided"],20)
        self.assertEqual(row,before)
        for key,value in (("calls_avoided",0),("original_callback_is_hard",False),
          ("source_reads_rates_deadlines_or_guards_weakened",True)):
            wrong=copy.deepcopy(row);wrong["bootstrap_metadata"]["early_pressure"]["metadata_failfast_connection"]["identity_duplicate_guard"][key]=value
            with self.assertRaises(ValueError):v.metadata_identity_evidence(wrong)
        with self.assertRaises(ValueError):v.metadata_identity_evidence(dict(row,selected_test_index=153))

    def test_closed_new_data_historical_run1_current_physical2(self):
        p=lambda name:dict(path=name,bytes=1,sha256="0"*64)
        step=NS(index=154,before=147,pin=p("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v15",index=154,before=147,
          qualification_run=1,physical_product_run=2,base_step_pin=step.pin,
          prior_v14_data_pin=p(v.OLD14.data_path(154)),qualification_pin=p(v.QUAL_PATH),
          controller_code_pins=[p(v.SELF),p(v.TEST)],component_pins=v.COMPONENT_PINS,
          component_qualification_pins=v.COMPONENT_QUAL_PINS,actual153_pin=v.ACTUAL153_PIN,
          actual147_pin=v.ACTUAL147_PIN,reviewed_failure_pins=v.RETRY.HISTORY)
        self.assertIs(v.validate_data(row,step),row)
        for key,value in (("physical_product_run",1),("qualification_run",2),("reviewed_failure_pins",[])):
            with self.assertRaises(ValueError):v.validate_data(dict(row,**{key:value}),step)
        for index in (153,True,250):
            with self.assertRaises(ValueError):v.data_path(index)
        with self.assertRaises(ValueError):v.run_owned(1)

    def test_original_engine_one_adapter_and_original_summary_code(self):
        old,_=v.OLD14.OLD12.template();engine,proof=v.template();state=v.ATTEMPT_STATES[-1]
        self.assertEqual(state.original_engine_code,old.run_owned.__code__)
        self.assertEqual(engine.worker.__code__,old.worker.__code__)
        self.assertTrue(proof["one_current_physical_adapter_not_stacked"])
        self.assertEqual(state.physical_product_run,2);self.assertEqual(state.actual_engine_calls,0)
        summary=proof["metadata_identity_connection"]["summary_projection"]
        self.assertEqual(summary["type_dependency_changes"],1);self.assertEqual(len(summary["functions"]),3)
        self.assertIs(engine.run_owned.__globals__["native"],v.NATIVE)
        self.assertIs(engine.worker.__globals__["native"],v.NATIVE)

    def test_full_preflight10_original_code_and_ephemeral_alias_not_data_rewrite(self):
        p=v.M.source.prior.prior.prior.METADATA_PIN
        raw=(v.M.c.ROOT/p["path"]).read_bytes();leaf=v.M.source.prior.leaf_bytes()
        old=v.OLD14.preflight_projection(raw,leaf);new=v.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        row=dict(qualification_run=1,physical_product_run=2)
        with patch.object(v,"own_inputs",return_value=row):view=new.__globals__["connection_data"](None)
        self.assertEqual(view,dict(row,run=1));self.assertNotIn("run",row)
        self.assertIs(new.__globals__["base"].native,v.NATIVE)

    def test_actual_outer_entry_single_physical_two_binding_one_no_product(self):
        seen=[]
        def engine_run(run):seen.append(("engine",run,binding(None)));return 0
        fn=FunctionType(engine_run.__code__,dict(binding=lambda q:"stale"),closure=engine_run.__closure__)
        connected,state,_=v.RETRY.connect_engine(NS(run_owned=fn,worker=lambda task:0),154)
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
        self.assertEqual(seen,[("binding",1),("engine",2,"FULL_BINDING")])
        self.assertEqual(state.actual_engine_calls,1)

if __name__=="__main__":unittest.main()
