"""Small engine-connection contracts, not actual engine/Native evidence."""
import copy
from types import FunctionType,SimpleNamespace as NS
import unittest
import batch_engine_connection as module
import batch_scope_admission as admission
import current_stored_runtime_scope as scope


def pin(name):return dict(path=name,bytes=1,sha256='0'*64)


def exact(actual,expected,label):
    if type(actual) is not type(expected) or actual != expected:raise ValueError(label)


def fields(actual,expected,label):
    for k,v in expected.items():exact(actual.get(k),v,label)


class RetentionContracts(unittest.TestCase):
    def setUp(self):
        result=dict(state='PASS_BATCH_REAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE',cleanup_confirmed=True,
            GO_authorized=False,accepted_count_delta=0,product_or_worker_or_process_executed=False,
            whole_batch=dict(phase='EMPTY_BATCH_AUDITED_NOT_ACCEPTED',whole_inputs=3319,current_inputs=2898,
                preservation_inputs=421,whole_initial_complete=True,whole_final_complete=True,cases_with_original_Frame_checks=0),
            construction_source_pins=[pin(n) for n in admission.PROGRAMS])
        self.row=dict(schema_version='hwpx-agent.p09-batch-source-metadata-qualification/v1',
            qualification_only_not_native_or_execution_permission=True,preparation_report_pin=copy.deepcopy(admission.PACKAGE[3]),
            result=result)
        self.api=NS(read_exact=lambda *args:copy.deepcopy(self.row),exact=exact,fields=fields)
        self.reader=NS(fresh_pin=lambda n:pin(n))

    def test_unchanged_qualification_retained_without_whole_replay(self):
        proof=module.retained_metadata(self.reader,self.api,admission)
        self.assertEqual(proof['unchanged_programs'],8)
        self.assertFalse(proof['whole3319_or_parent_metadata_reexecuted'])
        self.assertFalse(proof['Native_or_product_qualification_reused'])

    def test_changed_program_cannot_reuse_qualification(self):
        self.reader.fresh_pin=lambda n:dict(pin(n),bytes=2)
        with self.assertRaisesRegex(ValueError,'UNCHANGED_ACTUALLY'):module.retained_metadata(self.reader,self.api,admission)

    def test_incomplete_whole_closing_is_not_reusable(self):
        self.row['result']['whole_batch']['whole_final_complete']=False
        with self.assertRaisesRegex(ValueError,'EXACT_TWO_WHOLE'):module.retained_metadata(self.reader,self.api,admission)

    def test_wrong_package_is_not_reusable(self):
        self.row['preparation_report_pin']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'EXACT_PUBLISHED'):module.retained_metadata(self.reader,self.api,admission)

    def test_go_is_not_inherited_as_permission(self):
        self.row['result']['GO_authorized']=True
        with self.assertRaisesRegex(ValueError,'ACTUAL_COMPLETED'):module.retained_metadata(self.reader,self.api,admission)

    def test_duplicate_or_subset_program_table_is_not_reusable(self):
        self.row['result']['construction_source_pins'][-1]=copy.deepcopy(self.row['result']['construction_source_pins'][0])
        with self.assertRaisesRegex(ValueError,'EXACT_EIGHT'):module.retained_metadata(self.reader,self.api,admission)


class ScopeContracts(unittest.TestCase):
    def test_add_only_named_production_module(self):
        current={'a':pin('a')};history={'b':pin('b')}
        data=NS(planned=NS(whole={**current,**history},current=current,history=history,logical={**current,**history}))
        fake_batch=NS(scope=scope,Batch=lambda whole,current,history,**kw:NS(whole=whole,current=current,history=history))
        reader=NS(pin=pin,checkpoint=lambda:None,snapshots={'unexpected':pin('unexpected')})
        module.extend_execution(data,reader,fake_batch)
        self.assertEqual(set(data.planned.current),{'a',*module.EXECUTION_INPUTS})
        self.assertEqual(data.planned.history,history)
        self.assertNotIn(module.TEST,data.planned.whole)
        self.assertNotIn(module.QUALIFICATION['path'],data.planned.whole)
        self.assertNotIn('unexpected',data.planned.whole)

    def test_policy_helper_declaration_is_closed_and_explicit(self):
        self.assertEqual(module.POLICY_HELPERS,('tools/p09/historical_receipt_batch_partition_v1.py',
            'tools/p09/phased_preservation_read_gate_v1.py','tools/p09/phased_preservation_read_gate_v2.py'))
        self.assertEqual(len(set(module.EXECUTION_INPUTS)),5)

    def test_prior_scope_projection_not_silently_reused(self):
        def body():pass
        projected=FunctionType(body.__code__,{'_batch':object()})
        runtime=NS(connect_factory=NS(__globals__={'current_input_scope':projected}))
        with self.assertRaisesRegex(ValueError,'ORIGINAL_SCOPE_NOT_PRIOR'):module.original_scope_runtime(runtime)

    def test_original_scope_recovered_without_mutation(self):
        def body():pass
        original=FunctionType(body.__code__,{})
        prior=object();runtime=NS(connect_factory=NS(__globals__={'current_input_scope':original}),current_input_scope=prior)
        recovered=module.original_scope_runtime(runtime)
        self.assertIs(recovered.current_input_scope,original)
        self.assertIs(runtime.current_input_scope,prior)

    def test_selected_logical_scope_must_match_exact_current_carriers(self):
        old=pin('old.json');carrier=pin('carrier.json');hot=pin('code.py');cold=pin('history.json')
        binding=NS(semantic_union=lambda rows,check:(rows,None),
            descriptors=lambda:[dict(semantic_original_pin=old,physical_envelope_pin=carrier)])
        def project(rows,check):
            self.assertNotIn(cold['path'],rows)
            return NS(physical_pins={carrier['path']:carrier,hot['path']:hot}),None
        binding.project=project
        data=NS(planned=NS(logical={p['path']:p for p in (old,hot,cold)},current={p['path']:p for p in (carrier,hot)}))
        selected=module.current_logical(data,binding,lambda:None,scope,exact)
        self.assertEqual(set(selected),{old['path'],hot['path']})

    def test_wrong_current_projection_is_not_a_subset_pass(self):
        binding=NS(semantic_union=lambda rows,check:(rows,None),descriptors=lambda:[],
            project=lambda *args:(NS(physical_pins={}),None))
        data=NS(planned=NS(logical={'a':pin('a')},current={'a':pin('a')}))
        with self.assertRaisesRegex(ValueError,'EXACT_NEW_CURRENT_PROJECTION'):
            module.current_logical(data,binding,lambda:None,scope,exact)


class HelperContracts(unittest.TestCase):
    def test_all_missing_helpers_reported_before_io(self):
        calls=[]
        reader=NS(pin=lambda name:calls.append(name))
        with self.assertRaises(ValueError) as raised:
            module.admit_helpers(dict(original_Native_helper_union=['a','z','b']),
                {'a':pin('a')},reader,exact)
        self.assertEqual(raised.exception.args,
            ('BATCH_ENGINE_EVERY_OBSERVED_HELPER_ALREADY_DECLARED',('b','z')))
        self.assertEqual(calls,[])

    def test_every_declared_helper_freshly_checked(self):
        calls=[]
        def fresh(name):calls.append(name);return pin(name)
        module.admit_helpers(dict(original_Native_helper_union=['a','b']),
            {n:pin(n) for n in ('a','b')},NS(pin=fresh),exact)
        self.assertEqual(calls,['a','b'])

    def test_changed_helper_fails_exact_check(self):
        with self.assertRaisesRegex(ValueError,'ACTUAL_HELPER_PIN_NOT_HIDDEN'):
            module.admit_helpers(dict(original_Native_helper_union=['a']),
                {'a':pin('a')},NS(pin=lambda n:dict(pin(n),bytes=2)),exact)


class MappingContracts(unittest.TestCase):
    def fixture(self):
        carrier=pin('carrier.json')
        descriptor=dict(semantic_original_pin=pin('semantic.json'),physical_envelope_pin=carrier)
        return NS(descriptors=lambda:[descriptor]),{carrier['path']:carrier}

    def test_all_original_current_mappings_retained(self):
        binding,current=self.fixture()
        self.assertEqual(module.current_mappings(binding,current),binding.descriptors())

    def test_preservation_or_missing_carrier_rejected_before_io(self):
        binding,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'ALL_ORIGINAL_MAPPING_CARRIERS_EXACT_CURRENT'):
            module.current_mappings(binding,{})

    def test_changed_carrier_pin_rejected(self):
        binding,current=self.fixture();current['carrier.json']=dict(current['carrier.json'],bytes=2)
        with self.assertRaisesRegex(ValueError,'ALL_ORIGINAL_MAPPING_CARRIERS_EXACT_CURRENT'):
            module.current_mappings(binding,current)

    def test_empty_mapping_table_not_a_vacuous_pass(self):
        with self.assertRaisesRegex(ValueError,'ALL_ORIGINAL_MAPPING_CARRIERS_EXACT_CURRENT'):
            module.current_mappings(NS(descriptors=lambda:[]),{})


class AccountingOrderContracts(unittest.TestCase):
    def fixture(self):
        import current_queue_successor_lossless_runtime_v4 as configuration
        import native009_full75_dispatch_connection_v1 as connector
        calls=[];binding=object()
        def whole(row):
            calls.append('whole')
            if row:raise ValueError('ORIGINAL_PRODUCT_FAILURE')
            return 'original-result'
        env=dict(whole.__globals__,prior=NS(WINDOW=NS(SECONDS=10)))
        original=FunctionType(whole.__code__,env,closure=whole.__closure__)
        checker=NS(validate_candidate=original,environment=env,graph=NS(binding=binding))
        env['validate_candidate']=original
        def connect(*args,**kwargs):return checker,{}
        isolated=FunctionType(connect.__code__,{},closure=connect.__closure__)
        names=NS(current_queue_successor_oracle=NS(connect=isolated))
        loader=NS(load=lambda *args:(names,[]))
        def accounting(*args):calls.append('accounting')
        private=FunctionType(configuration.oracle_namespace.__code__,
            dict(configuration.oracle_namespace.__globals__,validate_accounting=accounting))
        selected=NS(oracle_namespace=private,validate_accounting=accounting)
        metadata=NS()
        api,state=connector.oracle_loader('root',loader,selected,metadata,NS(),configuration.ORACLE)
        actual,_=api.load('root',[configuration.ORACLE],{'current_queue_successor_connections':metadata})
        result,_=actual.current_queue_successor_oracle.connect()
        self.assertEqual(state.loads,1)
        return result,original,calls,connector,selected,binding

    def test_original_product_checker_runs_before_additional_accounting(self):
        checker,original,calls,*_=self.fixture()
        self.assertEqual(checker.validate_candidate(False),'original-result')
        self.assertEqual(calls,['whole','accounting'])

    def test_original_failure_does_not_run_accounting_or_become_pass(self):
        checker,original,calls,*_=self.fixture()
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PRODUCT_FAILURE'):
            checker.validate_candidate(True)
        self.assertEqual(calls,['whole'])

    def test_connected_checker_retains_original_family_and_accounting(self):
        checker,original,calls,connector,configuration,binding=self.fixture()
        proof=connector.verify_checker(checker,NS(binding=binding),configuration)
        self.assertTrue(proof['existing_additional_lossless_accounting_connected'])
        self.assertIs(checker.validate_candidate.__closure__[-1].cell_contents,original)
        self.assertEqual(calls,[])


class PrivateBootstrapContracts(unittest.TestCase):
    def fixture(self):
        import sys
        from pathlib import Path
        root=Path(module.__file__).resolve().parents[2]
        return sys,root

    def test_exact_loader_and_guards_do_not_register_or_remove_modules(self):
        sys,root=self.fixture()
        before={name:value for name,value in sys.modules.items()
            if getattr(value,'__file__','') and str(root/'tools/p09') in str(value.__file__)}
        loader=module.bootstrap_loader(root)
        guards,_=loader.load(root,list(module.BOOTSTRAP[1:]),{})
        self.assertTrue(callable(guards.prepared_run_closure_v1.configure_host_policy))
        after={name:value for name,value in sys.modules.items()
            if getattr(value,'__file__','') and str(root/'tools/p09') in str(value.__file__)}
        self.assertEqual(set(before),set(after))
        self.assertTrue(all(after[name] is value for name,value in before.items()))

    def test_changed_bootstrap_pin_denied(self):
        from unittest.mock import patch
        _,root=self.fixture()
        with patch.object(module,'BOOTSTRAP',(dict(module.BOOTSTRAP[0],sha256='0'*64),)):
            with self.assertRaisesRegex(ValueError,'EXACT_BOOTSTRAP_LOADER'):module.bootstrap_loader(root)

    def test_private_late_imports_keep_default_modules_unchanged(self):
        import importlib
        import current_queue_successor_lossless_runtime_v4 as configuration
        def body():
            import batch_worker_entry
            import importlib
            return batch_worker_entry,importlib.import_module('runtime_envelope_namespace_bundle_v1')
        env=dict(body.__globals__,__name__='p09_exact_bootstrap_contract')
        original=FunctionType(body.__code__,env);admission=NS(body=original)
        worker,loader=object(),object();before=importlib.import_module
        module.private_package_imports(admission,worker,loader,configuration)
        self.assertEqual(admission.body(),(worker,loader))
        self.assertIs(admission.body.__code__,original.__code__)
        self.assertIs(importlib.import_module,before)


RAW_BATCH=None


class SharedContracts(unittest.TestCase):
    def fixture(self):
        import shared_metadata_frame_decoder_budget_v1 as shared
        class Base:pass
        class Projected(Base):pass
        owner=shared.SharedBudget()
        wrapper=shared.frame_type(Base,None,lambda *args:Projected,owner)
        class Parent(wrapper):pass
        return Parent,Base,owner,shared

    def test_exact_original_shared_layer_and_owner_allowed(self):
        self.assertTrue(module.shared_chain(*self.fixture()))

    def test_wrong_owner_denied(self):
        parent,base,owner,shared=self.fixture()
        with self.assertRaisesRegex(ValueError,'EXACT_SAME_PRIVATE'):
            module.shared_chain(parent,base,shared.SharedBudget(),shared)

    def test_arbitrary_layer_denied(self):
        parent,base,owner,shared=self.fixture()
        class Arbitrary(parent.__mro__[2]):
            def __init__(self):pass
        class Fake(Arbitrary):pass
        with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_SHARED'):
            module.shared_chain(Fake,base,owner,shared)

    def test_extra_subclass_denied(self):
        parent,base,owner,shared=self.fixture()
        class Extra(parent):pass
        with self.assertRaisesRegex(ValueError,'EXACT_SHARED_FIVE'):
            module.shared_chain(Extra,base,owner,shared)

    def test_private_projection_retains_default_batch(self):
        import batch_verification as batch
        import shared_metadata_frame_decoder_budget_v1 as shared
        original=batch.Batch.connect_parent
        selected=module.shared_batch_type(batch,RAW_BATCH,NS(shared_metadata_frame_decoder_budget_v1=shared))
        self.assertTrue(issubclass(selected,batch.Batch))
        self.assertIs(batch.Batch.connect_parent,original)

    def test_changed_original_predicate_not_silently_accepted(self):
        import batch_verification as batch
        import shared_metadata_frame_decoder_budget_v1 as shared
        wrong=RAW_BATCH.replace(b'len(frame_type.__mro__) == 4',b'len(frame_type.__mro__) == 6',1)
        self.assertNotEqual(wrong,RAW_BATCH)
        with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_BATCH_PARENT_METHOD'):
            module.shared_batch_type(batch,wrong,NS(shared_metadata_frame_decoder_budget_v1=shared))


class WorkerContracts(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        import runtime_envelope_namespace_bundle_v1 as loader
        import batch_worker_launch as worker
        self.worker=worker
        self.api=worker.worker_api(Path(module.__file__).resolve().parents[2],loader)

    def test_new_task_and_original_closed_handle_arguments(self):
        self.assertEqual(self.api.arguments(['--ready-handle','123','--task',self.worker.TASK]),123)

    def test_old_task_not_replayed(self):
        with self.assertRaisesRegex(ValueError,'EXACT_READY_HANDLE'):
            self.api.arguments(['--ready-handle','123','--task','case165-current-r009-tests'])

    def test_extra_argument_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACT_READY_HANDLE'):
            self.api.arguments(['--ready-handle','123','--task',self.worker.TASK,'--GO'])

    def test_invalid_handle_rejected(self):
        with self.assertRaisesRegex(ValueError,'HANDLE_INTEGER'):
            self.api.arguments(['--ready-handle','0','--task',self.worker.TASK])

    def test_launch_identity_and_original_functions_are_private(self):
        from pathlib import Path
        import runtime_envelope_namespace_bundle_v1 as loader
        root=Path(module.__file__).resolve().parents[2]
        libraries,_=loader.load(root,[self.worker.LAUNCH],{})
        original=libraries.native009_worker_launch_v1
        launch=self.worker.family(original,dict(ENTRY=self.worker.SELF,TASK=self.worker.TASK))
        self.assertEqual(launch.TASK,self.worker.TASK)
        self.assertEqual(launch.ENTRY,self.worker.SELF)
        self.assertIs(launch.connect.__code__,original.connect.__code__)
        self.assertIs(launch.source.__code__,original.source.__code__)
        self.assertEqual(original.TASK,'case165-current-r009-tests')
        self.assertNotEqual(original.ENTRY,launch.ENTRY)

    def test_probe_mode_is_explicit_and_default_arguments_unchanged(self):
        args=['--ready-handle','123','--task',self.worker.TASK]
        self.assertEqual(self.worker.probe_invocation(args),(False,args))
        self.assertEqual(self.worker.probe_invocation(['--probe-no-go',*args]),(True,args))
        with self.assertRaisesRegex(ValueError,'EXACT_READY_HANDLE'):
            self.api.arguments(self.worker.probe_invocation(['--probe-no-go','--probe-no-go',*args])[1])

    def test_probe_input_accepts_only_real_eof(self):
        import io
        self.assertEqual(self.worker.NoGoInput(io.StringIO('')).readline(),'')
        for value in ('P149_GO\n','x\n','\n'):
            with self.assertRaisesRegex(ValueError,'NO_GO_PROBE_REQUIRES_REAL_EOF'):
                self.worker.NoGoInput(io.StringIO(value)).readline()

    def test_probe_all_process_creation_events_denied(self):
        for event in ('subprocess.Popen','os.system','os.startfile'):
            with self.assertRaisesRegex(ValueError,'NO_GO_PROBE_PROCESS_DENIED'):
                self.worker.deny_probe_process(event,())
        self.worker.deny_probe_process('open',())


class ReadinessProbeContracts(unittest.TestCase):
    def fixture(self):
        import sys
        from pathlib import Path
        import probe_batch_worker_readiness as probe
        import batch_worker_launch as worker
        root=Path(module.__file__).resolve().parents[2]
        command=[sys.executable,'-B',str(root/worker.SELF),'--ready-handle','123','--task',worker.TASK]
        return probe,worker,root,command

    def test_diagnostic_flag_is_only_command_change(self):
        probe,worker,root,command=self.fixture()
        self.assertEqual(probe.diagnostic_command(command,root,worker),[*command[:3],'--probe-no-go',*command[3:]])

    def test_wrong_task_and_malformed_commands_denied(self):
        probe,worker,root,command=self.fixture()
        for bad in ([],command[:4],command+['--GO'],command[:-1]+['case165-current-r009-tests'],
            command[:4]+['0']+command[5:]):
            with self.assertRaisesRegex(ValueError,'ONE_EXACT_PRODUCTION_LAUNCH'):
                probe.diagnostic_command(bad,root,worker)

    def test_child_errors_do_not_expose_arbitrary_text(self):
        probe,*_=self.fixture()
        self.assertEqual(probe.closed_child_error('ValueError: SAFE_CODE')['error_code'],'SAFE_CODE')
        row=probe.closed_child_error('ValueError: private_token=value')
        self.assertIsNone(row['error_code'])
        self.assertFalse(row['raw_log_preserved_or_printed'])

    def test_job_handle_closed_even_when_termination_fails(self):
        probe,worker,root,_=self.fixture()
        calls=[]
        def failed_limits(job):raise ValueError('INITIAL_READBACK_FAILURE')
        windows=NS(job=lambda:'owned-job',verify_job_limits=failed_limits,
            k=NS(TerminateJobObject=lambda *args:calls.append('terminate') or False,
                CloseHandle=lambda job:calls.append('close') or True))
        row={}
        with self.assertRaisesRegex(ValueError,'OWNED_JOB_TERMINATE'):
            probe.run(root,None,None,None,NS(Windows=lambda:windows),worker,
                None,None,None,None,None,row)
        self.assertEqual(calls,['terminate','close'])
        self.assertTrue(row['cleanup']['job_handle_closed'])
        self.assertIsNone(row['cleanup']['active_processes'])
