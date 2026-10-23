"""Ordered protocol, actual readonly x86 pipes and core/ports first-step denial."""
import io
import json
import os
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
import crossref_native_host_channel as host


def wire(sequence, case_index=1, operation='checkpoint', **extra):
    return json.dumps(dict(schema_version=host.REQUEST,sequence=sequence,case_index=case_index,
        operation=operation,**extra),separators=(',',':'))


def identity():
    return dict(process_id=10,session_id=1,created_at_utc='2026-10-17T00:00:00.0000000Z',
        executable_sha256=host.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True)


def quiet_protocol():
    return host.HostProtocol(lambda *a:None,lambda *a:None,lambda *a:None)


def actual_readonly_child(pipe_denial=False, wrapper_only=False):
    """Only this immutable-scope readonly test driver; never native prompt work.

    Two bounded drain threads perform pipe IO only, not resource sampling. The
    outer original owned-Job supervisor remains the sole resource sampler.
    """
    shell=r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
    driver=ROOT/'implementation/p09/tools/test-crossref-host-channel.ps1'
    args=[shell,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(driver)]
    if pipe_denial:args.append('-PortDenial')
    if wrapper_only:args.append('-WrapperOnly')
    process=subprocess.Popen(args,cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding='utf-8',errors='strict',creationflags=subprocess.CREATE_NO_WINDOW)
    events=queue.Queue(maxsize=8);failures=[];stderr=bytearray();stdout_size=0
    def read_out():
        try:
            while True:
                line=process.stdout.readline(4097)
                if not line:break
                if len(line.encode('utf-8'))>4096 or not line.endswith('\n'):
                    raise ValueError('READONLY_TEST_PIPE_LINE_LIMIT')
                events.put(line.rstrip('\r\n'),timeout=1)
        except (ValueError,OSError,UnicodeError,queue.Full):
            failures.append('READONLY_TEST_STDOUT_FAILED')
        finally:
            try:events.put(None,timeout=1)
            except queue.Full:failures.append('READONLY_TEST_EVENT_QUEUE_FULL')
    def read_err():
        try:
            while True:
                chunk=process.stderr.read(1024)
                if not chunk:break
                stderr.extend(chunk.encode('utf-8'))
                if len(stderr)>4096:raise ValueError('READONLY_TEST_STDERR_LIMIT')
        except (ValueError,OSError,UnicodeError):
            failures.append('READONLY_TEST_STDERR_FAILED')
    threads=[threading.Thread(target=read_out,daemon=True),threading.Thread(target=read_err,daemon=True)]
    for thread in threads:thread.start()
    observed=[];finished=[]
    def deny(*args):
        observed.append(args)
        raise ValueError('STOP_TEST_PARENT_DENIED')
    protocol=host.HostProtocol(deny,lambda *a:(_ for _ in ()).throw(ValueError('STOP_TEST_NO_ADMISSION')),
        lambda *args:finished.append(args))
    result=None;cleanup=False
    try:
        deadline=time.monotonic()+45  # THIS readonly test only; never a native prompt timer.
        while True:
            if time.monotonic()>=deadline:raise ValueError('READONLY_TEST_PIPE_DEADLINE')
            if failures:raise ValueError(failures[0])
            try:line=events.get(timeout=.5)
            except queue.Empty:continue
            if line is None:break
            stdout_size+=len(line.encode('utf-8'))
            if stdout_size>32768:raise ValueError('READONLY_TEST_STDOUT_LIMIT')
            packet=json.loads(line)
            if packet.get('schema_version')==host.REQUEST:
                if not pipe_denial:raise ValueError('READONLY_TEST_UNEXPECTED_REQUEST')
                answer=protocol.respond(line)
                process.stdin.write(answer+'\n');process.stdin.flush()
            else:
                if result is not None:raise ValueError('READONLY_TEST_DUPLICATE_RESULT')
                result=packet
        process.stdin.close()
        code=process.wait(timeout=2)
        if code or stderr or failures or result is None:raise ValueError('READONLY_TEST_CHILD_FAILED_NO_RAW_VALUES')
        return dict(exit_code=code,result=result,host=protocol.summary(),
            checkpoint_callbacks=len(observed),finish_callbacks=len(finished),stdout_bytes=stdout_size,
            stderr_bytes=len(stderr),readonly_child_cleanup=True)
    finally:
        # Killing is permitted only for this fixed readonly test, never native work.
        if process.poll() is None:process.kill()
        process.wait(timeout=2)
        for stream in (process.stdin,process.stdout,process.stderr):
            if not stream.closed:stream.close()
        for thread in threads:thread.join(timeout=2)
        cleanup=process.poll() is not None and not any(t.is_alive() for t in threads)
        if not cleanup:raise ValueError('READONLY_TEST_CHILD_CLEANUP_FAILED')


class HostChannelContracts(unittest.TestCase):
    actual=[]

    def test_01_fixed_eight_cases_and_all_checkpoint_admission_frames(self):
        calls=[]
        protocol=host.HostProtocol(lambda *a:calls.append(('checkpoint',a)),
            lambda *a:calls.append(('admit_owner',a)),lambda *a:calls.append(('finish',a)))
        n=0
        for case in range(1,9):
            for operation,step in host.FLOW:
                n+=1
                extra=dict(step=step) if operation=='checkpoint' else dict(identity=identity(),window_handle=1)
                reply=json.loads(protocol.respond(wire(n,case,operation,**extra)))
                self.assertTrue(reply['acknowledged'])
            n+=1
            self.assertTrue(json.loads(protocol.respond(wire(n,case,'finish',case_status='returned')))['acknowledged'])
        self.assertEqual(n,152)
        self.assertEqual(len(calls),152)
        self.assertTrue(protocol.summary()['all_eight_callback_cases_returned'])
        self.assertFalse(protocol.summary()['native_execution_attested'])
        self.assertEqual(protocol.summary()['accepted_count_delta'],0)

    def test_02_wrong_order_cannot_skip_owner_admission(self):
        protocol=quiet_protocol()
        for n,step in enumerate(('prepare_slot','create_save_session'),1):
            self.assertTrue(json.loads(protocol.respond(wire(n,step=step)))['acknowledged'])
        response=json.loads(protocol.respond(wire(3,step='source_open')))
        self.assertFalse(response['acknowledged'])
        self.assertEqual(response['error_code'],'XREF_HOST_FIXED_OPERATION_ORDER')
        self.assertTrue(protocol.stopped)

    def test_03_duplicate_unknown_coerced_and_oversized_requests_rejected(self):
        good=wire(1,step='prepare_slot')
        values=[good.replace('"sequence":1','"sequence":1,"sequence":1'),
            good.replace('"case_index":1','"case_index":true'),
            good.replace('"sequence":1','"sequence":true'),
            good.replace('"operation":"checkpoint"','"operation":"execute"'),
            good[:-1]+',"command":"private synthetic"}', 'x'*4097,'{}','null',good+'\n']
        for bad in values:
            protocol=quiet_protocol();result=json.loads(protocol.respond(bad))
            self.assertFalse(result['acknowledged'])
            self.assertTrue(protocol.stopped)
            self.assertNotIn('private synthetic',json.dumps(result))
        protocol=quiet_protocol();protocol.respond(good)
        self.assertFalse(json.loads(protocol.respond(good))['acknowledged'])

    def test_04_failed_checkpoint_stays_stopped_but_finish_cleans_once(self):
        cleaned=[]
        def stop(*args):raise ValueError('STOP_TEST_NATIVE_CHECKPOINT')
        protocol=host.HostProtocol(stop,lambda *a:None,lambda *a:cleaned.append(a))
        self.assertFalse(json.loads(protocol.respond(wire(1,step='prepare_slot')))['acknowledged'])
        first=protocol.primary_error
        self.assertFalse(json.loads(protocol.respond(wire(2,step='prepare_slot')))['acknowledged'])
        self.assertTrue(json.loads(protocol.respond(wire(3,operation='finish',case_status='failed')))['acknowledged'])
        self.assertEqual(cleaned,[(1,'failed')])
        self.assertFalse(json.loads(protocol.respond(wire(4,operation='finish',case_status='failed')))['acknowledged'])
        self.assertEqual(protocol.primary_error,first)
        self.assertEqual(len(cleaned),1)

    def test_05_primary_and_cleanup_failure_stay_separate_and_redacted(self):
        def stop(*a):raise ValueError('private synthetic checkpoint')
        def cleanup(*a):raise ValueError('STOP_TEST_CLEANUP')
        protocol=host.HostProtocol(stop,lambda *a:None,cleanup)
        protocol.respond(wire(1,step='prepare_slot'))
        protocol.respond(wire(2,operation='finish',case_status='failed'))
        summary=protocol.summary()
        self.assertEqual(summary['primary_error'],'XREF_HOST_CALLBACK_FAILED_NO_RAW_VALUES')
        self.assertEqual(summary['cleanup_error'],'STOP_TEST_CLEANUP')
        self.assertNotIn('private synthetic',json.dumps(summary))

    def test_06_worker_failure_and_premature_success_never_start_next_case(self):
        cleaned=[];protocol=host.HostProtocol(lambda *a:None,lambda *a:None,lambda *a:cleaned.append(a))
        self.assertTrue(json.loads(protocol.respond(wire(1,operation='finish',case_status='failed')))['acknowledged'])
        self.assertEqual(cleaned,[(1,'failed')])
        self.assertFalse(json.loads(protocol.respond(wire(2,2,step='prepare_slot')))['acknowledged'])
        protocol=quiet_protocol()
        self.assertFalse(json.loads(protocol.respond(wire(1,operation='finish',case_status='returned')))['acknowledged'])

    def test_07_callback_return_is_not_native_or_cleanup_authority(self):
        protocol=host.HostProtocol(lambda *a:dict(native_execution_authorized=True),lambda *a:True,lambda *a:True)
        reply=json.loads(protocol.respond(wire(1,step='prepare_slot')))
        self.assertTrue(reply['acknowledged'])
        self.assertFalse(reply['native_execution_authorized'] or reply['p09_complete'])
        self.assertFalse(protocol.summary()['native_cleanup_qualified'])

    def test_08_resource_adapter_rejects_prep_guard_and_cleans_without_sampler(self):
        with self.assertRaisesRegex(ValueError,'NO_PREPARATION_ONLY_NATIVE_GUARD'):
            host.NativeResourceScope(NS(check=lambda:None,preparation_CPU=object()),lambda:None)
        scope=host.NativeResourceScope.__new__(host.NativeResourceScope)
        closed=[];scope.profiles=[];scope.current_case=1
        scope.guard=NS(check=lambda:(_ for _ in ()).throw(ValueError('STOP_TEST')))
        scope.current=NS(close=lambda:closed.append(True),profile=dict(cleanup_confirmed=True))
        scope.finish(1,'failed')
        self.assertEqual(closed,[True])
        self.assertIsNone(scope.current)
        scope.finish(2,'failed')  # A constructor failure before the next checkpoint has nothing to retire.

    def test_09_actual_x86_response_parser_contracts(self):
        value=actual_readonly_child()
        self.assertEqual(value['result']['state'],'two_ps_channel_contracts_pass_not_native')
        self.assertEqual(value['result']['passed'],2)
        self.assertFalse(value['result']['actual_Hangul_or_COM'])
        self.actual.append(value)

    def test_10_actual_x86_pipe_core_ports_host_denial_and_cleanup(self):
        value=actual_readonly_child(pipe_denial=True)
        self.assertEqual(value['result']['state'],'actual_x86_pipe_ports_denial_and_finish_pass_not_native')
        self.assertEqual(value['checkpoint_callbacks'],1)
        self.assertEqual(value['finish_callbacks'],1)
        self.assertEqual(value['host']['sequence'],2)
        self.assertEqual(value['host']['primary_error'],'STOP_TEST_PARENT_DENIED')
        self.assertFalse(value['result']['native_directory_created'] or value['result']['actual_Hangul_or_COM'])
        self.actual.append(value)


    def test_11_actual_product_wrapper_with_fixed_in_memory_denial(self):
        value=actual_readonly_child(wrapper_only=True)
        self.assertEqual(value['result']['state'],'one_actual_host_bound_wrapper_denial_contract_pass_not_native')
        self.assertTrue(value['result']['fixed_denial_not_external_input'])
        self.assertFalse(value['result']['native_directory_created'] or value['result']['actual_Hangul_or_COM'])
        self.actual.append(value)


if __name__=='__main__':
    wrapper_only=sys.argv[1:]==['--wrapper-only']
    if sys.argv[1:] and not wrapper_only:raise SystemExit(2)
    suite=unittest.TestSuite([HostChannelContracts('test_11_actual_product_wrapper_with_fixed_in_memory_denial')]) if wrapper_only else unittest.defaultTestLoader.loadTestsFromTestCase(HostChannelContracts)
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state=('one_host_bound_wrapper_contract_pass_not_native' if wrapper_only else 'eleven_host_channel_contracts_pass_not_native') if result.wasSuccessful()
        else 'host_channel_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_readonly_children=HostChannelContracts.actual,prior_ten_not_reexecuted=wrapper_only,
        actual_Hangul_or_COM=False,native_execution_authorized=False,host_one_percent_job_installed=False,
        complete_native_guard_integration_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
