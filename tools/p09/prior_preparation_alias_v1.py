"""Reconcile only exact approved-prior physical aliases in metadata unions.

Original semantic_union still validates the complete logical scope. This does
not read/cache source bytes, change disk counters, remove originals, loosen a
Frame guard, or authorize Native. Caller must admit the predecessor normally.
"""
import re
from types import FunctionType

SELF="tools/p09/prior_preparation_alias_v1.py"
TEST="tools/p09/tests/test_prior_preparation_alias_v1.py"
BINDINGS=dict(path="tools/p09/current_queue_successor_binding.py",bytes=15040,
    sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915")


def require(ok,label):
    if not ok:raise ValueError("PRIOR_PREPARATION_ALIAS_"+label)


def normalize(scope,historical_pairs,rows,index,checkpoint):
    require(type(index) is int and 161<=index<=249 and callable(checkpoint),"EXACT_CONTEXT")
    require(type(historical_pairs) in (list,tuple) and len(historical_pairs)<=249,"BOUNDED_PRIOR_PAIRS")
    require(type(rows) is dict,"COMPLETE_METADATA_MAPPING")
    current=scope.pins(list(rows.values()));require(current==rows,"EXACT_MAPPING_KEYS")
    reverse={};logical=set()
    for pair in historical_pairs:
        checkpoint()
        require(type(pair) is dict and set(pair)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"}
            and pair["schema_version"]=="hwpx-agent.p09-lossless-runtime-source-projection/v1"
            and type(pair["next_case"]) is int and 112<=pair["next_case"]<index,"APPROVED_PRIOR_CONTEXT_ONLY")
        old,new=pair["semantic_original_pin"],pair["physical_envelope_pin"]
        scope.pins([old,new])
        match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",old["path"])
        require(match is not None and 112<=int(match[1])<=pair["next_case"]
            and new["path"].startswith("implementation/p09/evidence/p361-lossless-runtime-inputs/")
            and new["path"].endswith(".envelope.v1.json")
            and 0<old["bytes"]<=16777216 and 0<new["bytes"]<=16777216,"ORIGINAL_PRIOR_RECEIPT_AND_EXPLICIT_PHYSICAL_ALIAS")
        require(new["path"] not in reverse and old["path"] not in logical,"BIJECTIVE_APPROVED_PRIOR_TABLE")
        reverse[new["path"]]=(old,new);logical.add(old["path"])
    normalized={};mapped=0
    for name,pin in current.items():
        checkpoint()
        if name in reverse:
            old,expected=reverse[name]
            require(pin==expected,"EXACT_PRIOR_PHYSICAL_PIN_NOT_PATH_ONLY")
            pin=dict(old);name=pin["path"];mapped+=1
        require(name not in normalized or normalized[name]==pin,"NO_LOGICAL_CONFLICT_REBASE")
        normalized[name]=dict(pin)
    checkpoint()
    return normalized,dict(approved_prior_aliases_reconciled=mapped,unmapped_inputs_unchanged=True,
        source_bytes_or_hashes_cached=False,physical_IO_not_relabelled=True)


def install(module,historical_pairs,index):
    original=module.Binding.semantic_union
    require(type(original) is FunctionType and original.__globals__.get("__name__","").startswith("p09_exact_runtime_envelope_scope_binding_v1"),"PRIVATE_ORIGINAL_SCOPE_METHOD_ONLY")
    require(not getattr(module,"prior_preparation_alias_installed",False),"ONE_EXPLICIT_SCOPE_ADAPTER")
    others={n:fn for n,fn in vars(module.Binding).items() if n!="semantic_union"}
    # Freeze metadata only; no source contents or successful source reads are cached.
    pairs=[dict(r,semantic_original_pin=dict(r["semantic_original_pin"]),physical_envelope_pin=dict(r["physical_envelope_pin"])) for r in historical_pairs]
    def semantic_union(self,rows,checkpoint):
        normalized,_=normalize(module.source.scope,pairs,rows,index,checkpoint)
        return original(self,normalized,checkpoint)
    module.Binding.semantic_union=semantic_union;module.prior_preparation_alias_installed=True
    require(all(vars(module.Binding).get(n) is fn for n,fn in others.items()),"ALL_OTHER_ORIGINAL_BINDING_METHODS_RETAINED")


def main():
    import argparse,io,json,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import flat_current_queue_envelope_runtime_v25 as envelope
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();require(1<=args.attempt<=8,"CODE_ATTEMPT")
    output=f"implementation/p09/evidence/p09-361-case165-prior-preparation-alias-code{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_CODE_REPORT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_PRIOR_PREPARATION_ALIAS_CODE_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,"tools/p09/current_stored_runtime_scope.py"):q.pin(name)
        a.exact(q.pin(BINDINGS["path"]),BINDINGS,"ORIGINAL_BINDING_STATIC_API")
        modules,_=envelope.namespace_bundle.load(c.ROOT,[BINDINGS],{})
        bindings=modules.current_queue_successor_binding
        for pin in bindings.PINS:a.exact(q.pin(pin["path"]),pin,"ORIGINAL_PROJECTION_SOURCES")
        tests,_=envelope.namespace_bundle.load(c.ROOT,[q.snapshots[TEST]],{})
        tests.test_prior_preparation_alias_v1.Tests.data.__globals__.update(MODULE=sys.modules[__name__],SCOPE=scope,
            BINDINGS_API=bindings,ROOT=c.ROOT,LOADER=envelope.namespace_bundle,CHECKPOINT=guard.check)
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests.test_prior_preparation_alias_v1))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped));row["contracts"]=contracts
        row["contract_error_types"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors]
        a.exact(contracts,dict(run=6,errors=0,failures=0,skipped=0),"ALL_ALIAS6")
        q.finish();guard.check(force=True)
        row.update(state="PASS_PRIOR_PREPARATION_ALIAS_CODE6_NOT_CURRENT_ENTRY_OR_PRODUCT",source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"CODE_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
