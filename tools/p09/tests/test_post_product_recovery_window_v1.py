import io
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import strict_product_window_v1 as original
import strict_product_window_model_v1 as model
import native_pressure_failfast_v1 as pressure
import current_stored_runtime_scope as scope
from tests.test_strict_product_window_model_v1 import old_model,RAW,pins

MODULE=None
RAW_WINDOW=(Path(__file__).resolve().parents[3]/original.SELF).read_bytes()


class Capture:
    def __init__(self,process):self.process=process;self.closed=False;self.timeout=None
    def communicate(self,timeout):self.timeout=timeout;return ("complete","")
    def progress(self):return ([],[])
    def close(self):self.closed=True


def started():
    component=MODULE.tighten_window(original,RAW_WINDOW)
    now=[0.];process=NS(stdin=io.BytesIO())
    binding=component.connect(lambda:process,Capture,clock=lambda:now[0])
    binding.Popen();process.stdin.write(original.GO);process.stdin.flush()
    return component,binding,process,now


class Tests(unittest.TestCase):
    def test_exact_private_compilation_profile_is_verified_as_a_whole(self):
        import ast,math,time
        tree=ast.parse(RAW_WINDOW.decode("utf-8"))
        nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef))]
        env=dict(__name__="p09_exact_fixture",math=math,time=time,NS=NS)
        exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
            original.connect.__code__.co_filename,"exec"),env)
        private=NS(**env);new=MODULE.tighten_window(private,RAW_WINDOW)
        self.assertEqual(new.SECONDS,10);self.assertEqual(private.SECONDS,15)
        mixed=NS(**{**vars(private),"connect":original.connect})
        # If both profiles compile identically there is no mixed distinction.
        if private.connect.__code__!=original.connect.__code__:
            with self.assertRaises(ValueError):MODULE.tighten_window(mixed,RAW_WINDOW)

    def test_failed_job_assignment_terminates_only_the_owned_waiting_helper(self):
        from unittest.mock import patch
        process=NS(stdin=io.BytesIO(),stdout=io.BytesIO(),stderr=io.BytesIO(),pid=12345,
            returncode=None,terminated=False)
        process.poll=lambda:process.returncode
        def terminate():process.terminated=True;process.returncode=1
        def wait(timeout):
            self.assertTrue(process.terminated);self.assertEqual(timeout,2);return 1
        process.terminate=terminate;process.wait=wait
        closed=[];k=NS(OpenProcess=lambda *args:1,AssignProcessToJobObject=lambda *args:False,
            CloseHandle=lambda h:closed.append(h) or True,TerminateJobObject=lambda *args:True)
        windows=NS(k=k,job=lambda:2,verify_job_limits=lambda job:dict(verified=True),
            accounting=lambda job:dict(active_processes=0))
        c=NS(Windows=lambda:windows,ROOT="unused")
        component=MODULE.tighten_window(original,RAW_WINDOW)
        with patch("subprocess.Popen",return_value=process):
            with self.assertRaisesRegex(ValueError,"OWNED_PIPE_JOB_ASSIGN"):
                MODULE.owned_pipe_cases(c,NS(check=lambda **kwargs:None),component)
        self.assertTrue(process.terminated);self.assertEqual(closed,[1,2])
        self.assertTrue(process.stdin.original.closed and process.stdout.closed and process.stderr.closed)

    def test_original_classes_and_globals_are_not_mutated(self):
        before=dict(original.Window.remaining.__globals__);new=MODULE.tighten_window(original,RAW_WINDOW)
        self.assertEqual(original.SECONDS,15);self.assertEqual(original.Window.remaining.__globals__,before)
        self.assertEqual(new.SECONDS,10);self.assertIs(new.Input,original.Input)
        self.assertIs(new.connect.__code__,original.connect.__code__)
        for name,value in vars(original.Window).items():
            if callable(value):self.assertIs(getattr(new.Window,name).__code__,value.__code__)

    def test_actual_capture_completes_below_ten_and_timeout_is_capped(self):
        _,binding,_,now=started();cap=binding.Capture(binding.state.process);now[0]=9.
        self.assertEqual(cap.communicate(100),("complete",""));self.assertEqual(cap.timeout,1.)
        self.assertEqual(binding.state.diagnostics()["maximum_GO_to_complete_capture_seconds"],10)
        self.assertTrue(binding.state.diagnostics()["actual_complete_capture_within_window"])

    def test_ten_second_stop_is_latched_and_cleanup_stays_unguarded(self):
        _,binding,_,now=started();cap=binding.Capture(binding.state.process);now[0]=10.
        with self.assertRaisesRegex(ValueError,"STOP_STRICT_PRODUCT_WINDOW"):cap.communicate(100)
        cap.close();self.assertTrue(cap.closed);now[0]=11.
        with self.assertRaises(ValueError):binding.state.remaining()
        self.assertFalse(binding.state.diagnostics()["actual_complete_capture_within_window"])

    def test_duplicate_GO_process_and_capture_are_still_rejected(self):
        _,binding,process,_=started();binding.Capture(process)
        for fn in (lambda:binding.Popen(),lambda:process.stdin.write(original.GO),lambda:binding.Capture(process)):
            with self.assertRaises(ValueError):fn()

    def test_wrong_source_and_modified_original_methods_rejected(self):
        with self.assertRaises(ValueError):MODULE.tighten_window(original,RAW_WINDOW+b"\n")
        class Changed(original.Window):
            def remaining(self):return 1000
        with self.assertRaises(ValueError):MODULE.tighten_window(NS(**{**vars(original),"Window":Changed}),RAW_WINDOW)

    def test_model_reduces_only_actual_product_reservation_by_five(self):
        old,_=model.project(old_model(),RAW,pressure,scope);new=MODULE.tighten_model(old)
        before=old(pins(),167);after=new(pins(),167)
        changed={k for k in after if before.get(k)!=after[k]}
        self.assertEqual(changed,{"product_allowance_seconds","predicted_runtime_combined_seconds",
            "strict_GO_to_complete_capture_window_seconds","product_reservation_reduction_seconds"})
        self.assertEqual(before["predicted_runtime_combined_seconds"]-after["predicted_runtime_combined_seconds"],5)
        self.assertEqual(after["product_allowance_seconds"],10)
        self.assertTrue(after["actual_window_binding_and_complete_capture_required_before_acceptance"])

    def test_all_source_rates_margins_and_diagnostic_allowances_remain(self):
        old,_=model.project(old_model(),RAW,pressure,scope);new=MODULE.tighten_model(old);row=new(pins(),167)
        for key,value in (("selected_acquisition_rate_per_second",14),("unallocated_margin_seconds",60),
            ("additional_early_source_wait_allowance_seconds",11),("unchanged_lock_deadline_seconds",600),
            ("final_inventory_pacing_seconds",167/20)):
            self.assertEqual(row[key],value)
        with self.assertRaises(ValueError):new(pins(),167,PDH_seconds=0)
        with self.assertRaises(ValueError):new(pins(300*1048576),167)

    def test_whole_model_inverse_and_original_closure_remain_untouched(self):
        old,_=model.project(old_model(),RAW,pressure,scope);inner=old.__closure__[0].cell_contents
        new=MODULE.tighten_model(old);changed=new.__closure__[0].cell_contents
        self.assertIs(old.__closure__[0].cell_contents,inner);self.assertIs(new.__globals__,old.__globals__)
        constants=list(changed.__code__.co_consts);index=next(i for i,v in enumerate(inner.__code__.co_consts) if type(v)is int and v==15)
        constants[index]=15;self.assertEqual(changed.__code__.replace(co_consts=tuple(constants)),inner.__code__)

    def test_unknown_models_and_already_tightened_models_fail_closed(self):
        with self.assertRaises(ValueError):MODULE.tighten_model(lambda *args:None)
        old,_=model.project(old_model(),RAW,pressure,scope)
        with self.assertRaises(ValueError):MODULE.tighten_model(MODULE.tighten_model(old))

    def test_no_GO_queue_or_implicit_runtime_authority_is_introduced(self):
        old,_=model.project(old_model(),RAW,pressure,scope);new=MODULE.tighten_model(old)
        row=new(pins(),167)
        self.assertFalse(row["GO_authorized"]);self.assertFalse(row["input_scope_reduction_or_rate_change"])
        self.assertIs(row["actual_window_binding_and_complete_capture_required_before_acceptance"],True)
