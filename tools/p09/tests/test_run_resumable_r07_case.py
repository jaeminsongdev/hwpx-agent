import copy
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import run_resumable_r07_case as v


class RunSingleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=json.loads((v.c.ROOT/v.run.PARENT['path']).read_text(encoding='utf-8'))
        cls.expected,cls.exe=v.run.parent_scope(cls.parent)
        cls.names=cls.parent['source_test_names']
    def invoke(self,go='P149_GO\n',member=True,index=1):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=member;return True
        calls=[]
        with patch.object(v.c,'Windows',return_value=SimpleNamespace(k=Kernel())), \
                patch.object(v.c.sys,'stdin',io.StringIO(go)),patch.object(v.c.shutil,'which',return_value='fixture-cargo'), \
                patch.object(v.c.subprocess,'call',side_effect=lambda args,**kw:calls.append((args,kw)) or 0):
            result=v.worker(v.task_for(index))
        return result,calls
    def test_exact_one_current_exe_no_compile(self):
        code,calls=self.invoke();self.assertEqual(code,0)
        self.assertEqual(calls[0][0],[str(v.c.ROOT/self.exe['path']),*v.v.arguments(self.names[0])])
        self.assertEqual(len(calls),1)
    def test_GO_and_membership_before_call(self):
        for go,member in (('wrong\n',True),('P149_GO\n',False)):
            with self.assertRaises(ValueError):self.invoke(go,member)
    def test_assertions_overflow_capture_threads_and_rustup_retained(self):
        with patch.dict(v.c.os.environ,{'RUST_TEST_NOCAPTURE':'1'}):_,calls=self.invoke()
        env=calls[0][1]['env']
        for k,value in dict(RUST_TEST_NOCAPTURE='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true').items():
            self.assertEqual(env[k],value)
    def test_worker_policy_roles_restored(self):
        target=v.c.TARGET;tasks=v.c.TASKS;policy=copy.deepcopy(v.c.POLICY);call=v.c.subprocess.call
        self.invoke();self.assertEqual(v.c.TARGET,target);self.assertIs(v.c.TASKS,tasks)
        self.assertEqual(v.c.POLICY,policy);self.assertIs(v.c.subprocess.call,call)
    def test_67_history_only_moved_to_boundaries(self):
        runtime,history=v.runtime_scope(self.expected,self.exe)
        self.assertEqual(len(history),67);self.assertEqual(sum(n.endswith('.exe') for n in runtime),1)
        self.assertEqual(set(runtime)|history,set(self.expected))
        self.assertEqual({n for n in self.expected if not n.endswith('.exe')},
                         {n for n in runtime if not n.endswith('.exe')})
    def test_missing_history_or_current_exe_rejected(self):
        expected=copy.deepcopy(self.expected);del expected[self.exe['path']]
        with self.assertRaises(ValueError):v.runtime_scope(expected,self.exe)
        expected=copy.deepcopy(self.expected);old=next(n for n in expected if n.endswith('.exe') and n!=self.exe['path'])
        del expected[old]
        with self.assertRaises(ValueError):v.runtime_scope(expected,self.exe)
    def test_corpus_not_ignored_but_no_actual_launch_before_split(self):
        for i,n in enumerate(self.names,1):
            if n.startswith(v.v.CORPUS_PREFIX):
                with self.assertRaises(ValueError):v.selected_name(i,self.names)
    def test_task_indices_and_generation_closed(self):
        for i in (0,250,True,'1'):
            with self.assertRaises(ValueError):v.task_for(i)
        for i in (0,100,True,'1'):
            with self.assertRaises(ValueError):v.paths(i)
        with self.assertRaises(ValueError):v.worker('p152-current-stored-full-r07-tests')
    def test_original1200_deadline_not_extended(self):
        v.run.original.require_scope(1200)
        with self.assertRaises(ValueError):v.run.original.require_scope(1201)
    def test_single_summary_stays_distinct_from_full249(self):
        name=self.names[0]
        output=f'running 1 test\ntest {name} ... ok\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out; finished in 0.01s\n'
        self.assertEqual(v.v.terminal(output,'',name)['passed'],1)
        with self.assertRaises(ValueError):v.run.original.full.validate_output(output)

    def test_mutated_scoped_receipt_state_does_not_turn_normal_exit_into_failure(self):
        status=v.v.plan(self.names,self.expected,self.exe)
        binding=(self.expected,self.names,self.exe,status)
        destination=SimpleNamespace(parent=SimpleNamespace(mkdir=lambda **kw:None))
        def simulate_parent(*args):
            cls=v.run.original.full.bounded.BoundedProcessCapture
            capture=cls(SimpleNamespace());capture.accepted=True
            capture.diagnostics=lambda:dict(error_code=None)
            row=dict(state='PASS_SCOPED_NOT_GATE',policy=v.c.POLICY,maximum_seconds=1200,
                cleanup_confirmed=True,owned_tree_empty=True,job_final=dict(active_processes=0,owned_processes=[]),
                stop_reason=None,exit_code=0,writer_authorized=True,worker_created=True,job_assigned=True,
                owned_limits_readback=dict(verified=True))
            json.dump(row,io.StringIO())
            self.assertEqual(row['state'],v.v.CASE_PASS)
            return 2  # Original c.run compares its old state name here.
        with patch.object(v.s,'scoped_path',return_value=destination), \
                patch.object(v.BASE_CAPTURE,'__init__',lambda self,*a,**kw:None), \
                patch.object(v.c,'run',simulate_parent):
            code,_=v.run_case(1,binding)
        self.assertEqual(code,0)


if __name__=='__main__':unittest.main()
