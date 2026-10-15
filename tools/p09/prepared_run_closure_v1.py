"""Preparation-only predecessor closure, not a fabricated Native receipt.

Original Native/failed-graph checks remain for every other run. Closure requires
actual Native absence, unchanged prepared packets and fresh EOF/NO-GO startup.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import re
import sys

# Legacy v4 intentionally rewrites generic SELF/TEST globals on installed
# functions. Producer witnesses are separate authority, not role metadata.
CLOSURE_SOURCE="tools/p09/prepared_run_closure_v1.py"
CLOSURE_TEST="tools/p09/tests/test_prepared_run_closure_v1.py"
ENTRY=dict(path="tools/p09/level6_closed_preparation_v1.py",bytes=24229,
    sha256="7caea0f722b6205ad9691d35ff217e9c299da490ad2c22dfe98e1300367c55eb")
OLD=dict(path="tools/p09/expanded_closed_preparation_v1.py",bytes=21675,
    sha256="8de7dc45657401ceefc05a8535114155da138f79d3d17a9c6f2491808e43fca1")
PREFIX="implementation/p09/evidence/p09-361-case165-"
STATE="PASS_PREPARATION_ONLY_CLOSED_WITHOUT_NATIVE_NOT_RUNTIME_OR_PRODUCT"


def require(ok,label):
    if not ok:raise ValueError("PREPARED_RUN_CLOSURE_"+label)


def configure_host_policy(c):
    """Configure this parent process; do not rewrite the frozen shared source.

    The parent owns the sole host sampler/Job supervisor. Workers inherit the
    same CPU/Job limits and have no separate host-RAM admission loop here.
    Update the shared dict in place so already-bound guard imports agree.
    """
    before=dict(c.POLICY)
    baseline=dict(profile="P149_OWNED_WORKLOAD_V4_PARTITIONED_TEST_CODEGEN",
        start_ram_min_percent=10,stop_ram_min_percent=8)
    selected=dict(profile="P149_OWNED_WORKLOAD_V5_HOST_RAM_95_PERCENT",
        start_ram_min_percent=5,stop_ram_min_percent=5)
    require({k:before.get(k) for k in baseline} in (baseline,selected),"KNOWN_HOST_POLICY_PROFILE")
    protected=dict(logical_cpu_limit=1,priority="BelowNormal",sample_seconds=.5,
        emergency_cpu_percent=98,emergency_cpu_consecutive_samples=4,
        stop_commit_used_percent=95,job_memory_limit_percent=8,job_memory_stop_percent=7)
    require(all(type(before.get(k)) is type(v) and before[k]==v for k,v in protected.items()),"UNCHANGED_CPU_COMMIT_JOB_LIMITS")
    c.POLICY.update(selected)
    require(c.POLICY==dict(before,**selected),"ONLY_THREE_HOST_PROFILE_SETTINGS")
    return dict(c.POLICY)


def one_run(fn,run):
    require(type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_")
        and type(run) is int and 2<=run<=8,"PRIVATE_ORIGINAL_RETRY_BODY")
    if run==2:return fn
    constants=fn.__code__.co_consts
    require(sum(type(v) is int and v==2 for v in constants)==1
        and not any(type(v) is int and v==run for v in constants),"ONE_UNAMBIGUOUS_RANGE_START")
    code=fn.__code__.replace(co_consts=tuple(run if type(v) is int and v==2 else v for v in constants))
    inverse=code.replace(co_consts=tuple(2 if type(v) is int and v==run else v for v in code.co_consts))
    require(inverse==fn.__code__,"ENTIRE_RETRY_RANGE_CODE_INVERSE")
    result=FunctionType(code,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def validate(row,index,run,a):
    require(type(index) is int and index==165 and type(run) is int and 4<=run<=7,"EXACT_PREPARATION_CONTEXT")
    a.fields(row,dict(state=STATE,index=index,physical_run=run,cleanup_confirmed=True,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,
        actual_Native_absent_before=True,actual_Native_absent_after=True,source_profile_version="v9"),"EXACT_PREPARATION_ONLY_CLOSURE")
    require(type(row["fresh_inputs"]) is int and row["fresh_inputs"]==row["final_fresh_hashes"]>0,"COMPLETE_CLOSING_HASHES")
    a.fields(row["no_go_probe"],dict(exit_code=1,original_GO_rejection_observed=True,
        historical_runtime_or_authority_opens=0,GO_sent=False,product_child_execution_authorized=False),"ACTUAL_NO_GO_NOT_DECLARED_INTENT")
    expected=OLD if run==4 else ENTRY
    a.exact(row["worker_entry_pin"],expected,"EXACT_READONLY_LEGACY_WORKER_SOURCE")
    require(row["graph_pin"]["path"]==PREFIX+f"successor-connections{run:03}.v9.json"
        and row["capsule_pin"]["path"]==PREFIX+f"successor-worker-capsule{run:03}.compact.v9.json"
        and row["bootstrap_pin"]["path"]==PREFIX+f"successor-worker-bootstrap{run:03}.v9.json","EXACT_PREPARED_PACKET_PATHS")


def absent(q,path):
    q.checkpoint();target=q.root/path
    for parent in (target.parent,*target.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_ABSENCE_ANCESTORS")
        if parent==q.root:break
    try:target.lstat()
    except FileNotFoundError:return True
    return False


def producer_inventory(row):
    inventory={p["path"]:p for p in row["source_pins"]}
    require(CLOSURE_SOURCE in inventory and CLOSURE_TEST in inventory,"PRODUCER_SOURCE_WITNESSES")
    return inventory


def admit(q,ctx,run,a):
    root=PREFIX+f"current-runtime-run{run:03}.v1.json"
    require(absent(q,root),"NATIVE_ABSENT_BEFORE_CLOSURE_ADMISSION")
    name=PREFIX+f"prepared-only-closure-run{run:03}-attempt005.v1.json"
    row=q.json(name);validate(row,ctx.index,run,a)
    inventory=producer_inventory(row)
    # Historical graph program pins need not equal today's source: no historical
    # Native run is claimed. The closure producer and packet bytes must match.
    for path in (CLOSURE_SOURCE,CLOSURE_TEST,row["worker_entry_pin"]["path"]):
        a.exact(q.pin(path),inventory[path],"CURRENT_CLOSURE_AND_WORKER_SOURCE")
    graph=a.read_exact(q,row["graph_pin"])
    a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
        index=165,product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,cleanup_confirmed=True),"REAL_PREPARED_GRAPH")
    a.exact(graph["capsule_pin"],row["capsule_pin"],"SAME_PREPARED_WIRE")
    a.exact(q.pin(row["capsule_pin"]["path"]),row["capsule_pin"],"UNCHANGED_PREPARED_WIRE_BYTES")
    a.exact(q.pin(row["bootstrap_pin"]["path"]),row["bootstrap_pin"],"UNCHANGED_PREPARED_BOOTSTRAP_BYTES")
    require(absent(q,root),"NATIVE_ABSENT_AFTER_CLOSURE_ADMISSION")


def install_retry(namespace,a):
    original=namespace.previous_stops
    def previous_stops(q,ctx,api,bridge):
        for run in range(2,ctx.run):
            root=f"implementation/p09/evidence/p09-361-case{ctx.index}-current-runtime-run{run:03}.v1.json"
            closure=PREFIX+f"prepared-only-closure-run{run:03}-attempt005.v1.json"
            if ctx.index==165 and 4<=run<=7 and absent(q,root) and not absent(q,closure):
                admit(q,ctx,run,api)
            else:
                # Same original predicates for existing Native and unresolved
                # failed graphs; only range metadata narrows this one call.
                one_run(original,run)(q,NS(**{**vars(ctx),"run":run+1}),api,bridge)
    original.__globals__["previous_stops"]=previous_stops;namespace.previous_stops=previous_stops


def main():
    import argparse,io,json,os,subprocess,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    active_host_policy=configure_host_policy(c)
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    parser.add_argument("--closure-code",action="store_true");parser.add_argument("--close-run",type=int)
    parser.add_argument("--closure-attempt",type=int,default=5)
    args,remainder=parser.parse_known_args()
    if args.closure_code or args.close_run is not None:
        # Publication-only dependencies must not enlarge the production graph.
        # Forwarded CODE/preflight/qualification/Native retain their own exact
        # dependencies and full source witnesses; no sys.modules mutation.
        import terminal_metadata_pressure_v1 as pressure
        import distinct_final_sample_guard_v1 as distinct
        import successor_preparation_workspace_v1 as publisher
        require(not remainder and 1<=args.closure_attempt<=8,"EXCLUSIVE_PRODUCER_MODE")
        run=args.close_run
        require(args.closure_code or type(run) is int and 4<=run<=7,"BOUNDED_CLOSED_RUN")
        output=PREFIX+(f"prepared-closure-code{args.closure_attempt:03}.v1.json" if args.closure_code else
            f"prepared-only-closure-run{run:03}-attempt{args.closure_attempt:03}.v1.json")
        require(not(c.ROOT/output).exists(),"EXCLUSIVE_CLOSURE_RECEIPT")
        guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic();q=None
        row=dict(state="FAILED_PREPARED_ONLY_CLOSURE_NOT_ADOPTED",index=165,physical_run=run,
            product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
            host_resource_policy=active_host_policy)
        try:
            guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            for path in (CLOSURE_SOURCE,CLOSURE_TEST):q.pin(path)
            if args.closure_code:
                tests,_=envelope.namespace_bundle.load(c.ROOT,[q.snapshots[CLOSURE_TEST]],{})
                tests.test_prepared_run_closure_v1.Tests.data.__globals__.update(MODULE=sys.modules[__name__],API=a)
                result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests.test_prepared_run_closure_v1))
                contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped));row["contracts"]=contracts
                a.exact(contracts,dict(run=9,errors=0,failures=0,skipped=0),"ALL_CLOSURE9")
                row["state"]="PASS_PREPARED_ONLY_CLOSURE_CODE9_NOT_ENTRY_NATIVE_OR_PRODUCT"
            else:
                code=q.json(PREFIX+"prepared-closure-code006.v1.json")
                a.fields(code,dict(state="PASS_PREPARED_ONLY_CLOSURE_CODE9_NOT_ENTRY_NATIVE_OR_PRODUCT",
                    contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                    host_resource_policy=active_host_policy),"QUALIFIED_CLOSURE_CODE9")
                for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CLOSURE_CODE")
                root=PREFIX+f"current-runtime-run{run:03}.v1.json";require(absent(q,root),"NATIVE_MUST_ACTUALLY_BE_ABSENT")
                graph_name=PREFIX+f"successor-connections{run:03}.v9.json";graph=q.json(graph_name)
                a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
                    index=165,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"ACTUAL_OLD_PREPARED_GRAPH")
                capsule=graph["capsule_pin"];hint_name=PREFIX+f"successor-worker-bootstrap{run:03}.v9.json"
                a.exact(q.pin(capsule["path"]),capsule,"OLD_PREPARED_WIRE_BYTES")
                hint=q.json(hint_name);a.exact(hint["capsule_pin"],capsule,"SAME_OLD_BOOTSTRAP_WIRE")
                worker=OLD if run==4 else ENTRY;a.exact(q.pin(worker["path"]),worker,"PINNED_CLOSURE_WORKER")
                program="""import json,os,re,sys
sys.path.insert(0,'tools/p09')
hits=[]
def audit(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
  name=os.fsdecode(os.fspath(args[0])).replace('\\\\','/').rsplit('/',1)[-1]
  if re.fullmatch(r'p09-361-case[0-9]{3}-current-(?:runtime-run[0-9]{3}|epoch-accept[0-9]{3})\\.v1\\.json',name):hits.append(1)
sys.addaudithook(audit)
import conservative_maintenance as c
c.Windows()
import flat_current_queue_envelope_runtime_v25 as e
pin=json.loads(sys.argv[1]);run=int(sys.argv[2]);modules,proof=e.namespace_bundle.load(c.ROOT,[pin],{})
module=getattr(modules,pin['path'].rsplit('/',1)[-1][:-3])
if run!=4:module.main.__globals__['VERSION']='v9'
sys.argv=[pin['path'],'--owned-worker','--task',f'case165-current-r{run:03}-tests']
try:module.main()
finally:print(json.dumps({'historical_runtime_or_authority_opens':len(hits)}))
"""
                guard.check(force=True)
                child=subprocess.run([sys.executable,"-B","-c",program,json.dumps(worker),str(run)],input="",text=True,
                    capture_output=True,encoding="utf-8",errors="replace",timeout=15,cwd=c.ROOT,
                    creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
                guard.check(force=True)
                require(len(child.stdout.encode())<=4096 and len(child.stderr.encode())<=16384,"BOUNDED_NO_GO_OUTPUT")
                audit=json.loads(child.stdout.strip())
                require(child.returncode==1 and "WORKER_NOT_AUTHORIZED" in child.stderr,"ORIGINAL_EOF_GO_REJECTION")
                a.exact(audit,dict(historical_runtime_or_authority_opens=0),"NO_HISTORICAL_WORKER_IO")
                require(absent(q,root),"NATIVE_ABSENCE_AFTER_PROBE")
                row.update(state=STATE,worker_entry_pin=worker,source_profile_version="v9",graph_pin=q.snapshots[graph_name],
                    capsule_pin=capsule,bootstrap_pin=q.snapshots[hint_name],actual_Native_absent_before=True,actual_Native_absent_after=True,
                    no_go_probe=dict(exit_code=child.returncode,original_GO_rejection_observed=True,historical_runtime_or_authority_opens=0,
                        GO_sent=False,product_child_execution_authorized=False),new_canonical_Native_receipt_created=False)
            q.finish();guard.check(force=True)
            row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.TimeoutExpired) as error:
            row["error_type"]=type(error).__name__
            if error.args and isinstance(error.args[0],str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
        finally:
            guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
                CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
        require(guard.cleanup,"PRODUCER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
        print(json.dumps({k:row.get(k) for k in ("state","physical_run","contracts","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
        return 0 if row["state"].startswith("PASS_") else 1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[ENTRY],{})
    entry=raw.level6_closed_preparation_v1;original_profile=entry.loader_profile
    def profile(root,loader,core,api,prior_alias):
        base=original_profile(root,loader,core,api,prior_alias)
        def load(*items,**kwargs):
            modules,proof=base.load(*items,**kwargs)
            v5=getattr(modules,"current_queue_sealed_metadata_runtime_v5",None)
            if v5 is not None:
                original_paths=v5.retry_paths
                def retry_paths(raw,namespace,pin):
                    original_paths(raw,namespace,pin);install_retry(namespace,api)
                v5.retry_paths=retry_paths;original_paths.__globals__["retry_paths"]=retry_paths
            fix=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
            if fix is not None:
                original=fix.load
                def connected(*args,**options):
                    values=list(args);a0=values[1]
                    class Reader(a0.AcceptanceReader):
                        def __init__(self,*args,**kwargs):
                            super().__init__(*args,**kwargs)
                            for name in (CLOSURE_SOURCE,CLOSURE_TEST):self.pin(name)
                            code=self.json(PREFIX+"prepared-closure-code006.v1.json")
                            api.fields(code,dict(state="PASS_PREPARED_ONLY_CLOSURE_CODE9_NOT_ENTRY_NATIVE_OR_PRODUCT",
                                contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                                host_resource_policy=active_host_policy),"CURRENT_CLOSURE_ADAPTER_CODE")
                            for pin in code["source_pins"]:api.exact(self.pin(pin["path"]),pin,"CURRENT_CLOSURE_ADAPTER_SOURCE")
                    values[1]=NS(**{**vars(a0),"AcceptanceReader":Reader})
                    return original(*values,**options)
                fix.load=connected
            return modules,proof
        return NS(**{**vars(base),"load":load})
    entry.main.__globals__["loader_profile"]=profile
    sys.argv=[ENTRY["path"]]+remainder
    return entry.main()


if __name__=="__main__":raise SystemExit(main())
