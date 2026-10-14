"""Closed private import map and unchanged function code."""
from pathlib import Path
import ast
from types import FunctionType,SimpleNamespace as NS
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_wire_runtime_v2 as m


class Tests(unittest.TestCase):
    def test_private_imports_keep_code_and_shared_builtins(self):
        def original():
            import explicit_fixture_dependency
            return explicit_fixture_dependency
        env=dict(original.__globals__,__name__="p09_exact_fixture")
        fn=FunctionType(original.__code__,env)
        namespace=NS(original=fn);value=object()
        import builtins
        before=builtins.__import__
        m.bind_imports(namespace,dict(explicit_fixture_dependency=value))
        self.assertIs(namespace.original.__code__,fn.__code__)
        self.assertIs(namespace.original(),value)
        self.assertIs(builtins.__import__,before)
        self.assertNotIn("explicit_fixture_dependency",sys.modules)
    def test_all_frozen_sources_declared_and_worker_entry_is_shared(self):
        self.assertEqual(len(m.PINS),5)
        self.assertTrue(any(p["path"].endswith("current_queue_successor_runtime.py") for p in m.PINS))
        self.assertTrue(any(p["path"].endswith("current_queue_successor_dispatch.py") for p in m.PINS))
        self.assertNotEqual(m.SELF,"tools/p09/current_queue_successor_runtime.py")
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        load=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="load")
        condition=next(n for n in load.body if isinstance(n,ast.If) and isinstance(n.test,ast.UnaryOp))
        self.assertEqual(ast.unparse(condition.test),"not worker")
        self.assertTrue(any(isinstance(n,ast.Name) and n.id=="OLD_CONTROLLER" for n in ast.walk(condition)))
        projector=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="graph_v2_paths")
        self.assertTrue(any(isinstance(n,ast.Constant) and n.value=="WHOLE_GRAPH_PATH_AST_INVERSE" for n in ast.walk(projector)))


if __name__=="__main__":unittest.main()
