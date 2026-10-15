"""Exact same-case failed-capture extension; no Native entry or retry.

Validate the entire existing68 constructor first, then run its complete raw
constructor on exactly those68 + one admitted failure. All scope/byte/handle
oracle methods and Projection methods remain the original function objects.
The old preparation context is not relabelled as a Native009 qualification.
"""
import copy
import hashlib
import sys
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/native008_failure_binding_v1.py"
TEST="tools/p09/tests/test_native008_failure_binding_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
PUBLICATION=dict(path=PREFIX+"native008-carrier-g001-attempt001.v1.json",bytes=6985,
    sha256="08693e9b6b1dcb98c9f739516e84d005eacafa577abf0394c5f503835dda9732")
FULL69=dict(path=PREFIX+"native008-full69-physical-attempt001.v1.json",bytes=43535,
    sha256="9882f3eb79a5eb2f6e5674ec466f7fc4b932eb1b4e23f00900cd770cd05c4702")
ORIGINAL=dict(path=PREFIX+"current-runtime-run008.v1.json",bytes=3999022,
    sha256="53e27ba4e2f9555ecfa47d942fcbfe4319e3b91e91f7e5180ac18585a02e9df2")
PHYSICAL=dict(path="implementation/p09/evidence/p361-lossless-runtime-inputs/case165-runtime-run008.failed.strict-window.xz8m-g001.envelope.v1.json",
    bytes=270794,sha256="7f42635e0edbe72a9169c2f81413a66eb3041094011c8f46e03bd6e0823ffc75")
TABLE="c858a48e5c4d615e8aac8709b5e214b09a35d5533860370a035204b63fdc8026"
ROLE=dict(schema_version="hwpx-agent.p09-failed-capture-alias-admission/v1",current_case=165,
    failed_physical_run=8,candidate_successor_physical_run=9,
    source_role="same_case_failed_capture_unknown_product_execution_not_accepted",
    failed_runtime_pin=ORIGINAL,physical_pin=PHYSICAL,physical_verification_pin=FULL69,
    actual_failed_product_child_executed=None,original_failure_promoted=False,
    current_product_or_GO_qualified=False)


def require(ok,label):
    if not ok:raise ValueError("NATIVE008_FAILURE_BINDING_"+label)


def fingerprint(rows):
    import json
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(",",":")).encode("ascii")).hexdigest()


def admission(q,a,producer):
    row=a.read_exact(q,FULL69);pub=a.read_exact(q,PUBLICATION)
    a.fields(row,dict(state="PASS_FULL69_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE",
        pair_count=69,decode_count=138,fresh_inputs=160,final_fresh_hashes=160,cleanup_confirmed=True,
        original_full68_mapping_or_descriptor_policy_changed=False,accepted_count_delta=0,GO_authorized=False,
        actual_Native_binding_or_full_successor_scope_qualified=False),"REAL_FULL69_PHYSICAL_PROOF_ONLY")
    a.exact(row["new_failed_semantic_pin"],ORIGINAL,"EXACT_FAILURE_ORIGINAL")
    a.exact(row["new_failed_physical_pin"],PHYSICAL,"EXACT_FAILURE_PHYSICAL")
    a.exact(pub["original_pin"],ORIGINAL,"PUBLICATION_ORIGINAL")
    a.exact(pub["published_carrier_pin"],PHYSICAL,"PUBLICATION_PHYSICAL")
    a.fields(row["decoder_budget"],dict(aggregate_limit_seconds=5.0,attempted_decodes=138,completed_decodes=138,
        active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True),"SHARED_FULL69_DECODER5")
    require(0<=row["decoder_budget"]["elapsed_decoder_work_seconds"]<5,"ACTUAL_FULL69_DECODER_INSIDE5")
    producer.failed_state(a.read_exact(q,ORIGINAL))
    a.exact(q.pin(PHYSICAL["path"]),PHYSICAL,"CURRENT_CARRIER_BYTES")
    for proof in (row,pub):
        for pin in proof["source_pins"]:
            if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                a.exact(q.pin(pin["path"]),pin,"UNCHANGED_PHYSICAL_VERIFIER_PROGRAMS")
    return copy.deepcopy(ROLE)


def install(module,prior_rows,admitted,xz,*,physical_run):
    require(type(physical_run) is int and physical_run==9,"EXPLICIT_SUCCESSOR9_NOT_REPLAY8")
    require(type(module) is NS and type(getattr(module,"source",None)) is NS,"PRIVATE_BINDING_GRAPH")
    module.exact(admitted,ROLE,"EXACT_TYPED_UNKNOWN_EXECUTION_ROLE")
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get("__name__","").startswith("p09_exact_") and env.get("descriptor") is source.descriptor
        and not any(getattr(m,"__dict__",None) is env for m in tuple(sys.modules.values()) if m),"FRESH_PRIVATE_GRAPH_NOT_DEFAULT")
    require(not hasattr(module,"native008_failure_alias"),"ONE_EXPLICIT_INSTALLATION")
    require(type(prior_rows) is list and len(prior_rows)==68 and fingerprint(prior_rows)==TABLE
        and hasattr(module,"xz_ordinary_profile") and module.xz_ordinary_profile["count"]==61,
        "ENTIRE_EXISTING68_XZ61_NOT_A_SUBSET")
    old_init=module.Binding.__init__;base_init=module.xz_original_initialize
    require(type(base_init) is FunctionType and base_init.__name__=="__init__"
        and base_init.__code__.co_filename.replace("\\","/").endswith("runtime_envelope_scope_binding_v1.py"),
        "WHOLE_ORIGINAL_RAW_BINDING_CONSTRUCTOR")
    old_descriptor=source.descriptor;old_codec=source.codec;old_representation=module.Binding.representation
    methods={k:v for k,v in vars(module.Binding).items() if k not in ("__init__","representation")}
    projection_methods=dict(vars(source.Projection));frozen=copy.deepcopy(prior_rows);provenance=copy.deepcopy(admitted)
    pair=dict(schema_version=source.SCHEMA,next_case=165,semantic_original_pin=dict(ORIGINAL),physical_envelope_pin=dict(PHYSICAL))
    full=frozen+[pair];state=dict(ready=False)
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get("path")!=ORIGINAL["path"]:
            return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==165,"EXACT_CURRENT_CASE")
        module.exact(source.copy_pin(old),ORIGINAL,"ONE_EXACT_FAILED_ORIGINAL")
        module.exact(source.copy_pin(new),PHYSICAL,"ONE_EXACT_FAILED_CARRIER")
        return copy.deepcopy(pair)
    def initialize(self,rows,manifest_pin,*,next_case):
        state["ready"]=False
        module.exact(rows,full,"ALL_ORIGINAL68_PLUS_ONE_FAILURE_ONLY")
        require(type(next_case) is int and next_case==165,"EXACT_FULL69_CASE")
        # Execute the unchanged full68 wrapper and all its fixed-table checks.
        old_init(self,rows[:68],manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),frozen,"ORIGINAL68_CONSTRUCTOR_ACTUALLY_COMPLETED")
        # The unchanged complete constructor now validates every69 row, pin,
        # bijection and manifest. Never mutate its code or skip other methods.
        base_init(self,rows,manifest_pin,next_case=next_case)
        module.exact(self.descriptors(),full,"WHOLE_RAW_CONSTRUCTOR69_COMPLETED")
        state["ready"]=True
    def decode(raw,checkpoint):
        checkpoint()
        require(type(raw) is bytes and 0<len(raw)<=xz.MAX_BYTES,"FRESH_BOUNDED_CODEC_INPUT")
        if hashlib.sha256(raw).hexdigest()==PHYSICAL["sha256"]:
            require(state["ready"],"FULL69_CONSTRUCTOR_BEFORE_FAILURE_DECODE")
            return xz.decode(raw,checkpoint)
        return old_codec.decode(raw,checkpoint)
    def representation(self,projection):
        require(ORIGINAL["path"] in self.originals,"EXPLICIT_FAILURE_ALIAS_REQUIRED")
        result=old_representation(self,projection)
        result["same_case_failed165_run008_provenance"]=copy.deepcopy(provenance)
        return result
    source.descriptor=descriptor;env["descriptor"]=descriptor
    source.codec=NS(**{**vars(old_codec),"decode":decode});env["codec"]=source.codec
    module.Binding.__init__=initialize;module.Binding.representation=representation
    module.native008_failure_alias=copy.deepcopy(provenance)
    require(all(vars(module.Binding).get(k) is v for k,v in methods.items()),"ALL_NONCONSTRUCTOR_SCOPE_BYTE_HANDLE_ORACLES_RETAINED")
    require(all(vars(source.Projection).get(k) is v for k,v in projection_methods.items()),"ALL_ORIGINAL_PROJECTION_METHODS_RETAINED")
    return dict(existing68_full_constructor_executed_before_raw69=True,original_constructor_code_unchanged=True,
        original_nonconstructor_oracles_and_Projection_methods_retained=True,
        unknown_execution_not_relabelled_as_pre_product_stop=True,Native009_binding_or_GO_authorized=False)


def existing(c,a,envelope,unified,binder,scope,bytes_policy,guard):
    """Actual unchanged v18 preparation context8, not a Native009 rebase."""
    setup=binder.components(c,envelope,unified)
    current=setup.profile.connect(c.ROOT,envelope,a,unified.registry(),require_code=True,role="code")
    env=current.main.__globals__
    raw,_=current.envelope.namespace_bundle.load(c.ROOT,[env["CORE"],current.frozen.PRIOR_ALIAS],{})
    core=raw.level6_ordinary_binding_v1
    profiled=env["loader_profile"](c.ROOT,current.envelope.namespace_bundle,core,a,raw.prior_preparation_alias_v1)
    proxy=NS(**{**vars(envelope),"namespace_bundle":profiled})
    sources,_=profiled.load(c.ROOT,[core.FRONT],{});front=sources.expanded_closed_preparation_v1
    _,_,entry_proxy,_=front.components(c.ROOT,proxy)
    entry_ns,_=entry_proxy.namespace_bundle.load(c.ROOT,[front.FIX],{})
    ctx=NS(preflight=PREFIX+"successor-preflight-run008-attempt001.v1.json",
        qualification=PREFIX+"successor-dispatch-qualification-run008-attempt001.v1.json")
    linked=entry_ns.closed_prebody_factory_admission_fix_v1.load(c.ROOT,a,scope,bytes_policy,entry_proxy,
        PREFIX+"sealed-metadata-code001.v1.json",ctx=ctx)
    q=linked.api.AcceptanceReader(c.ROOT,guard.check)
    base=q.json(binder.GRAPH["path"]);step=base["step"];prior=a.read_exact(q,step["prior_candidate_pin"])
    baseline,rows,_=core.admit(q,a,scope)
    connection=linked.connection.binding_api(linked.modules.current_queue_successor_binding,linked.alias,q.closed_source_policy)
    def factory():
        return connection.connect(c.ROOT,entry_proxy.namespace_bundle,scope,165,
            baseline["historical_predecessor_provenance"],prior["source_input_representation"]["descriptors"])[0]
    return NS(reader=q,factory=factory,rows=rows,manifest_pin=base["manifest_pin"],original_preparation_run=8)


def main():
    import argparse,importlib.util,io,json,re,time,unittest
    from pathlib import Path
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
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=PREFIX+f"native008-failure-binding-code{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_CODE_OUTPUT")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None;old=None
    row=dict(state="FAILED_EXACT_NATIVE008_ALIAS_CODE_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,whole_successor_current_source_plan_qualified=False,
        actual_Native009_or_worker_connection_qualified=False,automatic_retry=False)
    try:
        guard.acquire();guard.check(force=True)
        old=existing(c,a,envelope,unified,binder,scope,bytes_policy,guard)
        q=a.AcceptanceReader(c.ROOT,guard.check);admitted=admission(q,a,producer)
        q.pin(SELF);q.pin(TEST)
        spec=importlib.util.spec_from_file_location("native008_failure_binding_contracts",c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.ADMITTED=admitted;tests.FOUNDATION=old;tests.XZ=xz
        tests.SCOPE=scope;tests.CHECKPOINT=guard.check;tests.CARRIER=bytes(q._read(PHYSICAL["path"],parse=True)[1])
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contract_failures"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"ALL_FAILURE_BINDING12")
        tests.CARRIER=None
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        old.reader.finish();q.finish();guard.check(force=True)
        row.update(state="PASS_EXACT_NATIVE008_FAILED_ALIAS12_NOT_NATIVE009_BINDING_OR_ACCEPTANCE",
            admitted_role=admitted,old_foundation_preparation_context=8,
            old_foundation_fresh=len(old.reader.snapshots),old_foundation_final=old.reader.final_fresh_hashes,
            old_foundation_source_pins=list(old.reader.snapshots.values()),
            old_foundation_not_relabelled_as_Native009=True,source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"CODE_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_failures","old_foundation_fresh","old_foundation_final",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
