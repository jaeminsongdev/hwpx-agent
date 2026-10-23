"""New startup contracts: models plus actual readonly registration/empty Job.

Never invokes real Hwp CreateProcess/Resume, COM, document IO or a product attempt.
Model APIs are explicitly local in-memory objects, not installed native evidence.
"""
import ast
import copy
import ctypes
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import accept_case112_current_epoch as a
import crossref_native_startup as startup


def parent(flags=0):
    return dict(job_present=True,query_succeeded=True,flags=flags,affinity=1,priority=0x4000,
        rate_flags=5,rate=625)


def model(created=True):
    events=[];state=startup.PreassignedNativeStartup.__new__(startup.PreassignedNativeStartup)
    state.closed=False;state.start_attempted=False;state.resume_attempted=False;state.bind_attempted=False
    state.process=None;state.thread=None;state.pid=None;state.birth=None;state.session=None;state.parent=None
    state.guard=NS(check=lambda:events.append('guard'))
    state.profile=dict(state='unstarted',created=False,pre_run_verified=False,resumed=False,
        native_startup_qualified=False,native_execution_authorized=False)
    state._fresh_image=lambda:events.append('fresh_image')
    state._parent_unchanged=lambda:parent()
    state.verify_suspended=lambda:events.append('pre_run_verify')
    def initialize(attributes,count,flags,size):
        ctypes.cast(size,ctypes.POINTER(ctypes.c_size_t)).contents.value=64
        if attributes is None:ctypes.set_last_error(122);return False
        events.append('attribute_initialize');return True
    def update(attributes,flags,kind,jobs,size,previous,length):
        assert kind==startup.JOB_LIST and jobs[0]==777 and size==ctypes.sizeof(startup.w.HANDLE)
        events.append('job_list');return True
    def create(image,command,ps,ts,inherit,flags,env,cwd,si,pi):
        assert image==startup.limits.EXECUTABLE and not inherit and flags==startup.CREATE_FLAGS
        assert command.value.endswith(' -Automation') and '-regserver' not in command.value.lower()
        assert ctypes.cast(si,ctypes.POINTER(startup.StartupInfoEx)).contents.attributes
        info=ctypes.cast(pi,ctypes.POINTER(startup.ProcessInfo)).contents
        info.process,info.thread,info.pid,info.tid=1001,1002,91,92
        events.append('create_suspended');return created
    kernel=NS(InitializeProcThreadAttributeList=initialize,UpdateProcThreadAttribute=update,
        CreateProcessW=create,DeleteProcThreadAttributeList=lambda p:events.append('attribute_delete'),
        WaitForSingleObject=lambda h,t:258,ResumeThread=lambda h:1)
    state.windows=NS(k=kernel,accounting=lambda j:dict(active_processes=0))
    state.owner_job=NS(job=777,readback=lambda:events.append('limits_readback'))
    return state,events


class NativeStartupContracts(unittest.TestCase):
    actual=[]

    def test_01_fixed_registered_command_rejects_extra_args_and_other_executables(self):
        image=startup.limits.EXECUTABLE
        for text in (image+' -Automation','"'+image+'" -Automation','  "'+image.upper()+'" -automation  '):
            self.assertEqual(startup.registered_command(text),[image,'-Automation'])
        for value in (None,True,'',image,image+' /Automation',image+' -Automation -regserver',
                image+' -Automation\r\nwhoami','cmd.exe /c '+image+' -Automation',
                '"'+image+' -Automation"','D:\\other\\hwp.exe -Automation',image+' -Embedding'):
            with self.assertRaises(ValueError):startup.registered_command(value)

    def test_02_parent_kill_time_breakaway_or_unknown_policy_rejected(self):
        for flags in (0x2000,0x800,0x1000,2,4):
            with patch.object(startup.host,'read_parent_cpu',return_value=parent(flags)):
                with self.assertRaisesRegex(ValueError,'PARENT_LIFECYCLE_NOT_NATIVE_SAFE'):
                    startup.parent_without_prompt_kill(None)
        with patch.object(startup.host,'read_parent_cpu',return_value=dict(parent(),query_succeeded=False)):
            with self.assertRaises(ValueError):startup.parent_without_prompt_kill(None)
        with patch.object(startup.host,'read_parent_cpu',return_value=parent()):
            with self.assertRaisesRegex(ValueError,'PARENT_LIFECYCLE_NOT_NATIVE_SAFE'):
                startup.parent_without_prompt_kill(None)
        jobless=dict(parent(),job_present=False,query_succeeded=False)
        with patch.object(startup.host,'read_parent_cpu',return_value=jobless):
            self.assertEqual(startup.parent_without_prompt_kill(None),jobless)

    def test_03_native_backend_has_no_cli_com_activation_kill_or_late_assign(self):
        source=(ROOT/'tools/p09/crossref_native_startup.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls)&{'Popen','run','system','TerminateJobObject','TerminateProcess','kill',
            'AssignProcessToJobObject','GetActiveObject','Dispatch','CoCreateInstance','sleep'})
        self.assertFalse(any(isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for n in tree.body))
        self.assertNotIn('SetValue',source)
        self.assertNotIn('deadline',ast.unparse(next(n for n in ast.walk(tree)
            if isinstance(n,ast.FunctionDef) and n.name=='resume')))

    def test_04_model_atomic_job_attribute_precedes_creation_and_readback(self):
        state,events=model()
        with patch.object(startup,'hwp_pids',return_value=set()),patch.object(startup,'read_registered_command',
                return_value=[startup.limits.EXECUTABLE,'-Automation']):state.create_suspended()
        self.assertLess(events.index('job_list'),events.index('create_suspended'))
        self.assertLess(events.index('create_suspended'),events.index('pre_run_verify'))
        self.assertEqual(events[-1],'attribute_delete')
        self.assertEqual((state.process,state.thread,state.pid),(1001,1002,91))
        self.assertFalse(state.profile['native_startup_qualified'])
        with self.assertRaisesRegex(ValueError,'NO_START_RETRY'):state.create_suspended()

    def test_05_model_uncertain_creation_retains_handles_and_never_retries(self):
        state,events=model(created=False)
        with patch.object(startup,'hwp_pids',return_value=set()),patch.object(startup,'read_registered_command',
                return_value=[startup.limits.EXECUTABLE,'-Automation']):
            with self.assertRaisesRegex(ValueError,'CREATE_PINNED_NATIVE_SUSPENDED') as caught:
                state.create_suspended()
        self.assertIs(caught.exception.preassigned_native_startup,state)
        self.assertEqual((state.process,state.thread),(1001,1002))
        self.assertEqual(events[-1],'attribute_delete')
        with self.assertRaisesRegex(ValueError,'NO_START_RETRY'):state.create_suspended()
        state.guard.check=lambda:(_ for _ in ()).throw(ValueError('STOP_TEST'))
        with self.assertRaisesRegex(ValueError,'LIVE_NATIVE_RETAIN_HANDLES_AND_JOB'):state.close()
        self.assertEqual((state.process,state.thread,state.owner_job.job),(1001,1002,777))

    def test_06_model_failed_resume_and_freshness_check_latch_without_retry(self):
        for phase in ('freshness','resume'):
            state,events=model();state.profile['pre_run_verified']=True
            if phase=='freshness':state._fresh_image=lambda:(_ for _ in ()).throw(ValueError('STOP_MODEL_PIN'))
            else:state.windows.k.ResumeThread=lambda h:0xffffffff
            with self.assertRaises(ValueError):state.resume()
            self.assertTrue(state.resume_attempted);self.assertFalse(state.profile['resumed'])
            with self.assertRaisesRegex(ValueError,'NO_RESUME_RETRY'):state.resume()

    def test_07_model_other_owner_rejected_before_any_window_or_process_query(self):
        state,events=model();state.profile['resumed']=True;state.pid=91;state.session=1
        state.birth=startup.limits.creation_ticks('2026-10-17T00:00:00.0000001Z')
        identity=dict(process_id=92,session_id=1,created_at_utc=startup.utc_identity(state.birth),
            executable_sha256=startup.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True)
        with self.assertRaisesRegex(ValueError,'BIND_PREASSIGNED_IDENTITY_ONLY'):state.bind_owner(identity,1)
        self.assertTrue(state.bind_attempted);self.assertEqual(events,[])
        with self.assertRaisesRegex(ValueError,'NO_BIND_RETRY'):state.bind_owner(identity,1)

    def test_08_exact_utc_roundtrip_and_preparation_guard_rejection(self):
        ticks=startup.limits.creation_ticks('2026-10-17T12:34:56.1234567Z')
        self.assertEqual(startup.utc_identity(ticks),'2026-10-17T12:34:56.1234567Z')
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_GUARD_REQUIRED'):
            startup.PreassignedNativeStartup(NS(check=lambda:None,preparation_CPU=True),lambda:None)

    def test_09_actual_registration_inventory_and_native_parent_rejection_no_launch(self):
        windows=startup.limits.c.Windows()
        # Only the enclosing original supervisor samples resources. Its kill-on-close
        # readonly parent MUST NOT become an inherited native permission-prompt policy.
        self.assertEqual(startup.read_registered_command(),[startup.limits.EXECUTABLE,'-Automation'])
        observed=startup.host.read_parent_cpu(windows)
        self.assertTrue(observed['job_present'] and observed['query_succeeded'] and observed['flags']&0x2000)
        inventory=startup.hwp_pids(windows,lambda:None)
        image=Path(startup.limits.EXECUTABLE)
        reader=a.AcceptanceReader(image.parent,lambda:None)
        self.assertEqual(reader.pin(image.name)['sha256'],startup.limits.EXECUTABLE_SHA)
        state=startup.PreassignedNativeStartup(NS(windows=windows,check=lambda:None),
            lambda:(_ for _ in ()).throw(ValueError('TEST_FRESH_IMAGE_MUST_NOT_REACH')))
        try:
            with self.assertRaisesRegex(ValueError,'PARENT_LIFECYCLE_NOT_NATIVE_SAFE') as caught:
                state.create_suspended()
            self.assertIs(caught.exception.preassigned_native_startup,state)
            self.assertFalse(state.profile['created']);self.assertIsNone(state.process)
            self.assertIsNone(state.thread)
            reader.finish();self.assertEqual(reader.final_fresh_hashes,1)
        finally:state.close()
        profile=copy.deepcopy(state.profile)
        profile.update(registration_matches_fixed_command=True,hwp_inventory_count=len(inventory),
            inherited_readonly_kill_policy_rejected=True,image_pin=reader.snapshots[image.name],
            installed_image_source_reads=dict(first=1,final=1))
        self.actual.append(profile)

    def test_10_model_handle_birth_membership_then_window_binding_use_same_handle(self):
        state,events=model();state.process=1001;state.pid=91
        state.profile.update(resumed=True);state.parent=parent()
        ticks=startup.limits.creation_ticks('2026-10-17T12:34:56.1234567Z')
        def number(pointer,kind,value):
            ctypes.cast(pointer,ctypes.POINTER(kind)).contents.value=value;return True
        def image(handle,flags,buffer,size):
            self.assertEqual(handle,1001);buffer.value=startup.limits.EXECUTABLE;return True
        def times(handle,birth,exit_time,kernel,user):
            value=ctypes.cast(birth,ctypes.POINTER(startup.w.FILETIME)).contents
            value.dwLowDateTime=ticks & 0xffffffff;value.dwHighDateTime=ticks>>32;return True
        def affinity(handle,allowed,system):
            number(allowed,ctypes.c_size_t,1);number(system,ctypes.c_size_t,65535);return True
        k=state.windows.k;k.GetProcessId=lambda handle:91
        k.QueryFullProcessImageNameW=image;k.GetProcessTimes=times
        k.ProcessIdToSessionId=lambda pid,p:number(p,startup.w.DWORD,1)
        k.GetExitCodeProcess=lambda handle,p:number(p,startup.w.DWORD,259)
        k.IsProcessInJob=lambda handle,job,p:number(p,startup.w.BOOL,True)
        k.GetProcessAffinityMask=affinity;k.GetPriorityClass=lambda handle:0x4000
        state.owner_job.plan=dict(affinity=1,priority=0x4000)
        state.owner_job.profile=dict(limits_readback=dict(verified=True))
        state.owner_job.observe=lambda:events.append('observe_job')
        state.owner_job._observe_identity=lambda handle,identity,window,birth:events.append(
            ('same_handle_window_check',handle,window,birth))
        with patch.object(startup,'hwp_pids',return_value={91}):
            state._handle_identity()
            self.assertEqual(state.birth,ticks)
            identity=dict(process_id=91,session_id=1,created_at_utc=startup.utc_identity(ticks),
                executable_sha256=startup.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True)
            self.assertEqual(state.bind_owner(identity,123),dict(verified=True))
            self.assertTrue(state.profile['owner_bound'])
            self.assertIn(('same_handle_window_check',1001,123,ticks),events)
            self.assertFalse(state.profile['native_startup_qualified'])
            k.GetProcessId=lambda handle:92
            with self.assertRaisesRegex(ValueError,'EXACT_HANDLE_PID'):state._handle_identity()


if __name__=='__main__':
    parent_only=sys.argv[1:]==['--parent-chain-only']
    if sys.argv[1:] and not parent_only:raise SystemExit(2)
    names=unittest.defaultTestLoader.getTestCaseNames(NativeStartupContracts)
    selected=[name for name in names if not parent_only or int(name.split('_')[1]) in (2,9)]
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.TestSuite(NativeStartupContracts(name) for name in selected))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state=('two_parent_chain_startup_contracts_pass_no_native_launch' if parent_only
        else 'ten_preassigned_native_startup_contracts_pass_no_native_launch') if result.wasSuccessful()
        else 'preassigned_native_startup_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),
        declared=result.testsRun,failures=failures,actual_no_launch_profiles=NativeStartupContracts.actual,
        prior_eight_not_reexecuted=parent_only,
        atomic_create_resume_bind_success_is_model_only=True,prior_suites_reexecuted=False,
        actual_Hangul_or_COM=False,native_startup_qualified=False,native_execution_authorized=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
