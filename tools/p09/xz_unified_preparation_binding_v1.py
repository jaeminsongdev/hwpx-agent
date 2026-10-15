"""Explicit CODE006 metadata binding on the fixed unified v18 entry.

Library dependency, loaded from its complete checked source pin. No Native,
worker, GO, review or acceptance entry. Do not mutate imported modules.
"""
from types import FunctionType,SimpleNamespace as NS
import hashlib
import json
import re
import sys

SELF="tools/p09/xz_unified_preparation_binding_v1.py"
TEST="tools/p09/tests/test_xz_unified_preparation_binding_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CODE=PREFIX+"xz-unified-preparation-binding-code001.v1.json"
STATE="PASS_UNIFIED_CODE006_BINDING8_NOT_PREFLIGHT_DISPATCH_NATIVE_OR_PRODUCT"
ENTRY_PIN=dict(path="tools/p09/xz_unified_runtime_v1.py",bytes=23320,
    sha256="d1daf6cd120e11ea81472aa76d80b6af17afe01a2c1c2b7323bea4daef3a2af9")
WHOLE_CODE=dict(path=PREFIX+"successor-code-run008-attempt006.v1.json",bytes=42447,
    sha256="37f5498907a4edc4adf84717e026c345457a282573a8fa211d40c55c5adfc061")
GRAPH=dict(path=PREFIX+"successor-connections008.v18.json",bytes=57643,
    sha256="c4eee543ebe43d7f3abc657acaa50761d32dadae2dd7d1712605018ddce9859b")
EOF=dict(path=PREFIX+"successor-xz-factory003.v1.json",bytes=72742,
    sha256="7d2c54fec140c5d92b1ed9fa504c3af3b7ba3866d2d72e2908545682b43c4e80")
RECOVERY_CODE=WHOLE_CODE["path"].replace("successor-code-","successor-recovery-code-",1)


def require(ok,label):
    if not ok:raise ValueError("UNIFIED_PREPARATION_BINDING_"+label)


def witnesses(q,a,unified,entry,policy,profile,startup,whole,*,proof):
    # This still checks the exact qualified v17 CODE005 foundation. It is not
    # relabelled as the new CODE006; current execution witnesses follow it.
    unified.witnesses(q,a,entry,policy,profile,startup,whole,code=True)
    for path in (SELF,TEST):q.pin(path)
    a.exact(q.pin(ENTRY_PIN["path"]),ENTRY_PIN,"FIXED_ACTUAL_UNIFIED_ENTRY")
    current=a.read_exact(q,WHOLE_CODE);whole.validate(current,a)
    a.exact(current["runtime_default_import_count"],60,"ACTUAL_NEW_WHOLE_CODE_DEFAULT_HELPERS")
    graph=a.read_exact(q,GRAPH)
    a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
        index=165,pair_count=68,new_ordinary_count=61,preserved_special_count=7,cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"ACTUAL_V18_GRAPH")
    factory=a.read_exact(q,EOF);startup.check_factory(factory,a)
    for record in (current,graph,factory):
        require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"EVERY_REAL_CLOSING_HASH_BOUNDARY")
        for pin in record["source_pins"]:
            if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                a.exact(q.pin(pin["path"]),pin,"EVERY_CURRENT_EXECUTED_PROGRAM")
    if proof:
        own=q.json(CODE)
        a.fields(own,dict(state=STATE,contracts=dict(run=8,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False),"CURRENT_BINDING8")
        require(type(own["fresh_inputs"]) is int and own["fresh_inputs"]==own["final_fresh_hashes"]>0,"BINDING_SOURCE_BOUNDARIES")
        for pin in own["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_BINDING_PROGRAMS")


def adapt(unified):
    require(unified.SELF==ENTRY_PIN["path"] and unified.CODE==PREFIX+"xz-unified-entry-code002.v1.json","ONLY_FIXED_QUALIFIED_ENTRY")
    env=dict(vars(unified),ACTUAL_CODE=WHOLE_CODE["path"],RECOVERY_CODE=RECOVERY_CODE)
    family=unified.build.__globals__
    for name,fn in vars(unified).items():
        if type(fn) is FunctionType and fn.__globals__ is family:
            clone=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
            clone.__kwdefaults__=fn.__kwdefaults__;env[name]=clone
            require(clone.__code__ is fn.__code__ and clone.__closure__ is fn.__closure__,"WHOLE_UNIFIED_FAMILY_RETAINED")
    env["context"]=unified.literal_only(env["context"],"5","6")
    def current(q,a,entry,policy,profile,startup,whole,*,code):
        require(code is True,"ACTUAL_STAGE_REQUIRES_BINDING_PROOF")
        return witnesses(q,a,unified,entry,policy,profile,startup,whole,proof=True)
    env["witnesses"]=current
    return NS(**env)


def invoke(unified,stage,attempt,preflight_attempt=None):
    api=adapt(unified);api.context(stage,attempt,preflight_attempt)
    arguments=["--"+stage,"--attempt",str(attempt)]
    if stage=="qualify":arguments.extend(["--preflight-attempt",str(preflight_attempt)])
    previous=sys.argv
    try:
        sys.argv=[ENTRY_PIN["path"]]+arguments
        return api.recovery_adapter_code()
    finally:sys.argv=previous


def components(c,envelope,unified):
    def dynamic(path):
        raw=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    modules,_=envelope.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=modules.preparation_attributed_entry_v1
    raw,_=envelope.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS+[unified.BASELINE,unified.STARTUP,unified.WHOLE],{})
    raw.prepared_run_closure_v1.configure_host_policy(c)
    profiles,_=envelope.namespace_bundle.load(c.ROOT,[unified.PROFILE_PIN],{})
    profile=unified.profile_shell(profiles.xz_closed_preparation_v1)
    original=raw.preparation_attributed_cpu_v1;baseline=raw.owned_cpu_baseline_v1
    def guarded(base,*,role):return baseline.guard_type(original.guard_type(base,role=role))
    return NS(entry=entry,raw=raw,profile=profile,policy=NS(**{**vars(original),"guard_type":guarded}))


def qualify(c,a,envelope,unified,attempt):
    import io,time,unittest
    require(type(attempt) is int and 1<=attempt<=8,"FINITE_BINDING_CODE")
    output=PREFIX+f"xz-unified-preparation-binding-code{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_BINDING_CODE_RESULT")
    setup=components(c,envelope,unified);entry=setup.entry;raw=setup.raw;policy=setup.policy
    metrics={};phase=dict(value="bootstrap_policy");guards=[];started=time.monotonic()
    old=unified.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),metrics,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return unified.observed_guard(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"),metrics,phase)()
    row=dict(state="FAILED_UNIFIED_CODE006_BINDING_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy);a.exact(q.pin(unified.BASELINE["path"]),unified.BASELINE,"MEASURED_BASELINE")
        def verify(q):
            witnesses(q,a,unified,entry,policy,setup.profile,raw.xz_startup_adapter_v1,raw.xz_whole_code_adapter_v1,proof=False)
            data=(c.ROOT/TEST).read_bytes();pin=dict(path=TEST,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            tests,_=envelope.namespace_bundle.load(c.ROOT,[pin],{})
            suite=tests.test_xz_unified_preparation_binding_v1
            for name,value in dict(MODULE=NS(**globals()),ENTRY=unified,ROOT=c.ROOT).items():
                for cls in vars(suite).values():
                    if type(cls) is type:
                        for fn in vars(cls).values():
                            if type(fn) is FunctionType:fn.__globals__[name]=value
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(suite))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
            a.exact(row["contracts"],dict(run=8,errors=0,failures=0,skipped=0),"ALL_CURRENT_REFERENCE_BINDING8")
        q,proof=entry.closed_bootstrap(c.ROOT,a,old,prep,verify_policy,verify,guards)
        row.update(state=STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_CODE_pin=WHOLE_CODE,actual_graph_pin=GRAPH,actual_EOF_pin=EOF,bootstrap_policy_validation=proof)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        samples=[s for g in guards for s in g.samples]
        row.update(cleanup_confirmed=all(g.cleanup for g in guards),elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_BINDING_CODE_GUARDS_CLOSED")
    raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_errors","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"]==STATE else 1
