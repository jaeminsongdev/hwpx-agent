"""Guarded actual108 binding/115 engine contracts, no product or Native run."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_case115_current_queue as r

CHECKPOINT=lambda:None


class Current115Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=r.accepted114.a.AcceptanceReader(r.c.ROOT,CHECKPOINT)
        cls.required,cls.rust=r.binding(cls.q)
        cls.entry,cls.proof=r.entry()
        cls.engine,cls.engine_proof=r.template()
        cls.terminal=cls.engine.terminal_api(cls.q)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def test_distinct108_complete_source_and_current_Rust787_not_fixture(self):
        self.assertGreaterEqual(len(self.required),1761);self.assertEqual(len(self.rust),787)
        self.assertEqual(self.required[r.scope.EXE_PIN['path']],r.scope.EXE_PIN)
        self.assertIn(r.accepted114.SOURCE_PIN['path'],self.q.snapshots)
        self.assertEqual(len([n for n in self.q.snapshots if '/p361-case114-compound-qualified-code/' in n]),4)
        source=r.accepted114.a.read_exact(self.q,r.accepted114.SOURCE_PIN)
        self.assertTrue(all(self.required[p['path']]==p for p in source['complete_source_pins']))
    def test_exact_engine_and_one_same_observer_timestamp_only(self):
        self.assertTrue(self.proof['qualified113_entry_AST_restored_exactly'])
        self.assertEqual(self.proof['receipt_path_constants_projected'],2)
        self.assertTrue(self.engine_proof['original_engine_AST_restored_exactly'])
        proof=self.engine_proof['postcleanup_same_owner_handoff']
        self.assertTrue(proof['exact_original_engine_code_verified_before_change'])
        self.assertTrue(proof['engine_AST_restored_exactly'])
        self.assertEqual(proof['added_timestamp_assignments'],1)
        self.assertFalse(proof['CPU_RAM_native_deadlines_extended'])
        self.assertFalse(proof['extra_sampler_query_thread_or_process'])
        self.assertFalse(proof['missing_interval_errors_suppressed'])
        final=self.engine_proof['final_postcleanup_actual_resource_sample']
        self.assertTrue(final['all_preexisting_engine_AST_restored_exactly'])
        self.assertTrue(final['final_original_guard_requirement_added_once'])
        self.assertFalse(final['new_observer_or_thread_or_zero_CPU_fabricated'])
    def test_entry_drift_rejected_before_definitions(self):
        with (r.c.ROOT/r.ENTRY_PIN['path']).open('rb') as stream:raw=stream.read(r.ENTRY_PIN['bytes']+1)
        with self.assertRaises(ValueError):r.entry_projection(raw[:-1])
    def test_exact115_terminal_rejects_replayed112_113_114(self):
        output='running 1 test\ntest '+r.CASE+' ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'
        self.assertEqual(self.terminal.terminal(output,'',r.CASE)['passed'],1)
        for name in (r.accepted114.s.r.CASE,r.stable.CASE,r.scope.CASE112):
            with self.subTest(),self.assertRaises(ValueError):self.terminal.terminal(output.replace(r.CASE,name),'',r.CASE)
    def test_task_and_retry_refuse_old_case_or_observation_timeout_restart(self):
        self.assertEqual(r.run_for(r.task_for(1)),1)
        for task in ('case114-current-r001-tests','case115-current-r000-tests','case115-current-r001'):
            with self.subTest(),self.assertRaises(ValueError):r.run_for(task)
        with self.assertRaisesRegex(ValueError,'NO_AUTOMATIC_RETRY'):r.binding_attempt(NS(),2)
    def worker_patches(self,go=True,job=True):
        def member(process,owned,pointer):pointer._obj.value=job;return True
        return (patch.object(r.c,'Windows',return_value=NS(k=NS(GetCurrentProcess=lambda:17,IsProcessInJob=member))),
            patch.object(r.c.sys,'stdin',io.StringIO('P149_GO\n' if go else 'BAD\n')),
            patch.object(r.c.shutil,'which',return_value='fake-cargo'),patch.object(r.stable.prior.build,'direct_path'))
    def test_original_worker_GO_Job_115_assertions_and_threads(self):
        p1,p2,p3,p4=self.worker_patches()
        with p1,p2,p3,p4,patch.object(r.subprocess,'call',return_value=0) as call:
            self.assertEqual(self.engine.worker(r.task_for(999)),0)
        self.assertEqual(call.call_args.args[0],[str(r.c.ROOT/r.scope.EXE_PIN['path']),*r.arguments()])
        for k,v in dict(RUST_TEST_THREADS='1',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items():
            self.assertEqual(call.call_args.kwargs['env'][k],v)
        for go,job in ((False,True),(True,False)):
            p1,p2,p3,p4=self.worker_patches(go,job)
            with p1,p2,p3,p4,patch.object(r.subprocess,'call') as bad:
                with self.assertRaises(ValueError):self.engine.worker(r.task_for(998))
            bad.assert_not_called()
    def test_whole_new_closure_budget_preserves_original_costs_limits_and_margin(self):
        for name in (r.SELF,r.TEST):self.q.pin(name)
        required=r.scope.extend(self.required,self.q.snapshots)
        model=r.runtime_budget(required,167);baseline=r.scope.cost(required,14)
        self.assertLess(model['predicted_runtime_combined_seconds'],600)
        self.assertEqual(model['unchanged_lock_deadline_seconds'],600)
        self.assertEqual(model['selected_acquisition_rate_per_second'],14)
        self.assertEqual(model['unchanged_byte_native_ceiling_per_second'],20)
        self.assertEqual(model['two_actual_byte_pass_nominal_seconds'],baseline['two_actual_byte_pass_nominal_seconds'])
        self.assertEqual(model['removed_second_duplicate_handle_reservations'],len(required))
        self.assertEqual(model['unallocated_margin_seconds'],60)
        self.assertEqual(model['additional_serial_PDH_maximum_sample_budget_seconds'],2.05)
        self.assertEqual(model['final_postcleanup_distinct_sample_wait_allowance_seconds'],.5)
        self.assertEqual(model['predicted_runtime_combined_seconds'],r.native.model(required,167)['predicted_runtime_combined_seconds']+.5)
    def test_distinct_parent_wrong_count_or_rebased_single_frame_refused(self):
        real=self.q.json
        for key,value in (('accepted_count_after',109),('Native_product_single_frame_qualified',True),
                ('product_and_source_epochs_distinct',False),('accepted_epoch_key','fake')):
            def changed(name):
                row=real(name)
                if name==r.PRIOR_ACCEPT_PIN['path']:row=copy.deepcopy(row);row[key]=value
                return row
            with self.subTest(),patch.object(self.q,'json',side_effect=changed),self.assertRaises(ValueError):r.binding(self.q)
    def test_failure_serializes115_without_Gate_or_queue_success(self):
        stream=io.StringIO()
        def fake_run(task,destination,maximum):
            self.assertIn('case115-current-runtime-run997',str(destination));self.assertEqual(maximum,1200)
            json.dump(dict(state='DEFERRED_NOT_STARTED',writer_authorized=False,cleanup_confirmed=True,
                owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]),stop_reason='STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'),stream)
            return 2
        with patch.object(r.c,'run',side_effect=fake_run):self.assertEqual(self.engine.run_owned(997),2)
        row=json.loads(stream.getvalue());self.assertEqual(row['selected_test_index'],115)
        self.assertEqual(row['prior_queue_cases'],108);self.assertEqual(row['accepted_count_delta'],0)
        self.assertFalse(row['Native_source_frame_qualified'])
    def test_original_sample_not_fabricated_or_moved_forward(self):
        self.assertEqual(r.handoff.timestamp((50.,0.),clock=lambda:50.),50.)
        self.assertGreaterEqual(50.-r.handoff.timestamp((49.4,0.),clock=lambda:50.),.5)
        for value in (None,[],(True,0),(51.,0),(49.,float('nan'))):
            with self.subTest(),self.assertRaises(ValueError):r.handoff.timestamp(value,clock=lambda:50.)
    def test_fast_and_already_due_closing_produce_real_same_owner_sample(self):
        for first,last in ((50.1,50.),(50.6,50.)):
            now=[first];stamp=[last];samples=[];waits=[];calls=[]
            def guard():
                calls.append(now[0])
                if now[0]-stamp[0]>=.5:samples.append(now[0]);stamp[0]=now[0]
            def sleep(value):waits.append(value);now[0]+=value
            r.final_sample.sample(guard,lambda:stamp[0],lambda:len(samples),clock=lambda:now[0],sleeper=sleep)
            self.assertEqual(len(samples),1)
            self.assertLessEqual(sum(waits),.5)
            self.assertEqual(len(waits),1 if first<50.5 else 0)
    def test_final_sampling_never_suppresses_failure_or_fabricates_zero(self):
        def failed():raise ValueError('ORIGINAL_DEADLINE_OR_CPU_RAM_STOP')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_DEADLINE'):
            r.final_sample.sample(failed,lambda:50.,lambda:0,clock=lambda:50.1)
        with self.assertRaisesRegex(ValueError,'NO_SUPPRESSED_DUE_SAMPLE'):
            r.final_sample.sample(lambda:None,lambda:50.,lambda:0,clock=lambda:50.6)
        with self.assertRaisesRegex(ValueError,'REAL_FINAL_SAMPLE_REQUIRED'):
            r.final_sample.sample(lambda:None,lambda:50.,lambda:0,clock=lambda:50.1,sleeper=lambda _:None)


if __name__=='__main__':
    guard=r.accepted114.a.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Current115Contracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_or_Native_frame_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
