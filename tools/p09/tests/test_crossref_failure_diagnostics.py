"""Failure transport/entry models only: no actual worker, Native, COM or file writes."""
import contextlib,copy,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
import crossref_native_worker_io as subject
import run_external_crossref_fixed_batch as entry

SCHEMA='hwpx-agent.private.crossref-session-worker-result/v1'


def result(**extra):
    return dict(schema_version=SCHEMA,state='session_worker_failed_or_uncertain',
        error_code='P09_XREF_ROT_NO_MATCH',phase='exact_existing_owner',**extra)


def native():
    return NS(closed=False,process=987,pid=1001,owner_job=NS(job=543),close=Mock())


def transport(data,*,stderr='',retained=False,interrupt_cleanup=False):
    current=native();events=[];record={}
    value=dict(data)
    if retained:value['retained_live_or_uncertain_owners']=1
    worker=NS(profile={'cleanup_confirmed':False},process=object(),returncode=2,
        stdin=io.StringIO(),stdout=io.StringIO(json.dumps(value)+'\n'),stderr=io.StringIO(stderr),
        signal_readonly_target=Mock(),observe=Mock(return_value={'peak_job_private_percent':0}),
        poll=Mock(return_value=2),wait=Mock())
    def close():worker.profile['cleanup_confirmed']=True
    worker.close=Mock(side_effect=close)
    handler=NS(current_native=Mock(return_value=current),summary=Mock(return_value={'primary_error':'MODEL_FAILED'}),close=Mock(),handle=Mock())
    guard=NS(check=Mock(),windows=object(),samples=[])
    def wait(*args):
        events.append(('wait',copy.deepcopy(record)))
        if interrupt_cleanup:raise KeyboardInterrupt
        current.closed=True
    with patch.object(subject,'wait_native_exit',side_effect=wait):
        try:returned=subject.run(guard,worker,object(),Mock(),handler,SCHEMA,{},lambda n:events.append(('notice',n)),record)
        except BaseException as error:returned=error
    return returned,record,events,worker,handler


def modeled_entry(execute):
    class Guard:
        def __init__(self):self.windows=NS();self.samples=[];self.cleanup=False
        def acquire(self):pass
        def check(self,force=False):pass
        def close(self):self.cleanup=True
    shell=dict(path='powershell.exe',bytes=1000,sha256='a'*64)
    def reader(root,check):
        item=NS(snapshots={entry.CODE:dict(path=entry.CODE,bytes=1,sha256='b'*64)},final_fresh_hashes=0)
        def finish():item.final_fresh_hashes=len(item.snapshots)
        item.pin=Mock(return_value=shell);item.fresh_pin=Mock(return_value=shell);item.finish=Mock(side_effect=finish);return item
    writes=[];readers=[]
    exists=Path.exists;scratch=entry.r.c.ROOT/'target/p09-external-qualified-fixed-eight-scratch-001'
    def fresh_reader(*args):
        value=reader(*args);readers.append(value);return value
    def publish(path,value):writes.append((path,copy.deepcopy(value)));return {'path':'MODEL_ONLY'}
    with contextlib.ExitStack()as stack:
        patches=[patch.object(entry,'OUTPUT','target/p09-model-no-output-file.json'),
            patch.object(entry,'CLAIM','target/p09-model-no-claim-file.json'),
            patch.object(entry.r.tools,'select_own_single_cpu',return_value={}),
            patch.object(entry.r.shared.host,'configure_host_policy'),
            patch.object(entry.r.shared.baseline,'guard_type',return_value=Guard),
            patch.object(entry.r.shared.final,'guard_type',return_value=Guard),
            patch.object(entry.r.a,'AcceptanceReader',side_effect=fresh_reader),
            patch.object(entry,'load_manifest',return_value=({'external_shell_pins':[shell]}, {},set())),
            patch.object(entry.installed,'runtime_pin_matches'),patch.object(entry.installed,'current_identity',return_value={}),
            patch.object(entry.prerequisites,'inspect',return_value={'all_observed_prerequisites_passed':True}),
            patch.object(entry.runtime,'absent_attempts'),patch.object(entry.runtime,'execute',side_effect=execute),
            patch.object(entry,'publish',side_effect=publish),patch.object(entry.Path,'mkdir'),
            patch.object(entry.Path,'exists',autospec=True,side_effect=lambda p:False if p==scratch else exists(p)),
            patch.object(entry.r.audit,'environment',return_value={})]
        for item in patches:stack.enter_context(item)
        with contextlib.redirect_stdout(io.StringIO())as stdout:status=entry.main(['--execute-qualified-fixed-eight'])
    return status,writes,readers,stdout.getvalue()


class FailureContracts(unittest.TestCase):
    def test_01_no_current_native_is_no_wait_or_close(self):
        subject.wait_native_exit(None,object(),Mock())
    def test_02_already_closed_native_does_not_query_or_close(self):
        current=native();current.closed=True;subject.wait_native_exit(current,object(),Mock());current.close.assert_not_called()
    def test_03_exit_and_empty_owned_tree_close_once(self):
        current=native();windows=NS(k=NS(WaitForSingleObject=Mock(return_value=0)),accounting=Mock(return_value={'active_processes':0}))
        notice=Mock();subject.wait_native_exit(current,windows,notice);current.close.assert_called_once();notice.assert_not_called()
    def test_04_exited_main_with_live_child_is_not_cleanup(self):
        current=native();windows=NS(k=NS(WaitForSingleObject=Mock(return_value=0)),accounting=Mock(side_effect=[{'active_processes':1},{'active_processes':0}]))
        notice=Mock()
        with patch.object(subject.time,'sleep')as sleep:subject.wait_native_exit(current,windows,notice)
        self.assertEqual(notice.call_args.args[0]['owned_job_active_processes'],1);sleep.assert_called_once_with(.2);current.close.assert_called_once()
    def test_05_live_cleanup_is_explicitly_not_work_or_permission_wait(self):
        current=native();windows=NS(k=NS(WaitForSingleObject=Mock(return_value=258)),accounting=Mock(return_value={'active_processes':2}));notice=Mock()
        with patch.object(subject.time,'sleep',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):subject.wait_native_exit(current,windows,notice)
        value=notice.call_args.args[0]
        self.assertFalse(value['work_continuing']);self.assertTrue(value['manual_resolution_required']);self.assertTrue(value['rerun_forbidden']);current.close.assert_not_called()
    def test_06_failed_exact_handle_wait_never_closes_or_spins(self):
        current=native();windows=NS(k=NS(WaitForSingleObject=Mock(return_value=0xffffffff)),accounting=Mock())
        with self.assertRaisesRegex(ValueError,'CLEANUP_EXACT_HANDLE_WAIT_FAILED'):subject.wait_native_exit(current,windows,Mock())
        current.close.assert_not_called();windows.accounting.assert_not_called()
    def test_07_result_and_handler_evidence_exist_before_cleanup_wait(self):
        returned,record,events,worker,handler=transport(result())
        self.assertIs(type(returned),dict);waiting=next(v for k,v in events if k=='wait')
        self.assertEqual(waiting['result']['error_code'],'P09_XREF_ROT_NO_MATCH');self.assertEqual(waiting['handler_summary']['primary_error'],'MODEL_FAILED')
        self.assertEqual(events[0][0],'notice');self.assertTrue(record['cleanup']);self.assertFalse(record['cleanup_pending']);handler.close.assert_called_once();worker.close.assert_called_once()
    def test_08_interruption_preserves_failed_result_without_false_cleanup(self):
        returned,record,events,worker,handler=transport(result(),interrupt_cleanup=True)
        self.assertIsInstance(returned,KeyboardInterrupt);self.assertFalse(record['cleanup']);self.assertTrue(record['cleanup_pending'])
        self.assertEqual(record['result']['error_code'],'P09_XREF_ROT_NO_MATCH');self.assertEqual(record['exit_code'],2)
        self.assertEqual(record['cleanup_failure']['error_code'],'XREF_NATIVE_TRANSPORT_INTERRUPTED');worker.close.assert_not_called();handler.close.assert_not_called()
    def test_09_retained_owner_result_is_saved_before_early_wait(self):
        returned,record,events,worker,handler=transport(result(),retained=True,interrupt_cleanup=True)
        self.assertIsInstance(returned,KeyboardInterrupt);self.assertEqual(record['result']['retained_live_or_uncertain_owners'],1)
        self.assertIn('transport_failure',record);self.assertIn('cleanup_failure',record);self.assertFalse(record['cleanup']);worker.close.assert_not_called()
    def test_10_result_notice_never_echoes_arbitrary_worker_values(self):
        value=result();value.update(error_code='private@example.invalid',phase='private/path',message='PRIVATE_SOURCE_VALUE')
        notice=subject.result_notice(value);raw=json.dumps(notice)
        self.assertIsNone(notice['worker_error_code']);self.assertIsNone(notice['worker_phase']);self.assertNotIn('private',raw);self.assertNotIn('PRIVATE_SOURCE_VALUE',raw)
    def test_11_machine_bind_and_rot_codes_are_preserved(self):
        for code in('P09_XREF_BIND_SESSION_WORKER_FAILED','P09_XREF_ROT_NO_MATCH'):
            value=result();value['error_code']=code;self.assertEqual(subject.result_notice(value)['worker_error_code'],code)
    def test_12_transport_error_sanitizer_keeps_only_closed_code_shapes(self):
        for error in(ValueError('private/path'),KeyError('private@example.invalid'),OSError('SECRET_VALUE')):
            self.assertEqual(subject.safe_failure(error)['error_code'],'XREF_NATIVE_TRANSPORT_FAILURE_NO_RAW_VALUES')
        self.assertEqual(subject.safe_failure(ValueError('STOP_CPU_PRESSURE'))['error_code'],'STOP_CPU_PRESSURE')
    def test_13_stderr_failure_does_not_replace_worker_cause(self):
        returned,record,events,worker,handler=transport(result(),stderr='MODEL_PRIVATE_STDERR')
        self.assertIsInstance(returned,ValueError);self.assertEqual(record['result']['error_code'],'P09_XREF_ROT_NO_MATCH')
        self.assertIn('ONE_RESULT_AND_EMPTY_STDERR',record['transport_failure']['error_code'])
        self.assertNotIn('MODEL_PRIVATE_STDERR',json.dumps(events));self.assertTrue(record['cleanup'])
    def test_14_entry_interruption_is_terminal_failure_not_traceback_or_retry(self):
        def execute(guard,manifest,paths,shell,env,notify,row):
            row['qualification_worker']={'cleanup':False,'result':result()};raise KeyboardInterrupt
        status,writes,readers,stdout=modeled_entry(execute);value=writes[-1][1]
        self.assertEqual(status,2);self.assertTrue(value['native_claim_created']);self.assertTrue(value['interrupted']);self.assertFalse(value['cleanup'])
        self.assertEqual(value['error_code'],'EXTERNAL_ENTRY_INTERRUPTED_WITH_UNCONFIRMED_CLEANUP')
        self.assertFalse(value['fixed_eight_executed']);self.assertNotIn('final_fresh_hashes',value)
        self.assertTrue(all(r.finish.call_count==0 for r in readers));self.assertNotIn('Traceback',stdout);self.assertEqual(len(writes),2)
    def test_15_entry_persists_first_diagnostic_before_terminal_cleanup(self):
        def execute(guard,manifest,paths,shell,env,notify,row):
            notify(subject.result_notice(result()));notify(subject.result_notice(result()))
            row['qualification_worker']={'cleanup':False};raise KeyboardInterrupt
        status,writes,readers,stdout=modeled_entry(execute)
        self.assertEqual(status,2);self.assertEqual(len(writes),3)
        self.assertTrue(writes[1][0].endswith('worker-notice001.v1.json'));self.assertEqual(writes[1][1]['worker_error_code'],'P09_XREF_ROT_NO_MATCH')
        self.assertFalse(writes[1][1]['cleanup_confirmed']);self.assertTrue(writes[1][1]['force_kill_forbidden'])
    def test_16_consumed_actual_run_cannot_reexecute_or_publish(self):
        with patch.object(entry.runtime,'execute')as execute,patch.object(entry,'publish')as publish,patch.object(entry.r.tools,'select_own_single_cpu')as select:
            with self.assertRaisesRegex(ValueError,'EXTERNAL_ENTRY_IMMUTABLE_OUTPUT'):entry.main(['--execute-qualified-fixed-eight'])
        execute.assert_not_called();publish.assert_not_called();select.assert_not_called()
    def test_17_body_interrupt_does_not_reenter_native_cleanup_or_lose_cause(self):
        with patch.object(subject,'require',side_effect=KeyboardInterrupt):
            returned,record,events,worker,handler=transport(result())
        self.assertIsInstance(returned,KeyboardInterrupt);self.assertNotIn('result',record)
        self.assertEqual([v for k,v in events if k=='wait'],[])
        self.assertEqual(record['transport_failure']['error_code'],'XREF_NATIVE_TRANSPORT_INTERRUPTED')
        self.assertEqual(record['cleanup_failure']['error_code'],'XREF_NATIVE_TRANSPORT_INTERRUPTED')
        self.assertTrue(record['cleanup_pending']);self.assertFalse(record['cleanup']);worker.close.assert_not_called();handler.close.assert_not_called()
        returned,record,events,worker,handler=transport(result(),retained=True,interrupt_cleanup=True)
        self.assertIsInstance(returned,KeyboardInterrupt);self.assertEqual(len([v for k,v in events if k=='wait']),1)
        worker.close.assert_not_called();handler.close.assert_not_called()
    def test_18_early_notice_keeps_only_fixed_error_kind_and_numeric_hresult(self):
        for kind in('COMException','InvalidOperationException','OtherException'):
            notice=subject.result_notice(result(error_kind=kind,error_hresult='0x800401E3'))
            self.assertEqual(notice['worker_error_kind'],kind);self.assertEqual(notice['worker_error_hresult'],'0x800401E3')
        for kind,hresult in(('PRIVATE_TYPE','0x800401E3'),('COMException','PRIVATE_MESSAGE'),('COMException',2147221021),('COMException','0x1')):
            notice=subject.result_notice(result(error_kind=kind,error_hresult=hresult))
            if kind=='PRIVATE_TYPE':self.assertIsNone(notice['worker_error_kind'])
            if hresult!='0x800401E3':self.assertIsNone(notice['worker_error_hresult'])
            self.assertNotIn('PRIVATE',json.dumps(notice))


if __name__=='__main__':unittest.main()
