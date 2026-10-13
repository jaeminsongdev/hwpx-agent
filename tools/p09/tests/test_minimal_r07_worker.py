"""선택·원 worker 위임 계약. GO/Job은 mock이며 실제 자식/Job을 만들지 않는다."""
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import minimal_r07_worker as m
import conservative_maintenance as c


class MinimalWorkerTests(unittest.TestCase):
    def setUp(self):
        self.parent=dict(source_test_names=[f'public_case_{i}' for i in range(249)],compiled_test_executable_pin=dict(m.EXE))

    def test_exact_single_arguments(self):
        self.assertEqual(m.select(11,self.parent),('public_case_10',
            ['public_case_10','--exact','--test-threads=1','--format=pretty','--color=never']))

    def test_index_bounds_and_boolean_rejected(self):
        for value in (0,250,True,1.0,'11'):
            with self.assertRaises(ValueError):m.select(value,self.parent)

    def test_duplicate_or_incomplete_inventory_rejected(self):
        self.parent['source_test_names'][1]=self.parent['source_test_names'][0]
        with self.assertRaises(ValueError):m.select(1,self.parent)
        self.setUp();self.parent['source_test_names'].pop()
        with self.assertRaises(ValueError):m.select(1,self.parent)

    def test_corpus_is_pending_not_silently_executed(self):
        self.parent['source_test_names'][0]='actual_import::formula_policy_issuer::corpus::all36'
        with self.assertRaisesRegex(ValueError,'REGULAR_PUBLIC_CASE_ONLY'):m.select(1,self.parent)

    def test_nonpublic_name_or_exe_drift_rejected(self):
        for name in ('--list','case name','../case'):
            self.parent['source_test_names'][0]=name
            with self.assertRaises(ValueError):m.select(1,self.parent)
        self.setUp();self.parent['compiled_test_executable_pin']['sha256']='0'*64
        with self.assertRaises(ValueError):m.select(1,self.parent)

    def test_task_scope_rejected_before_import_or_child(self):
        with patch.object(m,'load_maintenance',side_effect=AssertionError('NO_IMPORT')):
            for task in ('p204-r07-case-11-tests','p191-r07-case-011-tests','p204-r07-case-000-tests','p204-r07-case-250-tests'):
                with self.assertRaises(ValueError):m.worker(task)

    def test_input_source_hash_mismatch_rejected(self):
        with patch.object(Path,'resolve',return_value=m.ROOT/'mock.py'), \
                patch.object(Path,'is_symlink',return_value=False),patch.object(Path,'is_junction',return_value=False), \
                patch.object(Path,'is_file',return_value=True),patch.object(Path,'stat',return_value=SimpleNamespace(st_size=1)), \
                patch.object(Path,'open',return_value=io.BytesIO(b'x')):
            with self.assertRaisesRegex(ValueError,'SOURCE_BYTE_HASH'):
                m.bounded_bytes(m.ROOT/'mock.py',dict(bytes=1,sha256='0'*64))

    def test_source_outside_root_rejected_before_read(self):
        with patch.object(Path,'open',side_effect=AssertionError('NO_READ')):
            with self.assertRaises(ValueError):m.bounded_bytes(m.ROOT.parent/'outside.py',dict(bytes=1,sha256='0'*64))

    def fake_windows(self,member=True):
        def in_job(handle,job,pointer):pointer._obj.value=member;return True
        return SimpleNamespace(k=SimpleNamespace(GetCurrentProcess=lambda:1,IsProcessInJob=in_job))

    def execute(self,go='P149_GO\n',member=True,call=None):
        with patch.object(m,'inventory',return_value=self.parent),patch.object(m,'load_maintenance',return_value=c), \
                patch.object(c,'Windows',return_value=self.fake_windows(member)),patch.object(c.sys,'stdin',io.StringIO(go)), \
                patch.object(c.shutil,'which',return_value='mock-cargo'),patch.object(c.subprocess,'call',call or (lambda *a,**k:0)):
            return m.worker('p204-r07-case-011-tests')

    def test_original_GO_denial_retained(self):
        with self.assertRaisesRegex(ValueError,'WORKER_NOT_AUTHORIZED'):self.execute(go='')

    def test_original_Job_membership_denial_retained(self):
        with self.assertRaisesRegex(ValueError,'WORKER_NOT_IN_JOB'):self.execute(member=False)

    def test_exact_exe_env_flags_and_return_preserved(self):
        seen=[]
        def called(args,**kw):seen.append((args,kw));return 7
        self.assertEqual(self.execute(call=called),7)
        args,kw=seen[0];self.assertEqual(args,[str(m.ROOT/m.EXE['path']),*m.select(11,self.parent)[1]])
        self.assertEqual(kw['env']['RUST_TEST_NOCAPTURE'],'0');self.assertEqual(kw['stdin'],c.subprocess.DEVNULL)
        self.assertEqual(kw['creationflags'],c.subprocess.BELOW_NORMAL_PRIORITY_CLASS|c.subprocess.CREATE_NO_WINDOW)
        self.assertEqual(kw['cwd'],m.ROOT)

    def test_original_roles_restored_after_failure(self):
        tasks,target,call=c.TASKS,c.TARGET,c.subprocess.call
        def denied(*args,**kw):raise RuntimeError('MOCK_CHILD_ERROR')
        with self.assertRaises(RuntimeError):self.execute(call=denied)
        self.assertIs(c.TASKS,tasks);self.assertEqual(c.TARGET,target);self.assertIs(c.subprocess.call,call)


if __name__=='__main__':unittest.main()
