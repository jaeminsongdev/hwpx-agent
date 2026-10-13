import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v10 as v10

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v10.M.base.CONFIG is None:v10.M.base.configure(148)

    def test_exact_namespaces_no_full_module_import_or_hiding(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v9",
                     "native_process_cpu_attribution_v3","native_diagnostic_connection_v3",
                     "native_diagnostic_oracle_connection_v2"):
            self.assertNotIn(name,sys.modules)
        self.assertEqual(v10.BACKEND.BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V3")
        self.assertEqual(v10.ORACLE_PROOF["additional"]["retained_leaf_changes"],1)
        self.assertEqual(len(v10.ORACLE_PROOF["additional"]["cloned_functions"]),6)
        self.assertIs(v10.BACKEND.native,v10.CAPTURE)

    def test_entire_current_prepare_and_native_oracle_code_original(self):
        self.assertIs(v10._full_prepare.__code__,v10.OLD9._full_prepare.__code__)
        self.assertIs(v10._full_prepare.__globals__["data_path"],v10.M.data_path)
        self.assertIs(v10._full_prepare.__globals__["validate_data"],v10.M.validate_data)
        self.assertIs(v10.CURRENT_SOURCE.validate_candidate.__code__,
                      v10.OLD9.CURRENT_SOURCE.validate_candidate.__code__)

    def test_previous148_executed_context_not_rebased(self):
        fn=v10.previous_function(148)
        self.assertIs(fn.__globals__["context"],v10.OLD9.context)
        self.assertIs(fn.__globals__["validator"],v10.OLD9.validator)
        self.assertIs(fn.__globals__["source"],v10.CURRENT_SOURCE)
        self.assertIs(v10.previous_function(147).__globals__["context"],v10.OLD9.OLD8.context)
        self.assertIs(v10.previous_function(149).__globals__["context"],v10.context)
        self.assertEqual(v10.ORACLE.for_index(148).BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V2")
        self.assertIs(v10.ORACLE.for_index(149),v10.CONNECTION)

    def test_no_successful_replay_and_closed_new_data(self):
        for index in (148,147,250,True):
            with self.assertRaises(ValueError):v10.data_path(index)
        with self.assertRaises(ValueError):v10.run_owned(1)
        pin=lambda path:dict(path=path,bytes=1,sha256="0"*64)
        step=NS(index=149,before=142,pin=pin("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v10",index=149,before=142,run=1,
         base_step_pin=step.pin,prior_v9_data_pin=pin(v10.OLD9.data_path(149)),qualification_pin=pin(v10.QUAL_PATH),
         controller_code_pins=[pin(v10.SELF),pin(v10.TEST)],component_pins=v10.COMPONENT_PINS,
         component_qualification_pins=v10.COMPONENT_QUAL_PINS,actual148_pin=v10.ACTUAL148_PIN,actual142_pin=v10.ACTUAL142_PIN)
        self.assertIs(v10.validate_data(row,step),row)
        wrong=copy.deepcopy(row);wrong["actual142_pin"]["sha256"]="1"*64
        with self.assertRaises(ValueError):v10.validate_data(wrong,step)

    def test_real_five_wrappers_fixed_entry_no_product_or_extra_probe(self):
        def stop(run):return 0
        entry=NS(run_owned=FunctionType(stop.__code__,{}));seen=[]
        def called(api,raw,old,backend,state):
            self.assertIs(api,entry);self.assertIs(backend,v10.BACKEND)
            self.assertTrue(raw);seen.append(1);state["actual_local_bindings"]+=1
        with patch.object(v10.M.base,"entry",return_value=(entry,{})), \
             patch.dict(v10.CONNECTION.connect_run.__globals__,connect_entry=called), \
             patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")), \
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            fn,state=v10.CONNECTION.connect_run(v10.API.original_run_owned,v10.BACKEND)
            self.assertEqual(fn(1),0)
        self.assertEqual(seen,[1]);self.assertEqual(state["actual_local_bindings"],1)

    def test_all_original_preflight10_bytecode_and_direct_backend(self):
        pin=v10.M.source.prior.prior.prior.METADATA_PIN
        data=(v10.M.c.ROOT/pin["path"]).read_bytes();leaf=v10.M.source.prior.leaf_bytes()
        old=v10.OLD9.preflight_projection(data,leaf);new=v10.preflight_projection(data,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        engine,_=v10.template()
        self.assertIs(engine.run_owned.__globals__["native"],v10.M.V3.NATIVE)

if __name__=="__main__":unittest.main()
