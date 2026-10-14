"""Execution entry must reject stale or non-product preparation evidence."""
from pathlib import Path
from types import SimpleNamespace as NS
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_dispatch as m


def exact(actual,expected,label):
    if actual!=expected:raise ValueError(label)
def fields(row,values,label):
    for k,v in values.items():exact(row.get(k),v,label)
def require(value,label):
    if not value:raise ValueError(label)
A=NS(exact=exact,fields=fields,require=require)


def fixture():
    ctx=m.context(161,2,8,7,1)
    pin=lambda name:dict(path=name,bytes=1,sha256="a"*64)
    code=dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",index=161,physical_run=2,
        contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True,accepted_count_delta=0,
        GO_authorized=False,product_or_Native_executed=False,fresh_inputs=1,final_fresh_hashes=1,
        runtime_default_import_count=63,source_pins=[pin("source")])
    pref=dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
        index=161,physical_run=2,original_preflight_contracts=10,Rust_inputs=787,cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_worker_or_Native_frame_executed=False,
        independent_oracle_connected=True,fresh_inputs=1,final_fresh_hashes=1,runtime_default_imports=64,
        code_pin=pin(ctx.code),current_source_pins=[pin("source")])
    rows={ctx.code:code,ctx.preflight:pref}
    snapshots={ctx.code:pin(ctx.code),ctx.preflight:pin(ctx.preflight),"source":pin("source"),m.SELF:pin(m.SELF),m.TEST:pin(m.TEST)}
    return ctx,NS(json=lambda name:rows[name],pin=lambda name:snapshots[name],snapshots=snapshots),code,pref


class Tests(unittest.TestCase):
    def test_closed_context_and_separate_namespace(self):
        ctx=m.context(161,2,8,7,1)
        self.assertNotEqual(ctx.qualification,ctx.code)
        for values in ((True,2,8,7,1),(160,2,8,7,1),(161,1,8,7,1),(161,2,9,7,1)):
            with self.assertRaises(ValueError):m.context(*values)
    def test_exact_frozen_code_and_full_preflight_admitted(self):
        ctx,q,code,pref=fixture();self.assertEqual(m.admit(q,ctx,A),(code,pref))
        def original(run):return template, binding_attempt, run
        import current_queue_successor_connections as metadata
        observed=[]
        def connect(fn,backend):
            self.assertIs(fn.__code__,original.__code__)
            self.assertIs(fn.__defaults__,original.__defaults__)
            self.assertIs(fn.__closure__,original.__closure__)
            observed.append(fn)
            return fn,dict(actual_local_bindings=0,static_leaf_connections=1)
        template=lambda:None
        callback=lambda reader:reader
        window=NS(API=NS(original_run_owned=original),CONNECTION=NS(connect_run=connect),BACKEND=object())
        execute,state=m.compose_outer(window,template,callback,metadata)
        self.assertEqual(execute(1)[2],1)
        self.assertEqual(execute(1)[1]("reader",1),"reader")
        with self.assertRaises(ValueError):execute(1)[1]("reader",2)
        self.assertEqual(len(observed),1)
    def test_stale_source_rejected(self):
        ctx,q,code,pref=fixture();q.snapshots["source"]["sha256"]="b"*64
        with self.assertRaisesRegex(ValueError,"UNCHANGED"):m.admit(q,ctx,A)
    def test_wrong_case_or_missing_oracle_rejected(self):
        for key,value in (("index",162),("independent_oracle_connected",False),("product_worker_or_Native_frame_executed",True)):
            ctx,q,code,pref=fixture();pref[key]=value
            with self.assertRaises(ValueError):m.admit(q,ctx,A)
        import ast
        tree=ast.parse((Path(__file__).parents[3]/m.SELF).read_text(encoding="utf-8"))
        construct=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="construct")
        callback=next(n for n in construct.body if isinstance(n,ast.FunctionDef) and n.name=="callback")
        # Full source admission is mandatory inside the actual engine callback,
        # not replaced by small startup metadata or deferred until after GO.
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="admit"
            for n in ast.walk(callback)))
    def test_preflight_must_pin_exact_code_and_all_closing_reads(self):
        for mutation in (lambda p:p["code_pin"].update(bytes=2),lambda p:p.update(final_fresh_hashes=0)):
            ctx,q,code,pref=fixture();mutation(pref)
            with self.assertRaises(ValueError):m.admit(q,ctx,A)
        ctx=m.context(161,3,1,1,1)
        row=dict(state="DEFERRED_NOT_STARTED",task="case161-current-r002-tests",worker_created=False,
            product_body_observed=False,actual_product_child_executed=False,cleanup_confirmed=True,
            owned_tree_empty=True,accepted_count_delta=0,current_generation_runtime_candidate_qualified=False,
            Native_source_frame_qualified=False,stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
            passed_test_names=[],source_frame=None)
        q=NS(json=lambda path:row)
        m.previous_stops(q,ctx,A)
        for key,value in (("worker_created",True),("passed_test_names",["test"]),("cleanup_confirmed",False)):
            old=row[key];row[key]=value
            with self.assertRaises(ValueError):m.previous_stops(q,ctx,A)
            row[key]=old
    def test_dispatch_qualification_requires_current_entry_and_test(self):
        ctx,q,code,pref=fixture()
        qualification=dict(state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",index=161,
            physical_run=2,contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,
            fresh_inputs=2,final_fresh_hashes=2,runtime_default_imports=64,code_pin=copy.deepcopy(q.snapshots[ctx.code]),
            preflight_pin=copy.deepcopy(q.snapshots[ctx.preflight]),source_pins=[copy.deepcopy(q.snapshots[m.SELF]),copy.deepcopy(q.snapshots[m.TEST])])
        m.admit(q,ctx,A,qualification)
        qualification["source_pins"].pop()
        with self.assertRaisesRegex(ValueError,"ENTRY_AND_TEST"):m.admit(q,ctx,A,qualification)


if __name__=="__main__":unittest.main()
