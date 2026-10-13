import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v7 as v7


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v7.M.base.CONFIG is None:v7.M.base.configure(146)

    def test_exact_base_and_fix_namespaces_no_module_import_or_hiding(self):
        self.assertEqual(v7.BASE.SELF,v7.BASE_PIN["path"])
        self.assertNotIn("flat_current_queue_native_diagnostic_runtime_v6",sys.modules)
        self.assertNotIn("native_diagnostic_connection_v2",sys.modules)
        self.assertIs(v7.CONNECTION.validate,v7.BASE.CONNECTION.validate)

    def test_successful146_replay_and_retry_denied(self):
        for index in (146,250,True):
            with self.assertRaises(ValueError):v7.data_path(index)
        with self.assertRaises(ValueError):v7.run_owned(1)

    def test_original_DATA004_postchecks_not_fed_DATA007(self):
        fn=v7._full_prepare
        self.assertIs(fn.__code__,v7.BASE.API.prepare.__code__)
        self.assertIs(fn.__globals__["data_path"],v7.M.data_path)
        self.assertIs(fn.__globals__["validate_data"],v7.M.validate_data)
        self.assertIs(fn.__globals__["own_inputs"],v7.own_inputs)
        self.assertNotEqual(fn.__globals__["data_path"](147),v7.data_path(147))

    def test_current_full_candidate_stays_native_strict(self):
        self.assertIs(v7._full_prepare.__globals__["source"],
                      v7.BASE.API.prepare.__globals__["source"])
        row=dict(selected_test_index=147,serial_CPU_attribution={})
        with self.assertRaises(ValueError):v7.BASE.ORACLE.dispatch(lambda row:True,row)

    def test_exact146_historical_context_is_preserved(self):
        fn=v7.legacy146_previous_function()
        self.assertIs(fn.__code__,v7.M.V3.OLD.API.previous_validation.__code__)
        self.assertIs(fn.__globals__["context"],v7.BASE.context)
        self.assertIs(fn.__globals__["validator"],v7.BASE.validator)
        self.assertIs(fn.__globals__["source"],v7.M.API.prepare.__globals__["source"])

    def test_five_real_wrappers_reach_fixed_binding_without_product(self):
        def stopped(run):return 0
        entry=NS(run_owned=FunctionType(stopped.__code__,{}));calls=[]
        def reached(api,raw,old,backend,state):
            self.assertIs(api,entry);self.assertTrue(raw);self.assertIs(backend,v7.BACKEND)
            calls.append(1);state["actual_local_bindings"]+=1
        execute,state=v7.CONNECTION.connect_run(v7.API.original_run_owned,v7.BACKEND)
        with patch.object(v7.M.base,"entry",return_value=(entry,{})), \
             patch.dict(v7.CONNECTION.connect_run.__globals__,connect_entry=reached), \
             patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")), \
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(execute(1),0)
        self.assertEqual(calls,[1]);self.assertEqual(state["actual_local_bindings"],1)
        self.assertEqual(len(state["cloned_functions"]),5)

    def test_original_engine_and_direct_native_backend_unchanged(self):
        engine,proof=v7.template();old,_=v7.BASE.template()
        self.assertEqual(engine.run_owned.__code__,old.run_owned.__code__)
        self.assertIs(engine.run_owned.__globals__["native"],v7.M.V3.NATIVE)
        self.assertEqual(engine.worker.__globals__["SELF"],v7.SELF)

    def test_closed_data_binds_exact_cutover_no_general_legacy_fallback(self):
        pin=lambda name:dict(path=name,bytes=1,sha256="0"*64)
        step=NS(index=147,before=140,pin=pin("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v7",index=147,before=140,run=1,
         base_step_pin=step.pin,prior_v6_data_pin=pin(v7.BASE.data_path(147)),qualification_pin=pin(v7.QUAL_PATH),
         controller_code_pins=[pin(v7.SELF),pin(v7.TEST)],namespace_fix_code_pins=v7.FIX_PINS,
         namespace_fix_qualification_pin=v7.FIX_QUAL,recorded_legacy146_pin=v7.LEGACY146_PIN,
         recorded_legacy146_authority_pin=v7.LEGACY146_AUTH)
        self.assertIs(v7.validate_data(row,step),row)
        bad=copy.deepcopy(row);bad["recorded_legacy146_pin"]["sha256"]="1"*64
        with self.assertRaises(ValueError):v7.validate_data(bad,step)
        bad=copy.deepcopy(row);bad["automatic_legacy_fallback"]=True
        with self.assertRaises(ValueError):v7.validate_data(bad,step)

    def test_original_all_metadata10_preflight_body_and_only_new_destination(self):
        pin=v7.M.source.prior.prior.prior.METADATA_PIN
        raw=(v7.M.c.ROOT/pin["path"]).read_bytes()
        leaf=v7.M.source.prior.leaf_bytes()
        old=v7.BASE.preflight_projection(raw,leaf);new=v7.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIn("-native-diagnostic-preflight007.v1.json",new.__code__.co_consts)


if __name__=="__main__":unittest.main()

