"""Entry contracts with explicit synthetic IO/guards/terminal state, not evidence."""
import base64
import hashlib
import json
import os
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_product_entry as m
import packed_receipt_json as packed
import test_native011_product_dispatch as dispatch_fixture


class Tests(unittest.TestCase):
    def fixture(self,*,execute=True,authority=True):
        f=dispatch_fixture.Tests().fixture(authority=authority)
        f.publications=[];f.guard_calls=[];f.guard_cleanup=True;f.pack_error=None;f.publish_error_at=None;f.cleanup=True
        f.api=NS(packed=packed)
        class Guard:
            def __init__(self):self.cleanup=False
            def acquire(self):f.guard_calls.append('acquire')
            def check(self,**kwargs):
                if f.pack_error is not None:raise f.pack_error
            def close(self):self.cleanup=f.guard_cleanup;f.guard_calls.append('close')
        def publish(root,path,row,a):
            if f.publish_error_at==len(f.publications):raise OSError('MODEL_EXCLUSIVE_PART_FAILURE')
            raw=(json.dumps(row,ensure_ascii=True,indent=2)+'\n').encode()
            f.publications.append((path,row));return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        f.publisher=NS(publish=publish)
        original_verify=f.route.verify
        def verify(*args,**kwargs):
            result=original_verify(*args,**kwargs)
            f.route.phase='CHECKED_NOT_ACCEPTED';f.route.guard=None;f.route.cleanup=True
            f.route.oracle_attempts=f.route.guard_creations=1
            return result
        f.route.verify=verify;f.route.phase='ORIGINAL'
        f.route._terminal=lambda:(f.batch,f.source.frame);f.route._checker=lambda:None
        f.pipeline.cleanup=lambda:f.driver.closed and f.cleanup
        f.driver.parent_handoff=NS(state=NS(cleanup_confirmed=True))
        audit=dict(original_deny_registrations=1,component_connections=1,factory_attempts=1,allowed_Popen_events=1,
            original_process_policy_arm_attempts=1,original_policy_Popen_attempts=1,denied_Popen_events=0,
            original_denied_events=0,scope_active=False,failed=False,original_private_dependency_restored=True,restore_error_types=[])
        f.driver.product_audit.evidence=lambda:dict(audit)
        class Base:
            def __init__(self):self.__dict__.update(vars(f.driver));f.driver=self
            @property
            def cleanup(self):return f.cleanup
            def factory(self,stage):
                f.guard_calls.append(stage);return Guard()
            def run(self,*args,**kwargs):
                self.product_dispatch=f.bind()
                return dict(state='PASS_MODEL_CONSTRUCTION_NOT_EXECUTION')
            def close(self):
                self.closed=True;f.pipeline.state.closed=True
                # Synthetic terminal witness only; actual route._terminal is
                # not replaced in the product implementation.
                f.source.frame.state='COMMITTED';f.source.frame.registered=False
                f.source.frame.held.closed=True;f.source.frame.owned_cleanup_seen=True
            def finish(self,root,row,publisher,a):
                row.update(state='PASS_MODEL_CONSTRUCTION_PLACEHOLDER',Frame_instances=0,actual_product_executed=False)
        f.driver=m.driver_type(Base,f.once,authorize=f.once.external,execute=execute)()
        f.row={}
        def run():
            with patch.object(os,'fsync'):return f.driver.run()
        f.run=run
        f.finish=lambda:f.driver.finish(object(),f.row,f.publisher,f.api)
        return f

    def test_product_mode_without_callback_or_with_authority_flags_never_constructs(self):
        for options in (dict(execute=True),dict(execute=True,authorize=True),dict(execute=1)):
            with self.assertRaises(ValueError):m.entry(NS(construct=lambda **kwargs:self.fail('NO_CONSTRUCTION')),**options)

    def test_connection_api_passes_only_new_instance_none_dependency_and_fixed_output(self):
        calls=[]
        def construct(**kwargs):calls.append(kwargs);return 17
        self.assertEqual(m.entry(NS(construct=construct)),17)
        self.assertIsNone(calls[0]['authorize']);self.assertEqual(calls[0]['output'],m.CONSTRUCTION)
        self.assertTrue(callable(calls[0]['wrap']))

    def test_cli_product_go_retry_and_implicit_modes_rejected_before_bootstrap(self):
        for args in ([],['--run-product'],['--go'],['--retry'],['--connect-only','--go']):
            with patch.object(sys,'argv',['entry.py',*args]):
                with self.assertRaisesRegex(ValueError,'CLI_CONNECTION_ONLY'):m.main()

    def test_default_connection_never_executes_claim_or_creates_publication_owner(self):
        f=self.fixture(execute=False,authority=None);f.run();f.driver.close();f.finish()
        self.assertEqual(f.row['state'],'PASS_NATIVE011_ENTRY_CONNECTION_NOT_EXECUTION')
        self.assertEqual(f.guard_calls,[]);self.assertEqual(f.publications,[]);self.assertEqual(f.memory.names,[])
        self.assertEqual(f.once.invocations,0);self.assertEqual(f.once.external_calls,0)
        self.assertFalse(f.row['actual_product_executed']);self.assertEqual(f.row['Frame_instances'],0)

    def test_complete_original_model_return_is_published_losslessly_only_after_close(self):
        f=self.fixture();f.run();expected=json.loads(json.dumps(f.driver.entry_value))
        f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('PASS_NATIVE011_COMPLETE_PRODUCT'))
        self.assertTrue(f.row['actual_product_executed']);self.assertEqual(f.row['Frame_instances'],1)
        self.assertEqual(f.row['accepted_count_delta'],0);self.assertFalse(f.row['official_queue_advanced'])
        raw=b''.join(base64.b64decode(row['base64']) for _,row in f.publications)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),f.row['product_entry_result_artifact']['sha256'])
        carrier,stats=json.loads(raw);self.assertEqual(packed.unpack(carrier,lambda:None),expected)
        self.assertEqual(f.guard_calls,['whole_metadata_preflight','acquire','close'])
        self.assertIsNone(f.driver.entry_value);self.assertTrue(f.row['cleanup_confirmed'])

    def test_original_native_error_preserved_despite_terminal_no_result_error(self):
        f=self.fixture();error=OSError('MODEL_PRIMARY');f.native_error=error;f.finish_error=ValueError('MODEL_TEARDOWN')
        with self.assertRaises(OSError) as caught:f.run()
        self.assertIs(caught.exception,error);f.driver.close();f.finish()
        self.assertEqual(f.row['error_type'],'OSError');self.assertEqual(f.row['error_code'],'MODEL_PRIMARY')
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertEqual(f.guard_calls,[])
        self.assertIsNone(f.driver.entry_value)

    def test_failed_original_process_with_frame_does_not_claim_body_was_not_executed(self):
        f=self.fixture();f.source.fault.body=True
        with self.assertRaises(ValueError):f.run()
        f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertEqual(f.row['Frame_instances'],1)
        self.assertIsNone(f.row['actual_product_executed']);self.assertEqual(f.publications,[])

    def test_incomplete_original_oracle_never_starts_publication_or_becomes_pass(self):
        f=self.fixture();f.run();f.route.oracle_attempts=0;f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertEqual(f.guard_calls,[])
        self.assertFalse(f.row['product_entry']['original_lifecycle_and_oracle_verified'])

    def test_wrong_canonical_namespace_rejected_without_publication(self):
        f=self.fixture();f.run();f.driver.entry_value['canonical_receipt_pin']['path']='diagnostic.json'
        f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertEqual(f.publications,[])

    def test_publication_guard_failure_preserves_original_result_fact_but_no_overall_pass(self):
        f=self.fixture();f.run();f.pack_error=ValueError('STOP_MODEL_PUBLICATION_CPU');f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertTrue(f.row['actual_product_executed'])
        self.assertTrue(f.row['product_entry']['original_lifecycle_and_oracle_verified'])
        self.assertFalse(f.row['product_entry']['complete_original_lifecycle_and_publication_verified'])
        self.assertEqual(f.guard_calls[-1],'close');self.assertIsNone(f.driver.entry_value)

    def test_failed_publication_cleanup_is_not_hidden_by_base_cleanup(self):
        f=self.fixture();f.run();f.guard_cleanup=False;f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertFalse(f.row['cleanup_confirmed'])
        self.assertTrue(f.publications);self.assertIsNone(f.driver.entry_value)

    def test_large_lossless_result_parts_are_bounded_and_partial_outputs_never_retried(self):
        f=self.fixture();f.run()
        f.driver.entry_value['model_entropy']=hashlib.shake_256(b'bounded-model').digest(230000).hex()
        f.publish_error_at=1;f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertEqual(len(f.publications),1)
        artifact=f.row['product_entry_result_artifact'];self.assertEqual(len(artifact['parts']),1)
        self.assertEqual(len(artifact['attempted_paths']),2);self.assertEqual(f.publications[0][1]['bytes'],m.PART_BYTES)
        with self.assertRaisesRegex(ValueError,'ONE_TERMINAL_PUBLICATION_NO_RETRY'):f.finish()
        self.assertEqual(len(f.publications),1);self.assertIsNone(f.driver.entry_value)

    def test_failed_base_cleanup_never_turns_completed_lifecycle_into_product_pass(self):
        f=self.fixture();f.run();f.cleanup=False;f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'));self.assertFalse(f.row['cleanup_confirmed'])
        self.assertEqual(f.guard_calls,[]);self.assertEqual(f.publications,[])

    def test_caught_duplicate_entry_call_cannot_be_erased_by_successful_first_return(self):
        f=self.fixture();f.run()
        try:f.run()
        except ValueError:pass
        f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'))
        self.assertEqual(f.row['error_code'],'NATIVE011_PRODUCT_ENTRY_ONE_ENTRY_NO_RETRY')
        self.assertEqual(f.publications,[]);self.assertIsNone(f.driver.entry_value)

    def test_caught_reentrant_entry_from_initial_authority_callback_cannot_return_success(self):
        original=dispatch_fixture.once_api.Once
        def authority():
            try:f.driver.run()
            except ValueError:pass
            return True
        def fresh_once(checkpoint,*,authorize=None):return original(checkpoint,authorize=authority)
        # A fresh original Once gets this callback at creation. No production
        # class body or existing authority origin is changed by the model.
        with patch.object(dispatch_fixture.once_api,'Once',fresh_once):f=self.fixture()
        with self.assertRaises(ValueError):f.run()
        f.driver.close();f.finish()
        self.assertTrue(f.row['state'].startswith('FAILED_'))
        self.assertEqual(f.row['error_code'],'NATIVE011_PRODUCT_ENTRY_ONE_ENTRY_NO_RETRY')
        self.assertEqual(f.publications,[]);self.assertIsNone(f.driver.entry_value)
