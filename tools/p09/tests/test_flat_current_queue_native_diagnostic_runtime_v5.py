import ast
import copy
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_native_diagnostic_runtime_v5 as v5


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if v5.M.base.CONFIG is None:
            v5.M.base.configure(146)
        if v5.M.base.CONFIG.index!=146:
            raise ValueError("TEST_ONLY_IMMUTABLE146")

    def data(self):
        step=v5.M.base.CONFIG
        pin=lambda path:dict(path=path,bytes=1,sha256="1"*64)
        return step,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v5",index=146,before=139,
                        run=1,base_step_pin=step.pin,prior_v4_data_pin=pin(v5.M.data_path(146)),
                        qualification_pin=pin(v5.QUAL_PATH),controller_code_pins=[pin(v5.SELF),pin(v5.TEST)],
                        native_component_pins=v5.FIXED_PINS)

    def test_all_exact_namespaces_no_module_import_or_hiding(self):
        self.assertEqual(v5.BACKEND.SELF,"tools/p09/native_process_cpu_attribution_v2.py")
        for name in ("native_process_cpu_attribution_v1","native_process_cpu_attribution_v2",
                     "bounded_cpu_attribution_probe_v1","native_diagnostic_connection_v1",
                     "native_diagnostic_oracle_connection_v1","flat_current_queue_direct_view_runtime_v4"):
            self.assertNotIn(name,sys.modules)

    def test_namespace_AST_unchanged_and_no_CLI(self):
        raw=b"import unavailable\nVALUE=4\ndef function():return VALUE\nif __name__=='__main__':raise AssertionError()\n"
        pin=dict(path="fixture.py",bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(v5.namespace(raw,pin,{}).function(),4)
        with self.assertRaises(ValueError):v5.namespace(raw+b" ",pin,{})

    def test_closed_data_and_original_v4_pin(self):
        step,row=self.data();self.assertIs(v5.validate_data(row,step),row)
        for key,value in (("run",2),("index",145),("before",138)):
            bad=copy.deepcopy(row);bad[key]=value
            with self.assertRaises(ValueError):v5.validate_data(bad,step)

    def test_extra_or_missing_data_rejected(self):
        step,row=self.data()
        for missing in (True,False):
            bad=copy.deepcopy(row)
            if missing:bad.pop("native_component_pins")
            else:bad["automatic_retry"]=True
            with self.assertRaises(ValueError):v5.validate_data(bad,step)

    def test_all_original_source_pins_preserved(self):
        step,row=self.data();bad=copy.deepcopy(row);bad["native_component_pins"]=bad["native_component_pins"][:-1]
        with self.assertRaises(ValueError):v5.validate_data(bad,step)
        self.assertEqual(len(v5.FIXED_PINS),11)

    def test_data_only_first_explicit_successor(self):
        for index in (145,250,True):
            with self.assertRaises(ValueError):v5.data_path(index)
        self.assertTrue(v5.data_path(146).endswith("-native-diagnostic-data005.v1.json"))

    def test_original_factory_body_and_direct_backend_unchanged(self):
        engine,proof=v5.template();old,_=v5.M.template()
        # Each exact-source template compiles a fresh code object; compare ALL
        # code fields, not Python object identity across separate compilations.
        self.assertEqual(engine.run_owned.__code__,old.run_owned.__code__)
        self.assertIs(engine.run_owned.__globals__["native"],v5.M.V3.NATIVE)
        self.assertEqual(engine.worker.__globals__["SELF"],v5.SELF)
        self.assertTrue(proof["original_engine_and_direct_view_backend_unchanged"])

    def test_full_candidate_code_preserved_with_one_diagnostic_leaf(self):
        old=v5.M.API.prepare.__globals__["source"].validate_candidate
        new=v5.API.prepare.__globals__["source"].validate_candidate
        self.assertIs(old.__code__,new.__code__)
        _,proof=v5.ORACLE.connect_candidate(old)
        self.assertEqual(proof["diagnostic_leaf_changes"],1)
        self.assertEqual(len(proof["cloned_functions"]),6)

    def test_runtime_binding_keeps_five_original_run_functions(self):
        fn,state=v5.CONNECTION.connect_run(v5.API.original_run_owned,v5.BACKEND)
        self.assertIs(fn.__code__,v5.API.original_run_owned.__code__)
        self.assertEqual(len(state["cloned_functions"]),5)
        self.assertEqual(state["actual_local_bindings"],0)

    def test_run_refuses_retry_or_unobserved_connection(self):
        with self.assertRaises(ValueError):v5.run_owned(2)
        with patch.object(v5.CONNECTION,"connect_run",return_value=(lambda run:0,dict(actual_local_bindings=0))):
            with self.assertRaises(ValueError):v5.run_owned(1)

    def test_old_predecessor_not_rebased_to_native_diagnostic(self):
        with patch.object(v5.M,"previous_validation",return_value="legacy") as old:
            self.assertEqual(v5.previous_validation(None,{},None,None,None,NS(INDEX=145)),"legacy")
        old.assert_called_once()

    def test_preflight_preserves_full_tests_and_raw_bytecode(self):
        pin=v5.M.source.prior.prior.prior.METADATA_PIN
        raw=(v5.M.c.ROOT/pin["path"]).read_bytes()
        leaf=v5.M.source.prior.leaf_bytes()
        old=v5.M.preflight_projection(raw,leaf);new=v5.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=old.__code__.co_consts),old.__code__)
        self.assertIn("-native-diagnostic-preflight005.v1.json",new.__code__.co_consts)


if __name__=="__main__":unittest.main()
