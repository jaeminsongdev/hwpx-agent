"""Explicit preparation publisher dependency, not hidden default modules.

Preserve the qualified whole orchestration source and original main function.
The publisher source remains in every stage's full fresh source inventory.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys
HELPER_FAILURES=[]
SELF="tools/p09/closed_preparation_private_entry_v1.py"
TEST="tools/p09/tests/test_closed_preparation_private_entry_v1.py"

PINS=[
    dict(path="tools/p09/closed_prebody_preparation_io_v1.py",bytes=18027,
        sha256="53ba98cb12bef239059719008471cd3920d297ba240869e92c3e948f990ea2e8"),
    dict(path="tools/p09/successor_preparation_workspace_v1.py",bytes=9656,
        sha256="003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,
        sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3"),
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,
        sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd")]


def publish_dynamic_family(dispatch):
    """A wrapper's globals can differ from the frozen main/construct family."""
    current=dispatch.current_namespaces
    for fn in vars(dispatch).values():
        if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"):
            fn.__globals__["current_namespaces"]=current


def entry_loader(loader):
    original=loader.load
    def load(*args,**kwargs):
        modules,proof=original(*args,**kwargs)
        entry=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            whole=entry.load
            def connected(*items,**options):
                arguments=list(items);api=arguments[1];original_require=api.require
                class Reader(api.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs)
                        for name in (SELF,TEST):self.pin(name)
                def checked(ok,label):
                    if not ok and label=="DISPATCH_ACTUAL_NATIVE_IMPORTED_HELPER_BOUND":
                        local=sys._getframe(1).f_locals
                        names=local.get("native_names");base=local.get("names")
                        if type(names) is set and type(base) is set and all(type(n) is str and n.startswith("tools/p09/") for n in names):
                            HELPER_FAILURES.append(dict(default_count=len(base),actual_count=len(names),
                                default_sources=sorted(base),extra_actual_sources=sorted(names-base)))
                    return original_require(ok,label)
                arguments[1]=NS(**{**vars(api),"require":checked,"AcceptanceReader":Reader})
                linked=whole(*arguments,**options)
                dispatch=linked.modules.current_queue_successor_dispatch
                publish_dynamic_family(dispatch)
                old=linked.connection.connect_dynamic
                def connect_dynamic(namespace,configure):
                    result=old(namespace,configure)
                    publish_dynamic_family(namespace)
                    return result
                linked.connection.connect_dynamic=connect_dynamic
                return linked
            entry.load=connected
        return modules,proof
    return NS(**{**vars(loader),"load":load})


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import flat_current_queue_envelope_runtime_v25 as envelope
    loader=envelope.namespace_bundle
    modules,_=loader.load(c.ROOT,PINS,{})
    original=modules.closed_prebody_preparation_io_v1.main
    builtins=dict(original.__builtins__);previous=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="successor_preparation_workspace_v1" and level==0:return modules.successor_preparation_workspace_v1
        if name in ("distinct_final_sample_guard_v1","terminal_metadata_pressure_v1") and level==0:return getattr(modules,name)
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:
            return NS(**{**vars(envelope),"namespace_bundle":entry_loader(loader)})
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    execute=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),
        argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    if execute.__code__ is not original.__code__ or execute.__defaults__ is not original.__defaults__ or execute.__closure__ is not original.__closure__:
        raise ValueError("PRIVATE_PREPARATION_WHOLE_MAIN_NOT_RETAINED")
    result=execute()
    if HELPER_FAILURES:
        import json
        print(json.dumps(dict(helper_bound_failure_diagnostic={k:HELPER_FAILURES[-1][k] for k in
            ("default_count","actual_count","extra_actual_sources")})))
    return result


if __name__=="__main__":raise SystemExit(main())
