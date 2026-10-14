"""Explicit v2 wire dependency for frozen successor parent and worker bodies.

Original v1 source files remain immutable and required. New source witnesses
join every real metadata reader before GO; old records are never relabelled.
"""
import builtins
import ast
import copy
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_successor_wire_runtime_v2.py"
TEST="tools/p09/tests/test_current_queue_successor_wire_runtime_v2.py"
PINS=[
    dict(path="tools/p09/current_queue_successor_dispatch.py",bytes=22558,sha256="afa51947097da26304dbbd03fb504fad75a0b0256e9c34282b384c0c411feaef"),
    dict(path="tools/p09/current_queue_successor_controller.py",bytes=15872,sha256="007dc8f38801329cc7a0ca552058aaf7409290c335faf4c1e2ac28300e1a47ab"),
    dict(path="tools/p09/current_queue_successor_runtime.py",bytes=27293,sha256="523fbe57dc31f73612651cf44dbca9a85fe706a40e563f391ccade2aa0cf63df"),
    dict(path="tools/p09/current_queue_successor_connections.py",bytes=19229,sha256="363d9665885eedc096a7c970098cd80568197e13930e13bc10347e044a687fa9"),
    dict(path="tools/p09/current_queue_successor_binding.py",bytes=15040,sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915")]
OLD_CONTROLLER=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def require(value,label):
    if not value:raise ValueError("SUCCESSOR_WIRE_RUNTIME_V2_"+label)


def bind_imports(namespace,reuse):
    """Closed dependency overrides, no sys.modules or shared builtins edits."""
    ordinary=builtins.__import__
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if level==0 and name in reuse:return reuse[name]
        return ordinary(name,globals,locals,fromlist,level)
    for name,fn in tuple(vars(namespace).items()):
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            env=fn.__globals__;env["__builtins__"]={**vars(builtins),"__import__":declared}
            changed=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
            changed.__kwdefaults__=fn.__kwdefaults__
            require(changed.__code__ is fn.__code__ and changed.__defaults__ is fn.__defaults__
                and changed.__closure__ is fn.__closure__,"ENTIRE_FUNCTION_RETAINED")
            env[name]=changed;setattr(namespace,name,changed)


def configure_runtime(runtime,wire,checkpoint):
    wire.install(runtime.metadata,checkpoint)
    # The original parent launches its SELF. Use this entry so its worker sees
    # the same explicit v2 transport, not the immutable v1 CLI by accident.
    for fn in vars(runtime).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__.update(SELF=SELF,TEST=TEST)
    runtime.SELF,runtime.TEST=SELF,TEST
    return runtime


def graph_v2_paths(namespace,pin):
    """Only graph receipt pathname metadata changes; exact AST inverse."""
    raw=(Path(__file__).resolve().parents[2]/pin["path"]).read_text(encoding="utf-8")
    tree=ast.parse(raw)
    for node in tree.body:
        if not isinstance(node,ast.FunctionDef):continue
        original=getattr(namespace,node.name,None)
        if type(original) is not FunctionType:continue
        before=ast.dump(node,include_attributes=False);changed=copy.deepcopy(node);count=0
        class Rewrite(ast.NodeTransformer):
            def visit_JoinedStr(self,value):
                nonlocal count
                if any(isinstance(n,ast.Constant) and type(n.value) is str and "-successor-connections" in n.value for n in value.values):
                    for item in value.values:
                        if isinstance(item,ast.Constant) and item.value==".v1.json":
                            item._old_graph_suffix=copy.deepcopy(item);item.value=".v2.json";count+=1
                return self.generic_visit(value)
        changed=Rewrite().visit(changed)
        if not count:continue
        class Undo(ast.NodeTransformer):
            def visit(self,value):
                if hasattr(value,"_old_graph_suffix"):return copy.deepcopy(value._old_graph_suffix)
                return super().visit(value)
        require(ast.dump(Undo().visit(copy.deepcopy(changed)),include_attributes=False)==before,"WHOLE_GRAPH_PATH_AST_INVERSE")
        env=original.__globals__
        exec(compile(ast.fix_missing_locations(ast.Module(body=[changed],type_ignores=[])),pin["path"],"exec"),env)
        setattr(namespace,node.name,env[node.name])
    return namespace


def load(root,a,scope,bytes_policy,envelope,*,worker=False):
    import bounded_successor_capsule_wire_v2 as wire
    modules,proof=envelope.namespace_bundle.load(root,PINS,{
        "current_stored_runtime_scope":scope,"owned_source_read_pressure":bytes_policy})
    private=vars(modules)
    # Add new witnesses to the actual readers, not just a later report. This
    # stays inside each original reader's resource guard and full final hashes.
    class Reader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for name in (SELF,TEST,wire.SELF,wire.TEST):self.pin(name)
            for pin in PINS:a.exact(self.pin(pin["path"]),pin,"V2_ALL_FROZEN_V1_SOURCE_PINS")
    api=NS(**{**vars(a),"AcceptanceReader":Reader})
    reuse={**private,"accept_case112_current_epoch":api,
        "runtime_envelope_namespace_bundle_v1":envelope.namespace_bundle}
    oldproof=[]
    if not worker:
        old,oldproof=envelope.namespace_bundle.load(root,[OLD_CONTROLLER],
            {"flat_current_queue_envelope_runtime_v25":envelope})
        reuse["case160_run007_controller"]=old.case160_run007_controller
    for namespace in private.values():bind_imports(namespace,reuse)
    for pin in PINS:graph_v2_paths(private[pin["path"].rsplit("/",1)[-1][:-3]],pin)
    connections=private["current_queue_successor_connections"]
    wire.install(connections,lambda:None)
    runtime=private["current_queue_successor_runtime"]
    for fn in vars(runtime).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__.update(SELF=SELF,TEST=TEST)
    runtime.SELF,runtime.TEST=SELF,TEST
    dispatch=private["current_queue_successor_dispatch"]
    original=dispatch.current_namespaces
    def current_namespaces(q,ctx,aa,old,ss,bb,qualification=None):
        linked,controller,sourceproof=original(q,ctx,aa,old,ss,bb,qualification)
        graph_v2_paths(linked,PINS[2])
        graph_v2_paths(controller,PINS[1])
        configure_runtime(linked,wire,q.checkpoint)
        for name in (SELF,TEST,wire.SELF,wire.TEST):q.pin(name)
        return linked,controller,sourceproof
    original.__globals__["current_namespaces"]=current_namespaces
    dispatch.current_namespaces=current_namespaces
    # Keep the original CODE/preflight selector and its own tests as frozen
    # witnesses. Entry qualification tests remain the original 6 contracts.
    return NS(**private),dict(frozen_source_proofs=proof,original_controller_proofs=oldproof,
        new_sources_in_every_metadata_reader=True,original_bodies_defaults_closures_retained=True,
        shared_default_modules_or_builtins_mutated=False,actual_product_or_Native_qualified=False)


def main():
    import argparse
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    is_worker=len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]
    modules,proof=load(c.ROOT,a,scope,bytes_policy,envelope,worker=is_worker)
    if is_worker:
        return modules.current_queue_successor_runtime.owned_worker_entry(sys.argv[3])
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--binding-attempt",type=int,default=1)
    parser.add_argument("--code-attempt",type=int,default=1);parser.add_argument("--preflight-attempt",type=int,default=1)
    parser.add_argument("--qualification-attempt",type=int,default=1)
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("graph","bootstrap","code","preflight","qualify","native"):mode.add_argument("--"+name,action="store_true")
    args=parser.parse_args();require(162<=args.case<=249 and 2<=args.run<=8,"CLOSED_V2_CONTEXT")
    controller=modules.current_queue_successor_controller;dispatch=modules.current_queue_successor_dispatch
    if args.graph:return modules.current_queue_successor_connections.prepare(args.case,args.binding_attempt,args.run,0)
    if args.bootstrap:
        # The original factory prepares the small hint and proves original EOF
        # rejection. Whole parent admission remains a later mandatory stage.
        return modules.current_queue_successor_runtime.qualify_factory(args.case,args.run,args.run,args.attempt,True)
    if args.code:return controller.run_code(args.case,args.run,args.attempt)
    if args.preflight:return controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    return dispatch.main(ctx,args.qualify)


if __name__=="__main__":raise SystemExit(main())
