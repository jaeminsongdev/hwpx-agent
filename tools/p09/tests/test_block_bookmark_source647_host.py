"""New fixed schedule and concrete adapter bodies, modeled owners only."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_bookmark_source647_host as m

IDENTITY=dict(process_id=123,session_id=1,created_at_utc='2026-10-23T00:00:00.0000001Z',
    executable_sha256=m.base.original.sessions.startup.limits.EXECUTABLE_SHA,window_handle_binds_exact_process=True)

def descriptor(label):
    return dict(profile=m.base.original.sessions.PROFILE,case_index=1,session_label=label,
        process_id=123,session_id=1,created_at_utc=IDENTITY['created_at_utc'],executable_sha256=IDENTITY['executable_sha256'],
        source='current_exact_preassigned_process_handle',COM_owner_bound=False,native_execution_authorized=False,
        native_startup_qualified=False,P09_complete=False)

def frames():
    values=[]
    for sequence,(op,step,index)in enumerate(m.FLOW,1):
        v=dict(schema_version=m.REQUEST,sequence=sequence,case_index=1,operation=op)
        if op=='checkpoint':v['step']=step
        elif op=='pulse':v.update(phase=step,range_index=index)
        else:v.update(identity=IDENTITY,window_handle=4)
        values.append(v)
    values.append(dict(schema_version=m.REQUEST,sequence=len(values)+1,case_index=1,operation='finish',case_status='returned'))
    return values

def answer(v):
    if v['operation']=='checkpoint'and v['step']in('create_save_session','create_reopen_session'):
        return descriptor('save'if v['step']=='create_save_session'else'reopen')

class Tests(unittest.TestCase):
    def test_complete_one_document_eight_ranges_two_sessions(self):
        callback=Mock(side_effect=answer);s=m.Schedule(callback)
        for v in frames():self.assertTrue(json.loads(s.respond(json.dumps(v)))['acknowledged'])
        self.assertTrue(s.done);self.assertEqual(callback.call_count,54)
        self.assertEqual(sum(v['operation']=='pulse'for v in frames()),35)
        self.assertEqual(len(m.STEPS),16);self.assertEqual(tuple(m.LEGACY.values()),m.base.original.original.STEPS)
        self.assertFalse(s.summary()['native_execution_authorized'])
    def test_extra_authority_path_case_bool_or_duplicate_rejected(self):
        bad=[dict(frames()[0],path='outside'),dict(frames()[0],native_execution_authorized=True),
            dict(frames()[0],case_index=2),dict(frames()[0],case_index=True),dict(frames()[0],sequence=True)]
        for v in bad:
            with self.assertRaises(ValueError):m.decode(json.dumps(v))
        with self.assertRaises(ValueError):m.decode(json.dumps(frames()[0])[:-1]+',"case_index":1}')
    def test_missing_or_reordered_range_pulse_stops(self):
        s=m.Schedule(answer);values=frames();pos=next(i for i,v in enumerate(values)if v.get('phase')=='bookmark_select')
        for v in values[:pos]:self.assertTrue(json.loads(s.respond(json.dumps(v)))['acknowledged'])
        wrong=dict(values[pos],phase='bookmark_execute')
        self.assertFalse(json.loads(s.respond(json.dumps(wrong)))['acknowledged']);self.assertTrue(s.stopped)
        self.assertFalse(json.loads(s.respond(json.dumps(dict(values[pos],sequence=s.sequence+1))))['acknowledged'])
    def test_success_before_all_steps_is_denied(self):
        s=m.Schedule(answer);v=dict(frames()[-1],sequence=1)
        self.assertFalse(json.loads(s.respond(json.dumps(v)))['acknowledged']);self.assertFalse(s.done)
    def test_one_failed_finish_after_callback_fault_no_retry(self):
        def fail(v):raise ValueError('STOP_CPU_LIMIT')
        s=m.Schedule(fail);self.assertFalse(json.loads(s.respond(json.dumps(frames()[0])))['acknowledged'])
        s.dispatch=Mock(return_value=None)
        v=dict(frames()[-1],sequence=2,case_status='failed')
        self.assertTrue(json.loads(s.respond(json.dumps(v)))['acknowledged'])
        self.assertFalse(json.loads(s.respond(json.dumps(dict(v,sequence=3))))['acknowledged'])
        self.assertEqual(s.dispatch.call_count,1);self.assertFalse(s.done)
    def test_descriptor_only_on_creation_and_no_authority(self):
        s=m.Schedule(lambda v:descriptor('save'))
        self.assertFalse(json.loads(s.respond(json.dumps(frames()[0])))['acknowledged'])
        s=m.Schedule(lambda v:None)
        self.assertTrue(json.loads(s.respond(json.dumps(frames()[0])))['acknowledged'])
        self.assertFalse(json.loads(s.respond(json.dumps(frames()[1])))['acknowledged'])
    def test_no_replay_after_returned(self):
        s=m.Schedule(answer)
        for v in frames():s.respond(json.dumps(v))
        self.assertFalse(json.loads(s.respond(json.dumps(dict(frames()[0],sequence=55))))['acknowledged'])
    def test_private_callback_exception_not_printed(self):
        def fail(v):raise ValueError('PRIVATE DOCUMENT TEXT')
        reply=m.Schedule(fail).respond(json.dumps(frames()[0]))
        self.assertNotIn('PRIVATE DOCUMENT TEXT',reply);self.assertFalse(json.loads(reply)['acknowledged'])
    def pulse_host(self):
        h=m.Host.__new__(m.Host)
        h.ready=True;h.worker_lease=Mock();h.source_case=1
        h.scope=NS(stopped=False,case_index=1,label='save',pending_admission=False,
            current=NS(closed=False,profile={'owner_bound':True},observe=Mock()))
        h.protocol=NS(protocol=NS(stopped=False,sequence=4));h.guard=Mock();h.worker=Mock();h.notify=Mock();h.drain_records=[]
        return h
    def test_actual_pulse_dispatch_observes_same_worker_and_native(self):
        h=self.pulse_host();self.assertIsNone(h._dispatch(dict(operation='pulse')))
        h.worker_lease.observe.assert_called_once_with(refresh_image=False)
        h.scope.current.observe.assert_called_once_with()
    def test_pulse_pending_or_unbound_owner_rejected(self):
        for change in('pending','unbound','wrong_source'):
            h=self.pulse_host()
            if change=='pending':h.scope.pending_admission=True
            elif change=='unbound':h.scope.current.profile['owner_bound']=False
            else:h.source_case=None
            with self.assertRaises(ValueError):h._dispatch(dict(operation='pulse'))
            h.scope.current.observe.assert_not_called()
    def test_actual_checkpoint_translation_and_guarded_drain(self):
        h=self.pulse_host();v=next(v for v in frames()if v.get('step')=='create_reopen_session')
        with patch.object(m.base.FixedEightHost,'respond',return_value=json.dumps(dict(acknowledged=True,owner_descriptor=descriptor('reopen'))))as old,patch.object(m.drain,'wait')as wait:
            self.assertEqual(h._dispatch(v),descriptor('reopen'))
            wait.assert_called_once_with(h.scope.current,h.guard,h.worker,h.notify,h.drain_records)
            sent=json.loads(old.call_args.args[0]);self.assertEqual(sent['sequence'],5)
            self.assertEqual(sent['step'],'create_reopen_session');self.assertEqual(sent['schema_version'],m.base.original.REQUEST)
    def test_actual_constructor_cannot_take_model_handoff(self):
        with self.assertRaises(ValueError):m.Host(Mock(),Mock(),object(),{},'0'*64,Mock(),Mock(),Mock(),Mock(),notify=Mock())

if __name__=='__main__':
    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)
    print(json.dumps(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped),
        failed_tests=[t.id().rsplit('.',1)[-1]for t,_ in result.errors+result.failures],actual_native_started=False)))
    raise SystemExit(0 if result.wasSuccessful()else 2)
