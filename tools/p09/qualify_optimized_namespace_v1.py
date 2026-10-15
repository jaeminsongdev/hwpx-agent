"""Qualify private AST-copy routing on actual existing68/failed69 binding.

No Native/worker/product execution; original context8 remains context8.
The optimized worker's EOF and guarded no-product diagnostics are separate.
"""
import sys
from pathlib import Path

SELF="tools/p09/qualify_optimized_namespace_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"


def main():
    import argparse,importlib.util,io,json,re,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import xz_unified_runtime_v1 as unified
    import xz_unified_preparation_binding_v1 as binder
    import receipt_xz_envelope_v1 as xz
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as connection
    import native008_failure_binding_v1 as failed
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f"optimized-namespace-code{attempt:03}.v1.json"
    a.require(not(c.ROOT/output).exists(),"EXCLUSIVE_OPTIMIZED_NAMESPACE_CODE")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None;old=None
    row=dict(state="FAILED_OPTIMIZED_NAMESPACE_CODE_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,whole_successor_scope_or_Native009_qualified=False)
    def tests(name,path):
        spec=importlib.util.spec_from_file_location(name,c.ROOT/path);module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module);return module
    def run(module,count,label):
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        values=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row.setdefault("contract_groups",{})[label]=values
        row.setdefault("contract_failures",[]).extend(dict(group=label,test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures)
        a.exact(values,dict(run=count,errors=0,failures=0,skipped=0),label)
        guard.check()
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,connection.SELF,connection.TEST,cloner.SELF,cloner.TEST,failed.SELF,failed.TEST,"tools/p09/optimized_ready_worker_v1.py"):q.pin(path)
        primitive=tests("optimized_primitive_contracts",cloner.TEST)
        primitive.MODULE=cloner;primitive.ROOT=c.ROOT;primitive.ENVELOPE=envelope;primitive.PIN=q.snapshots[cloner.SELF]
        run(primitive,8,"PRIMITIVE8")
        linked=tests("optimized_copy_connection_contracts",connection.TEST)
        linked.MODULE=connection;linked.CANDIDATE=cloner;linked.ORIGINAL=envelope.namespace_bundle;linked.ROOT=c.ROOT
        run(linked,8,"COPY_CONNECTION8")
        loader,proof=connection.connect(envelope.namespace_bundle,cloner)
        proxy=connection.envelope(envelope,loader)
        old=failed.existing(c,a,proxy,unified,binder,scope,bytes_policy,guard)
        admitted=failed.admission(q,a,producer)
        aliases=tests("optimized_failed_alias_contracts",failed.TEST)
        aliases.MODULE=failed;aliases.ADMITTED=admitted;aliases.FOUNDATION=old;aliases.XZ=xz
        aliases.SCOPE=scope;aliases.CHECKPOINT=guard.check
        aliases.CARRIER=bytes(q._read(failed.PHYSICAL["path"],parse=True)[1])
        run(aliases,12,"ACTUAL_FAILED_ALIAS12");aliases.CARRIER=None
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        old.reader.finish();q.finish();guard.check(force=True)
        row.update(state="PASS_OPTIMIZED_NAMESPACE28_ON_ACTUAL_BINDING_NOT_WORKER_OR_NATIVE009",
            contracts=28,namespace_connection_proof=proof,old_foundation_preparation_context=8,
            old_foundation_source_pins=list(old.reader.snapshots.values()),old_foundation_fresh=len(old.reader.snapshots),old_foundation_final=old.reader.final_fresh_hashes,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_whole69_binding_tested_with_original_oracles=True,original_default_modules_mutated=False,
            optimized_worker_or_parent_readiness_executed=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"OPTIMIZED_NAMESPACE_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_groups","contract_failures","old_foundation_fresh","old_foundation_final",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
