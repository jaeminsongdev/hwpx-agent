"""Four original-guard preparation epochs; never a Native deadline reset."""
import os
import threading
import time
from types import FunctionType

SELF='tools/p09/native011_metadata_epochs.py'
STAGES=('construction','opening','metadata','closing')
MARKERS=('source_begin','connect_first_begin','consumer_begin','connect_second_begin')


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_METADATA_EPOCH_'+code)


def idle_context(context,*,closed=False):
    batch=context.data.planned.batch;parent=batch.parent_connection;built=context.prepared.linked
    phases=('EMPTY_BATCH_AUDITED_NOT_ACCEPTED',) if closed else ('NEW','READY')
    require(batch.identity()==batch.owner and batch.phase in phases and batch.active is None
        and not batch.cases and not batch.metadata_reader_active,'LIVE_READONLY_OWNER_NO_CASE_OR_METADATA')
    expected={n:dict(p) for n,p in batch.whole.items()}
    if batch.phase=='NEW':require(batch.initial is batch.final is batch.initial_reader is None,'NO_OPENING_BEFORE_REAL_BEGIN')
    else:
        reader=batch.initial_reader
        require(reader is not None and batch.initial==expected and reader.snapshots==expected
            and reader.read_passes==len(expected) and reader.bytes_read==sum(p['bytes'] for p in expected.values()),
            'ACTUAL_COMPLETE_WHOLE_OPENING')
        require(batch.final==expected if closed else batch.final is None,'ACTUAL_COMPLETE_WHOLE_CLOSING')
    require(parent is not None and parent.state.attempts==0 and parent.state.frames==[]
        and built.state.attempts==built.state.calls==0,'ZERO_NATIVE_FRAME_OR_WORKER_EXECUTION')
    require(all(set(vars(cls))==set(saved) and all(vars(cls)[n] is v for n,v in saved.items())
        for cls,saved in parent.classes),'UNCHANGED_ORIGINAL_FRAME_CLASSES')
    require(all(fn.__code__ is code and fn.__defaults__ is defaults and fn.__closure__ is closure
        and fn.__kwdefaults__==keywords for fn,code,defaults,closure,keywords in parent.methods),
        'UNCHANGED_ORIGINAL_FRAME_METHODS')
    shared=batch.shared
    require(shared.identity()==shared.owner and shared.frame is None and not shared.restored and shared.error is None
        and all(b is None or b.active is None and b.error is None for b in (shared.metadata,shared.frame)),
        'NO_ACTIVE_FAILED_OR_NATIVE_SHARED_DECODER')
    # This preparation deliberately has the unchanged strict-window function,
    # not the later product readiness/Job injector. Do not fabricate a context.
    fn=built.window.WINDOW_LINK.connect_engine
    require(type(fn) is FunctionType and fn.__closure__ is None
        and fn.__code__.co_filename.replace('\\','/').endswith('strict_product_window_connection_v1.py'),
        'ORIGINAL_UNINJECTED_STRICT_WINDOW_NOT_A_READINESS_QUALIFICATION')


def summarize(stage,guard,elapsed):
    samples=guard.samples
    return dict(stage=stage,elapsed_seconds=elapsed,cleanup_confirmed=guard.cleanup,
        original_resource_sample_count=len(samples),terminal_resource_samples=[dict(s) for s in samples[-8:]],
        system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
        available_RAM_min=min((s['available_ram_percent'] for s in samples),default=None),
        commit_used_max=max((s['commit_used_percent'] for s in samples),default=None),
        preparation_policy=guard.preparation_CPU.summary(),owned_limits=guard.preparation_limits,
        Native_deadline_or_policy_changed=False)


class Epochs:
    def __init__(self,factory,*,validator=idle_context,clock=time.monotonic,
                 identity=lambda:(os.getpid(),threading.get_ident())):
        require(callable(factory) and callable(validator),'ORIGINAL_FACTORY_AND_READONLY_VALIDATOR')
        self.factory=factory;self.validator=validator;self.clock=clock;self.identity=identity;self.owner=identity()
        self.guard=None;self.records=[];self.broken=False;self.closed=False;self.context=None;self.stage=None
    def check(self,*args,**kwargs):
        try:
            require(not self.broken and not self.closed and self.identity()==self.owner and self.guard is not None,
                'LIVE_SAME_OWNER_NO_RETRY')
            return self.guard.check(*args,**kwargs)
        except BaseException:self.broken=True;raise
    def bind(self,context):
        try:
            require(self.context is None and self.stage=='construction','ONE_ACTUAL_CONSTRUCTION')
            self.check();self.validator(context);self.context=context
        except BaseException:self.broken=True;raise
    def advance(self,stage):
        try:
            require(not self.broken and not self.closed and self.identity()==self.owner,'NO_FAILED_OR_FOREIGN_ROTATION')
            index=len(self.records)+(self.guard is not None)
            require(index<len(STAGES) and stage==STAGES[index],'FOUR_EXACT_PREPARATION_STAGES')
            if self.guard is not None:
                self.check(force=True);require(self.context is not None,'BOUND_ACTUAL_PARENT_BEFORE_ROTATION')
                self.validator(self.context);self._release()
            self.stage=stage;self.started=self.clock()
            role='dispatch_construction' if stage=='construction' else 'whole_metadata_preflight'
            self.guard=self.factory(role);self.guard.acquire()
        except BaseException:self.broken=True;raise
    def _release(self):
        guard=self.guard
        if guard is None:return
        self.guard=None
        try:guard.close()
        finally:self.records.append(summarize(self.stage,guard,self.clock()-self.started))
        require(guard.cleanup is True,'ORIGINAL_LEASE_RELEASE_BEFORE_SUCCESSOR')
    def close(self):
        self.closed=True
        self._release()
