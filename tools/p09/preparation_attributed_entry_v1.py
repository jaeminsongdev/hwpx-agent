"""Explicit preparation-only CPU connection on the frozen recovery entry.

No Native/worker/product entry. Default and historical namespaces stay intact.
CODE/probe sources are freshly closed before adoption, then again in every
original stage reader. Whole frozen preparation and source checks remain.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

ENTRY_SOURCE="tools/p09/preparation_attributed_entry_v1.py"
ENTRY_TEST="tools/p09/tests/test_preparation_attributed_entry_v1.py"
SELF=ENTRY_SOURCE
TEST=ENTRY_TEST
PREFIX="implementation/p09/evidence/p09-361-case165-"
ENTRY=dict(path="tools/p09/prepared_run_closure_v1.py",bytes=23900,
    sha256="c159da53076f5bb88dce252db163f82a1f1d71522c9dd248349ca615dc84e672")
POLICY_SOURCE=dict(path="tools/p09/preparation_attributed_cpu_v1.py",bytes=9869,
    sha256="ddc1b48f17645337e65125373d9db822477ca6a94cc34e23992498e6c2c7d13d")
POLICY_CODE=PREFIX+"preparation-attributed-CPU-design-code001.v1.json"
PROBE=PREFIX+"preparation-attributed-CPU-probe001.v1.json"
CONNECTION_STATE="PASS_PREPARATION_ATTRIBUTED_CONNECTION_CODE_NOT_NATIVE_OR_STAGE_EXECUTION"
UTIL_PINS=[
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3"),
    dict(path="tools/p09/successor_preparation_workspace_v1.py",bytes=9656,sha256="003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98")]


def require(ok,label):
    if not ok:raise ValueError("PREPARATION_ENTRY_"+label)


def context(arguments):
    require(type(arguments) is list and all(type(v) is str for v in arguments),"EXPLICIT_ARGUMENTS")
    forbidden=("--native","--owned-worker","--task","--review","--accept","--graph","--bootstrap","--code")
    require(not any(v.split("=",1)[0] in forbidden for v in arguments),"NO_NATIVE_PRODUCT_WORKER_OR_ACCEPT_ENTRY")
    modes=[v for v in arguments if v in ("--preflight","--qualify")]
    require(len(modes)==1,"ONE_PREPARATION_MODE")
    values={}
    for flag in ("--case","--run","--attempt","--code-attempt"):
        require(arguments.count(flag)==1 and arguments.index(flag)+1<len(arguments),"EXACT_PREPARATION_FLAGS")
        raw=arguments[arguments.index(flag)+1]
        require(raw.isascii() and raw.isdecimal(),"INTEGER_PREPARATION_VALUE");values[flag]=int(raw)
    require(values["--case"]==165 and values["--run"]==8 and 1<=values["--attempt"]<=8
        and values["--code-attempt"]==1,"ONLY_CURRENT165_RUN008_QUALIFIED_CODE1")
    if modes[0]=="--qualify":
        require(arguments.count("--preflight-attempt")==1 and arguments.index("--preflight-attempt")+1<len(arguments),"EXPLICIT_QUALIFICATION_PREFLIGHT")
        value=arguments[arguments.index("--preflight-attempt")+1]
        require(value.isascii() and value.isdecimal() and 1<=int(value)<=8,"BOUNDED_QUALIFICATION_PREFLIGHT")
        values["--preflight-attempt"]=int(value)
    return NS(role="whole_metadata_preflight" if modes[0]=="--preflight" else "dispatch_construction",
        stage="preflight" if modes[0]=="--preflight" else "qualify",attempt=values["--attempt"],values=values)


def closure(q,path,state,a,contracts=None):
    record=q.json(path);expected=dict(state=state,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False)
    if contracts is not None:expected["contracts"]=dict(run=contracts,errors=0,failures=0,skipped=0)
    a.fields(record,expected,"CURRENT_PREPARATION_POLICY_CLOSURE")
    require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"COMPLETE_POLICY_SOURCE_CLOSURE")
    for pin in record["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_PREPARATION_POLICY_SOURCES")
    return record


def connection_path(attempt):
    require(type(attempt) is int and 1<=attempt<=8,"EXPLICIT_BOUNDED_CONNECTION_RECEIPT")
    return PREFIX+f"preparation-attributed-connection-code{attempt:03}.v1.json"


def witnesses(q,a,policy,*,connection=True,connection_attempt=None):
    for path in (ENTRY_SOURCE,ENTRY_TEST):q.pin(path)
    a.exact(q.pin(ENTRY["path"]),ENTRY,"ORIGINAL_RECOVERY_ENTRY_UNCHANGED")
    a.exact(q.pin(POLICY_SOURCE["path"]),POLICY_SOURCE,"EXACT_POLICY_DESIGN_SOURCE")
    design=closure(q,POLICY_CODE,policy.CODE_STATE,a,20)
    a.fields(design,dict(runtime_policy_installed=False,next_preflight_start_authorized=False),"DESIGN_NOT_AUTOMATIC_ADOPTION")
    probe=closure(q,PROBE,"PASS_CONTROLLED_PREPARATION_CPU_GUARD_SOURCE_READS_NOT_RUNTIME_INSTALLATION",a)
    a.fields(probe,dict(runtime_policy_installed=False,actual_Native_or_product_executed=False,
        actual_P09_preflight_executed=False,subprocess_construction_blocked=True,Native008_absent_before_after=True),"CONTROLLED_NO_CHILD_PROBE")
    if connection:closure(q,connection_path(connection_attempt),CONNECTION_STATE,a,13)


def preflight_audit(q,a,policy,attempt):
    name=PREFIX+f"preparation-attributed-preflight-run008-attempt{attempt:03}.v1.json"
    row=q.json(name)
    a.fields(row,dict(state="RECORDED_PREPARATION_CPU_POLICY_NOT_NATIVE_OR_ACCEPTANCE",stage="preflight",
        original_stage_exit_code=0,accepted_count_delta=0,GO_authorized=False,
        actual_Native_or_product_executed=False,Native008_absent_before_after=True,cleanup_confirmed=True),"ACTUAL_PREPARATION_POLICY_AUDIT")
    target=PREFIX+f"successor-recovery-preflight-run008-attempt{attempt:03}.v1.json"
    require(row["original_stage_record_pin"]["path"]==target,"EXACT_PREPARATION_AUDIT_TARGET")
    a.exact(q.pin(target),row["original_stage_record_pin"],"UNCHANGED_AUDITED_PREFLIGHT")
    require(type(row["bootstrap_fresh_inputs"]) is int and row["bootstrap_fresh_inputs"]==row["bootstrap_final_fresh_hashes"]>0,"CLOSED_AUDIT_BOOTSTRAP_SOURCES")
    for pin in row["bootstrap_source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_AUDITED_CONNECTION_SOURCES")
    require(type(row["guard_summaries"]) is list and bool(row["guard_summaries"]),"ACTUAL_PREPARATION_GUARDS")
    for summary in row["guard_summaries"]:
        a.fields(summary,dict(profile=policy.PROFILE,role="whole_metadata_preflight",policy=policy.POLICY,
            stopped=False,Native_policy_changed=False,GO_authorized=False,
            original_hard_guard_and_RAM_commit_deadline_required=True),"PREPARATION_GUARD_NOT_NATIVE_OR_STOPPED")
    return row


def pressure_facade(original,policy,role,instances):
    def guard_type(base):
        revised=policy.guard_type(base,role=role)
        class Guard(revised):
            def __init__(self):
                super().__init__();require(len(instances)<16,"BOUNDED_SERIAL_PREPARATION_GUARDS");instances.append(self)
        return Guard
    return NS(**{**vars(original),"guard_type":guard_type,"summary":lambda guard:guard.preparation_CPU.summary()})


def connect_old(old,policy,role,instances):
    pressure=pressure_facade(old.base.FIRST.terminal_metadata_pressure_v1,policy,role,instances)
    first=NS(**{**vars(old.base.FIRST),"terminal_metadata_pressure_v1":pressure})
    return NS(**{**vars(old),"base":NS(**{**vars(old.base),"FIRST":first})})


def bind_envelope(namespace,envelope):
    name=getattr(namespace,"__name__",None)
    if type(name) is not str or not name.startswith("p09_exact_"):return
    for key,fn in tuple(vars(namespace).items()):
        if type(fn) is not FunctionType or fn.__globals__.get("__name__")!=name:continue
        prior=fn.__builtins__["__import__"]
        def imports(target,globals=None,locals=None,fromlist=(),level=0,previous=prior):
            if target=="flat_current_queue_envelope_runtime_v25" and level==0:return envelope
            return previous(target,globals,locals,fromlist,level)
        env=fn.__globals__;env["__builtins__"]={**fn.__builtins__,"__import__":imports}
        revised=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
        revised.__kwdefaults__=fn.__kwdefaults__
        if env.get(key) is fn:env[key]=revised
        setattr(namespace,key,revised)


def route_loader(root,original,policy,a,role,instances,*,require_connection=True,connection_attempt=None,audit_attempt=None,envelope=None):
    def load(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        pressure=getattr(modules,"terminal_metadata_pressure_v1",None)
        if pressure is not None:
            revised=pressure_facade(pressure,policy,role,instances)
            modules.terminal_metadata_pressure_v1=revised
        old=getattr(modules,"case160_run007_controller",None)
        if old is not None:
            revised=connect_old(old,policy,role,instances)
            for fn in vars(old).values():
                if type(fn) is FunctionType and fn.__globals__.get("__name__")==old.__name__:
                    fn.__globals__["base"]=revised.base
            old.base=revised.base
        entry=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            whole=entry.load
            def connected(*items,**options):
                values=list(items);api=values[1]
                class Reader(api.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs);witnesses(self,a,policy,connection=require_connection,connection_attempt=connection_attempt)
                        if audit_attempt is not None:preflight_audit(self,a,policy,audit_attempt)
                values[1]=NS(**{**vars(api),"AcceptanceReader":Reader})
                return whole(*values,**options)
            entry.load=connected
        if proxy is not None:
            for namespace in vars(modules).values():bind_envelope(namespace,proxy)
        return modules,proof
    routed=NS(**{**vars(original),"load":load})
    proxy=None if envelope is None else NS(**{**vars(envelope),"namespace_bundle":routed})
    return routed


def execute(entry,envelope,arguments):
    original=entry.main;prior=original.__builtins__["__import__"]
    def imports(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:return envelope
        return prior(name,globals,locals,fromlist,level)
    env=dict(original.__globals__,__builtins__={**original.__builtins__,"__import__":imports})
    connected=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    connected.__kwdefaults__=original.__kwdefaults__
    require(connected.__code__ is original.__code__,"ENTIRE_ORIGINAL_PREPARATION_ENTRY")
    previous=sys.argv
    try:sys.argv=[ENTRY["path"]]+arguments;return connected()
    finally:sys.argv=previous


def main():
    import argparse,hashlib,io,json,re,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    raw,_=envelope.namespace_bundle.load(c.ROOT,[ENTRY,POLICY_SOURCE]+UTIL_PINS,{})
    entry=raw.prepared_run_closure_v1;policy=raw.preparation_attributed_cpu_v1
    host_policy=entry.configure_host_policy(c)
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument("--connection-code",action="store_true")
    parser.add_argument("--connection-attempt",type=int);args,remainder=parser.parse_known_args()
    require(sys.argv[1:].count("--connection-attempt")==1,"EXPLICIT_SINGLE_CONNECTION_ATTEMPT")
    connection_record=connection_path(args.connection_attempt)
    old=raw.terminal_metadata_pressure_v1;distinct=raw.distinct_final_sample_guard_v1
    publisher=raw.successor_preparation_workspace_v1
    guard=old.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic();instances=[]
    if args.connection_code:
        require(not remainder,"EXCLUSIVE_CONNECTION_QUALIFICATION")
        output=connection_record
        require(not(c.ROOT/output).exists(),"EXCLUSIVE_CONNECTION_RECORD")
        record=dict(state="FAILED_PREPARATION_CONNECTION_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,
            actual_Native_or_product_executed=False,host_resource_policy=host_policy)
        try:
            guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);witnesses(q,a,policy,connection=False)
            from tests import test_preparation_attributed_entry_v1 as tests
            tests.MODULE=sys.modules[__name__];tests.POLICY=policy;tests.ENTRY_MODULE=entry;tests.ENVELOPE=envelope
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            record["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(record["contracts"],dict(run=13,errors=0,failures=0,skipped=0),"ALL_CONNECTION13")
            for module in tuple(sys.modules.values()):
                filename=getattr(module,"__file__",None)
                if filename and Path(filename).absolute().is_relative_to(c.ROOT/"tools/p09"):
                    q.pin(Path(filename).absolute().relative_to(c.ROOT).as_posix())
            q.finish();guard.check(force=True)
            record.update(state=CONNECTION_STATE,source_pins=list(q.snapshots.values()),
                fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            record["error_type"]=type(error).__name__
            if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):record["error_code"]=error.args[0]
        finally:
            guard.close();record.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
                CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
                RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
        require(guard.cleanup,"CONNECTION_CODE_CLEANUP");publisher.publish(c.ROOT,output,record,a)
        print(json.dumps({k:record.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
        return 0 if record["state"]==CONNECTION_STATE else 1
    ctx=context(remainder)
    root_name=PREFIX+"current-runtime-run008.v1.json"
    def absent():
        try:(c.ROOT/root_name).lstat()
        except FileNotFoundError:return True
        return False
    require(absent(),"NO_EXISTING_NATIVE008")
    # Fresh qualification still uses the unchanged 75% baseline guard.
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);witnesses(q,a,policy,connection_attempt=args.connection_attempt)
        if ctx.stage=="qualify":preflight_audit(q,a,policy,ctx.values["--preflight-attempt"])
        q.finish();guard.check(force=True)
    finally:guard.close()
    require(guard.cleanup,"PREPARATION_BOOTSTRAP_CLEANUP")
    audit=PREFIX+f"preparation-attributed-{ctx.stage}-run008-attempt{ctx.attempt:03}.v1.json"
    require(not(c.ROOT/audit).exists(),"EXCLUSIVE_POLICY_STAGE_AUDIT")
    routed=route_loader(c.ROOT,envelope.namespace_bundle,policy,a,ctx.role,instances,
        connection_attempt=args.connection_attempt,
        audit_attempt=ctx.values["--preflight-attempt"] if ctx.stage=="qualify" else None,envelope=envelope)
    proxy=NS(**{**vars(envelope),"namespace_bundle":routed})
    code=execute(entry,proxy,remainder)
    require(absent() and instances and all(g.cleanup for g in instances),"NO_NATIVE_AND_ALL_STAGE_GUARDS_CLOSED")
    target=PREFIX+(f"successor-recovery-preflight-run008-attempt{ctx.attempt:03}.v1.json" if ctx.stage=="preflight" else
        f"successor-recovery-dispatch-qualification-run008-attempt{ctx.attempt:03}.v1.json")
    target_pin=None
    if (c.ROOT/target).is_file():
        data=(c.ROOT/target).read_bytes();target_pin=dict(path=target,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    publisher.publish(c.ROOT,audit,dict(state="RECORDED_PREPARATION_CPU_POLICY_NOT_NATIVE_OR_ACCEPTANCE",
        stage=ctx.stage,original_stage_exit_code=code,original_stage_record_pin=target_pin,
        accepted_count_delta=0,GO_authorized=False,actual_Native_or_product_executed=False,
        Native008_absent_before_after=True,cleanup_confirmed=True,
        guard_summaries=[g.preparation_CPU.summary() for g in instances],
        bootstrap_source_pins=list(q.snapshots.values()),bootstrap_fresh_inputs=len(q.snapshots),
        bootstrap_final_fresh_hashes=q.final_fresh_hashes),a)
    print(json.dumps(dict(preparation_policy_audit=audit,original_stage_exit_code=code,guards=len(instances))))
    return code


if __name__=="__main__":raise SystemExit(main())
