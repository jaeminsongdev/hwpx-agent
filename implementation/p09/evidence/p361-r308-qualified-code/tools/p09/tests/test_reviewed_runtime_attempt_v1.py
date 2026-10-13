import sys,unittest
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_runtime_attempt_v1 as m

class Tests(unittest.TestCase):
    def test_explicit_physical_path_task_and_no_successful_replay(self):
        self.assertEqual(m.public_run(153,2),1)
        self.assertTrue(m.root_path(NS(index=153)).endswith("case153-current-runtime-run002.v1.json"))
        self.assertEqual(m.task(153),"case153-current-r002-tests")
        for index,run in ((152,1),(153,1),(153,3),(153,True),(250,1)):
            with self.assertRaises(ValueError):m.public_run(index,run)
        self.assertEqual(m.public_run(154,1),1)
        self.assertEqual(m.task(154),"case154-current-r001-tests")

    def test_real_engine_argument_two_same_binding_environment_and_worker(self):
        seen=[]
        def original(run):
            seen.append((run,binding(None)))
            return 7
        def worker(task):return task
        env=dict(binding=lambda q:"stale")
        fn=FunctionType(original.__code__,env,closure=original.__closure__)
        engine=NS(run_owned=fn,worker=worker,unchanged=object())
        connected,state,proof=m.connect_engine(engine,153)
        # Same mutation made by the complete original outer entry, after template().
        connected.run_owned.__globals__["binding"]=lambda q:"complete-original-binding"
        self.assertEqual(connected.run_owned(1),7)
        self.assertEqual(seen,[(2,"complete-original-binding")])
        self.assertIs(connected.worker,worker)
        self.assertIs(fn.__code__,state.original_engine_code)
        self.assertEqual(state.actual_engine_calls,1)
        self.assertTrue(proof["original_private_binding_environment_shared"])
        with self.assertRaises(ValueError):connected.run_owned(1)

    def test_engine_error_propagated_and_not_retried(self):
        def failure(run):raise OSError("ERROR_NOT_PRODUCT")
        engine=NS(run_owned=failure,worker=lambda task:0)
        connected,state,_=m.connect_engine(engine,153)
        with self.assertRaises(OSError):connected.run_owned(1)
        self.assertEqual(state.actual_engine_calls,1)
        with self.assertRaises(ValueError):connected.run_owned(1)
        with self.assertRaises(ValueError):connected.run_owned(2)

    def test_later_case_physical_one_and_all_other_dependencies_retained(self):
        def original(run):return run
        engine=NS(run_owned=original,worker=lambda task:0,marker=object())
        connected,state,_=m.connect_engine(engine,154)
        self.assertIs(connected.marker,engine.marker)
        self.assertEqual(connected.run_owned(1),1)
        self.assertEqual(state.physical_product_run,1)

    def test_failure_requires_exact_stop_review_handles_and_no_body(self):
        import copy
        row=dict(state="DEFERRED_NOT_STARTED",stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
          selected_test_index=153,product_body_observed=False,Native_source_frame_qualified=False,
          cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0,
          source_frame=dict(handles=dict(input_lock_handles_opened=1329,input_lock_handles_closed=1329,
          input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True)))
        review=dict(state="DEFERRED_NOT_STARTED",stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
          product_body=False,cleanup=True,owned_tree_empty=True,accepted_count_delta=0,
          original_current153_receipt_unchanged=True)
        def fields(obj,expected,code):
            for k,v in expected.items():
                if type(obj.get(k)) is not type(v) or obj[k]!=v:raise ValueError(code)
        def read(q,pin):
            self.assertIn(pin,(m.STOPPED,m.REVIEW))
            return row if pin is m.STOPPED else review
        before=copy.deepcopy(row)
        self.assertEqual(m.reviewed_failure(None,read,fields),(m.STOPPED,m.REVIEW))
        self.assertEqual(row,before)
        for key,value in (("product_body_observed",True),("cleanup_confirmed",False),("accepted_count_delta",1)):
            old=row[key];row[key]=value
            with self.assertRaises(ValueError):m.reviewed_failure(None,read,fields)
            row[key]=old
        row["source_frame"]["handles"]["input_lock_handles_remaining"]=1
        with self.assertRaises(ValueError):m.reviewed_failure(None,read,fields)

    def test_actual_identity_not_path_only_or_task_relabelling(self):
        step=NS(index=153);pin=dict(path=m.root_path(step))
        row=dict(selected_test_index=153,task=m.task(153))
        self.assertFalse(m.validate_actual(row,step,pin)["full_product_oracle_replaced"])
        with self.assertRaises(ValueError):m.validate_actual(dict(row,task="case153-current-r001-tests"),step,pin)
        with self.assertRaises(ValueError):m.validate_actual(row,step,m.STOPPED)
        with self.assertRaises(ValueError):m.validate_actual(dict(row,selected_test_index=True),step,pin)

if __name__=="__main__":unittest.main()
