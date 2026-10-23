"""Original connected Native Frame boundaries with an intentional no-product abort.

One600 clock includes metadata and both complete current-input reads. No GO,
worker, fake Job commit, case completion or successful batch close is supplied.
The actual executable driver must provide the original metadata/API/readers.
"""
import os
import threading
import time
from types import FunctionType,SimpleNamespace as NS

SELF='tools/p09/native011_readonly_frame_probe.py'
TEST='tools/p09/tests/test_native011_readonly_frame_probe.py'


def require(ok,label):
    if not ok:raise ValueError('READONLY_NATIVE_FRAME_'+label)


def parent_readonly(parent,delegate):
    """Run the original ownership wrapper with only its engine delegate denied.

    No counter or saved class is edited. The original wrapper records its own
    one attempt and runs its original private patch/restoration and cleanup.
    Its entire engine body is replaced by this explicit no-product diagnostic
    delegate, not a partial product execution or accepted Native result.
    """
    run=parent.parent.run_owned
    require(type(run) is FunctionType and run.__closure__ is not None,'ORIGINAL_PARENT_FUNCTION')
    cells=dict(zip(run.__code__.co_freevars,run.__closure__))
    require({'original','state','native','env'}<=set(cells)
        and cells['state'].cell_contents is parent.state and parent.state.attempts==0
        and cells['original'].cell_contents is parent.state.original
        and cells['native'].cell_contents.frames.Frame is parent.frame_type
        and cells['env'].cell_contents is run.__globals__,'EXACT_ORIGINAL_PARENT_CLOSURE_OWNER')
    def cell(value):return (lambda:value).__closure__[0]
    selected=FunctionType(run.__code__,run.__globals__,argdefs=run.__defaults__,
        closure=tuple(cell(delegate) if name=='original' else old for name,old in cells.items()))
    require(selected.__code__ is run.__code__ and selected.__globals__ is run.__globals__
        and all(new is old for name,new,old in zip(run.__code__.co_freevars,selected.__closure__,run.__closure__)
            if name!='original'),'ONLY_EXPLICIT_NO_PRODUCT_ENGINE_DELEGATE')
    return selected(1)


def precise_native(native_type,pacer_type,checkpoint):
    """Choose the clock before any lock wrapper captures its pacer identity.

    Both original classes and all algorithms remain. No used counter, previous
    timestamp, credit, resource sample or lock/Native deadline is reset.
    """
    native=native_type(checkpoint);old=native.pacer;saved=dict(vars(old))
    require(type(native) is native_type and type(old) is pacer_type and old.checkpoint is checkpoint
        and old.clock is time.monotonic and old.sleeper is time.sleep and old.rate==32
        and old.opens==0 and old.previous is None and old.sleep_seconds==0,'ONLY_UNUSED_ORIGINAL_NATIVE_PACER')
    selected=pacer_type(checkpoint,rate=old.rate,clock=time.perf_counter,sleeper=old.sleeper)
    require(type(selected) is type(old) and set(vars(selected))==set(saved)
        and all(vars(selected)[key] is value or vars(selected)[key]==value
            for key,value in saved.items() if key!='clock') and vars(old)==saved,
        'ONLY_FRESH_NATIVE_PACING_CLOCK_DIFFERS')
    native.pacer=selected
    return native,dict(original_Native_and_OpenPacer_classes_retained=True,unused_owner_only=True,
        before_clock='monotonic',after_clock='perf_counter',
        before_resolution=time.get_clock_info('monotonic').resolution,
        after_resolution=time.get_clock_info('perf_counter').resolution,
        rate_selected_by_original_acquisition_wrapper=True,
        saved_phase_clock_captured_after_selection=True,
        previous_counter_credit_checkpoint_or_sleeper_reset=False,
        Native600_lock600_decoder5_READY15_product10_unchanged=True)


class NativePhase:
    def __init__(self,*,clock=time.monotonic,identity=lambda:(os.getpid(),threading.get_ident())):
        self.clock=clock;self.identity=identity;self.owner=identity();self.state='NEW';self.failed=False
        self.started=None;self.checkpoint=None;self.frame=None;self.held=None;self.loan=None
        self.cleanup_errors=[];self.proof={}
    def check(self,*args,**kwargs):
        self.checkpoint(*args,**kwargs)
        require(self.identity()==self.owner and not self.failed and self.state!='CLOSED',
            'SAME_ACTIVE_OWNER_NOT_FAILED')
        require(self.started is not None and 0<=self.clock()-self.started<600,
            'ORIGINAL600_INCLUDES_METADATA_AND_BOTH_READS')
    def run(self,context,root,metadata_once,reader_factory,resources,checkpoint,coverage,inheritance,required_sources):
        require(self.state=='NEW' and not self.failed and self.identity()==self.owner,'ONE_READONLY_PHASE_NO_RETRY')
        self.checkpoint=checkpoint;self.started=self.clock();self.state='METADATA';primary=None;result=None
        owner=context.data.planned.batch;parent=owner.parent_connection;initial=owner.initial_reader
        try:
            self.check()
            require(type(required_sources) is dict and len(required_sources)==201,'EXACT_REQUIRED_WORKER201')
            require(owner.phase=='READY' and owner.active is None and not owner.cases and not owner.metadata_reader_active
                and owner.initial=={n:dict(p) for n,p in owner.whole.items()}
                and initial.snapshots==owner.initial and initial.read_passes==len(owner.whole)
                and initial.bytes_read==sum(pin['bytes'] for pin in owner.whole.values()),
                'ACTUAL_COMPLETE_NEW_WHOLE_OPENING_NOT_PRIOR_PASS')
            require(parent.lifecycle_connected and parent.state.frames==[] and parent.state.attempts==0
                and context.prepared.linked.state.attempts==context.prepared.linked.state.calls==0
                and owner.shared.metadata is owner.shared.frame is None and not owner.shared.restored,
                'ORIGINAL_CONNECTED_LIFECYCLE_AND_UNUSED_SHARED_OWNER')
            metadata=metadata_once(self.check);self.check()
            require(owner.phase=='READY' and not owner.metadata_reader_active and owner.shared.metadata is not None
                and owner.shared.frame is None and not owner.shared.restored,'REAL_METADATA_BEFORE_FRAME')
            api=metadata.api
            self.proof['metadata']=metadata.proof
            def diagnostic(run):
                require(run==1 and parent.state.attempts==1 and not parent.state.frames,
                    'ORIGINAL_PARENT_OWNS_ONE_DIAGNOSTIC_ATTEMPT')
                try:self._read_frame(owner,parent,metadata,root,reader_factory,resources,coverage,inheritance,required_sources)
                finally:self._cleanup()
            parent_readonly(parent,diagnostic)
            self.proof.update(original_parent_wrapper_called=True,original_parent_wrapper_attempts=parent.state.attempts,
                original_engine_body_called=False,explicit_no_product_delegate_only=True)
        except BaseException as error:self.failed=True;primary=error
        finally:
            self._cleanup()
            self.state='CLOSED'
            if self.cleanup_errors:self.failed=True
        if primary is not None:raise primary
        require(not self.failed and not self.cleanup_errors,'ALL_ORIGINAL_HANDLE_CLEANUP_CONFIRMED')
        require(self.frame.state=='CLOSED' and not self.frame.registered and self.frame.held.closed
            and self.frame.raw_policy.restored and not self.frame.raw_policy.installed
            and owner.phase=='BROKEN' and not owner.cases and parent.state.attempts==1
            and context.prepared.linked.state.attempts==context.prepared.linked.state.calls==0,
            'INTENTIONAL_READONLY_ABORT_NOT_NATIVE_CASE_OR_BATCH_PASS')
        result=dict(state='COMPLETED_READONLY_FRAME_BOUNDARIES_NOT_PRODUCT_OR_BATCH_ACCEPTANCE',
            proof=self.proof,frame=self.frame.summary(),batch_phase_after_readonly_abort=owner.phase,
            actual_accepted_count_delta=0,actual_owned_Native_acceptance_qualified=False)
        return result

    def _cleanup(self):
        if self.loan is not None and self.loan.state!='RESTORED':
            try:
                if not self.loan.restore():self.cleanup_errors.append('SOURCE_FLAG_RESTORE_FAILED')
            except (ValueError,OSError):self.cleanup_errors.append('SOURCE_FLAG_RESTORE_FAILED')
        if self.frame is not None and self.frame.state!='CLOSED':
            try:
                if not self.frame.close():self.cleanup_errors.append('FRAME_CLOSE_UNCONFIRMED')
            except (ValueError,OSError):self.cleanup_errors.append('FRAME_CLOSE_UNCONFIRMED')
        elif self.frame is None and self.held is not None and not self.held.closed:
            try:
                if not self.held.close():self.cleanup_errors.append('UNACQUIRED_LOCK_CLEANUP_FAILED')
            except (ValueError,OSError):self.cleanup_errors.append('UNACQUIRED_LOCK_CLEANUP_FAILED')

    def _read_frame(self,owner,parent,metadata,root,reader_factory,resources,coverage,inheritance,required_sources):
        api=metadata.api;phase=NS(phase='native_acquisition')
        early=api.EarlySourceCheckpoint(self.check,resources)
        native,clock_proof=precise_native(metadata.native_type,metadata.pacer_type,early)
        self.held=api.InputLocks(root,early,resources,phase,api=native)
        require(self.held.phase_pacer is native.pacer and self.held.phase_clock is time.perf_counter
            and self.held.phase_pacer.opens==0 and not self.held.phase_used,
            'ORIGINAL_ACQUISITION_CAPTURES_SELECTED_UNUSED_CLOCK')
        self.proof['native_open_pacer']=clock_proof
        self.frame=parent.frame_type(parent.registry_type(),metadata.required,early,held=self.held)
        frame=self.frame;require(parent.state.frames==[frame] and frame.state=='NEW'
            and {n:dict(p) for n,p in frame.inputs.items()}=={n:dict(p) for n,p in owner.current.items()}
            and frame.held.maximum_seconds==600,'EXACT_WHOLE_CURRENT_FRAME_NOT_SOURCE_SUBSET')
        self.state='ACQUIRING';frame.held.mark('before_acquire');frame.acquire();frame.held.mark('after_acquire')
        require(owner.phase=='CASE_ACTIVE' and owner.active[1] is frame,'ORIGINAL_CASE_LIFECYCLE_ACTIVATED')
        guards=[]
        def factory(guard):return reader_factory(guard,api)
        self.state='FIRST_READ';phase.phase='first_full_native_hash'
        api.read_with_held_path_guards(frame,factory,self.check,guards)
        self.proof['before_coverage']=coverage.verify(frame,required_sources,frame_type=parent.frame_type,boundary='before')
        self.state='SOURCE_FLAGS'
        self.loan=inheritance.SourceInheritance(frame,required_sources,coverage,frame_type=parent.frame_type)
        handles=self.loan.arm();require(len(handles)==len(required_sources),'ALL_DECLARED_SOURCE_FLAGS_ARMED')
        require(self.loan.restore(),'ORIGINAL_SOURCE_FLAGS_RESTORED_BEFORE_IDENTITY_OR_READ')
        self.proof['loan']=self.loan.summary()
        self.proof['restored_coverage']=coverage.verify(frame,required_sources,frame_type=parent.frame_type,boundary='before')
        self.state='SECOND_READ';phase.phase='final_fresh_hash'
        api.read_with_held_path_guards(frame,factory,self.check,guards)
        self.proof['after_coverage']=coverage.verify(frame,required_sources,frame_type=parent.frame_type,boundary='after')
        self.check();require(len(frame.readers)==2 and frame.readers[0] is not frame.readers[1]
            and len(frame.boundaries)==2,'BOTH_REAL_FRESH_BOUNDARIES_NOT_REUSED_READER')
        self.proof.update(shared_decoder=owner.shared.evidence(),path_guards=guards,
            readonly600_elapsed_seconds=self.clock()-self.started,current_inputs=len(frame.inputs),
            worker_source_count=len(required_sources),product_or_worker_processes_created=0,
            GO_writes=0,original_Job_commit_supplied=False,case_finished_called=False)
