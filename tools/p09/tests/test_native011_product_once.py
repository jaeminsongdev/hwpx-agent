from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_product_once as m
import successor_preparation_workspace_v1 as publisher
import test_native011_product_parent_handoff as parent_fixture


class Tests(unittest.TestCase):
    def fixture(self,authorize=lambda:True):
        events=[];claims={}
        once=m.Once(lambda:events.append('guard'),authorize=authorize)
        def write(value):
            events.append('claim')
            if m.CLAIM in claims:raise FileExistsError('MODEL_EXISTING_INTENT')
            claims[m.CLAIM]=dict(value)
            return dict(path=m.CLAIM,bytes=300,sha256='a'*64)
        def entry():events.append('entry');self.assertTrue(once.authorize_native());return 'MODEL_ORIGINAL_RETURN'
        return NS(once=once,events=events,claims=claims,write=write,entry=entry)

    def test_default_absent_authority_denies_before_intent_entry_or_native(self):
        f=self.fixture(None)
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.once.execute(f.entry,f.write)
        self.assertEqual(f.claims,{});self.assertEqual(f.once.entry_calls,0);self.assertEqual(f.once.native_authorizations,0)
        with self.assertRaisesRegex(ValueError,'ONE_INVOCATION_NO_RETRY'):f.once.execute(f.entry,f.write)

    def test_false_or_truthy_nonboolean_authority_does_not_publish_or_execute(self):
        for value in (False,1,'approved',object()):
            with self.subTest(value_type=type(value).__name__):
                calls=[];f=self.fixture(lambda:(calls.append(1) or value))
                with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.once.execute(f.entry,f.write)
                self.assertEqual(calls,[1]);self.assertEqual(f.claims,{});self.assertEqual(f.once.entry_calls,0)

    def test_approved_entry_claims_first_and_native_authorization_is_used_once_not_acceptance(self):
        f=self.fixture();result=f.once.execute(f.entry,f.write)
        self.assertEqual(result,'MODEL_ORIGINAL_RETURN');self.assertLess(f.events.index('claim'),f.events.index('entry'))
        self.assertEqual(f.claims[m.CLAIM],m.intent());self.assertFalse(f.claims[m.CLAIM]['queue_acceptance_authorized'])
        proof=f.once.evidence();self.assertEqual(proof['phase'],'RETURNED_NOT_ACCEPTED')
        self.assertEqual(proof['original_native_authorization_calls'],1);self.assertFalse(proof['product_acceptance_qualified'])
        with self.assertRaisesRegex(ValueError,'ONE_INVOCATION_NO_RETRY'):f.once.execute(f.entry,f.write)

    def test_duplicate_persistent_claim_blocks_another_instance_before_entry(self):
        f=self.fixture();f.once.execute(f.entry,f.write);before=dict(f.claims)
        second=m.Once(lambda:None,authorize=lambda:True);called=[]
        with self.assertRaises(FileExistsError):second.execute(lambda:called.append(1),f.write)
        self.assertEqual(called,[]);self.assertEqual(f.claims,before);self.assertEqual(second.native_authorizations,0)

    def test_claim_failure_preserves_primary_error_and_does_not_enter_or_retry(self):
        f=self.fixture();error=OSError('MODEL_FSYNC_ERROR')
        def fail(value):raise error
        with self.assertRaises(OSError) as caught:f.once.execute(f.entry,fail)
        self.assertIs(caught.exception,error);self.assertEqual(f.once.intent_attempts,1);self.assertEqual(f.once.entry_calls,0)
        with self.assertRaisesRegex(ValueError,'ONE_INVOCATION_NO_RETRY'):f.once.execute(f.entry,f.write)

    def test_bad_claim_pin_cannot_authorize_native_or_enter(self):
        for failure in ('path','bytes','sha256','extra'):
            f=self.fixture();pin=dict(path=m.CLAIM,bytes=300,sha256='a'*64)
            if failure=='path':pin['path']='other.json'
            elif failure=='bytes':pin['bytes']=True
            elif failure=='sha256':pin['sha256']='bad'
            else:pin['approved']=True
            with self.assertRaisesRegex(ValueError,'EXACT_PERSISTED_ORIGINAL_INTENT_PIN'):f.once.execute(f.entry,lambda value:pin)
            self.assertEqual(f.once.entry_calls,0);self.assertEqual(f.once.native_authorizations,0)

    def test_entry_failure_keeps_claim_and_original_error_without_postfailure_guard(self):
        f=self.fixture();error=ValueError('MODEL_ORIGINAL_NATIVE_ERROR')
        def fail():f.once.authorize_native();raise error
        with self.assertRaises(ValueError) as caught:f.once.execute(fail,f.write)
        self.assertIs(caught.exception,error);self.assertIn(m.CLAIM,f.claims);self.assertTrue(f.once.failed)
        self.assertEqual(f.once.native_authorizations,1)

    def test_missing_or_repeated_native_gate_cannot_return_success_even_if_caught(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_AUTHORITY_CONSUMED_ONCE'):f.once.execute(lambda:'MODEL_NO_NATIVE',f.write)
        f=self.fixture()
        def caught():
            f.once.authorize_native()
            try:f.once.authorize_native()
            except ValueError:pass
            return 'MODEL_CAUGHT_ERROR'
        with self.assertRaisesRegex(ValueError,'ORIGINAL_NATIVE_AUTHORITY_CONSUMED_ONCE'):f.once.execute(caught,f.write)
        self.assertTrue(f.once.failed);self.assertEqual(f.once.native_authorizations,1)

    def test_native_gate_before_claim_or_wrong_owner_cannot_create_authority(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'ONE_CLAIMED_ORIGINAL_NATIVE_ENTRY_ONLY'):f.once.authorize_native()
        self.assertEqual(f.claims,{})
        with self.assertRaisesRegex(ValueError,'ONE_INVOCATION_NO_RETRY'):f.once.execute(f.entry,f.write)
        f=self.fixture()
        with patch.object(m.threading,'get_ident',return_value=-1):
            with self.assertRaisesRegex(ValueError,'SAME_OWNER_PROCESS_THREAD'):f.once.execute(f.entry,f.write)
        self.assertEqual(f.claims,{});self.assertEqual(f.once.invocations,0)

    def test_original_parent_gate_consumes_once_dependency_only_after_claim_model_only(self):
        f=self.fixture();original=parent_fixture.Tests().fixture(authorize=f.once.authorize_native);connected=original.install()
        self.assertEqual(original.journal,[]);self.assertEqual(f.once.native_authorizations,0)
        self.assertEqual(f.once.execute(lambda:original.actual.run_owned(1),f.write),17)
        self.assertEqual(f.once.native_authorizations,1);self.assertEqual(connected.context.jobs,1)
        self.assertTrue(connected.state.cleanup_confirmed)
        self.assertEqual(connected.context.bindings[0].gates[0].seconds,15)
        self.assertEqual(original.strict_state.states[0].diagnostics()['maximum_GO_to_complete_capture_seconds'],10)

    def test_original_parent_with_absent_external_authority_never_gets_job_or_frame_model_only(self):
        f=self.fixture(None);original=parent_fixture.Tests().fixture(authorize=f.once.authorize_native);original.install()
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):
            f.once.execute(lambda:original.actual.run_owned(1),f.write)
        self.assertEqual(original.journal,[]);self.assertEqual(f.claims,{})

    def test_caught_failure_in_external_check_or_claim_cannot_reach_entry_and_keeps_first_cause(self):
        for where in ('external','claim'):
            def premature():
                try:f.once.authorize_native()
                except ValueError:pass
            # Bind the callback at creation; do not bypass the origin guard to
            # reach the separate caught-failure contract under test.
            f=self.fixture((lambda:(premature() or True)) if where=='external' else (lambda:True))
            if where=='external':
                write=f.write
            else:
                def write(value):
                    pin=f.write(value);premature();return pin
            with self.assertRaises(ValueError):f.once.execute(f.entry,write)
            self.assertEqual(f.once.entry_calls,0);self.assertNotIn('entry',f.events)
            self.assertEqual(f.once.evidence()['error_code'],'NATIVE011_PRODUCT_ONCE_ONE_CLAIMED_ORIGINAL_NATIVE_ENTRY_ONLY')

    def test_caught_reentrant_native_gate_inside_guard_cannot_return_true_to_original_parent(self):
        f=self.fixture();original=parent_fixture.Tests().fixture(authorize=f.once.authorize_native);original.install()
        def checkpoint():
            if f.once.phase=='ENTRY' and f.once.native_authorizations==1:
                try:f.once.authorize_native()
                except ValueError:pass
        f.once.checkpoint=checkpoint
        with self.assertRaisesRegex(ValueError,'NO_CAUGHT_FAILURE_OR_PHASE_CHANGE_AT_CHECKPOINT'):
            f.once.execute(lambda:original.actual.run_owned(1),f.write)
        self.assertEqual(original.journal,[]);self.assertEqual(f.once.native_authorizations,1)
        self.assertEqual(f.once.evidence()['error_code'],'NATIVE011_PRODUCT_ONCE_ONE_CLAIMED_ORIGINAL_NATIVE_ENTRY_ONLY')

    def test_whole_original_publisher_is_bound_without_io_and_wrong_payload_or_code_is_denied(self):
        raw=(Path(__file__).resolve().parents[3]/m.PUBLISHER['path']).read_bytes()
        write=m.claim_writer(raw,publisher,object(),object())
        changed=m.intent();changed['queue_acceptance_authorized']=True
        with self.assertRaisesRegex(ValueError,'EXACT_ONCE_INTENT_NOT_APPROVAL'):write(changed)
        before=publisher.publish.__code__
        try:
            publisher.publish.__code__=before.replace(co_consts=(*before.co_consts,'MODEL_CHANGED'))
            with self.assertRaisesRegex(ValueError,'ORIGINAL_PUBLISHER_CODE_UNCHANGED'):write(m.intent())
        finally:publisher.publish.__code__=before
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_PUBLISHER_SOURCE'):m.claim_writer(raw+b' ',publisher,object(),object())

    def test_cli_constructs_only_and_rejects_native_go_or_retry_arguments(self):
        with patch.object(sys,'argv',['once.py']),patch.object(m,'construct_entry',return_value=17) as construct:
            self.assertEqual(m.main(),17);construct.assert_called_once()
        for args in (['--native'],['--go'],['--runtime'],['--attempt','1']):
            with patch.object(sys,'argv',['once.py',*args]),patch.object(m,'construct_entry',side_effect=AssertionError('NO_NATIVE')):
                with self.assertRaisesRegex(ValueError,'CONSTRUCTION_ONLY_NO_GO_OR_NATIVE_ARGUMENTS'):m.main()

    def test_evidence_does_not_repeat_arbitrary_external_exception_values(self):
        f=self.fixture()
        def fail():raise ValueError('MODEL_PRIVATE_EXTERNAL_VALUE')
        with self.assertRaises(ValueError):f.once.execute(fail,f.write)
        self.assertEqual(f.once.evidence()['error_code'],'ORIGINAL_ENTRY_ERROR')

    def test_construct_entry_rejects_unbounded_outputs_and_noncallable_outer_before_io(self):
        for options in (dict(outer=True),dict(output='D:/outside.json'),
                dict(output=m.RUNTIME),dict(output='implementation/p09/evidence/p09-361-native011-other.v1.json'),
                dict(checkpoint_route=lambda *args:None),dict(outer=lambda *args:None,checkpoint_route=True)):
            with self.assertRaises(ValueError):m.construct_entry(**options)

    def test_fresh_authority_dependency_is_exact_and_never_rebinds_default_once(self):
        default=self.fixture(None);fresh=self.fixture();authority=fresh.once.external
        class Base:pass
        for wrong in (None,True,False,lambda:True):
            with self.assertRaises(ValueError):m.driver_type(Base,fresh.once,authorize=wrong)
        with self.assertRaises(ValueError):m.driver_type(Base,default.once,authorize=authority)
        self.assertIsNone(default.once.external);self.assertEqual(default.once.external_calls,0)
        self.assertTrue(issubclass(m.driver_type(Base,fresh.once,authorize=authority),Base))
        self.assertEqual(fresh.once.external_calls,0)

    def test_authority_flags_are_rejected_before_construct_entry_filesystem_work(self):
        for authority in (True,False,'approved',1):
            with self.assertRaisesRegex(ValueError,'EXPLICIT_OPTIONAL_AUTHORITY_DEPENDENCY_NOT_FLAG'):
                m.construct_entry(authorize=authority)

    def test_default_or_authorized_origin_cannot_be_replaced_after_creation(self):
        for original in (None,lambda:True):
            f=self.fixture(original);f.once.external=lambda:True
            with self.assertRaisesRegex(ValueError,'AUTHORITY_DEPENDENCY_FIXED_AT_CREATION'):
                f.once.execute(f.entry,f.write)
            self.assertEqual(f.claims,{});self.assertEqual(f.once.external_calls,0);self.assertEqual(f.once.invocations,0)

    def test_real_parent_dependency_identity_and_two_named_inputs_are_witnessed_by_outer_driver_model(self):
        f=self.fixture(None);calls=[];authorize=f.once.authorize_native
        def execute(run):return authorize()
        evidence=dict(authorization_dependency_present=True,execution_attempts=0,component_connections=0)
        class Base:
            def __init__(self):self.construct_only=True;self.native=None;self.parent_handoff=NS(evidence=lambda:evidence)
            def bind(self,*args):pass
            def run(self,*args):calls.append('original-construction');return dict(GO_authorized=False)
        pins={name:dict(path=name,bytes=2,sha256='0'*64) for name in (m.SELF,m.TEST)}
        reader=NS(snapshots={},final_fresh_hashes=0,checkpoint=lambda:calls.append('guard'))
        def pin(name):reader.snapshots[name]=pins[name];return pins[name]
        def finish():reader.final_fresh_hashes=len(reader.snapshots);calls.append('closing2')
        reader.pin=pin;reader.finish=finish
        a=NS(AcceptanceReader=lambda *args:reader,exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        q=NS(checkpoint=lambda:None,finish=lambda:(_ for _ in ()).throw(AssertionError('NO_REPEATED_ORIGINAL_CLOSE')))
        control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple('base'+str(i) for i in range(72))))
        driver=m.driver_type(Base,f.once)();driver.bind(None,None,None,None,None,control)
        self.assertEqual(len(control.admit(None,None,None).control_names),74)
        data=NS(planned=NS(current=pins,batch=NS(parent_connection=NS(parent=NS(run_owned=execute)))))
        out=driver.run(Path('model-root'),q,a,None,None,None,data,None,None,None,None,{},None,None)
        self.assertEqual(calls,['original-construction','closing2','guard'])
        self.assertTrue(out['product_once_entry']['original_parent_authority_dependency_connected'])
        self.assertFalse(out['product_once_entry']['external_execution_authority_supplied'])
        self.assertFalse(out['product_once_entry']['original_complete_entry_lifecycle_connected'])


if __name__=='__main__':unittest.main()
