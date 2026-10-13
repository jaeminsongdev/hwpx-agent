import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v9 as v9


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v9.M.base.CONFIG is None:v9.M.base.configure(147)

    def test_exact_namespaces_no_full_module_import_or_hiding(self):
        self.assertNotIn("flat_current_queue_native_diagnostic_runtime_v8",sys.modules)
        self.assertNotIn("native_additional_observer_connection_v1",sys.modules)
        self.assertEqual(v9.OLD8.SELF,v9.OLD8_PIN["path"])
        self.assertEqual(v9.ADDITIONAL_PROOF["retained_leaf_changes"],1)
        self.assertEqual(len(v9.ADDITIONAL_PROOF["cloned_functions"]),6)

    def test_entire_current_prepare_and_native_oracle_code_original(self):
        self.assertIs(v9._full_prepare.__code__,v9.OLD8._full_prepare.__code__)
        self.assertIs(v9._full_prepare.__globals__["data_path"],v9.M.data_path)
        self.assertIs(v9._full_prepare.__globals__["validate_data"],v9.M.validate_data)
        self.assertIs(v9.CURRENT_SOURCE.validate_candidate.__code__,
                      v9.OLD8._full_prepare.__globals__["source"].validate_candidate.__code__)

    def test_previous147_executed_context_not_rebased_to_v9(self):
        fn=v9.previous_function(147)
        self.assertIs(fn.__globals__["context"],v9.OLD8.context)
        self.assertIs(fn.__globals__["validator"],v9.OLD8.validator)
        self.assertIs(fn.__globals__["source"],v9.CURRENT_SOURCE)
        self.assertIs(v9.previous_function(148).__globals__["context"],v9.context)

    def test_successful147_replay_and_bad_closed_data_rejected(self):
        for index in (147,250,True):
            with self.assertRaises(ValueError):v9.data_path(index)
        with self.assertRaises(ValueError):v9.run_owned(1)
        pin=lambda path:dict(path=path,bytes=1,sha256="0"*64)
        step=NS(index=148,before=141,pin=pin("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v9",index=148,before=141,run=1,
         base_step_pin=step.pin,prior_v8_data_pin=pin(v9.OLD8.data_path(148)),qualification_pin=pin(v9.QUAL_PATH),
         controller_code_pins=[pin(v9.SELF),pin(v9.TEST)],additional_observer_code_pins=v9.ADDITIONAL_PINS,
         additional_observer_qualification_pin=v9.ADDITIONAL_QUAL,actual147_pin=v9.ACTUAL147_PIN,actual141_pin=v9.ACTUAL141_PIN)
        self.assertIs(v9.validate_data(row,step),row)
        wrong=copy.deepcopy(row);wrong["actual141_pin"]["sha256"]="1"*64
        with self.assertRaises(ValueError):v9.validate_data(wrong,step)

    def test_real_five_wrappers_reach_fixed_entry_without_product_or_extra_probe(self):
        def stop(run):return 0
        entry=NS(run_owned=FunctionType(stop.__code__,{}));seen=[]
        def called(api,raw,old,backend,state):
            self.assertIs(api,entry);self.assertIs(backend,v9.BACKEND)
            self.assertTrue(raw);seen.append(1);state["actual_local_bindings"]+=1
        fn,state=v9.CONNECTION.connect_run(v9.API.original_run_owned,v9.BACKEND)
        with patch.object(v9.M.base,"entry",return_value=(entry,{})), \
             patch.dict(v9.CONNECTION.connect_run.__globals__,connect_entry=called), \
             patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")), \
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            self.assertEqual(fn(1),0)
        self.assertEqual(seen,[1]);self.assertEqual(state["actual_local_bindings"],1)

    def test_all_original_preflight10_bytecode_and_direct_backend_preserved(self):
        pin=v9.M.source.prior.prior.prior.METADATA_PIN
        data=(v9.M.c.ROOT/pin["path"]).read_bytes()
        leaf=v9.M.source.prior.leaf_bytes()
        old=v9.OLD8.preflight_projection(data,leaf);new=v9.preflight_projection(data,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        engine,_=v9.template()
        self.assertIs(engine.run_owned.__globals__["native"],v9.M.V3.NATIVE)


if __name__=="__main__":unittest.main()
