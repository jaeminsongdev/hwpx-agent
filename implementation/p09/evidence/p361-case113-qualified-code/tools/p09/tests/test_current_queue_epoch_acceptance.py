"""Synthetic oracle projection ONLY; not actual113 product/Native acceptance.

Construct a marked in-memory full-scope model from actual112 metadata plus new
controller pins. Never write it to evidence, assign it an actual root pin, run
product/Native, or move the queue. Actual failed113 receipts must be rejected.
"""
import copy
import json
from pathlib import Path, PurePosixPath
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_current_queue_epoch as a

CHECKPOINT=lambda:None


class QueueEpochContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=a.original.AcceptanceReader(a.original.c.ROOT,CHECKPOINT)
        cls.actual112=a.original.read_exact(cls.q,a.original.ROOT_PIN)
        cls.actual113=a.original.read_exact(cls.q,a.ROOT_PIN)
        cls.listing=a.original.read_exact(cls.q,a.original.scope.LIST_PIN)
        cls.body=a.original.read_exact(cls.q,a.original.BODY_PIN)
        cls.fresh=a.original.packed.unpack(a.original.read_exact(cls.q,a.original.FRESH_PIN),CHECKPOINT)
        cls.q.pin(a.ORACLE_PIN['path'])
        with (a.original.c.ROOT/a.ORACLE_PIN['path']).open('rb') as stream:
            cls.source=stream.read(a.ORACLE_PIN['bytes']+1)
        cls.fixture=cls.synthetic(cls.actual112)
        check,cls.proof=a.validator(cls.source,cls.fixture,cls.listing,cls.body)
        cls.check=staticmethod(check)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    @classmethod
    def synthetic(cls,base):
        row=copy.deepcopy(base);row['synthetic_fixture_not_runtime_evidence']=True
        added=[cls.q.pin(name) for name in a.CONTROLLERS]
        required=a.original.scope.extend(a.original.scope.pins(row['source_freeze']),a.original.scope.pins(added))
        row['source_freeze']=list(required.values())
        bootstrap=a.original.scope.extend(a.original.scope.pins(row['bootstrap_metadata']['input_pins']),a.original.scope.pins(added))
        row['bootstrap_metadata']['input_pins']=list(bootstrap.values())
        row['imported_worker_source_paths']=sorted(set(row['imported_worker_source_paths'])|set(a.CONTROLLERS))
        row.update(schema_version=a.runtime.SCHEMA,state=a.runtime.PASS,prior_queue_cases=106,next_case=113,
            prior_queue_fresh_pin=a.runtime.PRIOR_ACCEPT_PIN,selected_test_index=113,
            selected_test_names=[a.runtime.CASE],passed_test_names=[a.runtime.CASE],test_arguments=a.runtime.arguments())
        n=len(required);total=sum(p['bytes'] for p in required.values())
        dirs=len({p.as_posix() for name in required for p in PurePosixPath(name).parents});held=n+dirs
        binary=sum(p['bytes'] for name,p in required.items() if name.endswith('.exe'))
        frame=row['source_frame'];frame.update(input_count=n,input_bytes=total)
        frame['held_identity_after_owned_cleanup'].update(regular_file_count=n,directory_count=dirs)
        for boundary in frame['actual_byte_boundaries']:
            boundary['actual_byte_pins']=list(required.values())
            boundary['reader_diagnostics'].update(read_passes=n,bytes_read=total,
                bytes_read_by_kind=dict(binary=binary,other=total-binary))
        h=frame['handles'];h.update(input_lock_handles_opened=held,input_lock_handles_closed=held,
            handle_metadata_checks=2*held+2*n,byte_stream_identity_checks=2*n)
        h['borrowed_byte_streams'].update(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,shared_offset_resets=2*n)
        h['native_open_pacing']['open_reservations']=held+2*n
        h['acquisition_phase_pressure']['acquisition_reservations']=held
        h['acquisition_source_warning_fail_fast']['checks']=held
        for guard in row['source_path_guard_diagnostics']:
            guard.update(native_metadata_queries_attempted=n,fresh_held_metadata_queries=n,original_path_guard_predicates=3*n)
        row['complete_runtime_budget']=a.runtime.runtime_budget(required,167)
        return row
    def bad(self,mutation):
        row=copy.deepcopy(self.fixture);mutation(row)
        with self.assertRaises(ValueError):
            self.check(row,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_synthetic_complete_model_and_exact_oracle_AST_projection(self):
        result=self.check(self.fixture,self.listing,self.body,self.fresh,CHECKPOINT)
        self.assertTrue(self.fixture['synthetic_fixture_not_runtime_evidence'])
        self.assertEqual(result['whole_runtime_input_count'],1714)
        self.assertTrue(self.proof['original_oracle_AST_restored_exactly'])
        self.assertEqual(self.proof['metadata_fields_projected'],9)
        self.assertFalse(self.proof['qualification_checks_skipped'])
    def test_actual113_missing_pin_never_prepare_or_advance(self):
        with patch.object(a,'ROOT_PIN',None):
            with self.assertRaisesRegex(ValueError,'ACTUAL_COMPLETED_CANDIDATE_PIN_REQUIRED'):a.prepare(self.q)
    def test_immutable_actual113_complete_receipt_oracle_without_queue_or_product_replay(self):
        check,proof=a.validator(self.source,self.actual113,self.listing,self.body)
        result=check(self.actual113,self.listing,self.body,self.fresh,CHECKPOINT)
        a.additional_observer_evidence(self.actual113)
        self.assertEqual(result['whole_runtime_input_count'],1731)
        self.assertEqual(proof['additional_PDH_cost_equality_extended_by_seconds'],2.05)
        self.assertTrue(proof['original_oracle_AST_restored_exactly'])
    def test_additional_cost_observer_and_cleanup_cannot_be_omitted(self):
        for field,value in (('existing_observer_instances',2),('second_sampler_thread_or_process',True),
                ('original_CPU_RAM_decisions_replaced',True),('additional_PDH_queries_explicit',False)):
            row=copy.deepcopy(self.actual113);row['serial_CPU_attribution'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):a.additional_observer_evidence(row)
        for field,value in (('query_remaining',True),('cleanup_confirmed',False)):
            row=copy.deepcopy(self.actual113);row['serial_CPU_attribution']['probes'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):a.additional_observer_evidence(row)
        row=copy.deepcopy(self.actual113);row['complete_runtime_budget']['additional_serial_PDH_maximum_sample_budget_seconds']=0
        with self.assertRaises(ValueError):a.additional_observer_evidence(row)
        row=copy.deepcopy(self.actual113);row['source_frame']['handles']['all_acquisition_checkpoint_warning_fail_fast']['latched']=True
        with self.assertRaises(ValueError):a.additional_observer_evidence(row)
    def test_both_actual113_failed_receipts_rejected_not_promoted(self):
        for pin in (a.runtime.FAILED001_PIN,dict(path='implementation/p09/evidence/p09-361-case113-current-runtime-run002.v1.json',
            bytes=71337,sha256='12326aa8aa378f2adef14c91ddb94ca735af93a3c56b009108af29e2f1140bef')):
            row=a.original.read_exact(self.q,pin)
            with self.subTest(),self.assertRaises(ValueError):self.check(row,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_modified_original_oracle_cannot_project(self):
        for source in (self.source[:-1],self.source.replace(b'32768',b'32769')):
            with self.subTest(),self.assertRaises(ValueError):a.validator(source,self.fixture,self.listing,self.body)
    def test_old112_name_cursor_or_false_bool_types_rejected(self):
        self.bad(lambda r:r.update(selected_test_names=[a.original.scope.CASE112]))
        self.bad(lambda r:r.update(prior_queue_cases=105))
        self.bad(lambda r:r.update(exit_code=False))
        self.bad(lambda r:r.update(selected_test_index=113.0))
    def test_new_controller_scope_missing_or_not_bootstrapped_rejected(self):
        self.bad(lambda r:r['source_freeze'].pop())
        self.bad(lambda r:r['bootstrap_metadata']['input_pins'].pop())
    def test_complete_before_after_not_partial_cache_or_swapped(self):
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'].reverse())
        self.bad(lambda r:r['source_frame'].update(serialized_pin_reused_as_live_handle=True))
    def test_held_identity_duplicate_offsets_cleanup_not_relaxed(self):
        self.bad(lambda r:r['source_frame']['handles'].update(input_lock_handles_remaining=1))
        self.bad(lambda r:r['source_frame']['handles']['borrowed_byte_streams'].update(shared_offset_resets=0))
        self.bad(lambda r:r['source_frame']['held_identity_after_owned_cleanup'].update(held_identity_checks_complete=False))
    def test_pressure_deadline_original_guards_and_costs_retained(self):
        self.bad(lambda r:r['source_frame']['handles'].update(maximum_lock_seconds=720))
        self.bad(lambda r:r['complete_runtime_budget'].update(product_allowance_seconds=0))
        self.bad(lambda r:r['samples'][0].update(commit_used_percent=95))
    def test_output_capture_and_Job_cleanup_not_optional(self):
        self.bad(lambda r:r['capture_diagnostics']['received_bytes'].update(stdout=229))
        self.bad(lambda r:r['job_final'].update(active_processes=1))
        self.bad(lambda r:r['owned_limits_readback'].update(verified=False))
    def test_full249_signed16_Gate_cannot_be_promoted(self):
        for key,value in (('full249_current_qualified',True),('signed16_current_qualified',True),('P09_gate','PASS')):
            with self.subTest():self.bad(lambda r:r.update({key:value}))


if __name__=='__main__':
    guard=a.original.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(QueueEpochContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,synthetic_only=True,actual113_acceptance=False,product_child_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
