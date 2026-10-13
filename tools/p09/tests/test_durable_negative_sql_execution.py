"""Twelve current39 composition contracts, never an actual SQL/backend proof."""
import base64
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import run_durable_negative_sql_probe as s

NONCE='12345678-1234-4234-8234-123456789abc'
RUN='87654321-4321-4321-8321-cba987654321'


class CurrentSQLExecutionTests(unittest.TestCase):
    def call(self):
        return (s.contract.BUILD_PIN['path'],'implementation/p09/evidence/p09-146-corpus-consumer-run08.v1.json',
            0,'original','unchanged','approval')

    def event(self):
        event=SimpleNamespace(name='fixture-event',closed=False)
        event.close=Mock(side_effect=lambda:setattr(event,'closed',True));event.request=Mock();event.is_set=Mock(return_value=True)
        return event

    def test_closed_selection_and_fresh_receipt(self):
        with patch.object(s.subject,'scoped_path') as scoped:
            self.assertEqual(s.arguments(8,0,'original','unchanged'),self.call())
            scoped.assert_called_once_with(self.call()[1],fresh=True)
            for run,index,mode,expected in ((True,0,'original','unchanged'),(8,True,'original','unchanged'),
                    (0,0,'original','unchanged'),(8,36,'original','unchanged'),(8,0,'original','changed')):
                with self.assertRaises(ValueError):s.arguments(run,index,mode,expected)
        with patch.object(s.subject,'scoped_path',side_effect=ValueError('SQL_EXECUTION_FRESH_PATH_REQUIRED')):
            with self.assertRaises(ValueError):s.arguments(8,0,'original','unchanged')

    def test_same_supervisor_limits_and_owned_finalization(self):
        event=self.event();parent={};reader,resources=Mock(),Mock()
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s,'supervise_owned_call',return_value=parent) as supervise, \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')) as finalize:
            row=s.execute(self.call(),resources,reader)
        self.assertEqual(supervise.call_args.args[0][3:],['--worker',NONCE,event.name,'8','0','original','unchanged'])
        self.assertEqual(supervise.call_args.kwargs,dict(maximum_seconds=690,grace_seconds=135))
        self.assertEqual(supervise.call_args.args[0][2],str(s.c.ROOT/s.SELF))
        finalize.assert_called_once_with(parent,NONCE,'approval',self.call(),resources,reader,None)
        self.assertTrue(parent['parent_event_closed']);event.request.assert_not_called()
        self.assertEqual(row['provided_driver_adapter']['guard_count_delta'],[842,846])
        self.assertEqual(row['provided_driver_adapter']['exact_required_check_count'],39)

    def test_pre_cancel_signal_before_worker_not_limit_weakening(self):
        event=self.event();trace=[];event.request.side_effect=lambda:trace.append('signal')
        def supervise(*a,**kw):trace.append('supervise');return {}
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s,'supervise_owned_call',side_effect=supervise), \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')):
            row=s.execute(self.call(),Mock(),Mock(),pre_cancel=True)
        self.assertEqual(trace,['signal','supervise']);self.assertTrue(row['pre_cancel_signal_sent_before_supervision'])
        event.is_set.assert_called_once()
        with self.assertRaises(ValueError):s.execute(self.call(),Mock(),Mock(),pre_cancel=1)

    def test_event_close_failure_still_finalizes_owned_intent(self):
        event=self.event();event.close.side_effect=OSError('PRIVATE_FIXTURE_VALUE');parent={}
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s,'supervise_owned_call',return_value=parent), \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')) as finalize:
            s.execute(self.call(),Mock(),Mock())
        finalize.assert_called_once();self.assertFalse(parent['parent_event_closed'])
        self.assertNotIn('PRIVATE_FIXTURE_VALUE',parent['parent_event_close_error_code'])

    def test_root_recovery_only_exact_journal_UUID_current_suffix(self):
        event=self.event();path=SimpleNamespace(exists=Mock(side_effect=[False,True,True,True]))
        with patch.object(s.uuid,'uuid4',return_value=NONCE),patch.object(s.CancelEvent,'create',return_value=event), \
                patch.object(s.subject.ownership,'journal_path',return_value=path), \
                patch.object(s.subject.ownership,'load_intent',return_value=dict(intent=dict(run_id=RUN))), \
                patch.object(s.subject,'scoped_path',return_value=path),patch.object(s.shutil,'which',return_value='fixture-docker'), \
                patch.object(s,'supervise_owned_call',return_value={}), \
                patch.object(s.subject,'finalize_owned_call',return_value=dict(state='FAILED_NOT_ACCEPTED')), \
                patch.object(s.root.OwnedRootHolder,'manifest',autospec=True,return_value=dict(created=True)) as manifest:
            s.execute(self.call(),Mock(),Mock())
        holder=manifest.call_args.args[0];self.assertEqual(holder.run,RUN);self.assertIs(holder.root,path)
        self.assertEqual(holder.crypto,str(s.c.ROOT/s.contract.build.executable_name(1)))

    def component(self):
        execution=dict(state='ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE',
            original_receipt_pin=dict(path='fixture'),retained_owned_ciphertext_root=dict(created=True,owner_exact=True,
                run_id=RUN,retained=True,files=[{},{}],total_bytes=1000,OS_ACL_qualified=False,
                independent_restart_or_key_custody_qualified=False))
        receipt=dict(compiled_build_binding=dict(scheme=s.contract.SCHEME,receipt_pin=s.contract.BUILD_PIN,
            compiled_source_count=846,required_check_count=39),product_executable_pin=dict(path=s.contract.build.executable_name(1)),
            product_probe=dict(result=dict(checks=s.driver.required_checks(),failed_stage=None,durable_blob_store_qualified=False)),
            durable_blob_store_qualified=False,P09_gate='OPEN',product_complete=False,run_id=RUN)
        return execution,receipt

    def test_one_case_scope_not_full_DS_native_custody_or_all36(self):
        execution,receipt=self.component();row=s.verify_component(execution,SimpleNamespace(json=lambda n:receipt))
        self.assertTrue(row['current_signed_SQL_case_with_private_DS06_controls_qualified'])
        for key in ('all_36_sources_qualified','full_durable_DS01_DS09_qualified','production_key_custody_qualified',
                'independent_process_restart_qualified','PC_freeze_resolved'):self.assertFalse(row[key])

    def test_31_checks_stale_receipt_or_phase_upgrade_denied(self):
        execution,receipt=self.component()
        for scope,key,value in (('result','checks',s.driver.prior.required_checks()),('binding','scheme','p150_current_runtime_r05'),
                ('binding','compiled_source_count',845),('binding','required_check_count',31),
                ('receipt','durable_blob_store_qualified',True),('receipt','P09_gate','CLOSED')):
            changed=copy.deepcopy(receipt);target={'result':changed['product_probe']['result'],
                'binding':changed['compiled_build_binding'],'receipt':changed}[scope];target[key]=value
            with self.assertRaises(ValueError):s.verify_component(execution,SimpleNamespace(json=lambda n:changed))

    def test_missing_or_foreign_root_proof_never_product_success(self):
        execution,receipt=self.component()
        for key,value in (('created',False),('owner_exact',False),('run_id',NONCE),('files',[]),
                ('OS_ACL_qualified',True),('independent_restart_or_key_custody_qualified',True)):
            changed=copy.deepcopy(execution);changed['retained_owned_ciphertext_root'][key]=value
            with self.assertRaises(ValueError):s.verify_component(changed,SimpleNamespace(json=lambda n:receipt))

    def test_worker_reader_finish_event_close_before_closed_protocol(self):
        event=self.event();resources=SimpleNamespace(admit=Mock(),reason=None);reader=Mock();made=Mock();trace=[]
        reader.finish.side_effect=lambda:trace.append('finish')
        def call(*args):trace.append('call');return dict(child_event_closed=False)
        with patch.object(s.CancelEvent,'open',return_value=event),patch.object(s,'SQLRuntimeResources',return_value=resources), \
                patch.object(s,'LiveSQLReader',return_value=reader),patch.object(s,'make_driver',return_value=(made,None)), \
                patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s.subject,'scoped_path'),patch.object(s.subject,'journalled_driver_call',side_effect=call) as called, \
                patch.object(s,'finish_watcher',return_value=True),patch.object(s.subject,'decode_worker') as decode,patch('builtins.print'):
            self.assertEqual(s.worker(NONCE,event.name,'8','0','original','unchanged'),0)
        self.assertEqual(trace,['finish','call']);called.assert_called_once_with(made,self.call(),event,NONCE,'approval')
        self.assertTrue(event.closed);decode.assert_called_once()

    def cancelled(self):
        limits=dict(verified=True,cpu_hard_cap_machine_percent=6.25,affinity_mask=1,priority_class=16384,
            active_process_limit=16,kill_on_close=True,breakaway_disabled=True)
        accounted=dict(state='ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS',driver_return_code=None,
            driver_error_code=s.CANCEL_REASON,cooperative_resource_count=1,cooperative_resource_stop_reason=s.CANCEL_REASON,
            cooperative_resource_stop_latched=True,original_resource_type_inherited=True,original_driver_dependencies_restored=True,
            reader_count=0,source_final_hash_completed=False)
        worker=dict(child_event_closed=True,journal_write_count=0,journal_pin=None,accounted_call=accounted)
        parent=dict(state='OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE',worker_result=worker,forced_termination=False,
            parent_event_closed=True,pipe_cleanup_confirmed=True,owned_job_profile=dict(limits_readback=limits,
                owned_tree_empty=True,cleanup_confirmed=True,job_handle_closed=True,worker_created=True,job_assigned=True,
                target_authorized=True,last_job_accounting=dict(active_processes=0)))
        return dict(state='ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE',supervisor=parent,parent_nonce=NONCE,
            pre_cancel_signal_sent_before_supervision=True,journal_pin=None,fallback_cleanup=None,original_receipt_pin=None,
            backend_container_cleanup_confirmed=None,retained_owned_ciphertext_root=dict(created=False))

    def test_pre_cancel_requires_original_stop_and_no_backend_not_final_hash_upgrade(self):
        row=self.cancelled()
        with patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s.subject,'scoped_path',return_value=SimpleNamespace(exists=lambda:False)):
            proof=s.verify_pre_cancelled(row,self.call());self.assertFalse(proof['live_SQL_cancellation_and_backend_cleanup_qualified'])
            self.assertTrue(proof['original_final_hash_not_promoted'])
            for key,value in (('reader_count',1),('source_final_hash_completed',True),('driver_return_code',0),
                    ('driver_error_code',None),('cooperative_resource_stop_latched',False)):
                changed=copy.deepcopy(row);changed['supervisor']['worker_result']['accounted_call'][key]=value
                with self.subTest(key=key),self.assertRaises(ValueError):s.verify_pre_cancelled(changed,self.call())
            changed=copy.deepcopy(row);changed['supervisor']['owned_job_profile']['target_authorized']=False
            with self.assertRaises(ValueError):s.verify_pre_cancelled(changed,self.call())

    def test_precancel_backend_or_receipt_presence_not_clean_success(self):
        row=self.cancelled()
        with patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:False)), \
                patch.object(s.subject,'scoped_path',return_value=SimpleNamespace(exists=lambda:False)):
            for key,value in (('journal_pin',{}),('fallback_cleanup',{}),('original_receipt_pin',{}),
                    ('backend_container_cleanup_confirmed',True)):
                with self.subTest(key=key),self.assertRaises(ValueError):
                    s.verify_pre_cancelled(dict(row,**{key:value}),self.call())
            changed=copy.deepcopy(row);changed['retained_owned_ciphertext_root']['created']=True
            with self.assertRaises(ValueError):s.verify_pre_cancelled(changed,self.call())
        for journal,receipt in ((True,False),(False,True)):
            with patch.object(s.subject.ownership,'journal_path',return_value=SimpleNamespace(exists=lambda:journal)), \
                    patch.object(s.subject,'scoped_path',return_value=SimpleNamespace(exists=lambda:receipt)):
                with self.assertRaises(ValueError):s.verify_pre_cancelled(row,self.call())

    def test_closed_driver_DI_retains_policy_and_adds_current_caller_sources(self):
        raw=(s.c.ROOT/s.contract.DRIVER).read_bytes();pin=dict(path=s.contract.DRIVER,bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
        reader=SimpleNamespace(json=lambda n:dict(files=[pin]),pin=lambda n:{k:pin[k] for k in ('path','bytes','sha256')})
        made,holder=s.make_driver(reader,NONCE)
        binding=dict(scheme=s.contract.SCHEME,actual_SQL_qualified=False,receipt_pin=s.contract.BUILD_PIN,
            closing_audit_pin=s.contract.CLOSING_PIN,compiled_source_count=846,current_Rust_input_count=785,
            required_check_count=39,helper_paths=[])
        self.assertTrue(set(s.SOURCES)<=set(made.consumer_sources(binding)))
        self.assertEqual(made.ROOT_CHECKS,s.driver.required_checks());self.assertIsNone(holder.root)
        self.assertEqual(made.resource_policy(),s.driver.prior.original.resource_policy())


if __name__=='__main__':unittest.main()
