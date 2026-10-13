"""Retain the original six capsule contracts and test the v5 wire dependency."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_successor_worker_capsule_v5 as m
import runtime_successor_binding_v2 as successor
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_worker_connection_v1 as original
from test_runtime_successor_binding_v1 import lineage
from test_runtime_failed_receipt_projection_v1 import graph

path=Path(__file__).with_name("test_runtime_successor_worker_capsule_v2.py")
tree=ast.parse(path.read_text(encoding="utf-8"))
selected=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
nodes=copy.deepcopy(selected)
if [ast.dump(n,include_attributes=False) for n in nodes]!=[ast.dump(n,include_attributes=False) for n in selected]:
    raise ValueError("ALL_ORIGINAL_CAPSULE_TEST_AST")
env=dict(Path=Path,sys=sys,unittest=unittest,m=m,successor=successor,first=first,second=second,
    original=original,lineage=lineage,graph=graph,hashlib=hashlib,json=json,
    __name__="p09_exact_capsule_v5_tests",__file__=str(path))
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(path),"exec"),env)

class Tests(env["Tests"]):
    def test_actual_test_dependency_exists(self):
        self.assertEqual(m.TEST,"tools/p09/tests/test_runtime_successor_worker_capsule_v5.py")
        self.assertTrue(Path(__file__).resolve().parents[3].joinpath(m.TEST).is_file())

    def test_v5_schema_and_same_run002_task(self):
        api,binding,_=self.setup_api()
        raw,_=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        self.assertEqual(json.loads(raw)["schema_version"],"hwpx-agent.p09-envelope-worker-policy-capsule/v6")
        self.assertEqual(api.TASK,"case160-current-r003-tests")
        self.assertEqual(m.original.SCHEMA,"hwpx-agent.p09-envelope-worker-policy-capsule/v5")

    def test_old_wire_schema_rejected_with_valid_transport_hash(self):
        api,binding,_=self.setup_api()
        data,_=api.encode(binding,successor.AUTHORITY,successor.ROOT,lambda:None)
        row=dict(json.loads(data),schema_version=m.original.SCHEMA)
        raw=json.dumps(row).encode("ascii")
        with self.assertRaises(ValueError):
            api.decode(raw,dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),lambda:None)

if __name__=="__main__":unittest.main()
