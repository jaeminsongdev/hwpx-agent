"""Diagnostic transport dependency: original readiness, never original GO.

Keep the original connection, Gate.write and strict-window Input unchanged.
The Gate's transport is replaced only after the original Popen returns its
actual process. It raises after real readiness checks, before Input.write.
This is not a product runner or an acceptance/Frame-commit authority.
"""
from types import CellType,FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_pre_go_stop.py'
TEST='tools/p09/tests/test_batch_pre_go_stop.py'
STOP='BATCH_PRE_GO_DIAGNOSTIC_STOP'


def require(ok,code):
    if not ok:raise ValueError('BATCH_PRE_GO_'+code)


class DiagnosticStop(ValueError):
    def __init__(self):super().__init__(STOP)


class BlockedTransport:
    """No bytes/flush delegated; close still closes the actual original pipe."""
    def __init__(self,original,gate,state,go):
        self.original=original;self.gate=gate;self.state=state;self.go=go
        self.blocks=0;self.reached=False;self.closed=False

    def __getattr__(self,name):return getattr(self.original,name)

    def write(self,value):
        self.blocks+=1
        require(not self.closed and not self.reached,'NO_RETRY_OR_CLOSED_TRANSPORT')
        require(type(value) is bytes and value==self.go,
            'EXACT_ORIGINAL_GO_AT_STOP')
        require(self.gate.original is self and self.gate.attempted is True and self.gate.ready is True
            and self.gate.written is False and self.gate.stopped is False,'ORIGINAL_READY_GATE_BEFORE_FORWARD')
        require(self.original.state is self.state and self.state.started is None and self.state.completed is None
            and self.state.go_writes==self.state.capture_count==0,'ORIGINAL_PRODUCT_WINDOW_NOT_STARTED')
        self.reached=True
        raise DiagnosticStop()

    def flush(self):
        raise ValueError('BATCH_PRE_GO_FLUSH_PERMANENTLY_DENIED')

    def close(self):
        # Do not pre-mark cleanup successful if the real close raises.
        result=self.original.close();self.closed=True;return result


class DeferredBlock:
    """Preserve a successfully created process even if adapter setup fails."""
    def __init__(self,original):self.original=original
    def __getattr__(self,name):return getattr(self.original,name)
    def write(self,value):raise ValueError('BATCH_PRE_GO_ADAPTER_SETUP_FAILED')
    def flush(self):raise ValueError('BATCH_PRE_GO_ADAPTER_SETUP_FAILED')
    def close(self):return self.original.close()


def connection_api(connection,protocol,component):
    """Explicit private dependency for native009_worker_launch.connect.

    No default module/class edits, counters, sampler, clock, Job, process or
    event are introduced. A failed attachment never loses a launched process.
    """
    require(component.SECONDS==10 and protocol.SECONDS==15 and component.GO==protocol.GO,
        'ORIGINAL_PRODUCT10_PREPARATION15')
    original_connect=connection.connect
    def connect(*args,**kwargs):
        require(len(args)>=2 and args[0] is component and args[1] is protocol,'SAME_EXPLICIT_ORIGINAL_COMPONENTS')
        binding=original_connect(*args,**kwargs)
        blockers=[];errors=[];attempts=[]
        original_popen=binding.Popen
        def popen(*a,**kw):
            require(not attempts,'ONE_DIAGNOSTIC_LAUNCH_NOT_RETRY')
            attempts.append(True)
            process=original_popen(*a,**kw)
            original_stream=process.stdin
            try:
                require(len(binding.gates)==len(binding.events)==1,'ONE_ORIGINAL_GATE_AND_EVENT')
                gate=binding.gates[0];state=binding.original_binding.state
                require(process.stdin is gate and gate.process is process and gate.event is binding.events[0],
                    'SAME_CREATED_PROCESS_GATE_EVENT')
                require(type(gate).__bases__==(protocol.Gate,) and 'write' not in vars(type(gate))
                    and 'flush' not in vars(type(gate)),'UNCHANGED_ORIGINAL_GATE_WRITE_AND_FLUSH')
                require(type(gate.original) is component.Input and gate.original.state is state
                    and state.process is process,'SAME_ACTUAL_STRICT_WINDOW_INPUT')
                require(gate.attempted is False and gate.ready is False and gate.written is False
                    and gate.stopped is False and state.started is state.completed is None
                    and state.go_writes==state.capture_count==0,'UNUSED_ORIGINAL_GATE_AND_WINDOW')
                blocker=BlockedTransport(gate.original,gate,state,protocol.GO)
                gate.original=blocker;blockers.append(blocker)
            except BaseException as error:
                errors.append(type(error).__name__)
                process.stdin=DeferredBlock(original_stream)
            return process
        def evidence():
            gate=binding.gates[0] if len(binding.gates)==1 else None
            state=binding.original_binding.state
            return dict(diagnostic_launch_attempts=len(attempts),transport_adapters=len(blockers),
                adapter_setup_error_types=list(errors),
                stop_reached_after_original_readiness=bool(blockers) and blockers[0].reached,
                original_input_write_or_flush_delegated_by_adapter=False,actual_GO_writes=state.go_writes,
                actual_capture_count=state.capture_count,original_product_clock_started=state.started is not None,
                original_gate=binding.state.diagnostics(),
                actual_transport_closed=bool(blockers) and blockers[0].closed,
                original_gate_stopped=None if gate is None else gate.stopped,
                added_sampler_or_Job_or_Frame=False,Native_or_product_or_acceptance_qualified=False)
        def validate_stop(*,cleanup_required):
            require(type(cleanup_required) is bool,'EXPLICIT_CLEANUP_REQUIREMENT')
            require(len(attempts)==len(blockers)==len(binding.gates)==len(binding.events)==1 and not errors,
                'ONE_SUCCESSFUL_ADAPTER_NOT_SETUP_FAILURE')
            blocker=blockers[0];gate=binding.gates[0];state=binding.original_binding.state
            require(blocker.reached and blocker.blocks==1 and gate.ready is True and gate.attempted is True
                and gate.stopped is True and gate.written is False and gate.original is blocker,
                'EXACT_DIAGNOSTIC_STOP_NOT_READINESS_OR_RESOURCE_FAILURE')
            require(state.started is state.completed is None and state.go_writes==state.capture_count==0,
                'ZERO_ACTUAL_GO_OR_CAPTURE')
            if cleanup_required:require(blocker.closed,'ACTUAL_INPUT_CLOSE_REQUIRED')
            return evidence()
        return NS(**{**vars(binding),'Popen':popen,'pre_go_evidence':evidence,
            'validate_pre_go_stop':validate_stop})
    return NS(**{**vars(connection),'connect':connect,'diagnostic_NO_GO_only':True})


def connect_parent(context):
    """Replace one explicit connection closure cell on the actual parent.

    Call before its single original owner_scope execution; restore afterwards.
    The original parent connect body and all other closure objects are retained.
    No run method, Frame method, Job dependency or execution counter is changed.
    """
    require(context.parent is not None and context.parent.attempts==0 and context.parent.frames==[]
        and context.attempts==context.jobs==context.restorations==context.frame_checks==0
        and not context.active and not context.bindings and len(context.windows)==1,
        'ONE_ACTUAL_UNEXECUTED_PARENT_CONTEXT')
    component=context.windows[0].component;original=component.connect
    require(type(original) is FunctionType and original.__name__=='connect'
        and original.__code__.co_filename.replace('\\','/').endswith('native009_parent_launch_v1.py'),
        'ORIGINAL_PARENT_COMPONENT_CONNECT')
    names=original.__code__.co_freevars
    cells=dict(zip(names,(c.cell_contents for c in original.__closure__)))
    require(set(cells)=={'c','connection','context','entry_pin','launch','original_component','protocol','root'}
        and cells['context'] is context,'EXACT_ORIGINAL_PARENT_DEPENDENCIES')
    selected=connection_api(cells['connection'],cells['protocol'],cells['original_component'])
    bindings=[];restored=False
    def connect(*args,**kwargs):
        require(not restored and not bindings,'ONE_ORIGINAL_PARENT_DIAGNOSTIC_BINDING')
        binding=selected.connect(*args,**kwargs);bindings.append(binding);return binding
    dependency=NS(**{**vars(selected),'connect':connect})
    closure=tuple(CellType(dependency) if n=='connection' else c for n,c in zip(names,original.__closure__))
    wrapped=FunctionType(original.__code__,original.__globals__,name=original.__name__,
        argdefs=original.__defaults__,closure=closure)
    wrapped.__kwdefaults__=original.__kwdefaults__
    require(wrapped.__code__ is original.__code__ and wrapped.__globals__ is original.__globals__
        and wrapped.__defaults__ is original.__defaults__ and wrapped.__kwdefaults__ is original.__kwdefaults__
        and all(n=='connection' or a is b for n,a,b in zip(names,wrapped.__closure__,original.__closure__)),
        'ENTIRE_PARENT_CONNECT_CODE_AND_OTHER_CLOSURE_CELLS')
    component.connect=wrapped
    def restore():
        nonlocal restored
        require(not context.active,'ORIGINAL_OWNER_SCOPE_MUST_CLOSE_FIRST')
        require(component.connect is (original if restored else wrapped),'PRIVATE_CONNECTION_NOT_OVERWRITTEN')
        component.connect=original;restored=True
    def evidence(*,cleanup_required):
        require(len(bindings)==1 and len(context.bindings)==1,'SAME_ACTUAL_PARENT_RETAINED_BINDING')
        actual=context.bindings[0];selected=bindings[0]
        require(actual.original_binding is selected.original_binding and actual.gates is selected.gates
            and actual.events is selected.events and actual.Popen is selected.Popen
            and actual.validate_pre_go_stop is selected.validate_pre_go_stop,
            'SAME_ACTUAL_PARENT_RETAINED_BINDING')
        row=bindings[0].validate_pre_go_stop(cleanup_required=cleanup_required)
        require(context.attempts==context.jobs==1 and context.frame_checks>0,
            'ORIGINAL_PARENT_JOB_AND_FRAME_CHECKS_OBSERVED')
        require(context.parent.attempts==1 and len(context.parent.frames)==1,'ORIGINAL_ENGINE_ATTEMPT_REQUIRED')
        if cleanup_required:
            require(restored and not context.active and context.restorations==1,
                'ORIGINAL_PARENT_SCOPE_AND_CONNECTION_RESTORED')
        return dict(row,parent_connect_code_defaults_globals_and_other_closure_cells_unchanged=True,
            parent_original_scope=context.evidence(),private_connection_restored=restored,
            actual_Native_Frame_or_product_qualified=False)
    return NS(original=original,wrapped=wrapped,bindings=bindings,restore=restore,evidence=evidence)
