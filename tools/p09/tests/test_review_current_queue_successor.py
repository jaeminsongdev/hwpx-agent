"""Whole prepare wrapper retains its code and never provides a queue writer."""
import ast
from pathlib import Path
import sys
from types import FunctionType,SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import review_current_queue_successor as m


class Tests(unittest.TestCase):
    def test_entire_frozen_prepare_code_and_dependencies_retained(self):
        def original(q,pin):return validate_candidate,root_path,r,q,pin
        env=dict(original.__globals__,r=NS(CONFIG=None,context=None))
        original=FunctionType(original.__code__,env)
        legacy=NS(source=NS(prepare_projection=lambda raw:original))
        checker=NS(validate_candidate=object(),environment=dict(context=object()))
        identity=NS(root_path=object());step=object()
        fn=m.connect_prepare(legacy,checker,identity,step,b"source")
        self.assertIs(fn.__code__,original.__code__)
        self.assertIs(fn.__defaults__,original.__defaults__)
        self.assertIs(fn.__closure__,original.__closure__)
        self.assertIs(fn.__globals__["r"].CONFIG,step)
        self.assertIs(fn.__globals__["root_path"],identity.root_path)
        self.assertIs(fn.__globals__["validate_candidate"],checker.validate_candidate)
    def test_prepare_scope_precedes_candidate_and_no_execution_or_acceptance(self):
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="prepare")
        calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ("run_owned","worker","accept","execute") for n in calls))
        scope_call=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=="current_input_scope")
        candidate=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=="execute")
        self.assertLess(scope_call.lineno,candidate.lineno)
        self.assertTrue(any(isinstance(n.func,ast.Attribute) and n.func.attr=="previous_stops" for n in calls))


if __name__=="__main__":unittest.main()
