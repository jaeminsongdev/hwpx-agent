"""Worker202 READY/real EOF between the original whole Native byte reads.

Diagnostic only: preserve the original readonly abort, Native600 and source
ownership. Its child uses a preparation-only nested Job, not the product Job.
No product GO, original Job commit, retry, acceptance or canonical run011 file.
"""
import ast
import copy
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import subprocess
import sys
import time
from types import CodeType, FunctionType, MethodType, SimpleNamespace as NS

SELF='tools/p09/native011_full_frame_worker_ready.py'
TEST='tools/p09/tests/test_native011_full_frame_worker_ready.py'
SOURCE=dict(path='tools/p09/native011_readonly_frame_probe.py',bytes=11883,
    sha256='cab0f91b6e947b73362e5bf3c20e35f20c3e239ba1e5ec58f4d7afd93dcc92c6')
ENTRY='tools/p09/native011_product_worker_entry.py'
TASK='case165-current-r011-tests'
CONSTRUCTION='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-ready-construct001.v1.json'
DIAGNOSTIC='implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-ready-probe001.v1.json'


def require(ok,code):
    if not ok:raise ValueError('FULL_FRAME_WORKER_READY_'+code)


def projected_run(module,raw,original_parent_run=None):
    """One worker count and label, whole inverse; no boundary body edits."""
    require(type(raw) is bytes and len(raw)==SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],'EXACT_ORIGINAL_READONLY_SOURCE')
    base=module.NativePhase;original=base.run
    require(type(base) is type and type(original) is FunctionType
        and original.__code__.co_filename.replace('\\','/').endswith(SOURCE['path']),
        'ORIGINAL_READONLY_CLASS_NOT_REWRITTEN_BODY')
    def nested(code,name):
        return [value for value in code.co_consts if type(value) is CodeType and value.co_name==name]
    parsed=ast.parse(raw)
    declarations=[node for node in parsed.body if isinstance(node,ast.ClassDef) and node.name=='NativePhase']
    require(len(declarations)==1,'ONE_EXACT_ORIGINAL_CLASS_DECLARATION')
    method_names={node.name for node in declarations[0].body if isinstance(node,ast.FunctionDef)}
    tree=compile(raw,original.__code__.co_filename,'exec')
    classes=nested(tree,'NativePhase')
    require(len(classes)==1,'ONE_COMPLETE_ORIGINAL_PHASE_CLASS')
    expected={value.co_name:value for value in classes[0].co_consts
        if type(value) is CodeType and value.co_name in method_names}
    if not all(type(value) is FunctionType and value.__code__==expected.get(name)
            for name,value in vars(base).items() if type(value) is FunctionType):
        nodes=[node for node in parsed.body if isinstance(node,(ast.Assign,ast.FunctionDef,ast.ClassDef))]
        classes=nested(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
            original.__code__.co_filename,'exec'),'NativePhase')
        require(len(classes)==1,'ONE_IMPORT_STRIPPED_ORIGINAL_PHASE_CLASS')
        expected={value.co_name:value for value in classes[0].co_consts
            if type(value) is CodeType and value.co_name in method_names}
    require({name for name,value in vars(base).items() if type(value) is FunctionType}==set(expected)==method_names
        and all(value.__code__==expected[name] for name,value in vars(base).items() if type(value) is FunctionType),
        'EVERY_ORIGINAL_PHASE_METHOD_CODE_UNCHANGED')
    constants=list(original.__code__.co_consts);edits=[]
    for old,new in ((201,202),('EXACT_REQUIRED_WORKER201','EXACT_REQUIRED_WORKER202')):
        positions=[i for i,value in enumerate(constants) if type(value) is type(old) and value==old]
        require(len(positions)==1,'ONE_EXPECTED_WORKER_COUNT_AND_LABEL_SLOT')
        index=positions[0];edits.append((index,old));constants[index]=new
    code=original.__code__.replace(co_consts=tuple(constants));undo=list(code.co_consts)
    for index,value in edits:undo[index]=value
    require(code.replace(co_consts=tuple(undo))==original.__code__,'ENTIRE_READONLY_RUN_CODE_INVERSE')
    environment=original.__globals__
    if original_parent_run is not None:
        require(type(original_parent_run) is FunctionType,'EXPLICIT_ORIGINAL_PARENT_FOR_NO_PRODUCT_DELEGATE')
        old=module.parent_readonly
        def parent_readonly(parent,delegate):
            # The real installed parent remains denied. The original diagnostic
            # wrapper receives only its saved pre-install function and the same
            # state/Frame type; it never calls the product engine body.
            require(parent.state.original is not original_parent_run,'PARENT_WRAPPER_NOT_ENGINE_BODY')
            selected=NS(**{**vars(parent),'parent':NS(**{**vars(parent.parent),'run_owned':original_parent_run})})
            return old(selected,delegate)
        environment=dict(environment,parent_readonly=parent_readonly)
    selected=FunctionType(code,environment,argdefs=original.__defaults__,closure=original.__closure__)
    selected.__kwdefaults__=original.__kwdefaults__
    require(selected.__defaults__ is original.__defaults__ and selected.__closure__ is original.__closure__,
        'ORIGINAL_PHASE_DEFAULTS_AND_CLOSURE')
    return selected,dict(entire_original_run_code_inverse=True,original_phase_method_count=len(expected),
        worker_count=202,only_expected_worker_count_and_label_changed=True,
        original_parent_readonly_dependency_selected=original_parent_run is not None,
        original_Native600_metadata_two_boundaries_and_abort_retained=True,
        product_or_original_Job_commit_qualified=False,GO_authorized=False)


def projected_read(module,raw):
    """Correct only the diagnostic worker count; every read/check stays."""
    tree=ast.parse(raw);classes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='NativePhase']
    require(len(classes)==1,'ONE_PHASE_CLASS_FOR_DIAGNOSTIC_COUNT')
    before=ast.dump(classes[0],include_attributes=False);revised=copy.deepcopy(classes[0])
    methods=[node for node in revised.body if isinstance(node,ast.FunctionDef) and node.name=='_read_frame']
    require(len(methods)==1,'ONE_WHOLE_READ_FRAME_METHOD')
    counts=[keyword for node in ast.walk(methods[0]) if isinstance(node,ast.Call)
        for keyword in node.keywords if keyword.arg=='product_or_worker_processes_created']
    require(len(counts)==1 and isinstance(counts[0].value,ast.Constant) and type(counts[0].value.value) is int
        and counts[0].value.value==0,'ONE_LITERAL_ORIGINAL_DIAGNOSTIC_ZERO_WORKERS')
    counts[0].value.value=1
    code=compile(ast.fix_missing_locations(ast.Module(body=[revised],type_ignores=[])),
        module.NativePhase._read_frame.__code__.co_filename,'exec')
    classes_code=[value for value in code.co_consts if type(value) is CodeType and value.co_name=='NativePhase']
    require(len(classes_code)==1,'ONE_PROJECTED_READ_FRAME_CLASS_CODE')
    selected=[value for value in classes_code[0].co_consts if type(value) is CodeType and value.co_name=='_read_frame']
    require(len(classes_code)==len(selected)==1,'WHOLE_PROJECTED_READ_METHOD_NOT_PARTIAL_BODY')
    counts[0].value.value=0
    require(ast.dump(revised,include_attributes=False)==before,'ENTIRE_READ_FRAME_CLASS_AST_INVERSE')
    original=module.NativePhase._read_frame
    restored=compile(ast.fix_missing_locations(ast.Module(body=[revised],type_ignores=[])),original.__code__.co_filename,'exec')
    restored_class=[value for value in restored.co_consts if type(value) is CodeType and value.co_name=='NativePhase']
    restored_read=[value for value in restored_class[0].co_consts if type(value) is CodeType and value.co_name=='_read_frame']
    require(len(restored_class)==len(restored_read)==1 and restored_read[0]==original.__code__,
        'ENTIRE_ORIGINAL_READ_METHOD_CODE_AFTER_INVERSE')
    result=FunctionType(selected[0],original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    result.__kwdefaults__=original.__kwdefaults__
    return result


def prepare_phase(module,raw,callback,*,original_parent_run=None):
    """Compile one per-run helper before Native, never reuse input IO credit."""
    require(callable(callback),'EXPLICIT_NO_GO_WORKER_CALLBACK')
    run,projection=projected_run(module,raw,original_parent_run)
    read=projected_read(module,raw);base=module.NativePhase;members=dict(vars(base));mro=base.__mro__
    functions={name:(value,value.__code__,value.__defaults__,value.__kwdefaults__,value.__closure__)
        for name,value in members.items() if type(value) is FunctionType}
    environments={id(value.__globals__):(value.__globals__,dict(value.__globals__))
        for value,*_ in functions.values()}
    used=False
    def create(*,phase=None):
        nonlocal used
        require(not used,'ONE_PREPARED_PHASE_CREATION_NO_RETRY');used=True
        require(module.NativePhase is base and base.__mro__ is mro and set(vars(base))==set(members)
            and all(vars(base)[name] is value for name,value in members.items()),'PREPARED_ORIGINAL_CLASS_UNCHANGED')
        require(all(value.__code__ is code and value.__defaults__ is defaults
            and value.__kwdefaults__ is keywords and value.__closure__ is closure
            for value,code,defaults,keywords,closure in functions.values()),'PREPARED_ORIGINAL_FUNCTIONS_UNCHANGED')
        require(all(set(environment)==set(saved) and all(environment[name] is value for name,value in saved.items())
            for environment,saved in environments.values()),'PREPARED_ORIGINAL_GLOBAL_BINDINGS_UNCHANGED')
        selected=FullFramePhase.__new__(FullFramePhase)
        selected._initialize(module,callback,run,copy.deepcopy(projection),read,phase=phase)
        return selected
    return NS(create=create,projection=copy.deepcopy(projection),preparation=dict(
        original_whole_run_and_read_source_code_attested_before_Native=True,
        original_class_function_and_global_bindings_rechecked_on_creation=True,
        compiled_helpers_per_driver_construction=1,Native_phase_or_Frame_allocated_during_preparation=False,
        source_byte_hash_JSON_AST_or_closing_credit_reused=False,one_phase_creation_no_retry=True,
        original_Native600_READY15_decoder5_product10_and_guards_changed=False))


class FullFramePhase:
    def __init__(self,module,raw,callback,*,original_parent_run=None,phase=None):
        require(callable(callback),'EXPLICIT_NO_GO_WORKER_CALLBACK')
        run,projection=projected_run(module,raw,original_parent_run)
        self._initialize(module,callback,run,projection,projected_read(module,raw),phase=phase)
    def _initialize(self,module,callback,run,projection,read,*,phase=None):
        self.run_original=run;self.projection=projection
        self.phase=module.NativePhase() if phase is None else phase
        require(type(self.phase) is module.NativePhase and self.phase.state=='NEW','UNUSED_ORIGINAL_PHASE_INSTANCE')
        self.phase._read_frame=MethodType(read,self.phase)
        self.projection['original_read_Frame_class_AST_inverse']=True
        self.projection['diagnostic_worker_process_count']=1
        self.callback=callback;self.callback_attempts=0;self.callback_completed=False;self.callback_result=None
        self.proof=self.phase.proof
    def __getattr__(self,name):return getattr(self.phase,name)
    def run(self,context,root,metadata_once,reader_factory,resources,checkpoint,coverage,inheritance,required):
        require(self.callback_attempts==0 and not self.callback_completed and type(required) is dict and len(required)==202,
            'ONE_SOURCE202_DIAGNOSTIC_NOT_RETRY')
        phase=self.phase;outer=self
        def source_loan(frame,sources,actual_coverage,*,frame_type):
            require(frame is phase.frame and phase.state=='SOURCE_FLAGS' and sources is required
                and actual_coverage is coverage,'SAME_FIRST_FULL_BOUNDARY_AND_ORIGINAL_SOURCE_LOAN')
            original=inheritance.SourceInheritance(frame,sources,actual_coverage,frame_type=frame_type)
            class Loan:
                def __getattr__(self,name):return getattr(original,name)
                def arm(self):return original.arm()
                def summary(self):return original.summary()
                def restore(self):
                    restored=original.restore()
                    if restored:
                        require(outer.callback_attempts==0,'NO_DUPLICATE_WORKER_AFTER_RESTORE')
                        phase.check();outer.callback_attempts+=1
                        outer.callback_result=outer.callback(phase,frame)
                        phase.check();outer.callback_completed=True
                    return restored
            return Loan()
        result=self.run_original(phase,context,root,metadata_once,reader_factory,resources,checkpoint,
            coverage,NS(**{**vars(inheritance),'SourceInheritance':source_loan}),required)
        require(self.callback_attempts==1 and self.callback_completed,'ACTUAL_CALLBACK_COMPLETED_BETWEEN_READS')
        result['proof']['whole_Frame_worker_ready']=dict(projection=self.projection,
            callback_attempts=self.callback_attempts,callback_completed=True,worker=self.callback_result,
            original_product_Job_or_commit_qualified=False,product_or_GO_authorized=False)
        return result


class WorkerProbe:
    """One bounded no-GO child, borrowing the caller's live whole Frame."""
    def __init__(self,root,windows,required,frame_type,api,capture_type,*,factory=subprocess.Popen,clock=time.monotonic):
        require(type(required) is dict and len(required)==202 and ENTRY in required,'EXPLICIT_WORKER202_SOURCE_DECLARATION')
        require(callable(factory) and callable(clock) and type(capture_type) is type,'EXPLICIT_BOUNDED_PROCESS_DEPENDENCIES')
        self.root=root;self.windows=windows;self.required={name:dict(pin) for name,pin in required.items()}
        self.frame_type=frame_type;self.api=api;self.capture_type=capture_type;self.factory=factory;self.clock=clock
        self.attempts=0;self.proof=dict(state='NOT_RUN_WHOLE_FRAME_WORKER_READY',GO_authorized=False,
            original_product_Job_or_commit_qualified=False,accepted_count_delta=0)
    def __call__(self,phase,frame):
        require(self.attempts==0 and frame is phase.frame and type(frame) is self.frame_type,
            'ONE_ACTUAL_PHASE_FRAME_AND_NO_CHILD_RETRY')
        self.attempts+=1;api=self.api;windows=self.windows
        job=process=capture=event=handoff=None;assigned=False;primary=None;started=self.clock()
        row=self.proof;row['state']='FAILED_WHOLE_FRAME_WORKER_READY_NOT_PRODUCT'
        counts=dict(frame.held.stream_read_counts);identities=copy.deepcopy(frame.held.files)
        observations={name:dict(calls=0,failed_calls=0,wall_seconds=0.,CPU_seconds=0.,maximum_wall_seconds=0.)
            for name in ('original_gate_checkpoint','original_owned_check')}
        row['gate_cost_observation']=dict(original_gate_seconds=15,observations=observations,
            observation_used_for_admission_or_budget=False,child_progress_or_timeout_cause_qualified=False)
        def observed(name,call,*args):
            # Measure the unchanged dependency, including its failing call. Do
            # not add a checkpoint, retry, child wait or alternative clock to Gate.
            value=observations[name];begin=time.perf_counter();cpu=time.process_time();failed=True
            try:
                result=call(*args);failed=False;return result
            finally:
                elapsed=time.perf_counter()-begin
                value['calls']+=1;value['failed_calls']+=int(failed)
                value['wall_seconds']+=elapsed;value['CPU_seconds']+=time.process_time()-cpu
                value['maximum_wall_seconds']=max(value['maximum_wall_seconds'],elapsed)
        try:
            phase.check()
            row['before_coverage']=api.coverage.verify(frame,self.required,frame_type=self.frame_type,boundary='before')
            normalized=api.nested.InnerPreparationJob(windows);job=normalized.create()
            row['preparation_job_limits']=normalized.verify(job)
            frame.held.api.pacer.reserve();event=api.protocol.WindowsEvent();event.inheritable(True)
            handoff=api.transfer.Handoff(self.root,self.required[ENTRY],frame,self.required,api.coverage,
                api.inheritance,api.bridge,api.protocol,phase.check,frame_type=self.frame_type)
            startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[event.handle]}
            command=[sys.executable,'-B',str(self.root/ENTRY),'--ready-handle',str(event.handle),'--task',TASK]
            try:
                process=handoff.spawn(self.factory,command,cwd=self.root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW,
                    startupinfo=startup,close_fds=True)
            finally:event.inheritable(False)
            require(windows.k.AssignProcessToJobObject(job,int(process._handle)),'SAME_PREPARATION_JOB_ASSIGNMENT');assigned=True
            def owned(actual):
                normalized.parent_check();member=w.BOOL()
                return actual is process and bool(windows.k.IsProcessInJob(int(actual._handle),job,ctypes.byref(member))) and bool(member.value)
            output_only=NS(stdin=NS(close=lambda:None),stdout=process.stdout,stderr=process.stderr,wait=process.wait)
            capture=self.capture_type(output_only,output_limit=32768,parse_markers=False)
            sink=api.original.NoGoReadySink(api.protocol.GO)
            gate=api.protocol.Gate(sink,event,process,
                lambda actual:observed('original_owned_check',handoff.verify_owned,actual,owned),
                lambda:observed('original_gate_checkpoint',handoff.gate_checkpoint))
            handoff.bind_gate(gate);gate_error=None
            try:gate.write(api.protocol.GO)
            except ValueError as error:
                if error.args!=('READINESS_PROBE_PRODUCT_GO_DENIED',):gate_error=error
            else:gate_error=ValueError('FULL_FRAME_WORKER_READY_ORIGINAL_GO_MUST_BE_DENIED')
            row['readiness']=gate.diagnostics()
            if gate_error is not None:raise gate_error
            process.stdin.close();deadline=self.clock()+30
            while True:
                phase.check();require(self.clock()<deadline,'ORIGINAL_CHILD_TERMINAL30_AFTER_GATE15')
                try:stdout,stderr=capture.communicate(timeout=.1);break
                except subprocess.TimeoutExpired:capture.progress()
            child=json.loads(stdout.splitlines()[-1]);row['child']=child;row['child_exit_code']=process.returncode
            require(gate.ready and gate.stopped and not gate.written and sink.attempts==1
                and handoff.started and not handoff.failed and process.returncode==1,'REAL_READY15_THEN_ORIGINAL_EOF_NOT_GO')
            api.probe.validate_child(child,self.required,api.worker.pin_digest)
            require(json.loads(stderr.strip())['terminal']=='WORKER_NOT_AUTHORIZED','ORIGINAL_REAL_EOF_TERMINAL')
            require(frame.held.stream_read_counts==counts and frame.held.files==identities,
                'CHILD_READS_NOT_PARENT_NATIVE_BYTE_CREDIT')
            row['restored_coverage']=api.coverage.verify(frame,self.required,frame_type=self.frame_type,boundary='before')
            row['preparation_job_limits_after_ready']=normalized.verify(job)
        except BaseException as error:primary=error
        finally:
            # Reuse the original owned cleanup, but the enclosing Native phase
            # owns its Frame and guard. This adapter never closes either one.
            lifecycle=NS(windows=windows,close=lambda:None,cleanup=True)
            try:clean=api.probe.cleanup(lifecycle,job,process,capture,assigned,event,handoff,None,row)
            except BaseException as error:
                clean=False
                if primary is None:primary=error
            row.update(cleanup_confirmed=clean,child_launch_attempts=self.attempts,elapsed_seconds=self.clock()-started,
                original_Native_Frame_and_guard_closed_by_child_probe=False,
                preparation_only_nested_Job_not_product_Job=True,product_GO_writes=0)
        if primary is not None:raise primary
        require(clean,'ALL_CHILD_OWNED_HANDLE_CLEANUP_CONFIRMED')
        phase.check()
        row['state']='PASS_WHOLE_FRAME_WORKER202_SOURCE_READY_REAL_EOF_NOT_NATIVE_ACCEPTANCE'
        return row
