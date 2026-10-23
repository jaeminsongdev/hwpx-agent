"""Synthetic controllers/process/IO; never use the real Native/product entry."""
from pathlib import Path
from types import SimpleNamespace as NS
import io
import os
import unittest
from unittest.mock import patch

import native011_product_dispatch as m
import native011_product_once as once_api
import successor_preparation_workspace_v1 as publisher
import test_native011_product_lifecycle as lifecycle_fixture


class MemoryStream(io.BytesIO):
    def fileno(self):return 0
    def __exit__(self,*args):return False


class MemoryRoot:
    parents=()
    def __init__(self):self.stream=MemoryStream();self.names=[]
    def __truediv__(self,name):self.names.append(name);return self
    @property
    def parent(self):return self
    def is_dir(self):return True
    def is_symlink(self):return False
    def is_junction(self):return False
    def open(self,mode):
        if mode!='xb' or self.stream.getvalue():raise FileExistsError('MODEL_NO_RETRY')
        return self.stream


class Tests(unittest.TestCase):
    def fixture(self,authority=True):
        f=lifecycle_fixture.Tests().fixture(authority=authority)
        f.memory=MemoryRoot();root=Path(__file__).resolve().parents[3]
        api=NS(require=m.require,exact=lambda actual,expected,label:m.require(actual==expected,label))
        f.write=once_api.claim_writer((root/once_api.PUBLISHER['path']).read_bytes(),publisher,f.memory,api)
        f.policy.attempts=0
        def arm(context):f.policy.attempts+=1;f.events.append('process_armed')
        f.policy.arm=arm
        f.compiled.bind_inputs(f.context,f.api,f.Reader,f.policy,lambda:None)
        f.pipeline=NS(route=f.route,relay=f.relay,epochs=f.epochs,state=NS(closed=False,
            reader_bound=True,parent_bound=True,coordinator_bound=True,process_audit_bound=True,oracle_inputs_bound=True))
        f.driver=NS(lifecycle_controllers=f.pipeline,lifecycle_procedure=f.compiled,lifecycle_context=f.context,
            oracle_inputs=NS(api=f.api,Reader=f.Reader,policy=f.policy,seal=lambda:None),
            product_audit=NS(policy=f.policy,failed=False),coordinator_boundary=NS(seal=lambda:None),
            construct_only=True,native=None,closed=False,stage='construction')
        f.bind=lambda authorize=f.once.external:m.bind(f.driver,f.once,once_api,f.write,f.events.append,authorize=authorize)
        def run():
            with patch.object(os,'fsync') as fsync:
                result=f.dispatch.run()
                fsync.assert_called_once_with(0)
                return result
        f.run=run
        return f

    def test_bind_is_inert_and_returns_the_unchanged_complete_original_result(self):
        f=self.fixture();f.dispatch=f.bind()
        self.assertEqual(f.events,[]);self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.external_calls,0)
        result=f.run()
        self.assertEqual(result['canonical_receipt_pin']['path'],lifecycle_fixture.m.CANONICAL)
        self.assertEqual(f.memory.names,[once_api.CLAIM]);self.assertEqual(f.connected.context.jobs,1)
        self.assertTrue(f.dispatch.evidence()['original_complete_lifecycle_returned'])
        self.assertFalse(f.dispatch.evidence()['product_or_Native_qualified'])
        self.assertIsNone(f.compiled.state.active_entry);self.assertIsNone(f.compiled.state.returned_result)

    def test_default_absent_and_flag_authority_rejected_before_claim_or_io(self):
        for authority in (True,False,'approved'):
            f=self.fixture(authority=None)
            with self.assertRaises(ValueError):f.bind(authorize=authority)
            self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.external_calls,0)

    def test_default_plan_can_connect_but_is_permanently_denied_before_original_entry(self):
        f=self.fixture(authority=None);f.dispatch=f.bind()
        self.assertFalse(f.dispatch.evidence()['external_authority_dependency_supplied'])
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED_BEFORE_ENTRY'):f.dispatch.run()
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.invocations,0);self.assertEqual(f.events,[])
        self.assertIsNone(f.once.external)

    def connection_fixture(self):
        f=self.fixture(authority=None);root=Path(__file__).resolve().parents[3];f.reads=[]
        f.raw=(root/once_api.PUBLISHER['path']).read_bytes()
        pins={name:dict(path=name,bytes=1,sha256='0'*64) for name in (m.SELF,m.TEST)}
        pins[once_api.PUBLISHER['path']]=dict(once_api.PUBLISHER);f.current=pins
        f.reader=NS(snapshots={})
        def pin(name):f.reads.append(name);f.reader.snapshots[name]=pins[name];return pins[name]
        def read(name,*,parse):self.assertTrue(parse);return pin(name),f.raw
        f.reader.pin=pin;f.reader._read=read;f.reader._bind=lambda name,value:f.reader.snapshots.update({name:value})
        f.api_exact=NS(exact=lambda actual,expected,label:m.require(actual==expected,label),require=m.require)
        f.connect=lambda:m.connect(f.driver,f.once,f.memory,f.reader,f.api_exact,f.current,publisher)
        return f

    def test_connection_reads_explicit_sources_and_original_publisher_without_claim_or_native(self):
        f=self.connection_fixture();plan=f.connect()
        self.assertEqual(f.reads,[m.SELF,m.TEST,once_api.PUBLISHER['path']])
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.events,[])
        self.assertTrue(plan.evidence()['bound']);self.assertEqual(plan.evidence()['dispatch_attempts'],0)
        self.assertTrue(plan.evidence()['original_whole_entry_callable_connected'])

    def test_connection_rejects_noncurrent_original_publisher_before_binding(self):
        f=self.connection_fixture();f.current=dict(f.current)
        f.current[once_api.PUBLISHER['path']]={**once_api.PUBLISHER,'bytes':1}
        with self.assertRaisesRegex(ValueError,'DIRECT_CURRENT_DISPATCH_PUBLISHER'):f.connect()
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.invocations,0)

    def test_connection_rejects_changed_publisher_bytes_before_claim_or_entry(self):
        f=self.connection_fixture();f.raw+=b' '
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_PUBLISHER_SOURCE'):f.connect()
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.invocations,0)

    def test_other_callable_does_not_rebind_existing_default_or_authorized_once(self):
        for original in (None,True):
            f=self.fixture(authority=original);previous=f.once.external
            with self.assertRaises(ValueError):f.bind(authorize=lambda:True)
            self.assertIs(f.once.external,previous);self.assertEqual(f.memory.names,[])

    def test_replaced_origin_is_rejected_even_when_caller_passes_same_new_callback(self):
        f=self.fixture(authority=None);f.once.external=lambda:True
        with self.assertRaisesRegex(ValueError,'AUTHORITY_DEPENDENCY_FIXED_AT_CREATION'):
            f.bind(authorize=f.once.external)
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.once.external_calls,0)

    def test_false_actual_authority_stops_before_claim_and_whole_opening(self):
        f=self.fixture(authority=False);f.dispatch=f.bind()
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EXECUTION_AUTHORITY_REQUIRED'):f.dispatch.run()
        self.assertEqual(f.memory.names,[]);self.assertNotIn('whole_opening',f.events)
        self.assertTrue(f.dispatch.state.failed)

    def test_second_dispatch_is_denied_without_replaying_the_successful_entry(self):
        f=self.fixture();f.dispatch=f.bind();f.run();calls=f.once.invocations
        with self.assertRaisesRegex(ValueError,'ONE_COMPLETE_DISPATCH_NO_RETRY'):f.dispatch.run()
        self.assertEqual(f.once.invocations,calls);self.assertEqual(f.connected.context.jobs,1)

    def test_changed_input_facade_is_denied_before_authority_or_intent(self):
        f=self.fixture();f.dispatch=f.bind();f.driver.oracle_inputs.api=NS()
        with self.assertRaisesRegex(ValueError,'BOUND_DEPENDENCIES_UNCHANGED'):f.dispatch.run()
        self.assertEqual(f.once.external_calls,0);self.assertEqual(f.memory.names,[])

    def test_closed_controller_is_not_reopened_and_failed_dispatch_cannot_retry(self):
        f=self.fixture();f.dispatch=f.bind();f.pipeline.state.closed=True
        with self.assertRaisesRegex(ValueError,'SAME_OPEN_ORIGINAL_CONTROLLER_PIPELINE'):f.dispatch.run()
        f.pipeline.state.closed=False
        with self.assertRaisesRegex(ValueError,'ONE_COMPLETE_DISPATCH_NO_RETRY'):f.dispatch.run()
        self.assertEqual(f.once.external_calls,0)

    def test_original_error_and_secondary_teardown_error_preserve_primary(self):
        f=self.fixture();error=OSError('MODEL_PRIMARY');f.native_error=error;f.finish_error=ValueError('MODEL_SECONDARY')
        f.dispatch=f.bind()
        with patch.object(os,'fsync'):
            with self.assertRaises(OSError) as caught:f.dispatch.run()
        self.assertIs(caught.exception,error);self.assertTrue(f.compiled.state.finish_failed)
        self.assertTrue(f.dispatch.state.failed);self.assertEqual(f.dispatch.state.error_type,'OSError')

    def test_original_oracle_error_is_not_turned_into_adapter_success(self):
        f=self.fixture();error=ValueError('MODEL_ORACLE');f.oracle_error=error;f.dispatch=f.bind()
        with patch.object(os,'fsync'):
            with self.assertRaises(ValueError) as caught:f.dispatch.run()
        self.assertIs(caught.exception,error);self.assertFalse(f.dispatch.state.returned)
        self.assertIsNone(f.compiled.state.returned_result)

    def test_arbitrary_claim_callback_cannot_supply_a_fake_receipt(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'WHOLE_ORIGINAL_CLAIM_WRITER'):
            m.bind(f.driver,f.once,once_api,lambda row:{},f.events.append,authorize=f.once.external)
        self.assertEqual(f.memory.names,[])

    def test_guard_failure_before_authority_preserves_original_exception(self):
        f=self.fixture();f.dispatch=f.bind();error=ValueError('STOP_MODEL_PRESSURE')
        def stop():raise error
        f.driver.coordinator_boundary.seal=stop
        with self.assertRaises(ValueError) as caught:f.dispatch.run()
        self.assertIs(caught.exception,error);self.assertEqual(f.once.external_calls,0);self.assertEqual(f.memory.names,[])

    def test_owner_mismatch_does_not_create_claim_or_job(self):
        f=self.fixture();f.dispatch=f.bind();f.once.owner=(-1,-1)
        with self.assertRaisesRegex(ValueError,'SAME_OWNER_PROCESS_THREAD'):f.dispatch.run()
        self.assertEqual(f.memory.names,[]);self.assertEqual(f.connected.context.jobs,0)
