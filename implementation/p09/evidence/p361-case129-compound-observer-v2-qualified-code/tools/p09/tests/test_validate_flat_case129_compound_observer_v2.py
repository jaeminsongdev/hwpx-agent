"""Actual source002 injected by guarded qualifier; no replay or synthetic PASS."""
import copy
import unittest
from unittest.mock import patch

import validate_flat_case129_compound_observer_v2 as m

DOCUMENTS = None
CHECKPOINT = None


class ObserverCompoundTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(DOCUMENTS, "guarded actual receipt injection required")
        self.assertTrue(callable(CHECKPOINT))

    def args(self, row=None, **kw):
        docs = dict(DOCUMENTS, **kw)
        return (docs["row"] if row is None else row, docs["pin"], docs["previous"],
            docs["connection"], docs["observed"], docs["real"], CHECKPOINT)

    def epoch_mutation(self, *path, value):
        row = dict(DOCUMENTS["row"])
        row["source_observer_epoch"] = copy.deepcopy(row["source_observer_epoch"])
        target = row["source_observer_epoch"]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return row

    def rejects(self, row=None, **kw):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            m.validate_epoch(*self.args(row, **kw))

    def test_actual_source002_epoch(self):
        result = m.validate_epoch(*self.args())
        self.assertEqual(result["sole_observer_samples"], 964)
        self.assertTrue(result["all_previous1904_inputs_retained"])

    def test_actual_full_original_compound_oracle_once(self):
        d = DOCUMENTS
        result = m.validate(d["original"], m.source.STOP_PIN, d["row"], d["pin"],
            d["authority"], m.source.AUTHORITY_PIN, d["listing"], d["sourcequal"],
            m.prior.QUAL_PIN, d["previous"], d["connection"], d["observed"], d["real"], CHECKPOINT)
        self.assertEqual(result["state"], m.PASS)
        self.assertEqual(result["accepted_count_after"], 122)
        self.assertEqual(result["accepted_count_delta"], 0)
        self.assertFalse(result["independent_compound_acceptance_qualified"])
        self.assertFalse(result["authoritative_counter_or_queue_write_performed"])

    def test_failed_header_before_full_oracle(self):
        with patch.object(m.prior, "validate", side_effect=AssertionError("must not traverse")):
            self.rejects(dict(DOCUMENTS["row"], state="FAILED_NOT_QUALIFIED"))

    def test_synthetic_source_rejected(self):
        self.rejects(dict(DOCUMENTS["row"], synthetic_fixture_only_not_evidence=True))

    def test_wrong_source_receipt_pin(self):
        self.rejects(pin=dict(DOCUMENTS["pin"], sha256="0" * 64))

    def test_wrong_connection_receipt(self):
        self.rejects(self.epoch_mutation("qualification_pin", value=m.OBSERVER_PIN))

    def test_PDH_cleanup_failure(self):
        self.rejects(self.epoch_mutation("PDH_cleanup_confirmed", value=False))

    def test_default_module_mutation(self):
        self.rejects(self.epoch_mutation("default_module_classes_mutated", value=True))

    def test_old_failed_root_promotion(self):
        self.rejects(self.epoch_mutation("old_failed_root_promoted", value=True))

    def test_product_body_replay(self):
        self.rejects(self.epoch_mutation("product_body_replayed", value=True))

    def test_changed_PDH_allowance(self):
        self.rejects(self.epoch_mutation("original_PDH_allowance_seconds", value=0.0))

    def test_connection_contract_skip(self):
        bad = dict(DOCUMENTS["connection"], contracts=dict(run=10, errors=0, failures=0, skipped=1))
        self.rejects(connection=bad)

    def test_observer_contract_failure(self):
        bad = dict(DOCUMENTS["observed"], contracts=dict(run=15, errors=0, failures=1, skipped=0))
        self.rejects(observed=bad)

    def test_previous_failed_source_promoted(self):
        self.rejects(previous=dict(DOCUMENTS["previous"], state=m.source.PASS))

    def test_previous_live_handle(self):
        bad = dict(DOCUMENTS["previous"])
        bad["source_frame"] = copy.deepcopy(bad["source_frame"])
        bad["source_frame"]["handles"]["active_byte_streams"] = 1
        self.rejects(previous=bad)

    def test_previous_scope_input_removed(self):
        bad = dict(DOCUMENTS["row"], required_source_pins=DOCUMENTS["row"]["required_source_pins"][1:])
        self.rejects(bad)

    def test_previous_input_hash_changed(self):
        pins = list(DOCUMENTS["row"]["required_source_pins"])
        pins[0] = dict(pins[0], sha256="0" * 64)
        self.rejects(dict(DOCUMENTS["row"], required_source_pins=pins))

    def test_missing_qualified_dependency(self):
        bad = dict(DOCUMENTS["observed"], unchanged_dependency_pins=[
            dict(path="tools/p09/unqualified.py", bytes=1, sha256="0" * 64)])
        self.rejects(observed=bad)

    def test_extra_sampler(self):
        self.rejects(self.epoch_mutation("observer", "second_sampler_thread_or_process", value=True))

    def test_extra_probe(self):
        row = self.epoch_mutation("observer", "probes", value=[
            DOCUMENTS["row"]["source_observer_epoch"]["observer"]["probes"][0]] * 2)
        self.rejects(row)

    def test_unclosed_probe_query(self):
        self.rejects(self.epoch_mutation("observer", "probes", 0, "query_remaining", value=True))

    def test_original_resource_guard_replaced(self):
        self.rejects(self.epoch_mutation("observer", "original_K32_CPU_RAM_decisions_replaced", value=True))

    def test_counter_bool_not_int(self):
        self.rejects(self.epoch_mutation("observer", "probes", 0, "warning_only_checks", value=True))

    def test_counter_missing_sample(self):
        self.rejects(self.epoch_mutation("observer", "probes", 0, "cold_skips", value=963))

    def test_actual_cold_query_added(self):
        self.rejects(self.epoch_mutation("observer", "probes", 0, "collect_calls", value=2))

    def test_cost_float_type_preserved(self):
        self.rejects(self.epoch_mutation("observer", "probes", 0, "total_added_sample_seconds", value=0))

    def test_warning_sample_relabel(self):
        samples = list(DOCUMENTS["row"]["resource_samples"])
        samples[0] = dict(samples[0], system_cpu_percent=75.0)
        self.rejects(dict(DOCUMENTS["row"], resource_samples=samples))

    def test_causal_fix_claim_rejected(self):
        self.rejects(self.epoch_mutation("causal_trigger_or_freeze_fix_established", value=True))

    def test_real_light_cleanup_failure(self):
        self.rejects(real=dict(DOCUMENTS["real"], preparation_cleanup_confirmed=False))

    def test_no_checkpoint_rejected(self):
        args = list(self.args()); args[-1] = None
        with self.assertRaises(ValueError):
            m.validate_epoch(*args)


if __name__ == "__main__":
    unittest.main()
