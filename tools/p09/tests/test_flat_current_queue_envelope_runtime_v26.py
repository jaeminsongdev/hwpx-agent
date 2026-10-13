import copy
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v26 as m


def data():
    pin=lambda path:dict(path=path,bytes=1,sha256="0"*64)
    return dict(schema_version=m.SCHEMA,index=159,before=152,run=1,physical_product_run=1,
        base_step_pin=m.base.CONFIG.pin,authority_pin=m.current_binding.successor.AUTHORITY,
        prior_runtime_pin=m.current_binding.successor.ROOT,manifest_pin=m.MANIFEST,capsule_pin=m.CAPSULE,
        qualification_pin=pin(m.QUAL),binding_code_pin=pin(m.BINDING_CODE),
        controller_code_pins=[pin(m.SELF),pin(m.TEST)])


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if m.base.CONFIG is None:m.base.configure(159)
        m.only159()
    def test_closed_actual159_DATA_shape(self):
        row=data();self.assertIs(m.validate_data(row),row)
        for bad in (dict(row,extra=True),dict(row,index=True),dict(row,index=158),dict(row,before=151),
                    dict(row,run=2),dict(row,physical_product_run=True)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):m.validate_data(bad)
    def test_actual_authority_root_manifest_capsule_cannot_be_substituted(self):
        for key in ("authority_pin","prior_runtime_pin","manifest_pin","capsule_pin"):
            row=data();row[key]=dict(row[key],sha256="0"*64)
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_data(row)
    def test_qualification_and_binding_path_substitution_rejected(self):
        for key in ("qualification_pin","binding_code_pin"):
            row=data();row[key]=dict(row[key],path="implementation/p09/evidence/wrong.json")
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_data(row)
    def test_controller_pair_must_be_exact_both_sources(self):
        row=data();row["controller_code_pins"][1]=dict(row["controller_code_pins"][1],path="tools/p09/wrong.py")
        with self.assertRaises(ValueError):m.validate_data(row)
    def test_bounded_bootstrap_typed_twenty_pairs(self):
        graph=m.graph_value();self.assertEqual(graph.binding.next_case,159)
        self.assertEqual(len(graph.binding.descriptors()),20)
        self.assertEqual(dict(graph.binding.manifest_pin),m.MANIFEST)
    def test_parent_worker_and_full_oracle_same_private_binding_module(self):
        graph=m.graph_value()
        self.assertIs(graph.parent.access.source,graph.binding_module)
        self.assertIs(graph.worker.raw_policy.source,graph.binding_module)
        self.assertIs(graph.full_oracle.binding_module,graph.binding_module)
    def test_actual_original_engine_and_worker_connected_not_executed(self):
        engine,proof=m.template();state=m.PARENT_STATES[-1]
        self.assertIs(engine.worker,state.original_worker)
        self.assertIs(engine.run_owned.__globals__,state.original.__globals__)
        self.assertEqual(state.attempts,0);self.assertEqual(state.frames,[])
        self.assertEqual(m.prior.ATTEMPT_STATES[-1].physical_product_run,1)
        self.assertEqual(m.prior.ATTEMPT_STATES[-1].actual_engine_calls,0)
    def test_wrong_task_denied_before_bootstrap_or_body(self):
        with patch.object(m,"graph_value") as graph,patch.object(m.prior,"template") as engine:
            for task in ("case158-current-r005-tests","case159-current-r002-tests",True):
                with self.subTest(task=task),self.assertRaises(ValueError):m.worker(task)
        graph.assert_not_called();engine.assert_not_called()
    def test_wrong_physical_run_never_starts_engine(self):
        with patch.object(m.prior.CONNECTION,"connect_run") as run:
            for index in (True,0,2,5):
                with self.subTest(index=index),self.assertRaises(ValueError):m.run_owned(index)
        run.assert_not_called()
    def test_existing_runtime_never_overwritten(self):
        with patch.object(Path,"exists",return_value=True),patch.object(m.prior.CONNECTION,"connect_run") as run:
            with self.assertRaises(ValueError):m.run_owned(1)
        run.assert_not_called()
    def test_missing_whole_pref_denied_before_engine(self):
        with patch.object(Path,"exists",return_value=False),patch.object(Path,"is_file",return_value=False),\
                patch.object(m.prior.CONNECTION,"connect_run") as run:
            with self.assertRaises(ValueError):m.run_owned(1)
        run.assert_not_called()
    def test_independent_acceptance_not_promoted_from_controller_code(self):
        for endpoint in (m.API.prepare,m.API.accept):
            with self.assertRaises(ValueError):endpoint(None,None)
    def test_original_whole_preflight_code_retained_except_destination(self):
        source=m.prior.lean.source;pin=source.prior.prior.prior.METADATA_PIN
        raw=(m.c.ROOT/pin["path"]).read_bytes();leaf=source.prior.leaf_bytes()
        original=m.prior.preflight_projection(raw,leaf);new=m.preflight_projection(raw,leaf)
        self.assertEqual(new.__code__.replace(co_consts=tuple("-product-window-preflight019.v1.json"
            if x=="-envelope-controller-preflight034.v1.json" else x for x in new.__code__.co_consts)),original.__code__)
    def test_bootstrap_reader_denies_original_receipt_path_before_open(self):
        reader=m.bootstrap.Reader(m.old,lambda:None)
        with patch.object(Path,"open") as opened:
            with self.assertRaises(ValueError):reader.pin(m.current_binding.successor.ROOT["path"])
        opened.assert_not_called()


if __name__=="__main__":unittest.main()
