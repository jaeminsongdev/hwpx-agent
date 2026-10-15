from types import SimpleNamespace as NS
import unittest

MODULE=C=LAUNCH=CONNECTED=CONTEXT=SOURCE=GRAPH=HELPERS=INHERITED=SCOPE=API=GUARD=RECOVERY=WINDOW_TOOL=WINDOW_RAW=ORIGINAL_WINDOW=None


class Windows:
    def __init__(self):self.calls=0
    def job(self):self.calls+=1;return 456


class FakeFrame:
    def __init__(self):self.state='BEFORE_READ';self.reading=False;self.boundaries=[object()];self.checks=0;self.error=None
    def check(self):
        self.checks+=1
        if self.error is not None:raise self.error


def fixture():
    context=MODULE.Context(NS(Windows=Windows),LAUNCH)
    parent=NS(frames=[],attempts=0);context.bind_parent(parent)
    return context,parent,Windows()


class Tests(unittest.TestCase):
    def test_original_Job_is_delegated_once_and_method_restored(self):
        ctx,_,windows=fixture();before=Windows.job
        with ctx.owner_scope():
            self.assertEqual(windows.job(),456);self.assertIs(ctx.owner,windows);self.assertEqual(ctx.job,456)
            with self.assertRaises(ValueError):windows.job()
        self.assertIs(Windows.job,before);self.assertEqual(windows.calls,1)
        self.assertEqual((ctx.jobs,ctx.attempts,ctx.restorations),(1,1,1));self.assertFalse(ctx.active)

    def test_original_Job_method_restores_on_body_failure_and_no_retry(self):
        ctx,_,windows=fixture();before=Windows.job;error=ValueError('SYNTHETIC_ORIGINAL_STOP')
        with self.assertRaises(ValueError) as caught:
            with ctx.owner_scope():windows.job();raise error
        self.assertIs(caught.exception,error);self.assertIs(Windows.job,before)
        with self.assertRaises(ValueError):
            with ctx.owner_scope():pass

    def test_original_job_allocation_failure_is_not_relabelled(self):
        error=OSError('SYNTHETIC_JOB_ERROR')
        class Failing:
            def job(self):raise error
        ctx=MODULE.Context(NS(Windows=Failing),LAUNCH);ctx.bind_parent(NS(frames=[],attempts=0));before=Failing.job
        with self.assertRaises(OSError) as caught:
            with ctx.owner_scope():Failing().job()
        self.assertIs(caught.exception,error);self.assertIs(Failing.job,before);self.assertEqual(ctx.jobs,0)

    def test_no_metadata_only_guard_substituted_for_original_Frame_check(self):
        ctx,parent,windows=fixture();frame=FakeFrame();parent.frames.append(frame)
        with ctx.owner_scope():windows.job();ctx.checkpoint()
        self.assertEqual(frame.checks,1);self.assertEqual(ctx.frame_checks,1)

    def test_missing_or_unread_Frame_fails_closed(self):
        for kind in ('missing','NEW','reading','two_boundaries'):
            ctx,parent,windows=fixture();frame=FakeFrame()
            if kind!='missing':parent.frames.append(frame)
            if kind=='NEW':frame.state='NEW'
            if kind=='reading':frame.reading=True
            if kind=='two_boundaries':frame.boundaries.append(object())
            with ctx.owner_scope():
                windows.job()
                with self.assertRaises(ValueError):ctx.checkpoint()

    def test_original_Frame_resource_error_has_precedence(self):
        ctx,parent,windows=fixture();frame=FakeFrame();frame.state='NEW';error=ValueError('SYNTHETIC_CPU_STOP');frame.error=error
        parent.frames.append(frame)
        with ctx.owner_scope():
            windows.job()
            with self.assertRaises(ValueError) as caught:ctx.checkpoint()
            self.assertIs(caught.exception,error)

    def test_parent_is_bound_once_only_before_execution(self):
        ctx,parent,_=fixture()
        with self.assertRaises(ValueError):ctx.bind_parent(parent)
        other=MODULE.Context(NS(Windows=Windows),LAUNCH)
        with self.assertRaises(ValueError):other.bind_parent(NS(frames=[object()],attempts=0))
        with self.assertRaises(ValueError):other.bind_parent(NS(frames=[],attempts=1))

    def test_original_windows_and_template_checker_not_mutated(self):
        row=CONTEXT.windows[0];current=row.window;original=row.original_window
        self.assertIs(current.template.__code__,original.template.__code__)
        self.assertIs(current.template.__defaults__,original.template.__defaults__)
        self.assertIs(current.template.__closure__,original.template.__closure__)
        self.assertIs(current.WINDOW_LINK.check_evidence,original.WINDOW_LINK.check_evidence)
        self.assertEqual((original.WINDOW.SECONDS,current.WINDOW.SECONDS),(10,10))
        self.assertIsNot(current.WINDOW,original.WINDOW)

    def test_real_parent_shared_globals_and_original_worker_preserved(self):
        self.assertIs(CONNECTED.parent.run_owned.__globals__,CONNECTED.original_run.__globals__)
        self.assertIs(CONNECTED.parent.worker,CONNECTED.original_worker)
        self.assertEqual(len(CONTEXT.original_runs),1)
        self.assertIs(CONTEXT.parent,CONNECTED.parent_state)

    def test_actual_current_full72_and_independent_oracle_still_connected(self):
        self.assertEqual(len(GRAPH.binding.descriptors()),72)
        self.assertIs(type(SOURCE.state.policy),SOURCE.state.alias.VerifiedPolicy)
        self.assertEqual(CONNECTED.checker.environment['base'].CONFIG.index,165)
        self.assertEqual(CONNECTED.checker.environment['prior'].WINDOW.SECONDS,10)
        self.assertEqual(CONNECTED.checker.projectors,[])

    def test_actual_helper64_before_tests_and_no_native_execution(self):
        self.assertLessEqual(HELPERS['Native_count'],64)
        self.assertTrue(HELPERS['observed_before_project_test_module_load'])
        self.assertEqual((CONTEXT.jobs,CONTEXT.attempts,CONTEXT.frame_checks),(0,0,0))
        self.assertEqual(CONTEXT.bindings,[]);self.assertEqual(CONNECTED.parent_state.frames,[])
        self.assertEqual((CONNECTED.built.state.attempts,CONNECTED.built.state.calls),(0,0))

    def test_parent_owned_verification_uses_same_captured_Job_and_actual_process(self):
        seen=[];process=object()
        def verify(owner,job,expected,actual):seen.append((owner,job,expected,actual));return True
        ctx=MODULE.Context(NS(Windows=Windows),NS(same_owned_job=verify));ctx.bind_parent(NS(frames=[],attempts=0));windows=Windows()
        ctx.bindings.append(NS(launch_state=NS(actual=process),events=[]))
        with ctx.owner_scope():windows.job();self.assertTrue(ctx.owned(process))
        self.assertEqual(seen,[(windows,456,process,process)])
