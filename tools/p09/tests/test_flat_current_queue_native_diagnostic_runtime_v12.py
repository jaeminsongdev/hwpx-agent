import copy
import sys
import unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v12 as v12

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v12.M.base.CONFIG is None:v12.M.base.configure(150)

    def test_exact_namespaces_no_full_module_import_or_hiding(self):
        for name in ("flat_current_queue_native_diagnostic_runtime_v9",
                     "native_process_cpu_attribution_v3","native_diagnostic_connection_v3",
                     "native_diagnostic_oracle_connection_v2"):
            self.assertNotIn(name,sys.modules)
        self.assertEqual(v12.BACKEND.BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V3")
        self.assertEqual(v12.ORACLE_PROOF["additional"]["retained_leaf_changes"],1)
        self.assertEqual(len(v12.ORACLE_PROOF["additional"]["cloned_functions"]),6)
        self.assertEqual(v12.COMPACT.SELF,"tools/p09/compact_runtime_record_v1.py")
        self.assertIs(v12.NATIVE.load.__code__,v12.M.V3.NATIVE.load.__code__)

    def test_entire_current_prepare_and_native_oracle_code_original(self):
        self.assertIs(v12._full_prepare.__code__,v12.OLD11._full_prepare.__code__)
        self.assertIs(v12._full_prepare.__globals__["data_path"],v12.M.data_path)
        self.assertIs(v12._full_prepare.__globals__["validate_data"],v12.M.validate_data)
        self.assertIs(v12.CURRENT_SOURCE.validate_candidate.__code__,
                      v12.OLD11.CURRENT_SOURCE.validate_candidate.__code__)

    def test_previous148_executed_context_not_rebased(self):
        fn=v12.previous_function(150)
        self.assertIs(fn.__globals__["context"],v12.OLD11.context)
        self.assertIs(fn.__globals__["validator"],v12.OLD11.validator)
        self.assertIs(fn.__globals__["source"],v12.CURRENT_SOURCE)
        self.assertIs(v12.previous_function(147).__globals__["context"],v12.OLD11.OLD10.OLD9.OLD8.context)
        self.assertIs(v12.previous_function(151).__globals__["context"],v12.context)
        self.assertEqual(v12.ORACLE.for_index(148).BACKEND,"NATIVE_TOOLHELP_PROCESS_TIMES_V2")
        self.assertIs(v12.ORACLE.for_index(149),v12.CONNECTION)

    def test_no_successful_replay_and_closed_new_data(self):
        for index in (150,149,250,True):
            with self.assertRaises(ValueError):v12.data_path(index)
        with self.assertRaises(ValueError):v12.run_owned(1)
        pin=lambda path:dict(path=path,bytes=1,sha256="0"*64)
        step=NS(index=151,before=144,pin=pin("step"))
        row=dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v12",index=151,before=144,run=1,
         base_step_pin=step.pin,prior_v11_data_pin=pin(v12.OLD11.data_path(151)),qualification_pin=pin(v12.QUAL_PATH),
         controller_code_pins=[pin(v12.SELF),pin(v12.TEST)],component_pins=v12.COMPONENT_PINS,
         component_qualification_pins=v12.COMPONENT_QUAL_PINS,actual150_pin=v12.ACTUAL150_PIN,actual144_pin=v12.ACTUAL144_PIN)
        self.assertIs(v12.validate_data(row,step),row)
        wrong=copy.deepcopy(row);wrong["actual144_pin"]["sha256"]="1"*64
        with self.assertRaises(ValueError):v12.validate_data(wrong,step)

    def test_real_five_wrappers_fixed_entry_no_product_or_extra_probe(self):
        def stop(run):return 0
        entry=NS(run_owned=FunctionType(stop.__code__,{}));seen=[]
        def called(api,raw,old,backend,state):
            self.assertIs(api,entry);self.assertIs(backend,v12.BACKEND)
            self.assertTrue(raw);seen.append(1);state["actual_local_bindings"]+=1
        with patch.object(v12.M.base,"entry",return_value=(entry,{})), \
             patch.dict(v12.CONNECTION.connect_run.__globals__,connect_entry=called), \
             patch("subprocess.Popen",side_effect=AssertionError("NO_CHILD")), \
             patch("subprocess.run",side_effect=AssertionError("NO_CHILD")):
            fn,state=v12.CONNECTION.connect_run(v12.API.original_run_owned,v12.BACKEND)
            self.assertEqual(fn(1),0)
        self.assertEqual(seen,[1]);self.assertEqual(state["actual_local_bindings"],1)

    def test_all_original_preflight10_bytecode_and_direct_backend(self):
        pin=v12.M.source.prior.prior.prior.METADATA_PIN
        data=(v12.M.c.ROOT/pin["path"]).read_bytes();leaf=v12.M.source.prior.leaf_bytes()
        old=v12.OLD11.preflight_projection(data,leaf);new=v12.preflight_projection(data,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        oldengine,_=v12.OLD11.template()
        engine,proof=v12.template()
        self.assertEqual(engine.run_owned.__code__.replace(co_code=oldengine.run_owned.__code__.co_code,
            co_names=oldengine.run_owned.__code__.co_names),oldengine.run_owned.__code__)
        self.assertFalse(proof["original_engine_bytecode_unchanged"])
        self.assertIs(engine.run_owned.__globals__["native"],v12.NATIVE)
        self.assertIs(engine.worker.__globals__["native"],v12.NATIVE)

if __name__=="__main__":unittest.main()
