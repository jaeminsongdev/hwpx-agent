"""New dual-clock contracts, including an actual held self-process/parent query.

Native success objects below are in-memory models only. The actual child is a
closed x86 PowerShell self-inspector in the enclosing original readonly Job.
"""
import ast
import copy
import ctypes
from ctypes import wintypes as w
import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import crossref_dual_owner_identity as dual

SHELL=r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
DRIVER='implementation/p09/tools/test-crossref-dual-owner-identity.ps1'
PROBE='implementation/p09/tools/inspect-crossref-dual-identity.ps1'


def model_record():
    compat=dict(process_id=135,session_id=1,created_at_utc='2026-10-17T00:00:00.0000000Z',
        executable_sha256=dual.native.EXECUTABLE_SHA,window_handle_binds_exact_process=True)
    kernel=dict(compat,created_at_utc='2026-10-17T00:00:00.0000006Z')
    return dict(schema_version='hwpx-agent.private.crossref-dual-owner-identity/v1',
        compatibility_kind='original_p58_identity',compatibility_identity=compat,kernel_identity=kernel,
        kernel_creation_filetime_100ns=str(dual.native.creation_ticks(kernel['created_at_utc'])),
        kernel_process_image=dual.native.EXECUTABLE,kernel_window_verified=True,
        kernel_before_after_same_handle_equal=True,compatibility_fresh_check_returned=True,
        kernel_creation_not_derived_from_cim=True,native_provenance_qualified=False,
        native_execution_authorized=False,p09_complete=False)


class DualClockContracts(unittest.TestCase):
    actual=[]

    def test_01_original_cim_preserved_canonical_not_rounded_or_time_tolerated(self):
        value=model_record();original=copy.deepcopy(value)
        result=dual.decode_record(value)
        self.assertEqual(value,original)
        self.assertEqual(result['kernel_identity']['created_at_utc'],'2026-10-17T00:00:00.0000006Z')
        self.assertEqual(result['compatibility_identity']['created_at_utc'],'2026-10-17T00:00:00.0000000Z')
        self.assertFalse(result['physical_native_admission_qualified'])

    def test_02_single_kernel_tick_mismatch_rejected(self):
        for mode in ('utc','filetime'):
            row=model_record()
            if mode=='utc':row['kernel_identity']['created_at_utc']='2026-10-17T00:00:00.0000007Z'
            else:row['kernel_creation_filetime_100ns']=str(int(row['kernel_creation_filetime_100ns'])+1)
            with self.assertRaisesRegex(ValueError,'EXACT_KERNEL_CLOCK_NO_TOLERANCE'):dual.decode_record(row)

    def test_03_nonclock_drift_false_observation_or_promotion_rejected(self):
        for key in ('process_id','session_id'):
            row=model_record();row['kernel_identity'][key]+=1
            with self.assertRaises(ValueError):dual.decode_record(row)
        for key in ('kernel_before_after_same_handle_equal','compatibility_fresh_check_returned',
                'kernel_creation_not_derived_from_cim'):
            row=model_record();row[key]=False
            with self.assertRaises(ValueError):dual.decode_record(row)
        for key in ('native_execution_authorized','native_provenance_qualified','p09_complete'):
            row=model_record();row[key]=True
            with self.assertRaises(ValueError):dual.decode_record(row)

    def test_04_original_exact_native_verifier_still_rejects_compat_and_one_tick_drift_model(self):
        row=model_record();canonical=dual.canonical_native_candidate(row)
        ticks=dual.native.creation_ticks(canonical['created_at_utc'])
        state=dual.native.NativeOwnerJob.__new__(dual.native.NativeOwnerJob)
        def number(pointer,kind,value):
            ctypes.cast(pointer,ctypes.POINTER(kind)).contents.value=value;return True
        def image(handle,flags,buffer,size):buffer.value=dual.native.EXECUTABLE;return True
        def times(handle,birth,exit_time,kernel,user):
            value=ctypes.cast(birth,ctypes.POINTER(w.FILETIME)).contents
            value.dwLowDateTime=ticks & 0xffffffff;value.dwHighDateTime=ticks>>32;return True
        state.k=NS(QueryFullProcessImageNameW=image,GetProcessTimes=times,
            GetExitCodeProcess=lambda h,p:number(p,w.DWORD,259),ProcessIdToSessionId=lambda pid,p:number(p,w.DWORD,1))
        state.u=NS(GetWindowThreadProcessId=lambda hwnd,p:number(p,w.DWORD,135))
        state._observe_identity(1001,canonical,123,ticks)
        for identity in (row['compatibility_identity'],dict(canonical,created_at_utc='2026-10-17T00:00:00.0000007Z')):
            with self.assertRaisesRegex(ValueError,'PROCESS_IDENTITY'):
                state._observe_identity(1001,identity,123,dual.native.creation_ticks(identity['created_at_utc']))

    def test_05_ps_source_keeps_original_fresh_check_between_same_handle_queries(self):
        text=(ROOT/'implementation/p09/tools/crossref-dual-owner-identity.ps1').read_text(encoding='utf-8')
        observe=text[text.index('function Observe-P09XrefDualOwnedIdentity'):text.index('function Invoke-P09XrefCanonicalHostAdmission')]
        self.assertLess(observe.index('$before=$lease.ReadOwnedWindow'),observe.index('Test-P58Owner $Owner'))
        self.assertLess(observe.index('Test-P58Owner $Owner'),observe.index('$after=$lease.ReadOwnedWindow'))
        self.assertIn('Assert-P09XrefOriginalOwnerFunction',observe)
        self.assertIn('$lease.Dispose()',observe)
        self.assertIn('identity=$observed.kernel_identity;window=$Owner.window',text)
        for bad in ('-ComObject ', 'CoCreateInstance','GetActiveObject','CreateProcess','TerminateProcess',
                'FinalReleaseComObject','SaveAs(','.Quit('):self.assertNotIn(bad,text)
        tree=ast.parse((ROOT/'tools/p09/crossref_dual_owner_identity.py').read_text(encoding='utf-8'))
        self.assertFalse(any(isinstance(n,ast.If) and '__name__' in ast.unparse(n.test) for n in tree.body))

    def test_06_actual_powershell_pure_record_models_no_kernel_or_com(self):
        run=subprocess.run([SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(ROOT/DRIVER),'-ModelsOnly'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        self.assertEqual(run.returncode,0,'P09_DUAL_MODEL_DRIVER_FAILED')
        self.assertEqual(run.stderr,'','P09_DUAL_MODEL_DRIVER_STDERR')
        result=json.loads(run.stdout)
        self.assertEqual((result['passed'],result['failed']),(2,0));self.assertTrue(result['model_only'])
        self.assertEqual(dual.canonical_native_candidate(result['model_record']),model_record()['kernel_identity'])

    def test_07_actual_self_peer_kernel_birth_matches_independent_parent_handle_exactly(self):
        process=subprocess.Popen([SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(ROOT/PROBE),'-InspectOnly'],
            cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        replies=queue.Queue(1);tails={};threads=[];handle=None
        def read_stdout():
            line=process.stdout.readline(4097);replies.put(line)
            tails['stdout']=process.stdout.read(4097)
        def read_stderr():tails['stderr']=process.stderr.read(4097)
        for target in (read_stdout,read_stderr):
            thread=threading.Thread(target=target,daemon=True);thread.start();threads.append(thread)
        try:
            raw=replies.get(timeout=40)
            self.assertTrue(raw.endswith(b'\n') and 0<len(raw)<=4096,'P09_DUAL_ACTUAL_RECORD_BOUNDARY')
            record=json.loads(raw);decoded=dual.decode_record(record)
            self.assertEqual(record['compatibility_kind'],'current_process_cim_only')
            self.assertEqual(decoded['kernel_identity']['process_id'],process.pid)
            self.assertFalse(record['kernel_window_verified'])
            with self.assertRaisesRegex(ValueError,'OWN_PROCESS_INSPECTION_CANNOT_BE_NATIVE_CANDIDATE'):
                dual.canonical_native_candidate(record)
            windows=dual.native.c.Windows();k=windows.k
            for name,args,result in (
                ('GetProcessId',[w.HANDLE],w.DWORD),
                ('GetProcessTimes',[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4,w.BOOL),
                ('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD),
                ('ProcessIdToSessionId',[w.DWORD,ctypes.POINTER(w.DWORD)],w.BOOL)):
                fn=getattr(k,name);fn.argtypes,fn.restype=args,result
            handle=k.OpenProcess(0x00101000,False,process.pid)
            self.assertTrue(handle);self.assertEqual(k.GetProcessId(handle),process.pid)
            self.assertEqual(k.WaitForSingleObject(handle,0),258)
            image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
            self.assertTrue(k.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(size)))
            self.assertEqual(image.value.casefold(),SHELL.casefold())
            points=[w.FILETIME() for _ in range(4)]
            self.assertTrue(k.GetProcessTimes(handle,*(ctypes.byref(t) for t in points)))
            actual=points[0].dwLowDateTime | points[0].dwHighDateTime<<32
            session=w.DWORD();self.assertTrue(k.ProcessIdToSessionId(process.pid,ctypes.byref(session)))
            self.assertEqual(actual,decoded['kernel_filetime_100ns'])
            self.assertEqual(session.value,decoded['kernel_identity']['session_id'])
            self.assertEqual(k.WaitForSingleObject(handle,0),258)
            process.stdin.write(b'P09_XREF_DUAL_INSPECTION_DONE\n');process.stdin.flush();process.stdin.close()
            self.assertEqual(process.wait(timeout=10),0)
            for thread in threads:thread.join(2)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(tails,{'stdout':b'','stderr':b''})
            self.actual.append(dict(state='actual_self_dual_record_parent_exact_handle_verified_not_hancom',
                original_cim_identity=decoded['compatibility_identity'],canonical_kernel_identity=decoded['kernel_identity'],
                kernel_filetime_100ns=str(actual),cim_kernel_exact_equal=(actual==dual.native.creation_ticks(decoded['compatibility_identity']['created_at_utc'])),
                parent_independent_kernel_exact=True,self_native_candidate_rejected=True,exit_code=0,
                io_threads_joined=True,actual_Hangul_or_COM=False,native_execution_authorized=False,
                native_provenance_qualified=False,p09_complete=False))
        finally:
            if not process.stdin.closed:process.stdin.close() # EOF gracefully releases a denied inspection.
            process.wait(timeout=10)
            for thread in threads:thread.join(2)
            for stream in (process.stdout,process.stderr):stream.close()
            if handle is not None:self.assertTrue(k.CloseHandle(handle))


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(DualClockContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='seven_dual_identity_contracts_and_two_ps_models_pass_not_native' if result.wasSuccessful()
        else 'dual_identity_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_observations=DualClockContracts.actual,ps_pure_models=2,prior_suites_reexecuted=False,
        actual_Hangul_or_COM=False,native_execution_authorized=False,native_provenance_qualified=False,
        complete_native_guard_integration_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
