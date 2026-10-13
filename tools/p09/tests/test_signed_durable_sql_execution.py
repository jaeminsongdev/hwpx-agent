"""Current caller composition mocks; original cancellation/backend suite retained."""
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import run_signed_durable_sql_probe as s

NONCE='12345678-1234-4234-8234-123456789abc'
RUN='87654321-4321-4321-8321-cba987654321'


class DurableSQLExecutionTests(unittest.TestCase):
    def call(self):
        return (s.contract.BUILD_PIN['path'],'implementation/p09/evidence/p09-146-corpus-consumer-run07.v1.json',
                0,'original','unchanged','approval')

    def event(self):
        obj=SimpleNamespace(name='fixture-event',closed=False)
        obj.close=Mock(side_effect=lambda:setattr(obj,'closed',True));return obj

    def test_current_worker_original_supervisor_limits_and_finalization(self):
        event=self.event();parent=dict(state='fixture-parent');reader,resources=Mock(),Mock()
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s,'supervise_owned_call',return_value=parent) as supervise, \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')) as finalize:
            result=s.execute(self.call(),resources,reader)
        argv=supervise.call_args.args[0]
        self.assertEqual(argv[3:],['--worker',NONCE,event.name,'7','0','original','unchanged'])
        self.assertEqual(supervise.call_args.kwargs,dict(maximum_seconds=690,grace_seconds=135))
        self.assertIs(supervise.call_args.args[1],resources);self.assertIs(supervise.call_args.args[2],event)
        self.assertTrue(parent['parent_event_closed'])
        finalize.assert_called_once_with(parent,NONCE,'approval',self.call(),resources,reader,None)
        self.assertFalse(result['retained_owned_ciphertext_root']['created'])
        self.assertEqual(result['provided_driver_adapter']['guard_count_delta'],[842,845])

    def test_close_failure_does_not_skip_owned_intent_finalization(self):
        event=self.event();event.close.side_effect=OSError('PRIVATE_FIXTURE');parent={}
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s,'supervise_owned_call',return_value=parent), \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')) as finalize:
            s.execute(self.call(),Mock(),Mock())
        finalize.assert_called_once();self.assertFalse(parent['parent_event_closed'])
        self.assertNotIn('PRIVATE_FIXTURE',parent['parent_event_close_error_code'])

    def test_root_recovered_only_from_current_owned_intent_run(self):
        event=self.event();parent={};expected=s.c.ROOT/s.root.root_name(RUN)
        path=SimpleNamespace(exists=Mock(side_effect=[False,True,True,True]))
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=path), \
                patch.object(s.subject.ownership,'load_intent',return_value=dict(intent=dict(run_id=RUN))), \
                patch.object(s.subject,'scoped_path',return_value=path), \
                patch.object(s.shutil,'which',return_value='fixture-docker'), \
                patch.object(s,'supervise_owned_call',return_value=parent), \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')), \
                patch.object(s.root.OwnedRootHolder,'manifest',autospec=True,return_value=dict(created=True)) as manifest:
            s.execute(self.call(),Mock(),Mock())
        holder=manifest.call_args.args[0];self.assertEqual(holder.run,RUN);self.assertIs(holder.root,path)
        self.assertEqual(holder.crypto,str(s.c.ROOT/s.contract.build.executable_name(5)))

    def component(self):
        execution=dict(state='ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE',
            original_receipt_pin=dict(path='fixture-receipt'),retained_owned_ciphertext_root=dict(created=True,
            owner_exact=True,run_id=RUN,retained=True,files=[{},{}],total_bytes=1000,OS_ACL_qualified=False,
            independent_restart_or_key_custody_qualified=False))
        receipt=dict(compiled_build_binding=dict(scheme='p150_current_runtime_r05',receipt_pin=s.contract.BUILD_PIN),
            product_executable_pin=dict(path=s.contract.build.executable_name(5)),
            product_probe=dict(result=dict(checks=s.driver.required_checks(),failed_stage=None,durable_blob_store_qualified=False)),
            durable_blob_store_qualified=False,P09_gate='OPEN',product_complete=False,run_id=RUN)
        return execution,receipt

    def test_component_scope_does_not_promote_restart_custody_native_or_all36(self):
        execution,receipt=self.component();row=s.verify_component(execution,SimpleNamespace(json=lambda n:receipt))
        self.assertTrue(row['current_signed_SQL_case_qualified'])
        for key in ('all_36_sources_qualified','full_durable_DS01_DS09_qualified','production_key_custody_qualified',
                    'independent_process_restart_qualified','PC_freeze_resolved'):self.assertFalse(row[key])

    def test_incomplete_checks_old_build_or_durable_promotion_rejected(self):
        execution,receipt=self.component()
        for scope,key,value in (('result','checks',s.driver.original.ROOT_CHECKS),('binding','scheme','current_r4'),
                ('receipt','durable_blob_store_qualified',True),('receipt','P09_gate','CLOSED')):
            changed=copy.deepcopy(receipt);target={'result':changed['product_probe']['result'],
                'binding':changed['compiled_build_binding'],'receipt':changed}[scope];target[key]=value
            with self.assertRaises(ValueError):s.verify_component(execution,SimpleNamespace(json=lambda n:changed))

    def test_root_missing_wrong_UUID_or_unproven_qualification_rejected(self):
        execution,receipt=self.component()
        for key,value in (('created',False),('owner_exact',False),('run_id',NONCE),('OS_ACL_qualified',True),
                           ('independent_restart_or_key_custody_qualified',True),('files',[])):
            changed=copy.deepcopy(execution);changed['retained_owned_ciphertext_root'][key]=value
            with self.assertRaises(ValueError):s.verify_component(changed,SimpleNamespace(json=lambda n:receipt))

    def test_existing_receipt_never_reused(self):
        with patch.object(s.subject,'scoped_path',side_effect=ValueError('SQL_EXECUTION_FRESH_PATH_REQUIRED')):
            with self.assertRaises(ValueError):s.arguments(7,0,'original','unchanged')

    def test_worker_closes_preparation_reader_and_event_before_closed_protocol(self):
        event=self.event();resources=SimpleNamespace(admit=Mock(),reason=None);reader=Mock();made=Mock()
        row=dict(child_event_closed=False);trace=[]
        reader.finish.side_effect=lambda:trace.append('preparation-finish')
        def call(*a):trace.append('driver-call');return row
        with patch.object(s.CancelEvent,'open',return_value=event),patch.object(s,'SQLRuntimeResources',return_value=resources), \
                patch.object(s,'LiveSQLReader',return_value=reader),patch.object(s.driver,'make_driver',return_value=(made,None)), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s.subject,'scoped_path'),patch.object(s.subject,'journalled_driver_call',side_effect=call) as called, \
                patch.object(s,'finish_watcher',return_value=True),patch.object(s.subject,'decode_worker') as decode, \
                patch('builtins.print'):
            self.assertEqual(s.worker(NONCE,event.name,'7','0','original','unchanged'),0)
        self.assertEqual(trace,['preparation-finish','driver-call']);self.assertTrue(row['child_event_closed'])
        called.assert_called_once_with(made,self.call(),event,NONCE,'approval');decode.assert_called_once()


if __name__=='__main__':unittest.main()
