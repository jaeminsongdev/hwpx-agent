"""Preparation-only binding of a raw reconstruction's current validator.

No validator body, source schema, physical pin, source scope or budget changes.
Keep the qualified expanded entry and its actual worker CLI immutable.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import ast
import copy
import hashlib
import sys

SELF="tools/p09/expanded_unhooked_setup_dependency_v1.py"
TEST="tools/p09/tests/test_expanded_unhooked_setup_dependency_v1.py"
FRONT=dict(path="tools/p09/expanded_closed_preparation_v1.py",bytes=21675,
    sha256="8de7dc45657401ceefc05a8535114155da138f79d3d17a9c6f2491808e43fca1")
ORCHESTRATION=dict(path="tools/p09/closed_prebody_preparation_io_v1.py",bytes=18027,
    sha256="53ba98cb12bef239059719008471cd3920d297ba240869e92c3e948f990ea2e8")


def project_setup_main(root,fn):
    raw=(root/ORCHESTRATION["path"]).read_bytes()
    if len(raw)!=ORCHESTRATION["bytes"] or hashlib.sha256(raw).hexdigest()!=ORCHESTRATION["sha256"]:
        raise ValueError("EXACT_FROZEN_SETUP_SOURCE")
    original=next(n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="main")
    filename=fn.__code__.co_filename
    def compiled(node):
        env=dict(fn.__globals__)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),filename,"exec",dont_inherit=True),env)
        return env["main"]
    if compiled(copy.deepcopy(original)).__code__!=fn.__code__:raise ValueError("WHOLE_SETUP_FUNCTION_CODE_BEFORE_PROJECTION")
    changed=copy.deepcopy(original);edits=[]
    for node in ast.walk(changed):
        if isinstance(node,ast.JoinedStr) and any(isinstance(v,ast.Constant) and type(v.value) is str
            and "successor-worker-bootstrap" in v.value for v in node.values):
            for value in node.values:
                if isinstance(value,ast.Constant) and value.value==".v4.json":
                    edits.append((value,value.value));value.value=".v6.json"
        if isinstance(node,ast.Assign) and any(isinstance(v,ast.Name) and v.id in ("setup_name","diagnostic_name") for v in node.targets):
            for value in ast.walk(node.value):
                if isinstance(value,ast.Constant) and value.value=="closed-io-":
                    edits.append((value,value.value));value.value="closed-io2-"
    if len(edits)!=3:raise ValueError("THREE_EXACT_SETUP_METADATA_LITERALS")
    inverse_values={(node.lineno,node.col_offset,node.value):old for node,old in edits}
    inverse=copy.deepcopy(changed)
    for node in ast.walk(inverse):
        if isinstance(node,ast.Constant) and type(node.value) is str:
            key=(node.lineno,node.col_offset,node.value)
            if key in inverse_values:node.value=inverse_values[key]
    if ast.dump(inverse,include_attributes=False)!=ast.dump(original,include_attributes=False):raise ValueError("WHOLE_SETUP_METADATA_AST_INVERSE")
    result=compiled(changed)
    if result.__defaults__!=fn.__defaults__ or result.__closure__!=fn.__closure__:raise ValueError("SETUP_DEFAULTS_CLOSURE_RETAINED")
    return result


def align(runtime):
    for name in ("worker_hint","reconstruct_worker_graph"):
        original=getattr(runtime,name)
        if type(original) is not FunctionType or not original.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_runtime"):continue
        linked=FunctionType(original.__code__,dict(original.__globals__,validate_worker_hint=runtime.validate_worker_hint),
            argdefs=original.__defaults__,closure=original.__closure__)
        linked.__kwdefaults__=original.__kwdefaults__
        original.__globals__[name]=linked;setattr(runtime,name,linked)


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    if not any(flag in sys.argv for flag in ("--preflight","--qualify")) or any(flag in sys.argv for flag in ("--native","--review","--accept")):
        raise ValueError("EXPANDED_SETUP_PREPARATION_ONLY")
    loader=envelope.namespace_bundle
    front_ns,_=loader.load(c.ROOT,[FRONT],{})
    front=front_ns.expanded_closed_preparation_v1
    def load(*items,**options):
        namespaces,proof=loader.load(*items,**options)
        orchestration=getattr(namespaces,"closed_prebody_preparation_io_v1",None)
        if orchestration is not None:orchestration.main=project_setup_main(c.ROOT,orchestration.main)
        namespace=getattr(namespaces,"expanded_preparation_namespace_v1",None)
        if namespace is not None:
            original=namespace.install
            def install(runtime):original(runtime);align(runtime)
            namespace.install=install
        entry=getattr(namespaces,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            whole=entry.load
            def connected(*items,**options):
                values=list(items);api=values[1]
                class Reader(api.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs)
                        for name in (SELF,TEST):self.pin(name)
                values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                return whole(*values,**options)
            entry.load=connected
        return namespaces,proof
    proxy=NS(**{**vars(envelope),"namespace_bundle":NS(**{**vars(loader),"load":load})})
    original=front.main;builtins=dict(original.__builtins__);previous=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:return proxy
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    execute=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    return execute()


if __name__=="__main__":raise SystemExit(main())
