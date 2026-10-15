"""Explicit lossless aliases for fully closed earlier attempts of one case.

No Native/worker/GO/queue entry. Same-case PASS/current/future/unresolved records
are not ordinary historical aliases. Verify the original complete prebody gate,
fresh originals and encoded bytes before constructing a private binding policy.
"""
import copy
import hashlib
import re
import sys
from types import MappingProxyType

SELF="tools/p09/closed_prebody_source_alias_v1.py"
TEST="tools/p09/tests/test_closed_prebody_source_alias_v1.py"
SCHEMA="hwpx-agent.p09-closed-prebody-source-producer/v1"
POLICY="hwpx-agent.p09-qualified-closed-prebody-source-policy/v1"
STATE="PREPARED_EXACT_CLOSED_PREBODY_LOSSLESS_SOURCES_NOT_NATIVE_OR_PRODUCT"
CODE_STATE="PASS_CLOSED_PREBODY_ALIAS_CODE14_NOT_NATIVE_OR_PRODUCT"
PREFIX="implementation/p09/evidence/"
BRIDGE_PIN=dict(path="tools/p09/current_queue_successor_wire_runtime_v2.py",bytes=11932,
    sha256="74c509ee713b571a8ed8d52f904513a567ff19391fb418942d1336a5ce6d6efd")
RETRY_PIN=dict(path="tools/p09/current_queue_successor_retry_runtime_v3.py",bytes=11451,
    sha256="c8f2c06f224890581177d8e3d8e55ab3111463ac5b11d505f6c47171d61ce348")
_TOKEN=object()


def require(ok,label):
    if not ok:raise ValueError("CLOSED_PREBODY_ALIAS_"+label)


def root_attempt(pin,index,before_run,scope):
    require(type(index) is int and 165<=index<=249 and type(before_run) is int and 3<=before_run<=8,"CLOSED_TARGET_CONTEXT")
    scope.pins([pin])
    match=re.fullmatch(PREFIX+rf"p09-361-case{index}-current-runtime-run([0-9]{{3}})\.v1\.json",pin["path"])
    require(match is not None and 2<=int(match[1])<before_run,"EARLIER_SAME_CASE_ONLY")
    return int(match[1])


def encoded_path(pin,index,before_run,scope):
    attempt=root_attempt(pin,index,before_run,scope)
    return PREFIX+f"p361-lossless-runtime-inputs/case{index}-runtime-run{attempt:03}.envelope.v1.json"


def producer_fields(index,before,code_pin,originals,pairs):
    old_bytes=sum(p["semantic_original_pin"]["bytes"] for p in pairs)
    new_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in pairs)
    return dict(schema_version=SCHEMA,state=STATE,index=index,before_run=before,
        source_qualification_pin=copy.deepcopy(code_pin),requested_original_pins=copy.deepcopy(originals),
        closed_descriptors=copy.deepcopy(pairs),original_bytes=old_bytes,encoded_bytes=new_bytes,
        bytes_saved=old_bytes-new_bytes,decode_passes=2*len(pairs),
        expected_roots_not_derived_from_current_observed_contents=True)


class VerifiedPolicy:
    __slots__=("index","before_run","producer_pin","_pairs")
    def __init__(self,token,index,before_run,producer_pin,pairs):
        require(token is _TOKEN,"VERIFIED_FACTORY_ONLY")
        object.__setattr__(self,"index",index);object.__setattr__(self,"before_run",before_run)
        object.__setattr__(self,"producer_pin",MappingProxyType(dict(producer_pin)))
        object.__setattr__(self,"_pairs",tuple(MappingProxyType(dict(row,
            semantic_original_pin=MappingProxyType(dict(row["semantic_original_pin"])),
            physical_envelope_pin=MappingProxyType(dict(row["physical_envelope_pin"])))) for row in pairs))
    def __setattr__(self,name,value):raise AttributeError("IMMUTABLE_VERIFIED_POLICY")
    def descriptors(self):
        return [dict(row,semantic_original_pin=dict(row["semantic_original_pin"]),
            physical_envelope_pin=dict(row["physical_envelope_pin"])) for row in self._pairs]
    def evidence(self):
        return dict(schema_version=POLICY,index=self.index,before_run=self.before_run,
            producer_pin=dict(self.producer_pin),closed_descriptors=self.descriptors(),
            earlier_closed_prebody_only=True,current_or_passed_product_not_permitted=True,
            original_raw_receipts_not_claimed_physically_locked=True)


def verify(q,producer_pin,index,run,a,scope,bridge,codec,source_schema):
    """Independent full source checks, not candidate-derived expected aliases."""
    scope.pins([producer_pin])
    require(re.fullmatch(PREFIX+rf"p09-361-case{index}-closed-prebody-sources00[1-8]\.v1\.json",producer_pin["path"]) is not None,"EXACT_PRODUCER_PATH")
    row=a.read_exact(q,producer_pin)
    a.fields(row,dict(schema_version=SCHEMA,state=STATE,index=index,cleanup_confirmed=True,
        original_receipts_rewritten=False,product_or_Native_executed=False,accepted_count_delta=0),"EXACT_CLOSED_SOURCE_PRODUCER")
    before=row["before_run"]
    require(type(run) is int and type(before) is int and 3<=before<=run<=8,"EXACT_RUN_BOUNDARY")
    inventory=scope.pins(row["fresh_input_pins"])
    require(type(row["fresh_inputs"]) is int and row["fresh_inputs"]==row["final_fresh_hashes"]>0
        and len(inventory)==row["fresh_inputs"],"COMPLETE_PRODUCER_HASHES")
    pairs=row["closed_descriptors"]
    require(type(pairs) is list and 1<=len(pairs)<=6,"BOUNDED_CLOSED_PAIRS")
    a.exact(row.get("requested_original_pins"),[p["semantic_original_pin"] for p in pairs],"EXACT_PREDECLARED_EXPECTED_ROOTS")
    a.exact(row.get("expected_roots_not_derived_from_current_observed_contents"),True,"INDEPENDENT_ROOT_PIN_DECLARATIONS")
    code_pin=row["source_qualification_pin"];scope.pins([code_pin])
    require(re.fullmatch(PREFIX+rf"p09-361-case{index}-closed-prebody-code00[1-8]\.v1\.json",code_pin["path"]) is not None,"EXACT_CODE_PATH")
    a.exact(inventory.get(code_pin["path"]),code_pin,"CODE_IN_PRODUCER_FINAL_INVENTORY")
    code=a.read_exact(q,code_pin)
    a.fields(code,dict(state=CODE_STATE,contracts=dict(run=14,errors=0,failures=0,skipped=0),
        cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False),"MANDATORY_CLOSED_ALIAS_CODE14")
    require(type(code["fresh_inputs"]) is int and code["fresh_inputs"]==code["final_fresh_hashes"]>0,"CLOSED_CODE_HASHES")
    names={p["path"] for p in code["source_pins"]}
    require({SELF,TEST,BRIDGE_PIN["path"]}<=names,"CODE_AND_FROZEN_GATE_WITNESSES")
    for pin in code["source_pins"]+row["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_QUALIFIED_ALIAS_SOURCES")
    a.exact(q.pin(BRIDGE_PIN["path"]),BRIDGE_PIN,"EXACT_FULL_PREBODY_GATE_SOURCE")
    seen=set();physical=set();attempts=[]
    for pair in pairs:
        require(type(pair) is dict and set(pair)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"},"CLOSED_PAIR_SHAPE")
        a.fields(pair,dict(schema_version=source_schema,next_case=index),"EXACT_PAIR_CONTEXT")
        old,new=pair["semantic_original_pin"],pair["physical_envelope_pin"]
        attempt=root_attempt(old,index,before,scope);scope.pins([new])
        require(old["path"] not in seen and new["path"] not in physical,"UNIQUE_BIJECTIVE_PAIRS")
        require(new["path"]==encoded_path(old,index,before,scope),"EXPLICIT_CLOSED_PHYSICAL_PATH")
        require(old["bytes"]<=codec.MAX_BYTES and new["bytes"]<=codec.MAX_BYTES,"ORIGINAL_CODEC_BOUNDS")
        a.exact(inventory.get(old["path"]),old,"RAW_ROOT_IN_PRODUCER_FINAL_INVENTORY")
        a.exact(inventory.get(new["path"]),new,"ENCODED_ROOT_IN_PRODUCER_FINAL_INVENTORY")
        seen.add(old["path"]);physical.add(new["path"]);attempts.append(attempt)
        original=a.read_exact(q,old)
        bridge.closed_prebody_stop(original,index,attempt,a)
        for flag in ("actual_Cargo_SQL_Hangul_run","product_complete"):
            if flag in original:a.exact(original[flag],False,"NO_DECLARED_PRODUCT_OR_EXTERNAL_RUNTIME")
        pin,buffer=q._read(new["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,new,"ACTUAL_FRESH_CLOSED_PHYSICAL_PIN")
        decoded=codec.decode(bytes(buffer),q.checkpoint)
        require(len(decoded)==old["bytes"] and hashlib.sha256(decoded).hexdigest()==old["sha256"],"EXACT_FULL_ORIGINAL_BYTES_RESTORED")
    require(attempts==sorted(set(attempts)),"ORDERED_EXPLICIT_PRIOR_ATTEMPTS")
    old_bytes=sum(p["semantic_original_pin"]["bytes"] for p in pairs)
    new_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in pairs)
    a.fields(row,dict(original_bytes=old_bytes,encoded_bytes=new_bytes,bytes_saved=old_bytes-new_bytes,
        decode_passes=2*len(pairs)),"EXACT_PRODUCER_BYTE_AND_DECODE_ACCOUNTING")
    return VerifiedPolicy(_TOKEN,index,before,producer_pin,pairs)


def install(module,policy):
    """Extend ONLY a private descriptor predicate with exact verified pin pairs."""
    require(type(policy) is VerifiedPolicy,"VERIFIED_POLICY_REQUIRED")
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get("__name__","").startswith("p09_exact_") and
        not any(getattr(m,"__dict__",None) is env for m in tuple(sys.modules.values()) if m),"PRIVATE_SOURCE_NAMESPACE_REQUIRED")
    original=source.descriptor;represented=module.Binding.representation
    pairs={row["semantic_original_pin"]["path"]:row for row in policy.descriptors()}
    methods={n:v for n,v in vars(module.Binding).items() if n!="representation"}
    def descriptor(old,new,*,next_case):
        if type(old) is dict and old.get("path") in pairs:
            require(type(next_case) is int and next_case==policy.index,"EXACT_CLOSED_ALIAS_CASE")
            expected=pairs[old["path"]]
            module.exact(source.copy_pin(old),expected["semantic_original_pin"],"EXACT_VERIFIED_CLOSED_ORIGINAL")
            module.exact(source.copy_pin(new),expected["physical_envelope_pin"],"EXACT_VERIFIED_CLOSED_ENCODING")
            return copy.deepcopy(expected)
        return original(old,new,next_case=next_case)
    def representation(self,projection):
        result=represented(self,projection)
        result["closed_prebody_source_policy"]=policy.evidence()
        return result
    source.descriptor=descriptor;env["descriptor"]=descriptor
    module.Binding.representation=representation
    require(all(vars(module.Binding).get(n) is v for n,v in methods.items()),"ALL_ORIGINAL_BINDING_ORACLE_METHODS_RETAINED")
    return dict(profile=POLICY,source_schema_unchanged=True,ordinary_descriptor_retained=True,
        complete_semantic_scope_projection_and_both_physical_boundaries_retained=True,
        original_budget_identity_handle_and_cleanup_validator_methods_retained=True,
        new_profile_evidence_in_representation=True,shared_default_modules_not_mutated=True,
        actual_Native_worker_or_product_qualified=False)


def main():
    import argparse,io,json,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import runtime_envelope_namespace_bundle_v1 as loader
    import runtime_envelope_physical_io_v1 as physical
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True);parser.add_argument("--before-run",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True);parser.add_argument("--code-attempt",type=int,default=1)
    parser.add_argument("--root-pin",action="append",default=[],help="Explicit attempt,bytes,sha256 from actual stopped execution")
    mode=parser.add_mutually_exclusive_group(required=True)
    for name in ("code","produce","probe"):mode.add_argument("--"+name,action="store_true")
    args=parser.parse_args();index,before=args.case,args.before_run
    require(type(index) is int and 165<=index<=249 and 3<=before<=8 and
        all(1<=n<=8 for n in (args.attempt,args.code_attempt)),"CLOSED_CLI_CONTEXT")
    code_name=PREFIX+f"p09-361-case{index}-closed-prebody-code{args.code_attempt:03}.v1.json"
    producer_name=PREFIX+f"p09-361-case{index}-closed-prebody-sources{args.attempt:03}.v1.json"
    output=code_name if args.code else producer_name if args.produce else PREFIX+f"p09-361-case{index}-closed-prebody-projection{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_OUTPUT_NO_REPLAY")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_CLOSED_PREBODY_SOURCE_PREPARATION_NOT_ADOPTED",index=index,before_run=before,
        product_or_Native_executed=False,accepted_count_delta=0,original_receipts_rewritten=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,bindings.SELF,bindings.TEST,loader.SELF,publisher.SELF):q.pin(name)
        names,proof=loader.load(c.ROOT,[BRIDGE_PIN,RETRY_PIN],{})
        bridge=names.current_queue_successor_wire_runtime_v2;retry=names.current_queue_successor_retry_runtime_v3
        for pin in [BRIDGE_PIN,RETRY_PIN]+bindings.PINS:a.exact(q.pin(pin["path"]),pin,"ALL_FROZEN_SOURCE_AND_GATE_DEPENDENCIES")
        code13=q.json(PREFIX+"p09-361-case158-envelope-physical-code13-r625.v1.json")
        a.fields(code13,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_CODEC_PUBLISHER_CODE13")
        for pin in code13["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CODEC_AND_PUBLISHER_SOURCES")
        if args.code:
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromName("tests.test_closed_prebody_source_alias_v1"))
            contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contracts"]=contracts;a.exact(contracts,dict(run=14,errors=0,failures=0,skipped=0),"ALL_POLICY14")
            row["state"]=CODE_STATE
        elif args.produce:
            code=q.json(code_name)
            a.fields(code,dict(state=CODE_STATE,contracts=dict(run=14,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_POLICY_CODE14")
            for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_QUALIFIED_POLICY_SOURCE")
            require(1<=len(args.root_pin)<=6,"EXPLICIT_OBSERVED_ROOT_PINS_REQUIRED")
            originals=[]
            for item in args.root_pin:
                parts=item.split(",");require(len(parts)==3,"EXPLICIT_ROOT_PIN_ARGUMENT")
                attempt,size=int(parts[0]),int(parts[1])
                pin=dict(path=PREFIX+f"p09-361-case{index}-current-runtime-run{attempt:03}.v1.json",bytes=size,sha256=parts[2])
                root_attempt(pin,index,before,scope);originals.append(pin)
            require([root_attempt(p,index,before,scope) for p in originals]==sorted(set(root_attempt(p,index,before,scope) for p in originals)),"UNIQUE_ORDERED_EXPECTED_ROOTS")
            target=PREFIX+f"p09-361-case{index}-current-runtime-run{before:03}.v1.json"
            require(retry.absent(q,target,a),"CURRENT_TARGET_MUST_NOT_EXIST")
            pacer=physical.bytes_policy.OwnedPacer();pairs=[]
            for old in originals:
                actual,buffer=q._read(old["path"],parse=True);q._bind(old["path"],actual)
                a.exact(actual,old,"EXACT_PREDECLARED_ACTUAL_STOP_ROOT")
                document=json.loads(bytes(buffer).decode("utf-8"));bridge.closed_prebody_stop(document,index,root_attempt(old,index,before,scope),a)
                raw=bytes(buffer);encoded=physical.source.codec.encode(raw,guard.check)
                new=dict(path=encoded_path(old,index,before,scope),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
                for _ in range(2):a.exact(physical.source.codec.decode(encoded,guard.check),raw,"EXACT_WHOLE_STOP_RECORD_RESTORED")
                if retry.absent(q,new["path"],a):physical.publish_exclusive(c.ROOT,encoded,new,guard.check,write_pacer=pacer)
                a.exact(q.fresh_pin(new["path"]),new,"FRESH_CLOSED_DERIVATIVE")
                pairs.append(dict(schema_version=physical.source.SCHEMA,next_case=index,semantic_original_pin=old,physical_envelope_pin=new))
            row.update(producer_fields(index,before,q.snapshots[code_name],originals,pairs))
            require(retry.absent(q,target,a),"CURRENT_TARGET_ABSENCE_RECHECK")
        else:
            pin=q.pin(producer_name)
            policy=verify(q,pin,index,before,a,scope,bridge,physical.source.codec,physical.source.SCHEMA)
            baseline=q.json(PREFIX+f"p09-361-case{index}-successor-preflight-run003-attempt006.v1.json")
            a.fields(baseline,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
                index=index,physical_run=3,cleanup_confirmed=True),"SEALED_BASELINE_SCOPE_NOT_NEW_NATIVE")
            prepared=q.json(PREFIX+f"p09-361-case{index}-successor-binding001.v1.json")
            manifest=a.read_exact(q,prepared["manifest_pin"]);prior=a.read_exact(q,manifest["prior_manifest_pin"])
            module,proof=bindings.connect(c.ROOT,loader,scope,index,manifest["historical_predecessor_provenance"],prior["descriptors"])
            original=module.Binding(manifest["descriptors"],prepared["manifest_pin"],next_case=index)
            required=scope.extend(scope.pins(baseline["complete_semantic_source_scope"]),
                scope.pins([p["semantic_original_pin"] for p in policy.descriptors()]))
            old_projection,_=original.project(required,guard.check)
            installed=install(module,policy)
            current=module.Binding(manifest["descriptors"]+policy.descriptors(),prepared["manifest_pin"],next_case=index)
            projected,_=current.project(required,guard.check)
            a.exact({n:dict(p) for n,p in old_projection.semantic_pins.items()},
                {n:dict(p) for n,p in projected.semantic_pins.items()},"NO_SEMANTIC_INPUT_DROPPED_OR_CHANGED")
            row.update(state="PASS_DECLARED_FULL_SCOPE_CLOSED_ALIAS_PROJECTION_NOT_NATIVE_OR_PRODUCT",
                producer_pin=pin,policy_evidence=policy.evidence(),connection_proof=installed,pair_count=len(current.descriptors()),
                semantic_input_count=len(projected.semantic_pins),physical_input_count=len(projected.physical_pins),
                physical_bytes_before=sum(p["bytes"] for p in old_projection.physical_pins.values()),
                physical_bytes_after=sum(p["bytes"] for p in projected.physical_pins.values()),
                whole_current_source_byte_inventory_rechecked=False,full_worker_and_independent_oracle_connection_NOT_RUN=True)
            row["physical_bytes_saved"]=row["physical_bytes_before"]-row["physical_bytes_after"]
        q.finish();guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()),fresh_input_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["state"]="FAILED_CLOSED_PREBODY_SOURCE_PREPARATION_NOT_ADOPTED";row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PREPARATION_CLEANUP")
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","original_bytes","encoded_bytes","bytes_saved",
        "pair_count","semantic_input_count","physical_bytes_saved","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type")}))
    return 0 if row["state"].startswith(("PASS_","PREPARED_")) else 1


if __name__=="__main__":raise SystemExit(main())
