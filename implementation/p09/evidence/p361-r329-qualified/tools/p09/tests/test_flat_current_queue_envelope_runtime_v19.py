import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v19 as m


def data():
    pin=lambda name:dict(path=name,bytes=1,sha256="0"*64)
    return dict(schema_version=m.SCHEMA,index=158,before=151,run=1,base_step_pin=m.base.CONFIG.pin,
        manifest_pin=pin(m.manifest.PATH),capsule_pin=m.CAPSULE,qualification_pin=pin(m.QUAL),
        controller_code_pins=[pin(m.SELF),pin(m.TEST)])


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if m.base.CONFIG is None:m.base.configure(158)

    def test_exact_pinned_capsule_has_all11_and_manifest(self):
        binding=m.binding_value()
        self.assertEqual(len(binding.originals),11)
        self.assertEqual(binding.next_case,158)
        self.assertEqual(binding.manifest_pin["path"],m.manifest.PATH)
        self.assertEqual(len(m.NAMESPACE_PROOF),16)
        self.assertTrue(all(p["original_function_class_constants_and_initialization_AST_retained"]
            and not p["actual_module_imported_or_sys_modules_hidden"] for p in m.NAMESPACE_PROOF))

    def test_closed_DATA_and_controller_pair_shape(self):
        row=data();self.assertIs(m.validate_data(row),row)
        for bad in (dict(row,extra=True),dict(row,index=True),dict(row,before=150),dict(row,run=2)):
            with self.assertRaises(ValueError):m.validate_data(bad)

    def test_qualification_capsule_or_manifest_path_substitution_denied(self):
        row=data()
        for key in ("qualification_pin","manifest_pin","capsule_pin"):
            bad=dict(row);bad[key]=dict(row[key],path="implementation/p09/evidence/substitution.json")
            with self.assertRaises(ValueError):m.validate_data(bad)

    def test_prior157_oracle_uses_unchanged_prior_callback(self):
        token=object();ctx=NS(INDEX=157)
        with patch.object(m,"_accepted_validator",return_value=token) as callback:
            self.assertIs(m.validator(b"source",ctx,False),token)
        callback.assert_called_once_with(b"source",ctx,False)

    def test_real_current158_template_keeps_original_worker_and_no_engine_calls(self):
        engine,proof=m.template();state=m.PARENT_STATES[-1]
        self.assertIs(engine.worker,state.original_worker)
        self.assertIs(engine.run_owned.__globals__,state.original.__globals__)
        self.assertEqual(state.attempts,0);self.assertEqual(state.frames,[])
        self.assertTrue(proof["explicit_parent_physical_Frame_connected"])

    def test_original_full_preflight_body_preserved_and_new_destination(self):
        source=m.prior.lean.source
        pin=source.prior.prior.prior.METADATA_PIN
        raw=(m.c.ROOT/pin["path"]).read_bytes()
        self.assertEqual(len(raw),pin["bytes"]);self.assertEqual(hashlib.sha256(raw).hexdigest(),pin["sha256"])
        leaf=source.prior.leaf_bytes()
        old=m.prior.preflight_projection(raw,leaf);new=m.preflight_projection(raw,leaf)
        old_name="-product-window-preflight019.v1.json";new_name="-envelope-controller-preflight025.v1.json"
        self.assertIn(new_name,new.__code__.co_consts)
        restored=new.__code__.replace(co_consts=tuple(old_name if x==new_name else x for x in new.__code__.co_consts))
        self.assertEqual(restored,old.__code__)

    def test_existing_runtime_receipt_and_other_worker_task_never_replayed(self):
        with patch.object(Path,"exists",return_value=True):
            with self.assertRaisesRegex(ValueError,"ROOT_OVERWRITE"):m.run_owned(1)
        for value in (True,2):
            with self.assertRaises(ValueError):m.run_owned(value)
        with self.assertRaises(ValueError):m.worker("case157-current-r001-tests")


if __name__=="__main__":unittest.main()
