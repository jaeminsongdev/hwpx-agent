"""Bounded live predecessor-policy test, never a Native/product entry.

Exercise the pinned original retry body on real closed Native records 2/3 and
prepared-only records 4..7 without repeating the whole metadata preflight.
This supporting result does not replace dispatcher qualification or acceptance.
"""
from pathlib import Path
from types import SimpleNamespace as NS
from types import FunctionType
import argparse
import ast
import json
import re
import sys
import time

SELF="tools/p09/probe_prepared_run_admission_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import runtime_envelope_namespace_bundle_v1 as bundle
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser()
    parser.add_argument("--attempt",type=int,default=2)
    parser.add_argument("--code-attempt",type=int,default=2)
    parser.add_argument("--run",type=int,default=7)
    args=parser.parse_args()
    a.require(2<=args.attempt<=8 and 1<=args.code_attempt<=8 and args.run in (7,8),"BOUNDED_LIVE_PROBE_CONTEXT")
    output=PREFIX+f"prepared-closure-live-admission{args.attempt:03}.v1.json"
    a.require(not(c.ROOT/output).exists(),"EXCLUSIVE_LIVE_ADMISSION_TEST")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    q=None;started=time.monotonic()
    row=dict(state="FAILED_LIVE_PREPARATION_ADMISSION_NOT_ADOPTED",
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        code=q.json(PREFIX+f"successor-code-run{args.run:03}-attempt{args.code_attempt:03}.v1.json")
        a.fields(code,dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",
            contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_TEST_BASELINE")
        pins={p["path"]:p for p in code["source_pins"]}
        # Every direct helper used by this fresh test process stays a real input.
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename and Path(filename).absolute().is_relative_to(c.ROOT/"tools/p09"):
                name=Path(filename).absolute().relative_to(c.ROOT).as_posix()
                if name!=SELF:a.exact(q.pin(name),pins[name],"EXACT_DIRECT_TEST_DEPENDENCY")
        names=("prepared_run_closure_v1","current_queue_sealed_metadata_runtime_v5",
            "current_queue_successor_retry_runtime_v3","current_queue_successor_wire_runtime_v2")
        selected=[pins["tools/p09/"+name+".py"] for name in names]
        for pin in selected:a.exact(q.pin(pin["path"]),pin,"EXACT_PRIVATE_TEST_DEPENDENCY")
        modules,proof=bundle.load(c.ROOT,selected,{})
        retry=modules.current_queue_successor_retry_runtime_v3
        retry_pin=pins[retry.SELF]
        modules.current_queue_sealed_metadata_runtime_v5.retry_paths(
            (c.ROOT/retry.SELF).read_bytes(),retry,retry_pin)
        adapter=modules.prepared_run_closure_v1
        qualification=q.json(PREFIX+"prepared-closure-code004.v1.json")
        a.fields(qualification,dict(state="PASS_PREPARED_ONLY_CLOSURE_CODE6_NOT_ENTRY_NATIVE_OR_PRODUCT",
            contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_CLOSURE_CODE6")
        for pin in qualification["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CLOSURE_SOURCE")
        adapter.install_retry(retry,a)
        # Execute the exact pinned original v4 loop which caused the real
        # dispatcher failure. Do not replace it with an expected mock result.
        v4_path="tools/p09/current_queue_successor_lossless_runtime_v4.py"
        a.exact(q.pin(v4_path),pins[v4_path],"EXACT_ORIGINAL_LATE_ROLE_REWRITE")
        tree=ast.parse((c.ROOT/v4_path).read_text(encoding="utf-8"))
        load=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="load")
        loops=[n for n in load.body if isinstance(n,ast.For) and "vars(retry)" in ast.unparse(n.iter)
            and "fn.__globals__.update" in ast.unparse(n)]
        a.require(len(loops)==1,"ONE_ORIGINAL_RETRY_ROLE_REWRITE")
        roles={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("SELF","TEST")}
        exec(compile(ast.Module(body=loops,type_ignores=[]),v4_path,"exec"),
            dict(retry=retry,FunctionType=FunctionType,**roles))
        a.exact(adapter.producer_inventory.__globals__["SELF"],roles["SELF"],"ACTUAL_ROLE_REBIND_OCCURRED")
        retry.previous_stops(q,NS(index=165,run=8),a,modules.current_queue_successor_wire_runtime_v2)
        a.require(all(adapter.absent(q,PREFIX+f"current-runtime-run{n:03}.v1.json") for n in range(4,9)),
            "NO_NEW_OR_UNRESOLVED_NATIVE")
        q.finish();guard.check(force=True)
        row.update(state="PASS_LIVE_PREDECESSOR_ADMISSION_NOT_DISPATCHER_NATIVE_PRODUCT_OR_ACCEPTANCE",
            original_Native_prebody_records_checked=2,prepared_only_closures_checked=4,
            original_retry_suffix_AST_projection_retained=True,source_pins=list(q.snapshots.values()),
            actual_original_v4_late_role_rewrite_exercised=True,
            private_source_proofs=proof,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and isinstance(error.args[0],str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"LIVE_TEST_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_type","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
