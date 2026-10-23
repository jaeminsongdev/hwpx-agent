import io
from pathlib import Path
import subprocess
from types import FunctionType, SimpleNamespace as NS
import unittest

import native011_product_parent_handoff as m
import native011_product_source_handoff as transfer
import native009_parent_launch_v1 as parent
import native009_worker_launch_v1 as launch
import batch_worker_launch as families
import worker_readiness_v1 as protocol
import worker_readiness_connection_v1 as readiness
import strict_product_window_connection_v1 as strict
import strict_product_window_v1 as window
import post_product_recovery_window_v1 as recovery
import test_native011_product_source_handoff as source_fixture


class Tests(unittest.TestCase):
    def fixture(self,*,authorize=None):
        f=source_fixture.Tests().fixture();journal=[];fault=NS(job_member=True,guard=False,body=False)
        required={m.ENTRY:dict(path=m.ENTRY,bytes=2,sha256='0'*64)}
        required.update({f'helper{i}.py':dict(path=f'helper{i}.py',bytes=2,sha256='0'*64) for i in range(201)})
        f.flags.clear();f.flags.update({1001+i:0 for i in range(202)})
        held=f.frame.held;held.owned=[(name,None,1001+i,False) for i,name in enumerate(required)]
        held.stream_read_counts={name:1 for name in required}
        class Base:pass
        class Middle(Base):pass
        class Shared(Middle):pass
        class Frame(Shared):pass
        frame=Frame();frame.__dict__.update(vars(f.frame));frame.boundaries=[{'model_only':True}]
        def check():
            journal.append('frame-check')
            if fault.guard:raise ValueError('MODEL_GUARD_STOP')
        frame.check=check
        state=NS(frames=[],attempts=0)
        class Event:
            handle=33
            def inheritable(self,value):journal.append(('event-inherit',value))
            def wait(self,milliseconds):journal.append('ready-wait');return True
            def close(self):journal.append('event-close')
        class Kernel:
            def IsProcessInJob(self,process,job,member):
                journal.append(('same-job',job));member._obj.value=fault.job_member;return True
        class Windows:
            def __init__(self):self.k=Kernel()
            def job(self):journal.append('original-job');return 777
        class Pipe(io.BytesIO):
            def close(self):
                if not self.closed:self.saved=self.getvalue()
                super().close()
        pipe=Pipe();f.process.stdin=pipe;f.process._handle=999
        def factory(*args,**kwargs):
            journal.append('factory');return f.factory(*args,**kwargs)
        class Capture:
            def __init__(self,process):process.stdin.close()
            def communicate(self,timeout):return 'model-output',''
        sp=NS(Popen=factory,PIPE=subprocess.PIPE,BELOW_NORMAL_PRIORITY_CLASS=subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            CREATE_NO_WINDOW=subprocess.CREATE_NO_WINDOW,STARTUPINFO=subprocess.STARTUPINFO)
        fake_json=NS(dump=lambda *args,**kwargs:None)
        root=f.handoff.root
        space=dict(subprocess=sp,json=fake_json,BoundedProcessCapture=Capture,
            transfer=transfer,m=m,protocol=protocol)
        def body(run):
            Windows().job();state.frames.append(frame);journal.append('first-full-model-boundary')
            process=sp.Popen([transfer.sys.executable,
                str(root/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',m.TASK],
                cwd=root,stdin=sp.PIPE,stdout=sp.PIPE,stderr=sp.PIPE,
                creationflags=sp.BELOW_NORMAL_PRIORITY_CLASS|sp.CREATE_NO_WINDOW)
            journal.append('original-job-assignment')
            process.stdin.write(protocol.GO);process.stdin.flush()
            if fault.body:raise ValueError('MODEL_ORIGINAL_BODY_ERROR')
            cap=space['BoundedProcessCapture'](process);cap.communicate(1)
            return 17
        original_body=FunctionType(body.__code__,space,argdefs=body.__defaults__,closure=body.__closure__)
        worker=lambda:None
        component=recovery.tighten_window(window,(Path(__file__).resolve().parents[3]/recovery.WINDOW_PIN['path']).read_bytes())
        engine,strict_state=strict.connect_engine(NS(run_owned=original_body,worker=worker),component)
        linked=NS(engine=engine,window=NS(WINDOW=component),state=NS(attempts=0,calls=0),original_worker=worker)
        actual=NS(run_owned=engine.run_owned,worker=worker)
        connection=NS(parent=actual,state=state,frame_type=Frame)
        owner=NS(parent_connection=connection,phase='NEW',shared=NS(metadata=None,frame=None,restored=False),
            metadata_connection=NS(original_run=engine.run_owned,readers=[],budgets=[]))
        # Only the exact source predicate is stubbed, in a private model family.
        # All launch/Context/Gate/Input10/handoff code bodies are the real ones.
        def family(original,updates):
            value=families.family(original,updates)
            value.connect.__globals__['source']=lambda root,pin:journal.append('model-source-predicate')
            return value
        selected_protocol=NS(**{**vars(protocol),'WindowsEvent':Event})
        api=NS(transfer=transfer,inheritance=f.handoff.inheritance,bridge=f.handoff.bridge,
            protocol=selected_protocol,readiness=readiness,parent=parent,launch=launch,family=family)
        raw=(Path(__file__).resolve().parents[3]/m.STRICT['path']).read_bytes()
        def install():return m.install(root,NS(Windows=Windows,subprocess=sp),linked,actual,owner,
            required,required[m.ENTRY],api,f.handoff.coverage,raw,authorize=authorize)
        return NS(f=f,journal=journal,fault=fault,required=required,frame=frame,owner=owner,linked=linked,
            actual=actual,api=api,raw=raw,install=install,Windows=Windows,sp=sp,pipe=pipe,strict_state=strict_state)

    def test_install_is_inert_and_default_native_authority_denies_before_job_or_io(self):
        f=self.fixture();before_job=f.Windows.job;before_code=f.linked.engine.run_owned.__code__
        before_closure=f.linked.engine.run_owned.__closure__;connected=f.install()
        self.assertEqual(f.journal,[]);self.assertEqual(f.f.events,[]);self.assertIsNone(connected.handoff.actual)
        self.assertIs(f.Windows.job,before_job);self.assertIs(f.linked.engine.run_owned.__code__,before_code)
        self.assertIs(f.linked.engine.run_owned.__closure__,before_closure)
        with self.assertRaisesRegex(ValueError,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED'):f.actual.run_owned(1)
        self.assertEqual(f.journal,[]);self.assertEqual(connected.context.attempts,0)
        self.assertFalse(connected.evidence()['GO_authorized'])
        self.assertFalse(connected.evidence()['actual_Native_Frame_or_worker_or_product_qualified'])

    def test_original_chain_binds_before_frame_but_lends_only_after_original_job_and_boundary(self):
        f=self.fixture(authorize=lambda:True);before_job=f.Windows.job;connected=f.install()
        self.assertEqual(f.actual.run_owned(1),17)
        self.assertLess(f.journal.index('original-job'),f.journal.index('first-full-model-boundary'))
        self.assertLess(f.journal.index('first-full-model-boundary'),f.journal.index('factory'))
        self.assertLess(f.journal.index('original-job-assignment'),f.journal.index('ready-wait'))
        self.assertEqual(f.pipe.saved,f.api.bridge.START+protocol.GO)
        self.assertEqual(connected.context.jobs,1);self.assertEqual(connected.context.restorations,1)
        self.assertIs(f.Windows.job,before_job);self.assertTrue(connected.state.cleanup_confirmed)
        self.assertEqual(f.strict_state.states[0].diagnostics()['maximum_GO_to_complete_capture_seconds'],10)
        self.assertEqual(connected.context.bindings[0].gates[0].seconds,15)
        self.assertEqual(len(f.f.created),1);self.assertEqual(set(f.f.flags.values()),{0})
        self.assertEqual(f.frame.held.stream_read_counts,{name:1 for name in f.required})

    def test_wrong_job_denies_start_and_go_and_restores_original_job_method(self):
        f=self.fixture(authorize=lambda:True);f.fault.job_member=False;before=f.Windows.job;connected=f.install()
        with self.assertRaises(ValueError):f.actual.run_owned(1)
        self.assertEqual(f.pipe.getvalue(),b'');self.assertIs(f.Windows.job,before)
        self.assertTrue(connected.state.failed);self.assertTrue(connected.state.cleanup_confirmed)
        self.assertEqual(connected.context.restorations,1);self.assertIn('event-close',f.journal)
        f.pipe.close()

    def test_original_guard_failure_before_spawn_allocates_no_source_handoff_or_process(self):
        f=self.fixture(authorize=lambda:True);f.fault.guard=True;connected=f.install()
        with self.assertRaisesRegex(ValueError,'MODEL_GUARD_STOP'):f.actual.run_owned(1)
        self.assertIsNone(connected.handoff.actual);self.assertEqual(f.f.created,[])
        self.assertTrue(connected.state.failed);self.assertFalse(connected.context.active)
        self.assertEqual(connected.context.restorations,1)

    def test_original_body_error_survives_final_cleanup_failure_and_no_retry(self):
        f=self.fixture(authorize=lambda:True);f.fault.body=True;connected=f.install()
        connected.handoff.cleanup_handles=lambda:False
        with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_BODY_ERROR'):f.actual.run_owned(1)
        self.assertFalse(connected.state.cleanup_confirmed)
        with self.assertRaisesRegex(ValueError,'ONE_LOGICAL_RUN1_NO_RETRY'):f.actual.run_owned(1)
        f.pipe.close()

    def test_successful_body_cannot_return_success_when_final_cleanup_is_unconfirmed(self):
        f=self.fixture(authorize=lambda:True);connected=f.install();connected.handoff.cleanup_handles=lambda:False
        with self.assertRaisesRegex(ValueError,'SOURCE_HANDLE_CLEANUP_UNCONFIRMED'):f.actual.run_owned(1)
        self.assertTrue(connected.state.failed);self.assertEqual(connected.context.restorations,1)

    def test_source_code_tamper_or_unused_closure_tamper_rejected_before_install(self):
        f=self.fixture();component=f.linked.window.WINDOW;before=component.connect
        with self.assertRaisesRegex(ValueError,'EXACT_STRICT_CONNECTION_SOURCE'):
            m.strict_body(f.raw+b' ',f.linked.engine.run_owned,component)
        m.closure(f.linked.engine.run_owned)['calls'].append(1)
        with self.assertRaisesRegex(ValueError,'EXACT_UNUSED_STRICT_COMPONENT_CLOSURE'):f.install()
        self.assertIs(component.connect,before);self.assertEqual(f.journal,[])

    def test_missing_source_stale_parent_or_non_private_component_rejected_without_mutation(self):
        for fault in ('scope','parent','component'):
            f=self.fixture();original=f.actual.run_owned;component=f.linked.window.WINDOW;before=component.connect
            if fault=='scope':f.required.pop('helper200.py')
            elif fault=='parent':f.owner.parent_connection.state.frames.append(f.frame)
            else:f.linked.window.WINDOW=type('Unsafe',(),vars(component))()
            with self.assertRaises(ValueError):f.install()
            self.assertIs(f.actual.run_owned,original);self.assertIs(component.connect,before);self.assertEqual(f.journal,[])

    def test_binding_cannot_be_called_outside_original_owner_scope_or_installed_twice(self):
        f=self.fixture();connected=f.install()
        with self.assertRaisesRegex(ValueError,'ONE_COMPONENT_CONNECTION_IN_ORIGINAL_OWNER_SCOPE'):
            f.linked.window.WINDOW.connect(lambda:None,object)
        # The original execute still refers to the selected private object;
        # a second selector would otherwise wrap the same launch recursively.
        with self.assertRaises(ValueError):f.install()
        self.assertIsNone(connected.handoff.actual);self.assertEqual(f.f.created,[])

    def test_lazy_single_spawn_failure_cannot_retry_or_claim_coverage(self):
        f=self.fixture();connected=f.install()
        with self.assertRaises(ValueError):connected.handoff.spawn(lambda:None,[])
        self.assertTrue(connected.handoff.failed);self.assertIsNone(connected.handoff.actual)
        with self.assertRaisesRegex(ValueError,'ONE_LAZY_HANDOFF_NO_RETRY'):connected.handoff.spawn(lambda:None,[])
        self.assertTrue(connected.handoff.cleanup_handles());self.assertEqual(f.f.created,[])

    def driver_fixture(self):
        f=self.fixture();record=[]
        class Base:
            def __init__(self):self.construct_only=True
            def bind(self,root,a,c,*args):self.c=c
            def run(self,*args):return dict(actual_product_launch_handoff_installed=False,GO_authorized=False)
        declared=NS(required=f.required,control_names=tuple('base'+str(i) for i in range(59)))
        control=NS(admit=lambda *args,**kwargs:declared);driver=m.driver_type(Base)()
        c=NS(Windows=f.Windows,subprocess=f.sp);driver.bind(f.f.handoff.root,None,c,None,None,control)
        a=NS(native=NS(frames=object()),exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        def verify():pass
        coverage=NS(verify=FunctionType(verify.__code__,dict(frames=a.native.frames)))
        libraries=NS(native009_parent_launch_v1=f.api.parent,native009_worker_launch_v1=f.api.launch,
            batch_worker_launch=NS(family=f.api.family),native011_product_source_handoff=f.api.transfer,
            native011_worker_source_inheritance=f.api.inheritance,native011_inherited_source_probe_child=f.api.bridge,
            worker_readiness_v1=f.api.protocol,worker_readiness_connection_v1=f.api.readiness,
            native011_source_coverage=coverage)
        paths=(m.SELF,m.TEST,m.STRICT['path'],*(f'tools/p09/{name}.py' for name in (
            'native009_parent_launch_v1','native009_worker_launch_v1','batch_worker_launch',
            'native011_product_source_handoff','native011_worker_source_inheritance','native011_inherited_source_probe_child',
            'worker_readiness_v1','worker_readiness_connection_v1','native011_source_coverage')))
        current={name:dict(path=name,bytes=2,sha256='0'*64) for name in paths};current[m.STRICT['path']]=m.STRICT
        connection_reader=NS(snapshots={},final_fresh_hashes=0)
        def pin(name):connection_reader.snapshots[name]=current[name];return current[name]
        def finish():
            record.append('final-fresh-hashes');connection_reader.final_fresh_hashes=len(connection_reader.snapshots)
        connection_reader.pin=pin;connection_reader.finish=finish
        connection_reader._read=lambda *args,**kwargs:(m.STRICT,f.raw);connection_reader._bind=lambda *args:None
        connection_reader.checkpoint=lambda:record.append('guard')
        def private_load(loader,root,q,a,names,reuse):
            self.assertIs(q,connection_reader)
            for name in names:q.pin('tools/p09/'+name+'.py')
            record.append('private-fresh-load');return libraries,{}
        def forbid():raise AssertionError('ORIGINAL_CLOSING_MUST_NOT_REPEAT')
        q=NS(finish=forbid,checkpoint=lambda:None)
        a.AcceptanceReader=lambda root,checkpoint:connection_reader
        f.linked.engine.run_owned.__globals__['c']=c
        prepared=NS(linked=f.linked);data=NS(planned=NS(batch=f.owner,current=current));batch=NS(scope=object())
        return NS(f=f,driver=driver,control=control,q=q,a=a,record=record,connection_reader=connection_reader,
            run=lambda:driver.run(f.f.handoff.root,q,a,None,None,batch,data,prepared,None,None,None,{},private_load,None))

    def test_driver_declares_all64_named_roles_once_before_actual_construction(self):
        f=self.driver_fixture();value=f.control.admit(None,None,None)
        self.assertEqual(len(value.control_names),64);self.assertEqual(value.control_names[-5:],m.CONTROLS)
        with self.assertRaisesRegex(ValueError,'ONE_PARENT_HANDOFF_DECLARATION'):f.control.admit(None,None,None)
        self.assertEqual(f.driver.output,m.OUTPUT)

    def test_driver_installs_in_same_real_parent_without_job_frame_or_authority_and_closes_new_reads(self):
        f=self.driver_fixture();f.control.admit(None,None,None);out=f.run()
        self.assertTrue(out['actual_product_launch_handoff_installed'])
        self.assertFalse(out['actual_worker202_GO_or_Native_qualified'])
        self.assertFalse(out['actual_parent_handoff_connection']['authorization_dependency_present'])
        self.assertEqual(f.record,['private-fresh-load','final-fresh-hashes','guard'])
        self.assertEqual(f.f.journal,[]);self.assertEqual(f.f.owner.parent_connection.state.frames,[])
        with self.assertRaisesRegex(ValueError,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED'):f.f.actual.run_owned(1)

    def test_driver_does_not_report_success_on_current_closing_hash_failure(self):
        f=self.driver_fixture();f.control.admit(None,None,None)
        def fail():raise ValueError('MODEL_CURRENT_CLOSING_HASH_FAILURE')
        f.connection_reader.finish=fail
        with self.assertRaisesRegex(ValueError,'MODEL_CURRENT_CLOSING_HASH_FAILURE'):f.run()
        self.assertEqual(f.f.journal,[]);self.assertEqual(f.f.owner.parent_connection.state.frames,[])

    def test_explicit_false_authority_still_does_not_enter_owner_or_spawn(self):
        calls=[];f=self.fixture(authorize=lambda:(calls.append('request') or False));connected=f.install()
        with self.assertRaisesRegex(ValueError,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED'):f.actual.run_owned(1)
        self.assertEqual(calls,['request']);self.assertEqual(connected.context.attempts,0);self.assertEqual(f.journal,[])


if __name__=='__main__':unittest.main()
