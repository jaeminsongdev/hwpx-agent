import sys,unittest,copy
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_runtime_attempt_v2 as m

class Tests(unittest.TestCase):
    def test_physical154_two_prior153_two_later_one_no_implicit_retry(self):
        self.assertEqual(m.public_run(154,2),1)
        self.assertEqual(m.physical_run(153),2);self.assertEqual(m.physical_run(155),1)
        for i,r in ((154,1),(154,3),(154,True),(152,1),(250,1)):
            with self.assertRaises(ValueError):m.public_run(i,r)
        self.assertTrue(m.root_path(NS(index=154)).endswith("case154-current-runtime-run002.v1.json"))
        self.assertEqual(m.task(154),"case154-current-r002-tests")

    def test_entire_prior_code_defaults_closures_unchanged(self):
        for name in ("root_path","task","public_run","connect_engine","validate_actual"):
            a=getattr(m,name);b=getattr(m.prior,name)
            self.assertIs(a.__code__,b.__code__);self.assertIs(a.__defaults__,b.__defaults__)
            self.assertIs(a.__closure__,b.__closure__)
        self.assertEqual(m.prior.physical_run(154),1)

    def test_real_engine_physical_two_same_private_binding_no_retry(self):
        seen=[]
        def actual(run):seen.append((run,binding(None)));return 0
        fn=FunctionType(actual.__code__,dict(binding=lambda q:"stale"),closure=actual.__closure__)
        old=NS(run_owned=fn,worker=lambda task:task)
        e,state,_=m.connect_engine(old,154)
        e.run_owned.__globals__["binding"]=lambda q:"original-complete-binding"
        self.assertEqual(e.run_owned(1),0)
        self.assertEqual(seen,[(2,"original-complete-binding")])
        self.assertEqual(state.actual_engine_calls,1);self.assertIs(e.worker,old.worker)
        with self.assertRaises(ValueError):e.run_owned(1)

    def test_reviewed_failure_exact_pins_no_source_or_body_rebase(self):
        row=dict(state="DEFERRED_NOT_STARTED",task="case154-current-r001-tests",selected_test_index=154,
          stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",product_body_observed=False,
          worker_created=False,Native_source_frame_qualified=False,source_frame=None,cleanup_confirmed=True,
          owned_tree_empty=True,accepted_count_delta=0)
        review=dict(state="REVIEWED154_METADATA_CPU_WARNING_BEFORE_NATIVE_OR_PRODUCT",original_runtime_pin=m.NEW_STOPPED,
          original_runtime_preserved=True,stopped154_retried=False,accepted_count_delta=0,cleanup_confirmed=True)
        from unittest.mock import patch
        def fields(obj,expected,code):
            for k,v in expected.items():
                if type(obj.get(k)) is not type(v) or obj[k]!=v:raise ValueError(code)
        def read(q,pin):
            self.assertIn(pin,(m.NEW_STOPPED,m.NEW_REVIEW))
            return row if pin is m.NEW_STOPPED else review
        before=copy.deepcopy(row)
        with patch.object(m.prior,"reviewed_failure",return_value=(m.STOPPED,m.REVIEW)) as previous:
            self.assertEqual(m.reviewed_failure(None,read,fields),tuple(m.HISTORY))
            previous.assert_called_once()
            self.assertEqual(row,before)
            row["source_frame"]={}
            with self.assertRaises(ValueError):m.reviewed_failure(None,read,fields)

    def test_actual_task_and_root_identity_not_original_run001(self):
        row=dict(selected_test_index=154,task=m.task(154));s=NS(index=154);p=dict(path=m.root_path(s))
        self.assertEqual(m.validate_actual(row,s,p)["physical_product_run"],2)
        with self.assertRaises(ValueError):m.validate_actual(row,s,m.NEW_STOPPED)
        with self.assertRaises(ValueError):m.validate_actual(dict(row,task="case154-current-r001-tests"),s,p)

    def test_engine_errors_propagate_and_later155_not_second_attempt(self):
        def failed(run):raise OSError("ORIGINAL_ERROR")
        e,state,_=m.connect_engine(NS(run_owned=failed,worker=lambda task:0),154)
        with self.assertRaises(OSError):e.run_owned(1)
        self.assertEqual(state.actual_engine_calls,1)
        def one(run):return run
        e,state,_=m.connect_engine(NS(run_owned=one,worker=lambda task:0),155)
        self.assertEqual(e.run_owned(1),1);self.assertEqual(state.physical_product_run,1)

if __name__=="__main__":unittest.main()
