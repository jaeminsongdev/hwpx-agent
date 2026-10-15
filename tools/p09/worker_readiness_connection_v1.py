"""Candidate mechanical binding, not installed in the Native orchestrator.

Launch/Job membership/resource checkpoints are explicit dependencies. The
original 10-second component constructs its real Input and Capture first;
readiness is outside that Input, never a substitute window or fake GO.
"""
import math
from types import SimpleNamespace as NS

SELF="tools/p09/worker_readiness_connection_v1.py"
TEST="tools/p09/tests/test_worker_readiness_connection_v1.py"


def require(ok,label):
    if not ok:raise ValueError("READINESS_CONNECTION_"+label)


def connect(component,protocol,factory,capture_type,launch,verify_owned,checkpoint,
            *,event_factory=None,clock=None,seconds=15):
    require(type(component.SECONDS) is int and component.SECONDS==10 and component.GO==protocol.GO,"ORIGINAL_WINDOW10_AND_GO")
    require(all(callable(v) for v in (factory,launch,verify_owned,checkpoint)),"EXPLICIT_LAUNCH_JOB_AND_GUARD")
    require(type(seconds) in (int,float) and math.isfinite(seconds) and 0<seconds<=protocol.SECONDS,"BOUNDED_READINESS")
    if event_factory is None:event_factory=protocol.WindowsEvent
    require(callable(event_factory),"EXPLICIT_EVENT_FACTORY")
    events=[];gates=[];construction_errors=[]
    def owned_factory(*args,**kwargs):
        require(not events,"ONE_OWNED_LAUNCH_NOT_RETRY")
        event=event_factory();events.append(event)
        try:return launch(factory,event,*args,**kwargs)
        except BaseException:event.close();raise
    options={} if clock is None else dict(clock=clock)
    original=component.connect(owned_factory,capture_type,**options)
    class Input(protocol.Gate):
        def close(self):
            try:return super().close()
            finally:self.event.close()
    class DeferredFailure:
        # Never lose a created process by throwing before the original runner
        # receives it and assigns the Job. Surface setup failure at its GO.
        def __init__(self,stream,event,error):self.original=stream;self.event=event;self.error=error
        def __getattr__(self,name):return getattr(self.original,name)
        def write(self,value):raise self.error
        def flush(self):raise self.error
        def close(self):
            try:return self.original.close()
            finally:self.event.close()
    def popen(*args,**kwargs):
        process=original.Popen(*args,**kwargs);inner=process.stdin
        try:
            require(getattr(inner,"state",None) is original.state,"OUTSIDE_ACTUAL_ORIGINAL_WINDOW_INPUT")
            gate=Input(inner,events[0],process,verify_owned,checkpoint,seconds=seconds,**options)
            process.stdin=gate;gates.append(gate)
        except BaseException as error:
            construction_errors.append(type(error).__name__)
            process.stdin=DeferredFailure(inner,events[0],error)
        return process
    class State:
        def __getattr__(self,name):return getattr(original.state,name)
        def diagnostics(self):
            return dict(original.state.diagnostics(),worker_readiness=None if not gates else gates[0].diagnostics(),
                readiness_outside_actual_window_input=bool(gates),readiness_setup_errors=list(construction_errors),
                added_Native_retry_or_acceptance_authority=False)
    return NS(Popen=popen,Capture=original.Capture,state=State(),original_binding=original,
        events=events,gates=gates,Native_installed=False)


def budget_delta(base,*,additional_acquisitions,additional_other_bytes,
                 additional_inventory_checkpoints,readiness_seconds=15):
    """Explicit conservative delta, not a full source-qualified Native model.

    All additions include their actual new scope; callers must derive these
    from the complete manifest. This function never credits overlap, caching,
    the old 3 seconds, the 60-second margin or an unmeasured speed improvement.
    """
    require(type(base) is dict,"ORIGINAL_MODEL_REQUIRED")
    expected=dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
        product_allowance_seconds=10,strict_GO_to_complete_capture_window_seconds=10,
        selected_acquisition_rate_per_second=14,aggregate_envelope_decoder_allowance_seconds=5.0,
        actual_two_pass_byte_reads_retained=True)
    for key,value in expected.items():
        actual=base.get(key)
        require(type(actual) is type(value) and actual==value,"UNCHANGED_ORIGINAL_MODEL_TERMS")
    for value in (additional_acquisitions,additional_other_bytes,additional_inventory_checkpoints):
        require(type(value) is int and value>=0,"MEASURED_NONNEGATIVE_SCOPE_DELTA")
    require(type(readiness_seconds) in (int,float) and math.isfinite(readiness_seconds) and 0<readiness_seconds<=15,"BOUNDED_PREPARATION_ALLOWANCE")
    previous=base.get("predicted_runtime_combined_seconds")
    require(type(previous) in (int,float) and math.isfinite(previous) and 0<previous<600,"VALID_BASE_TOTAL")
    acquisition=additional_acquisitions/14
    byte_reads=2*additional_other_bytes/(2*1024*1024)
    inventory=additional_inventory_checkpoints/20
    total=previous+readiness_seconds+acquisition+byte_reads+inventory
    require(total<600,"COMPLETE_DELTA_OUTSIDE_ORIGINAL600")
    return dict(base_predicted_seconds=previous,additional_readiness_seconds=readiness_seconds,
        additional_native_acquisition_seconds=acquisition,additional_two_actual_byte_pass_seconds=byte_reads,
        additional_inventory_pacing_seconds=inventory,predicted_seconds=total,
        unchanged_deadline_seconds=600,unchanged_margin_seconds=60,
        preparation_added_without_overlap_or_old_allowance_credit=True,
        complete_manifest_derivation_still_required=True,actual_completion_guaranteed=False,
        Native_binding_qualified=False,GO_authorized=False)
