import copy
import hashlib
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_case112_current_stored as r
import current_stored_native_bridge as native
from test_current_stored_native_bridge import Reader,PacerNative
from test_borrowed_locked_streams import API


class MetadataReader(Reader):
    def json(self,name):return json.loads(self.text(name))
    def checkpoint(self):pass


class RuntimeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.required,cls.rust=r.binding(MetadataReader())
        cls.lean=native.load(Reader(),12,r.c)
        cls.terminal=r.terminal_api(Reader())
    def test_authoritative_old105_and_current_full_union_binding_not_single_fixture_scope(self):
        self.assertEqual(len(self.required),1686);self.assertEqual(len(self.rust),787)
        self.assertEqual(self.required[r.scope.EXE_PIN['path']],r.scope.EXE_PIN)
        self.assertIn(r.scope.CURRENT_MODULE['path'],self.rust)
        for row in r.scope.ARCHIVES:self.assertEqual(self.required[row['path']],row)
    def test_original_full_name_terminal_and_arguments_used_exactly(self):
        output='running 1 test\ntest '+r.scope.CASE112+' ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'
        self.assertEqual(self.terminal.arguments(r.scope.CASE112),r.arguments())
        self.assertEqual(self.terminal.terminal(output,'',r.scope.CASE112)['passed'],1)
        for bad in (output.replace('1 passed','2 passed'),output.replace('248 filtered','247 filtered'),
                    output.replace(r.scope.CASE112,'other_test'),output+'test other_test ... ok\n'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):self.terminal.terminal(bad,'',r.scope.CASE112)
        with self.assertRaises(ValueError):self.terminal.terminal(output,'warning',r.scope.CASE112)
    def test_complete_runtime_budget_adds_product_inventory_commit_not_source_only_model(self):
        model=r.runtime_budget(self.required,160)
        self.assertEqual(model['product_allowance_seconds'],20)
        self.assertEqual(model['final_inventory_pacing_seconds'],8)
        self.assertGreater(model['selected_acquisition_rate_per_second'],10)
        self.assertLessEqual(model['selected_acquisition_rate_per_second'],14)
        self.assertLess(model['predicted_runtime_combined_seconds'],600)
        with self.assertRaisesRegex(ValueError,'NO_SAFE_COMPLETE_RUNTIME_BUDGET'):r.runtime_budget(self.required,6000)
    def test_worker_only_exact112_original_owned_dispatch(self):
        argv=['cargo',*r.MARKER_ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(r.TARGET)]
        kwargs=dict(cwd=r.c.ROOT,stdin=r.subprocess.DEVNULL,
            env=dict(RUST_TEST_THREADS='1',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true'))
        def original(task):return r.subprocess.call(argv,**kwargs)
        with patch.object(r.build,'direct_path'),patch.object(r.subprocess,'call',return_value=0) as raw, \
             patch.object(r.c,'worker',side_effect=original):
            self.assertEqual(r.worker(r.task_for(998)),0)
        self.assertEqual(raw.call_args.args[0],[str(r.c.ROOT/r.scope.EXE_PIN['path']),*r.arguments()])
        self.assertEqual(raw.call_args.kwargs['env']['RUST_TEST_NOCAPTURE'],'0')
    def test_generation_and_assertion_environment_fail_closed(self):
        for run in (True,0,1000,'1'):
            with self.subTest(run=run),self.assertRaises(ValueError):r.task_for(run)
        for task in ('old111-tests','case112-current-r000-tests','case112-current-r001'):
            with self.subTest(task=task),self.assertRaises(ValueError):r.run_for(task)
        argv=['cargo',*r.MARKER_ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(r.TARGET)]
        kwargs=dict(cwd=r.c.ROOT,stdin=r.subprocess.DEVNULL,env=dict(RUST_TEST_THREADS='2'))
        with patch.object(r.build,'direct_path'),patch.object(r.c,'worker',side_effect=lambda _:r.subprocess.call(argv,**kwargs)):
            with self.assertRaises(ValueError):r.worker(r.task_for(997))
    def frame(self):
        api=PacerNative();api.pacer.checkpoint=lambda:None
        owner=NS(lock=threading.Lock(),samples=[dict(system_cpu_percent=20)])
        early=self.lean.EarlySourceCheckpoint(lambda:None,owner);api.pacer.checkpoint=early
        held=self.lean.InputLocks(r.c.ROOT,early,owner,NS(phase='metadata_hash'),api=api,borrow_api=API(api))
        # The fake Native reports size1 by default; expose the actual borrowed3
        # bytes to the same size and stream identity checks.
        original=api.open
        def sized(path,directory):
            handle=original(path,directory)
            if not directory:api.handles[handle]['size']=3
            return handle
        api.open=sized
        row=dict(path='tools/p09/mock.py',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())
        frame=native.frames.Frame(native.frames.Registry(),{row['path']:row},early,held=held);frame.acquire()
        return frame,api,owner
    def boundary(self,frame,owner,guards):
        return self.lean.read_with_held_path_guards(frame,lambda guard:r.BoundaryReader(r.c.ROOT,guard,owner=owner,api=self.lean),
            lambda:None,guards)
    def test_original_two_borrowed_bytes_exact_identity_path_predicates_and_final_cleanup(self):
        frame,api,owner=self.frame();guards=[]
        try:
            self.boundary(frame,owner,guards);self.boundary(frame,owner,guards)
            owned=dict(cleanup_confirmed=True,owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]))
            snapshot=frame.commit(owned)
            self.assertEqual(snapshot['frame_state'],'COMMITTED')
            self.assertEqual(snapshot['handles']['byte_stream_identity_checks'],2)
            self.assertEqual(snapshot['handles']['borrowed_byte_streams']['duplicate_handles_closed'],2)
            self.assertEqual(snapshot['handles']['input_lock_handles_remaining'],0)
            self.assertEqual([x['original_path_guard_predicates'] for x in guards],[3,3])
            self.assertTrue(all(x['original_reader_root_restored'] for x in guards));self.assertEqual(api.handles,{})
        finally:frame.close()
    def test_byte_or_identity_drift_never_committed_and_borrow_root_restored(self):
        frame,api,owner=self.frame();guards=[]
        try:
            handle=next(handle for _,_,handle,directory in frame.held.owned if not directory)
            api.handles[handle]['identity']=[9,9]
            with self.assertRaisesRegex(ValueError,'FRESH_HELD_PATH_IDENTITY'):self.boundary(frame,owner,guards)
            self.assertTrue(guards[0]['original_reader_root_restored'])
        finally:frame.close()
        self.assertEqual(api.handles,{})
    def test_incomplete_source_or_owned_cleanup_cannot_be_committed(self):
        frame,api,owner=self.frame();guards=[]
        try:
            self.boundary(frame,owner,guards)
            with self.assertRaises(ValueError):frame.commit(dict(cleanup_confirmed=True,owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[])))
            self.boundary(frame,owner,guards)
            with self.assertRaises(ValueError):frame.commit(dict(cleanup_confirmed=False,owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[])))
        finally:frame.close()
        self.assertEqual(api.handles,{})


if __name__=='__main__':unittest.main()
