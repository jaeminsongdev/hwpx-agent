"""Planned retirement bounds and only-source7..8 profile; no Native activation."""
import contextlib,inspect,io,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import prepared_bookmark689_drain as drain
import prepared_bookmark631_drain as olddrain
import prepared_bookmark_native690 as m
import prepared_bookmark_native684 as old
import prepared_bookmark690_io as wire
import prepared_bookmark684_io as oldwire
import run_prepared_bookmark_native690 as entry
import prepared_bookmark690_notice as notice

def record(pid,birth=None,session=1):return dict(process_id=pid,process_birth_100ns=pid*10 if birth is None else birth,session_id=session,closed=False,observations=[])
def frame(**kw):
    v=dict(schema_version=m.REQUEST,sequence=1,case_index=1,operation='checkpoint',step='prepare_slot');v.update(kw);return json.dumps(v)

class Contracts(unittest.TestCase):
    def test_01_eight_cases_accept13th_and16th_retirements(self):
        rows=drain.SessionRecords(8)
        for i in range(1,17):rows.append(record(i))
        self.assertEqual(len(rows),16);self.assertEqual(rows.maximum_sessions,16)
        with self.assertRaisesRegex(ValueError,'PLANNED_SESSION_LIMIT'):rows.append(record(17))
        self.assertEqual(len(rows),16);self.assertTrue(rows.stopped)
    def test_02_tail_two_exactly_four_sessions(self):
        rows=drain.SessionRecords(2)
        for i in range(1,5):rows.append(record(i))
        with self.assertRaises(ValueError):rows.append(record(5))
        self.assertEqual(len(rows),4)
    def test_03_invalid_planned_count_denied(self):
        for n in(True,0,9,2.0):
            with self.assertRaises(ValueError):drain.SessionRecords(n)
    def test_04_duplicate_kernel_owner_seals_even_after_closed(self):
        rows=drain.SessionRecords(8);v=record(1);v['closed']=True;rows.append(v)
        with self.assertRaisesRegex(ValueError,'RETIRED_TWICE'):rows.append(record(1))
        with self.assertRaises(ValueError):rows.append(record(2))
        self.assertEqual(len(rows),1)
    def test_05_reused_pid_with_different_birth_is_distinct(self):
        rows=drain.SessionRecords(2);rows.append(record(1,10));rows.append(record(1,11));self.assertEqual(len(rows),2)
    def test_06_invalid_identity_not_counted(self):
        for row in(record(True),record(1,0),record(1,1,-1)):
            rows=drain.SessionRecords(2)
            with self.assertRaises(ValueError):rows.append(row)
            self.assertEqual(len(rows),0)
    def fixtures(self,states):
        clock=NS(now=0.)
        def sleep(s):clock.now+=s
        g=NS(check=Mock(),windows=NS(k=NS(WaitForSingleObject=Mock(return_value=0)),accounting=Mock(side_effect=[dict(active_processes=n)for n in states])),samples=[dict(system_cpu_percent=1.,available_ram_percent=50.)])
        current=NS(pid=1,birth=10,session=1,closed=False,process=1,owner_job=NS(job=2,observe=Mock()))
        worker=NS(observe=Mock());rows=drain.SessionRecords(2)
        return current,g,worker,rows,dict(clock=lambda:clock.now,sleep=sleep,observe_identities=lambda *a:[])
    def test_07_actual_guarded_drain_to_empty(self):
        c,g,w,rows,args=self.fixtures([1,0]);drain.wait(c,g,w,Mock(),rows,**args)
        self.assertTrue(rows[0]['closed']);self.assertEqual(g.check.call_count,2)
    def test_08_cpu_or_memory_failure_stops_before_owner_work(self):
        c,g,w,rows,args=self.fixtures([1]);g.check.side_effect=ValueError('STOP_RAM')
        with self.assertRaisesRegex(ValueError,'STOP_RAM'):drain.wait(c,g,w,Mock(),rows,**args)
        c.owner_job.observe.assert_not_called();w.observe.assert_not_called();self.assertFalse(rows[0]['closed'])
    def test_09_raw_record_list_cannot_bypass_planned_policy(self):
        c,g,w,rows,args=self.fixtures([0])
        with self.assertRaises(ValueError):drain.wait(c,g,w,Mock(),[],**args)
    def test_10_original45s_guard_wait_cleanup_body_preserved(self):
        expected=inspect.getsource(olddrain.wait).replace('    row = dict(process_id=current.pid, root_exited=False, closed=False, observations=[])',"    require(type(records) is SessionRecords, 'PLANNED_SESSION_RECORDS_REQUIRED')\n    row = dict(process_id=current.pid, process_birth_100ns=current.birth, session_id=current.session,\n               root_exited=False, closed=False, observations=[])").replace("    require(len(records) <= 12, 'SINGLE_RETIREMENT_PER_SESSION')\n",'').replace('DRAIN631','DRAIN689')
        self.assertEqual(inspect.getsource(drain.wait),expected);self.assertEqual(drain.SECONDS,olddrain.SECONDS)
        self.assertEqual(inspect.getsource(drain.identities),inspect.getsource(olddrain.identities))
    def test_11_exact_source_mapping7_and8(self):
        self.assertEqual([m.directory(i)[-2:]for i in(1,2)],['07','08'])
        for i in(True,0,3,7):
            with self.assertRaises(ValueError):m.directory(i)
    def test_12_new_wire_accepts_only_two_original_typed_steps(self):
        for index in(1,2):
            for step in m.STEPS:
                v,internal=m.translate_request(frame(case_index=index,step=step));self.assertEqual(internal['step'],m.LEGACY[step])
        for value in(frame(case_index=3),frame(case_index=True),frame(schema_version=old.REQUEST),frame(step='sdk_insert'),frame(path='caller')):
            with self.assertRaises(ValueError):m.translate_request(value)
    def test_13_old_host_and_case_owner_ordering_kept(self):
        for name in('respond','close','summary'):
            self.assertEqual(inspect.getsource(getattr(m.Host,name)),inspect.getsource(getattr(old.Host,name)).replace('684','690'))
        self.assertEqual(inspect.getsource(m.Cases),inspect.getsource(old.Cases).replace('684','690'))
    def test_14_finish_two_then_closed_boundary3_only(self):
        h=NS(guard=Mock());cases=NS(between=Mock(return_value=True));handler=m.Handler(h,cases)
        with patch.object(m.base.BatchHandler,'handle',return_value=json.dumps(dict(acknowledged=True))):
            handler.handle(json.dumps(dict(operation='finish',case_index=1,case_status='returned')));h.guard.advance.assert_not_called()
            handler.handle(json.dumps(dict(operation='finish',case_index=2,case_status='returned')))
        label,closed=h.guard.advance.call_args.args;self.assertEqual(label,'batch_close');self.assertTrue(closed());cases.between.assert_called_once_with(3)
    def test_15_new_ports_and_channel_are_only_namespace_projection(self):
        for current,prior in((m.PORTS,old.PORTS),(m.CHANNEL,old.CHANNEL)):
            self.assertEqual((m.r.c.ROOT/current).read_text(encoding='utf-8'),(m.r.c.ROOT/prior).read_text(encoding='utf-8').replace('684','690'))
    def test_16_fixed_worker_selects_only_last_two(self):
        source=(m.r.c.ROOT/old.TARGET).read_text(encoding='utf-8').replace('684','690').replace('PreparedBlockEightAfterCurrentSession','PreparedBlockRemainingTwoAfterCurrentSession')
        expected=source.replace('foreach ($case in @($manifest.cases))','foreach ($case in @($manifest.cases | Select-Object -Skip 6))').replace('$sourceIndex=$index','$sourceIndex=$index+6').replace('$completed -eq 8','$completed -eq 2').replace('planned_cases=8','planned_cases=2').replace('block_eight_callbacks','block_tail_two_callbacks')
        self.assertEqual((m.r.c.ROOT/m.TARGET).read_text(encoding='utf-8'),expected)
    def test_17_same_section_limits_only_two_case_sections(self):
        expected=(m.r.c.ROOT/'tools/p09/prepared_bookmark684_sections.py').read_text().replace('684','690').replace('range(1,9)','range(1,3)').replace('eight-closed','tail-two-closed')
        self.assertEqual((m.r.c.ROOT/'tools/p09/prepared_bookmark690_sections.py').read_text(),expected);self.assertEqual((m.sections.SECTION_SECONDS,m.sections.WHOLE_SECONDS),(600,1800))
    def test_18_original_transport_function_byte_identical(self):
        self.assertEqual(inspect.getsource(wire.run),inspect.getsource(oldwire.run));self.assertIs(wire.wait_native_exit,oldwire.wait_native_exit)
    def test_19_parser_never_replays_consumed_flag(self):
        for args in([],['--execute-block-eight-once'],['--execute-remaining-two-once','--retry'],['--execute-remaining-two-once','--inspect-only']):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):entry.parser().parse_args(args)
        self.assertTrue(entry.parser().parse_args(['--execute-remaining-two-once']).execute_remaining_two_once)
    def test_20_two_trace_ordinals_and_four_profiles(self):
        reader=Mock();reader.snapshots={};reader.final_fresh_hashes=0;host=NS(scope=NS(sessions=[1,2,3,4]))
        with patch.object(m.evidence.r.a,'AcceptanceReader',return_value=reader),patch.object(m.evidence,'captured',side_effect=lambda q,f,i,p:(i,p)):
            row=m.evidence.current_artifacts(Mock(),host,m.directory)
        self.assertEqual(row['cases'],[(1,[1,2]),(2,[3,4])])
        source=inspect.getsource(old.evidence.captured).replace('684','690').replace("trace['source_case_index'] == index,","trace['source_case_index'] == index+6,").replace('source_case_index=index,','source_case_index=index+6,')
        self.assertEqual(inspect.getsource(m.evidence.captured),source)
    def test_21_tail_result_notice_truthful_and_redacted(self):
        for state,failed in(('block_tail_two_callbacks_returned_semantics_unqualified',False),('block_tail_two_callbacks_failed_or_partial',True)):
            result=notice.result_notice(dict(state=state,phase='fixed_eight',error_code='PRIVATE VALUE'))
            self.assertIs(result['worker_failed_or_uncertain'],failed);self.assertNotIn('PRIVATE VALUE',json.dumps(result))
    def test_22_new_worker_is_fixed_no_arbitrary_target(self):
        reader=Mock();reader.root=m.r.c.ROOT;reader.snapshots={m.base.candidate.original.BOOTSTRAP:dict(sha256=m.base.candidate.original.BOOTSTRAP_SHA)}
        args=json.loads(m.Worker._fixed_command(object(),reader)[-1]);self.assertEqual(args[-1],'-PreparedBlockRemainingTwoAfterCurrentSession');self.assertEqual(args[-2],str(m.r.c.ROOT/m.TARGET))
    def test_23_no_partial_owner_set_passes_artifact_gate(self):
        host=NS(protocol=NS(protocol=NS(case_index=3,stopped=False)),scope=NS(sessions=[1,2,3]))
        with patch.object(m.evidence,'current_artifacts')as producer,self.assertRaises(ValueError):m.artifacts(Mock(),host)
        producer.assert_not_called()
    def test_24_no_new_deadline_on_bad_wait_status(self):
        c,g,w,rows,args=self.fixtures([0]);g.windows.k.WaitForSingleObject.return_value=0xffffffff
        with self.assertRaisesRegex(ValueError,'EXACT_ROOT_WAIT_FAILED'):drain.wait(c,g,w,Mock(),rows,**args)
        self.assertFalse(rows[0]['closed'])

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Contracts).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),failed_tests=[str(t)for t,_ in result.errors+result.failures],actual_native_started=False)))
    sys.exit(0 if result.wasSuccessful()else 2)
