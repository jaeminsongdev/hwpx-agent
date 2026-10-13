"""Guarded actual-doc injection; simulated future authority NEVER evidence."""
import copy
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch

import flat_preserved129_compound_connection_v1 as m

DOCUMENTS = None
CODE_PINS = None
RAW_PREPARE = None
RAW_PREFLIGHT = None
RAW_LEAF = None
CHECKPOINT = None


def future_fixture():
    """Counter123 is a unit fixture only; no authority file is produced."""
    old = DOCUMENTS["authority"]
    row = dict(schema_version=m.SCHEMA, state=m.PASS, acceptance_kind=m.KIND,
        accepted_count_before=122, accepted_count_after=123, accepted_count_delta=1,
        accepted_test_indices=[129], accepted_test_names=[m.contract.source.CASE],
        accepted_current_generation_case_count=18, next_runtime_index=130,
        runtime_remaining_individual_cases=126, resource_cleanup_confirmed=True,
        product_and_source_epochs_distinct=True, Native_product_single_frame_qualified=False,
        original_failed_root_state_rewritten=False, successful_product_cases_reexecuted=False,
        product_child_executed=False, Native_frame_reexecuted=False,
        prior105_historical_epochs_preserved=True, prior105_current_generation_rebased=False,
        duplicate_acceptance_refuses_overwrite=True, full249_current_qualified=False,
        signed16_current_qualified=False, whole_runtime_reconciliation_required=True,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", P10_started=False,
        sole_serial_sampler=True, parallel_observer_started=False,
        preserved_failed_product_root_pin=m.contract.source.STOP_PIN,
        independent_full_source_pin=m.contract.SOURCE_PIN,
        prior_queue_authority_pin=m.contract.source.AUTHORITY_PIN,
        accepted_epoch_key=m.contract.source.STOP_PIN["sha256"]+":129:source:"+m.contract.SOURCE_PIN["sha256"],
        fresh_input_pins=old["fresh_input_pins"], fresh_read_passes=old["fresh_read_passes"],
        fresh_bytes_read=old["fresh_bytes_read"], final_fresh_hashes=old["final_fresh_hashes"],
        file_open_ceiling_per_second=20, qualifier_read_rates_by_kind=dict(binary=1048576, other=2097152),
        resource_samples=old["resource_samples"], actual_compound_evidence_validation=DOCUMENTS["candidate"],
        connection_qualification_pin=dict(path=m.QUAL_PATH,bytes=1,sha256="0"*64))
    queue = dict(path=m.OUTPUT, bytes=1, sha256="1"*64)
    step = NS(index=130, before=123, case=DOCUMENTS["listing"]["source_test_names"][129],
        prior_queue_pin=queue, prior_candidate_pin=m.contract.source.STOP_PIN,
        path=m.base.config_path(130), pin=dict(path=m.base.config_path(130),bytes=1,sha256="2"*64))
    return row, step


class FixtureReader:
    """IN-MEMORY unit fixture; not a current-byte/Native/queue observation."""
    def __init__(self, row, step):
        self.row = row; self.step = step; self.snapshots = {}
        self.pins = dict(DOCUMENTS["required"])
        self.pins.update(m.base.scope.pins(CODE_PINS, 2))
        self.pins[step.path] = step.pin
        self.pins[m.OUTPUT] = step.prior_queue_pin
        self.pins[m.QUAL_PATH] = row["connection_qualification_pin"]
        data = dict(schema_version="hwpx-agent.p09-compound-predecessor/v1", index=130, before=123,
            acceptance_kind=m.KIND, base_step_pin=step.pin, prior_authority_pin=step.prior_queue_pin,
            preserved_body_pin=m.contract.source.STOP_PIN, full_source_pin=m.contract.SOURCE_PIN,
            connection_qualification_pin=row["connection_qualification_pin"])
        self.data = json.dumps(data)
        self.pins[m.predecessor_data_path(130)] = dict(path=m.predecessor_data_path(130),bytes=len(self.data),sha256="3"*64)
        self.checkpoint = CHECKPOINT

    def pin(self, name):
        pin = self.pins[name]; self.snapshots[name] = pin; return pin

    def text(self, name):
        self.pin(name)
        if name == m.predecessor_data_path(130):
            return self.data
        raise AssertionError("UNEXPECTED_FIXTURE_TEXT")

    def json(self, name):
        self.pin(name)
        if name == m.OUTPUT:
            return self.row
        if name == m.QUAL_PATH:
            return dict(state="PASS_COMPOUND129_AUTHORITY_AND_NEXT130_CODE_NOT_ACTUAL_ACCEPTANCE",
                accepted_count_after=122, accepted_count_delta=0, cleanup_confirmed=True,
                product_body_replayed=False, Native_source_replayed=False,
                next130_production_entry_dependencies_qualified=True,
                contracts=dict(run=30,errors=0,failures=0,skipped=0),new_code_pins=CODE_PINS)
        raise AssertionError("UNEXPECTED_FIXTURE_JSON")


class CompoundConnectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(DOCUMENTS, "actual guarded receipt injection required")
        self.assertTrue(callable(CHECKPOINT))
        CHECKPOINT()
        self.parent, self.step = future_fixture()

    def rejects(self, **kw):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            m.parent_header(dict(self.parent, **kw), self.step)

    def test_explicit_compound_parent_fixture(self):
        self.assertGreater(len(m.parent_header(self.parent, self.step)), 0)

    def test_normal_PASS_not_compound(self):
        self.rejects(state=m.source.prior.accepted.original.PASS)

    def test_ordinary_candidate_alias_rejected(self):
        self.rejects(runtime_candidate_pin=m.contract.source.STOP_PIN)

    def test_counter_skip_rejected(self):
        self.rejects(accepted_count_after=124)

    def test_duplicate_delta_rejected(self):
        self.rejects(accepted_count_delta=2)

    def test_bool_delta_rejected(self):
        self.rejects(accepted_count_delta=True)

    def test_wrong_next_cursor_rejected(self):
        self.rejects(next_runtime_index=131)

    def test_historical_rebase_rejected(self):
        self.rejects(prior105_current_generation_rebased=True)

    def test_failed_product_promoted_rejected(self):
        self.rejects(original_failed_root_state_rewritten=True)

    def test_same_frame_claim_rejected(self):
        self.rejects(Native_product_single_frame_qualified=True)

    def test_product_replay_rejected(self):
        self.rejects(successful_product_cases_reexecuted=True)

    def test_wrong_source_pin_rejected(self):
        self.rejects(independent_full_source_pin=m.contract.PREVIOUS_PIN)

    def test_incomplete_fresh_reads_rejected(self):
        self.rejects(fresh_read_passes=1)

    def test_missing_final_hash_rejected(self):
        self.rejects(final_fresh_hashes=0)

    def test_guard_relaxation_rejected(self):
        self.rejects(file_open_ceiling_per_second=40)

    def test_synthetic_authority_rejected(self):
        self.rejects(synthetic_fixture_only_not_evidence=True)

    def test_other_step_not_routed_to_compound(self):
        with self.assertRaises(ValueError):
            m.parent_header(self.parent, NS(**{**vars(self.step), "index":131,"before":124}))

    def test_actual_body_remains_STOP(self):
        self.assertEqual(DOCUMENTS["original"]["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(DOCUMENTS["candidate"]["accepted_count_delta"], 0)

    def test_next130_real_binding_branch_with_fixture_queue(self):
        q = FixtureReader(self.parent, self.step)
        actual = (DOCUMENTS["row"], DOCUMENTS["original"], DOCUMENTS["listing"],
            DOCUMENTS["required"], DOCUMENTS["candidate"])
        with patch.object(m.base,"CONFIG",self.step), patch.object(m,"documents",return_value=actual):
            required, rust = m.binding(q)
        self.assertEqual(len(rust),787)
        self.assertTrue(all(required[n] == p for n,p in DOCUMENTS["required"].items()))
        self.assertEqual(required[m.OUTPUT],self.step.prior_queue_pin)

    def test_unmatched_compound_validation_rejected(self):
        q = FixtureReader(dict(self.parent,actual_compound_evidence_validation={}),self.step)
        actual = (DOCUMENTS["row"], DOCUMENTS["original"], DOCUMENTS["listing"],
            DOCUMENTS["required"], DOCUMENTS["candidate"])
        with patch.object(m.base,"CONFIG",self.step), patch.object(m,"documents",return_value=actual):
            with self.assertRaises(ValueError):m.binding(q)

    def test_runtime_actual_template_namespace_connection(self):
        old = (m.source.template,m.source.SELF,m.source.TEST)
        with patch.object(m.base,"CONFIG",self.step):
            engine, proof = m.template()
        self.assertEqual(engine.run_owned.__globals__["SELF"],m.SELF)
        self.assertEqual(engine.worker.__globals__["SELF"],m.SELF)
        self.assertTrue(proof["source_engine_bytecode_unchanged"])
        self.assertEqual((m.source.template,m.source.SELF,m.source.TEST),old)

    def test_parent_runner_exact_original_code_and_dependencies(self):
        captured=[]
        def factory(code,env,argdefs=None):
            captured.append((code,env));return lambda run: run
        with patch.object(m.base,"CONFIG",self.step),patch.object(m,"FunctionType",side_effect=factory):
            self.assertEqual(m.run_owned(1),1)
        code,env=captured[0]
        self.assertIs(code,m.source.run_owned.__code__)
        self.assertIs(env["binding_attempt"],m.binding_attempt)
        self.assertIs(env["template"],m.template)

    def test_prepare_expects_explicit_compound_without_receipt_rewrite(self):
        with patch.object(m.base,"CONFIG",self.step):
            original=m.source.prepare_projection(RAW_PREPARE)
            projected=m.prepare_projection(RAW_PREPARE)
        self.assertEqual(projected.__code__,original.__code__)
        self.assertEqual(projected.__globals__["PASS"],m.PASS)
        self.assertEqual(original.__globals__["PASS"],m.source.prior.accepted.original.PASS)
        self.assertIs(projected.__globals__["validate_candidate"],m.validate_candidate)

    def test_preflight_original_code_and_real_binding_dependency(self):
        with patch.object(m.base,"CONFIG",self.step):
            old=m.source.preflight_projection(RAW_PREFLIGHT,RAW_LEAF)
            new=m.preflight_projection(RAW_PREFLIGHT,RAW_LEAF)
        self.assertEqual(new.__code__,old.__code__)
        self.assertIs(new.__globals__["binding_attempt"],m.binding_attempt)
        self.assertIs(new.__globals__["template"],m.template)

    def test_original_runtime_limits_not_changed(self):
        self.assertEqual(m.source.attempt(130),1)
        self.assertEqual(m.base.context(self.step).arguments(),
            [self.step.case,"--exact","--test-threads=1","--format=pretty","--color=never"])
        self.assertEqual(m.contract.source.source_budget(DOCUMENTS["required"]),DOCUMENTS["row"]["source_budget"])

    def test_prepare_binding_before_current_root_read(self):
        calls=[]
        def sourceprepare(q,pin):raise ValueError("ROOT_READ_MARKER")
        def factory(code,env,argdefs=None):
            self.assertIs(code,sourceprepare.__code__)
            return lambda q,pin: sourceprepare(q,pin)
        with patch.object(m.source,"reviewed_inputs",side_effect=lambda q,r:calls.append("review")), \
            patch.object(m,"binding",side_effect=lambda q:(calls.append("binding") or ({},set()))), \
            patch.object(m.source,"prepare",sourceprepare),patch.object(m,"FunctionType",side_effect=factory):
            with self.assertRaisesRegex(ValueError,"ROOT_READ_MARKER"):m.prepare(None,{})
        self.assertEqual(calls,["review","binding"])

    def test_accept130_original_code_and_stronger_prepare(self):
        captured=[]
        def factory(code,env,argdefs=None):
            captured.append((code,env));return lambda pin: pin
        with patch.object(m.base,"CONFIG",self.step),patch.object(m,"FunctionType",side_effect=factory):
            self.assertEqual(m.accept130({"fixture":"not evidence"}),{"fixture":"not evidence"})
        self.assertIs(captured[0][0],m.source.accept.__code__)
        self.assertIs(captured[0][1]["prepare"],m.prepare)

    def test_no_automatic_product_retry(self):
        with patch.object(m.base,"CONFIG",self.step):
            with self.assertRaises(ValueError):m.binding_attempt(None,2)

    def test_queue_scan_single_fresh_stat_per_exact_path(self):
        calls=[];pacer=NS(reserve=lambda:calls.append("paced"))
        with patch.object(Path,"lstat",side_effect=FileNotFoundError):
            result=m.scan_future(NS(open_pacer=pacer),129)
        self.assertEqual(len(calls),242)
        self.assertEqual(result["exact_path_observations"],242)

    def test_duplicate_authority_scan_rejected(self):
        with patch.object(Path,"lstat",return_value=object()):
            with self.assertRaises(ValueError):m.scan_future(NS(open_pacer=NS(reserve=lambda:None)),129)


if __name__ == "__main__":
    unittest.main()
