"""Whole original Native entry on the fixed unified worker and CODE006.

Explicit source-pinned library, never a hidden/default module replacement.
Preparation uses its qualified policy; Native keeps the original Guard. No
review/acceptance entry or automatic retry after original Native invocation.
"""
from types import FunctionType,SimpleNamespace as NS
import hashlib
import json
import math
import re
import sys

SELF="tools/p09/xz_unified_native_entry_v1.py"
TEST="tools/p09/tests/test_xz_unified_native_entry_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CODE=PREFIX+"xz-unified-native-entry-code001.v1.json"
STATE="PASS_UNIFIED_NATIVE_WIRING12_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE"
BINDING=dict(path="tools/p09/xz_unified_preparation_binding_v1.py",bytes=9473,
    sha256="0759a9aa7d2f81190340cdcdd22000966612d93011e025b64837dada26bee74f")


def require(ok,label):
    if not ok:raise ValueError("UNIFIED_NATIVE_ENTRY_"+label)


def native_arguments(preflight,qualification):
    require(type(preflight) is int and preflight in (15,16) and type(qualification) is int and qualification==8,"ONLY_FINAL_CURRENT_METADATA_REFERENCES")
    return ["--native","--case","165","--run","8","--attempt","1","--code-attempt","6",
        "--preflight-attempt",str(preflight),"--qualification-attempt",str(qualification)]


def absent(root):
    path=root/(PREFIX+"current-runtime-run008.v1.json")
    require(not path.exists() and not path.is_symlink() and not path.is_junction(),"NO_EXISTING_NATIVE008")


def no_previous_intent(root):
    for attempt in range(1,9):
        require(not(root/(PREFIX+f"xz-unified-native-invocation{attempt:03}.intent.v1.json")).exists(),"NO_RETRY_AFTER_NATIVE_INVOCATION_INTENT")


def witnesses(q,a,unified,binding,entry,policy,profile,startup,whole,*,proof):
    binding.witnesses(q,a,unified,entry,policy,profile,startup,whole,proof=True)
    for path in (SELF,TEST):q.pin(path)
    a.exact(q.pin(BINDING["path"]),BINDING,"UNCHANGED_CODE006_PREPARATION_BINDING")
    if proof:
        record=q.json(CODE)
        a.fields(record,dict(state=STATE,contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            Native_policy_changed=False,product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False),"WHOLE_NATIVE_WIRING12")
        require(type(record["fresh_inputs"]) is int and record["fresh_inputs"]==record["final_fresh_hashes"]>0,"NATIVE_ADAPTER_SOURCE_BOUNDARIES")
        for pin in record["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_NATIVE_ADAPTER_PROGRAMS")


def preparation_api(unified,binding):
    api=binding.adapt(unified)
    def current(q,a,entry,policy,profile,startup,whole,*,code):
        require(code is True,"PREPARATION_REQUIRES_NATIVE_WIRING_PROOF")
        return witnesses(q,a,unified,binding,entry,policy,profile,startup,whole,proof=True)
    # The callable's live owner is the whole entry, not the earlier wrapper.
    api.recovery_adapter_code.__globals__["witnesses"]=current;api.witnesses=current
    return api


def prepare(unified,binding,stage,attempt,preflight=None):
    require((stage=="preflight" and attempt in (15,16) and preflight is None) or
        (stage=="qualify" and type(attempt) is int and attempt==8 and preflight in (15,16)),"FINAL_PREPARATION_ONLY")
    api=preparation_api(unified,binding);api.context(stage,attempt,preflight)
    arguments=["--"+stage,"--attempt",str(attempt)]
    if stage=="qualify":arguments.extend(["--preflight-attempt",str(preflight)])
    previous=sys.argv
    try:
        sys.argv=[unified.SELF]+arguments
        return api.recovery_adapter_code()
    finally:sys.argv=previous


def build_native(root,envelope,a,unified,binding,setup,*,witness):
    """Keep the frozen entire Native body; route only explicit dependencies."""
    base_guard=a.Guard;entry=setup.entry;closure=setup.raw.prepared_run_closure_v1
    current=setup.profile.connect(root,envelope,a,unified.registry(),require_code=True,role="code")
    original=current.envelope.namespace_bundle;holder={}
    raw=(root/entry.ENTRY["path"]).read_bytes()
    require(len(raw)==entry.ENTRY["bytes"] and hashlib.sha256(raw).hexdigest()==entry.ENTRY["sha256"],"EXACT_WHOLE_FROZEN_NATIVE_ORCHESTRATOR")
    def aliased(*args,**kwargs):
        modules,proof=original.load(*args,**kwargs)
        legacy=getattr(modules,"level6_closed_preparation_v1",None)
        if legacy is not None:
            api=NS(**{**vars(current.frozen),"main":current.main,"loader_profile":current.main.__globals__["loader_profile"],
                "SELF":setup.profile.SELF,"CORE":setup.profile.CORE,"VERSION":setup.profile.VERSION})
            entry.bind_envelope(api,holder["envelope"]);modules.level6_closed_preparation_v1=api
        return modules,proof
    alias=NS(**{**vars(original),"load":aliased})
    # Deliberately no route_loader, pressure_facade or controller_transform.
    routed=entry.metadata_loader(alias)
    windows=entry.window_components(root,envelope);window=windows.post_product_recovery_window_v1
    routed,observations=windows.recovery_dispatch_window_v1.connect_loader(routed,envelope,
        windows.post_product_recovery_connection_v1,window,(root/window.WINDOW_PIN["path"]).read_bytes(),entry.bind_envelope)
    proxy=NS(**{**vars(envelope),"namespace_bundle":routed});holder["envelope"]=proxy
    api=binding.adapt(unified);recovery=windows.post_product_recovery_connection_v1
    def wrap(previous):
        def completed(*args,**kwargs):return api.reference_loader(previous(*args,**kwargs),recovery,witness=witness)
        return completed
    fn=unified.project_closure(closure.main,raw,wrap)
    require(a.Guard is base_guard,"ORIGINAL_NATIVE_GUARD_NOT_REPLACED")
    return NS(main=fn,envelope=proxy,dispatch_window_observations=observations,Native_policy_changed=False,
        preparation_CPU_Guard_constructed=False,current_worker_entry=unified.SELF,actual_CODE_reference=binding.WHOLE_CODE["path"])


def readiness(q,a,binding,preflight,qualification):
    native_arguments(preflight,qualification)
    pref_name=PREFIX+f"successor-recovery-preflight-run008-attempt{preflight:03}.v1.json"
    qual_name=PREFIX+f"successor-recovery-dispatch-qualification-run008-attempt{qualification:03}.v1.json"
    pref=q.json(pref_name);qual=q.json(qual_name)
    a.fields(pref,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
        index=165,physical_run=8,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
        product_worker_or_Native_frame_executed=False),"ACTUAL_FINAL_PREFLIGHT_NOT_OLD_EPOCH")
    a.fields(qual,dict(state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",index=165,physical_run=8,
        contracts=dict(run=6,errors=0,failures=0,skipped=0),runtime_default_imports=60,actual_Native_helper_count=64,
        cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"ACTUAL_FINAL_DISPATCH64")
    for row in (pref,qual):
        require(type(row["fresh_inputs"]) is int and row["fresh_inputs"]==row["final_fresh_hashes"]>0,"ACTUAL_FINAL_SOURCE_BOUNDARIES")
        a.exact(row["code_pin"],binding.WHOLE_CODE,"ACTUAL_CODE006_NOT_COPIED_OR_LEGACY001")
    a.exact(qual["preflight_pin"],q.snapshots[pref_name],"QUALIFICATION_REFERENCES_THIS_EXACT_PREFLIGHT")
    budget=qual["complete_runtime_budget"]
    predicted=budget["predicted_runtime_combined_seconds"]
    require(budget["unchanged_lock_deadline_seconds"]==600 and budget["unallocated_margin_seconds"]==60
        and budget["aggregate_envelope_decoder_allowance_seconds"]==5 and type(predicted) in (int,float)
        and math.isfinite(predicted) and 0<predicted<=600,"UNCHANGED_BUDGET_AND_MARGIN")
    return NS(preflight_pin=q.snapshots[pref_name],qualification_pin=q.snapshots[qual_name])


def native(c,a,envelope,unified,binding,preflight,qualification,attempt):
    arguments=native_arguments(preflight,qualification)
    require(type(attempt) is int and 1<=attempt<=8,"FINITE_NATIVE_BOOTSTRAP_AUDIT")
    output=PREFIX+f"xz-unified-native-invocation{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_NATIVE_INVOCATION_AUDIT");absent(c.ROOT);no_previous_intent(c.ROOT)
    setup=binding.components(c,envelope,unified);entry=setup.entry;raw=setup.raw
    # Same original Native bootstrap as the protected bridge, not preparation CPU.
    guard=raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    row=dict(state="FAILED_UNIFIED_NATIVE_BOOTSTRAP_NOT_ENTERED",index=165,physical_run=8,Native_entry_invoked=False,
        Native_policy_changed=False,GO_authorized_by_adapter=False,accepted_count_delta=0)
    def witness(q):witnesses(q,a,unified,binding,entry,setup.policy,setup.profile,raw.xz_startup_adapter_v1,raw.xz_whole_code_adapter_v1,proof=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        witness(q);references=readiness(q,a,binding,preflight,qualification)
        for earlier in range(1,attempt):
            path=PREFIX+f"xz-unified-native-invocation{earlier:03}.v1.json"
            if(c.ROOT/path).exists():require(q.json(path)["Native_entry_invoked"] is False,"NO_RETRY_AFTER_ORIGINAL_NATIVE_INVOCATION")
        q.finish();guard.check(force=True)
        row.update(bootstrap_fresh=len(q.snapshots),bootstrap_final=q.final_fresh_hashes,
            preflight_pin=references.preflight_pin,qualification_pin=references.qualification_pin)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_code"]=error_code(error)
    finally:guard.close()
    row["bootstrap_cleanup_confirmed"]=guard.cleanup
    if not guard.cleanup:
        row["error_code"]="ORIGINAL_NATIVE_BOOTSTRAP_OWNER_NOT_CLOSED"
        raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
        print(json.dumps(row));return row
    if "error_code" not in row:
        try:
            absent(c.ROOT)
            linked=build_native(c.ROOT,envelope,a,unified,binding,setup,witness=witness)
            no_previous_intent(c.ROOT)
            intent=PREFIX+f"xz-unified-native-invocation{attempt:03}.intent.v1.json"
            raw.successor_preparation_workspace_v1.publish(c.ROOT,intent,dict(state="ORIGINAL_NATIVE_ENTRY_INVOCATION_INTENT",
                index=165,physical_run=8,arguments=arguments,preflight_pin=references.preflight_pin,qualification_pin=references.qualification_pin,
                automatic_retry_allowed=False,Native_policy_changed=False,accepted_count_delta=0),a)
            row["Native_entry_invoked"]=True
            row["original_entry_exit_code"]=entry.execute(NS(main=linked.main),linked.envelope,arguments)
            require(bool(linked.dispatch_window_observations),"ACTUAL_NATIVE_DISPATCH_WINDOW10_CONNECTED")
            row.update(state="RECORDED_ORIGINAL_UNIFIED_NATIVE_ENTRY_NOT_REVIEW_OR_ACCEPTANCE",dispatch_window_seconds=10)
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            row.update(state="FAILED_AFTER_ORIGINAL_NATIVE_INVOCATION_NO_AUTOMATIC_RETRY" if row["Native_entry_invoked"] else
                "FAILED_NATIVE_DEPENDENCY_BUILD_NOT_ENTERED",error_code=error_code(error))
    row["Native008_record_exists"]=(c.ROOT/(PREFIX+"current-runtime-run008.v1.json")).exists()
    raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps(row))
    return row


def error_code(error):
    value=error.args[0] if error.args else None
    return value if type(value) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,159}",value) else type(error).__name__


def qualify(c,a,envelope,unified,binding,attempt):
    import io,time,unittest
    require(type(attempt) is int and 1<=attempt<=8,"FINITE_NATIVE_WIRING_CODE")
    output=PREFIX+f"xz-unified-native-entry-code{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_NATIVE_WIRING_CODE")
    setup=binding.components(c,envelope,unified);entry=setup.entry;raw=setup.raw;policy=setup.policy
    metrics={};phase=dict(value="bootstrap_policy");guards=[];started=time.monotonic()
    old=unified.observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),metrics,phase)
    def prep():
        phase["value"]="bootstrap_connection"
        return unified.observed_guard(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"),metrics,phase)()
    row=dict(state="FAILED_UNIFIED_NATIVE_WIRING_NOT_ADOPTED",accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False,Native_policy_changed=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy);a.exact(q.pin(unified.BASELINE["path"]),unified.BASELINE,"MEASURED_BASELINE")
        def verify(q):
            witnesses(q,a,unified,binding,entry,policy,setup.profile,raw.xz_startup_adapter_v1,raw.xz_whole_code_adapter_v1,proof=False)
            data=(c.ROOT/TEST).read_bytes();pin=dict(path=TEST,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            tests,_=envelope.namespace_bundle.load(c.ROOT,[pin],{})
            suite=tests.test_xz_unified_native_entry_v1
            values=dict(MODULE=NS(**globals()),ENTRY=unified,BINDING=binding,SETUP=setup,ROOT=c.ROOT,ENVELOPE=envelope,ACCEPTANCE=a)
            for cls in vars(suite).values():
                if type(cls) is type:
                    for fn in vars(cls).values():
                        if type(fn) is FunctionType:fn.__globals__.update(values)
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(suite))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
            a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"ALL_NATIVE_WIRING12_NOT_PRODUCT")
        q,proof=entry.closed_bootstrap(c.ROOT,a,old,prep,verify_policy,verify,guards)
        row.update(state=STATE,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_CODE_pin=binding.WHOLE_CODE,bootstrap_policy_validation=proof)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:row["error_code"]=error_code(error)
    finally:
        samples=[s for g in guards for s in g.samples]
        row.update(cleanup_confirmed=all(g.cleanup for g in guards),elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_WIRING_CODE_GUARDS_CLOSED")
    raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_errors","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"]==STATE else 1
