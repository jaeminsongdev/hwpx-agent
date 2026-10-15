"""Serial three-receipt measurement, not a new corpus/profile/runtime.

Originals/derivatives stay read-only. Encoded candidates stay in memory.
Only an exclusive diagnostic receipt is published after owned guard cleanup.
"""
from pathlib import Path
from types import FunctionType
import re
import sys

SELF="tools/p09/probe_receipt_codec_candidates_v1.py"
TEST="tools/p09/tests/test_probe_receipt_codec_candidates_v1.py"
XZ_SOURCE="tools/p09/receipt_xz_envelope_v1.py"
XZ_TEST="tools/p09/tests/test_receipt_xz_envelope_v1.py"
BASELINE_SOURCE="tools/p09/owned_cpu_baseline_v1.py"
BASELINE_TEST="tools/p09/tests/test_owned_cpu_baseline_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
PINS=[
    dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f")]
PHYSICAL=dict(path="tools/p09/runtime_envelope_physical_io_v1.py",bytes=7214,
    sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c")


def require(ok,label):
    if not ok:raise ValueError("CODEC_CANDIDATE_PROBE_"+label)


def deflate9(original):
    require(type(original) is FunctionType and original.__globals__.get("__name__","").startswith("p09_exact_")
        and original.__name__=="encode" and original.__code__.co_filename.replace("\\","/").endswith("runtime_record_envelope_v1.py"),"PRIVATE_FROZEN_ENCODER")
    before=original.__code__;values=list(before.co_consts)
    slots=[i for i,v in enumerate(values) if type(v) is int and v==1]
    require(len(slots)==1 and not any(type(v) is int and v==9 for v in values),"ONE_EXACT_COMPRESSION_LEVEL")
    i=slots[0];values[i]=9;changed=before.replace(co_consts=tuple(values));undo=list(changed.co_consts);undo[i]=1
    require(changed.replace(co_consts=tuple(undo))==before,"ENTIRE_ENCODER_CODE_INVERSE")
    fn=FunctionType(changed,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    fn.__kwdefaults__=original.__kwdefaults__;return fn


def select(rows):
    require(type(rows) is list and len(rows)==68,"FULL68_MANIFEST")
    originals=set();physical=set();eligible=[]
    for row in rows:
        require(type(row) is dict and set(row)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"}
            and row["schema_version"]=="hwpx-agent.p09-lossless-runtime-source-projection/v1"
            and type(row["next_case"]) is int and row["next_case"]==165,"CLOSED_CURRENT_CONTEXT")
        old,new=row["semantic_original_pin"],row["physical_envelope_pin"]
        require(old["path"] not in originals and new["path"] not in physical,"BIJECTIVE_MANIFEST")
        originals.add(old["path"]);physical.add(new["path"])
        if new["path"].endswith(".level6.envelope.v1.json"):
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",old["path"])
            require(match is not None and 112<=int(match[1])<165
                and new["path"]==f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{match[1]}-runtime-run{match[2]}.level6.envelope.v1.json","ORDINARY_ONLY_NOT_CURRENT_OR_FAILED")
            eligible.append(row)
    require(len(eligible)==61,"ALL61_ORDINARY_IDENTIFIED")
    return sorted(eligible,key=lambda row:(-row["physical_envelope_pin"]["bytes"],row["semantic_original_pin"]["path"]))[:3]


def main():
    import argparse,hashlib,io,json,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as e
    import runtime_envelope_physical_io_v1 as physical
    import owned_cpu_baseline_v1 as baseline
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();require(type(args.attempt) is int and 1<=args.attempt<=8,"BOUNDED_DIAGNOSTIC_ATTEMPT")
    output=PREFIX+f"codec-candidate-sample{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_DIAGNOSTIC_RECORD")
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    helpers,_=e.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=helpers.preparation_attributed_entry_v1
    raw,_=e.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    codecs,_=e.namespace_bundle.load(c.ROOT,PINS+[dynamic(XZ_SOURCE)],{})
    old=codecs.runtime_record_envelope_v2;new=codecs.receipt_xz_envelope_v1;level9=deflate9(codecs.runtime_record_envelope_v1.encode)
    original_guard=raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard))
    candidate_guard=baseline.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"))
    publisher=raw.successor_preparation_workspace_v1;bootstrap=[];guard=None;q=None;started=time.monotonic();budgets={}
    row=dict(state="FAILED_RECEIPT_CODEC_SAMPLE_NOT_ADOPTED",samples=[],accepted_count_delta=0,GO_authorized=False,
        Native_or_product_executed=False,derivative_files_published=False,original_or_existing_derivative_rewritten=False,
        current_runtime_profile_changed=False,whole61_corpus_or_decoder5_NOT_RUN=True)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            for path in (BASELINE_SOURCE,BASELINE_TEST):q.pin(path)
            from tests import test_owned_cpu_baseline_v1 as baseline_tests
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(baseline_tests))
            row["baseline_contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["baseline_contracts"],dict(run=3,errors=0,failures=0,skipped=0),"ALL_COLD_BASELINE3_BEFORE_USE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            for path in (SELF,TEST,XZ_SOURCE,XZ_TEST):q.pin(path)
            for pin in PINS+[PHYSICAL]:a.exact(q.pin(pin["path"]),pin,"EXACT_SAMPLE_COMPONENTS")
            from tests import test_receipt_xz_envelope_v1 as codec_tests
            from tests import test_probe_receipt_codec_candidates_v1 as probe_tests
            codec_tests.MODULE=new;probe_tests.MODULE=sys.modules[__name__];probe_tests.ENCODER=codecs.runtime_record_envelope_v1.encode;probe_tests.DECODER=old.decode
            suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in (codec_tests,probe_tests))
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"ALL_CODEC_SAMPLE9")
        admission,proof=entry.closed_bootstrap(c.ROOT,a,original_guard,candidate_guard,
            verify_policy,verify,bootstrap)
        row["bootstrap_policy_validation"]=proof
        guard=candidate_guard();guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in admission.snapshots.values():a.exact(q.pin(pin["path"]),pin,"ALL_FRESH_SAMPLE_SOURCE_WITNESSES")
        graph=q.json(PREFIX+"successor-connections008.v10.json")
        a.fields(graph,dict(index=165,state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            cleanup_confirmed=True,product_or_Native_executed=False,GO_authorized=False),"CURRENT_UNCHANGED_GRAPH")
        manifest=a.read_exact(q,graph["manifest_pin"]);pairs=select(manifest["descriptors"])
        budgets={name:physical.DecoderBudget(guard.check) for name in ("baseline","deflate9","xz8m")}
        for pair in pairs:
            logical,encoded=pair["semantic_original_pin"],pair["physical_envelope_pin"]
            pin,buffer=q._read(logical["path"],parse=True);q._bind(logical["path"],pin);a.exact(pin,logical,"FRESH_RAW_ORIGINAL")
            original=bytes(buffer);del buffer
            pin,buffer=q._read(encoded["path"],parse=True);q._bind(encoded["path"],pin);a.exact(pin,encoded,"FRESH_CURRENT_LEVEL6")
            current=bytes(buffer);del buffer
            sample=dict(original_pin=logical,existing_physical_pin=encoded,candidates={})
            for name,encode,decode in (("baseline",None,old.decode),("deflate9",level9,old.decode),("xz8m",new.encode,new.decode)):
                tick=time.process_time();candidate=current if encode is None else encode(original,guard.check)
                encode_cpu=time.process_time()-tick;tick=time.process_time()
                for _ in range(2):a.exact(budgets[name].run(lambda check:decode(candidate,check)),original,"TWO_FRESH_EXACT_DECODES")
                sample["candidates"][name]=dict(encoded_bytes=len(candidate),encoded_sha256=hashlib.sha256(candidate).hexdigest(),
                    encode_CPU_seconds=encode_cpu,two_decode_CPU_seconds=time.process_time()-tick,bytes_saved=len(current)-len(candidate))
                if name!="baseline":del candidate
            row["samples"].append(sample);del original,current
        q.finish();guard.check(force=True)
        row.update(state="PASS_THREE_REAL_RECEIPT_CODEC_SAMPLES_NOT_CORPUS_PROFILE_OR_RUNTIME",
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            selected_samples=3,ordinary_table_unchanged=61,preserved_special_table_unchanged=7,
            savings_bytes={name:sum(s["candidates"][name]["bytes_saved"] for s in row["samples"]) for name in budgets},
            XZ_dictionary_bytes=new.DICTIONARY_BYTES,XZ_decoder_memory_limit=new.DECODE_MEMORY_LIMIT,
            chunk_bound_bytes=new.CHUNK_BYTES,one_frozen_encoder_constant_inverse=True,
            sample_budget_not_whole_corpus_budget=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        if guard is not None:guard.close()
        samples=[s for g in bootstrap for s in g.samples]+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=all(g.cleanup for g in bootstrap) and (guard is None or guard.cleanup),
            first_preparation_parent_CPU_machine_percent=bootstrap[1].samples[0].get("parent_cpu_machine_percent") if len(bootstrap)>1 and bootstrap[1].samples else None,
            decoder_budgets={name:budget.evidence() for name,budget in budgets.items()},elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_SAMPLE_GUARDS_CLOSED");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","contracts","selected_samples","savings_bytes","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
