"""New preparation successor contracts only. No actual worker/Native invocation."""
import ast,json,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import crossref_preassigned_preparation as subject


def request(operation='checkpoint',sequence=1,**extra):
    return json.dumps(dict(schema_version=subject.wire.REQUEST,case_index=1,sequence=sequence,operation=operation,**extra),separators=(',',':'))


class PreparationContracts(unittest.TestCase):
    def test_01_exact_two_messages_deny_prepare_then_ack_failed_cleanup(self):
        state=subject.DenialProtocol();first=json.loads(state.respond(request(step='prepare_slot')))
        self.assertFalse(first['acknowledged']);self.assertIsNone(first['owner_descriptor']);self.assertFalse(first['native_execution_authorized'])
        last=json.loads(state.respond(request('finish',2,case_status='failed')))
        self.assertTrue(last['acknowledged']);self.assertEqual(last['sequence'],2);self.assertFalse(last['p09_complete'])
    def test_02_returned_finish_never_accepted(self):
        state=subject.DenialProtocol();state.respond(request(step='prepare_slot'))
        with self.assertRaises(ValueError):state.respond(request('finish',2,case_status='returned'))
    def test_03_creation_step_rejected_without_scope(self):
        for step in('create_save_session','create_reopen_session','source_open'):
            state=subject.DenialProtocol()
            with self.assertRaises(ValueError):state.respond(request(step=step))
            self.assertTrue(state.failed);self.assertEqual(state.sequence,0)
    def test_04_wrong_sequence_case_and_bool_rejected(self):
        for key,value in(('sequence',2),('sequence',True),('case_index',2)):
            state=subject.DenialProtocol();data=json.loads(request(step='prepare_slot'));data[key]=value
            with self.assertRaises(ValueError):state.respond(json.dumps(data))
    def test_05_extra_path_or_approval_rejected(self):
        for key,value in(('path','PRIVATE'),('approved',True),('command','DO_NOT_EXECUTE')):
            state=subject.DenialProtocol();data=json.loads(request(step='prepare_slot'));data[key]=value
            with self.assertRaises(ValueError):state.respond(json.dumps(data))
    def test_06_failed_wire_does_not_restart(self):
        state=subject.DenialProtocol()
        with self.assertRaises(ValueError):state.respond('{}')
        with self.assertRaises(ValueError):state.respond(request(step='prepare_slot'))
        self.assertEqual(state.sequence,0)
    def test_07_third_message_and_second_finish_denied(self):
        state=subject.DenialProtocol();state.respond(request(step='prepare_slot'));state.respond(request('finish',2,case_status='failed'))
        with self.assertRaises(ValueError):state.respond(request('finish',3,case_status='failed'))
    def test_08_duplicate_json_keys_never_reach_callbacks(self):
        state=subject.DenialProtocol()
        with self.assertRaises(ValueError):state.respond(request(step='prepare_slot').replace('"sequence":1','"sequence":1,"sequence":1'))
        self.assertEqual(state.sequence,0)
    def test_09_fixed_command_pins_every_source_no_native_switch(self):
        pins=[]
        reader=NS(root=subject.c.ROOT,snapshots={subject.original.BOOTSTRAP:{'sha256':subject.original.BOOTSTRAP_SHA}},pin=pins.append)
        args=subject.command(reader);target=json.loads(args[-1])
        self.assertEqual(pins,list(subject.SOURCE_FILES));self.assertEqual(target[-1],'-InspectPreparationOnly')
        self.assertEqual(target[0],subject.original.SHELL);self.assertEqual(target[-2],str(subject.c.ROOT/subject.TARGET))
        self.assertNotIn('-ExecuteNative',target);self.assertNotIn('Native011',' '.join(target))
    def test_10_no_worker_restart_before_any_command_read(self):
        state=subject.PreparationWorker.__new__(subject.PreparationWorker);state.closed=False;state.start_attempted=True
        with self.assertRaises(ValueError):state.start_preparation(None)
    def test_11_new_worker_live_close_retains_original_non_killing_handle(self):
        state=subject.PreparationWorker.__new__(subject.PreparationWorker)
        state.closed=False;state.job=123;state.process=NS(poll=lambda:None);state.profile={'cleanup_confirmed':False}
        with self.assertRaisesRegex(ValueError,'LIVE_WORKER_NO_FORCE_CLOSE'):state.close()
        self.assertEqual(state.job,123);self.assertFalse(state.closed);self.assertFalse(hasattr(state,'kill'))
    def test_12_no_native_scope_constructor_or_termination_route(self):
        tree=ast.parse(Path(subject.__file__).read_text(encoding='utf-8'))
        calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call)and isinstance(n.func,(ast.Name,ast.Attribute))}
        self.assertFalse(calls & {'PreassignedSessionScope','PreassignedNativeStartup','TerminateProcess','TerminateJobObject','kill','system'})
