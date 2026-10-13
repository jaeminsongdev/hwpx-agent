"""Guarded flat queue/complete actual115 oracle contracts; no product replay."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_runtime as r
import flat_current_queue_acceptance as m

CHECKPOINT=lambda:None
ROOT_PIN=None


class FlatContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=m.a.AcceptanceReader(r.c.ROOT,CHECKPOINT)
        cls.required,cls.rust=r.binding(cls.q)
        cls.entry,cls.entry_proof=r.entry();cls.engine,cls.engine_proof=r.template()
        cls.terminal=cls.engine.terminal_api(cls.q)
        cls.previous=m.a.read_exact(cls.q,r.CONFIG.prior_candidate_pin)
        cls.listing=m.a.read_exact(cls.q,r.scope.LIST_PIN);cls.oldbody=m.a.read_exact(cls.q,m.a.BODY_PIN)
        cls.fresh=m.a.packed.unpack(m.a.read_exact(cls.q,m.a.FRESH_PIN),CHECKPOINT)
        ctx=r.context(r.CONFIG,index=115,before=108,name=r.stable.CASE,parent=cls.previous['prior_queue_fresh_pin'])
        project,_=m.validator(m.candidate.read_source(cls.q,m.candidate.ACCEPTOR_PIN),ctx,flat=False)
        cls.check=staticmethod(project(m.candidate.read_source(cls.q,m.candidate.original.ORACLE_PIN),cls.previous,cls.listing,cls.oldbody)[0])
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def bad(self,mutate):
        CHECKPOINT();row=copy.deepcopy(self.previous);mutate(row)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            self.check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
        CHECKPOINT()
    def test_actual109_whole1771_current787_complete_previous_not_reexecuted(self):
        self.assertGreaterEqual(len(self.required),1774);self.assertEqual(len(self.rust),787)
        self.assertEqual(self.previous['source_frame']['frame_state'],'COMMITTED')
        self.assertTrue(all(self.required[p['path']]==p for p in self.previous['source_freeze']))
        self.assertIn(r.CONFIG.path,self.q.snapshots)
        self.assertEqual(len([n for n in self.q.snapshots if '/p361-case115-qualified-code/' in n]),7)
    def test_wrapper_and_original_engines_exact_with_same_final_resource_guards(self):
        self.assertTrue(self.entry_proof['original115_wrapper_AST_restored_exactly'])
        self.assertEqual(self.entry_proof['receipt_metadata_literals_parameterized'],1)
        self.assertTrue(self.engine_proof['original_engine_AST_restored_exactly'])
        self.assertTrue(self.engine_proof['same_owner_handoff']['engine_AST_restored_exactly'])
        self.assertTrue(self.engine_proof['final_actual_sample']['all_preexisting_engine_AST_restored_exactly'])
    def test_step_data_shape_wrong_cursor_pin_path_and_duplicate_keys_refused(self):
        real=json.loads((r.c.ROOT/r.CONFIG.path).read_text(encoding='utf-8'))
        for key,value in (('before',110),('index',True),('case','bad name'),('extra','not allowed')):
            row=copy.deepcopy(real);row[key]=value
            with self.subTest(),self.assertRaises(ValueError):r.validate_config(row,116)
        row=copy.deepcopy(real);row['prior_queue_pin']['path']='../bad'
        with self.assertRaises(ValueError):r.validate_config(row,116)
        with self.assertRaises(ValueError):r.unique([('index',116),('index',117)])
    def test_next_data_metadata_does_not_import_next_per_case_controller(self):
        before=set(sys.modules)
        fake=NS(index=117,before=110,case='synthetic_metadata_only_not_evidence',prior_queue_pin=dict(r.CONFIG.prior_queue_pin))
        with patch.object(r,'CONFIG',fake):
            engine,proof=r.template()
            self.assertTrue(proof['original_engine_AST_restored_exactly'])
            self.assertEqual(engine.worker.__globals__['MARKER_ARGS'],['current-queue-case117-runtime-only'])
        self.assertEqual(before,set(sys.modules))
    def test_exact116_terminal_rejects_old112_113_114_115(self):
        name=r.CONFIG.case;output='running 1 test\ntest '+name+' ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'
        self.assertEqual(self.terminal.terminal(output,'',name)['passed'],1)
        for old in (r.stable.CASE,r.stable.accepted114.s.r.CASE,r.stable.stable.CASE,r.scope.CASE112):
            with self.subTest(),self.assertRaises(ValueError):self.terminal.terminal(output.replace(name,old),'',name)
    def test_no_repeat_or_arbitrary_case_task(self):
        self.assertEqual(r.run_for(r.task_for(1)),1)
        with self.assertRaises(ValueError):r.run_for('case115-current-r001-tests')
        with self.assertRaises(ValueError):r.run_for('case116-current-r000-tests')
        with self.assertRaisesRegex(ValueError,'NO_AUTOMATIC_RETRY'):r.binding_attempt(NS(),2)
    def worker_patches(self,go=True,job=True):
        def member(process,owned,pointer):pointer._obj.value=job;return True
        return (patch.object(r.c,'Windows',return_value=NS(k=NS(GetCurrentProcess=lambda:17,IsProcessInJob=member))),
            patch.object(r.c.sys,'stdin',io.StringIO('P149_GO\n' if go else 'BAD\n')),
            patch.object(r.c.shutil,'which',return_value='fake-cargo'),patch.object(r.stable.stable.prior.build,'direct_path'))
    def test_original_worker_116_GO_Job_assertions_and_thread1(self):
        p1,p2,p3,p4=self.worker_patches()
        with p1,p2,p3,p4,patch.object(r.subprocess,'call',return_value=0) as call:
            self.assertEqual(self.engine.worker(r.task_for(999)),0)
        self.assertEqual(call.call_args.args[0],[str(r.c.ROOT/r.scope.EXE_PIN['path']),*r.arguments()])
        for name,value in dict(RUST_TEST_THREADS='1',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items():
            self.assertEqual(call.call_args.kwargs['env'][name],value)
        for go,job in ((False,True),(True,False)):
            p1,p2,p3,p4=self.worker_patches(go,job)
            with p1,p2,p3,p4,patch.object(r.subprocess,'call') as bad:
                with self.assertRaises(ValueError):self.engine.worker(r.task_for(998))
            bad.assert_not_called()
    def test_failure_not_queue_advance_or_gate_and_correct116_metadata(self):
        stream=io.StringIO()
        def fake_run(task,destination,maximum):
            self.assertIn('case116-current-runtime-run997',str(destination));self.assertEqual(maximum,1200)
            json.dump(dict(state='DEFERRED_NOT_STARTED',writer_authorized=False,cleanup_confirmed=True,
                owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]),stop_reason='STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'),stream)
            return 2
        with patch.object(r.c,'run',side_effect=fake_run):self.assertEqual(self.engine.run_owned(997),2)
        row=json.loads(stream.getvalue());self.assertEqual(row['selected_test_index'],116)
        self.assertEqual(row['prior_queue_cases'],109);self.assertEqual(row['accepted_count_delta'],0)
        self.assertFalse(row['Native_source_frame_qualified'])
    def test_complete_previous_oracle_resources_Job_bytes_and_identity_not_weakened(self):
        self.bad(lambda row:row.update(writer_authorized=False))
        self.bad(lambda row:row['job_final'].update(active_processes=1))
        self.bad(lambda row:row['source_frame']['actual_byte_boundaries'][1]['actual_byte_pins'].pop())
        self.bad(lambda row:row['source_frame'].update(held_identity_after_owned_cleanup=None))
        self.bad(lambda row:row.update(post_Job_cleanup_resource_samples=[]))
        self.bad(lambda row:row['samples'][0].update(commit_used_percent=95))
        self.bad(lambda row:row['complete_runtime_budget'].update(unallocated_margin_seconds=0))
        self.bad(lambda row:row.update(P09_gate='PASS'))
    def test_complete_flat_closure_and_original600_budget(self):
        for name in (r.SELF,r.TEST,m.SELF):self.q.pin(name)
        required=r.scope.extend(self.required,self.q.snapshots)
        model=r.stable.runtime_budget(required,167)
        self.assertLess(model['predicted_runtime_combined_seconds'],600)
        self.assertEqual(model['unchanged_lock_deadline_seconds'],600)
        self.assertEqual(model['unallocated_margin_seconds'],60)
        self.assertEqual(model['selected_acquisition_rate_per_second'],14)
        self.assertEqual(model['unchanged_byte_native_ceiling_per_second'],20)
        self.assertEqual(model['final_postcleanup_distinct_sample_wait_allowance_seconds'],.5)
    def test_fixed_acceptor_original_AST_and_unique116_metadata(self):
        raw=m.candidate.read_source(self.q,m.candidate.ACCEPTOR_PIN)
        pin=dict(path='implementation/p09/evidence/p09-361-case116-current-runtime-run001.v1.json',bytes=1,sha256='0'*64)
        execute,proof=m.run_projection(raw,pin)
        self.assertTrue(proof['original_acceptor_AST_restored_exactly'])
        self.assertEqual(proof['queue_metadata_fields'],10)
        self.assertEqual(proof['explicit_distinct_sample_wait_seconds'],.5)
        with self.assertRaises(ValueError):m.run_projection(raw[:-1],pin)
    def synthetic_current_model(self):
        # MEMORY ONLY, conspicuously tagged. Never written as a receipt, passed
        # to a real queue writer or mistaken for Native/product execution.
        for name in (r.SELF,r.TEST,m.SELF):self.q.pin(name)
        expected=r.scope.extend(self.required,self.q.snapshots)
        row=copy.deepcopy(self.previous);ctx=r.context(r.CONFIG)
        row.update(synthetic_fixture_only_not_evidence=True,selected_test_index=116,
            selected_test_names=[ctx.CASE],passed_test_names=[ctx.CASE],test_arguments=ctx.arguments(),
            prior_queue_cases=109,next_case=116,prior_queue_fresh_pin=ctx.PRIOR_ACCEPT_PIN,
            source_freeze=list(expected.values()))
        row['bootstrap_metadata']['input_pins']=list(self.q.snapshots.values())
        row['imported_worker_source_paths']=sorted(set(row['imported_worker_source_paths'])|{r.SELF,r.TEST,m.SELF})
        n=len(expected);d=len({p.as_posix() for name in expected for p in Path(name).parents});held=n+d
        total=sum(p['bytes'] for p in expected.values());binary=sum(p['bytes'] for name,p in expected.items() if name.lower().endswith('.exe'))
        frame=row['source_frame'];frame.update(input_count=n,input_bytes=total)
        frame['held_identity_after_owned_cleanup'].update(regular_file_count=n,directory_count=d)
        for boundary in frame['actual_byte_boundaries']:
            boundary['actual_byte_pins']=list(expected.values());boundary['reader_diagnostics'].update(read_passes=n,bytes_read=total,
                bytes_read_by_kind=dict(binary=binary,other=total-binary))
        h=frame['handles'];h.update(input_lock_handles_opened=held,input_lock_handles_closed=held,
            handle_metadata_checks=2*held+2*n,byte_stream_identity_checks=2*n)
        h['borrowed_byte_streams'].update(duplicate_handles_opened=n,duplicate_handles_closed=n,shared_offset_resets=2*n,
            physical_handle_peak=held+n,new_duplicate_open_reservations=n,reused_stream_pressure_checkpoints=n,
            logical_read_leases=2*n,logical_read_lease_returns=2*n)
        h['native_open_pacing']['open_reservations']=held+n
        h['acquisition_phase_pressure']['acquisition_reservations']=held
        h['acquisition_source_warning_fail_fast']['checks']=held
        for guard in row['source_path_guard_diagnostics']:
            guard.update(native_metadata_queries_attempted=n,fresh_held_metadata_queries=n,original_path_guard_predicates=3*n)
        row['complete_runtime_budget']=r.stable.runtime_budget(expected,167)
        project,_=m.validator(m.candidate.read_source(self.q,m.candidate.ACCEPTOR_PIN),ctx)
        check,_=project(m.candidate.read_source(self.q,m.candidate.original.ORACLE_PIN),row,self.listing,self.oldbody)
        return row,check
    def test_memory_only_full_current_oracle_shape_not_actual116_or_queue_PASS(self):
        row,check=self.synthetic_current_model()
        proof=check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT);m.candidate.retained_evidence(row)
        self.assertTrue(row['synthetic_fixture_only_not_evidence'])
        self.assertEqual(proof['whole_runtime_input_count'],len(row['source_freeze']))
        with self.assertRaisesRegex(ValueError,'NO_SYNTHETIC'):
            m.validate_candidate(self.q,row,self.listing,self.oldbody,self.fresh,r.context(r.CONFIG))
    def test_memory_only_current_shape_missing_source_or_final_sample_rejected(self):
        row,check=self.synthetic_current_model()
        row['post_Job_cleanup_resource_samples']=[]
        with self.assertRaises(ValueError):check(row,self.listing,self.oldbody,self.fresh,CHECKPOINT)
    def test_actual_current_root_if_supplied_strict_not_synthetic(self):
        if ROOT_PIN is None:
            with self.assertRaises(ValueError):m.prepare(self.q,None)
            return
        row,listing,evidence,proof=m.prepare(self.q,ROOT_PIN)
        self.assertEqual(row['selected_test_index'],116)
        self.assertEqual(row['state'],r.PASS)
        self.assertTrue(proof['all_original_whole_Native_product_resource_and_cleanup_checks_retained'])
        ctx=r.context(r.CONFIG)
        project,_=m.validator(m.candidate.read_source(self.q,m.candidate.ACCEPTOR_PIN),ctx)
        check,_=project(m.candidate.read_source(self.q,m.candidate.original.ORACLE_PIN),row,listing,self.oldbody)
        for change in (lambda r:r['source_freeze'].pop(),lambda r:r.update(post_Job_cleanup_resource_samples=[]),
                lambda r:r.update(full249_current_qualified=True),lambda r:r.update(cleanup_confirmed=False)):
            altered=copy.deepcopy(row);change(altered)
            with self.assertRaises(ValueError):check(altered,listing,self.oldbody,self.fresh,CHECKPOINT)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root-bytes',type=int);parser.add_argument('--root-sha256')
    args=parser.parse_args();r.configure(116)
    if args.root_bytes is not None:
        ROOT_PIN=dict(path='implementation/p09/evidence/p09-361-case116-current-runtime-run001.v1.json',bytes=args.root_bytes,sha256=args.root_sha256)
        m.a.scope.pins([ROOT_PIN])
    guard=m.a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(FlatContracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,current_actual_root_checked=ROOT_PIN is not None,
        actual_product_or_Native_replayed=False,queue_delta=0)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
