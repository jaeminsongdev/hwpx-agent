"""Generic identity projection with the unchanged original template chain."""
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
sys.path.insert(0,str(Path(__file__).parent))
import current_queue_successor_runtime as m
import runtime_envelope_namespace_bundle_v1 as loader

ROOT=Path(__file__).parents[3]


def physical_run(index):return 1
def root_path(step):return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{physical_run(step.index):03}.v1.json"
def task(index):return f"case{index}-current-r{physical_run(index):03}-tests"
def public_run(index,run):
    if type(run) is not int or run!=physical_run(index):raise ValueError("EXACT_PHYSICAL_RUN")
    return 1


def fixture_window():
    def validate_actual(*args):return None
    def connect_engine(*args):return None
    retry=NS(physical_run=physical_run,root_path=root_path,task=task,public_run=public_run,
        validate_actual=validate_actual,connect_engine=connect_engine)
    # Original fixture functions resolve the same private physical dependency,
    # just as the qualified engine adapter does.
    from types import FunctionType
    env=dict(root_path.__globals__,physical_run=physical_run)
    retry.root_path=FunctionType(root_path.__code__,env)
    retry.task=FunctionType(task.__code__,env)
    retry.public_run=FunctionType(public_run.__code__,env)
    def level15():return RETRY
    def level16():return OLD15.template()
    def level17():return OLD16.template()
    def window18():return OLD17.template()
    old15=NS(RETRY=retry,template=FunctionType(level15.__code__,dict(RETRY=retry)))
    old16=NS(OLD15=old15,template=FunctionType(level16.__code__,dict(OLD15=old15)))
    old17=NS(OLD16=old16,template=FunctionType(level17.__code__,dict(OLD16=old16)))
    window=NS(OLD17=old17,template=FunctionType(window18.__code__,dict(OLD17=old17)))
    return window,retry


class Tests(unittest.TestCase):
    def parent_fixture(self):
        from test_current_queue_successor_connections import Tests as GraphTests
        graph,unused,state,semantic,held,engine=GraphTests().connected_parent_fixture()
        engine.run_owned.__globals__.update(SELF="fixture-source",TEST="fixture-test")
        return graph,engine,semantic,held

    def test_current_parent_composition_preserves_body_and_two_reads(self):
        graph,engine,semantic,held=self.parent_fixture();body=engine.run_owned;worker=engine.worker
        def binding(q):return semantic,{"crates/product-cli/src/current.rs"}
        connected,state,proof=m.compose_parent(lambda:(engine,{}),graph,binding,lambda:None)
        row=connected.run_owned(1)
        self.assertIs(state.original,body);self.assertIs(connected.worker,worker)
        self.assertEqual(len(row["source_frame"]["actual_byte_boundaries"]),2)
        self.assertEqual(row["source_input_representation"]["next_case"],161)
        self.assertFalse(held.open);self.assertTrue(state.frames[0].raw_policy.restored)
        self.assertFalse(proof["actual_parent_Native_product_or_GO_qualified"])

    def test_current_worker_connector_is_once_only_and_rejects_other_task(self):
        graph,engine,semantic,held=self.parent_fixture();worker=engine.worker
        execute,state,policy,proof=m.compose_worker(lambda:(engine,{}),graph,ROOT,lambda:None)
        with self.assertRaises(ValueError):execute("case162-current-r001-tests")
        self.assertEqual(state.attempts,0)
        self.assertEqual(execute(graph.worker.TASK),2)
        with self.assertRaises(ValueError):execute(graph.worker.TASK)
        self.assertIs(state.original,worker);self.assertTrue(policy.restored)

    def test_parent_admission_rejects_wrong_case_before_receipt_IO(self):
        graph,engine,semantic,held=self.parent_fixture()
        class Reader:
            checkpoint=staticmethod(lambda:None)
            def pin(self,*args):raise AssertionError("UNEXPECTED_RECEIPT_IO")
        with self.assertRaises(ValueError):m.current_input_scope(Reader(),graph,dict(index=162),{},{},{})

    def test_contexts_and_single_adapter_are_exact(self):
        for index,run in ((161,2),(161,8),(165,3),(249,8)):
            window,retry=fixture_window();before=window.template.__globals__.copy()
            template,names,proof=m.connect_factory(ROOT,loader,window,index,run,lambda:None)
            self.assertEqual(names.task(index),f"case{index}-current-r{run:03}-tests")
            self.assertEqual(names.public_run(index,run),1)
            self.assertEqual(template().physical_run(index),run)
            self.assertEqual(retry.physical_run(index),1)
            self.assertEqual(window.template.__globals__,before)
            self.assertTrue(proof["original_single_argument_adapter_not_stacked"])
            self.assertFalse(proof["actual_Native_product_or_GO_qualified"])

    def test_invalid_contexts_rejected(self):
        window,_=fixture_window()
        for index,run in ((True,2),(160,2),(250,2),(161,True),(161,1),(161,9),(161,"2")):
            with self.assertRaises(ValueError):m.connect_factory(ROOT,loader,window,index,run,lambda:None)

    def test_original_guard_failure_identity_retained(self):
        window,_=fixture_window();error=ValueError("ORIGINAL_GUARD_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:m.connect_factory(ROOT,loader,window,161,2,stop)
        self.assertIs(caught.exception,error)


if __name__=="__main__":unittest.main()
