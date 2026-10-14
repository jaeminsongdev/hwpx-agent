"""Run004 connection contracts only; no product, Native or queue writer."""
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case160_run004_controller as c


def pin(path):
    return dict(path=path, bytes=1, sha256="a"*64)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c.old.base.configure(160)

    def setUp(self):
        self.saved = (c._env["_graph"], c._env["_checkpoint"], c._env["_execution_requested"])

    def tearDown(self):
        c._env["_graph"], c._env["_checkpoint"], c._env["_execution_requested"] = self.saved

    def data(self):
        successor = c.predecessor._env["current_binding"].successor
        return dict(schema_version=c.SCHEMA, index=160, before=153, run=1, physical_product_run=4,
            base_step_pin=c.old.base.CONFIG.pin, authority_pin=successor.AUTHORITY,
            prior_runtime_pin=successor.ROOT, manifest_pin=c.MANIFEST, capsule_pin=c.CAPSULE,
            qualification_pin=pin(c.QUAL), controller_code_pins=[pin(c.SELF), pin(c.TEST)],
            binding_code_pin=pin(c.BINDING_CODE))

    def test_exact_closed_current_data(self):
        self.assertIs(c.validate_data(self.data()).get("physical_product_run"), 4)

    def test_old_run_data_rejected(self):
        row = self.data(); row["physical_product_run"] = 3
        with self.assertRaises(ValueError): c.validate_data(row)

    def test_extra_permission_key_rejected(self):
        row = self.data(); row["GO_authorized"] = True
        with self.assertRaises(ValueError): c.validate_data(row)

    def test_wrong_authority_rejected(self):
        row = self.data(); row["authority_pin"] = pin("other")
        with self.assertRaises(ValueError): c.validate_data(row)

    def test_wrong_controller_pair_rejected(self):
        row = self.data(); row["controller_code_pins"] = [pin(c.SELF), pin("wrong")]
        with self.assertRaises(ValueError): c.validate_data(row)

    def test_wrong_qualification_rejected(self):
        row = self.data(); row["qualification_pin"] = pin(c.predecessor.QUAL)
        with self.assertRaises(ValueError): c.validate_data(row)

    def test_run003_identity_unchanged(self):
        self.assertEqual(c.predecessor.RETRY.task(160), "case160-current-r003-tests")
        self.assertEqual(c.RETRY.task(160), "case160-current-r004-tests")
        self.assertNotEqual(c.RETRY.root_path(c.old.base.CONFIG), c.predecessor.RETRY.root_path(c.old.base.CONFIG))

    def test_whole_worker_code_inverse(self):
        self.assertEqual(c.M.worker.__code__.replace(co_consts=c.worker_code.co_consts), c.worker_code)
        self.assertIn(c.attempt.TASK, c.M.worker.__code__.co_consts)

    def test_whole_preflight_code_inverse(self):
        self.assertEqual(c.M.preflight_projection.__code__.replace(co_consts=c.fn.__code__.co_consts), c.fn.__code__)
        self.assertIn(c.after, c.M.preflight_projection.__code__.co_consts)

    def test_original_whole_engine_connection_body(self):
        self.assertIs(c.API.run_owned.__code__, c.predecessor.API.run_owned.__code__)
        self.assertIs(c.API.run_owned.__globals__["binding_attempt"].__globals__, c._env)

    def test_one_controller_function_family(self):
        for name in ("worker", "template", "validator", "context", "validate_candidate", "graph_value"):
            self.assertIs(getattr(c.M, name).__globals__, c._env)

    def test_new_api_is_not_unqualified_predecessor_prepare(self):
        self.assertIs(c.API.prepare, c.prepare_candidate)
        self.assertIsNot(c.API.prepare, c.predecessor.API.prepare)

    def test_queue_write_remains_closed(self):
        with self.assertRaisesRegex(ValueError, "READ_ONLY_ORACLE_QUALIFICATION_REQUIRED"):
            c.API.accept(pin(c.attempt.ROOT))

    def test_wrong_current_root_denied_before_binding(self):
        with patch.object(c, "binding", side_effect=AssertionError("must not bind")):
            with self.assertRaises(ValueError): c.prepare_candidate(NS(), pin(c.attempt.STOPPED["path"]))

    def test_only_physical004_allowed(self):
        for run in (1, 2, 3, True, "4"):
            with self.assertRaises(ValueError): c.run_owned(run)

    def test_new_preflight_required_before_dispatch(self):
        def missing_new(path):
            return NS(exists=lambda:False, is_file=lambda:False)
        class Root:
            def __truediv__(self, path): return missing_new(path)
        with patch.object(c.old.c, "ROOT", Root()), patch.object(c.prior.CONNECTION, "connect_run", side_effect=AssertionError("dispatch forbidden")):
            with self.assertRaisesRegex(ValueError, "NEW_RUN004_PREFLIGHT_MISSING"): c.run_owned(4)

    def test_private_sources_not_imported_or_hidden(self):
        self.assertTrue(all(not p["actual_module_imported_or_sys_modules_hidden"] for p in c.SOURCE_PROOFS))
        self.assertFalse(any(name in sys.modules for name in ("successor_current_binding_v7", "successor_bounded_graph_bootstrap_v7")))

    def test_original_capsule_and_manifest_preserved(self):
        self.assertEqual(c.predecessor.MANIFEST, c.bootstrap.original.original.MANIFEST)
        self.assertNotEqual(c.MANIFEST, c.predecessor.MANIFEST)
        self.assertEqual(c.CAPSULE["bytes"], 12008)

    def test_actual_bounded34_graph_without_engine_or_native(self):
        checked = []
        graph, proof = c.bootstrap.load(c.old, lambda:checked.append(True))
        self.assertEqual(len(graph.binding.descriptors()), 34)
        self.assertEqual(graph.worker.TASK, c.attempt.TASK)
        self.assertEqual((proof["bounded_reader_reads"], proof["bounded_reader_bytes"]), (28, 133296))
        self.assertFalse(proof["current_controller_engine_worker_Native_or_GO_qualified"])
        self.assertTrue(checked)

    def test_no_predecessor_graph_state_reused(self):
        self.assertIsNot(c._env, c.predecessor._env)
        self.assertIsNot(c._api_env, c.predecessor._api_env)
        self.assertIsNot(c._env["PARENT_STATES"], c.predecessor._env["PARENT_STATES"])


if __name__ == "__main__": unittest.main()
