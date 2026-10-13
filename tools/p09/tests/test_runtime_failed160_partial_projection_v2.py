"""Original partial role6 tests plus attribute-name regression."""
import ast
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_failed160_partial_projection_v2 as m
path=Path(__file__).with_name("test_runtime_failed160_partial_projection_v1.py")
tree=ast.parse(path.read_text(encoding="utf-8"))
nodes=copy.deepcopy([n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))])
if [ast.dump(n,include_attributes=False) for n in nodes]!=[ast.dump(n,include_attributes=False)
    for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]:
    raise ValueError("ALL_ORIGINAL_PARTIAL_ROLE_TEST_AST")
env=dict(Path=Path,sys=sys,unittest=unittest,m=m,__name__="p09_exact_role_tests",__file__=str(path))
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),"exec"),env)
class Tests(env["Tests"]):
    def test_attribute_and_constant_names_both_projected_and_reversible(self):
        code=m.original.connect.__code__;revised=m.project(code,m.MAPPING)
        self.assertNotIn("failed004_receipt_extension",revised.co_names)
        self.assertIn("failed160_partial_receipt_extension",revised.co_names)
        self.assertEqual(m.project(revised,{v:k for k,v in m.MAPPING.items()}),code)
