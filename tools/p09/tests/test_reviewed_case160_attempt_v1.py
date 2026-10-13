"""All original identity8 tests, metadata inverse, plus run002 tests4."""
import ast
import copy
import hashlib
from pathlib import Path
import sys
from types import CodeType,FunctionType,SimpleNamespace as NS
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewed_case160_attempt_v1 as m
import reviewed_runtime_attempt_v2 as original

PIN={"sha256":"06f61dddea188cc9a25be41b3015bd840e1c681361fc283526055faba10e3661","bytes":2663,"path":"tools/p09/tests/test_reviewed_case158_attempt_v4.py"}
root=Path(__file__).resolve().parents[3]
raw=(root/PIN["path"]).read_bytes()
if len(raw)!=PIN["bytes"] or hashlib.sha256(raw).hexdigest()!=PIN["sha256"]:
    raise ValueError("EXACT_ORIGINAL_IDENTITY_TEST_SOURCE")
tree=ast.parse(raw.decode("utf-8"))
nodes=copy.deepcopy([n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))])
if [ast.dump(n,include_attributes=False) for n in nodes]!=[ast.dump(n,include_attributes=False)
    for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]:
    raise ValueError("ALL_ORIGINAL_IDENTITY_TEST_AST")
env=dict(Path=Path,sys=sys,NS=NS,unittest=unittest,m=m,original=original,
    __name__="p09_exact_identity_tests",__file__=PIN["path"])
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),PIN["path"],"exec"),env)
mapping={158:160,"case158-current-r001-tests":"case160-current-r001-tests"}
def changed(code,values):
    return code.replace(co_consts=tuple(changed(x,values) if type(x) is CodeType else
        values.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
for name,fn in tuple(vars(env["Tests"]).items()):
    if type(fn) is FunctionType:
        code=changed(fn.__code__,mapping)
        if changed(code,{v:k for k,v in mapping.items()})!=fn.__code__:
            raise ValueError("ENTIRE_ORIGINAL_IDENTITY_TEST_METADATA_INVERSE")
        new=FunctionType(code,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
        new.__kwdefaults__=fn.__kwdefaults__;setattr(env["Tests"],name,new)

class Tests(env["Tests"]):
    def test_current160_root_task_and_public_run(self):
        names=m.identity(original)
        self.assertEqual(names.physical_run(160),2)
        self.assertEqual(names.root_path(NS(index=160)),m.ROOT)
        self.assertEqual(names.public_run(160,2),1)
    def test_original160_default_root_is_still_run001(self):
        m.identity(original)
        self.assertEqual(original.root_path(NS(index=160)),
            "implementation/p09/evidence/p09-361-case160-current-runtime-run001.v1.json")
    def test_failure_and_review_paths_are_not_prior_accepted_product(self):
        self.assertIn("case160-current-runtime-run001",m.STOPPED["path"])
        self.assertIn("stop-review",m.REVIEW)
        self.assertNotEqual(m.ROOT,m.STOPPED["path"])
    def test_worker_connector_only_changes_task_dependency(self):
        def connector(worker,policy):return TASK,worker,policy
        worker=object();policy=object()
        task,w,p=m.connect_worker(connector,worker,policy)
        self.assertEqual(task,m.TASK);self.assertIs(w,worker);self.assertIs(p,policy)
