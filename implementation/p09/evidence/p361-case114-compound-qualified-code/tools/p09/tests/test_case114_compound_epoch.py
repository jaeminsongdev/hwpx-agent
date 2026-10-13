"""Actual immutable recovery qualification contracts; no synthetic receipt PASS."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case114_compound_epoch as m

CHECKPOINT=lambda:None


class CompoundContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=m.a.AcceptanceReader(m.a.c.ROOT,CHECKPOINT)
        cls.source,cls.body,cls.listing,cls.expected,cls.proof=m.prepare(cls.q)
        cls.raw=m.s.candidate.read_source(cls.q,m.s.candidate.original.ORACLE_PIN)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def bad(self,mutate):
        CHECKPOINT();row=copy.deepcopy(self.source);mutate(row)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.validate_source(row,self.body,self.raw,CHECKPOINT)
        CHECKPOINT()
    def test_actual_two_distinct_epochs_checked_without_promoting_failed_body(self):
        self.assertEqual(self.body['state'],'STOPPED_NOT_ACCEPTED')
        self.assertIsNone(self.body['source_frame']['held_identity_after_owned_cleanup'])
        self.assertEqual(self.source['source_frame']['frame_state'],'COMMITTED')
        self.assertEqual(self.proof['source']['whole_source_count'],1758)
        self.assertTrue(self.proof['source']['product_and_source_epochs_distinct'])
        self.assertFalse(self.source['actual_product_executed_inside_new_source_frame'])
    def test_no_missing_source_pin_or_drifted_actual_receipt(self):
        with patch.object(m,'SOURCE_PIN',None):
            with self.assertRaises(ValueError):m.prepare(self.q)
        with patch.object(m,'SOURCE_PIN',dict(m.SOURCE_PIN,sha256='0'*64)):
            with self.assertRaises(ValueError):m.prepare(self.q)
    def test_only_actual_independent_success_not_runtime_or_gate(self):
        for key,value in (('state','PASS'),('queue_advance',1),('product_body_replayed',True),
                ('Native_product_single_frame_qualified',True),('P09_gate','PASS'),
                ('original_failed_root_state_rewritten',True),('original_final_identities_retroactively_fabricated',True)):
            with self.subTest(key=key):self.bad(lambda row:row.update({key:value}))
    def test_inherited_and_new_scope_cannot_be_cut_or_silently_rebased(self):
        self.bad(lambda row:row['inherited_source_pins'].pop())
        self.bad(lambda row:row['complete_source_pins'].pop())
        self.bad(lambda row:row['bootstrap_input_pins'][0].update(sha256='0'*64))
        self.bad(lambda row:row['imported_source_paths'].append(m.SELF))
    def test_both_full_actual_byte_reads_order_and_original_pressure_preserved(self):
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'].pop())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'].reverse())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][0]['reader_diagnostics'].update(bytes_read=1))
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][1]['reader_diagnostics']['near_saturation_read_backpressure'].update(original_read_checks_skipped=True))
    def test_real_final_identities_all_metadata_and_every_cleanup_required(self):
        self.bad(lambda row:row['source_frame'].update(held_identity_after_owned_cleanup=None))
        self.bad(lambda row:row['source_frame'].update(original_owned_cleanup_confirmed_before_release=False))
        self.bad(lambda row:row['source_frame']['handles'].update(handle_metadata_checks=5625))
        self.bad(lambda row:row['source_frame']['handles'].update(input_lock_handles_remaining=1))
        self.bad(lambda row:row.update(cleanup_confirmed=False))
        self.bad(lambda row:row['serial_CPU_attribution']['probes'][0].update(query_remaining=True))
    def test_retained_streams_exact_physical_and_two_logical_passes(self):
        for key,value in (('duplicate_handles_closed',3516),('shared_offset_resets',1758),
                ('logical_read_lease_returns',1758),('physical_handle_peak',3868),
                ('parsed_JSON_hash_or_byte_cache',True),('reused_stream_pressure_checkpoints',0)):
            with self.subTest(key=key):
                self.bad(lambda row:row['source_frame']['handles']['borrowed_byte_streams'].update({key:value}))
        self.bad(lambda row:row['source_frame']['handles']['native_open_pacing'].update(open_reservations=5625))
        self.bad(lambda row:row['source_frame']['handles']['all_acquisition_checkpoint_warning_fail_fast'].update(original_warning_percent=100))
    def test_original_resource_history_limits_no_zeroed_or_missing_sample(self):
        self.bad(lambda row:row.update(resource_samples=[]))
        self.bad(lambda row:row['resource_samples'][0].update(system_cpu_percent=None))
        self.bad(lambda row:row['resource_samples'][0].update(commit_used_percent=95))
        self.bad(lambda row:row['source_frame']['handles'].update(maximum_lock_seconds=720))
        self.bad(lambda row:row.update(elapsed_seconds=600.))
    def test_exact_serial_cost_metadata_and_inventory_no_hidden_credit(self):
        self.bad(lambda row:row['complete_recovery_budget'].update(predicted_global_recovery_seconds=0))
        self.bad(lambda row:row['complete_recovery_budget'].update(measured_pre_Native_bootstrap_elapsed_seconds=float('nan')))
        self.bad(lambda row:row['complete_recovery_budget'].update(unallocated_margin_seconds=0))
        self.bad(lambda row:row['complete_recovery_budget'].update(post_Native_fresh_metadata_nominal_seconds=0))
        self.bad(lambda row:row.update(metadata_final_fresh_hashes=101))
        self.bad(lambda row:row['current_Rust_inventory_observations'][0].update(requests=1))
    def test_exact_types_original_oracle_and_actual_roots_not_rewritten(self):
        self.bad(lambda row:row.update(queue_advance=False))
        with self.assertRaises(ValueError):m.source_validator(self.raw+b' ',self.expected)
        before=copy.deepcopy(self.source);body_before=copy.deepcopy(self.body)
        m.validate_source(self.source,self.body,self.raw,CHECKPOINT)
        self.assertEqual(before,self.source);self.assertEqual(body_before,self.body)
        self.assertEqual(m.a.read_exact(self.q,m.SOURCE_PIN),self.source)
        self.assertEqual(m.a.read_exact(self.q,m.s.BODY_PIN),self.body)


if __name__=='__main__':
    guard=m.a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompoundContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_or_Native_replayed=False,actual_queue_delta=0)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
