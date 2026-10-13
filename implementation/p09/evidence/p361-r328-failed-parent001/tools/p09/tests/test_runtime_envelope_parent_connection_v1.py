import copy
import io
import json
from pathlib import Path
import sys
from types import FunctionType,SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_envelope_parent_connection_v1 as m
import runtime_input_frame as original_frames
from test_runtime_envelope_frame_connection_v1 import setup as frame_fixture


def make_engine(mode="normal",checkpoint=lambda:None):
    fixture,held,factory,made,binding,semantic=frame_fixture()
    class QualifiedFixtureHeld(type(held)):
        def summary(self):
            n=len(self.rows);closed=not self.open
            return dict(input_lock_handles_remaining=0 if closed else n,
                input_lock_handles_opened=n,input_lock_handles_closed=n if closed else 0,
                handle_close_failed_attempts=0,byte_stream_identity_checks=2*n,
                active_reader_bindings=len(self.active_readers),active_byte_streams=0,
                maximum_lock_seconds=600,input_lock_cleanup_confirmed=closed)
    held=QualifiedFixtureHeld();seen=[];reader=NS(checkpoint=checkpoint)
    def bootstrap(q):seen.append(q);return copy.deepcopy(semantic),{"crates/product-cli/src/current.rs"}
    def budget(rows,requests):
        seen.append((rows,requests))
        return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
            predicted_runtime_combined_seconds=580.0)
    def body(run):
        required,rust=binding_call(reader)
        cost=runtime_budget(required,167)
        if mode=="before_frame_error":raise original_error
        frame=native.frames.Frame(native.frames.Registry(),required,checkpoint,held=held)
        try:
            frame.acquire()
            if mode=="raw_error":
                (Path.cwd()/next(iter(policy_binding.originals))).open("rb")
            frame.read_boundary(factory,checkpoint);frame.read_boundary(factory,checkpoint)
            if mode=="closed_false_claim":frame.close()
            else:frame.commit(dict(cleanup_confirmed=True,owned_tree_empty=True,
                job_final=dict(active_processes=0,owned_processes=[])))
            row=dict(source_freeze=[dict(p) for p in frame.inputs.values()],source_frame=frame.summary(),
                current_generation_runtime_candidate_qualified=True,complete_runtime_budget=cost)
            json.dump(row,io.StringIO())
            return row
        finally:frame.close()
    # bind the frozen test function's global dependency name to the interface
    # used by the real original engine (rather than fixture-only binding_call).
    code=body.__code__.replace(co_names=tuple("binding" if n=="binding_call" else n for n in body.__code__.co_names))
    error=OSError("ORIGINAL_ENGINE_FAILURE")
    env=dict(body.__globals__,binding=bootstrap,runtime_budget=budget,
        native=NS(frames=original_frames),c=NS(ROOT=Path.cwd()),original_error=error,
        policy_binding=binding)
    # Test closures retain the original fixture objects; the component must not
    # rewrite observed counters or row content to satisfy its oracle.
    worker=lambda task:2
    function=FunctionType(code,env,argdefs=body.__defaults__,closure=body.__closure__)
    engine=NS(run_owned=function,worker=worker)
    return engine,binding,semantic,held,made,seen,error


class Tests(unittest.TestCase):
    def test_full_original_fixture_engine_two_boundaries_commit_and_explicit_row(self):
        engine,binding,semantic,held,made,seen,error=make_engine()
        connected,state=m.connect_engine(engine,binding);row=connected.run_owned(1)
        self.assertEqual(row["source_frame"]["frame_state"],"COMMITTED")
        self.assertEqual(row["complete_runtime_budget"]["predicted_runtime_combined_seconds"],585.0)
        self.assertEqual(row["source_input_representation"]["semantic_source_freeze"],
            binding.representation(state.frames[0].explicit_projection)["semantic_source_freeze"])
        self.assertEqual(len(made),2);self.assertTrue(state.frames[0].raw_policy.restored)
        self.assertEqual(state.bootstrap_calls,state.budget_calls);self.assertEqual(state.dump_calls,1)

    def test_private_environment_and_original_worker_identity_preserved(self):
        engine,binding,*_=make_engine();before=dict(engine.run_owned.__globals__)
        connected,state=m.connect_engine(engine,binding)
        self.assertIs(connected.worker,engine.worker)
        self.assertIs(connected.run_owned.__globals__,engine.run_owned.__globals__)
        connected.run_owned(1)
        for name,value in before.items():self.assertIs(engine.run_owned.__globals__[name],value)
        self.assertIs(state.original,engine.run_owned)

    def test_bootstrap_keeps_every_original_pin_budget_and_frame_project_same_scope(self):
        engine,binding,semantic,held,made,seen,error=make_engine()
        connected,state=m.connect_engine(engine,binding);connected.run_owned(1)
        budget_inputs,requests=seen[1]
        self.assertEqual(budget_inputs,{n:dict(p) for n,p in state.frames[0].inputs.items()})
        self.assertEqual(dict(state.frames[0].semantic_inputs),semantic);self.assertEqual(requests,167)

    def test_original_error_before_frame_retained_and_globals_restored(self):
        engine,binding,_,_,_,_,error=make_engine("before_frame_error")
        before=dict(engine.run_owned.__globals__);connected,state=m.connect_engine(engine,binding)
        with self.assertRaises(OSError) as caught:connected.run_owned(1)
        self.assertIs(caught.exception,error);self.assertEqual(state.frames,[])
        for name,value in before.items():self.assertIs(engine.run_owned.__globals__[name],value)

    def test_live_raw_attempt_rejected_then_original_close_and_policy_restore(self):
        engine,binding,*_=make_engine("raw_error");connected,state=m.connect_engine(engine,binding)
        with self.assertRaisesRegex(ValueError,"STOP_LIVE_RAW"):connected.run_owned(1)
        self.assertEqual(state.frames[0].raw_policy.raw_attempts,1)
        self.assertTrue(state.frames[0].raw_policy.restored)
        self.assertEqual(state.frames[0].summary()["frame_state"],"CLOSED")

    def test_closed_frame_false_candidate_claim_rejected(self):
        engine,binding,*_=make_engine("closed_false_claim");connected,state=m.connect_engine(engine,binding)
        with self.assertRaisesRegex(ValueError,"EXACT_TERMINAL_FRAME_NOT_PROMOTION"):connected.run_owned(1)
        self.assertTrue(state.frames[0].raw_policy.restored)

    def test_wrong_run_and_second_call_rejected_without_replaying_body(self):
        engine,binding,*_=make_engine();connected,state=m.connect_engine(engine,binding)
        for run in (True,2):
            with self.assertRaises(ValueError):connected.run_owned(run)
        self.assertEqual(state.attempts,0);connected.run_owned(1)
        with self.assertRaises(ValueError):connected.run_owned(1)
        self.assertEqual(state.attempts,1)

    def test_existing_guard_error_preserved_before_any_frame_or_product(self):
        error=ValueError("ORIGINAL_CPU_STOP")
        def stop():raise error
        engine,binding,*_=make_engine(checkpoint=stop);connected,state=m.connect_engine(engine,binding)
        with self.assertRaises(ValueError) as caught:connected.run_owned(1)
        self.assertIs(caught.exception,error);self.assertEqual(state.frames,[])

    def test_component_evidence_never_qualifies_whole158_or_GO(self):
        engine,binding,*_=make_engine();connected,state=m.connect_engine(engine,binding)
        connected.run_owned(1);proof=m.evidence(state)
        self.assertFalse(proof["full_current158_parent_worker_or_oracle_qualified"])
        self.assertFalse(proof["GO_authorized"])


if __name__=="__main__":unittest.main()
