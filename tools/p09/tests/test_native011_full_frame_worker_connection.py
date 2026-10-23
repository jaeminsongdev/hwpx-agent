from pathlib import Path
import sys
from types import CodeType, FunctionType, SimpleNamespace as NS
import unittest
from unittest.mock import patch

import native011_full_frame_worker_connection as m
import native011_full_frame_worker_ready as component
import native011_readonly_frame_probe as phase_api
import native011_ready_scope_connection as scope_connection
import native011_engine_owned_metadata_callback as metadata_callback
import native011_engine_owned_metadata_connection as metadata_connection
import native011_metadata_audit as metadata_audit
import native011_engine_owned_metadata_adoption as metadata_adoption


class Tests(unittest.TestCase):
    def audit(self):
        root=Path('model-root');raw=(Path(__file__).resolve().parents[3]/m.AUDIT['path']).read_bytes();registered=[]
        selected=m.AuditSelection(root,raw,registered.append)
        code=compile(raw,m.AUDIT['path'],'exec')
        main=next(value for value in code.co_consts if type(value) is CodeType and value.co_name=='main')
        deny=next(value for value in main.co_consts if type(value) is CodeType and value.co_name=='deny')
        denied=[];cell=(lambda:denied).__closure__[0];fn=FunctionType(deny,{},closure=(cell,))
        selected.register(fn)
        command=[sys.executable,'-B',str(root/m.ENTRY),'--ready-handle','33','--task',m.TASK,
            '--source-mapping','44','100','0'*64]
        options=dict(cwd=root,stdin=m.subprocess.PIPE,stdout=m.subprocess.PIPE,stderr=m.subprocess.PIPE,
            creationflags=m.subprocess.BELOW_NORMAL_PRIORITY_CLASS|m.subprocess.CREATE_NO_WINDOW,
            startupinfo=NS(lpAttributeList={'handle_list':list(range(1,205))}),close_fds=True)
        events=[];frame=NS(state='BEFORE_READ',registered=True,reading=False)
        phase=NS(state='SOURCE_FLAGS',frame=frame,check=lambda:events.append('guard'))
        return NS(selected=selected,root=root,raw=raw,hook=registered[0],fn=fn,denied=denied,command=command,
            options=options,phase=phase,events=events,registered=registered)

    def test_exact_one_child_audit_event_and_created_process_always_returns_for_original_cleanup(self):
        f=self.audit();process=object()
        def popen(command,**options):
            self.assertEqual(options['executable'],sys.executable)
            f.hook('subprocess.Popen',(sys.executable,m.subprocess.list2cmdline(command),str(f.root),None));return process
        with patch.object(m.subprocess,'Popen',popen):self.assertIs(f.selected.create(f.phase,f.command,**f.options),process)
        self.assertEqual(f.selected.allowed,1);self.assertEqual(f.selected.factory_attempts,1)
        self.assertIsNone(f.selected.command);self.assertEqual(f.denied,[])
        with self.assertRaisesRegex(ValueError,'ONE_REGISTERED_NO_GO_CHILD_FACTORY'):
            f.selected.create(f.phase,f.command,**f.options)
        with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):
            f.hook('subprocess.Popen',(sys.executable,f.command,str(f.root),None))

    def test_no_armed_scope_or_other_process_is_still_denied_by_original_code(self):
        f=self.audit()
        for event,values in (('subprocess.Popen',(sys.executable,f.command,str(f.root),None)),('os.system',('command',)),
                ('os.startfile',('file',)),('os.exec',()),('os.posix_spawn',()),('os.fork',())):
            with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):f.hook(event,values)
        self.assertEqual(len(f.denied),6);self.assertEqual(f.selected.allowed,0)

    def test_wrong_command_options_handle_list_and_phase_fail_before_popen(self):
        for failure in ('entry','task','mapping','shell','handles','phase'):
            f=self.audit();command=list(f.command);options=dict(f.options)
            if failure=='entry':command[2]='other.py'
            elif failure=='task':command[6]='other-task'
            elif failure=='mapping':command[8]=command[4]
            elif failure=='shell':options['shell']=True
            elif failure=='handles':options['startupinfo']=NS(lpAttributeList={'handle_list':[33,44]})
            else:f.phase.state='SECOND_READ'
            with patch.object(m.subprocess,'Popen',side_effect=AssertionError('NO_SPAWN')):
                with self.assertRaises(ValueError):f.selected.create(f.phase,command,**options)
            self.assertEqual(f.selected.factory_attempts,0);self.assertEqual(f.selected.allowed,0)

    def test_wrong_event_executable_cwd_or_repeated_event_cannot_pass_active_scope(self):
        for failure in ('executable','cwd','repeat'):
            f=self.audit()
            def popen(command,**options):
                valid=(sys.executable,command,str(f.root),None)
                if failure=='repeat':f.hook('subprocess.Popen',valid)
                values=('other.exe',command,str(f.root),None) if failure=='executable' else (
                    sys.executable,command,'other-root',None) if failure=='cwd' else valid
                f.hook('subprocess.Popen',values)
            with patch.object(m.subprocess,'Popen',popen):
                with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):
                    f.selected.create(f.phase,f.command,**f.options)
            self.assertIsNone(f.selected.command);self.assertEqual(f.selected.denied,1)

    def test_original_guard_error_at_audit_is_preserved_and_scope_clears(self):
        f=self.audit();checks=[]
        def check():
            checks.append(1)
            if len(checks)==2:raise ValueError('MODEL_ORIGINAL_NATIVE_CPU_STOP')
        f.phase.check=check
        def popen(command,**options):f.hook('subprocess.Popen',(sys.executable,command,str(f.root),None))
        with patch.object(m.subprocess,'Popen',popen):
            with self.assertRaisesRegex(ValueError,'MODEL_ORIGINAL_NATIVE_CPU_STOP'):
                f.selected.create(f.phase,f.command,**f.options)
        self.assertIsNone(f.selected.command);self.assertEqual(f.selected.allowed,0);self.assertEqual(f.denied,[])

    def test_tampered_audit_and_duplicate_registration_are_rejected_and_other_hooks_preserved(self):
        f=self.audit()
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL_PROCESS_AUDIT_SOURCE'):
            m.AuditSelection(f.root,f.raw+b' ',lambda value:None)
        with self.assertRaisesRegex(ValueError,'ONE_ORIGINAL_AUDIT_REGISTRATION'):f.selected.register(f.fn)
        other=lambda event,values:None;f.selected.register(other);self.assertIs(f.registered[-1],other)
        changed=FunctionType(f.fn.__code__.replace(co_consts=(*f.fn.__code__.co_consts,'tampered')),{},closure=f.fn.__closure__)
        fresh=m.AuditSelection(f.root,f.raw,lambda value:None)
        with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_DENIAL_CODE'):fresh.register(changed)

    def test_other_thread_cannot_arm_or_use_same_launch_scope(self):
        f=self.audit()
        with patch.object(m.threading,'get_ident',return_value=f.selected.thread+1):
            with self.assertRaisesRegex(ValueError,'ONE_REGISTERED_NO_GO_CHILD_FACTORY'):
                f.selected.create(f.phase,f.command,**f.options)
        self.assertEqual(f.selected.factory_attempts,0)

    def test_actual_common_projected_constructor_keeps_the_exact_original_audit_body(self):
        f=self.audit();projected,proof=scope_connection.project(f.raw,{},lambda *args:None,lambda *args:None,
            driver=NS(output='model-only-never-written.json'))
        code=next(value for value in projected.__code__.co_consts if type(value) is CodeType and value.co_name=='deny')
        denied=[];cell=(lambda:denied).__closure__[0];actual=FunctionType(code,{},closure=(cell,))
        registered=[];selection=m.AuditSelection(f.root,f.raw,registered.append);selection.register(actual)
        self.assertEqual(selection.registrations,1);self.assertTrue(proof['entire_original_constructor_AST_inverse'])
        with self.assertRaisesRegex(ValueError,'CURRENT805_SHARED_NO_PROCESS'):
            registered[0]('subprocess.Popen',(sys.executable,f.command,str(f.root),None))

    def test_real_windows_audit_boundary_has_fixed_executable_and_is_stopped_before_process_creation(self):
        f=self.audit();root=Path(__file__).resolve().parents[3];f.selected.root=root
        command=list(f.command);command[2]=str(root/m.ENTRY);options=dict(f.options,cwd=root)
        actual_popen=m.subprocess.Popen;actual_register=sys.addaudithook;observed=[];returned=[]
        # Actual runtime audit, not a fabricated callback. The explicit stop
        # runs before _winapi.CreateProcess. Fake204 handles are not inherited;
        # this case qualifies the audit boundary only, not Native or handle IO.
        f.selected.original_register=actual_register;f.selected.registrations=0;f.selected.register(f.fn)
        class ExpectedAuditBoundary(ValueError):pass
        def stop(event,values):
            if event=='subprocess.Popen':
                observed.append((values[0],values[1],values[2]));raise ExpectedAuditBoundary('MODEL_AUDIT_BOUNDARY_BEFORE_CREATEPROCESS')
        actual_register(stop)
        def bridge(command,**keywords):
            self.assertEqual(keywords['executable'],sys.executable)
            keywords.pop('startupinfo')  # Model handles, no handle-transfer claim.
            process=actual_popen(command,**keywords);returned.append(process);return process
        try:
            with patch.object(m.subprocess,'Popen',bridge):
                with self.assertRaises(ExpectedAuditBoundary):f.selected.create(f.phase,command,**options)
            self.assertEqual(len(observed),1);self.assertEqual(observed[0][0],sys.executable)
            self.assertEqual(observed[0][1],m.subprocess.list2cmdline(command));self.assertEqual(observed[0][2],str(root))
            self.assertEqual(f.selected.allowed,1);self.assertEqual(f.selected.denied,0);self.assertEqual(returned,[])
            self.assertIsNone(f.selected.command)
        finally:
            for process in returned:
                if process.poll() is None:process.terminate()
                process.wait(timeout=2)
                for stream in (process.stdin,process.stdout,process.stderr):stream.close()

    def driver(self,*,execute=False):
        events=[];audit=NS(registrations=1 if execute else 0,factory_attempts=0,allowed=0,evidence=lambda:{'model_only':True})
        class Base:
            def __init__(self):self.construct_only=True;self.stage='construction';self.native=None
            def bind(self,root,a,c,guards,loader,control):self.control=control
            def run(self,*args):return dict(actual_product_launch_handoff_installed=True,GO_authorized=False)
            def finish(self,root,row,publisher,a):events.append(('finish',self.construct_only))
            def marker(self,value):self.stage=value
            def metadata_evidence(self,owner):return dict(physical_read_passes=2,physical_bytes_read=6,
                original_metadata_binary2p5_other4_MiB_policy_retained=True)
        driver=m.driver_type(Base,audit,execute_whole=execute)()
        required={m.ENTRY:dict(path=m.ENTRY,bytes=2,sha256='0'*64)}
        required.update({f'helper{i}.py':dict(path=f'helper{i}.py',bytes=2,sha256='0'*64) for i in range(201)})
        previous={name:dict(pin) for name,pin in required.items() if name!=m.ENTRY}
        control=NS(admit=lambda *args,**kwargs:NS(control_names=tuple('base'+str(i) for i in range(64))),
            declarations=lambda record,scope:previous)
        driver.bind(None,None,None,None,None,control)
        driver.handoff_declaration=NS(required=required)
        def original_parent(run):pass
        driver.parent_handoff=NS(original_run=original_parent,handoff=NS(api=NS(),coverage=NS()))
        reader=NS(snapshots={},final_fresh_hashes=0)
        names=('native011_full_frame_worker_ready','native011_readonly_frame_driver','native011_readonly_frame_probe',
            'native011_nested_preparation_job','native011_product_worker_ready_probe','native011_product_worker_entry',
            'native011_inherited_worker_ready_inspection','bounded_process_progress',
            'native011_engine_owned_metadata_callback','native011_engine_owned_metadata_connection','native011_metadata_audit',
            'native011_engine_owned_metadata_adoption')
        paths={m.SELF,m.TEST,m.CONTROLS[3],m.CONTROLS[5],m.AUDIT['path'],metadata_connection.ENGINE['path'],
            *('tools/p09/'+name+'.py' for name in names)}
        rows={name:dict(path=name,bytes=2,sha256='0'*64) for name in paths}
        rows[m.DRIVER['path']]=m.DRIVER;rows[component.SOURCE['path']]=component.SOURCE
        rows[metadata_callback.SOURCE['path']]=metadata_callback.SOURCE
        rows[metadata_connection.ENGINE['path']]=metadata_connection.ENGINE
        raw=(Path(__file__).resolve().parents[3]/component.SOURCE['path']).read_bytes()
        raw_inputs={pin['path']:(Path(__file__).resolve().parents[3]/pin['path']).read_bytes()
            for pin in (component.SOURCE,metadata_callback.SOURCE,metadata_connection.ENGINE)}
        def pin(name):reader.snapshots[name]=rows[name];return rows[name]
        def finish():reader.final_fresh_hashes=len(reader.snapshots);events.append('closing18')
        reader.pin=pin;reader._read=lambda name,**kwargs:(rows[name],raw_inputs[name])
        reader._bind=lambda name,pin:reader.snapshots.__setitem__(name,pin)
        reader.finish=finish;reader.checkpoint=lambda:events.append('guard')
        a=NS(AcceptanceReader=lambda *args:reader,native=NS(frames=NS()),
            exact=lambda actual,expected,label:self.assertEqual(actual,expected))
        q=NS(checkpoint=lambda:None,pin=reader.pin)
        frame_type=type('Frame',(),{})
        data=NS(planned=NS(current=rows,batch=NS(parent_connection=NS(frame_type=frame_type))))
        class FakePhase:
            def __init__(self,api,raw,callback,**options):self.phase=object();self.callback=callback;self.frame=object()
        class FakeWorker:
            def __init__(self,*args,**kwargs):self.proof=dict(cleanup_confirmed=True,model_only=True);self.attempts=0
            def __call__(self,phase,frame):self.attempts+=1;audit.allowed=1;audit.factory_attempts=1;return self.proof
        def fake_prepare(api,raw,callback,**options):
            _,projection=component.projected_run(api,raw,options.get('original_parent_run'))
            return NS(create=lambda:FakePhase(api,raw,callback,**options),projection=projection,preparation={'model_only':True})
        selected_component=NS(**{**vars(component),'prepare_phase':fake_prepare,'WorkerProbe':FakeWorker}) if execute else component
        class Readonly:
            @staticmethod
            def run(view,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,load,publisher):
                libs,_=load(loader,root,q,a,('native011_readonly_frame_probe',),{})
                if libs.native011_metadata_audit.metadata is not view._owner.owned_metadata.callback:
                    raise AssertionError('ORIGINAL_OWNED_PREFIX_MUST_BE_CONNECTED')
                view._owner.owned_metadata.state.attempts=view._owner.owned_metadata.state.completed=1
                view.native=libs.native011_readonly_frame_probe.NativePhase();view.stage='native';view.guard=NS(windows=NS())
                view.native.callback(view.native.phase,object())
                return dict(state='MODEL_WHOLE_READONLY_DONE',actual_Native_Frame_created=True,actual_product_executed=False)
        libraries=NS(native011_full_frame_worker_ready=selected_component,native011_readonly_frame_driver=NS(Driver=Readonly),
            native011_readonly_frame_probe=phase_api,native011_nested_preparation_job=NS(),native011_product_worker_ready_probe=NS(),
            native011_product_worker_entry=NS(),native011_inherited_worker_ready_inspection=NS(),
            bounded_process_progress=NS(BoundedProcessCapture=type('Capture',(),{})),
            native011_engine_owned_metadata_callback=metadata_callback,
            native011_engine_owned_metadata_connection=metadata_connection,native011_metadata_audit=metadata_audit,
            native011_engine_owned_metadata_adoption=metadata_adoption)
        def private_load(loader,root,q,a,names,reuse):
            for name in names:q.pin('tools/p09/'+name+'.py')
            return libraries,{}
        return NS(driver=driver,audit=audit,events=events,control=control,reader=reader,required=required,previous=previous,
            run=lambda:driver.run(Path('model-root'),q,a,None,None,NS(scope=NS()),data,None,None,None,None,{},private_load,None))

    def test_constructor_selects_same_driver_and_source202_without_frame_worker_or_audit_exception(self):
        f=self.driver();value=f.control.admit(None,None,None);self.assertEqual(len(value.control_names),70)
        out=f.run();self.assertIn('NOT_EXECUTION',out['state'])
        self.assertEqual(out['full_frame_worker_connection']['fresh_inputs'],18)
        self.assertEqual(out['full_frame_worker_connection']['final_fresh_hashes'],18)
        phase=out['full_frame_worker_connection']['phase_preparation']
        self.assertEqual(phase['compiled_helpers_per_driver_construction'],1)
        self.assertFalse(phase['Native_phase_or_Frame_allocated_during_preparation'])
        self.assertFalse(phase['source_byte_hash_JSON_AST_or_closing_credit_reused'])
        self.assertTrue(phase['one_phase_creation_no_retry'])
        self.assertEqual(f.driver.owned_metadata.state.attempts,0)
        self.assertTrue(out['full_frame_worker_connection']['owned_metadata_callback_projection']['entire_original_metadata_body_inverse'])
        self.assertIsNone(f.driver.native);self.assertIsNone(f.driver.full_worker);self.assertTrue(f.driver.construct_only)
        observed=f.driver.readonly_view.control.declarations({},None)
        self.assertEqual(observed,f.required);observed[m.ENTRY]['bytes']=3;self.assertEqual(f.required[m.ENTRY]['bytes'],2)
        self.assertEqual(f.events,['closing18','guard'])

    def test_diagnostic_uses_only_original_readonly_run_and_source_child_not_product_route(self):
        f=self.driver(execute=True);f.control.admit(None,None,None);out=f.run()
        self.assertEqual(out['state'],'PASS_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH')
        self.assertTrue(out['actual_Native_Frame_created']);self.assertFalse(out['actual_product_executed'])
        self.assertTrue(f.driver.construct_only);self.assertEqual(f.audit.allowed,1)
        f.driver.finish(None,{},None,None);self.assertIn(('finish',False),f.events)

    def test_changed_201_declarations_and_failed_component_closing_cannot_be_accepted(self):
        f=self.driver();f.control.admit(None,None,None);f.run();f.previous.pop('helper0.py')
        with self.assertRaisesRegex(ValueError,'EXACT_ORIGINAL201_PLUS'):f.driver.readonly_view.control.declarations({},None)
        f=self.driver();f.control.admit(None,None,None)
        def fail():raise ValueError('MODEL_NEW_COMPONENT_CLOSING_FAILURE')
        f.reader.finish=fail
        with self.assertRaisesRegex(ValueError,'MODEL_NEW_COMPONENT_CLOSING_FAILURE'):f.run()
        self.assertIsNone(f.driver.full_phase_factory)

    def test_view_forwards_lifecycle_state_and_rebinds_methods_without_enabling_product_driver(self):
        f=self.driver();f.control.admit(None,None,None);f.run();view=f.driver.readonly_view
        view.marker('opening');self.assertEqual(f.driver.stage,'opening');self.assertFalse(view.construct_only)
        self.assertTrue(f.driver.construct_only)
        with self.assertRaisesRegex(ValueError,'READONLY_VIEW_MODE'):view.construct_only=True

    def test_main_rejects_product_go_or_unbounded_arguments_before_bootstrap(self):
        for args in (['--go'],['--whole-no-go','--whole-no-go'],['--attempt','2']):
            with patch.object(sys,'argv',['connection.py',*args]):
                with self.assertRaisesRegex(ValueError,'CLOSED_CONSTRUCTION_OR_WHOLE_NO_GO_ONLY'):m.main()

    def test_failed_partial_diagnostic_reports_observed_frame_metadata_and_child_not_only_final_success(self):
        f=self.driver(execute=True);f.control.admit(None,None,None);f.run()
        f.driver.full_connection.update(full_Native_phase_created=False,actual_whole_Frame_or_child_executed=False,
            metadata_allocation_or_body_executed=False)
        f.driver.owned_metadata.state.completed=0;f.driver.owned_metadata.state.failed=True
        row={};f.driver.finish(None,row,None,None);observed=row['full_frame_worker_connection']
        self.assertTrue(observed['full_Native_phase_created']);self.assertTrue(observed['actual_whole_Frame_or_child_executed'])
        self.assertTrue(observed['metadata_allocation_or_body_executed']);self.assertFalse(observed['GO_authorized'])

    def test_metadata_evidence_reports_actual_owned_rates_and_never_the_legacy_fixed_rate_label(self):
        f=self.driver();f.control.admit(None,None,None);f.run()
        record=dict(original_engine_owned_assignment_adopted=True,source_table_and_read_proxy_retained=True,
            original_owned_rates=dict(binary=1048576,other=2097152),physical_read_passes=2,physical_bytes_read=6)
        f.driver.metadata_adoption=NS(summary=lambda reader:record)
        reader=NS(pacer=NS(bytes_by_kind={'binary':0,'other':6}))
        owner=NS(metadata_connection=NS(readers=[reader]))
        result=f.driver.readonly_view.metadata_evidence(owner)
        self.assertFalse(result['original_metadata_binary2p5_other4_MiB_policy_retained'])
        self.assertTrue(result['original_owned_binary1_other2_MiB_policy_retained'])
        self.assertEqual(result['actual_paced_bytes_by_kind'],{'binary':0,'other':6})
        reader.pacer.bytes_by_kind['other']=5
        with self.assertRaisesRegex(ValueError,'ACTUAL_METADATA_ASSIGNMENT_AND_PACED_BYTES'):
            f.driver.readonly_view.metadata_evidence(owner)


if __name__=='__main__':unittest.main()
