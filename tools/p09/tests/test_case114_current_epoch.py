"""Guarded retained-mode oracle contracts; marked in-memory models are not evidence."""
import copy
import json
from pathlib import Path, PurePosixPath
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import accept_case114_current_epoch as a

CHECKPOINT=lambda:None


class Accept114Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old=a.original.original
        cls.q=old.AcceptanceReader(old.c.ROOT,CHECKPOINT)
        cls.source=a.read_source(cls.q,a.original.ORACLE_PIN)
        cls.acceptor=a.read_source(cls.q,a.ACCEPTOR_PIN)
        project,cls.proof=a.projection(cls.acceptor,'validator');cls.project=staticmethod(project)
        cls.listing=old.read_exact(cls.q,old.scope.LIST_PIN)
        cls.body=old.read_exact(cls.q,old.BODY_PIN)
        cls.fresh=old.packed.unpack(old.read_exact(cls.q,old.FRESH_PIN),CHECKPOINT)
        cls.actual113=old.read_exact(cls.q,a.original.ROOT_PIN)
        cls.actual114_failed=old.read_exact(cls.q,dict(
            path='implementation/p09/evidence/p09-361-case114-current-runtime-run001.v1.json',
            bytes=2061087,sha256='59d337ea82f6357bbe006f7508c61298ca983d7fb409cc896748c5990ea6e71f'))
        cls.fixture=cls.synthetic(cls.actual113)
        check,cls.validator_proof=cls.project(cls.source,cls.fixture,cls.listing,cls.body)
        cls.check=staticmethod(check)
        cls.actual114=old.read_exact(cls.q,a.ROOT_PIN) if a.ROOT_PIN else None
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    @classmethod
    def synthetic(cls,base):
        old=a.original.original;row=copy.deepcopy(base)
        row['synthetic_fixture_not_runtime_evidence']=True
        added=[cls.q.pin(name) for name in (a.runtime.SELF,a.runtime.TEST,a.runtime.native.SELF,a.runtime.native.TEST)]
        required=old.scope.extend(old.scope.pins(row['source_freeze']),old.scope.pins(added))
        row['source_freeze']=list(required.values())
        row['bootstrap_metadata']['input_pins']=list(old.scope.extend(old.scope.pins(row['bootstrap_metadata']['input_pins']),old.scope.pins(added)).values())
        row['imported_worker_source_paths']=sorted(set(row['imported_worker_source_paths'])|{p['path'] for p in added})
        row.update(prior_queue_cases=107,next_case=114,prior_queue_fresh_pin=a.runtime.PRIOR_ACCEPT_PIN,
            selected_test_index=114,selected_test_names=[a.runtime.CASE],passed_test_names=[a.runtime.CASE],test_arguments=a.runtime.arguments())
        n=len(required);total=sum(p['bytes'] for p in required.values())
        dirs=len({p.as_posix() for name in required for p in PurePosixPath(name).parents});held=n+dirs
        binary=sum(p['bytes'] for name,p in required.items() if name.endswith('.exe'))
        frame=row['source_frame'];frame.update(input_count=n,input_bytes=total)
        frame['held_identity_after_owned_cleanup'].update(regular_file_count=n,directory_count=dirs)
        for boundary in frame['actual_byte_boundaries']:
            boundary['actual_byte_pins']=list(required.values())
            boundary['reader_diagnostics'].update(read_passes=n,bytes_read=total,bytes_read_by_kind=dict(binary=binary,other=total-binary))
        h=frame['handles'];h.update(input_lock_handles_opened=held,input_lock_handles_closed=held,
            handle_metadata_checks=2*held+2*n,byte_stream_identity_checks=2*n)
        h['borrowed_byte_streams'].update(duplicate_handles_opened=n,duplicate_handles_closed=n,
            shared_offset_resets=2*n,retained_within_one_live_frame_only=True,unbuffered_raw_streams=True,
            parsed_JSON_hash_or_byte_cache=False,physical_handle_ceiling=8192,physical_handle_peak=held+n,
            new_duplicate_open_reservations=n,reused_stream_pressure_checkpoints=n,
            logical_read_leases=2*n,logical_read_lease_returns=2*n,pending_open_reservation=False,
            resource_callback_retained_on_reuse=True,cursor_reset_and_fresh_identity_on_each_pass=True)
        h['native_open_pacing']['open_reservations']=held+n
        h['acquisition_phase_pressure']['acquisition_reservations']=held
        h['acquisition_source_warning_fail_fast']['checks']=held
        for guard in row['source_path_guard_diagnostics']:
            guard.update(native_metadata_queries_attempted=n,fresh_held_metadata_queries=n,original_path_guard_predicates=3*n)
        row['complete_runtime_budget']=a.runtime.runtime_budget(required,167)
        return row
    def bad(self,mutate):
        row=copy.deepcopy(self.fixture);mutate(row)
        with self.assertRaises(ValueError):
            self.check(row,self.listing,self.body,self.fresh,CHECKPOINT);a.retained_evidence(row)
    def test_full_scope_synthetic_projection_exact_original_checks_and_no_observation_rewrite(self):
        before=copy.deepcopy(self.fixture)
        result=self.check(self.fixture,self.listing,self.body,self.fresh,CHECKPOINT);a.retained_evidence(self.fixture)
        self.assertEqual(result['whole_runtime_input_count'],1735)
        self.assertEqual(self.fixture,before)
        self.assertTrue(self.proof['qualified113_acceptor_AST_restored_exactly'])
        self.assertTrue(self.validator_proof['original_oracle_AST_restored_exactly'])
        self.assertEqual(self.proof['expected_duplicate_counter_changes'],3)
    def test_actual_complete114_or_missing_pin_never_synthetic_acceptance(self):
        with patch.object(a,'ROOT_PIN',None):
            with self.assertRaisesRegex(ValueError,'COMPLETED_ACTUAL114_PIN_REQUIRED'):a.prepare(self.q)
        if self.actual114 is not None:
            check,_=self.project(self.source,self.actual114,self.listing,self.body)
            check(self.actual114,self.listing,self.body,self.fresh,CHECKPOINT);a.retained_evidence(self.actual114)
    def test_old_actual113_not_114_even_with_valid_native_cleanup(self):
        with self.assertRaises(ValueError):self.check(self.actual113,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_real114_passed_body_but_missing_final_identity_not_candidate_PASS(self):
        self.assertTrue(self.actual114_failed['product_body_observed'])
        self.assertEqual(self.actual114_failed['source_frame']['frame_state'],'CLOSED')
        check,_=self.project(self.source,self.actual114_failed,self.listing,self.body)
        with self.assertRaises(ValueError):check(self.actual114_failed,self.listing,self.body,self.fresh,CHECKPOINT)
    def test_modified_qualified_acceptor_or_oracle_cannot_compile(self):
        for raw in (self.acceptor[:-1],self.acceptor.replace(b'NO_HIDDEN_COST',b'NO_HIDDEN_COSX')):
            with self.subTest(),self.assertRaises(ValueError):a.projection(raw,'validator')
        with self.assertRaises(ValueError):self.project(self.source[:-1],self.fixture,self.listing,self.body)
    def test_retained_handle_not_a_cached_hash_partial_or_fake_closed_duplicate(self):
        for field,value in (('duplicate_handles_closed',0),('duplicate_handles_remaining',1),
                ('duplicate_close_failed_attempts',1),('parsed_JSON_hash_or_byte_cache',True),
                ('shared_offset_resets',0),('logical_read_lease_returns',0),('pending_open_reservation',True),
                ('unbuffered_raw_streams',False),('retained_within_one_live_frame_only',False)):
            with self.subTest(field=field):self.bad(lambda r:r['source_frame']['handles']['borrowed_byte_streams'].update({field:value}))
    def test_original_second_fresh_identity_before_after_bytes_and_owned_cleanup_not_removed(self):
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda r:r['source_frame']['actual_byte_boundaries'].reverse())
        self.bad(lambda r:r['source_frame']['handles'].update(byte_stream_identity_checks=0))
        self.bad(lambda r:r['source_frame'].update(original_owned_cleanup_confirmed_before_release=False))
        self.bad(lambda r:r['job_final'].update(active_processes=1))
    def test_physical_ceiling_reuse_pressure_and_model_cannot_be_faked(self):
        self.bad(lambda r:r['source_frame']['handles']['borrowed_byte_streams'].update(physical_handle_peak=9000))
        self.bad(lambda r:r['source_frame']['handles']['borrowed_byte_streams'].update(reused_stream_pressure_checkpoints=0))
        self.bad(lambda r:r['complete_runtime_budget'].update(removed_second_duplicate_handle_reservations=0))
        self.bad(lambda r:r['complete_runtime_budget'].update(unchanged_lock_deadline_seconds=720))
        self.bad(lambda r:r['samples'][0].update(commit_used_percent=95))
    def test_whole_scope_new_controllers_capture_and_Gate_not_weakened(self):
        self.bad(lambda r:r['bootstrap_metadata']['input_pins'].pop())
        self.bad(lambda r:r['source_freeze'].pop())
        self.bad(lambda r:r['capture_diagnostics']['received_bytes'].update(stdout=1))
        self.bad(lambda r:r.update(full249_current_qualified=True))
        self.bad(lambda r:r.update(P09_gate='PASS'))
    def test_closed_queue_projection_exactly107_to108_once_not_double_count(self):
        execute,proof=a.projection(self.acceptor,'run')
        self.assertTrue(proof['qualified113_acceptor_AST_restored_exactly'])
        self.assertEqual(len(proof['changed_metadata_or_new_explicit_mechanics']),10)
        self.assertEqual(execute.__globals__['OUTPUT'],a.OUTPUT)
        self.assertEqual(execute.__globals__['ROOT_PIN'],a.ROOT_PIN)


if __name__=='__main__':
    guard=a.original.original.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Accept114Contracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,synthetic_models_not_evidence=True,actual_queue_advance=False,
        product_or_Native_frame_replayed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
