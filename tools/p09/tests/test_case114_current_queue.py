"""Guarded114 binding/closed metadata/original-worker contracts, no product run."""
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_case114_current_queue as r

CHECKPOINT=lambda:None


class Current114Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q=r.stable.accepted112.AcceptanceReader(r.c.ROOT,CHECKPOINT)
        cls.required,cls.rust=r.binding(cls.q)
        cls.entry,cls.proof=r.entry()
        cls.engine,cls.engine_proof=r.template()
        cls.terminal=cls.engine.terminal_api(cls.q)
    @classmethod
    def tearDownClass(cls):cls.q.finish()
    def test_prior107_full1731_Rust787_not_small_probe_or_fixtures(self):
        self.assertEqual(len(self.required),1731);self.assertEqual(len(self.rust),787)
        self.assertEqual(self.required[r.scope.EXE_PIN['path']],r.scope.EXE_PIN)
        self.assertTrue(r.PROBE_PIN['path'] in self.q.snapshots)
        self.assertEqual(len([n for n in self.q.snapshots if '/p361-case113-qualified-code/' in n]),10)
    def test_original113_entry_and112_engine_AST_guards_undo_exact(self):
        self.assertTrue(self.proof['qualified113_entry_AST_restored_exactly'])
        self.assertEqual(self.proof['receipt_path_constants_projected'],2)
        self.assertTrue(self.engine_proof['original_engine_AST_restored_exactly'])
        self.assertFalse(self.proof['original_GO_Job_worker_resource_and_frame_statements_replaced'])
    def test_modified113_source_rejected_before_definitions(self):
        with (r.c.ROOT/r.ENTRY_PIN['path']).open('rb') as stream:raw=stream.read(r.ENTRY_PIN['bytes']+1)
        for source in (raw[:-1],raw.replace(b'failed_close=False',b'failed_close=True')):
            with self.subTest(),self.assertRaises(ValueError):r.entry_projection(source)
    def test_exact114_terminal_no_replay113_or_112(self):
        output='running 1 test\ntest '+r.CASE+' ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'
        self.assertEqual(self.terminal.terminal(output,'',r.CASE)['passed'],1)
        for name in (r.stable.CASE,r.scope.CASE112):
            with self.subTest(),self.assertRaises(ValueError):self.terminal.terminal(output.replace(r.CASE,name),'',r.CASE)
    def test_task_and_retry_fail_closed_not_missing_observation_restart(self):
        for task in ('case113-current-r001-tests','case114-current-r000-tests','case114-current-r001'):
            with self.subTest(),self.assertRaises(ValueError):r.run_for(task)
        with self.assertRaisesRegex(ValueError,'NO_AUTOMATIC_RETRY'):r.binding_attempt(NS(),2)
    def worker_patches(self,go=True,job=True):
        def member(process,owned,pointer):pointer._obj.value=job;return True
        return (patch.object(r.c,'Windows',return_value=NS(k=NS(GetCurrentProcess=lambda:17,IsProcessInJob=member))),
            patch.object(r.c.sys,'stdin',io.StringIO('P149_GO\n' if go else 'BAD\n')),
            patch.object(r.c.shutil,'which',return_value='fake-cargo'),patch.object(r.stable.prior.build,'direct_path'))
    def test_original_worker_exact114_job_GO_assertions_and_threads(self):
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
    def test_complete_new_closure_costs_retained_without_deadline_or_IO_boost(self):
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
    def test_prior107_candidate_pin_or_count_not_arbitrary_PASS(self):
        real=self.q.json
        def changed(name):
            row=real(name)
            if name==r.PRIOR_ACCEPT_PIN['path']:row=copy.deepcopy(row);row['accepted_count_after']=108
            return row
        with patch.object(self.q,'json',side_effect=changed),self.assertRaises(ValueError):r.binding(self.q)
    def test_original_failure_serializes114_not_queue_or_gate_pass(self):
        stream=io.StringIO()
        def fake_run(task,destination,maximum):
            self.assertIn('case114-current-runtime-run997',str(destination));self.assertEqual(maximum,1200)
            json.dump(dict(state='DEFERRED_NOT_STARTED',writer_authorized=False,cleanup_confirmed=True,
                owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]),stop_reason='STOP_NATIVE_OPEN_AFTER_HOST_SATURATION'),stream)
            return 2
        with patch.object(r.c,'run',side_effect=fake_run):self.assertEqual(self.engine.run_owned(997),2)
        row=json.loads(stream.getvalue());self.assertEqual(row['selected_test_index'],114)
        self.assertEqual(row['prior_queue_cases'],107);self.assertEqual(row['accepted_count_delta'],0)
        self.assertFalse(row['Native_source_frame_qualified'])


if __name__=='__main__':
    guard=r.stable.accepted112.Guard();result=None
    try:
        guard.acquire();CHECKPOINT=guard.check
        result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Current114Contracts))
    finally:guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,passed=bool(result and result.wasSuccessful()),
        cleanup_confirmed=guard.cleanup,product_or_Native_frame_executed=False)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
