"""All original capsule6 tests plus run002 task/schema checks."""
import ast
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_worker_capsule_v3 as m
import runtime_successor_binding_v2 as successor
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_worker_connection_v1 as original
from test_runtime_successor_binding_v1 import lineage
from test_runtime_failed_receipt_projection_v1 import graph
import hashlib
import json

path=Path(__file__).with_name("test_runtime_successor_worker_capsule_v2.py")
tree=ast.parse(path.read_text(encoding="utf-8"))
nodes=copy.deepcopy([n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))])
if [ast.dump(n,include_attributes=False) for n in nodes]!=[ast.dump(n,include_attributes=False)
    for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]:
    raise ValueError("ALL_ORIGINAL_CAPSULE_TEST_AST")
env=dict(Path=Path,sys=sys,unittest=unittest,m=m,successor=successor,first=first,second=second,
    original=original,lineage=lineage,graph=graph,hashlib=hashlib,json=json,
    __name__="p09_exact_capsule_tests",__file__=str(path))
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),"exec"),env)
class Tests(env["Tests"]):
    def test_exact_run002_task_not_old_run001(self):
        api,_,_=self.setup_api()
        self.assertEqual(api.TASK,"case160-current-r002-tests")
        self.assertEqual(m.original.TASK,"case160-current-r001-tests")
    def test_new_closed_schema_is_explicit(self):
        api,binding,_=self.setup_api()
        raw,_=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        self.assertEqual(json.loads(raw)["schema_version"],m.SCHEMA)
        self.assertEqual(m.SCHEMA,"hwpx-agent.p09-envelope-worker-policy-capsule/v4")
