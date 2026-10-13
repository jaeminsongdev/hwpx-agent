import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import acceptance_stage_observer_v1 as m

class Guard:
    def __init__(self):self.samples=[dict(system_cpu_percent=83.,parent_cpu_machine_percent=0.)];self.calls=[];self.error=None
    def check(self,force=False):
        self.calls.append(force)
        if self.error:raise self.error
        return "guard_result"
class Reader:
    def __init__(self,root,checkpoint):self.checkpoint=checkpoint;self.calls=[];self.error=None
    def _read(self,name,parse=False):
        self.calls.append((name,parse));self.checkpoint()
        if self.error:raise self.error
        return ("same_pin",b"same_bytes")
    def finish(self):return self._read("crates/a.rs")
def fake_execute():return original
def make():
    tracker=m.Tracker();definition_calls=[]
    def definitions(text,names,namespace):
        definition_calls.append((text,names,namespace))
        def rust_inputs(root,checkpoint):checkpoint();return {"a.rs"}
        return NS(rust_inputs=rust_inputs)
    old=NS(Guard=Guard,AcceptanceReader=Reader,native=NS(definitions=definitions),other=object())
    from types import FunctionType
    execute=FunctionType(fake_execute.__code__,dict(fake_execute.__globals__,original=old))
    projected=m.projection(execute,tracker)
    return old,projected(),tracker,definition_calls,execute,projected

class Tests(unittest.TestCase):
    def test_original_execute_code_defaults_closure_and_namespace_retained(self):
        old,new,t,c,fn,p=make();self.assertIs(fn.__code__,p.__code__);self.assertEqual(fn.__defaults__,p.__defaults__)
        self.assertIs(fn.__closure__,p.__closure__);self.assertIs(new.other,old.other);self.assertIs(old.Guard,Guard)
    def test_guard_one_original_call_force_and_result(self):
        _,new,t,*_=make();g=new.Guard();self.assertEqual(g.check(force=True),"guard_result");self.assertEqual(g.calls,[True])
    def test_warning_error_identity_and_original_sample_retained(self):
        _,new,t,*_=make();g=new.Guard();error=ValueError("ORIGINAL_STOP");g.error=error
        r=new.AcceptanceReader("root",g.check)
        with self.assertRaises(ValueError) as ctx:r._read("crates/a.rs",True)
        self.assertIs(ctx.exception,error);self.assertEqual(g.calls,[False]);self.assertEqual(t.first_stop["stage"],"fresh_read:rust_source")
        self.assertEqual(t.first_stop["original_sample"],g.samples[-1]);self.assertEqual(t.current,"outside_io")
    def test_read_arguments_result_and_one_call_unchanged(self):
        _,new,t,*_=make();r=new.AcceptanceReader("root",lambda:None)
        self.assertEqual(r._read("implementation/private.json",True),("same_pin",b"same_bytes"))
        self.assertEqual(r.calls,[("implementation/private.json",True)]);self.assertEqual(t.read_completed,1)
        self.assertNotIn("private.json",str(t.summary()))
    def test_finish_calls_all_original_reads_and_restores_nested_state(self):
        _,new,t,*_=make();r=new.AcceptanceReader("root",lambda:None);self.assertEqual(r.finish(),("same_pin",b"same_bytes"))
        self.assertEqual(t.finish_completed,1);self.assertEqual(t.read_completed,1);self.assertFalse(t.final_hash)
        self.assertIn("final_hash:rust_source",t.history)
    def test_inventory_delegate_once_checkpoint_order_and_result(self):
        _,new,t,c,*_=make();seen=[];ns=new.native.definitions("text",("rust_inputs",),{})
        self.assertEqual(ns.rust_inputs("root",lambda:seen.append(1)),{"a.rs"});self.assertEqual(seen,[1]);self.assertEqual(len(c),1)
        self.assertEqual(t.inventory_attempts,1);self.assertEqual(t.inventory_completed,1)
    def test_inventory_error_keeps_stage_and_original_error_without_retry(self):
        _,new,t,*_=make();g=new.Guard();g.error=ValueError("STOP");ns=new.native.definitions("text",("rust_inputs",),{})
        with self.assertRaises(ValueError):ns.rust_inputs("root",g.check)
        self.assertEqual(t.first_stop["stage"],"rust_inventory");self.assertEqual(t.inventory_completed,0);self.assertEqual(g.calls,[False])
    def test_history_bound_and_first_stop_not_overwritten(self):
        t=m.Tracker()
        for i in range(100):t.enter("fresh_read:other")
        self.assertEqual(len(t.history),8);g=Guard();t.stop(ValueError(),g);first=t.first_stop;t.enter("outside_io");t.stop(RuntimeError(),g)
        self.assertIs(t.first_stop,first)
    def test_kind_does_not_record_file_paths_or_private_names(self):
        for name,kind in (("target/a.exe","binary"),("tools/p09/a.py","helper_code"),("implementation/private/secret.json","evidence"),("x","other")):
            self.assertEqual(m.kind(name),kind)
    def test_final_hash_guard_stop_marks_exact_phase_and_no_completed_finish(self):
        _,new,t,*_=make();g=new.Guard();g.error=ValueError("STOP");r=new.AcceptanceReader("root",g.check)
        with self.assertRaises(ValueError):r.finish()
        self.assertEqual(t.first_stop["stage"],"final_hash:rust_source");self.assertEqual(t.finish_completed,0)
    def test_private_runner_projection_and_original_writer_delegated_once(self):
        calls=[];tracker=m.Tracker()
        def publish(path,name,row):calls.append((path,name,row));return "original_pin"
        def projection(*args,**kwargs):return make()[-2],"state"
        def run(*args,**kwargs):return "run"
        acceptance=NS(prior=NS(publish=publish),projection=projection,run=run)
        fanout=NS(prior=acceptance,run=run)
        bound=m.connect_fanout(fanout,tracker);private=bound.__globals__["prior"]
        self.assertIs(bound.__code__,run.__code__);self.assertIs(private.run.__code__,run.__code__)
        fn,state=private.projection();self.assertEqual(state,"state");self.assertIs(fn.__code__,fake_execute.__code__)
        row=dict(cleanup_confirmed=True)
        writer=private.run.__globals__["prior"].publish
        self.assertEqual(writer("same_path","same_name",row),"original_pin")
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][:2],("same_path","same_name"))
        self.assertEqual(row,dict(cleanup_confirmed=True));self.assertEqual(calls[0][2]["acceptance_stage_diagnostics"],tracker.summary())
        self.assertIs(acceptance.prior.publish,publish);self.assertIs(fanout.prior,acceptance)

if __name__=="__main__":unittest.main()
