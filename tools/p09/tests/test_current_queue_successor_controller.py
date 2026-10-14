"""Closed controller selections and explicit non-runtime CODE boundaries."""
import ast
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_controller as m


class Tests(unittest.TestCase):
    def test_preflight_preserves_inventory_original_contracts_and_no_run(self):
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_preflight")
        calls=[n for n in ast.walk(function) if isinstance(n,ast.Call)]
        self.assertEqual(sum(isinstance(n.func,ast.Attribute) and n.func.attr=="finish" for n in calls),1)
        self.assertTrue(any(isinstance(n.func,ast.Attribute) and n.func.attr=="rust_inputs" for n in calls))
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ("run_owned","worker","accept") for n in calls))
        self.assertTrue(any(isinstance(n,ast.Constant) and n.value=="ALL_ORIGINAL_PREFLIGHT_CONTRACT10" for n in ast.walk(function)))

    def test_modes_and_attempts_are_closed_and_separate(self):
        self.assertNotEqual(m.destination(161,2,"code",1),m.destination(161,2,"preflight",1))
        self.assertNotEqual(m.destination(161,2,"code",1),m.destination(161,2,"code",2))
        for values in ((True,2,"code",1),(160,2,"code",1),(250,2,"code",1),(161,1,"code",1),
                       (161,2,"native",1),(161,2,"code",True),(161,2,"code",9)):
            with self.assertRaises(ValueError):m.destination(*values)

    def test_code_has_one_terminal_finish_and_no_runtime_call(self):
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_code")
        calls=[n for n in ast.walk(function) if isinstance(n,ast.Call)]
        self.assertEqual(sum(isinstance(n.func,ast.Attribute) and n.func.attr=="finish" for n in calls),1)
        self.assertFalse(any(isinstance(n.func,ast.Attribute) and n.func.attr in ("run_owned","worker","accept") for n in calls))

    def test_source_inventory_retains_visible_controller_module(self):
        names=m.imported_sources(Path(__file__).parents[3])
        self.assertIn(m.SELF,names)


if __name__=="__main__":unittest.main()
