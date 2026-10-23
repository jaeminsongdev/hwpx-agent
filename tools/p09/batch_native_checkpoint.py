"""One-way preparation-to-original-Native checkpoint dependency.

The original engine creates its own reader/pressure guard and sampler. Bind
that actual reader, follow its exact original pressure restoration, and never
reuse a closed preparation guard or install preparation policy in Native.
No timer, sample, input verification, process, Job or acceptance is replaced.
"""
import os
import threading

SELF='tools/p09/batch_native_checkpoint.py'
TEST='tools/p09/tests/test_batch_native_checkpoint.py'


def require(ok,code):
    if not ok:raise ValueError('BATCH_NATIVE_CHECKPOINT_'+code)


class Handoff:
    def __init__(self,preparation,idle,*,identity=lambda:(os.getpid(),threading.get_ident())):
        require(callable(idle) and callable(identity),'ORIGINAL_IDLE_CHECK_AND_OWNER')
        self.preparation=preparation;self.idle=idle;self.identity=identity;self.owner=identity()
        self.phase='PREPARATION';self.broken=False;self.checking=False
        self.result=None;self.reader=None;self.pressure=None;self.original=None;self.bindings=0

    def _owner(self):
        require(not self.broken and self.identity()==self.owner,'SAME_LIVE_OWNER_NOT_FAILED')

    def check(self,*args,**kwargs):
        try:
            self._owner();require(not self.checking,'NO_RECURSIVE_CHECKPOINT_CYCLE')
            self.checking=True
            if self.phase=='PREPARATION':return self.preparation.check(*args,**kwargs)
            require(self.phase=='NATIVE' and not args and not kwargs,'ONLY_ORIGINAL_NATIVE_CHECKPOINT')
            actual=self.reader.checkpoint
            if actual is self.pressure:
                require(self.pressure.active is True and self.pressure.latched is False,
                    'EXACT_ACTIVE_ORIGINAL_METADATA_PRESSURE')
            else:
                require(actual is self.original and self.pressure.active is False
                    and self.pressure.restored is True and self.pressure.latched is False,
                    'EXACT_ORIGINAL_PRESSURE_RESTORATION')
            return actual()
        except BaseException:
            self.broken=True;raise
        finally:self.checking=False

    def bind(self,result):
        try:
            self._owner();require(self.phase=='PREPARATION' and self.result is None,'ONE_CONSTRUCTED_PARENT')
            self.preparation.bind(result);self.result=result
        except BaseException:self.broken=True;raise

    def arm(self):
        try:
            self._owner();require(self.phase=='PREPARATION' and self.result is not None,'ONE_FORWARD_HANDOFF')
            prep=self.preparation
            require(prep.closed is True and prep.broken is False and prep.guard is None
                and [r['stage'] for r in prep.records]==['construction','opening_and_metadata']
                and all(r['cleanup_confirmed'] is True for r in prep.records),'CLOSED_PREPARATION_OWNERS')
            # This original inspector requires the real complete whole opening,
            # untouched original Frame classes and zero execution counters.
            self.idle(self.result)
            batch=self.result.assembled.batch
            require(batch.phase=='READY' and batch.shared.metadata is batch.shared.frame is None,
                'WHOLE_OPENING_WITHOUT_PRIOR_METADATA_OR_FRAME')
            self.phase='WAIT_ORIGINAL_NATIVE'
        except BaseException:self.broken=True;raise

    def admit_metadata(self,reader,context):
        try:
            self._owner();require(self.phase=='WAIT_ORIGINAL_NATIVE' and self.bindings==0,
                'ONE_ACTUAL_ORIGINAL_METADATA_BINDING')
            require(context.parent is self.result.assembled.batch.parent_connection.state
                and context.active is True and context.attempts==context.parent.attempts==1
                and context.jobs==0 and context.parent.frames==[],'ORIGINAL_EXECUTION_BEFORE_FRAME_AND_JOB')
            connection=self.result.assembled.batch.metadata_connection
            require(len(connection.readers)==len(connection.budgets)==1 and connection.readers[0] is reader,
                'ACTUAL_ORIGINAL_ENGINE_METADATA_READER')
            pressure=reader.checkpoint
            require(pressure.reader is reader and pressure.active is True and pressure.latched is False
                and pressure.restored is False and callable(pressure.original)
                and pressure.original is pressure.hard and pressure.owner.checkpoint_io is pressure.hard,
                'UNCHANGED_ORIGINAL_READER_AND_OWNER_CHECKPOINT')
            self.reader=reader;self.pressure=pressure;self.original=pressure.original
            self.bindings+=1;self.phase='NATIVE'
            self.check()
        except BaseException:self.broken=True;raise

    def finish_native(self,context):
        # Cleanup is never gated on current CPU/RAM or a prior resource error.
        # This does not prove Job/Frame cleanup; inspect the original receipt.
        require(self.identity()==self.owner and self.phase in ('WAIT_ORIGINAL_NATIVE','NATIVE')
            and context.active is False and context.attempts==context.restorations==1,
            'ORIGINAL_OWNER_SCOPE_TERMINAL')
        self.phase='NATIVE_TERMINAL'

    def evidence(self):
        return dict(phase=self.phase,failed=self.broken,actual_metadata_reader_bindings=self.bindings,
            original_pressure_restored=None if self.pressure is None else self.pressure.restored,
            original_pressure_latched=None if self.pressure is None else self.pressure.latched,
            preparation_guard_reused_in_Native=False,preparation_CPU_policy_installed_in_Native=False,
            added_sampler_or_timer_or_Job=False,execution_counters_reset=False,
            Native_or_product_or_Frame_cleanup_qualified=False)
