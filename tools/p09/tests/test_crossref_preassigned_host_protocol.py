"""New protocol/scope composition models. Fake process lifetimes are never Native evidence."""
import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_crossref_preassigned_session_scope as prior_models
import crossref_preassigned_host_protocol as subject


class ModelHost:
    def __init__(self):
        self.events=[];self.created=[];self.failure=None;self.auto_exit=True
        windows=subject.sessions.startup.limits.c.Windows.__new__(subject.sessions.startup.limits.c.Windows)
        self.scope=subject.sessions.PreassignedSessionScope(NS(check=Mock(),windows=windows),lambda:None)
        self.host=subject.PreassignedHostProtocol(self.scope)
        self.patcher=patch.object(subject.sessions.startup,'PreassignedNativeStartup',side_effect=self.factory)
    def factory(self,*args):
        item=prior_models.FakeStartup(len(self.created)+1,self.events);item.fail=self.failure;self.created.append(item);return item
    def __enter__(self):self.patcher.start();return self
    def __exit__(self,*args):self.patcher.stop()
    def request(self,operation='checkpoint',case_index=None,sequence=None,**extra):
        return json.dumps(dict(schema_version=subject.REQUEST,sequence=self.host.protocol.sequence+1 if sequence is None else sequence,
            case_index=self.scope.case_index if case_index is None else case_index,operation=operation,**extra),separators=(',',':'))
    def respond(self,raw):
        value=self.host.respond(raw);out=json.loads(value)
        if self.auto_exit and out['acknowledged']:
            request=json.loads(raw)
            if request.get('step')in('save_session_close','reopen_session_close'):self.scope.current.alive=False
        return value
    def send(self,operation='checkpoint',**extra):return json.loads(self.respond(self.request(operation,**extra)))
    def begin(self):
        self.send(step='prepare_slot');return self.send(step='create_save_session')['owner_descriptor']
    def admit(self,d=None):
        if d is None:d=self.scope.pending_owner_descriptor(self.scope.case_index)
        identity={k:d[k]for k in('process_id','session_id','created_at_utc','executable_sha256')}
        identity['window_handle_binds_exact_process']=True
        return self.send('admit_owner',identity=identity,window_handle=123)
    def complete_case(self):
        self.begin();assert self.admit()['acknowledged']
        # Bounded positive flow: a failed checkpoint must fail, never spin on an
        # unchanged cursor and consume a core during model verification.
        for _ in range(len(subject.original.STEPS)):
            if self.scope.cursor==len(subject.original.STEPS):break
            step=subject.original.STEPS[self.scope.cursor];out=self.send(step=step)
            assert out['acknowledged']
            if step=='create_reopen_session':assert self.admit(out['owner_descriptor'])['acknowledged']
        assert self.scope.cursor==len(subject.original.STEPS)
        return self.send('finish',case_status='returned')


class V2ProtocolContracts(unittest.TestCase):
    def test_01_all_eight_scope_and_wire_flows_keep_sixteen_unique_model_sessions(self):
        with ModelHost()as m:
            for _ in range(8):self.assertTrue(m.complete_case()['acknowledged'])
            self.assertEqual(m.host.protocol.sequence,152);self.assertEqual(len(m.created),16)
            summary=m.host.summary();self.assertTrue(summary['protocol']['all_eight_callback_cases_returned'])
            self.assertTrue(summary['scope']['all_eight_callback_cases_returned']);self.assertFalse(summary['native_execution_authorized'])
            self.assertEqual(len(summary['scope']['retired_sessions']),16)
    def test_02_only_creation_checkpoints_return_descriptor(self):
        with ModelHost()as m:
            self.assertIsNone(m.send(step='prepare_slot')['owner_descriptor']);out=m.send(step='create_save_session')
            self.assertEqual(out['owner_descriptor']['session_label'],'save');self.assertIsNone(m.admit()['owner_descriptor'])
            self.assertIsNone(m.send(step='source_open')['owner_descriptor'])
    def test_03_creation_ack_is_not_owner_or_native_authority(self):
        with ModelHost()as m:
            d=m.begin();self.assertFalse(d['COM_owner_bound']);self.assertTrue(m.scope.pending_admission)
            for key in('native_execution_authorized','native_startup_qualified','P09_complete'):self.assertFalse(d[key])
            self.assertFalse(m.send(step='source_open')['acknowledged'])
    def test_04_v1_request_cannot_enter_v2_and_latches_without_creation(self):
        with ModelHost()as m:
            raw=m.request(step='prepare_slot').replace(subject.REQUEST,subject.original.REQUEST)
            self.assertFalse(json.loads(m.respond(raw))['acknowledged']);self.assertEqual(m.created,[]);self.assertTrue(m.host.protocol.stopped)
    def test_05_extra_request_fields_and_unknown_operations_do_not_create(self):
        for extra in({'approved':True},{'path':'PRIVATE'},{'subset':[1]},{'operation':'launch'}):
            with ModelHost()as m:
                value=json.loads(m.request(step='prepare_slot'));value.update(extra)
                self.assertFalse(json.loads(m.respond(json.dumps(value)))['acknowledged']);self.assertEqual(m.created,[])
    def test_06_duplicate_escaped_keys_invalid_json_and_multiline_reject(self):
        for text in('{','[]','null','{"schema_version":"x","schema_versi\\u006fn":"y"}','{}\n{}'):
            with ModelHost()as m:self.assertFalse(json.loads(m.respond(text))['acknowledged']);self.assertEqual(m.created,[])
    def test_07_boolean_sequence_and_wrong_case_or_step_reject(self):
        for key,value in(('sequence',True),('sequence',2),('case_index',2),('step','source_open')):
            with ModelHost()as m:
                request=json.loads(m.request(step='prepare_slot'));request[key]=value
                self.assertFalse(json.loads(m.respond(json.dumps(request)))['acknowledged']);self.assertEqual(m.created,[])
    def test_08_wrong_canonical_birth_or_session_is_rejected_before_backend_bind(self):
        for field,value in(('created_at_utc','2026-10-21T00:00:00.0000001Z'),('session_id',2),('process_id',91)):
            with ModelHost()as m:
                d=m.begin();d[field]=value;self.assertFalse(m.admit(d)['acknowledged']);self.assertFalse(any(e[0]=='bind'for e in m.events))
                self.assertTrue(m.scope.pending_admission)
    def test_09_creation_failure_preserves_backend_and_closed_scope_error(self):
        with ModelHost()as m:
            m.failure='create';m.send(step='prepare_slot');out=m.send(step='create_save_session')
            self.assertFalse(out['acknowledged']);self.assertIsNone(out['owner_descriptor']);self.assertIs(m.scope.current,m.created[0])
            self.assertIsNotNone(m.host.scope_error);self.assertFalse(any(e[0]=='resume'for e in m.events))
    def test_10_resume_failure_never_sends_partial_descriptor(self):
        with ModelHost()as m:
            m.failure='resume';m.send(step='prepare_slot');out=m.send(step='create_save_session')
            self.assertFalse(out['acknowledged']);self.assertIsNone(out['owner_descriptor']);self.assertEqual(sum(e[0]=='resume'for e in m.events),1)
    def test_11_bind_failure_retains_exact_pending_owner(self):
        with ModelHost()as m:
            m.failure='bind';m.begin();self.assertFalse(m.admit()['acknowledged']);self.assertIs(m.scope.current,m.created[0]);self.assertTrue(m.scope.pending_admission)
    def test_12_failed_case_finish_can_reach_cleanup_once_without_new_creation(self):
        with ModelHost()as m:
            m.send(step='prepare_slot');self.assertTrue(m.send('finish',case_status='failed')['acknowledged'])
            self.assertFalse(m.send('finish',case_status='failed')['acknowledged']);self.assertEqual(m.created,[])
    def test_13_live_previous_owner_blocks_new_session_without_replacement(self):
        with ModelHost()as m:
            m.auto_exit=False;m.begin();m.admit()
            for _ in range(len(subject.original.STEPS)):
                if subject.original.STEPS[m.scope.cursor]=='create_reopen_session':break
                self.assertTrue(m.send(step=subject.original.STEPS[m.scope.cursor])['acknowledged'])
            self.assertEqual(subject.original.STEPS[m.scope.cursor],'create_reopen_session')
            self.assertFalse(m.send(step='create_reopen_session')['acknowledged']);self.assertEqual(len(m.created),1);self.assertIs(m.scope.current,m.created[0])
    def test_14_reply_and_descriptor_fit_bound_and_do_not_expose_paths(self):
        with ModelHost()as m:
            m.send(step='prepare_slot');raw=m.respond(m.request(step='create_save_session'));self.assertLess(len(raw.encode()),4096)
            self.assertNotIn('PRIVATE',raw);self.assertNotIn('C:\\',raw);self.assertEqual(set(json.loads(raw)['owner_descriptor']),subject.KEYS)
    def test_15_descriptor_rejects_extra_fields_true_flags_and_numeric_booleans(self):
        with ModelHost()as m:
            d=m.begin()
            for key,value in(('approved',True),('native_execution_authorized',True),('process_id',True),('session_id',2**31),('P09_complete',0)):
                bad=dict(d);bad[key]=value
                with self.assertRaises(ValueError):subject.validate_descriptor(bad,1,'save')
    def test_16_descriptor_rejects_context_clock_and_fixed_image_drift(self):
        with ModelHost()as m:
            d=m.begin()
            for key,value in(('case_index',2),('session_label','reopen'),('source','caller'),('created_at_utc','bad'),('executable_sha256','0'*64)):
                bad=dict(d);bad[key]=value
                with self.assertRaises(ValueError):subject.validate_descriptor(bad,1,'save')
