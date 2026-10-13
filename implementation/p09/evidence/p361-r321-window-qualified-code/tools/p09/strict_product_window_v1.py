"""Stricter actual GO-to-complete-capture window; no source scope reduction.

Single owned process, original stdin/pipe/capture APIs and cleanup. No extra
sampler/thread or process query. Blocking OS APIs are not hard-preempted; the
same owned Job cleanup must run on every stop. No implicit acceptance authority.
"""
import math
import time
from types import SimpleNamespace as NS

SELF="tools/p09/strict_product_window_v1.py"
TEST="tools/p09/tests/test_strict_product_window_v1.py"
SECONDS=15
GO=b"P149_GO\n"

def require(ok,code):
    if not ok:raise ValueError("STRICT_PRODUCT_WINDOW_"+code)

class Window:
    def __init__(self,clock=time.monotonic):
        require(callable(clock),"CLOCK")
        self.clock=clock;self.last=None;self.started=None;self.completed=None
        self.process=None;self.go_writes=0;self.capture_count=0;self.stopped=False
        self.pending_constructor_error=None
    def now(self):
        value=self.clock()
        require(type(value) in (int,float) and math.isfinite(value)
            and (self.last is None or value>=self.last),"MONOTONIC_CLOCK")
        self.last=value;return value
    def begin(self):
        require(self.process is not None and self.started is None,"ONE_OWNED_GO")
        self.started=self.now();self.go_writes+=1
    def remaining(self):
        if self.pending_constructor_error is not None:raise self.pending_constructor_error
        require(self.started is not None and not self.stopped,"GO_REQUIRED_NOT_STOPPED")
        left=SECONDS-(self.now()-self.started)
        if left<=0:
            self.stopped=True;raise ValueError("STOP_STRICT_PRODUCT_WINDOW")
        return left
    def finish(self):
        require(self.completed is None,"ONE_COMPLETE_CAPTURE")
        self.remaining();self.completed=self.last
    def diagnostics(self):
        return dict(maximum_GO_to_complete_capture_seconds=SECONDS,
            original_GO_bytes_retained=True,actual_GO_writes=self.go_writes,
            actual_capture_count=self.capture_count,
            actual_complete_capture_within_window=self.completed is not None,
            GO_to_complete_capture_elapsed_seconds=None if self.completed is None else self.completed-self.started,
            stopped=self.stopped,added_sampler_thread_or_process_query=False,
            capture_constructor_window_check_failed=self.pending_constructor_error is not None,
            original_source_scope_rates_CPU_RAM600_and_1200_retained=True,
            blocking_OS_latency_hard_preemption_guaranteed=False,
            queue_advance_authorized=False,PC_freeze_resolved=False)

class Input:
    def __init__(self,original,state):self.original=original;self.state=state
    def __getattr__(self,name):return getattr(self.original,name)
    def write(self,value):
        require(type(value) is bytes and value==GO,"EXACT_ORIGINAL_GO_BYTES")
        self.state.begin()
        count=self.original.write(value)
        require(type(count) is int and count==len(value),"COMPLETE_GO_WRITE")
        self.state.remaining();return count
    def flush(self):
        result=self.original.flush();self.state.remaining();return result
    def close(self):return self.original.close()

def connect(factory,capture_type,clock=time.monotonic):
    require(callable(factory) and type(capture_type) is type,"EXACT_FACTORY_AND_CAPTURE")
    state=Window(clock)
    def popen(*args,**kwargs):
        require(state.process is None,"ONE_OWNED_PROCESS")
        process=factory(*args,**kwargs)
        state.process=process
        process.stdin=Input(process.stdin,state)
        return process
    class Capture(capture_type):
        def __init__(self,process,*args,**kwargs):
            require(process is state.process and state.capture_count==0,"SAME_OWNED_PROCESS_CAPTURE")
            state.remaining();super().__init__(process,*args,**kwargs)
            state.capture_count+=1
            try:state.remaining()
            except BaseException as error:
                # Let the original runner retain the constructed capture before
                # surfacing our post-construction guard, so pipe cleanup runs.
                state.pending_constructor_error=error
        def communicate(self,timeout):
            require(type(timeout) in (int,float) and math.isfinite(timeout) and timeout>0,"ORIGINAL_POSITIVE_TIMEOUT")
            result=super().communicate(timeout=min(timeout,state.remaining()))
            state.finish();return result
        def progress(self):
            if state.completed is None:state.remaining()
            return super().progress()
        # Original close remains inherited: never time-guard cleanup.
    return NS(Popen=popen,Capture=Capture,state=state)
