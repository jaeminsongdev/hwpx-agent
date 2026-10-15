"""Measure all 61 ordinary XZ candidates, without publishing derivatives.

The original full68 mapping and seven special descriptors remain unchanged.
Both real reads and closing hashes are required. This is not a worker profile,
full68 oracle, Native permission, or acceptance. No automatic retry.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

SELF="tools/p09/probe_receipt_xz_corpus_v1.py"
TEST="tools/p09/tests/test_probe_receipt_xz_corpus_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
EXPECTED_TABLE="519e89382d5e1032324a6378394e8913ca2d51eb97fe6c6445b382404870d9ad"


def require(ok,label):
    if not ok:raise ValueError("XZ_CORPUS_PROBE_"+label)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(",",":")).encode("ascii")).hexdigest()


def ordinary(rows,sample):
    sample.select(rows)  # Full68, bijection, ordinary61, prior-case path policy.
    selected=[row for row in rows if row["physical_envelope_pin"]["path"].endswith(".level6.envelope.v1.json")]
    require(len(selected)==61 and fingerprint(selected)==EXPECTED_TABLE,"EXACT_FROZEN_ORDINARY61_MAPPING")
    return selected


def proposed_pin(row,encoded):
    before=row["physical_envelope_pin"]["path"]
    require(before.endswith(".level6.envelope.v1.json") and type(encoded) is bytes and bool(encoded),"ORDINARY_NONEMPTY_CANDIDATE")
    return dict(path=before.removesuffix(".level6.envelope.v1.json")+".xz8m.envelope.v1.json",
        bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as e
    import runtime_envelope_physical_io_v1 as physical
    import owned_cpu_baseline_v1 as baseline
    import probe_receipt_codec_candidates_v1 as sample
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();require(type(args.attempt) is int and 1<=args.attempt<=8,"BOUNDED_EXPLICIT_ATTEMPT")
    output=PREFIX+f"xz-corpus-diagnostic{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_DIAGNOSTIC_RECORD")
    def dynamic(path):
        data=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    helpers,_=e.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=helpers.preparation_attributed_entry_v1
    raw,_=e.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    codecs,_=e.namespace_bundle.load(c.ROOT,sample.PINS+[dynamic(sample.XZ_SOURCE)],{})
    old=codecs.runtime_record_envelope_v2;new=codecs.receipt_xz_envelope_v1
    original_guard=raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard))
    candidate_guard=baseline.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight"))
    publisher=raw.successor_preparation_workspace_v1;bootstrap=[];guard=None;q=None;started=time.monotonic();budget=None
    row=dict(state="FAILED_ORDINARY61_XZ_DIAGNOSTIC_NOT_ADOPTED",candidates=[],accepted_count_delta=0,
        GO_authorized=False,Native_or_product_executed=False,derivative_files_published=False,
        original_or_existing_derivative_rewritten=False,current_runtime_profile_changed=False,
        full68_oracle_NOT_RUN=True,automatic_retry=False)
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            for path in (sample.BASELINE_SOURCE,sample.BASELINE_TEST):q.pin(path)
            from tests import test_owned_cpu_baseline_v1 as tests
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["baseline_contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["baseline_contracts"],dict(run=3,errors=0,failures=0,skipped=0),"ALL_COLD_BASELINE3_BEFORE_USE")
        def verify(q):
            entry.witnesses(q,a,policy,connection_attempt=10)
            for path in (SELF,TEST,sample.SELF,sample.TEST,sample.XZ_SOURCE,sample.XZ_TEST):q.pin(path)
            for pin in sample.PINS+[sample.PHYSICAL]:a.exact(q.pin(pin["path"]),pin,"FROZEN_CODEC_COMPONENTS")
            from tests import test_receipt_xz_envelope_v1 as codec_tests
            from tests import test_probe_receipt_codec_candidates_v1 as sample_tests
            from tests import test_probe_receipt_xz_corpus_v1 as corpus_tests
            codec_tests.MODULE=new;sample_tests.MODULE=sample;sample_tests.ENCODER=codecs.runtime_record_envelope_v1.encode;sample_tests.DECODER=old.decode
            corpus_tests.MODULE=sys.modules[__name__];corpus_tests.SAMPLE=sample
            suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in (codec_tests,sample_tests,corpus_tests))
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"ALL_CODEC_AND_CORPUS12")
        admission,proof=entry.closed_bootstrap(c.ROOT,a,original_guard,candidate_guard,verify_policy,verify,bootstrap)
        row["bootstrap_policy_validation"]=proof
        guard=candidate_guard();guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in admission.snapshots.values():a.exact(q.pin(pin["path"]),pin,"ALL_FRESH_CORPUS_SOURCE_WITNESSES")
        graph=q.json(PREFIX+"successor-connections008.v10.json")
        a.fields(graph,dict(index=165,state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            cleanup_confirmed=True,product_or_Native_executed=False,GO_authorized=False),"UNCHANGED_CURRENT_GRAPH")
        manifest=a.read_exact(q,graph["manifest_pin"]);pairs=ordinary(manifest["descriptors"],sample)
        row["special_descriptors_unchanged"]=[r for r in manifest["descriptors"] if r not in pairs]
        require(len(row["special_descriptors_unchanged"])==7,"ALL_SEVEN_SPECIAL_DESCRIPTORS_PRESERVED")
        budget=physical.DecoderBudget(guard.check)
        row["source_manifest_pin"]=graph["manifest_pin"]
        for pair in pairs:
            logical,encoded=pair["semantic_original_pin"],pair["physical_envelope_pin"]
            pin,buffer=q._read(logical["path"],parse=True);q._bind(logical["path"],pin);a.exact(pin,logical,"FRESH_RAW_ORIGINAL")
            original=bytes(buffer);del buffer
            pin,buffer=q._read(encoded["path"],parse=True);q._bind(encoded["path"],pin);a.exact(pin,encoded,"FRESH_EXISTING_PHYSICAL")
            current=bytes(buffer);del buffer
            tick=time.process_time();candidate=new.encode(original,guard.check);encode_cpu=time.process_time()-tick
            # The candidate's two actual decodes share the unchanged wall5 budget.
            # Old bytes are freshly bound here, not re-labelled as new-format bytes.
            tick=time.process_time()
            for _ in range(2):a.exact(budget.run(lambda check:new.decode(candidate,check)),original,"TWO_EXACT_CANDIDATE_DECODES")
            require(old.decode(current,guard.check)==original,"EXISTING_ENCODING_ALSO_MATCHES_ORIGINAL")
            row["candidates"].append(dict(semantic_original_pin=logical,existing_physical_pin=encoded,
                proposed_physical_pin=proposed_pin(pair,candidate),encode_CPU_seconds=encode_cpu,
                candidate_two_decode_and_existing_decode_CPU_seconds=time.process_time()-tick))
            del original,current,candidate
        q.finish();guard.check(force=True)
        before=sum(r["existing_physical_pin"]["bytes"] for r in row["candidates"])
        after=sum(r["proposed_physical_pin"]["bytes"] for r in row["candidates"])
        require(len(row["candidates"])==61 and before>after>0,"COMPLETE61_MEASURED_SAVING")
        row.update(state="PASS_ORDINARY61_XZ_MEASUREMENT_NOT_FULL68_PROFILE_OR_RUNTIME",
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            ordinary_pair_count=61,special_descriptor_count=7,semantic_original_bytes=sum(r["semantic_original_pin"]["bytes"] for r in row["candidates"]),
            existing_physical_bytes=before,proposed_physical_bytes=after,bytes_saved=before-after,
            unchanged_other_IO_formula_saving_seconds=(before-after)/1048576,
            formula_saving_NOT_new_dispatch_budget_or_GO=True,proposed_mapping_sha256=fingerprint(row["candidates"]),
            XZ_dictionary_bytes=new.DICTIONARY_BYTES,XZ_decoder_memory_limit=new.DECODE_MEMORY_LIMIT,chunk_bound_bytes=new.CHUNK_BYTES)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        if guard is not None:guard.close()
        samples=[s for g in bootstrap for s in g.samples]+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=all(g.cleanup for g in bootstrap) and (guard is None or guard.cleanup),
            completed_candidate_pairs=len(row["candidates"]),decoder_budget=None if budget is None else budget.evidence(),
            elapsed_seconds=time.monotonic()-started,CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_CORPUS_GUARDS_CLOSED");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","contracts","completed_candidate_pairs","existing_physical_bytes","proposed_physical_bytes",
        "bytes_saved","fresh_inputs","final_fresh_hashes","decoder_budget","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
