"""Preparation-only expected bootstrap serialization for the v9 publisher.

The original factory body, byte/hash comparison, 16KiB bound and actual NO-GO
worker remain. No existing file is rewritten and no Native path is provided.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import json
import re
import sys

SELF="tools/p09/qualify_expanded_worker_startup_v1.py"
TEST="tools/p09/tests/test_expanded_worker_serialization_v1.py"
FRONT=dict(path="tools/p09/expanded_closed_preparation_v1.py",bytes=21675,
    sha256="8de7dc45657401ceefc05a8535114155da138f79d3d17a9c6f2491808e43fca1")
CODE_STATE="PASS_EXPANDED_BOOTSTRAP_SERIALIZATION_CODE4_NOT_NATIVE_OR_PRODUCT"


def require(ok,label):
    if not ok:raise ValueError("EXPANDED_BOOTSTRAP_SERIALIZATION_"+label)


def expected_dumps(row,**options):
    if options==dict(ensure_ascii=True,allow_nan=False,separators=(",",":")) and type(row) is dict:
        pin=row.get("capsule_pin")
        if type(pin) is dict and type(pin.get("path")) is str and pin["path"].endswith(".compact.v9.json"):
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-worker-capsule([0-9]{3})\.compact\.v9\.json",pin["path"])
            require(match is not None and type(row.get("index")) is int and type(row.get("run")) is int
                and row["index"]==int(match[1]) and row["run"]==int(match[2])
                and row.get("schema_version")=="hwpx-agent.p09-current-successor-worker-bootstrap/v1","EXACT_NEW_BOOTSTRAP_CONTEXT")
            declaration=row.get("closed_prebody_source_declaration")
            require(type(declaration) is dict and declaration.get("index")==row["index"]
                and declaration.get("schema_version")=="hwpx-agent.p09-qualified-closed-prebody-source-policy/v1","DECLARED_SOURCE_POLICY_REQUIRED")
            return json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)
    return json.dumps(row,**options)


def in_family(fn,code=None,builtins=None):
    """Keep late reader admission changes visible in the original family."""
    require(type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_FAMILY_ONLY")
    env=fn.__globals__;previous=env.get("__builtins__")
    env["__builtins__"]=fn.__builtins__ if builtins is None else builtins
    try:result=FunctionType(fn.__code__ if code is None else code,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    finally:env["__builtins__"]=previous
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def install(runtime):
    original=runtime.qualify_factory
    require(type(original) is FunctionType and original.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_FACTORY_ONLY")
    builtins=dict(original.__builtins__);previous=builtins["__import__"]
    private_json=NS(**{**vars(json),"dumps":expected_dumps})
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="json" and level==0:return private_json
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    linked=in_family(original,builtins=builtins)
    require(linked.__code__ is original.__code__ and linked.__defaults__ is original.__defaults__
        and linked.__closure__ is original.__closure__,"WHOLE_FACTORY_BODY_RETAINED")
    original.__globals__["qualify_factory"]=linked;runtime.qualify_factory=linked


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--code-attempt",type=int,default=2)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--serialization-code",action="store_true");mode.add_argument("--bootstrap",action="store_true")
    args=parser.parse_args();require(165<=args.case<=249 and 4<=args.run<=8 and 1<=args.attempt<=8,"CLOSED_CONTEXT")
    front_ns,_=envelope.namespace_bundle.load(c.ROOT,[FRONT],{})
    front=front_ns.expanded_closed_preparation_v1
    ns,_=envelope.namespace_bundle.load(c.ROOT,[front.PRIVATE],{})
    private=ns.closed_preparation_private_entry_v1
    modules,_=envelope.namespace_bundle.load(c.ROOT,private.PINS,{})
    code_path=f"implementation/p09/evidence/p09-361-case{args.case}-expanded-bootstrap-serialization-code{(args.attempt if args.serialization_code else args.code_attempt):03}.v1.json"
    if args.serialization_code:
        require(1<=args.code_attempt<=8 and not (c.ROOT/code_path).exists(),"EXCLUSIVE_CODE")
        guard=modules.terminal_metadata_pressure_v1.guard_type(modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
        started=time.monotonic();row=dict(state="FAILED_EXPANDED_BOOTSTRAP_SERIALIZATION_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0)
        try:
            guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            for name in (SELF,TEST):q.pin(name)
            a.exact(q.pin(FRONT["path"]),FRONT,"FROZEN_PREPARED_FRONTEND")
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromName("tests.test_expanded_worker_serialization_v1"))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=4,errors=0,failures=0,skipped=0),"ALL_SERIALIZATION4")
            q.finish();guard.check(force=True)
            row.update(state=CODE_STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        finally:
            guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
                CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
        modules.successor_preparation_workspace_v1.publish(c.ROOT,code_path,row,a)
        print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","cleanup_confirmed","CPU_max","RAM_min")}))
        return 0 if row["state"]==CODE_STATE else 1
    original_loader=envelope.namespace_bundle
    def load(*items,**options):
        namespaces,proof=original_loader.load(*items,**options)
        namespace=getattr(namespaces,"expanded_preparation_namespace_v1",None)
        if namespace is not None:
            whole_literal=namespace.literal_function
            def literal_function(fn,mapping):
                changed,proof=whole_literal(fn,mapping)
                if fn.__name__=="qualify_factory":changed=in_family(fn,changed.__code__)
                return changed,proof
            whole_literal.__globals__["literal_function"]=literal_function
            namespace.literal_function=literal_function
        entry=getattr(namespaces,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            whole=entry.load
            def connected(*items,**options):
                values=list(items);api=values[1]
                class Reader(api.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs)
                        row=self.json(code_path)
                        a.fields(row,dict(state=CODE_STATE,contracts=dict(run=4,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_SERIALIZATION_CODE4")
                        require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"CLOSED_CODE_HASHES")
                        for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"CURRENT_EXPECTED_SERIALIZATION_SOURCES")
                values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                linked=whole(*values,**options);install(linked.modules.current_queue_successor_runtime)
                return linked
            entry.load=connected
        return namespaces,proof
    proxy=NS(**{**vars(envelope),"namespace_bundle":NS(**{**vars(original_loader),"load":load})})
    original=front.main;builtins=dict(original.__builtins__);previous=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:return proxy
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    execute=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    # The outer --code-attempt belongs to this adapter, not the frozen parser.
    if "--code-attempt" in sys.argv:
        offset=sys.argv.index("--code-attempt");sys.argv=sys.argv[:offset]+sys.argv[offset+2:]
    return execute()


if __name__=="__main__":raise SystemExit(main())
