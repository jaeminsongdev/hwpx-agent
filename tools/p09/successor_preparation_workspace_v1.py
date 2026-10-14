"""Preparation-only reusable scratch; immutable v2 Native entry stays unchanged.

All original reader wrappers, source pins, fresh reads, guards and closing
hashes remain. No worker/Native/acceptance entry or automatic retry is added.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

SELF="tools/p09/successor_preparation_workspace_v1.py"
TEST="tools/p09/tests/test_successor_preparation_workspace_v1.py"
BRIDGE=dict(path="tools/p09/current_queue_successor_wire_runtime_v2.py",bytes=11932,
    sha256="74c509ee713b571a8ed8d52f904513a567ff19391fb418942d1336a5ce6d6efd")
MODES=("workspace-code","code","preflight","qualify")
GUARD_SOURCE=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def reader_api(a,chunk,raw,qualification_path):
    base,proof=chunk.reader_type(a.AcceptanceReader,raw)
    readers=[]
    class Reader(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            for name in (SELF,TEST,chunk.SELF,chunk.TEST,BRIDGE["path"]):self.pin(name)
            qualification=self.json(qualification_path)
            a.fields(qualification,dict(state="PASS_PREPARATION_WORKSPACE_CODE_NOT_NATIVE_OR_PRODUCT",
                contracts=dict(run=17,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                accepted_count_delta=0,product_or_Native_executed=False),"WORKSPACE_CODE_REQUIRED")
            for pin in qualification["source_pins"]:
                a.exact(self.pin(pin["path"]),pin,"WORKSPACE_ALL_TESTED_SOURCE_PINS")
            readers.append(self)
    return NS(**{**vars(a),"AcceptanceReader":Reader}),dict(proof,readers=readers)


def publish(root,name,row,a):
    import hashlib,json,os
    path=root/name
    for parent in (path.parent,*path.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"WORKSPACE_DIRECT_ANCESTORS")
        if parent==root:break
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=262144,"WORKSPACE_BOUNDED_RECEIPT")
    with path.open("xb") as stream:
        a.exact(stream.write(raw),len(raw),"WORKSPACE_COMPLETE_RECEIPT");stream.flush();os.fsync(stream.fileno())
    return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    import argparse,io,json,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    import reusable_audit_chunk_v1 as chunk
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--code-attempt",type=int,default=1);parser.add_argument("--preflight-attempt",type=int,default=1)
    parser.add_argument("--workspace-qualification",type=int,default=1)
    parser.add_argument("--mode",choices=MODES,required=True)
    args=parser.parse_args()
    a.require(163<=args.case<=249 and 2<=args.run<=8 and all(1<=v<=8 for v in
        (args.attempt,args.code_attempt,args.preflight_attempt,args.workspace_qualification)),"WORKSPACE_CLOSED_CONTEXT")
    name=f"implementation/p09/evidence/p09-361-case{args.case}-preparation-workspace-code{args.workspace_qualification:03}.v1.json"
    # Only this bounded construction/testing guard precedes the original stage.
    guard_names,proof=envelope.namespace_bundle.load(c.ROOT,[GUARD_SOURCE],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    guards=guard_names.case160_run007_controller.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();q=None;raw=None
    row=dict(state="FAILED_PREPARATION_WORKSPACE_SETUP_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False)
    try:
        if args.mode=="workspace-code":a.require(not (c.ROOT/name).exists(),"WORKSPACE_EXCLUSIVE_CODE")
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST,chunk.SELF,chunk.TEST,BRIDGE["path"]):q.pin(path)
        a.exact(q.snapshots[BRIDGE["path"]],BRIDGE,"WORKSPACE_EXACT_FROZEN_V2")
        a.exact(q.pin(GUARD_SOURCE["path"]),GUARD_SOURCE,"WORKSPACE_EXACT_FROZEN_GUARDS")
        pin,buffer=q._read(chunk.ORIGINAL_PIN["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,chunk.ORIGINAL_PIN,"WORKSPACE_EXACT_FROZEN_LEAF");raw=bytes(buffer)
        if args.mode=="workspace-code":
            original_test=q.pin(chunk.TEST);own_test=q.pin(TEST)
            tests,proof=envelope.namespace_bundle.load(c.ROOT,[original_test,own_test],
                {"reusable_audit_chunk_v1":chunk,"owned_source_read_pressure":bytes_policy})
            old=tests.test_reusable_audit_chunk_v1
            old.Contracts.setUpClass.__func__.__globals__.update(SOURCE_BYTES=raw,CHECKPOINT=guard.check)
            own=tests.test_successor_preparation_workspace_v1
            own.Tests.setUp.__globals__.update(MODULE=NS(reader_api=reader_api,BRIDGE=BRIDGE,MODES=MODES),
                API=a,CHUNK=chunk,RAW=raw,CHECKPOINT=guard.check)
            suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromModule(old),
                unittest.defaultTestLoader.loadTestsFromModule(own)))
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contracts"]=contracts
            a.exact(contracts,dict(run=17,errors=0,failures=0,skipped=0),"WORKSPACE_ALL_ORIGINAL15_AND_NEW2")
        else:
            qualification=q.json(name)
            a.fields(qualification,dict(state="PASS_PREPARATION_WORKSPACE_CODE_NOT_NATIVE_OR_PRODUCT",
                cleanup_confirmed=True,contracts=dict(run=17,errors=0,failures=0,skipped=0)),"WORKSPACE_CURRENT_CODE")
            for pin in qualification["source_pins"]:a.exact(q.pin(pin["path"]),pin,"WORKSPACE_UNCHANGED_CODE")
        q.finish();guard.check(force=True)
        row.update(state="PASS_PREPARATION_WORKSPACE_CODE_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"WORKSPACE_SETUP_CLEANUP")
    if args.mode=="workspace-code":
        publish(c.ROOT,name,row,a)
        print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
        return 0 if row["state"].startswith("PASS_") else 1
    a.require(row["state"].startswith("PASS_"),"WORKSPACE_SETUP_NOT_READY")
    api,reader_proof=reader_api(a,chunk,raw,name)
    # Same full frozen v2 body in an explicitly pinned private namespace. No
    # default import is hidden or removed; its source joins every real reader.
    frozen,proof=envelope.namespace_bundle.load(c.ROOT,[BRIDGE],{})
    bridge=frozen.current_queue_successor_wire_runtime_v2
    modules,proof=bridge.load(c.ROOT,api,scope,bytes_policy,envelope)
    controller=modules.current_queue_successor_controller
    if args.mode=="code":result=controller.run_code(args.case,args.run,args.attempt)
    elif args.mode=="preflight":result=controller.run_preflight(args.case,args.run,args.code_attempt,args.attempt)
    else:
        dispatch=modules.current_queue_successor_dispatch
        ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.attempt)
        result=dispatch.main(ctx,True)
    # Terminal counters from the actual stage readers, never a synthetic claim.
    # No original receipt is modified; no extra source read or sampler is added.
    rows=[dict(chunk.summary(reader),fresh_inputs=len(reader.snapshots),
        final_fresh_hashes=reader.final_fresh_hashes,actual_read_passes=reader.read_passes,
        actual_bytes_read=reader.bytes_read) for reader in reader_proof["readers"]]
    receipt=f"implementation/p09/evidence/p09-361-case{args.case}-workspace-{args.mode}-run{args.run:03}-attempt{args.attempt:03}.v1.json"
    diagnostic=dict(state="RECORDED_ACTUAL_PREPARATION_WORKSPACE_NOT_PRODUCT_OR_NATIVE",
        stage=args.mode,stage_exit_code=result,readers=rows,source_witnesses_in_original_stage=True,
        original_receipts_modified=False,product_or_Native_executed=False,accepted_count_delta=0)
    publish(c.ROOT,receipt,diagnostic,a)
    print(json.dumps(dict(workspace_receipt=receipt,actual_readers=len(rows),
        readinto_attempts=sum(r["readinto_attempts"] for r in rows),stage_exit_code=result)))
    return result


if __name__=="__main__":raise SystemExit(main())
