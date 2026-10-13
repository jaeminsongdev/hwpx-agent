from types import FunctionType,SimpleNamespace as NS
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case158_attempt_v3 as m
import reviewed_runtime_attempt_v2 as retry


def leaf_template():
    def run(n):return n
    engine=NS(run_owned=run,worker=lambda task:task)
    return RETRY.connect_engine(engine,158)[0],{}

def step16():return OLD15.template()
def step17():return OLD16.template()
def step18():return OLD17.template()


def graph():
    a=NS(RETRY=retry);a.template=FunctionType(leaf_template.__code__,dict(RETRY=retry,NS=NS))
    b=NS(OLD15=a);b.template=FunctionType(step16.__code__,dict(OLD15=a))
    c=NS(OLD16=b);c.template=FunctionType(step17.__code__,dict(OLD16=b))
    d=NS(OLD17=c);d.template=FunctionType(step18.__code__,dict(OLD17=c))
    return d


class Tests(unittest.TestCase):
    def test_original_single_adapter_really_passes2_to_unmodified_engine(self):
        original=graph();fn,proof=m.connect_template(original);engine,_=fn()
        self.assertEqual(engine.run_owned(1),2)
        self.assertEqual(proof["physical_product_run"],2)
        with self.assertRaises(ValueError):engine.run_owned(1)
    def test_original_default_template_still_passes1(self):
        original=graph();m.connect_template(original)
        engine,_=original.template();self.assertEqual(engine.run_owned(1),1)
        self.assertEqual(original.OLD17.OLD16.OLD15.RETRY.physical_run(158),1)
    def test_every_template_code_and_old_namespace_identity_kept(self):
        original=graph();before=original.OLD17;fn,_=m.connect_template(original)
        self.assertIs(fn.__code__,original.template.__code__)
        self.assertIs(original.OLD17,before)
        self.assertIs(fn.__globals__["OLD17"].template.__code__,before.template.__code__)
    def test_explicit_paths_and_task_separate_failed_attempt(self):
        self.assertTrue(m.ROOT.endswith("run002.v1.json"));self.assertEqual(m.TASK,"case158-current-r002-tests")
        self.assertIn("run001",m.FAILED)
    def test_clone_keeps_defaults_keyword_defaults_and_closure(self):
        token=object()
        def f(x=token,*,y=token):return x,y
        new=m.clone(f,extra=1)
        self.assertIs(new.__defaults__,f.__defaults__);self.assertIs(new.__kwdefaults__,f.__kwdefaults__)
        self.assertEqual(new(),(token,token))
    def test_worker_connector_uses2_without_mutating_original_global_task(self):
        def connector(original,policy):
            def execute(task):
                if task!=TASK:raise ValueError("TASK_MISMATCH")
                return original(task)
            return execute,{}
        fn=FunctionType(connector.__code__,dict(TASK="case158-current-r001-tests"))
        execute,_=m.connect_worker(fn,lambda task:task,object())
        self.assertEqual(execute(m.TASK),m.TASK)
        self.assertEqual(fn.__globals__["TASK"],"case158-current-r001-tests")
    def test_invalid_template_interface_is_not_promoted(self):
        with self.assertRaises(AttributeError):m.connect_template(NS())


if __name__=="__main__":unittest.main()
