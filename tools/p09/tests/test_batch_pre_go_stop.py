"""Real original Gate/strict10/connection, fake process/event only; no IO."""
import io
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import unittest
import batch_pre_go_stop as module
import worker_readiness_v1 as protocol
import worker_readiness_connection_v1 as connection
import strict_product_window_v1 as original_window
import post_product_recovery_window_v1 as recovery
import native009_parent_launch_v1 as parent_launch


class Clock:
    def __init__(self):self.value=0.
    def __call__(self):return self.value


class Pipe(io.BytesIO):
    def __init__(self):super().__init__();self.writes=0;self.flushes=0;self.closes=0;self.close_error=False
    def write(self,value):self.writes+=1;return super().write(value)
    def flush(self):self.flushes+=1;return super().flush()
    def close(self):
        self.closes+=1
        if self.close_error:raise OSError('TEST_CLOSE_FAILURE')
        return super().close()


class Event:
    def __init__(self,clock):self.clock=clock;self.waits=0;self.closes=0;self.ready=True;self.delay=.01
    def wait(self,ms):self.waits+=1;self.clock.value+=self.delay;return self.ready
    def close(self):self.closes+=1


class Capture:
    calls=0
    def __init__(self,process):Capture.calls+=1


WINDOW=None


def setUpModule():
    global WINDOW
    root=Path(__file__).resolve().parents[3]
    raw=(root/recovery.WINDOW_PIN['path']).read_bytes()
    WINDOW=recovery.tighten_window(original_window,raw)


def fixture(*,owned=lambda p:True,checkpoint=lambda:None,launch=None,conn=connection):
    clock=Clock();pipe=Pipe();event=Event(clock)
    process=NS(stdin=pipe,pid=123,poll=lambda:None);calls=[]
    def factory(*a,**kw):calls.append((a,kw));return process
    def actual_launch(original,actual_event,*a,**kw):
        assert actual_event is event
        return original(*a,**kw)
    api=module.connection_api(conn,protocol,WINDOW)
    binding=api.connect(WINDOW,protocol,factory,Capture,actual_launch if launch is None else launch,
        owned,checkpoint,event_factory=lambda:event,clock=clock)
    return NS(api=api,binding=binding,clock=clock,pipe=pipe,event=event,process=process,calls=calls)


class Tests(unittest.TestCase):
    def spawn(self,**kwargs):
        f=fixture(**kwargs);self.assertIs(f.binding.Popen('original',flag=3),f.process);return f

    def stop(self,f):
        with self.assertRaises(module.DiagnosticStop) as caught:f.process.stdin.write(protocol.GO)
        self.assertEqual(caught.exception.args,(module.STOP,))

    def test_real_gate_ready_then_stop_before_actual_input_or_clock(self):
        f=self.spawn();gate=f.binding.gates[0];original=gate.original.original
        self.stop(f);self.assertTrue(gate.ready and gate.stopped and gate.attempted)
        self.assertFalse(gate.written);self.assertEqual(f.event.waits,1)
        self.assertIs(original.state,f.binding.original_binding.state)
        self.assertEqual((f.pipe.writes,f.pipe.flushes),(0,0));self.assertEqual(f.pipe.getvalue(),b'')
        self.assertIsNone(original.state.started);self.assertEqual(original.state.go_writes,0)
        row=f.binding.validate_pre_go_stop(cleanup_required=False)
        self.assertTrue(row['stop_reached_after_original_readiness'])
        f.process.stdin.close();self.assertTrue(f.binding.validate_pre_go_stop(cleanup_required=True)['actual_transport_closed'])

    def test_original_factory_process_and_capture_preserved(self):
        f=self.spawn();self.assertEqual(f.calls,[(('original',),{'flag':3})])
        self.assertIs(f.binding.Capture,f.binding.original_binding.Capture)
        self.assertIs(f.binding.state.process,f.process);f.process.stdin.close()

    def test_original_gate_methods_and_component_classes_unchanged(self):
        methods=tuple((fn,fn.__code__,fn.__defaults__,fn.__closure__,fn.__kwdefaults__)
            for fn in (protocol.Gate.write,protocol.Gate.flush,WINDOW.Input.write,WINDOW.Input.close,
                connection.connect,WINDOW.connect))
        attrs=(dict(vars(protocol.Gate)),dict(vars(WINDOW.Input)))
        f=self.spawn();self.stop(f);f.process.stdin.close()
        for fn,code,defaults,closure,keywords in methods:
            self.assertIs(fn.__code__,code);self.assertIs(fn.__defaults__,defaults)
            self.assertIs(fn.__closure__,closure);self.assertEqual(fn.__kwdefaults__,keywords)
        self.assertEqual(dict(vars(protocol.Gate)),attrs[0]);self.assertEqual(dict(vars(WINDOW.Input)),attrs[1])
        self.assertEqual((original_window.SECONDS,WINDOW.SECONDS,protocol.SECONDS),(15,10,15))

    def test_resource_check_runs_at_original_two_guard_boundaries(self):
        checks=[];f=self.spawn(checkpoint=lambda:checks.append('original'))
        self.stop(f);self.assertEqual(checks,['original','original']);f.process.stdin.close()

    def test_owner_checked_before_wait_and_after_readiness(self):
        checks=[];f=self.spawn(owned=lambda p:checks.append(p) or True)
        self.stop(f);self.assertEqual(checks,[f.process]*3);f.process.stdin.close()

    def test_failed_owner_is_not_diagnostic_success_and_no_forward(self):
        f=self.spawn(owned=lambda p:False)
        with self.assertRaisesRegex(ValueError,'SAME_LIVE_OWNED'):f.process.stdin.write(protocol.GO)
        with self.assertRaisesRegex(ValueError,'EXACT_DIAGNOSTIC_STOP'):f.binding.validate_pre_go_stop(cleanup_required=False)
        self.assertEqual((f.pipe.writes,f.pipe.flushes),(0,0));self.assertEqual(f.event.waits,0)
        f.process.stdin.close()

    def test_dead_process_is_not_readiness_or_stop_success(self):
        f=self.spawn();f.process.poll=lambda:1
        with self.assertRaisesRegex(ValueError,'SAME_LIVE_OWNED'):f.process.stdin.write(protocol.GO)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=False)
        self.assertEqual(f.pipe.writes,0);f.process.stdin.close()

    def test_original_resource_failure_identity_and_no_window_start(self):
        error=ValueError('TEST_CPU_PRESSURE')
        def fail():raise error
        f=self.spawn(checkpoint=fail)
        with self.assertRaises(ValueError) as caught:f.process.stdin.write(protocol.GO)
        self.assertIs(caught.exception,error);self.assertIsNone(f.binding.state.started)
        self.assertEqual(f.event.waits,0);f.process.stdin.close()

    def test_resource_failure_after_ready_is_not_diagnostic_success(self):
        checks=[];error=ValueError('TEST_POST_READY_PRESSURE')
        def fail_second():
            checks.append(True)
            if len(checks)==2:raise error
        f=self.spawn(checkpoint=fail_second)
        with self.assertRaises(ValueError) as caught:f.process.stdin.write(protocol.GO)
        self.assertIs(caught.exception,error);self.assertEqual(f.event.waits,1)
        self.assertFalse(f.binding.gates[0].ready)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=False)
        f.process.stdin.close()

    def test_original15_timeout_not_relabelled_and_no_clock_or_GO(self):
        f=self.spawn();f.event.ready=False;f.event.delay=5
        with self.assertRaisesRegex(ValueError,'PREPARATION_TIMEOUT'):f.process.stdin.write(protocol.GO)
        self.assertEqual(f.event.waits,3);self.assertEqual(f.pipe.writes,0);self.assertIsNone(f.binding.state.started)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=False)
        f.process.stdin.close()

    def test_nonboolean_event_result_fails_before_stop(self):
        f=self.spawn();f.event.ready=1
        with self.assertRaisesRegex(ValueError,'EXACT_EVENT_RESULT'):f.process.stdin.write(protocol.GO)
        self.assertEqual(f.pipe.writes,0);f.process.stdin.close()

    def test_invalid_or_text_GO_never_forwards(self):
        for value in (b'GO\n','P149_GO\n',bytearray(protocol.GO),b''):
            f=self.spawn()
            with self.assertRaises(ValueError):f.process.stdin.write(value)
            self.assertEqual(f.event.waits,0);self.assertEqual(f.pipe.writes,0);f.process.stdin.close()

    def test_write_and_flush_retry_both_refused_after_diagnostic_stop(self):
        f=self.spawn();self.stop(f)
        with self.assertRaisesRegex(ValueError,'ONE_GO_ATTEMPT'):f.process.stdin.write(protocol.GO)
        with self.assertRaisesRegex(ValueError,'WRITTEN_GO_REQUIRED'):f.process.stdin.flush()
        self.assertEqual((f.pipe.writes,f.pipe.flushes),(0,0));f.process.stdin.close()

    def test_transport_direct_write_and_flush_cannot_bypass_original_gate(self):
        f=self.spawn();blocked=f.process.stdin.original
        with self.assertRaises(ValueError):blocked.write(protocol.GO)
        with self.assertRaises(ValueError):blocked.flush()
        self.assertEqual((f.pipe.writes,f.pipe.flushes),(0,0));f.process.stdin.close()

    def test_capture_refused_before_actual_GO_and_original_capture_not_constructed(self):
        f=self.spawn();self.stop(f);before=Capture.calls
        with self.assertRaisesRegex(ValueError,'GO_REQUIRED'):f.binding.Capture(f.process)
        self.assertEqual(Capture.calls,before);f.process.stdin.close()

    def test_close_required_and_real_close_failure_not_hidden(self):
        f=self.spawn();self.stop(f)
        with self.assertRaisesRegex(ValueError,'ACTUAL_INPUT_CLOSE_REQUIRED'):f.binding.validate_pre_go_stop(cleanup_required=True)
        f.pipe.close_error=True
        with self.assertRaises(OSError):f.process.stdin.close()
        self.assertEqual(f.event.closes,1)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=True)
        f.pipe.close_error=False;f.process.stdin.close()
        self.assertTrue(f.pipe.closed);f.binding.validate_pre_go_stop(cleanup_required=True)

    def test_launch_failure_not_retried_or_relabelled(self):
        error=OSError('TEST_SPAWN_ERROR')
        def fail(*a,**kw):raise error
        f=fixture(launch=fail)
        with self.assertRaises(OSError) as caught:f.binding.Popen()
        self.assertIs(caught.exception,error);self.assertEqual(f.event.closes,1)
        with self.assertRaises(ValueError):f.binding.Popen()
        self.assertEqual(f.calls,[])

    def test_postspawn_original_setup_failure_returns_process_and_blocks(self):
        f=fixture();f.process.pid=True
        self.assertIs(f.binding.Popen(),f.process)
        with self.assertRaisesRegex(ValueError,'ADAPTER_SETUP_FAILED'):f.process.stdin.write(protocol.GO)
        self.assertEqual(f.pipe.writes,0);f.process.stdin.close()
        self.assertTrue(f.pipe.closed);self.assertEqual(f.event.closes,1)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=False)

    def test_postspawn_adapter_error_never_loses_process(self):
        def altered(*a,**kw):
            result=connection.connect(*a,**kw);original=result.Popen
            def popen(*args,**kwargs):
                process=original(*args,**kwargs);result.gates.clear();return process
            return NS(**{**vars(result),'Popen':popen})
        f=fixture(conn=NS(connect=altered))
        self.assertIs(f.binding.Popen(),f.process)
        with self.assertRaisesRegex(ValueError,'ADAPTER_SETUP_FAILED'):f.process.stdin.flush()
        self.assertEqual((f.pipe.writes,f.pipe.flushes),(0,0));f.process.stdin.close();self.assertTrue(f.pipe.closed)

    def test_no_new_lifecycle_or_success_before_write(self):
        f=fixture();row=f.binding.pre_go_evidence()
        self.assertEqual(row['diagnostic_launch_attempts'],0);self.assertFalse(row['stop_reached_after_original_readiness'])
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=False)
        self.assertFalse(row['Native_or_product_or_acceptance_qualified'])

    def test_exact_component_and_original10_15_required(self):
        f=fixture()
        with self.assertRaises(ValueError):f.api.connect(NS(**vars(WINDOW)),protocol,None,None,None,None,None)
        with self.assertRaises(ValueError):module.connection_api(connection,protocol,original_window)

    def test_close_before_write_cannot_become_stop_success(self):
        f=self.spawn();f.process.stdin.close()
        with self.assertRaises(ValueError):f.process.stdin.write(protocol.GO)
        with self.assertRaises(ValueError):f.binding.validate_pre_go_stop(cleanup_required=True)
        self.assertEqual(f.pipe.writes,0)


def parent_fixture():
    """Original parent connection/scope, synthetic Job and Frame, no process."""
    class Windows:
        def job(self):return object()
    clock=Clock();event=Event(clock);pipe=Pipe()
    process=NS(stdin=pipe,pid=123,poll=lambda:None)
    current=NS(WINDOW=WINDOW,WINDOW_LINK=NS(connect_engine=lambda *a:None))
    def template():return None
    current.template=template
    def clone(fn,**environment):
        return FunctionType(fn.__code__,dict(fn.__globals__,**environment),argdefs=fn.__defaults__,closure=fn.__closure__)
    def connect(root,pin,component,prot,conn,factory,capture_type,subprocess,owned,checkpoint):
        def launch(original,event,*a,**kw):return original(*a,**kw)
        binding=conn.connect(component,prot,factory,capture_type,launch,owned,checkpoint,
            event_factory=lambda:event,clock=clock)
        return NS(**{**vars(binding),'launch_state':NS(actual=process)})
    launch=NS(connect=connect,same_owned_job=lambda owner,job,expected,actual:expected is actual)
    recovery_api=NS(current_window=lambda *a:(current,{}),clone=clone)
    api,ctx=parent_launch.recovery_api(recovery_api,None,{},launch,protocol,connection,NS(Windows=Windows,subprocess=None))
    api.current_window(None,None,None)
    state=NS(attempts=0,frames=[]);ctx.bind_parent(state)
    frame=NS(state='BEFORE_READ',reading=False,boundaries=[object()],check=lambda:None)
    return NS(ctx=ctx,state=state,frame=frame,process=process,event=event,pipe=pipe,Windows=Windows)


class ParentTests(unittest.TestCase):
    def test_actual_parent_connection_one_cell_change_and_restore(self):
        f=parent_fixture();fn=f.ctx.windows[0].component.connect
        adapter=module.connect_parent(f.ctx)
        self.assertIs(adapter.wrapped.__code__,fn.__code__);self.assertIs(adapter.wrapped.__globals__,fn.__globals__)
        for n,a,b in zip(fn.__code__.co_freevars,fn.__closure__,adapter.wrapped.__closure__):
            if n=='connection':self.assertIsNot(a,b)
            else:self.assertIs(a,b)
        self.assertEqual((f.ctx.attempts,f.ctx.jobs,f.state.attempts),(0,0,0))
        adapter.restore();self.assertIs(f.ctx.windows[0].component.connect,fn);adapter.restore()

    def test_actual_parent_connect_original_scope_checkpoint_and_same_retained_binding(self):
        f=parent_fixture();adapter=module.connect_parent(f.ctx);before=f.Windows.job
        f.state.frames.append(f.frame)
        with f.ctx.owner_scope():
            f.Windows().job()
            binding=f.ctx.windows[0].component.connect(lambda *a,**kw:f.process,Capture)
            self.assertIs(binding.Popen(),f.process)
            with self.assertRaises(module.DiagnosticStop):f.process.stdin.write(protocol.GO)
            self.assertIs(binding,f.ctx.bindings[0])
            self.assertIs(binding.original_binding,adapter.bindings[0].original_binding)
            self.assertEqual(f.ctx.frame_checks,2);self.assertTrue(binding.gates[0].ready)
            f.process.stdin.close()
            with self.assertRaisesRegex(ValueError,'SCOPE_MUST_CLOSE'):adapter.restore()
        adapter.restore()
        # A synthetic Frame/Job and original Context alone cannot qualify an
        # engine run: its actual parent attempt must have happened as well.
        with self.assertRaisesRegex(ValueError,'ORIGINAL_ENGINE_ATTEMPT_REQUIRED'):adapter.evidence(cleanup_required=True)
        self.assertIs(f.ctx.windows[0].component.connect,adapter.original);self.assertEqual(f.pipe.writes,0)
        self.assertEqual(f.state.attempts,0);self.assertIs(f.Windows.job,before)

    def test_actual_parent_missing_or_second_byte_boundary_still_denies(self):
        for invalid in ('no_frame','two_boundaries','wrong_state'):
            f=parent_fixture();adapter=module.connect_parent(f.ctx)
            if invalid!='no_frame':f.state.frames.append(f.frame)
            if invalid=='two_boundaries':f.frame.boundaries.append(object())
            if invalid=='wrong_state':f.frame.state='HELD'
            with f.ctx.owner_scope():
                f.Windows().job()
                binding=f.ctx.windows[0].component.connect(lambda *a,**kw:f.process,Capture);binding.Popen()
                with self.assertRaises(ValueError):f.process.stdin.write(protocol.GO)
                self.assertEqual(f.event.waits,0);f.process.stdin.close()
            adapter.restore()
            with self.assertRaises(ValueError):adapter.evidence(cleanup_required=True)

    def test_parent_scope_failure_restores_job_but_does_not_claim_diagnostic_stop(self):
        f=parent_fixture();adapter=module.connect_parent(f.ctx);before=f.Windows.job
        with self.assertRaises(OSError):
            with f.ctx.owner_scope():f.Windows().job();raise OSError('TEST_PARENT_BODY_FAILURE')
        adapter.restore();self.assertIs(f.Windows.job,before)
        with self.assertRaises(ValueError):adapter.evidence(cleanup_required=True)
        with self.assertRaises(ValueError):
            with f.ctx.owner_scope():pass

    def test_parent_adapter_rejects_started_or_used_context(self):
        for field,value in (('attempts',1),('jobs',1),('active',True),('frame_checks',1),('restorations',1)):
            f=parent_fixture();setattr(f.ctx,field,value)
            with self.assertRaises(ValueError):module.connect_parent(f.ctx)

    def test_parent_adapter_rejects_foreign_connect_or_closure(self):
        f=parent_fixture();f.ctx.windows[0].component.connect=lambda:None
        with self.assertRaises(ValueError):module.connect_parent(f.ctx)

    def test_parent_adapter_does_not_overwrite_later_component_change(self):
        f=parent_fixture();adapter=module.connect_parent(f.ctx)
        other=lambda:None;f.ctx.windows[0].component.connect=other
        with self.assertRaises(ValueError):adapter.restore()
        self.assertIs(f.ctx.windows[0].component.connect,other)

    def test_restored_adapter_cannot_be_reused_to_create_diagnostic_binding(self):
        f=parent_fixture();adapter=module.connect_parent(f.ctx);adapter.restore()
        dependencies=dict(zip(adapter.wrapped.__code__.co_freevars,
            (c.cell_contents for c in adapter.wrapped.__closure__)))
        with self.assertRaises(ValueError):dependencies['connection'].connect()
