"""Closed common readonly driver with one exact no-GO source worker.

The actual product parent remains denied. Only the original no-product
delegate gets the worker202 phase. Neither construction nor the diagnostic
consumes product intent or writes the canonical Native011 result.
"""
import ast
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import threading
from types import CodeType, FunctionType, MethodType, SimpleNamespace as NS
from unittest.mock import patch

SELF='tools/p09/native011_full_frame_worker_connection.py'
TEST='tools/p09/tests/test_native011_full_frame_worker_connection.py'
COMPONENT='tools/p09/native011_full_frame_worker_ready.py'
CONTROLS=(SELF,TEST,COMPONENT,'tools/p09/tests/test_native011_full_frame_worker_ready.py',
    'tools/p09/native011_engine_owned_metadata_callback.py','tools/p09/tests/test_native011_engine_owned_metadata_callback.py')
CONSTRUCTION='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-connection-construct004.v1.json'
DIAGNOSTIC='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-connection-probe005.v1.json'
PARENT=dict(path='tools/p09/native011_product_parent_handoff.py',bytes=17663,
    sha256='9b72f412a29cbe4c374ece3ffa84e810d27ecbbb1b21552933d531ea997ba4e8')
AUDIT=dict(path='tools/p09/native011_current_epoch_shared.py',bytes=17131,
    sha256='db60bee1016ccab236a05363a618435c2d6c813ebe5359ef55e9cae5114d6dc2')
DRIVER=dict(path='tools/p09/native011_readonly_frame_driver.py',bytes=18757,
    sha256='55b593f55f674ea7bc1190c892bec5cb0f34056b446afc5edd51a1de720a8051')
ENTRY='tools/p09/native011_product_worker_entry.py'
TASK='case165-current-r011-tests'


def require(ok,code):
    if not ok:raise ValueError('FULL_FRAME_WORKER_CONNECTION_'+code)


class AuditSelection:
    def __init__(self,root,raw,register):
        require(type(raw) is bytes and len(raw)==AUDIT['bytes']
            and hashlib.sha256(raw).hexdigest()==AUDIT['sha256'],'EXACT_ORIGINAL_PROCESS_AUDIT_SOURCE')
        self.root=root;self.raw=raw;self.original_register=register;self.thread=threading.get_ident()
        self.registrations=0;self.factory_attempts=0;self.allowed=0;self.denied=0;self.command=None;self.phase=None
    def register(self,fn):
        if not (type(fn) is FunctionType and fn.__code__.co_filename.replace('\\','/').endswith(AUDIT['path'])
                and fn.__name__=='deny'):
            return self.original_register(fn)
        require(threading.get_ident()==self.thread and self.registrations==0,'ONE_ORIGINAL_AUDIT_REGISTRATION')
        def child(code,name):return [value for value in code.co_consts if type(value) is CodeType and value.co_name==name]
        code=compile(self.raw,fn.__code__.co_filename,'exec');main=child(code,'main')
        require(len(main)==1,'ONE_ORIGINAL_AUDIT_MAIN');expected=child(main[0],'deny')
        require(len(expected)==1 and expected[0]==fn.__code__ and fn.__code__.co_freevars==('denied',),
            'ENTIRE_ORIGINAL_DENIAL_CODE_AND_CLOSURE_ROLE')
        self.registrations+=1
        def selected(event,values):
            if event=='subprocess.Popen':
                if self.permit(values):return
                self.denied+=1
            return fn(event,values)
        return self.original_register(selected)
    def permit(self,values):
        if not (threading.get_ident()==self.thread and self.command is not None and self.phase is not None
                and self.factory_attempts==1 and self.allowed==0 and len(values)>=3):return False
        command=list(self.command)
        if not (values[0]==sys.executable and values[1] in (command,subprocess.list2cmdline(command))
                and str(values[2])==str(self.root)):return False
        self.phase.check();self.allowed+=1;return True
    def create(self,phase,command,**options):
        require(threading.get_ident()==self.thread and self.registrations==1 and self.factory_attempts==0,
            'ONE_REGISTERED_NO_GO_CHILD_FACTORY')
        require(type(command) is list and len(command)==11 and command[:3]==[sys.executable,'-B',str(self.root/ENTRY)]
            and command[3]=='--ready-handle' and command[5:8]==['--task',TASK,'--source-mapping']
            and all(type(command[i]) is str and re.fullmatch('[1-9][0-9]{0,19}',command[i]) is not None
                and int(command[i])<2**64 for i in (4,8)) and command[4]!=command[8]
            and type(command[9]) is str and re.fullmatch('[1-9][0-9]{0,5}',command[9]) is not None and int(command[9])<=262144
            and type(command[10]) is str and re.fullmatch('[0-9a-f]{64}',command[10]) is not None,
            'EXACT_SOURCE_MAPPING_WORKER202_COMMAND')
        attributes=getattr(options.get('startupinfo'),'lpAttributeList',None)
        handles=attributes.get('handle_list') if type(attributes) is dict else None
        require(set(options)=={'cwd','stdin','stdout','stderr','creationflags','startupinfo','close_fds'}
            and options['cwd']==self.root and options['close_fds'] is True
            and all(options[key]==subprocess.PIPE for key in ('stdin','stdout','stderr'))
            and options['creationflags']==subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW
            and type(handles) is list and len(handles)==len(set(handles))==204
            and all(type(handle) is int and handle>0 for handle in handles)
            and int(command[4]) in handles and int(command[8]) in handles,
            'EXACT_ORIGINAL_PIPES_FLAGS_AND_204_EXPLICIT_HANDLES')
        require(phase.state=='SOURCE_FLAGS' and phase.frame.state=='BEFORE_READ'
            and phase.frame.registered and not phase.frame.reading,'ONLY_FIRST_WHOLE_FRAME_SOURCE_FLAGS_PHASE')
        phase.check();self.factory_attempts+=1;self.command=tuple(command);self.phase=phase
        try:
            # Windows reports the executable audit field as None when this
            # keyword is omitted. Keep the strict executable predicate and
            # explicitly select the same interpreter already fixed in argv.
            process=subprocess.Popen(command,executable=sys.executable,**options)
            # Once created, always return the process to the existing handoff
            # and original owned cleanup; never lose it on a postspawn check.
            return process
        finally:self.command=None;self.phase=None
    def evidence(self):
        return dict(original_process_denial_registrations=self.registrations,exact_child_factory_attempts=self.factory_attempts,
            exact_worker_Popen_events_allowed=self.allowed,other_Popen_events_denied=self.denied,
            launch_scope_active=self.command is not None,product_GO_or_intent_authorized=False)


class ReadonlyView:
    """Forward lifecycle state, select only diagnostic mode and declarations."""
    def __init__(self,owner,control):
        object.__setattr__(self,'_owner',owner);object.__setattr__(self,'_control',control)
    @property
    def construct_only(self):return False
    @property
    def control(self):return self._control
    def __getattr__(self,name):
        value=getattr(self._owner,name)
        if type(value) is MethodType and value.__self__ is self._owner:return MethodType(value.__func__,self)
        return value
    def __setattr__(self,name,value):
        require(name not in ('construct_only','control','_owner','_control'),'READONLY_VIEW_MODE_AND_OWNER_IMMUTABLE')
        setattr(self._owner,name,value)


def driver_type(base,audit,*,execute_whole=False):
    require(type(execute_whole) is bool,'EXPLICIT_NO_GO_DIAGNOSTIC_MODE')
    class Driver(base):
        def __init__(self):
            super().__init__();self.output=DIAGNOSTIC if execute_whole else CONSTRUCTION
            self.full_phase_factory=None;self.full_worker=None;self.readonly_view=None;self.full_connection=None
            self.extra_admission=False;self.owned_metadata=None;self.metadata_adoption=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);before=control.admit
            def declared(q,a,scope,**options):
                require(not self.extra_admission,'ONE_FULL_FRAME_CONNECTION_DECLARATION')
                value=before(q,a,scope,**options);self.extra_admission=True
                require(len(value.control_names)==64 and not set(CONTROLS)&set(value.control_names),
                    'EXACT70_EXPLICIT_FULL_FRAME_CONNECTION_CONTROLS')
                return NS(**{**vars(value),'control_names':value.control_names+CONTROLS})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            require(self.extra_admission and self.full_phase_factory is None and self.construct_only,
                'ONE_COMMON_PARENT_AFTER_INERT_HANDOFF_CONSTRUCTION')
            source_reader=a.AcceptanceReader(root,q.checkpoint)
            for name in (SELF,TEST,CONTROLS[3],CONTROLS[5]):source_reader.pin(name)
            names=('native011_full_frame_worker_ready','native011_readonly_frame_driver','native011_readonly_frame_probe',
                'native011_nested_preparation_job','native011_product_worker_ready_probe','native011_product_worker_entry',
                'native011_inherited_worker_ready_inspection','bounded_process_progress',
                'native011_engine_owned_metadata_callback','native011_engine_owned_metadata_connection','native011_metadata_audit',
                'native011_engine_owned_metadata_adoption')
            libraries,_=private_load(loader,root,source_reader,a,names,
                {'runtime_input_frame':a.native.frames,'current_stored_runtime_scope':batch.scope})
            component=libraries.native011_full_frame_worker_ready;phase_api=libraries.native011_readonly_frame_probe
            raw_pin,raw=source_reader._read(component.SOURCE['path'],parse=True);source_reader._bind(raw_pin['path'],raw_pin)
            a.exact(raw_pin,component.SOURCE,'FRESH_ORIGINAL_FULL_FRAME_PHASE_SOURCE')
            a.exact(source_reader.pin(DRIVER['path']),DRIVER,'UNCHANGED_WHOLE_READONLY_DRIVER_CODE')
            bridge=libraries.native011_engine_owned_metadata_callback;owned=libraries.native011_engine_owned_metadata_connection
            def source(pin):
                actual,data=source_reader._read(pin['path'],parse=True);source_reader._bind(actual['path'],actual)
                a.exact(actual,pin,'ORIGINAL_FULL_METADATA_AND_ENGINE_FOR_OWNED_PREFIX');return bytes(data)
            self.owned_metadata,metadata_projection=bridge.project(source(bridge.SOURCE),libraries.native011_metadata_audit.metadata,
                source(owned.ENGINE),owned)
            self.metadata_adoption=libraries.native011_engine_owned_metadata_adoption
            require(self.owned_metadata.state.attempts==self.owned_metadata.state.completed==0
                and not self.owned_metadata.state.failed,'METADATA_ALLOCATION_NOT_EXECUTED_DURING_CONSTRUCTION')
            source_reader.pin(AUDIT['path'])
            require(set(source_reader.snapshots)=={SELF,TEST,CONTROLS[3],CONTROLS[5],AUDIT['path'],owned.ENGINE['path'],
                *('tools/p09/'+name+'.py' for name in names)},'EXACT18_FRESH_FULL_FRAME_CONNECTION_INPUTS')
            for name,pin in source_reader.snapshots.items():
                a.exact(dict(data.planned.current[name]),pin,'FULL_FRAME_CONNECTION_INPUT_IS_DIRECT_CURRENT_NATIVE_SOURCE')
            source_reader.finish();source_reader.checkpoint()
            require(source_reader.final_fresh_hashes==len(source_reader.snapshots)==18,'FULL_CONNECTION_FIRST_AND_CLOSING18')
            required={name:dict(pin) for name,pin in self.handoff_declaration.required.items()}
            old_control=self.control;old_declarations=old_control.declarations
            def declarations(record,scope):
                previous=old_declarations(record,scope)
                require(previous=={name:pin for name,pin in required.items() if name!=ENTRY},
                    'EXACT_ORIGINAL201_PLUS_ALREADY_DECLARED_NEW_CHILD')
                return {name:dict(pin) for name,pin in required.items()}
            self.readonly_view=ReadonlyView(self,NS(**{**vars(old_control),'declarations':declarations}))
            original_api=self.parent_handoff.handoff.api;coverage=self.parent_handoff.handoff.coverage
            api=NS(**{**vars(original_api),'coverage':coverage,'nested':libraries.native011_nested_preparation_job,
                'probe':libraries.native011_product_worker_ready_probe,'worker':libraries.native011_product_worker_entry,
                'original':libraries.native011_inherited_worker_ready_inspection})
            def callback(phase,frame):
                require(self.stage=='native' and self.native.phase is phase and self.full_worker is None,
                    'ONLY_ACTUAL_NEW_NATIVE_PHASE_CAN_START_WORKER')
                self.full_worker=component.WorkerProbe(root,self.guard.windows,required,
                    data.planned.batch.parent_connection.frame_type,api,libraries.bounded_process_progress.BoundedProcessCapture,
                    factory=lambda command,**options:audit.create(phase,command,**options))
                return self.full_worker(phase,frame)
            phase_prepared=component.prepare_phase(phase_api,bytes(raw),callback,
                original_parent_run=self.parent_handoff.original_run)
            phase_factory=phase_prepared.create;self.full_phase_factory=phase_factory
            proof=dict(phase_projection=phase_prepared.projection,phase_preparation=phase_prepared.preparation,
                original_readonly_driver_run_code_retained=True,
                owned_metadata_callback_projection=metadata_projection,metadata_allocation_or_body_executed=False,
                original_product_parent_still_denied=True,full_Native_phase_created=False,actual_whole_Frame_or_child_executed=False,
                fresh_inputs=len(source_reader.snapshots),final_fresh_hashes=source_reader.final_fresh_hashes,
                source_pins=list(source_reader.snapshots.values()),original_closed_reader_reused_or_reset=False,
                GO_authorized=False,original_product_Job_or_commit_qualified=False)
            self.full_connection=proof
            if not execute_whole:
                require(audit.registrations==audit.factory_attempts==audit.allowed==0,'CONSTRUCTION_HAS_NO_AUDIT_OR_PROCESS_EXCEPTION')
                return dict(value,state='PASS_COMMON_FULL_FRAME_WORKER_READY_CONNECTION_CONSTRUCTION_NOT_EXECUTION',
                    full_frame_worker_connection=proof)
            require(audit.registrations==1,'ORIGINAL_AUDIT_CONNECTED_BEFORE_WHOLE_NO_GO_DIAGNOSTIC')
            selected=[]
            def load(*args,**kwargs):
                result,observed=private_load(*args,**kwargs)
                if hasattr(result,'native011_readonly_frame_probe'):
                    require(not selected,'ONE_ORIGINAL_READONLY_PHASE_FACTORY_DEPENDENCY');selected.append(True)
                    result=NS(**{**vars(result),'native011_readonly_frame_probe':NS(**{**vars(result.native011_readonly_frame_probe),
                        'NativePhase':phase_factory})})
                if hasattr(result,'native011_metadata_audit'):
                    result=NS(**{**vars(result),'native011_metadata_audit':NS(**{**vars(result.native011_metadata_audit),
                        'metadata':self.owned_metadata.callback})})
                return result,observed
            diagnostic=libraries.native011_readonly_frame_driver.Driver.run(self.readonly_view,root,q,a,loader,entry,batch,data,
                prepared,bound,resources,checked,row,load,publisher)
            require(selected==[True] and self.full_worker is not None and self.full_worker.proof['cleanup_confirmed'] is True
                and audit.allowed==1 and audit.factory_attempts==1
                and self.owned_metadata.state.attempts==self.owned_metadata.state.completed==1 and not self.owned_metadata.state.failed,
                'ONE_REAL_OWNED_METADATA_AND_NO_GO_CHILD_THEN_ORIGINAL_FULL_CLOSING')
            proof.update(full_Native_phase_created=True,actual_whole_Frame_or_child_executed=True,
                metadata_allocation_or_body_executed=True,
                worker=self.full_worker.proof,process_audit=audit.evidence())
            return {**value,**diagnostic,'state':'PASS_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH',
                'full_frame_worker_connection':proof}
        def metadata_evidence(self,owner):
            # Explicit base call also works through ReadonlyView, without a
            # zero-argument super() requiring the view to be a Driver instance.
            value=base.metadata_evidence(self,owner);reader=owner.metadata_connection.readers[0]
            require(self.metadata_adoption is not None,'ACTUAL_OWNED_METADATA_ADOPTION_API')
            adopted=self.metadata_adoption.summary(reader);paced=dict(reader.pacer.bytes_by_kind)
            require(adopted['original_engine_owned_assignment_adopted'] is True
                and adopted['source_table_and_read_proxy_retained'] is True
                and adopted['original_owned_rates']==dict(binary=1048576,other=2097152)
                and adopted['physical_read_passes']==value['physical_read_passes']
                and adopted['physical_bytes_read']==sum(paced.values())==value['physical_bytes_read']
                and set(paced)<=set(('binary','other')) and all(type(n) is int and n>=0 for n in paced.values()),
                'ACTUAL_METADATA_ASSIGNMENT_AND_PACED_BYTES_NOT_LEGACY_RATE_LABEL')
            return dict(value,original_metadata_binary2p5_other4_MiB_policy_retained=False,
                original_owned_binary1_other2_MiB_policy_retained=True,actual_owned_engine_adoption=adopted,
                actual_metadata_rates=dict(binary=1048576,other=2097152),actual_paced_bytes_by_kind=paced)
        def finish(self,root,row,publisher,a):
            if execute_whole and self.readonly_view is not None:
                # The default instance stays construct_only. Forward original
                # terminal publication with the same diagnostic view used above.
                base_finish=next(cls.__dict__['finish'] for cls in type(self).__mro__[1:]
                    if 'finish' in cls.__dict__)
                base_finish(self.readonly_view,root,row,publisher,a)
            else:super().finish(root,row,publisher,a)
            if self.full_connection is not None:
                frame_created=self.native is not None and getattr(self.native,'frame',None) is not None
                child_attempted=self.full_worker is not None and getattr(self.full_worker,'attempts',0)>0
                metadata_attempted=self.owned_metadata is not None and self.owned_metadata.state.attempts>0
                row['full_frame_worker_connection']=dict(self.full_connection,
                    full_Native_phase_created=frame_created,
                    actual_whole_Frame_or_child_executed=frame_created or child_attempted,
                    metadata_allocation_or_body_executed=metadata_attempted,
                    process_audit=audit.evidence(),worker=None if self.full_worker is None else self.full_worker.proof)
    return Driver


def main():
    require(sys.argv[1:] in ([],['--whole-no-go']),'CLOSED_CONSTRUCTION_OR_WHOLE_NO_GO_ONLY')
    execute_whole=bool(sys.argv[1:]);sys.dont_write_bytecode=True;root=Path(__file__).resolve().parents[2]
    output=DIAGNOSTIC if execute_whole else CONSTRUCTION
    require(not(root/output).exists(),'EXCLUSIVE_NEW_CONNECTION_OR_NO_GO_DIAGNOSTIC')
    def fresh(pin):
        path=root/pin['path']
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
        require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'EXACT_BOOTSTRAP_SOURCE')
        return raw
    loader_pin=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
        sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
    env=dict(__name__='p09_full_frame_worker_connection_bootstrap',__file__=loader_pin['path'])
    exec(compile(fresh(loader_pin),loader_pin['path'],'exec'),env)
    libraries,_=NS(**env).load(root,[PARENT],{});parent=libraries.native011_product_parent_handoff
    audit=AuditSelection(root,fresh(AUDIT),sys.addaudithook)
    original=parent.main
    def selected(base):return driver_type(parent.driver_type(base),audit,execute_whole=execute_whole)
    fn=FunctionType(original.__code__,dict(original.__globals__,OUTPUT=output,driver_type=selected),
        argdefs=original.__defaults__,closure=original.__closure__);fn.__kwdefaults__=original.__kwdefaults__
    before=sys.argv;sys.argv=[before[0]]
    try:
        if execute_whole:
            with patch.object(sys,'addaudithook',audit.register):return fn()
        return fn()
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
