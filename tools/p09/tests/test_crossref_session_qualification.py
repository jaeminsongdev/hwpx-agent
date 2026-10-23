"""New session protocol/kernel models only. No actual Native/COM/worker launch."""
import ctypes,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_session_qualification as subject
import crossref_session_worker as worker_subject

BIRTH=133000000000000001
SHELL_SHA='a'*64


def message(operation,sequence=1,**extra):
    return json.dumps(dict(schema_version=subject.REQUEST,sequence=sequence,operation=operation,**extra),separators=(',',':'))


def cleanup(closed=True):
    return dict(close_without_dirty_prompt_returned=closed,quit_invoked=closed,reference_release_returned=closed,remaining_owned_process_count=0 if closed else-1)


def worker_identity():
    return dict(process_id=701,session_id=1,created_at_utc=subject.startup.utc_identity(BIRTH),executable_sha256=SHELL_SHA)


class ModeledSession:
    def __init__(self):
        self.alive=False;self.failure=None;self.events=[];self.terminal=False
        self.windows=subject.startup.limits.c.Windows.__new__(subject.startup.limits.c.Windows)
        self.windows.k=NS(WaitForSingleObject=lambda h,m:258 if self.alive else 0)
        self.windows.accounting=lambda job:dict(active_processes=1 if self.alive else 0)
        self.guard=NS(check=Mock(),windows=self.windows)
        self.worker=subject.owned.OwnedHostProcess.__new__(subject.owned.OwnedHostProcess)
        self.worker.windows=self.windows;self.worker.process=NS(poll=lambda:0 if self.terminal else None)
        self.patchers=[patch.object(subject,'WorkerKernelLease',side_effect=self.lease),
            patch.object(subject.startup,'parent_without_prompt_kill',return_value={'job_present':False}),
            patch.object(subject.startup,'PreassignedNativeStartup',side_effect=self.factory)]
    def __enter__(self):
        self.mocks=[p.start()for p in self.patchers]
        self.protocol=subject.SessionQualifier(self.guard,self.worker,lambda:None,lambda:None);return self
    def __exit__(self,*args):
        for p in reversed(self.patchers):p.stop()
    def lease(self,*args):
        def observe():
            if self.failure=='lease':raise ValueError('XREF_SESSION_QUALIFICATION_MODEL_LEASE_FAILED')
        def close():
            if not self.terminal:raise ValueError('XREF_SESSION_QUALIFICATION_LIVE_WORKER_LEASE_RETAINED')
            self.leased.closed=True
        self.leased=NS(observe=observe,close=close,closed=False);observe();return self.leased
    def factory(self,*args):
        env=self
        class Backend:
            def __init__(self):
                self.pid=1001;self.session=1;self.birth=BIRTH;self.process=987;self.owner_job=NS(job=543);self.closed=False
                self.profile=dict(pre_run_verified=False,assigned_before_initial_thread=False,resumed=False,owner_bound=False,cleanup_confirmed=False)
            def create_suspended(self):
                env.events.append('create');env.alive=True
                if env.failure=='create':raise ValueError('XREF_NATIVE_STARTUP_MODEL_CREATE_UNCERTAIN')
                self.profile.update(pre_run_verified=True,assigned_before_initial_thread=True)
            def resume(self):
                env.events.append('resume')
                if env.failure=='resume':raise ValueError('XREF_NATIVE_STARTUP_MODEL_RESUME_UNCERTAIN')
                self.profile['resumed']=True
            def bind_owner(self,identity,window):
                env.events.append('bind');ticks=subject.startup.limits.validate_identity(identity,window)
                subject.require(identity['process_id']==self.pid and identity['session_id']==self.session and ticks==self.birth,'EXACT_MODEL_OWNER')
                self.profile['owner_bound']=True
            def close(self):
                env.events.append('close');subject.require(not env.alive,'LIVE_MODEL_NATIVE')
                self.closed=True;self.profile['cleanup_confirmed']=True
        self.backend=Backend();return self.backend
    def send(self,op,**extra):
        return json.loads(self.protocol.respond(message(op,self.protocol.sequence+1,**extra)))
    def ready(self):return self.send('ready',worker_identity=worker_identity())
    def admit(self):
        return self.send('admit_owner',identity=dict(process_id=1001,session_id=1,created_at_utc=subject.startup.utc_identity(BIRTH),
            executable_sha256=subject.startup.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True),window_handle=123)


def kernel_model():
    windows=subject.startup.limits.c.Windows.__new__(subject.startup.limits.c.Windows);k=Mock();windows.k=k
    k.OpenProcess.return_value=987;k.GetProcessId.return_value=701;k.WaitForSingleObject.return_value=258;k.GetCurrentProcessId.return_value=600
    k.GetPriorityClass.return_value=0x4000;k.CloseHandle.return_value=True
    def times(handle,birth,exit,kernel,user):
        birth._obj.dwLowDateTime=BIRTH&0xffffffff;birth._obj.dwHighDateTime=BIRTH>>32;return True
    def exit_code(handle,code):code._obj.value=259;return True
    def session(pid,output):output._obj.value=1;return True
    def member(handle,job,output):output._obj.value=1;return True
    def image(handle,flags,output,size):output.value=subject.owned.SHELL;return True
    def affinity(handle,allowed,system):allowed._obj.value=4;system._obj.value=0xffff;return True
    k.GetProcessTimes.side_effect=times;k.GetExitCodeProcess.side_effect=exit_code;k.ProcessIdToSessionId.side_effect=session
    k.IsProcessInJob.side_effect=member;k.QueryFullProcessImageNameW.side_effect=image;k.GetProcessAffinityMask.side_effect=affinity
    worker=subject.owned.OwnedHostProcess.__new__(subject.owned.OwnedHostProcess)
    worker.closed=False;worker.windows=windows;worker.job=543;worker.process=NS(poll=lambda:None)
    worker.profile=dict(role='private_session_qualification_candidate',qualification_target_pinned=True,
        host_worker_one_percent_installed=True,bootstrap_assigned=True,bootstrap_limits_readback=True,readonly_signal_written=True)
    worker.plan=dict(affinity=4,priority=0x4000);worker.observe=Mock();worker.readback=Mock()
    return worker,lambda:dict(path='powershell.exe',sha256=SHELL_SHA,bytes=1000)


class SessionContracts(unittest.TestCase):
    def test_01_parent_denial_precedes_any_native_constructor(self):
        with ModeledSession()as m:
            m.mocks[1].side_effect=ValueError('XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            out=m.ready();self.assertFalse(out['acknowledged']);m.mocks[2].assert_not_called();self.assertIsNone(m.protocol.current)
            self.assertTrue(m.send('failed',error_code='P09_XREF_BIND_SESSION_WORKER_FAILED',cleanup=cleanup(False))['acknowledged'])
    def test_02_complete_modeled_lifecycle_is_not_native_or_gate_authority(self):
        with ModeledSession()as m:
            out=m.ready();self.assertTrue(out['acknowledged']);self.assertIsNotNone(out['owner_descriptor'])
            self.assertTrue(m.admit()['acknowledged']);m.alive=False;self.assertTrue(m.send('closed',cleanup=cleanup())['acknowledged'])
            summary=m.protocol.summary();self.assertTrue(summary['lifecycle_candidate_observed']);self.assertFalse(summary['native_startup_qualified'])
            self.assertFalse(summary['fixed_eight_executed']);self.assertEqual(m.events,['create','resume','bind','close'])
    def test_03_closed_before_admission_latches_without_closing_live_native(self):
        with ModeledSession()as m:
            m.ready();self.assertFalse(m.send('closed',cleanup=cleanup())['acknowledged']);self.assertNotIn('close',m.events)
    def test_04_wrong_canonical_tick_is_not_bound(self):
        with ModeledSession()as m:
            m.ready();identity=dict(process_id=1001,session_id=1,created_at_utc=subject.startup.utc_identity(BIRTH+1),
                executable_sha256=subject.startup.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True)
            self.assertFalse(m.send('admit_owner',identity=identity,window_handle=123)['acknowledged']);self.assertFalse(m.backend.profile['owner_bound'])
    def test_05_create_failure_retains_same_backend_no_resume(self):
        with ModeledSession()as m:
            m.failure='create';self.assertFalse(m.ready()['acknowledged']);self.assertIs(m.protocol.current,m.backend);self.assertEqual(m.events,['create'])
    def test_06_resume_failure_retains_same_backend_no_restart(self):
        with ModeledSession()as m:
            m.failure='resume';self.assertFalse(m.ready()['acknowledged']);self.assertIs(m.protocol.current,m.backend)
            self.assertFalse(m.ready()['acknowledged']);self.assertEqual(m.events,['create','resume'])
    def test_07_second_ready_cannot_replace_owner(self):
        with ModeledSession()as m:m.ready();self.assertFalse(m.ready()['acknowledged']);self.assertEqual(m.events,['create','resume'])
    def test_08_boolean_and_wrong_sequence_rejected_before_creation(self):
        for sequence in(True,2):
            with ModeledSession()as m:
                out=json.loads(m.protocol.respond(message('ready',sequence,worker_identity=worker_identity())))
                self.assertFalse(out['acknowledged']);m.mocks[2].assert_not_called()
    def test_09_early_failed_finish_never_starts_native(self):
        with ModeledSession()as m:
            self.assertTrue(m.send('failed',error_code='P09_XREF_BIND_TEST_FAILURE',cleanup=cleanup(False))['acknowledged']);m.mocks[2].assert_not_called()
    def test_10_false_closed_claims_reject_before_retirement(self):
        with ModeledSession()as m:
            m.ready();m.admit();self.assertFalse(m.send('closed',cleanup=cleanup(False))['acknowledged']);self.assertNotIn('close',m.events)
    def test_11_live_native_despite_worker_closed_keeps_job_and_handles(self):
        with ModeledSession()as m:
            m.ready();m.admit();self.assertFalse(m.send('closed',cleanup=cleanup())['acknowledged']);self.assertFalse(m.protocol.lifecycle_candidate)
            with self.assertRaisesRegex(ValueError,'LIVE_NATIVE_RETAIN_HANDLES_AND_JOB'):m.protocol.close()
            self.assertIs(m.protocol.current,m.backend);self.assertFalse(m.backend.closed)
    def test_12_failed_finish_can_retire_exited_owner_without_candidate(self):
        with ModeledSession()as m:
            m.ready();m.alive=False;self.assertTrue(m.send('failed',error_code='P09_XREF_BIND_TEST_FAILURE',cleanup=cleanup(False))['acknowledged'])
            self.assertTrue(m.backend.closed);self.assertFalse(m.protocol.lifecycle_candidate)
    def test_13_preparation_guard_denied_before_worker_or_native(self):
        guard=NS(check=Mock(),windows=subject.startup.limits.c.Windows.__new__(subject.startup.limits.c.Windows),preparation_CPU={})
        with self.assertRaises(ValueError):subject.SessionQualifier(guard,None,lambda:None,lambda:None)
    def test_14_extra_keys_paths_and_duplicate_json_rejected(self):
        for extra in({'approved':True},{'path':'PRIVATE'}):
            value=json.loads(message('ready',worker_identity=worker_identity()));value.update(extra)
            with self.assertRaises(ValueError):subject.decode(json.dumps(value))
        with self.assertRaises(ValueError):subject.decode(message('ready',worker_identity=worker_identity()).replace('"sequence":1','"sequence":1,"sequence":1'))
    def test_15_numeric_cleanup_boolean_not_accepted(self):
        value=cleanup();value['remaining_owned_process_count']=False
        with self.assertRaises(ValueError):subject.decode(message('closed',cleanup=value))
    def test_16_worker_lease_failure_precedes_native_constructor(self):
        with ModeledSession()as m:
            m.failure='lease';self.assertFalse(m.ready()['acknowledged']);m.mocks[2].assert_not_called()
    def test_17_worker_query_handle_retained_until_worker_terminal(self):
        with ModeledSession()as m:
            m.ready();m.alive=False
            with self.assertRaisesRegex(ValueError,'LIVE_WORKER_LEASE_RETAINED'):m.protocol.close()
            m.terminal=True;m.protocol.close();self.assertTrue(m.leased.closed)
    def test_18_worker_command_is_closed_and_source_pinned(self):
        paths=[];reader=NS(root=subject.owned.c.ROOT,snapshots={subject.owned.BOOTSTRAP:{'sha256':subject.owned.BOOTSTRAP_SHA}},pin=paths.append)
        command=worker_subject.command(reader);args=json.loads(command[-1]);self.assertEqual(paths,list(worker_subject.SOURCES));self.assertEqual(args[-1],'-QualifySessionOnly')
        self.assertNotIn('-ExecuteNative',args)
    def test_19_session_worker_refuses_preparation_guard(self):
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_GUARD_REQUIRED'):worker_subject.SessionWorker(NS(check=Mock(),preparation_CPU={},windows=None))
    def test_20_kernel_lease_checks_same_job_and_query_only_rights(self):
        worker,pin=kernel_model();lease=subject.WorkerKernelLease(worker,worker_identity(),pin)
        worker.windows.k.OpenProcess.assert_called_once_with(0x00101000,False,701);self.assertTrue(lease.observe()['original_one_percent_job_member'])
        worker.process.poll=lambda:0;lease.close();worker.windows.k.CloseHandle.assert_called_once_with(987)
    def test_21_wrong_kernel_birth_closes_query_handle(self):
        worker,pin=kernel_model();identity=worker_identity();identity['created_at_utc']=subject.startup.utc_identity(BIRTH+1)
        with self.assertRaises(ValueError):subject.WorkerKernelLease(worker,identity,pin)
        worker.windows.k.CloseHandle.assert_called_once_with(987)
    def test_22_wrong_worker_role_rejects_before_open(self):
        worker,pin=kernel_model();worker.profile['role']='closed_preassigned_preparation_not_native'
        with self.assertRaises(ValueError):subject.WorkerKernelLease(worker,worker_identity(),pin)
        worker.windows.k.OpenProcess.assert_not_called()
    def test_23_other_session_is_not_current_worker(self):
        worker,pin=kernel_model();identity=worker_identity();identity['session_id']=2
        with self.assertRaises(ValueError):subject.WorkerKernelLease(worker,identity,pin)
    def test_24_fresh_executable_drift_closes_query_handle(self):
        worker,pin=kernel_model()
        with self.assertRaises(ValueError):subject.WorkerKernelLease(worker,worker_identity(),lambda:dict(path='powershell.exe',sha256='b'*64,bytes=1000))
        worker.windows.k.CloseHandle.assert_called_once_with(987)
    def test_25_live_worker_query_lease_cannot_be_abandoned(self):
        worker,pin=kernel_model();lease=subject.WorkerKernelLease(worker,worker_identity(),pin)
        with self.assertRaisesRegex(ValueError,'LIVE_WORKER_LEASE_RETAINED'):lease.close()
        self.assertEqual(lease.handle,987);worker.windows.k.CloseHandle.assert_not_called()
