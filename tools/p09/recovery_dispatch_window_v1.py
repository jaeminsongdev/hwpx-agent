"""Close the fresh dispatch-controller window without mutating frozen sources.

Only the exact pinned controller load is connected. Native keeps its original
CPU/RAM/Job/source guards; the preparation CPU entry still rejects Native.
"""
from pathlib import Path
from types import SimpleNamespace as NS,FunctionType
import ast
import copy
import sys

BRIDGE_SOURCE="tools/p09/recovery_dispatch_window_v1.py"
BRIDGE_TEST="tools/p09/tests/test_recovery_dispatch_window_v1.py"
CONTROLLER_PIN=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def require(ok,label):
    if not ok:raise ValueError("RECOVERY_DISPATCH_WINDOW_"+label)


def native_context(arguments):
    flags=("--case","--run","--attempt","--code-attempt","--preflight-attempt","--qualification-attempt")
    require(type(arguments) is list and len(arguments)==13 and arguments.count("--native")==1,"EXPLICIT_NATIVE_ONLY")
    values={};remaining=list(arguments);remaining.remove("--native")
    for flag in flags:
        require(remaining.count(flag)==1 and remaining.index(flag)+1<len(remaining),"EXACT_NATIVE_FLAGS")
        value=remaining[remaining.index(flag)+1]
        require(type(value) is str and value.isascii() and value.isdecimal(),"INTEGER_NATIVE_CONTEXT")
        values[flag]=int(value)
    require(values["--case"]==165 and values["--run"]==8 and values["--code-attempt"]==1
        and 1<=values["--preflight-attempt"]<=16
        and all(1<=values[k]<=8 for k in ("--attempt","--qualification-attempt")),"ONLY165_RUN008")
    require(set(remaining[::2])==set(flags),"NO_UNKNOWN_NATIVE_FLAGS")
    return values


def connect_loader(original,envelope,recovery,window,raw,bind,*,witness=None,controller_transform=None):
    """Private exact dependency routing, not a code/constant/model projection."""
    observations=[]
    def dispatch_load(actual_envelope,*args,**kwargs):
        modules,proof=actual_envelope.namespace_bundle.load(*args,**kwargs)
        pins=args[1] if len(args)>1 else kwargs.get("pins")
        reuse=args[2] if len(args)>2 else kwargs.get("reuse")
        require(pins==[CONTROLLER_PIN],"ONE_EXACT_CONTROLLER_SOURCE")
        if pins==[CONTROLLER_PIN]:
            require(type(reuse) is dict and set(reuse)=={"flat_current_queue_envelope_runtime_v25"},"EXACT_DISPATCH_LOAD_DEPENDENCY")
            old=modules.case160_run007_controller
            require(getattr(old,"__name__","")=="p09_exact_case160_run007_controller","FRESH_PRIVATE_CONTROLLER_ONLY")
            alias,details=recovery.prior_alias(old,window,raw)
            require(alias.base is old.base,"ORIGINAL_RESOURCE_GUARD_IDENTITY")
            require(alias.old.prior.WINDOW.SECONDS==10,"ACTUAL_PRIVATE_WINDOW10")
            if controller_transform is not None:
                require(callable(controller_transform),"EXPLICIT_PREPARATION_CONTROLLER_TRANSFORM")
                alias=controller_transform(alias)
                require(alias.old.prior.WINDOW.SECONDS==10,"PREPARATION_TRANSFORM_RETAINS_WINDOW10")
            modules.case160_run007_controller=alias
            observations.append(details)
        return modules,proof
    def load(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        entry=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            whole=entry.load
            def connected(*items,**options):
                values=list(items);api=values[1]
                if witness is not None:
                    class Reader(api.AcceptanceReader):
                        def __init__(self,*args,**kwargs):
                            super().__init__(*args,**kwargs);witness(self)
                    values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                linked=whole(*values,**options)
                dispatch=getattr(getattr(linked,"modules",None),"current_queue_successor_dispatch",None)
                if dispatch is not None:
                    revised=project_main(dispatch.main,dispatch_load)
                    dispatch.main.__globals__["main"]=revised;dispatch.main=revised
                return linked
            entry.load=connected
        for namespace in vars(modules).values():bind(namespace,proxy)
        return modules,proof
    routed=NS(**{**vars(original),"load":load,"dispatch_load":dispatch_load})
    proxy=NS(**{**vars(envelope),"namespace_bundle":routed})
    return routed,observations


def project_main(original,reload):
    """One explicit loader dependency; full AST inverse retains every predicate."""
    require(type(original) is FunctionType and original.__name__=="main"
        and original.__code__.co_filename.replace("\\","/").endswith("current_queue_successor_dispatch.py"),"EXACT_DISPATCH_MAIN")
    source=Path(original.__code__.co_filename)
    if not source.is_absolute():
        import conservative_maintenance as c
        source=c.ROOT/source
    tree=ast.parse(source.read_text(encoding="utf-8"))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
    def compiled(value):
        env=dict(original.__globals__,_recovery_dispatch_reload=reload)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[value],type_ignores=[])),original.__code__.co_filename,"exec",dont_inherit=True),env)
        return env["main"]
    if compiled(copy.deepcopy(node)).__code__!=original.__code__:
        edits=0
        for joined in ast.walk(node):
            if not isinstance(joined,ast.JoinedStr) or not any(isinstance(n,ast.Constant)
                    and type(n.value) is str and "-successor-connections" in n.value for n in joined.values):continue
            for value in joined.values:
                if isinstance(value,ast.Constant) and value.value==".v1.json":value.value=".v4.json";edits+=1
        require(edits==1 and compiled(copy.deepcopy(node)).__code__==original.__code__,"EXACT_QUALIFIED_GRAPH4_MAIN_BEFORE_CONNECTION")
    before=ast.dump(node,include_attributes=False)
    calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)
        and ast.dump(n.func,include_attributes=False)==ast.dump(ast.parse("envelope.namespace_bundle.load",mode="eval").body,include_attributes=False)]
    require(len(calls)==1 and len(calls[0].args)==3 and not calls[0].keywords
        and ast.dump(calls[0].args[1],include_attributes=False)==ast.dump(ast.parse("[ORIGINAL_CONTROLLER_PIN]",mode="eval").body,include_attributes=False),"ONE_EXACT_MAIN_CONTROLLER_DEPENDENCY")
    call=calls[0];prior=copy.deepcopy(call.func)
    call.func=ast.Name(id="_recovery_dispatch_reload",ctx=ast.Load());call.args.insert(0,ast.Name(id="envelope",ctx=ast.Load()))
    revised=compiled(copy.deepcopy(node));call.func=prior;call.args.pop(0)
    require(ast.dump(node,include_attributes=False)==before,"WHOLE_MAIN_INVERSE_ALL_PREDICATES_RETAINED")
    require(revised.__defaults__==original.__defaults__ and revised.__closure__==original.__closure__,"MAIN_DEFAULTS_AND_CLOSURE")
    original.__globals__["_recovery_dispatch_reload"]=reload
    linked=FunctionType(revised.__code__,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    linked.__kwdefaults__=original.__kwdefaults__
    return linked


def main():
    import argparse,hashlib
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--connection-attempt",type=int,required=True)
    args,forward=parser.parse_known_args()
    require(sys.argv[1:].count("--connection-attempt")==1,"ONE_CONNECTION_RECEIPT")
    native_context(forward)
    source="tools/p09/preparation_attributed_entry_v1.py";data=(c.ROOT/source).read_bytes()
    ns,_=envelope.namespace_bundle.load(c.ROOT,[dict(path=source,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())],{})
    entry=ns.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    components=entry.window_components(c.ROOT,envelope)
    original=raw.prepared_run_closure_v1;policy=raw.preparation_attributed_cpu_v1
    original.configure_host_policy(c)
    require(not(c.ROOT/(entry.PREFIX+"current-runtime-run008.v1.json")).exists(),"NO_EXISTING_NATIVE008")
    pressure=raw.terminal_metadata_pressure_v1;distinct=raw.distinct_final_sample_guard_v1
    # The Native bridge NEVER constructs a candidate preparation CPU Guard.
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    def witness(q):entry.witnesses(q,a,policy,connection_attempt=args.connection_attempt)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);witness(q);q.finish();guard.check(force=True)
    finally:guard.close()
    require(guard.cleanup,"ORIGINAL_BOOTSTRAP_GUARD_CLEANUP")
    recovery=components.post_product_recovery_connection_v1;window=components.post_product_recovery_window_v1
    window_raw=(c.ROOT/window.WINDOW_PIN["path"]).read_bytes()
    routed,observations=connect_loader(entry.metadata_loader(envelope.namespace_bundle),envelope,recovery,window,window_raw,
        entry.bind_envelope,witness=witness)
    proxy=NS(**{**vars(envelope),"namespace_bundle":routed})
    code=entry.execute(original,proxy,forward)
    require(bool(observations),"ACTUAL_DISPATCH_RELOADING_CONNECTED")
    print(dict(dispatch_window_seconds=10,Native_CPU_policy_changed=False,original_entry_exit_code=code))
    return code


if __name__=="__main__":raise SystemExit(main())
