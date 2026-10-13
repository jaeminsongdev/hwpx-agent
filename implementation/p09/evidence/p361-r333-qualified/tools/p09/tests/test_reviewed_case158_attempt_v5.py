from pathlib import Path
import sys
from types import FunctionType,SimpleNamespace as NS
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case158_attempt_v5 as m
import reviewed_runtime_attempt_v2 as retry


def leaf():
    def owned(n):return n
    return RETRY.connect_engine(NS(run_owned=owned,worker=lambda task:task),158)[0],{}
def step16():return OLD15.template()
def step17():return OLD16.template()
def step18():return OLD17.template()
def graph():
    a=NS(RETRY=retry);a.template=FunctionType(leaf.__code__,dict(RETRY=retry,NS=NS))
    b=NS(OLD15=a);b.template=FunctionType(step16.__code__,dict(OLD15=a))
    c=NS(OLD16=b);c.template=FunctionType(step17.__code__,dict(OLD16=b))
    d=NS(OLD17=c);d.template=FunctionType(step18.__code__,dict(OLD17=c))
    return d


class Tests(unittest.TestCase):
    def test_single_original_adapter_passes3_once_to_original_engine(self):
        fn,names,proof=m.connect_template(graph());engine,_=fn()
        self.assertEqual(engine.run_owned(1),3)
        self.assertEqual(proof["physical_product_run"],3)
        with self.assertRaises(ValueError):engine.run_owned(1)
    def test_original_default_template_and_namespace_unmodified(self):
        old=graph();m.connect_template(old);engine,_=old.template()
        self.assertEqual(engine.run_owned(1),1)
        self.assertEqual(old.OLD17.OLD16.OLD15.RETRY.physical_run(158),1)
    def test_whole_original_root_task_public_and_checker_code_retained(self):
        new=m.identity(retry)
        for name in ("root_path","task","public_run","validate_actual"):
            self.assertIs(getattr(new,name).__code__,getattr(retry,name).__code__)
    def test_physical_run001_002_boolean_or_other_run_rejected(self):
        new=m.identity(retry)
        for value in (1,2,True,4):
            with self.assertRaises(ValueError):new.public_run(158,value)
        self.assertEqual(new.public_run(158,3),1)
    def test_historical_attempts_stay_exact(self):
        new=m.identity(retry)
        for index in (153,154,155,157,159,249):
            self.assertEqual(new.physical_run(index),retry.physical_run(index))
            self.assertEqual(new.task(index),retry.task(index))
    def test_actual_row_with_run002_task_is_not_relabelled(self):
        row=dict(selected_test_index=158,task="case158-current-r002-tests");before=dict(row)
        with self.assertRaises(ValueError):m.identity(retry).validate_actual(row,NS(index=158),dict(path=m.ROOT))
        self.assertEqual(row,before)
    def test_worker_connector_task3_private_global_preserves_original_task(self):
        def connector(fn,p):
            def execute(task):
                if task!=TASK:raise ValueError("WRONG_TASK")
                return fn(task)
            return execute,{}
        original=FunctionType(connector.__code__,dict(TASK="case158-current-r001-tests"))
        execute,_=m.connect_worker(original,lambda task:task,None)
        self.assertEqual(execute(m.TASK),m.TASK)
        self.assertEqual(original.__globals__["TASK"],"case158-current-r001-tests")
    def test_stop002_with_observed_worker_cannot_qualify_new_attempt(self):
        class A:
            @staticmethod
            def read_exact(q,p):return dict(state="DEFERRED_NOT_STARTED",worker_created=True)
            @staticmethod
            def fields(row,expected,label):
                for key,value in expected.items():
                    if row.get(key)!=value:raise ValueError(label)
        with patch.object(m.original.prior,"reviewed_failure",return_value={}):
            with self.assertRaises(ValueError):m.reviewed_failure(None,A,dict(path=m.REVIEW_PATH))


if __name__=="__main__":unittest.main()
