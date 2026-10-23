"""Original runner connection contracts, not actual Frame/worker evidence."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import batch_pre_go_runtime as module
import accept_case112_current_epoch as a


def audit_fixture():
    root=Path('D:/development path/hwpx-agent');checks=[]
    context=NS(active=False,attempts=0,checkpoint=lambda:checks.append('original_Frame_guard'))
    policy=module.ProcessPolicy(root)
    argv=[module.sys.executable,'-B',str(root/module.WORKER),'--probe-no-go','--zlib','--ready-handle','123','--task',module.TASK]
    return NS(root=root,checks=checks,context=context,policy=policy,argv=argv)


def emit(f,argv=None,**changes):
    args=[None,subprocess.list2cmdline(f.argv if argv is None else argv),str(f.root),None]
    for k,v in changes.items():args[int(k)]=v
    return f.policy('subprocess.Popen',tuple(args))


def terminal_fixture():
    held=NS(acquired=True,closed=True,owned=[],active_readers=set(),active_streams=0,
        close_failures=0,opened_handles=10,closed_handles=10)
    summary={'synthetic_frame':True}
    frame=NS(state='CLOSED',registered=False,registry=NS(active=None),reading=False,
        boundaries=[{'role':'before'}],held=held,raw_policy=NS(restored=True,installed=False),
        inputs={'x':dict(path='x',bytes=3,sha256='0'*64)},summary=lambda:dict(summary))
    state=NS(attempts=1,frames=[frame])
    shared=dict(metadata_registered=True,Frame_registered=True,terminal_error_seen=False,total_decoder_work_seconds=1.)
    batch=NS(parent_connection=NS(state=state),phase='BROKEN',cases=[],shared=NS(evidence=lambda:dict(shared)))
    context=NS(result=NS(assembled=NS(batch=batch)))
    adapter=NS(evidence=lambda **kwargs:{'synthetic':True})
    relay=NS(phase='NATIVE_TERMINAL',broken=False,bindings=1,evidence=lambda:{'synthetic':True})
    actual=NS(parent=state);policy=NS(attempts=1,denied=[])
    row=dict(stop_reason='BATCH_PRE_GO_DIAGNOSTIC_STOP',cleanup_confirmed=True,owned_tree_empty=True,
        worker_created=True,job_assigned=True,writer_authorized=False,product_body_observed=False,
        actual_product_child_executed=False,Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False,accepted_count_delta=0,
        state='DEFERRED_NOT_STARTED',passed_test_names=[],job_final=dict(active_processes=0,owned_processes=[]),
        source_frame=dict(summary),samples=[],elapsed_seconds=1.)
    return NS(row=row,context=context,adapter=adapter,relay=relay,actual=actual,policy=policy,frame=frame,batch=batch,shared=shared)


def validate(f):return module.validate_terminal(f.row,f.context,f.adapter,f.relay,f.actual,f.policy,a)


class PolicyTests(unittest.TestCase):
    def test_only_exact_windows_quoted_command_and_original_checkpoint_once(self):
        f=audit_fixture();f.policy.arm(f.context);emit(f)
        self.assertEqual(f.policy.attempts,1);self.assertEqual(f.checks,['original_Frame_guard']);self.assertEqual(f.policy.denied,[])

    def test_all_process_creation_denied_before_native_arm(self):
        f=audit_fixture()
        with self.assertRaises(ValueError):emit(f)
        with self.assertRaises(ValueError):f.policy.arm(f.context)
        self.assertEqual(f.checks,[])

    def test_second_process_always_denied(self):
        f=audit_fixture();f.policy.arm(f.context);emit(f)
        with self.assertRaises(ValueError):emit(f)
        self.assertEqual(f.policy.attempts,1)

    def test_original_argv_list_is_not_the_actual_windows_audit_representation(self):
        f=audit_fixture();f.policy.arm(f.context)
        with self.assertRaises(ValueError):f.policy('subprocess.Popen',(None,f.argv,str(f.root),None))
        self.assertEqual(f.policy.attempts,0)

    def test_missing_diagnostic_flags_or_foreign_worker_task_denied(self):
        for index,value in ((0,'other.exe'),(2,'other.py'),(3,'--run'),(4,'--old'),(7,'--case'),(8,'other-task')):
            f=audit_fixture();f.policy.arm(f.context);argv=list(f.argv);argv[index]=value
            with self.assertRaises(ValueError):emit(f,argv)
            self.assertEqual(f.checks,[])

    def test_noncanonical_or_unbounded_handle_denied(self):
        for handle in ('0','-1','001','123;anything','18446744073709551616','1 2'):
            f=audit_fixture();f.policy.arm(f.context);argv=list(f.argv);argv[6]=handle
            with self.assertRaises(ValueError):emit(f,argv)

    def test_foreign_executable_root_or_environment_denied(self):
        for changes in ({'0':'other.exe'},{'2':'D:/other'},{'3':{'OTHER':'VALUE'}}):
            f=audit_fixture();f.policy.arm(f.context)
            with self.assertRaises(ValueError):emit(f,**changes)
            self.assertEqual(f.checks,[])

    def test_shell_exec_startfile_or_fork_never_allowed(self):
        for event in ('os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            f=audit_fixture();f.policy.arm(f.context)
            with self.assertRaises(ValueError):f.policy(event,())

    def test_original_frame_resource_error_identity_and_no_retry(self):
        f=audit_fixture();f.policy.arm(f.context);error=ValueError('TEST_NATIVE_CPU_PRESSURE')
        def fail():raise error
        f.context.checkpoint=fail
        with self.assertRaises(ValueError) as caught:emit(f)
        self.assertIs(caught.exception,error);self.assertEqual(f.policy.attempts,0)
        f.context.checkpoint=lambda:None
        with self.assertRaises(ValueError):emit(f)

    def test_nonprocess_audit_event_untouched(self):
        f=audit_fixture();f.policy('open',());self.assertEqual(f.policy.denied,[])

    def test_used_context_or_second_arm_denied(self):
        for name,value in (('active',True),('attempts',1)):
            f=audit_fixture();setattr(f.context,name,value)
            with self.assertRaises(ValueError):f.policy.arm(f.context)
        f=audit_fixture();f.policy.arm(f.context)
        with self.assertRaises(ValueError):f.policy.arm(f.context)


class TerminalTests(unittest.TestCase):
    def test_synthetic_exact_stop_is_not_claimed_as_full_native_or_product(self):
        f=terminal_fixture();row=validate(f)
        self.assertFalse(row['actual_Native_or_product_or_queue_qualified']);self.assertFalse(row['Frame_committed'])
        self.assertEqual(row['actual_first_byte_boundaries'],1)

    def test_wrong_stop_reason_or_any_product_acceptance_not_relabelled(self):
        for key,value in (('stop_reason','OTHER_STOP'),('writer_authorized',True),('product_body_observed',True),
            ('accepted_count_delta',1),('Native_source_frame_qualified',True),('actual_product_child_executed',None),
            ('cleanup_confirmed',False),('owned_tree_empty',False)):
            f=terminal_fixture();f.row[key]=value
            with self.assertRaises(ValueError):validate(f)

    def test_passed_test_body_cannot_be_reused(self):
        f=terminal_fixture();f.row['passed_test_names']=['some-test']
        with self.assertRaises(ValueError):validate(f)

    def test_nonempty_job_or_boolean_active_count_rejected(self):
        for job in (dict(active_processes=1,owned_processes=[]),dict(active_processes=0,owned_processes=[123]),
            dict(active_processes=False,owned_processes=[])):
            f=terminal_fixture();f.row['job_final']=job
            with self.assertRaises(ValueError):validate(f)

    def test_missing_or_extra_process_or_failed_handoff_rejected(self):
        for kind in ('zero','extra','denied','broken','bindings'):
            f=terminal_fixture()
            if kind=='zero':f.policy.attempts=0
            if kind=='extra':f.policy.attempts=2
            if kind=='denied':f.policy.denied.append('subprocess.Popen')
            if kind=='broken':f.relay.broken=True
            if kind=='bindings':f.relay.bindings=0
            with self.assertRaises(ValueError):validate(f)

    def test_committed_registered_active_or_second_boundary_frame_rejected(self):
        for name,value in (('state','COMMITTED'),('registered',True),('reading',True),('boundaries',[]),
            ('boundaries',[{'role':'before'},{'role':'after'}])):
            f=terminal_fixture();setattr(f.frame,name,value)
            with self.assertRaises(ValueError):validate(f)

    def test_any_handle_reader_stream_close_failure_or_unrestored_policy_rejected(self):
        for name,value in (('closed',False),('owned',[1]),('active_readers',{1}),('active_streams',1),
            ('close_failures',1),('closed_handles',9)):
            f=terminal_fixture();setattr(f.frame.held,name,value)
            with self.assertRaises(ValueError):validate(f)
        f=terminal_fixture();f.frame.raw_policy.restored=False
        with self.assertRaises(ValueError):validate(f)

    def test_original_frame_row_drift_or_batch_acceptance_rejected(self):
        f=terminal_fixture();f.row['source_frame']={'synthetic_frame':False}
        with self.assertRaises(ValueError):validate(f)
        for name,value in (('phase','READY'),('cases',[165])):
            f=terminal_fixture();setattr(f.batch,name,value)
            with self.assertRaises(ValueError):validate(f)

    def test_shared_budget_missing_error_or_over5_not_qualified(self):
        for key,value in (('metadata_registered',False),('Frame_registered',False),('terminal_error_seen',True),
            ('total_decoder_work_seconds',5.001)):
            f=terminal_fixture();f.shared[key]=value
            with self.assertRaises(ValueError):validate(f)


class ConnectionTests(unittest.TestCase):
    def test_source_reader_uses_handoff_from_its_initial_construction(self):
        import ast
        root=Path(__file__).resolve().parents[3]
        tree=ast.parse((root/module.SELF).read_bytes())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        assignments=[n for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='q' for t in n.targets)
            and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='Reader']
        self.assertEqual(len(assignments),1);checkpoint=assignments[0].value.args[1]
        self.assertIsInstance(checkpoint,ast.Attribute);self.assertEqual(checkpoint.attr,'check')
        self.assertIsInstance(checkpoint.value,ast.Name);self.assertEqual(checkpoint.value.id,'relay')

    def test_next_diagnostic_namespace_preserves_every_original_function_body(self):
        import batch_pre_go_receipt as original
        from types import FunctionType
        selected=module.diagnostic_namespace(original)
        self.assertEqual(selected.RECEIPT,module.RECEIPT);self.assertNotEqual(selected.RECEIPT,original.RECEIPT)
        self.assertTrue(original.RECEIPT.endswith('diagnostic001-run010.v1.json'))
        for name,value in vars(original).items():
            if type(value) is FunctionType and value.__globals__ is original.project_engine.__globals__:
                changed=getattr(selected,name)
                self.assertIs(changed.__code__,value.__code__);self.assertIs(changed.__defaults__,value.__defaults__)
                self.assertIs(changed.__closure__,value.__closure__)
        def leaf():return 'implementation/p09/evidence/p09-361-case165-current-runtime-run'
        import post_product_recovery_connection_v1 as metadata
        _,proof=selected.project_engine(NS(run_owned=leaf,worker=object()),metadata.receipt_namespace)
        self.assertEqual(proof['diagnostic_receipt'],module.RECEIPT);self.assertTrue(proof['complete_code_inverse'])

    def test_actual_binding_delegates_once_and_restores_exact_original(self):
        calls=[]
        def original(reader):calls.append(reader);return 'original'
        env={'binding':original}
        def fn():return None
        from types import FunctionType
        function=FunctionType(fn.__code__,env)
        context=NS(result=NS(assembled=NS(built=NS(engine=NS(run_owned=function))),attached=NS(callback=original)))
        checks=[];relay=NS(admit_metadata=lambda r,c:checks.append((r,c)));actual=NS(active=False)
        restore=module.connect_callback(context,relay,actual);reader=object()
        self.assertEqual(env['binding'](reader),'original');self.assertEqual(calls,[reader]);self.assertEqual(checks,[(reader,actual)])
        restore();self.assertIs(env['binding'],original)

    def test_invalid_mode_before_bootstrap_or_any_heavy_work(self):
        for args in ([],['--run'],['--native'],['--diagnose-no-go','--run'],['--connect-only','--diagnose-no-go']):
            with patch.object(module.sys,'argv',['probe',*args]),patch.object(module,'bootstrap') as bootstrap:
                with self.assertRaises(ValueError):module.main()
                bootstrap.assert_not_called()

    def test_canonical_and_diagnostic_names_distinct(self):
        self.assertNotEqual(module.CANONICAL,module.RECEIPT);self.assertNotEqual(module.INTENT,module.RECEIPT)
        self.assertNotIn('current-runtime-run',module.INTENT)
