"""Pure transport regressions. Fake handles/pipes only; no COM, subprocess or Native."""
import ast,hashlib,io,json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import accept_case112_current_epoch as epoch
import crossref_native_worker_io as old
import crossref_native_worker_io603 as subject

SCHEMA='hwpx-agent.private.crossref-fixed-worker-result/v1'
REQUEST=dict(schema_version='MODEL_ONLY',sequence=113,case_index=6,operation='checkpoint',step='reopen_session_close')
RESULT=dict(schema_version=SCHEMA,state='fixed_eight_callbacks_returned_semantics_unqualified',phase='fixed_eight',retained_live_or_uncertain_owners=0)

class Input(io.StringIO):
    def __init__(self,events):super().__init__();self.events=events;self.closes=0
    def close(self):
        if not self.closed:self.events.append('EOF');self.closes+=1
        super().close()

def model(frames=None,error=None,native=True,live_after_eof=False):
    events=[];record={};notices=[];worker=NS();current=NS(closed=False,pid=123,process=object(),owner_job=NS(job=object()))
    worker.profile=dict(cleanup_confirmed=False,input_eof_sent=False);worker.stdin=Input(events)
    worker.stdout=io.StringIO(''.join(json.dumps(f)+'\n'for f in ([REQUEST]if frames is None else frames)));worker.stderr=io.StringIO()
    worker.process=object();worker.returncode=0;worker.done=False
    def exited():return worker.stdin.closed and not live_after_eof
    def wait(handle,milliseconds):events.append('HANDLE_WAIT');return 0 if exited()else 258
    def accounting(job):return dict(active_processes=0 if exited()else 2)
    windows=NS(k=NS(WaitForSingleObject=wait),accounting=accounting)
    def retire():
        if current.closed:return
        if not exited():raise ValueError('XREF_MODEL_OWNER_STILL_LIVE')
        events.append('NATIVE_HANDLE_CLOSE');current.closed=True
    current.close=retire
    guard=NS(windows=windows,samples=[dict(system_cpu_percent=1,available_ram_percent=50)],check=Mock())
    def finish_worker():
        if not(worker.stdin.closed or worker.done):raise ValueError('XREF_MODEL_WORKER_STILL_WAITING_FOR_REPLY')
        events.append('WORKER_CLOSE');worker.profile['cleanup_confirmed']=True
    def wait_worker(timeout=None):
        if not(worker.stdin.closed or worker.done):raise ValueError('XREF_MODEL_WORKER_STILL_WAITING_FOR_REPLY')
        return 0
    worker.close=finish_worker;worker.wait=wait_worker
    worker.poll=lambda:0 if worker.stdin.closed or worker.done else None
    worker.observe=lambda:dict(peak_job_private_percent=.1)
    worker.signal_readonly_target=lambda:events.append('SIGNAL')
    def handle(line):
        if error is not None:raise error
        return '{}'
    def close_handler():
        if native:retire()
        events.append('HANDLER_CLOSE')
    handler=NS(handle=handle,current_native=lambda:current if native else None,close=close_handler,
        summary=lambda:dict(model_only=True,current_closed=current.closed))
    def run():return subject.run(guard,worker,NS(),lambda reader,env=None:events.append('START'),handler,SCHEMA,{},notices.append,record)
    return NS(events=events,record=record,notices=notices,worker=worker,current=current,guard=guard,handler=handler,run=run)

class Transport603(unittest.TestCase):
    def setUp(self):
        self.start_patch=patch('subprocess.Popen',side_effect=AssertionError('NO_SUBPROCESS_ALLOWED'));self.start=self.start_patch.start();self.addCleanup(self.start_patch.stop)
        self.native_patch=patch.object(subject.closed.startup,'PreassignedNativeStartup',side_effect=AssertionError('NO_NATIVE_ALLOWED'))
        self.native_start=self.native_patch.start();self.addCleanup(self.native_patch.stop)
    def tearDown(self):self.start.assert_not_called();self.native_start.assert_not_called()

    def test_01_original600_code_is_no_longer_discarded(self):
        code='CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT';error=ValueError(code)
        self.assertEqual(old.safe_failure(error)['error_code'],'XREF_NATIVE_TRANSPORT_FAILURE_NO_RAW_VALUES')
        self.assertEqual(subject.safe_failure(error)['error_code'],code)

    def test_02_actual_original_guard_deadline_failure_site_survives(self):
        guard=object.__new__(epoch.Guard);guard.deadline=0
        try:guard.check()
        except ValueError as error:row=subject.safe_failure(error)
        self.assertEqual(row['error_code'],'CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT')
        self.assertEqual(row['error_site']['module'],'accept_case112_current_epoch')
        self.assertGreater(row['error_site']['line'],0)

    def test_03_unknown_message_path_and_secret_are_not_logged(self):
        secret='CANARY_PRIVATE_VALUE_739';message='C:/private/document.hwpx '+secret
        row=subject.safe_failure(ValueError(message));self.assertNotIn(secret,json.dumps(row));self.assertNotIn('document.hwpx',json.dumps(row))
        self.assertEqual(row['error_code'],'XREF_NATIVE_TRANSPORT_FAILURE_NO_RAW_VALUES')

    def test_04_only_closed_request_fields_are_retained(self):
        value=dict(REQUEST,identity={'private':'CANARY'},command='secret',document='secret')
        self.assertEqual(subject.request_context(value),{k:REQUEST[k]for k in('sequence','case_index','operation','step')})
        for key,val in(('sequence',True),('case_index',9),('step','secret'),('operation',{})):
            row=dict(value);row[key]=val;self.assertNotIn(key,subject.request_context(row))

    def test_05_eof_precedes_native_wait_on_failed_request(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'))
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_TIMEOUT'):m.run()
        self.assertLess(m.events.index('EOF'),m.events.index('HANDLE_WAIT'))
        self.assertTrue(m.record['abort_eof_sent_before_native_wait']);self.assertTrue(m.record['cleanup'])
        self.assertTrue(m.current.closed);self.assertTrue(m.record['io_threads_joined'])

    def test_06_original_order_reproduces_wait_before_eof_without_hanging(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'))
        def legacy_wait(*args):
            self.assertFalse(m.worker.stdin.closed);raise ValueError('XREF_MODEL_REPRODUCED_WAITING_FOR_REPLY_CYCLE')
        with patch.object(old,'wait_native_exit',side_effect=legacy_wait),self.assertRaisesRegex(ValueError,'REPRODUCED_WAITING_FOR_REPLY_CYCLE'):
            old.run(m.guard,m.worker,NS(),lambda reader,env=None:None,m.handler,SCHEMA,{},m.notices.append,m.record)
        m.worker.stdin.close()  # Fake model only, no process or COM object.

    def test_07_failure_phase_request_counters_hashes_and_summary_survive(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'))
        with self.assertRaises(ValueError):m.run()
        primary=m.record['transport_failure']
        self.assertEqual(primary['transport_phase'],'handle_request');self.assertEqual(primary['last_received_request']['case_index'],6)
        self.assertGreater(m.record['stdout_bytes'],0);self.assertEqual(len(m.record['stdout_sha256']),64)
        self.assertEqual(m.record['requests'],0);self.assertTrue(m.record['handler_summary']['model_only'])

    def test_08_cleanup_error_does_not_replace_primary_failure(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'))
        m.handler.close=Mock(side_effect=ValueError('XREF_MODEL_CLEANUP_FAILURE'))
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_TIMEOUT'):m.run()
        self.assertEqual(m.record['cleanup_failure']['error_code'],'XREF_MODEL_CLEANUP_FAILURE')
        self.assertFalse(m.record['cleanup']);self.assertTrue(m.record['cleanup_pending']);self.assertTrue(m.record['io_threads_joined'])

    def test_09_interrupt_during_manual_native_wait_keeps_primary_and_handles(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'),live_after_eof=True)
        with patch.object(subject,'wait_native_exit',side_effect=KeyboardInterrupt),self.assertRaises(KeyboardInterrupt):m.run()
        self.assertEqual(m.record['transport_failure']['error_code'],'CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT')
        self.assertEqual(m.record['cleanup_failure']['error_code'],'XREF_NATIVE_TRANSPORT_INTERRUPTED')
        self.assertFalse(m.current.closed);self.assertFalse(m.record['cleanup']);self.assertTrue(m.record['io_threads_joined'])

    def test_10_initial_keyboard_interrupt_does_not_reenter_wait(self):
        m=model(error=KeyboardInterrupt())
        with patch.object(subject,'wait_native_exit')as wait,self.assertRaises(KeyboardInterrupt):m.run()
        wait.assert_not_called();self.assertFalse(m.record['cleanup']);self.assertTrue(m.record['io_threads_joined'])
        m.worker.stdin.close()

    def test_11_received_uncertain_result_keeps_old_owner_first_policy(self):
        result=dict(RESULT,retained_live_or_uncertain_owners=1,state='fixed_eight_worker_failed_or_uncertain')
        m=model(frames=[result],live_after_eof=True)
        def manual_wait(*args):self.assertFalse(m.worker.stdin.closed);raise KeyboardInterrupt()
        with patch.object(subject,'wait_native_exit',side_effect=manual_wait),self.assertRaises(KeyboardInterrupt):m.run()
        self.assertNotIn('abort_eof_sent_before_native_wait',m.record)
        self.assertEqual(m.record['result'],result);self.assertFalse(m.record['cleanup']);m.worker.stdin.close()

    def test_12_successful_no_native_result_returns_and_cleans(self):
        m=model(frames=[RESULT],native=False);m.worker.done=True
        self.assertEqual(m.run(),RESULT);self.assertTrue(m.record['cleanup']);self.assertTrue(m.record['io_threads_joined'])
        self.assertNotIn('transport_failure',m.record)

    def test_13_missing_result_fails_closed_after_eof(self):
        m=model(frames=[],native=False);m.worker.done=True
        with self.assertRaisesRegex(ValueError,'ONE_RESULT_AND_EMPTY_STDERR'):m.run()
        self.assertTrue(m.record['cleanup']);self.assertIn('transport_failure',m.record)

    def test_14_nonobject_frame_is_closed_error_not_raw_attribute_error(self):
        m=model(frames=[['CANARY']],native=False)
        with self.assertRaisesRegex(ValueError,'FRAME_OBJECT_REQUIRED'):m.run()
        self.assertNotIn('CANARY',json.dumps(m.record));self.assertTrue(m.record['cleanup'])

    def test_15_summary_failure_cannot_mask_original_or_claim_cleanup(self):
        m=model(error=ValueError('CURRENT_EPOCH_ACCEPT_ORIGINAL600_TIMEOUT'))
        m.handler.summary=Mock(side_effect=ValueError('C:/private/secret.docx CANARY'))
        with self.assertRaisesRegex(ValueError,'ORIGINAL600_TIMEOUT'):m.run()
        self.assertIn('handler_summary_failure',m.record);self.assertFalse(m.record['cleanup'])
        self.assertNotIn('CANARY',json.dumps(m.record))

    def test_16_original_notice_and_native_wait_are_not_reimplemented(self):
        self.assertIs(subject.result_notice,old.result_notice);self.assertIs(subject.wait_native_exit,old.wait_native_exit)

    def test_17_original_byte_frame_and_native_safety_limits_remain(self):
        source=Path(subject.__file__).read_text(encoding='utf-8');tree=ast.parse(source)
        for exact in('range(160)','readline(4098)',"counts['stdout_bytes']>32768","counts['stderr_bytes']>4096",'queue.Queue(maxsize=8)'):
            self.assertIn(exact,source)
        for call in ast.walk(tree):
            if isinstance(call,ast.Call)and isinstance(call.func,ast.Attribute):
                self.assertNotIn(call.func.attr,('kill','terminate','TerminateProcess','TerminateJobObject','Quit','ResetDeadline'))
        self.assertNotIn('deadline=',source);self.assertNotIn('.deadline =',source)

    def test_18_no_execution_retry_or_constructor_entry_is_added(self):
        for name in('main','execute','approve','retry','PreassignedNativeStartup'):self.assertNotIn(name,vars(subject))

if __name__=='__main__':unittest.main()
