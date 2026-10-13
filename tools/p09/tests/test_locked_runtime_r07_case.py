"""원 감독 연결/terminal/별도 frame 수용의 순수 계약. 실제 결과와 구분한다."""
import copy
import io
from contextlib import contextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import run_locked_runtime_r07_case as x


NAME='actual_import::field_ranges::mock_public_case'
OUTPUT='\nrunning 1 test\ntest '+NAME+' ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'


class Capture:
    def __init__(self,process):self.process=process
    def communicate(self,timeout):return self.process.output,self.process.errors


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.pin=dict(path='tools/p09/mock.txt',bytes=1,sha256='a'*64);self.inputs={self.pin['path']:self.pin}
        self.binding={'source':'original'}
        self.row=dict(schema_version=x.SCHEMA,state='PASS_SCOPED_NOT_GATE',native_frame_candidate_only=True,
            native_frame_closing_required=True,binding=self.binding,selected_test_names=[NAME],test_arguments=x.v.arguments(NAME),
            terminal_summary=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248),passed_test_names=[NAME],tests_passed=1,
            policy=x.c.POLICY,maximum_seconds=1200,cleanup_confirmed=True,owned_tree_empty=True,
            job_final=dict(active_processes=0,owned_processes=[]),resource_stop_reason=None,stop_reason=None,
            writer_authorized=True,worker_created=True,job_assigned=True,actual_job_membership_checked=True,
            owned_limits_verified=True,exit_code=0,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,PC_freeze_resolved=False,actual_Cargo_SQL_Hangul_run=False,
            P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
            capture=dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False),
            source_freeze=[self.pin],owned_source_reader_passes=[dict(read_passes=1,bytes_read=1,
                read_rates_by_kind=dict(binary=1048576,other=2097152),original_owned_read_operations_preserved=True)]*2,
            task='p204-r07-case-012-tests',minimal_worker_task='p204-r07-case-012-tests',
            minimal_owned_worker_path=x.m.SELF,minimal_worker_source_only_import_connected=True)
    def validate(self,row=None):x.validate_parent(self.row if row is None else row,NAME,self.binding,self.inputs)
    def test_complete_capture_uses_exact_one_named_terminal(self):
        found=[];kind=x.capture_type(NAME,found.append,Capture,Capture.communicate)
        cap=kind(SimpleNamespace(returncode=0,output=OUTPUT,errors=''));cap.communicate(1)
        self.assertTrue(cap.accepted);self.assertEqual(found,[cap])
    def test_wrong_name_stderr_or_partial_terminal_rejected(self):
        for output,errors in ((OUTPUT.replace(NAME,'other'),' '),(OUTPUT,'private failure'),(OUTPUT.replace('248 filtered','247 filtered'),'')):
            kind=x.capture_type(NAME,lambda cap:None,Capture,Capture.communicate)
            cap=kind(SimpleNamespace(returncode=0,output=output,errors=errors))
            with self.assertRaises(ValueError):cap.communicate(1)
            self.assertFalse(cap.accepted)
    def test_failed_child_never_has_accepted_terminal(self):
        kind=x.capture_type(NAME,lambda cap:None,Capture,Capture.communicate)
        cap=kind(SimpleNamespace(returncode=1,output=OUTPUT,errors=''));cap.communicate(1);self.assertFalse(cap.accepted)
    def test_valid_parent_requires_pending_separate_frame_closing(self):
        before=copy.deepcopy(self.row);self.validate();self.assertEqual(before,self.row)
        row=dict(self.row,native_frame_closing_required=False)
        with self.assertRaises(ValueError):self.validate(row)
    def test_source_hash_omission_or_missing_second_real_read_rejected(self):
        for kind in ('omission','one_pass','changed'):
            row=copy.deepcopy(self.row)
            if kind=='omission':row['source_freeze']=[]
            elif kind=='one_pass':row['owned_source_reader_passes'].pop()
            else:row['source_freeze'][0]['sha256']='b'*64
            with self.assertRaises(ValueError):self.validate(row)
    def test_policy_go_job_and_cleanup_weakening_rejected(self):
        for key in ('job_assigned','writer_authorized','actual_job_membership_checked','owned_limits_verified','cleanup_confirmed','owned_tree_empty'):
            row=dict(self.row,**{key:False})
            with self.assertRaises(ValueError):self.validate(row)
    def test_frame_parent_configures_original_worker_task_target_and_deadline(self):
        seen=[];frame=SimpleNamespace(check=lambda:None,boundaries=[],inputs=self.inputs)
        @contextmanager
        def scope(phase):yield
        def called(task,destination,seconds):
            seen.append((task,destination,seconds,x.c.__file__,x.c.TARGET,x.c.TASKS));return 2
        with patch.object(x,'ORIGINAL_RUN',called):
            self.assertEqual(x.run_parent(frame,12,NAME,'receipt',SimpleNamespace(scope=scope),self.binding),2)
        task,destination,seconds,path,target,tasks=seen[0]
        self.assertEqual((task,destination,seconds),('p204-r07-case-012-tests','receipt',1200))
        self.assertEqual(path,str(x.c.ROOT/x.m.SELF));self.assertEqual(target,x.m.TARGET);self.assertEqual(tasks,{task:x.m.TASK_ARGS})
    def test_parent_patch_restored_after_exception(self):
        original=(x.c.__file__,x.c.TASKS,x.c.Windows,x.c.pins)
        frame=SimpleNamespace(check=lambda:None,boundaries=[],inputs=self.inputs)
        with patch.object(x,'ORIGINAL_RUN',side_effect=RuntimeError('MOCK_STOP')):
            with self.assertRaises(RuntimeError):x.run_parent(frame,12,NAME,'receipt',None,self.binding)
        self.assertEqual((x.c.__file__,x.c.TASKS,x.c.Windows,x.c.pins),original)
    def test_frame_stop_prevents_original_parent_start(self):
        def stopped():raise ValueError('MOCK_FRAME_STOP')
        frame=SimpleNamespace(check=stopped)
        with patch.object(x,'ORIGINAL_RUN',side_effect=AssertionError('NO_PARENT')):
            with self.assertRaises(ValueError):x.run_parent(frame,12,NAME,'receipt',None,self.binding)
    def test_corpus_and_invalid_index_rejected_before_parent(self):
        with patch.object(x,'ORIGINAL_RUN',side_effect=AssertionError('NO_PARENT')):
            for index,name in ((0,NAME),(250,NAME),(True,NAME),(12,x.v.CORPUS_PREFIX+'mock')):
                with self.assertRaises(ValueError):x.run_parent(None,index,name,'receipt',None,self.binding)


if __name__=='__main__':unittest.main()
