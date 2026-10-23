"""Whole original opening/Native/closing/oracle procedure for Native011.

Only the result namespace and one progress label differ. The caller still
must qualify and connect the original controllers/current202 process audit.
No CLI, process, approval, intent write or product acceptance runs at import.
"""
import ast
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from types import CodeType, FrameType, FunctionType, SimpleNamespace as NS
from unittest.mock import patch

SELF='tools/p09/native011_product_lifecycle.py'
TEST='tools/p09/tests/test_native011_product_lifecycle.py'
SOURCE=dict(path='tools/p09/batch_product_runtime.py',bytes=23931,
    sha256='c98a4c734cdd7293fc8fbe6225480b0746d300df95944d65a366788f3e910a99')
PARENT=dict(path='tools/p09/native011_product_parent_handoff.py',bytes=17663,
    sha256='9b72f412a29cbe4c374ece3ffa84e810d27ecbbb1b21552933d531ea997ba4e8')
PREPARATION=dict(path='tools/p09/batch_zlib_metadata.py',bytes=19240,
    sha256='c8611aada02a99d9d82d29c3823d67bc835332ec053006f6706fea1785bf8115')
CONTROLLERS=(PREPARATION,
    dict(path='tools/p09/batch_native_checkpoint.py',bytes=5743,
        sha256='8295901ed4345141ca4417651fc172afc342a3da6dab5f0fb0701a30be299994'),
    dict(path='tools/p09/batch_post_job_checkpoint.py',bytes=8140,
        sha256='c8e57c6a09b8b144f8d8832ea1527b1f965e801dca8206b6c34e15996f79c3f3'),
    dict(path='tools/p09/preparation_checkpoint_owner.py',bytes=5731,
        sha256='2ef536c53e0e2a82df44f0917783cf7f9fcd67e8d5dcd3d28d17d458c5285078'),
    dict(path='tools/p09/batch_post_native.py',bytes=11267,
        sha256='cd386dba0aef5f55a31cf221bf5cf524da67c97b5973bced5f3aacf6a386b961'),
    dict(path='tools/p09/batch_pre_go_runtime.py',bytes=25016,
        sha256='cc4d2b0030c7ce4324c6cb994f5deb4f042a8d4f1bb2cc0b8366c2b9e8e83761'),
    dict(path='tools/p09/batch_verification.py',bytes=63495,
        sha256='296b4fe1070a6e5e4cfb882ba0ad9ca252edc702fc2441e970292cf5ad76dff9'),
    dict(path='tools/p09/run_case112_current_stored.py',bytes=23159,
        sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713'))
CANONICAL='implementation/p09/evidence/p09-361-case165-current-runtime-run011.v1.json'
ONCE=dict(path='tools/p09/native011_product_once.py',bytes=13595,
    sha256='dd193c89c911f197da1bf2ab96be9f792988af805fb582f67b48b080eb854f0e')
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
PROCESS_AUDIT=dict(path='tools/p09/native011_current_epoch_shared.py',bytes=17131,
    sha256='db60bee1016ccab236a05363a618435c2d6c813ebe5359ef55e9cae5114d6dc2')
PROCESS_CONNECTION=dict(path='tools/p09/native011_full_frame_worker_connection.py',bytes=21292,
    sha256='db312476f2e8515abcda357214f9f6494a074bd1a243642f9424302c3dd4ff19')
PROCESS_TRANSFER=dict(path='tools/p09/native011_product_source_handoff.py',bytes=11353,
    sha256='ed5c13d4c8d3ed7a3439a6a82616645b6f2f7b0bcb0b4b78136c18f524e8083f')
PRODUCT_ENTRY='tools/p09/native011_product_worker_entry.py'
PRODUCT_TASK='case165-current-r011-tests'
ORACLE_STEP=dict(path='implementation/p09/evidence/p09-361-case165-step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')
ORACLE_REFERENCES=(
    dict(path='implementation/p09/evidence/p09-361-case112-current-stored-list-run001.v1.json',bytes=774020,
        sha256='06a9affc55cc5f9b1892a1be3649fa210822427be7020f865dccdac8acf4daf4'),
    dict(path='implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json',bytes=565807,
        sha256='b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72'),
    dict(path='implementation/p09/evidence/locked-r07/p340-light-review-run131.v1.json',bytes=94990,
        sha256='6d05cb6bf810ff5c19c61d1bc2d76921a00abb00d0f959c51e5fed9402a782ff'))
ORACLE_READER_CODE=('tools/p09/batch_scope_admission.py','tools/p09/single_snapshot_source_guard_v1.py',
    'tools/p09/reusable_audit_chunk_v1.py','tools/p09/audit_evidence_io.py')
DISPATCH=('tools/p09/native011_product_dispatch.py','tools/p09/tests/test_native011_product_dispatch.py')
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-product-lifecycle-construct012.v1.json'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_PRODUCT_LIFECYCLE_'+code)


def exact(raw,pin):
    require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
        'EXACT_WHOLE_ORIGINAL_SOURCE');return raw


def nested(code,name):
    values=[value for value in code.co_consts if type(value) is CodeType and value.co_name==name]
    require(len(values)==1,'ONE_WHOLE_ORIGINAL_CODE_DEFINITION');return values[0]


def shape(code):
    return (code.co_code,tuple(shape(value) if type(value) is CodeType else value for value in code.co_consts),
        code.co_names,code.co_varnames,code.co_freevars,code.co_cellvars,code.co_argcount,
        code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,code.co_exceptiontable)


def product_audit_type(raw,connection):
    """Keep original deny registration; scope a product factory, not a probe."""
    exact(raw,PROCESS_CONNECTION);base=connection.AuditSelection;tree=ast.parse(raw)
    node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AuditSelection')
    names=tuple(n.name for n in node.body if isinstance(n,ast.FunctionDef))
    def matches(code):
        cls=nested(code,'AuditSelection')
        return all(type(vars(base).get(name)) is FunctionType
            and shape(vars(base)[name].__code__)==shape(nested(cls,name)) for name in names)
    if not matches(compile(raw,PROCESS_CONNECTION['path'],'exec')):
        code=compile(ast.fix_missing_locations(ast.Module(body=[n for n in tree.body
            if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),PROCESS_CONNECTION['path'],'exec')
        require(matches(code),'WHOLE_ORIGINAL_PROCESS_AUDIT_CLASS')
    class ProductAudit(base):
        def __init__(self,root,source,register,*,factory=None):
            exact(source,PROCESS_AUDIT);super().__init__(root,source,register)
            self.pid=os.getpid();self.original_factory=subprocess.Popen if factory is None else factory
            self.driver=self.once=self.link=self.actual_scope=None;self.failed=False;self.bound=False
            self.ever_bound=False;self.restored=False;self.original_denied=None;self.connections=0
            self.original_transfer=self.api=self.adapter=None;self.restore_errors=[];self.method_pins=[]
            self.transfer_compile_form=None
            self.arm_attempts=0;self.armed=False
            self.policy=NS(arm=self.arm,attempts=0,denied=None)
        def register(self,fn):
            selected=(type(fn) is FunctionType and fn.__code__.co_filename.replace('\\','/').endswith(PROCESS_AUDIT['path'])
                and fn.__name__=='deny')
            result=super().register(fn)
            if selected:
                self.original_denied=fn.__closure__[0].cell_contents;self.policy.denied=self.original_denied
            return result
        def owner_check(self):
            require(os.getpid()==self.pid and threading.get_ident()==self.thread and not self.failed,
                'SAME_PRODUCT_AUDIT_OWNER_NO_RETRY')
        def seal(self):
            self.owner_check()
            require(self.bound and self.api.transfer is self.adapter and self.link.handoff.api is self.api
                and getattr(self.policy.arm,'__self__',None) is self and self.policy.attempts==self.allowed
                and self.policy.denied is self.original_denied
                and all(fn.__code__ is body for fn,body in self.method_pins),'UNCHANGED_PRIVATE_PRODUCT_FACTORY_BINDING')
        def arm(self,context):
            try:
                self.seal();require(self.arm_attempts==0,'ONE_PRODUCT_PROCESS_POLICY_ARM')
                self.arm_attempts=1
                require(context is self.link.context and not context.active and context.attempts==context.jobs==0
                    and self.once.phase=='ENTRY' and self.once.claim_pin is not None
                    and self.once.native_authorizations==0 and self.driver.lifecycle_procedure.state.entry_calls==1
                    and self.driver.lifecycle_controllers.relay.phase=='WAIT_ORIGINAL_NATIVE'
                    and not self.original_denied and self.factory_attempts==self.allowed==self.denied==0,
                    'ORIGINAL_PROCESS_POLICY_ARM_AFTER_WHOLE_OPENING_BEFORE_NATIVE')
                self.driver.coordinator_boundary.seal();self.armed=True
            except BaseException:self.failed=True;raise
        def bind_parent(self,driver,once,raw_transfer):
            self.owner_check();exact(raw_transfer,PROCESS_TRANSFER)
            link=driver.parent_handoff;lazy=link.handoff;api=lazy.api;original=api.transfer
            tree=ast.parse(raw_transfer);code=compile(raw_transfer,PROCESS_TRANSFER['path'],'exec')
            require(not self.ever_bound and self.registrations==1 and self.allowed==self.factory_attempts==self.denied==0
                and self.original_denied==[] and link.context.attempts==link.context.jobs==link.state.attempts==0
                and lazy.actual is None and len(lazy.required)==202 and lazy.required.get(PRODUCT_ENTRY)==lazy.entry_pin
                and lazy.root==self.root and driver.lifecycle_controllers.route.context is link.context,
                'ONE_UNUSED_ACTUAL_PARENT_AND_REGISTERED_ORIGINAL_DENY')
            methods=tuple(n.name for n in next(n for n in tree.body
                if isinstance(n,ast.ClassDef) and n.name=='Handoff').body if isinstance(n,ast.FunctionDef))
            def matches(code):
                original_class=nested(code,'Handoff')
                return (type(original.connect) is FunctionType and shape(original.connect.__code__)==shape(nested(code,'connect'))
                    and all(type(vars(original.Handoff).get(name)) is FunctionType
                        and shape(vars(original.Handoff)[name].__code__)==shape(nested(original_class,name)) for name in methods))
            if matches(code):self.transfer_compile_form='whole_source'
            else:
                code=compile(ast.fix_missing_locations(ast.Module(body=[n for n in tree.body
                    if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),PROCESS_TRANSFER['path'],'exec')
                require(matches(code),'ENTIRE_ORIGINAL_SOURCE_HANDOFF_AND_CONNECT_LOADER_FORM')
                self.transfer_compile_form='pinned_namespace_loader_all_non_import_AST'
            self.driver=driver;self.once=once;self.link=link;self.api=api;self.original_transfer=original
            self.method_pins=[(original.connect,original.connect.__code__),
                *((vars(original.Handoff)[name],vars(original.Handoff)[name].__code__) for name in methods)]
            def connect(*args,**options):
                self.seal()
                require(self.armed and not options and len(args)==12 and args[0] is lazy and args[2]==self.root
                    and args[3]==lazy.entry_pin and args[4] is link.original_component
                    and args[5] is api.protocol and args[6] is api.readiness and args[7] is self.original_factory
                    and getattr(args[-1],'__self__',None) is link.context
                    and link.context.active and link.context.attempts==1 and link.context.jobs==0
                    and link.state.component_connections==1 and self.connections==0,
                    'ONE_ORIGINAL_COMPONENT_FACTORY_DEPENDENCY_BEFORE_JOB_OR_FRAME')
                self.connections=1
                def create(command,**kwargs):return self.create(command,**kwargs)
                return original.connect(*args[:7],create,*args[8:])
            self.adapter=NS(**{**vars(original),'connect':connect});api.transfer=self.adapter
            self.bound=self.ever_bound=True;self.seal()
        def live(self):
            self.seal();self.once.owner_check();context=self.link.context;lazy=self.link.handoff;actual=lazy.actual
            require(self.armed and self.once.phase=='ENTRY' and not self.once.failed and self.once.claim_pin is not None
                and self.once.native_authorizations==self.once.invocations==self.once.entry_calls==1
                and self.driver.lifecycle_procedure.state.entry_calls==1
                and context.active and context.attempts==context.jobs==context.parent.attempts==1
                and context.restorations==0 and context.owner is not None and context.job is not None
                and len(context.bindings)==1 and len(context.parent.frames)==1
                and actual is not None and actual is self.actual_scope and actual.phase=='SPAWNING'
                and actual.attempts==1 and not actual.failed and actual.process is None,
                'ORIGINAL_CLAIMED_NATIVE_OWNER_JOB_AND_ACTUAL_SPAWNING_HANDOFF')
            require(self.driver.coordinator_boundary.state.pre_native==1
                and not self.driver.coordinator_boundary.state.failed,'ORIGINAL_COORDINATOR_PRE_NATIVE_BOUNDARY_COMPLETED')
            frame=context.parent.frames[0];loan=actual.loan;descriptor=actual.descriptor
            require(type(frame) is lazy.connection.frame_type and actual.frame is frame
                and frame.state=='BEFORE_READ' and frame.registered and not frame.reading and len(frame.boundaries)==1
                and frame.held.acquired and not frame.held.closed and not frame.held.releasing
                and loan is not None and loan.frame is frame and loan.state=='ARMED' and not loan.failed
                and loan.arm_attempts==1 and loan.armed_count==202 and len(loan.handles)==202
                and descriptor is not None and descriptor.prepared and not descriptor.failed
                and descriptor.writer is None and type(descriptor.reader) is int and descriptor.reader>0
                and descriptor.close_failures==0,'SAME_FIRST_WHOLE_FRAME_AND_202_ARMED_SOURCE_HANDLES')
            self.driver.coordinator_boundary.seal();context.checkpoint()
            return actual
        def create(self,command,**options):
            self.owner_check()
            require(self.registrations==1 and self.factory_attempts==0 and self.allowed==self.denied==0
                and self.original_denied==[],'ONE_PRODUCT_FACTORY_ATTEMPT_WITH_ORIGINAL_DENY')
            self.factory_attempts=1;self.actual_scope=self.link.handoff.actual
            try:
                actual=self.live();frame=sys._getframe(2)
                require(frame.f_code is self.original_transfer.Handoff.spawn.__code__
                    and frame.f_globals is self.original_transfer.Handoff.spawn.__globals__
                    and frame.f_locals.get('self') is actual and frame.f_locals.get('child_command') is command,
                    'ONLY_ACTUAL_WHOLE_ORIGINAL_SOURCE_SPAWN_FACTORY_SITE')
                require(type(command) is list and len(command)==11
                    and command[:3]==[sys.executable,'-B',str(self.root/PRODUCT_ENTRY)]
                    and command[3]=='--ready-handle' and command[5:8]==['--task',PRODUCT_TASK,'--source-mapping']
                    and all(type(command[i]) is str and re.fullmatch('[1-9][0-9]{0,19}',command[i]) is not None
                        and int(command[i])<2**64 for i in (4,8)) and command[4]!=command[8]
                    and type(command[9]) is str and re.fullmatch('[1-9][0-9]{0,5}',command[9]) is not None
                    and 0<int(command[9])<=262144 and re.fullmatch('[0-9a-f]{64}',command[10]) is not None,
                    'EXACT_PRODUCT_WORKER202_ENTRY_TASK_MAPPING_COMMAND')
                raw=frame.f_locals.get('raw');descriptor=actual.descriptor
                require(type(raw) is bytes and len(raw)==int(command[9])
                    and hashlib.sha256(raw).hexdigest()==command[10] and descriptor.reader==int(command[8]),
                    'SAME_ACTUAL_READONLY_MAPPING_PACKET_NOT_SOURCE_CREDIT')
                attrs=getattr(options.get('startupinfo'),'lpAttributeList',None)
                handles=None if type(attrs) is not dict else attrs.get('handle_list')
                require(set(options)=={'cwd','stdin','stdout','stderr','creationflags','startupinfo','close_fds'}
                    and options['cwd']==self.root and options['close_fds'] is True
                    and all(options[key]==subprocess.PIPE for key in ('stdin','stdout','stderr'))
                    and options['creationflags']==subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW
                    and type(handles) is list and handles==[*actual.loan.handles,descriptor.reader,int(command[4])]
                    and len(handles)==len(set(handles))==204,'EXACT_202_SOURCE_MAPPING_EVENT_HANDLE_ORDER_AND_ORIGINAL_FLAGS')
                self.command=tuple(command)
                # Capture from the original connect() parameter, never look up
                # the global Popen while strict-window temporarily wraps it.
                return self.original_factory(command,executable=sys.executable,**options)
            except BaseException:self.failed=True;raise
            finally:self.command=None;self.actual_scope=None
        def permit(self,values):
            if not (self.bound and not self.failed and self.command is not None and self.factory_attempts==1
                and self.allowed==0 and os.getpid()==self.pid and threading.get_ident()==self.thread
                and len(values)==4 and values[0]==sys.executable and values[1] in
                    (list(self.command),subprocess.list2cmdline(self.command))
                and str(values[2])==str(self.root) and values[3] is None):return False
            self.live();self.allowed=1;self.policy.attempts=1;return True
        def restore(self):
            if self.restored:return
            try:
                require(self.ever_bound and not self.link.context.active and self.api.transfer is self.adapter,
                    'ORIGINAL_OWNER_TERMINAL_BEFORE_FACTORY_RESTORE')
                self.api.transfer=self.original_transfer;self.bound=False;self.armed=False;self.restored=True
            except BaseException as error:self.restore_errors.append(type(error).__name__);self.failed=True
        def evidence(self):
            return dict(original_deny_registrations=self.registrations,private_factory_dependency_connected=self.ever_bound,
                original_transfer_compile_form=self.transfer_compile_form,
                original_process_policy_arm_attempts=self.arm_attempts,product_scope_armed=self.armed,
                original_policy_Popen_attempts=self.policy.attempts,
                component_connections=self.connections,factory_attempts=self.factory_attempts,allowed_Popen_events=self.allowed,
                denied_Popen_events=self.denied,original_denied_events=0 if self.original_denied is None else len(self.original_denied),
                scope_active=self.command is not None,failed=self.failed,original_private_dependency_restored=self.restored,
                restore_error_types=list(self.restore_errors),original_Job_Frame_READY15_product10_and_guards_replaced=False,
                global_Popen_looked_up_inside_actual_spawn=False,actual_Native_or_product_process_qualified=False,
                GO_authorized=False,accepted_count_delta=0)
    return ProductAudit


class Finish:
    """Attempt original teardown once, preserving an already active error."""
    def __init__(self,original):self.original=original;self.failed=False;self.error_type=None;self.calls=0
    def __getattr__(self,name):return getattr(self.original,name)
    def finish_native(self,context):
        active=sys.exception();self.calls+=1
        try:return self.original.finish_native(context)
        except BaseException as error:
            self.failed=True;self.error_type=type(error).__name__
            if active is None:raise
            # The original finally resumes that exact primary exception.
            # No closing/oracle or success is reachable on this path.


def preparation(raw,original,actual_context=None):
    """Retain all original epoch bodies; select the actual new parent context.

    This is not a new sampling policy. Only the obsolete readiness-context
    lookup is replaced in a private namespace. No owner or clock is adopted,
    reset or populated with prepared evidence. A caller must create/bind the
    original epochs before its readers, and still connect the Native handoff.
    """
    exact(raw,PREPARATION)
    idle=original.idle;source=compile(raw,PREPARATION['path'],'exec')
    require(type(idle) is FunctionType and idle.__code__.co_filename.replace('\\','/').endswith(PREPARATION['path'])
        and shape(idle.__code__)==shape(nested(source,'idle')),'WHOLE_ORIGINAL_PREPARATION_IDLE_BODY')
    base=original.ReadOnlyEpochs;class_code=nested(source,'ReadOnlyEpochs')
    names=('__init__','check','bind','advance','_release','close')
    methods={name:vars(base)[name] for name in names}
    require(base.STAGES==('construction','opening_and_metadata','closing')
        and all(type(fn) is FunctionType and fn.__globals__ is idle.__globals__
            and shape(fn.__code__)==shape(nested(class_code,name)) for name,fn in methods.items()),
        'ALL_ORIGINAL_PREPARATION_EPOCH_METHOD_BODIES')
    env=dict(idle.__globals__)
    def clone(fn):
        value=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
        value.__kwdefaults__=None if fn.__kwdefaults__ is None else dict(fn.__kwdefaults__);return value
    def context(result):
        seal()
        require(actual_context is not None and actual_context.parent is result.assembled.batch.parent_connection.state,
            'ACTUAL_NEW_PARENT_CONTEXT_NOT_READINESS_CLOSURE')
        fn=result.assembled.built.window.WINDOW_LINK.connect_engine
        require(type(fn) is FunctionType and fn.__closure__ is None
            and fn.__code__.co_filename.replace('\\','/').endswith('strict_product_window_connection_v1.py'),
            'UNCHANGED_UNINJECTED_STRICT_WINDOW_NOT_FABRICATED_READINESS')
        return actual_context
    selected_idle=clone(idle);selected_methods={name:clone(fn) for name,fn in methods.items()}
    env.update(idle=selected_idle,readiness_context=context)
    attrs={name:value for name,value in vars(base).items() if name not in ('__dict__','__weakref__')}
    attrs.update(selected_methods)
    private=type(base.__name__,base.__bases__,attrs);env['ReadOnlyEpochs']=private
    bindings={name:env[name] for name in ('idle','readiness_context','require','time','os','threading','ReadOnlyEpochs')}
    code_snapshot={name:fn.__code__ for name,fn in selected_methods.items()}
    idle_code=selected_idle.__code__;context_code=context.__code__;require_code=env['require'].__code__
    def seal():
        require(all(env[name] is value for name,value in bindings.items())
            and selected_idle.__code__ is idle_code and context.__code__ is context_code
            and env['require'].__code__ is require_code
            and private.STAGES==base.STAGES==('construction','opening_and_metadata','closing')
            and all(vars(private)[name] is fn and fn.__code__ is code_snapshot[name]
                for name,fn in selected_methods.items()),'SEALED_ORIGINAL_PREPARATION_METHODS_AND_CONTEXT_DEPENDENCY')
    class Epochs(private):
        def __init__(self,*args,**kwargs):seal();super().__init__(*args,**kwargs)
        def bind(self,*args,**kwargs):
            try:seal();return super().bind(*args,**kwargs)
            except BaseException:self.broken=True;raise
        def advance(self,*args,**kwargs):
            try:seal();return super().advance(*args,**kwargs)
            except BaseException:self.broken=True;raise
    seal()
    def bind_context(value):
        nonlocal actual_context
        seal();require(actual_context is None and value is not None,'ONE_ACTUAL_PREPARATION_CONTEXT_BINDING')
        actual_context=value
    return NS(Epochs=Epochs,idle=selected_idle,seal=seal,bind_context=bind_context,original_method_codes=code_snapshot,
        projection=dict(entire_original_idle_body_retained=True,all_original_epoch_method_bodies_retained=True,
            private_dependency_changes=['readiness_context','idle'],actual_original_parent_context_dependency=True,
            original_three_stage_order_and_failure_latch_retained=True,new_guard_sampler_or_timer_created=False,
            default_module_changed=False,actual_controller_or_Native_handoff_connected=False,
            actual_Native_or_product_qualified=False,GO_authorized=False))


def controllers(raws,libraries,factory,exact_pin,*,identity=None):
    """Original pipeline created BEFORE readers capture its stable checkpoint.

    No Native admission, worker exception, product authorization or oracle
    input facade is implied. In particular WAIT still rejects ordinary IO.
    """
    require(set(raws)=={pin['path'] for pin in CONTROLLERS},'EXACT_ORIGINAL_CONTROLLER_SOURCES')
    for pin in CONTROLLERS:exact(raws[pin['path']],pin)
    names=('batch_zlib_metadata','batch_native_checkpoint','batch_post_job_checkpoint',
        'preparation_checkpoint_owner','batch_post_native','batch_pre_go_runtime')
    parts=[getattr(libraries,name) for name in names]
    targets=(('ReadOnlyEpochs','idle'),('Handoff',),('handoff_type',),
        ('Checkpoint',),('Closing',),('source_checkpoint','connect_callback'))
    compile_forms={}
    for pin,part,selected in zip(CONTROLLERS,parts,targets):
        tree=ast.parse(raws[pin['path']])
        def matches(code):
            for name in selected:
                value=getattr(part,name);expected=nested(code,name)
                if type(value) is FunctionType:
                    if shape(value.__code__)!=shape(expected):return False
                else:
                    node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
                    for method_name in (n.name for n in node.body if isinstance(n,ast.FunctionDef)):
                        method=nested(expected,method_name);actual=vars(value).get(method_name)
                        if type(actual) is not FunctionType or shape(actual.__code__)!=shape(method):return False
            return True
        if matches(compile(raws[pin['path']],pin['path'],'exec')):
            compile_forms[pin['path']]='whole_source'
        else:
            # The pinned namespace loader resolves import aliases separately
            # and compiles EVERY other original AST node in its original order.
            # Match that exact compiler input, not an edited function or a
            # name-only allowance. No method body/default AST is changed.
            nodes=[node for node in tree.body if not isinstance(node,(ast.Import,ast.ImportFrom))]
            code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),pin['path'],'exec')
            require(matches(code),'ENTIRE_ORIGINAL_CONTROLLER_FUNCTION_AND_CLASS_METHODS')
            compile_forms[pin['path']]='pinned_namespace_loader_all_non_import_AST'
    metadata,native,post_job,checkpoint,closing,prior=parts
    selected=preparation(raws[PREPARATION['path']],metadata)
    options={} if identity is None else dict(identity=identity)
    epochs=selected.Epochs(factory,**options)
    Handoff=post_job.handoff_type(native.Handoff,raws[CONTROLLERS[7]['path']])
    relay=Handoff(epochs,selected.idle,**options)
    source=prior.source_checkpoint(relay)
    owner=checkpoint.Checkpoint(relay,source,raws[CONTROLLERS[6]['path']],**options)
    route=closing.Closing(relay,owner.checkpoint,factory,exact_pin,**options)
    state=NS(reader_bound=False,parent_bound=False,closed=False,restore=None,cleanup_errors=[],coordinator_bound=False,
        process_audit_bound=False,oracle_inputs_bound=False)
    def bind_reader(reader):
        try:
            require(not state.closed and not state.reader_bound and reader.checkpoint is route.checkpoint,
                'ONE_CONTROLLER_CONSTRUCTION_READER_WITH_STABLE_CHECKPOINT')
            owner.bind_reader(reader);state.reader_bound=True
        except BaseException:relay.broken=True;epochs.broken=True;raise
    def bind_parent(result,actual):
        try:
            require(not state.closed and state.reader_bound and not state.parent_bound,
                'ONE_ACTUAL_PARENT_AFTER_STABLE_READER_CAPTURE')
            selected.bind_context(actual)
            relay.bind(result);route.bind_context(actual)
            state.restore=prior.connect_callback(NS(result=result),relay,actual)
            state.parent_bound=True
        except BaseException:relay.broken=True;epochs.broken=True;raise
    def close():
        if state.closed:return
        state.closed=True
        for action in (state.restore,route.close,epochs.close):
            if action is None:continue
            try:action()
            except BaseException as error:state.cleanup_errors.append(type(error).__name__)
    def cleanup():
        return (state.closed and not state.cleanup_errors and bool(epochs.records)
            and all(row['cleanup_confirmed'] is True for row in epochs.records)
            and route.cleanup in (None,True) and (route.context is None or not route.context.active))
    def evidence():
        return dict(pipeline_created_before_reader_capture=True,construction_reader_bound=state.reader_bound,
            whole_original_controller_compile_forms=dict(compile_forms),
            actual_parent_and_original_metadata_callback_bound=state.parent_bound,
            relay=relay.evidence(),post_native=route.evidence(),preparation_checkpoint_owner=owner.evidence(),
            preparation_context_projection=selected.projection,cleanup_confirmed=cleanup(),
            cleanup_error_types=list(state.cleanup_errors),guard_clock_or_execution_counter_adopted_or_reset=False,
            coordinator_pre_Native_and_terminal_transition_connected=state.coordinator_bound,
            actual_worker202_product_process_audit_connected=state.process_audit_bound,actual_oracle_data_facade_connected=state.oracle_inputs_bound,
            actual_full_controller_transition_or_Native_qualified=False,GO_authorized=False,accepted_count_delta=0)
    return NS(epochs=epochs,relay=relay,route=route,owner=owner,checkpoint=route.checkpoint,
        preparation=selected,bind_reader=bind_reader,bind_parent=bind_parent,close=close,cleanup=cleanup,
        evidence=evidence,state=state)


def coordinator_checkpoint(driver,once):
    require(driver.coordinator_boundary is not None,'COORDINATOR_BOUND_TO_SAME_ACTUAL_DRIVER')
    return driver.coordinator_boundary.check(once,sys._getframe(1))


def bind_coordinator(raw,once,driver,pipeline,procedure):
    """Two pure lifecycle checks, exclusively from original Once._checked.

    Ordinary reader/Native checkpoints never use this path. WAIT permits no
    IO; terminal uses original counter-only _terminal/_checker inspection,
    NOT _closed_oracle_case (which would call the already closed guard).
    """
    exact(raw,ONCE);cls=type(once);tree=ast.parse(raw)
    node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Once')
    names=tuple(n.name for n in node.body if isinstance(n,ast.FunctionDef))
    originals={name:vars(cls).get(name) for name in names}
    require(all(type(fn) is FunctionType for fn in originals.values()),'ORIGINAL_WHOLE_ONCE_METHOD_FAMILY')
    def matches(module):
        code=nested(module,'Once')
        return all(shape(fn.__code__)==shape(nested(code,name)) for name,fn in originals.items())
    code=compile(raw,ONCE['path'],'exec')
    if not matches(code):
        code=compile(ast.fix_missing_locations(ast.Module(body=[n for n in tree.body
            if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),ONCE['path'],'exec')
    require(matches(code),'ENTIRE_ORIGINAL_ONCE_CLASS_NOT_PARTIAL_GATE')
    bridge=once.checkpoint;bridge_code=nested(nested(code,'construct_entry'),'checkpoint')
    require(type(bridge) is FunctionType and shape(bridge.__code__)==shape(bridge_code)
        and bridge.__globals__ is originals['_checked'].__globals__,'WHOLE_ORIGINAL_ONCE_CONSTRUCTION_CHECKPOINT')
    cells=dict(zip(bridge.__code__.co_freevars,(c.cell_contents for c in bridge.__closure__ or ())))
    require(set(cells)=={'box','checkpoint_route','once'} and type(cells['box']) is list and len(cells['box'])==1
        and cells['box'][0] is driver and cells['once'] is once and cells['checkpoint_route'] is coordinator_checkpoint,
        'EXPLICIT_ORIGINAL_BRIDGE_TO_SAME_DRIVER_AND_ONCE')
    require(driver.lifecycle_controllers is pipeline and driver.lifecycle_procedure is procedure
        and pipeline.state.parent_bound and not pipeline.state.closed and not pipeline.state.coordinator_bound
        and once.phase=='NEW' and once.invocations==once.entry_calls==once.native_authorizations==0,
        'ONE_UNUSED_ACTUAL_CONTROLLER_COORDINATOR_BINDING')
    actual=driver.lifecycle_context.result.assembled.parent.run_owned
    saved=[(fn,fn.__code__,fn.__defaults__,fn.__closure__,None if fn.__kwdefaults__ is None else dict(fn.__kwdefaults__))
        for fn in (*originals.values(),bridge,actual)]
    parent_cells=dict(zip(actual.__code__.co_freevars,(c.cell_contents for c in actual.__closure__ or ())))
    require(parent_cells.get('context') is pipeline.route.context
        and getattr(parent_cells.get('authorize'),'__self__',None) is once,'SAME_ORIGINAL_PARENT_EXECUTION_DEPENDENCY')
    callback_code=coordinator_checkpoint.__code__
    terminal=getattr(pipeline.route._terminal,'__func__',pipeline.route._terminal)
    checker=getattr(pipeline.route._checker,'__func__',pipeline.route._checker)
    saved.extend((fn,fn.__code__,fn.__defaults__,fn.__closure__,None if fn.__kwdefaults__ is None else dict(fn.__kwdefaults__))
        for fn in (terminal,checker))
    state=NS(delegated=0,pre_native=0,terminal=0,failed=False)
    def seal():
        require(not state.failed and once.checkpoint is bridge and type(once) is cls
            and all(vars(cls)[name] is fn for name,fn in originals.items())
            and all(fn.__code__ is body and fn.__defaults__ is defaults and fn.__closure__ is closure
                and fn.__kwdefaults__==keywords for fn,body,defaults,closure,keywords in saved)
            and coordinator_checkpoint.__code__ is callback_code
            and len(cells['box'])==1 and cells['box'][0] is driver
            and all(cell.cell_contents is cells[name] for name,cell in zip(bridge.__code__.co_freevars,bridge.__closure__))
            and driver.lifecycle_controllers is pipeline and driver.lifecycle_procedure is procedure
            and driver.lifecycle_context.result.assembled.parent.run_owned is actual
            and getattr(pipeline.route._terminal,'__func__',pipeline.route._terminal) is terminal
            and getattr(pipeline.route._checker,'__func__',pipeline.route._checker) is checker,
            'UNCHANGED_ORIGINAL_ONCE_PARENT_AND_COORDINATOR_BINDINGS')
        procedure.seal();once.owner_check()
    def check(value,frame):
        try:
            seal();require(value is once and type(frame) is FrameType and frame.f_code is bridge.__code__
                and frame.f_globals is bridge.__globals__,'ONLY_ACTUAL_ORIGINAL_CHECKPOINT_BRIDGE_FRAME')
            checked=frame.f_back;caller=None if checked is None else checked.f_back
            require(checked is not None and checked.f_code is originals['_checked'].__code__
                and checked.f_globals is originals['_checked'].__globals__ and checked.f_locals.get('self') is once
                and caller is not None and caller.f_locals.get('self') is once,
                'ONLY_ACTUAL_ORIGINAL_ONCE_CHECKED_CALL')
            phase=checked.f_locals.get('phase');route=pipeline.route;relay=pipeline.relay;epochs=pipeline.epochs
            require(not pipeline.state.closed and not relay.broken and not route.broken and not epochs.broken,
                'LIVE_SAME_UNFAILED_ORIGINAL_CONTROLLER_PIPELINE')
            if relay.phase=='PREPARATION':
                require(phase in ('NEW','CLAIMING') and once.phase==phase
                    and caller.f_code is originals['execute'].__code__,'ONLY_ORIGINAL_PREPARATION_ONCE_CHECKS')
                state.delegated+=1;return pipeline.checkpoint()
            require(phase==once.phase=='ENTRY' and not once.failed and once.claim_pin is not None
                and once.invocations==once.external_calls==once.intent_attempts==once.entry_calls==once.native_authorizations==1
                and procedure.state.invocations==procedure.state.entry_calls==1,'ONE_CLAIMED_COMPLETE_ORIGINAL_ENTRY')
            if relay.phase=='WAIT_ORIGINAL_NATIVE':
                parent=caller.f_back
                require(caller.f_code is originals['authorize_native'].__code__ and parent is not None
                    and parent.f_code is actual.__code__ and parent.f_globals is actual.__globals__
                    and parent.f_locals.get('state') is parent_cells['state']
                    and parent.f_locals.get('context') is route.context and parent.f_locals.get('run')==1,
                    'ONLY_ORIGINAL_PARENT_PRE_NATIVE_AUTHORIZATION_CALL')
                require(state.pre_native==state.terminal==0 and not procedure.state.original_procedure_returned
                    and procedure.state.finish_calls==0 and epochs.closed and epochs.guard is None
                    and [r['stage'] for r in epochs.records]==['construction','opening_and_metadata']
                    and all(r['cleanup_confirmed'] is True for r in epochs.records)
                    and route.phase=='ORIGINAL' and route.guard is None and relay.bindings==0
                    and parent_cells['state'].attempts==0 and not parent_cells['state'].failed,
                    'CLOSED_PREPARATION_BEFORE_UNSTARTED_ORIGINAL_NATIVE_NOT_IO')
                pipeline.preparation.idle(route.result)
                state.pre_native=1;return None
            require(relay.phase=='NATIVE_TERMINAL' and caller.f_code is originals['execute'].__code__
                and caller.f_locals.get('entry') is procedure.state.active_entry
                and caller.f_locals.get('result') is procedure.state.returned_result
                and state.pre_native==1 and state.terminal==0 and procedure.state.original_procedure_returned
                and procedure.state.finish_calls==1 and not procedure.state.finish_failed
                and route.phase=='CHECKED_NOT_ACCEPTED' and route.guard is None and route.cleanup is True
                and route.guard_creations==route.oracle_attempts==1 and route.closing_reader is not None,
                'ONLY_COMPLETED_ORIGINAL_ENTRY_AND_CLOSED_ORACLE_OWNER')
            batch,frame=route._terminal();route._checker()
            require(batch.phase=='SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED'
                and route.closing_reader.checkpoint is route.checkpoint
                and frame.state=='COMMITTED','ORIGINAL_FINAL_CLOSING_COMMIT_NOT_NEW_GUARD_OR_IO')
            state.terminal=1;return None
        except BaseException:state.failed=True;raise
    def evidence():
        return dict(connected=True,original_preparation_checks_delegated=state.delegated,
            original_pre_Native_lifecycle_checks=state.pre_native,original_terminal_lifecycle_checks=state.terminal,
            failed=state.failed or once.failed,ordinary_IO_uses_original_route_only=True,original_Native_resource_checks_changed=False,
            new_guard_sampler_or_IO_or_GO_created=False,actual_Native_transition_qualified=False,accepted_count_delta=0)
    seal();pipeline.state.coordinator_bound=True
    return NS(check=check,seal=seal,evidence=evidence,state=state)


def oracle_reader_factory(root,reader,known,loader,batch,admission,a):
    fresh=batch.PacedNamespaceLoader(loader,reader,known).api
    return admission.optimized_reader(root,reader,known,fresh,a.AcceptanceReader,a)


def bind_oracle_inputs(source_reader,reference_reader,context,pipeline,procedure,prepared,bound,checked,a,Reader,policy):
    """Bind the original five-input function to independent expected inputs.

    No candidate is read and no validator is called. Three preserved logical
    reference pins remain separate from current physical source witnesses.
    Their preparation reads are NOT reused for the future original oracle.
    """
    assembled=context.result.assembled;batch=assembled.batch;route=pipeline.route
    require(procedure.state.invocations==0 and batch.phase=='NEW' and route.phase=='ORIGINAL'
        and route.result is context.result and route.context.parent is batch.parent_connection.state
        and batch.checkpoint is route.checkpoint and assembled.built is prepared.linked
        and assembled.checker is checked.checker and context.connected is bound.connected
        and bound.connected.core is prepared.entry.core and context.result.attached is bound.attached
        and reference_reader.checkpoint is source_reader.checkpoint is route.checkpoint
        and reference_reader.snapshots=={} and reference_reader.read_passes==reference_reader.bytes_read==0,
        'SAME_UNUSED_ACTUAL_ORACLE_CONTEXT_AND_FRESH_REFERENCE_READER')
    original_checker=route._checker();generator=assembled.checker.environment['context']
    require(type(generator) is FunctionType and type(original_checker) is FunctionType and callable(Reader)
        and callable(policy.arm),'ORIGINAL_CONTEXT_GENERATOR_CHECKER_AND_EXPLICIT_READER_POLICY')
    step=assembled.built.window.M.base.CONFIG;core=bound.connected.core
    row=a.read_exact(source_reader,ORACLE_STEP)
    require(type(row) is dict and set(row)=={'schema_version','index','before','case','prior_queue_pin','prior_candidate_pin'}
        and row['schema_version']=='hwpx-agent.p09-flat-current-queue-step/v1'
        and type(row['index']) is int and row['index']==165 and type(row['before']) is int and row['before']==158
        and core['step']==row and step.path==ORACLE_STEP['path'] and step.pin==ORACLE_STEP
        and all(getattr(step,name)==value for name,value in row.items()),'EXACT_INDEPENDENT_CURRENT_STEP_NOT_CANDIDATE')
    expected={**row,'prior_queue_pin':dict(row['prior_queue_pin']),'prior_candidate_pin':dict(row['prior_candidate_pin'])}
    for actual,pin in zip((a.scope.LIST_PIN,a.BODY_PIN,a.FRESH_PIN),ORACLE_REFERENCES):
        a.exact(actual,pin,'UNCHANGED_ORIGINAL_ORACLE_REFERENCE_PIN')
        a.exact(dict(checked.known[pin['path']]),pin,'INDEPENDENTLY_DECLARED_LOGICAL_ORACLE_REFERENCE')
    listing=a.read_exact(reference_reader,ORACLE_REFERENCES[0])
    for pin in ORACLE_REFERENCES[1:]:a.exact(reference_reader.pin(pin['path']),pin,'PRESERVED_REFERENCE_BYTES_NOT_NATIVE_CREDIT')
    require(type(listing['source_test_names']) is list and len(listing['source_test_names'])==249
        and listing['source_test_names'][164]==expected['case'],'ORIGINAL_LIST_EXACT_CURRENT_CASE')
    generated=generator(step)
    require(type(generated.INDEX) is int and generated.INDEX==165 and type(generated.BEFORE) is int and generated.BEFORE==158
        and generated.CASE==expected['case'] and generated.PRIOR_ACCEPT_PIN==expected['prior_queue_pin']
        and generated.arguments()==[expected['case'],'--exact','--test-threads=1','--format=pretty','--color=never'],
        'ACTUAL_ORIGINAL_CONTEXT_GENERATOR_SELECTS_ONE_CURRENT_CASE')
    api=NS(c=a.c,scope=NS(LIST_PIN=dict(ORACLE_REFERENCES[0])),BODY_PIN=dict(ORACLE_REFERENCES[1]),
        FRESH_PIN=dict(ORACLE_REFERENCES[2]),read_exact=a.read_exact,packed=a.packed)
    funcs=(generator,original_checker,a.read_exact,a.packed.unpack)
    saved=[(fn,fn.__code__,fn.__globals__,fn.__defaults__,fn.__closure__,
        None if fn.__kwdefaults__ is None else dict(fn.__kwdefaults__)) for fn in funcs]
    packed=a.packed;read_exact=a.read_exact;unpack=a.packed.unpack
    core_step=core['step']
    def seal():
        procedure.seal()
        require(context.result.assembled is assembled and assembled.batch is batch and route.result is context.result
            and context.connected is bound.connected and bound.connected.core is core and core['step'] is core_step
            and core_step==expected and all(getattr(step,name)==value for name,value in expected.items())
            and assembled.built is prepared.linked and assembled.built.window.M.base.CONFIG is step
            and step.path==ORACLE_STEP['path'] and step.pin==ORACLE_STEP
            and assembled.checker is checked.checker and checked.checker.environment['context'] is generator
            and checked.checker.validate_candidate is original_checker and route._checker() is original_checker
            and api.c is a.c and api.c.ROOT==a.c.ROOT and api.read_exact is read_exact
            and api.packed is packed and api.packed.unpack is unpack
            and all(fn.__code__ is body and fn.__globals__ is env and fn.__defaults__ is defaults
                and fn.__closure__ is closure and fn.__kwdefaults__==keywords for fn,body,env,defaults,closure,keywords in saved),
            'UNCHANGED_ORIGINAL_ORACLE_DATA_AND_FUNCTION_BINDINGS')
        for actual,pin in zip((api.scope.LIST_PIN,api.BODY_PIN,api.FRESH_PIN),ORACLE_REFERENCES):
            a.exact(actual,pin,'SEALED_ORIGINAL_ORACLE_INPUT_API')
    seal();procedure.bind_inputs(context,api,Reader,policy,seal)
    return NS(api=api,Reader=Reader,policy=policy,seal=seal,proof=dict(connected=True,
        original_oracle_inputs_function_body_retained=True,original_validator_or_context_generator_replaced=False,
        original_context_generator_preflight_calls=1,index=165,before=158,
        expected_step_pin=dict(ORACLE_STEP),independent_reference_pins=[dict(pin) for pin in ORACLE_REFERENCES],
        reference_pin_source='original_fixed_declarations_not_candidate',preserved_logical_references_not_current_physical_scope=True,
        preparation_reference_reads_not_future_oracle_credit=True,future_oracle_inputs_must_be_fresh=True,
        canonical_candidate_read=False,original_candidate_validator_executed=False,
        actual_Native_or_product_or_oracle_qualified=False,GO_authorized=False,accepted_count_delta=0))


def build(raw,original,parent_raw):
    exact(raw,SOURCE);exact(parent_raw,PARENT)
    names=('execute_chain','oracle_inputs');functions={name:getattr(original,name) for name in names}
    require(all(type(fn) is FunctionType and fn.__code__.co_filename.replace('\\','/').endswith(SOURCE['path'])
        for fn in functions.values()) and functions[names[0]].__globals__ is functions[names[1]].__globals__,
        'ORIGINAL_WHOLE_ENTRY_AND_ORACLE_FUNCTION_FAMILY')
    code=compile(raw,functions['execute_chain'].__code__.co_filename,'exec')
    require(all(shape(nested(code,name))==shape(fn.__code__) for name,fn in functions.items()),
        'BOTH_ENTIRE_ORIGINAL_FUNCTION_CODES')
    parent_code=nested(nested(compile(parent_raw,PARENT['path'],'exec'),'install'),'execute')
    before=functions['execute_chain'].__code__;constants=list(before.co_consts)
    old='RUNNING_ORIGINAL_NATIVE010_PRODUCT_ONCE';positions=[i for i,value in enumerate(constants) if value==old]
    require(len(positions)==1,'ONE_PROGRESS_LABEL_ONLY');constants[positions[0]]='RUNNING_ORIGINAL_NATIVE011_PRODUCT_ONCE'
    revised=before.replace(co_consts=tuple(constants));undo=list(revised.co_consts);undo[positions[0]]=old
    require(revised.replace(co_consts=tuple(undo))==before,'ENTIRE_ORIGINAL_ENTRY_CODE_INVERSE')
    canonical=CANONICAL;env=dict(functions['execute_chain'].__globals__,CANONICAL=canonical)
    def clone(fn,code):
        value=FunctionType(code,env,argdefs=fn.__defaults__,closure=fn.__closure__)
        value.__kwdefaults__=fn.__kwdefaults__;return value
    oracle=clone(functions['oracle_inputs'],functions['oracle_inputs'].__code__)
    execute=clone(functions['execute_chain'],revised);env['oracle_inputs']=oracle
    original_require=env['require'];require_code=original_require.__code__
    state=NS(invocations=0,entry_calls=0,original_procedure_returned=False,finish_calls=0,
        finish_failed=False,finish_error_type=None,active_entry=None,returned_result=None,input_binding=None)
    def seal():
        require(execute.__code__ is revised and oracle.__code__ is functions['oracle_inputs'].__code__
            and execute.__globals__ is oracle.__globals__ is env and env['CANONICAL']==canonical
            and env['oracle_inputs'] is oracle and env['require'] is original_require
            and original_require.__code__ is require_code,'PRIVATE_ORIGINAL_ENTRY_AND_ORACLE_BINDINGS_UNCHANGED')
    def parent(context,route,once,once_type):
        actual=context.result.assembled.parent.run_owned;batch=context.result.assembled.batch
        require(type(actual) is FunctionType and actual.__code__.co_filename.replace('\\','/').endswith(PARENT['path'])
            and shape(actual.__code__)==shape(parent_code),'WHOLE_ORIGINAL_INSTALLED_PARENT_EXECUTE')
        cells=dict(zip(actual.__code__.co_freevars,(value.cell_contents for value in actual.__closure__ or ())))
        dependency=cells.get('authorize');owner=cells['context'];status=cells['state']
        require(getattr(dependency,'__self__',None) is once and getattr(dependency,'__func__',None) is once_type.authorize_native
            and owner is route.context and owner.parent is batch.parent_connection.state
            and owner.active is False and owner.attempts==owner.jobs==owner.restorations==0
            and status.attempts==0 and status.failed is False and owner.parent.attempts==0 and owner.parent.frames==[]
            and batch.phase=='NEW' and batch.checkpoint is route.checkpoint,
            'SAME_UNUSED_ORIGINAL_OWNER_AND_ONCE_DEPENDENCY')
    def invoke(once,once_type,write_intent,context,route,relay,epochs,Reader,process_policy,a,progress):
        require(state.invocations==0,'ONE_LIFECYCLE_INVOCATION_NO_RETRY');state.invocations=1
        require(type(once) is once_type and callable(getattr(once_type,'authorize_native',None)),
            'EXPLICIT_ORIGINAL_ONCE_COORDINATOR_TYPE')
        once.owner_check();seal();parent(context,route,once,once_type)
        if state.input_binding is not None:
            item=state.input_binding
            require(context is item.context and a is item.api and Reader is item.Reader and process_policy is item.policy,
                'SAME_BOUND_ORACLE_CONTEXT_API_READER_AND_PROCESS_POLICY')
            item.seal()
        def entry():
            seal();parent(context,route,once,once_type);state.entry_calls+=1
            finish=Finish(relay)
            try:
                result=execute(context,route,finish,epochs,Reader,process_policy,a,progress)
                require(not finish.failed and finish.calls==1,'ORIGINAL_NATIVE_TEARDOWN_CONFIRMED_NOT_CAUGHT_FAILURE')
                seal();state.original_procedure_returned=True;state.returned_result=result;return result
            finally:
                state.finish_calls=finish.calls;state.finish_failed=finish.failed;state.finish_error_type=finish.error_type
        state.active_entry=entry
        try:return once.execute(entry,write_intent)
        finally:state.active_entry=None;state.returned_result=None
    def admit_parent_binding(context,actual_context,checkpoint,once,once_type,*,authorize=None):
        require((authorize is None or callable(authorize)) and type(once) is once_type and once.external is authorize and once.phase=='NEW'
            and once.invocations==once.native_authorizations==once.entry_calls==0,
            'INERT_PARENT_BINDING_NOT_EXECUTION_AUTHORITY')
        once.owner_check();seal();parent(context,NS(context=actual_context,checkpoint=checkpoint),once,once_type)
        return dict(actual_original_parent_and_once_binding_attested=True,
            original_controller_or_worker202_process_audit_connected=False,
            original_complete_entry_lifecycle_connected=False,product_or_intent_executed=False)
    def bind_inputs(context,api,Reader,policy,seal_inputs):
        require(state.invocations==0 and state.input_binding is None and callable(Reader) and callable(seal_inputs),
            'ONE_ORACLE_INPUT_BINDING_BEFORE_INVOCATION')
        seal_inputs();state.input_binding=NS(context=context,api=api,Reader=Reader,policy=policy,seal=seal_inputs)
    return NS(invoke=invoke,seal=seal,bind_inputs=bind_inputs,admit_parent_binding=admit_parent_binding,state=state,execute_chain=execute,oracle_inputs=oracle,
        projection=dict(whole_original_entry_code_inverse=True,whole_original_five_oracle_inputs_code_retained=True,
            exact_progress_label_changes=1,canonical_result=canonical,
            original_open_Native_teardown_close_and_oracle_order_retained=True,
            original_Native_Job_Frame_commit_oracle_or_resource_method_replaced=False,
            primary_error_preserved_if_original_teardown_also_fails=True,
            actual_controller_and_worker202_audit_connected=False,actual_Native_or_product_qualified=False,
            queue_acceptance_authorized=False,GO_authorized=False))


def driver_type(base,once,*,process_audit=None,authorize=None):
    """Install original controllers before construction captures its check."""
    class Driver(base):
        def __init__(self):
            super().__init__();self.output=OUTPUT;self.lifecycle_declared=False;self.lifecycle_controllers=None
            self.lifecycle_context=None;self.controller_libraries=None;self.controller_raws=None
            self.lifecycle_procedure=None;self.coordinator_boundary=None
            self.product_audit=process_audit
            self.oracle_inputs=None;self.product_dispatch=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);before=control.admit
            self.controller_raws={pin['path']:direct(root,pin) for pin in CONTROLLERS}
            self.controller_libraries,_=loader.load(root,list(CONTROLLERS[:6]),{})
            def declared(*args,**kwargs):
                require(not self.lifecycle_declared,'ONE_EXPLICIT_LIFECYCLE_DECLARATION')
                require(self.lifecycle_controllers is not None,'ORIGINAL_CONTROLLERS_BEFORE_READER_ADMISSION')
                reader=args[0] if args else kwargs['q']
                require(reader.checkpoint is self.lifecycle_controllers.checkpoint,
                    'ACTUAL_SOURCE_READER_CAPTURED_STABLE_ORIGINAL_ROUTE')
                self.lifecycle_controllers.bind_reader(reader)
                value=before(*args,**kwargs);self.lifecycle_declared=True
                require(len(value.control_names)==74 and not {SELF,TEST}&set(value.control_names),
                    'ORIGINAL74_AND_EXPLICIT_NEW_LIFECYCLE_SOURCES')
                require(PROCESS_AUDIT['path'] not in value.control_names,'ORIGINAL_COMMON_SELF_ROLE_ALREADY_DECLARED')
                explicit=(SELF,TEST,SOURCE['path'],PARENT['path'],*(pin['path'] for pin in CONTROLLERS),
                    PROCESS_CONNECTION['path'],PROCESS_TRANSFER['path'],*DISPATCH,
                    'tools/p09/native011_product_entry.py','tools/p09/tests/test_native011_product_entry.py')
                additions=tuple(name for name in explicit if name not in value.control_names)
                return NS(**{**vars(value),'control_names':value.control_names+additions})
            control.admit=declared
        def acquire(self):
            require(self.bound and self.lifecycle_controllers is None and self.guard is None and not self.records,
                'ONE_NEW_ORIGINAL_CONTROLLER_PIPELINE_NO_GUARD_ADOPTION')
            self.lifecycle_controllers=controllers(self.controller_raws,self.controller_libraries,self.factory,self.a.exact)
            epochs=self.lifecycle_controllers.epochs;epochs.advance('construction')
            self.stage='construction';self.started=epochs.started;self.guard=epochs.guard;self._marker(0)
        @property
        def check(self):
            return super().check if self.lifecycle_controllers is None else self.lifecycle_controllers.checkpoint
        @property
        def cleanup(self):
            original=super().cleanup if self.lifecycle_controllers is None else self.lifecycle_controllers.cleanup()
            return original and (self.product_audit is None or not self.product_audit.restore_errors)
        def close(self):
            if self.lifecycle_controllers is None:return super().close()
            if self.closed:return
            self.closed=True;epochs=self.lifecycle_controllers.epochs
            if epochs.guard is not None:self.last_samples=epochs.guard.samples
            if self.product_audit is not None and self.product_audit.ever_bound:self.product_audit.restore()
            self.lifecycle_controllers.close();self.guard=None
            # Copies of actual original epoch receipts for the existing outer
            # display only. No guard state, credit or counters are adopted.
            self.records=[dict(stage=r['stage'],elapsed_seconds=r['elapsed_seconds'],cleanup_confirmed=r['cleanup_confirmed'],
                resource_samples=len(r['samples']),system_CPU_max=max((s['system_cpu_percent'] for s in r['samples']),default=None),
                available_RAM_min=min((s['available_ram_percent'] for s in r['samples']),default=None),
                guard_kind='approved_preparation') for r in epochs.records]
        def finish(self,root,row,publisher,a):
            super().finish(root,row,publisher,a)
            if self.lifecycle_controllers is not None:
                row['product_controller_pipeline']=self.lifecycle_controllers.evidence()
                if self.coordinator_boundary is not None:row['product_coordinator_boundary']=self.coordinator_boundary.evidence()
                if self.product_audit is not None:row['product_process_audit']=self.product_audit.evidence()
                if self.oracle_inputs is not None:row['product_oracle_inputs']=self.oracle_inputs.proof
                if self.product_dispatch is not None:row['product_dispatch']=self.product_dispatch.evidence()
                if not self.cleanup:row.update(state='FAILED_PRODUCT_CONTROLLER_PIPELINE_CLEANUP_NOT_EXECUTION')
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            closed=(q.read_passes,q.bytes_read,len(q.snapshots),q.final_fresh_hashes)
            reader=a.AcceptanceReader(root,q.checkpoint)
            for name in (SELF,TEST):reader.pin(name)
            libraries,_=private_load(loader,root,reader,a,('batch_product_runtime','batch_zlib_metadata','batch_scope_admission','native011_product_dispatch'),{})
            def source(pin):
                observed,raw=reader._read(pin['path'],parse=True);reader._bind(observed['path'],observed)
                a.exact(observed,pin,'WHOLE_ORIGINAL_LIFECYCLE_SOURCE');return bytes(raw)
            for pin in CONTROLLERS:
                observed=reader.pin(pin['path']);a.exact(observed,pin,'ORIGINAL_CONTROLLER_SOURCE_FRESH_AFTER_BOOTSTRAP')
                require(self.controller_raws[pin['path']]==exact(self.controller_raws[pin['path']],observed),
                    'SAME_EXACT_CONTROLLER_SOURCE_NOT_CURRENT_IO_CREDIT')
            compiled=build(source(SOURCE),libraries.batch_product_runtime,source(PARENT));self.lifecycle_procedure=compiled
            actual_batch=data.planned.batch
            result=NS(assembled=NS(batch=actual_batch,parent=actual_batch.parent_connection.parent,
                built=prepared.linked,checker=checked.checker),attached=bound.attached)
            context=NS(result=result,connected=bound.connected);self.lifecycle_context=context
            admission=compiled.admit_parent_binding(context,self.parent_handoff.context,actual_batch.checkpoint,once,type(once),authorize=authorize)
            selected_preparation=self.lifecycle_controllers.preparation
            self.lifecycle_controllers.bind_parent(result,self.parent_handoff.context)
            self.coordinator_boundary=bind_coordinator(source(ONCE),once,self,self.lifecycle_controllers,compiled)
            require(self.product_audit is not None,'EXPLICIT_PRODUCT_AUDIT_DEPENDENCY')
            for pin in (PROCESS_AUDIT,PROCESS_CONNECTION):a.exact(reader.pin(pin['path']),pin,'UNCHANGED_PRODUCT_AUDIT_IMPLEMENTATION')
            self.product_audit.bind_parent(self,once,source(PROCESS_TRANSFER))
            self.lifecycle_controllers.state.process_audit_bound=True
            optimized=oracle_reader_factory(root,reader,checked.known,loader,batch,libraries.batch_scope_admission,a)
            references=a.AcceptanceReader(root,reader.checkpoint)
            self.oracle_inputs=bind_oracle_inputs(reader,references,context,self.lifecycle_controllers,compiled,
                prepared,bound,checked,a,optimized.Reader,self.product_audit.policy)
            references.finish();references.checkpoint()
            require(references.final_fresh_hashes==len(references.snapshots)==3,'THREE_FRESH_PRESERVED_ORACLE_REFERENCES')
            self.oracle_inputs.proof.update(reference_fresh_inputs=3,reference_final_fresh_hashes=3)
            self.lifecycle_controllers.state.oracle_inputs_bound=True
            self.product_dispatch=libraries.native011_product_dispatch.connect(self,once,root,reader,a,data.planned.current,publisher)
            require(selected_preparation.idle(result) is self.parent_handoff.context,
                'ACTUAL_UNOPENED_PARENT_PASSES_ENTIRE_ORIGINAL_IDLE_INSPECTION')
            require(self.lifecycle_declared and self.construct_only and self.native is None
                and compiled.state.invocations==compiled.state.entry_calls==0,'DEFAULT_LIFECYCLE_CONSTRUCTION_ONLY')
            for name,pin in reader.snapshots.items():
                a.exact(pin,dict(data.planned.current[name]),'DIRECT_CURRENT_LIFECYCLE_SOURCE')
            reader.finish();reader.checkpoint()
            require(closed==(q.read_passes,q.bytes_read,len(q.snapshots),q.final_fresh_hashes),
                'ORIGINAL_CLOSED_CONSTRUCTION_READER_NOT_REOPENED')
            require(reader.final_fresh_hashes==len(reader.snapshots)==24,'EXACT24_LIFECYCLE_ORACLE_AND_DISPATCH_SOURCES')
            return dict(value,state='PASS_PRODUCT_LIFECYCLE_PARENT_BINDING_CONSTRUCTION_NOT_EXECUTION',
                product_lifecycle=dict(projection=compiled.projection,parent_binding=admission,
                    original_procedure_invocations=compiled.state.invocations,connection_fresh_inputs=24,
                    connection_final_fresh_hashes=24,connection_source_pins=list(reader.snapshots.values()),
                    preparation_context_projection=selected_preparation.projection,
                    actual_parent_passed_original_preparation_idle_body=True,
                    actual_oracle_data_facade_connected=True,actual_controller_and_worker202_audit_connected=True,
                    original_closed_reader_reused_or_reset=False,accepted_count_delta=0,GO_authorized=False))
    return Driver


def direct(root,pin):
    path=root/pin['path']
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCE')
        if member==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    return exact(raw,pin)


def construct(*,authorize=None,wrap=None,output=OUTPUT):
    require((authorize is None or callable(authorize)) and (wrap is None or callable(wrap)),'EXPLICIT_NEW_INSTANCE_DEPENDENCIES')
    require(type(output) is str and re.fullmatch(r'implementation/p09/evidence/p09-361-native011-[A-Za-z0-9-]{1,120}\.v1\.json',output),
        'BOUNDED_CONSTRUCTION_OUTPUT_NOT_RUNTIME')
    root=Path(__file__).resolve().parents[2]
    require(not(root/output).exists() and not(root/CANONICAL).exists(),'EXCLUSIVE_INERT_LIFECYCLE_CONSTRUCTION')
    env=dict(__name__='p09_product_lifecycle_bootstrap',__file__=LOADER['path'])
    exec(compile(direct(root,LOADER),LOADER['path'],'exec'),env)
    libraries,_=NS(**env).load(root,[ONCE,PROCESS_CONNECTION],{})
    ProductAudit=product_audit_type(direct(root,PROCESS_CONNECTION),libraries.native011_full_frame_worker_connection)
    audit=ProductAudit(root,direct(root,PROCESS_AUDIT),sys.addaudithook)
    def outer(base,once):
        selected=driver_type(base,once,process_audit=audit,authorize=authorize)
        return selected if wrap is None else wrap(selected,once)
    with patch.object(sys,'addaudithook',audit.register):
        return libraries.native011_product_once.construct_entry(outer=outer,output=output,checkpoint_route=coordinator_checkpoint,authorize=authorize)


def main():
    require(not sys.argv[1:],'CONSTRUCTION_ONLY_NO_GO_OR_NATIVE_ARGUMENTS');sys.dont_write_bytecode=True
    return construct()


if __name__=='__main__':raise SystemExit(main())
