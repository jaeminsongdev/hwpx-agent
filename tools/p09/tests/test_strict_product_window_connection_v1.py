import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import strict_product_window_connection_v1 as m
import strict_product_window_v1 as window
import native_pressure_full_connection_v1 as link
import accept_case112_current_epoch as a

class Capture:
    def __init__(self,p):self.process=p
    def communicate(self,timeout):return ("ok","")
    def progress(self):return ([],[])
    def close(self):pass
def prototype(fail=False,qualify=True):
    proc=NS(stdin=io.BytesIO());outputs=[];sp=NS(Popen=lambda *args,**kwargs:proc)
    js=NS(dump=lambda row,file,**kw:outputs.append(row))
    def run(run):
        p=subprocess.Popen("original");p.stdin.write(window.GO);p.stdin.flush();c=BoundedProcessCapture(p);c.communicate(.5)
        if fail:raise error
        json.dump(dict(current_generation_runtime_candidate_qualified=qualify),None)
        return 0
    error=ValueError("ORIGINAL_ENGINE_ERROR")
    fn=FunctionType(run.__code__,dict(subprocess=sp,json=js,BoundedProcessCapture=Capture,window=window),closure=run.__closure__)
    return NS(run_owned=fn,worker=lambda task:0),sp,js,outputs,error

class Tests(unittest.TestCase):
    def test_original_engine_one_call_worker_and_global_bindings_restored(self):
        engine,sp,js,out,_=prototype();oldp,oldd,oldc=sp.Popen,js.dump,engine.run_owned.__globals__["BoundedProcessCapture"]
        connected,state=m.connect_engine(engine,window)
        self.assertEqual(connected.run_owned(1),0);self.assertEqual(state.calls,[1])
        self.assertIs(connected.worker,engine.worker);self.assertIs(sp.Popen,oldp);self.assertIs(js.dump,oldd)
        self.assertIs(engine.run_owned.__globals__["BoundedProcessCapture"],oldc)
        self.assertIs(out[0]["strict_product_window"]["actual_complete_capture_within_window"],True)
    def test_exception_identity_and_restoration_without_retry(self):
        engine,sp,js,_,error=prototype(True);oldp,oldd=sp.Popen,js.dump
        connected,state=m.connect_engine(engine,window)
        with self.assertRaises(ValueError) as ctx:connected.run_owned(1)
        self.assertIs(ctx.exception,error);self.assertIs(sp.Popen,oldp);self.assertIs(js.dump,oldd)
        with self.assertRaises(ValueError):connected.run_owned(1)
        self.assertEqual(state.calls,[1])
    def test_stopped_or_uncompleted_window_cannot_be_runtime_pass(self):
        class CaptureNoComplete(window.Window):pass
        engine,sp,js,out,_=prototype();broken=NS(**vars(window))
        def connect(*args,**kwargs):
            result=window.connect(*args,**kwargs)
            result.state.finish=lambda:None
            return result
        broken.connect=connect;connected,_=m.connect_engine(engine,broken)
        with self.assertRaises(ValueError):connected.run_owned(1)
        self.assertEqual(out,[])
    def test_nonqualified_stop_row_retains_diagnostic_without_pass(self):
        engine,_,_,out,_=prototype(qualify=False);connected,_=m.connect_engine(engine,window);connected.run_owned(1)
        self.assertIs(out[0]["current_generation_runtime_candidate_qualified"],False)
    def test_scalar_pipeline_row_rejected(self):
        engine,sp,js,_,_=prototype()
        original=engine.run_owned
        def scalar(run):json.dump([],None)
        engine.run_owned=FunctionType(scalar.__code__,original.__globals__)
        connected,_=m.connect_engine(engine,window)
        with self.assertRaises(ValueError):connected.run_owned(1)
    def test_full_oracle_only_runtime_cost_product_field_projected(self):
        import ast
        node=ast.parse('def f():\n fields(budget,dict(product_allowance_seconds=20,unallocated_margin_seconds=60),"RUNTIME_COST")\n').body[0]
        def budget(*args):return views.model(*args)
        def cost(*args):return runtime_budget(*args)
        def retained(*args):return runtime_budget(*args)
        orig=NS(runtime_budget=budget,cost=cost,retained_evidence=retained,mechanics_projection=lambda n:n)
        new=m.direct_oracle(orig,NS(model=lambda *a:None),link)
        revised=new.mechanics_projection(node)
        call=revised.body[0].value
        self.assertEqual(call.args[1].keywords[0].value.value,15)
        self.assertEqual(call.args[1].keywords[1].value.value,60)
        self.assertIs(new.runtime_budget.__code__,budget.__code__)
    def test_wrong_original_runtime_product_expectation_rejected(self):
        import ast
        node=ast.parse('def f():\n fields(budget,dict(product_allowance_seconds=19),"RUNTIME_COST")\n').body[0]
        orig=NS(runtime_budget=lambda:None,cost=lambda:None,retained_evidence=lambda:None,mechanics_projection=lambda n:n)
        new=m.direct_oracle(orig,NS(),link)
        with self.assertRaises(ValueError):new.mechanics_projection(node)
    def test_pipe_or_closed_frame_never_full_product_evidence(self):
        row=dict(selected_test_index=157,source_frame=dict(frame_state="CLOSED"))
        with self.assertRaises(ValueError):m.check_evidence(row,a)
    def test_historical156_and_other_unqualified_cases_rejected(self):
        for index in (True,156,158):
            with self.assertRaises(ValueError):m.check_evidence(dict(selected_test_index=index),a)

if __name__=="__main__":unittest.main()
