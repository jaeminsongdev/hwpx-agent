"""Fixed case165 XZ61 descriptor/decoder extension in one private namespace.

Retain seven special paths and every original nonconstructor scope/resource/
byte/handle/product oracle. This code is not a runtime entry or GO authorizer.
"""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS
import copy
import hashlib
import json
import re
import sys

SELF="tools/p09/xz_ordinary_binding_v1.py"
TEST="tools/p09/tests/test_xz_ordinary_binding_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
SPEC=dict(index=165,count=61,generation=1,mapping_sha256="38bbf083c60b66c125611e0abd136520557f2ffe952dae49c4ca356cc5ec24b5")
FULL68_DIGEST="c858a48e5c4d615e8aac8709b5e214b09a35d5533860370a035204b63fdc8026"
PROOF=dict(path=PREFIX+"xz-corpus-verification-g001-attempt001.v1.json",bytes=49841,
    sha256="1131c6351cc662a9ab23ca28c1c689a62ef4525c92c429ede5adb9a6349a1f6e")
BINDINGS=dict(path="tools/p09/current_queue_successor_binding.py",bytes=15040,
    sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915")
FRONT=dict(path="tools/p09/expanded_closed_preparation_v1.py",bytes=21675,
    sha256="8de7dc45657401ceefc05a8535114155da138f79d3d17a9c6f2491808e43fca1")


def require(ok,label):
    if not ok:raise ValueError("XZ_ORDINARY_BINDING_"+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(",",":")).encode("ascii")).hexdigest()


def is_new(row):
    return re.fullmatch(r"implementation/p09/evidence/p361-lossless-runtime-inputs/case[0-9]{3}-runtime-run[0-9]{3}\.xz8m-g00[1-8]\.envelope\.v1\.json",row["physical_envelope_pin"]["path"]) is not None


def admit(q,a,scope):
    proof=a.read_exact(q,PROOF)
    a.fields(proof,dict(state="PASS_XZ68_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_BINDING_PROFILE_OR_RUNTIME",cleanup_confirmed=True,
        pair_count=68,ordinary_pair_count=61,preserved_special_count=7,accepted_count_delta=0,GO_authorized=False,
        current_runtime_profile_changed=False,product_or_Native_executed=False,fresh_inputs=159,final_fresh_hashes=159),"QUALIFIED_PHYSICAL68_NOT_RUNTIME")
    a.fields(proof["decoder_budget"],dict(aggregate_limit_seconds=5.0,attempted_decodes=136,completed_decodes=136,
        active_decode=False,terminal_error_seen=False),"TWO_REAL_FRESH_BOUNDARIES_DECODER5")
    require(len(proof["decode_counts"])==68 and all(type(v) is int and v==2 for v in proof["decode_counts"].values()),"ALL68_ACTUAL_TWO_DECODE_COUNTS")
    for pin in proof["source_pins"]:
        if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"CURRENT_CORPUS_VERIFIER_SOURCES")
    delivery=a.read_exact(q,proof["publication_manifest_pin"])
    a.fields(delivery,dict(schema_version="hwpx-agent.p09-xz-corpus-delivery/v1",generation=1,diagnostic_only_not_runtime_adoption=True),"EXPLICIT_XZ_CORPUS_CONTEXT")
    baseline=a.read_exact(q,delivery["baseline_manifest_pin"]);rows=delivery["descriptors"]
    require(len(rows)==68 and fingerprint(rows)==FULL68_DIGEST and fingerprint([r for r in rows if is_new(r)])==SPEC["mapping_sha256"],"EXACT_CODE_PINNED_FULL68_AND_ORDINARY61")
    for old,new in zip(baseline["descriptors"],rows):
        a.exact({k:v for k,v in old.items() if k!="physical_envelope_pin"},{k:v for k,v in new.items() if k!="physical_envelope_pin"},"EVERY_LOGICAL_DESCRIPTOR_UNCHANGED")
        if not is_new(new):a.exact(new,old,"SPECIAL_DESCRIPTOR_NOT_REPLACED")
    require(len(baseline["descriptors"])==68,"FULL68_BASELINE_NOT_SUBSET")
    scope.pins([r["semantic_original_pin"] for r in rows]);scope.pins([r["physical_envelope_pin"] for r in rows])
    return baseline,rows,dict(SPEC)


def install(module,historical_pairs,xz, spec=SPEC):
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get("__name__","").startswith("p09_exact_runtime_envelope_source_projection_v1")
        and not any(getattr(m,"__dict__",None) is env for m in tuple(sys.modules.values()) if m),"PRIVATE_NAMESPACE_ONLY")
    require(type(spec) is dict and set(spec)=={"index","count","generation","mapping_sha256"}
        and type(spec["index"]) is int and spec["index"]==165 and type(spec["count"]) is int and spec["count"]==61
        and type(spec["generation"]) is int and 1<=spec["generation"]<=8
        and type(spec["mapping_sha256"]) is str and re.fullmatch("[0-9a-f]{64}",spec["mapping_sha256"]),"EXACT_PROFILE_CONTEXT")
    require(not hasattr(module,"level6_ordinary_profile"),"NEW_PROFILE_NOT_LAYERED_ON_LEVEL6")
    if hasattr(module,"xz_ordinary_profile"):
        module.exact(module.xz_ordinary_profile,spec,"ONE_EXACT_PROFILE_PER_PRIVATE_MODULE");return
    require(type(historical_pairs) in (tuple,list) and len(historical_pairs)<=249,"BOUNDED_HISTORY")
    inherited={r["semantic_original_pin"]["path"]:copy.deepcopy(r) for r in historical_pairs}
    require(len(inherited)==len(historical_pairs),"UNIQUE_HISTORICAL_PAIRS")
    seal=dict(spec);original=source.descriptor;initialize=module.Binding.__init__;original_codec=source.codec
    require(xz.SCHEMA=="hwpx-agent.p09-runtime-record-envelope-xz/v1" and xz.MAX_BYTES==original_codec.MAX_BYTES
        and xz.CHUNK_BYTES==65536 and xz.DECODE_MEMORY_LIMIT==33554432,"EXPLICIT_BOUNDED_XZ_CODEC")
    methods={n:fn for n,fn in vars(module.Binding).items() if n!="__init__"}
    projection_methods=dict(vars(source.Projection));state=dict(admitted_hashes=frozenset())
    def descriptor(old,new,*,next_case):
        if type(new) is not dict or ".xz8m-" not in str(new.get("path","")):return original(old,new,next_case=next_case)
        old=source.copy_pin(old);new=source.copy_pin(new)
        match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",old["path"])
        require(type(next_case) is int and next_case==seal["index"] and match is not None and 112<=int(match[1])<next_case,"ORDINARY_PRIOR_NOT_CURRENT")
        stem=source.PREFIX+f"case{match[1]}-runtime-run{match[2]}"
        require(new["path"]==stem+f".xz8m-g{seal['generation']:03}.envelope.v1.json","EXPLICIT_ORDINARY_GENERATION_PATH")
        prior=inherited.get(old["path"])
        before=copy.deepcopy(prior["physical_envelope_pin"]) if prior is not None else dict(new,path=stem+".envelope.v1.json")
        require(".failed." not in before["path"],"FAILED_HISTORY_RETAINED")
        expected=original(old,before,next_case=next_case)
        require(0<new["bytes"]<=original_codec.MAX_BYTES,"ORIGINAL_PHYSICAL_PARSE_BOUND")
        return dict(expected,physical_envelope_pin=new)
    def init(self,descriptors,manifest_pin,*,next_case):
        initialize(self,descriptors,manifest_pin,next_case=next_case)
        selected=[r for r in self.descriptors() if is_new(r)]
        if selected:
            require(len(self.descriptors())==68 and len(selected)==61 and fingerprint(selected)==seal["mapping_sha256"],"FULL61_EXACT_CODE_PINNED_TABLE")
            state["admitted_hashes"]=frozenset(r["physical_envelope_pin"]["sha256"] for r in selected)
    def decode(raw,checkpoint):
        require(type(raw) is bytes and 0<len(raw)<=original_codec.MAX_BYTES and callable(checkpoint),"BOUNDED_FRESH_CODEC_INPUT")
        checkpoint();identity=hashlib.sha256(raw).hexdigest();checkpoint()
        # New XZ can only be selected after a complete fixed-table constructor.
        # Unknown/new-schema inputs otherwise go to the unchanged old decoder.
        return (xz.decode if identity in state["admitted_hashes"] else original_codec.decode)(raw,checkpoint)
    routed=NS(**{**vars(original_codec),"decode":decode})
    source.descriptor=descriptor;env["descriptor"]=descriptor;source.codec=routed;env["codec"]=routed
    module.Binding.__init__=init;module.xz_ordinary_profile=dict(seal);module.xz_original_initialize=initialize
    module.xz_original_codec=original_codec
    require(all(vars(module.Binding).get(n) is fn for n,fn in methods.items()),"EVERY_ORIGINAL_NONCONSTRUCTOR_BINDING_ORACLE_RETAINED")
    require(all(vars(source.Projection).get(n) is fn for n,fn in projection_methods.items()),"EVERY_ORIGINAL_PROJECTION_METHOD_RETAINED")


@contextmanager
def bootstrap_seed(module,expected,manifest_pin):
    require(hasattr(module,"xz_original_initialize"),"PROFILE_REQUIRED_BEFORE_SEED")
    previous=module.Binding.__init__;state=dict(used=False)
    def initialize(self,descriptors,pin,*,next_case):
        if not state["used"]:
            module.exact(descriptors,[expected],"EXACT_ORIGINAL_METADATA_SEED_DESCRIPTOR")
            module.exact(pin,manifest_pin,"EXACT_ORIGINAL_METADATA_SEED_MANIFEST")
            state["used"]=True
            return module.xz_original_initialize(self,descriptors,pin,next_case=next_case)
        return previous(self,descriptors,pin,next_case=next_case)
    module.Binding.__init__=initialize
    try:
        yield state
        require(state["used"],"ORIGINAL_METADATA_SEED_MUST_ACTUALLY_RUN")
    finally:
        require(module.Binding.__init__ is initialize,"ONE_SCOPED_METADATA_SEED_OWNER")
        module.Binding.__init__=previous


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import flat_current_queue_envelope_runtime_v25 as e
    import xz_corpus_delivery_v1 as delivery
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True);args=parser.parse_args()
    delivery.identifier(args.attempt);output=PREFIX+f"xz-binding-code{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_CODE_RECORD")
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    entry_ns,_=e.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entry_ns.preparation_attributed_entry_v1
    raw,_=e.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    codecs,_=e.namespace_bundle.load(c.ROOT,[delivery.BASELINE,delivery.OLD_ENCODE,delivery.OLD,delivery.XZ],{})
    old_guard=raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard))
    def prep_guard():return codecs.owned_cpu_baseline_v1.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"))()
    guards=[];started=time.monotonic();q=None
    row=dict(state="FAILED_XZ_BINDING_CODE_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
        current_runtime_profile_changed=False,actual_parent_worker_entry_and_independent_review_NOT_RUN=True)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            for pin in (delivery.BASELINE,delivery.BASELINE_TEST):a.exact(q.pin(pin["path"]),pin,"QUALIFIED_COLD_CPU_BASELINE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            for name in (SELF,TEST):q.pin(name)
            a.exact(q.pin(BINDINGS["path"]),BINDINGS,"FROZEN_ORIGINAL_BINDING_API")
            modules,_=e.namespace_bundle.load(c.ROOT,[BINDINGS],{})
            api=modules.current_queue_successor_binding
            for pin in api.PINS:a.exact(q.pin(pin["path"]),pin,"ALL_FROZEN_BINDING_AND_CODEC_SOURCES")
            for pin in (delivery.XZ,delivery.XZ_TEST,delivery.BASELINE):a.exact(q.pin(pin["path"]),pin,"EXACT_EXTENDED_CODEC_SOURCES")
            q.pin("tools/p09/current_stored_runtime_scope.py")
            from tests import test_xz_ordinary_binding_v1 as tests
            tests.MODULE=sys.modules[__name__];tests.API=api;tests.ROOT=c.ROOT;tests.LOADER=e.namespace_bundle
            tests.SCOPE=scope;tests.CHECKPOINT=q.checkpoint;tests.XZ=codecs.receipt_xz_envelope_v1
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contract_errors"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
            a.exact(row["contracts"],dict(run=13,errors=0,failures=0,skipped=0),"ALL_XZ_BINDING13")
            baseline,rows,spec=admit(q,a,scope)
            row.update(full68_descriptor_digest=fingerprint(rows),ordinary_recompression_spec=spec,physical_corpus_proof_pin=PROOF)
        q,proof=entry.closed_bootstrap(c.ROOT,a,old_guard,prep_guard,verify_policy,verify,guards)
        row.update(state="PASS_XZ_ORDINARY_BINDING_CODE13_NOT_ENTRY_OR_PRODUCT",bootstrap_policy_validation=proof,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        samples=[s for g in guards for s in g.samples]
        row.update(cleanup_confirmed=all(g.cleanup for g in guards),elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_CODE_GUARDS_CLOSED");raw.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","contracts","contract_errors","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
