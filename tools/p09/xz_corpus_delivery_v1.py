"""Exclusive XZ delivery and independent full68 physical-boundary closure.

Ordinary61 get explicit generation paths. The seven exceptional descriptors
are byte-for-byte retained. Original/profile/Native/acceptance writes forbidden.
Published bytes do not become a runtime profile through this module.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import re
import sys

SELF="tools/p09/xz_corpus_delivery_v1.py"
TEST="tools/p09/tests/test_xz_corpus_delivery_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
MEASUREMENT=dict(path=PREFIX+"xz-corpus-diagnostic001.v1.json",bytes=111163,
    sha256="c3d6f9aad61a4d88755e8e95aceb074b57f67a87bcc2861c6891e83f14d388c7")
BASELINE=dict(path="tools/p09/owned_cpu_baseline_v1.py",bytes=1389,
    sha256="0fce7a5f5700270291b02167e96c3739943d5a44c0a912eef43555a1a729b4b5")
BASELINE_TEST=dict(path="tools/p09/tests/test_owned_cpu_baseline_v1.py",bytes=1797,
    sha256="22a458b2f288ea4d95fdb76f01f6c97b46ddf99cbe55969ee550b52d3ff81429")
XZ=dict(path="tools/p09/receipt_xz_envelope_v1.py",bytes=4012,
    sha256="21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09")
XZ_TEST=dict(path="tools/p09/tests/test_receipt_xz_envelope_v1.py",bytes=3798,
    sha256="826367a161a72a97ebe4855009970cfa5b0faf8eb8006889f2d01dd1f197a413")
OLD=dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,
    sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f")
OLD_ENCODE=dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,
    sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5")
PHYSICAL=dict(path="tools/p09/runtime_envelope_physical_io_v1.py",bytes=7214,
    sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c")
ORDINARY_DIGEST="519e89382d5e1032324a6378394e8913ca2d51eb97fe6c6445b382404870d9ad"
PUBLICATION="PASS_XZ61_EXCLUSIVE_PUBLICATION_NOT_FULL68_OR_RUNTIME"
VERIFICATION="PASS_XZ68_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_BINDING_PROFILE_OR_RUNTIME"


def require(ok,label):
    if not ok:raise ValueError("XZ_DELIVERY_"+label)


def digest(rows):
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,sort_keys=True,allow_nan=False,separators=(",",":")).encode("ascii")).hexdigest()


def identifier(value):
    require(type(value) is int and 1<=value<=8,"FINITE_IDENTIFIER")
    return value


def plan(rows,measurement,generation):
    identifier(generation)
    require(type(rows) is list and len(rows)==68,"FULL68_BASELINE")
    require(measurement["state"]=="PASS_ORDINARY61_XZ_MEASUREMENT_NOT_FULL68_PROFILE_OR_RUNTIME"
        and measurement["cleanup_confirmed"] is True and measurement["GO_authorized"] is False
        and type(measurement["accepted_count_delta"]) is int and measurement["accepted_count_delta"]==0
        and measurement["Native_or_product_executed"] is False
        and measurement["fresh_inputs"]==measurement["final_fresh_hashes"]==211,"CLOSED_MEASUREMENT_ONLY")
    budget=measurement["decoder_budget"]
    require(budget["aggregate_limit_seconds"]==5. and budget["attempted_decodes"]==budget["completed_decodes"]==122
        and 0<=budget["elapsed_decoder_work_seconds"]<5 and budget["active_decode"] is False
        and budget["terminal_error_seen"] is False,"UNCHANGED_QUALIFIED_DECODER5")
    ordinary=[r for r in rows if r["physical_envelope_pin"]["path"].endswith(".level6.envelope.v1.json")]
    require(len(ordinary)==61 and digest(ordinary)==ORDINARY_DIGEST,"FROZEN_ORDINARY61_TABLE")
    samples=measurement["candidates"]
    require(type(samples) is list and len(samples)==61,"FULL61_MEASUREMENTS")
    indexed={sample["semantic_original_pin"]["path"]:sample for sample in samples}
    require(len(indexed)==61,"UNIQUE61_MEASUREMENTS")
    result=[];special=[]
    for row in rows:
        require(type(row) is dict and set(row)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"}
            and row["schema_version"]=="hwpx-agent.p09-lossless-runtime-source-projection/v1"
            and type(row["next_case"]) is int and row["next_case"]==165,"EXACT_DESCRIPTOR_CONTEXT")
        if row in ordinary:
            sample=indexed.pop(row["semantic_original_pin"]["path"],None)
            require(sample is not None and sample["semantic_original_pin"]==row["semantic_original_pin"]
                and sample["existing_physical_pin"]==row["physical_envelope_pin"],"EXACT_MEASUREMENT_BASELINE")
            pin=copy.deepcopy(sample["proposed_physical_pin"])
            expected=row["physical_envelope_pin"]["path"].removesuffix(".level6.envelope.v1.json")+".xz8m.envelope.v1.json"
            require(pin["path"]==expected and type(pin["bytes"]) is int and 0<pin["bytes"]<=16*1048576
                and type(pin["sha256"]) is str and re.fullmatch("[0-9a-f]{64}",pin["sha256"]),"EXPLICIT_MEASURED_NEW_FORMAT")
            pin["path"]=expected.removesuffix(".xz8m.envelope.v1.json")+f".xz8m-g{generation:03}.envelope.v1.json"
            result.append(dict(copy.deepcopy(row),physical_envelope_pin=pin))
        else:special.append(copy.deepcopy(row));result.append(copy.deepcopy(row))
    require(not indexed and len(special)==7 and special==measurement["special_descriptors_unchanged"],"SEVEN_SPECIAL_DESCRIPTORS_UNCHANGED")
    require(len({r["semantic_original_pin"]["path"] for r in result})==len({r["physical_envelope_pin"]["path"] for r in result})==68,"FULL68_BIJECTION")
    return result


def is_xz(row):
    return re.fullmatch(r"implementation/p09/evidence/p361-lossless-runtime-inputs/case[0-9]{3}-runtime-run[0-9]{3}\.xz8m-g00[1-8]\.envelope\.v1\.json",row["physical_envelope_pin"]["path"]) is not None


def verify_decoded(raw,original):
    require(type(raw) is bytes and len(raw)==original["bytes"] and hashlib.sha256(raw).hexdigest()==original["sha256"],"EXACT_LOGICAL_ORIGINAL_BYTES")


def decode_seed(raw,original,decode,budget):
    decoded=budget.run(lambda check:decode(raw,check))
    verify_decoded(decoded,original)
    return decoded


def resource_observation(metrics,phase,sample):
    require(phase in ("bootstrap_policy","bootstrap_connection","admission","read_seed","encode","write","read_candidate","decode_candidate","finish"),"BOUNDED_OPERATION_PHASE")
    row=metrics.setdefault(phase,dict(fresh_samples=0,system_CPU_max=None,parent_CPU_max=None,
        parent_CPU_missing_samples=0,available_RAM_min=None,parent_private_percent_max=None))
    row["fresh_samples"]+=1
    for field,key,maximum in (("system_cpu_percent","system_CPU_max",True),("parent_cpu_machine_percent","parent_CPU_max",True),
        ("available_ram_percent","available_RAM_min",False),("parent_private_percent","parent_private_percent_max",True)):
        value=sample.get(field)
        if type(value) in (int,float) and math.isfinite(value):
            row[key]=value if row[key] is None else (max(row[key],value) if maximum else min(row[key],value))
        elif field=="parent_cpu_machine_percent":row["parent_CPU_missing_samples"]+=1


def observed_guard(original,metrics,phase):
    class Guard(original):
        def check(self,force=False):
            before=len(self.samples)
            try:return super().check(force=force)
            finally:
                # Reuse only original fresh samples, including its stopping sample.
                # No new Windows call, counter, sampler, forced sample, or retry.
                for sample in self.samples[before:]:resource_observation(metrics,phase["value"],sample)
    return Guard


def reader_type(original,pairs,budget,xz,old,counts,exact):
    bindings={r["physical_envelope_pin"]["path"]:r for r in pairs}
    require(len(bindings)==68,"WHOLE68_READER_BINDINGS")
    class Reader(original):
        def _read(self,name,parse=False):
            if name not in bindings:return super()._read(name,parse=parse)
            pin,buffer=super()._read(name,parse=True);pair=bindings[name]
            exact(pin,pair["physical_envelope_pin"],"FRESH_EXPLICIT_PHYSICAL_PIN")
            decoder=xz.decode if is_xz(pair) else old.decode
            decoded=budget.run(lambda check:decoder(bytes(buffer),check))
            verify_decoded(decoded,pair["semantic_original_pin"])
            counts[name]=counts.get(name,0)+1
            return pin,buffer if parse else None
    return Reader


def main():
    import argparse,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as e
    import owned_source_read_pressure as bytes_policy
    parser=argparse.ArgumentParser();modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--publish",action="store_true");modes.add_argument("--verify",action="store_true")
    parser.add_argument("--generation",type=int,required=True);parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--publication-attempt",type=int)
    args=parser.parse_args();generation=identifier(args.generation);attempt=identifier(args.attempt)
    require((args.publish and args.publication_attempt is None) or (args.verify and args.publication_attempt is not None),"EXACT_PHASE_ARGUMENTS")
    if args.verify:identifier(args.publication_attempt)
    phase="publication" if args.publish else "verification"
    output=PREFIX+f"xz-corpus-{phase}-g{generation:03}-attempt{attempt:03}.v1.json"
    manifest_name=PREFIX+f"xz-corpus-manifest-g{generation:03}-attempt{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists() and (not args.publish or not(c.ROOT/manifest_name).exists()),"EXCLUSIVE_PHASE_OUTPUT")
    def dynamic(path):
        raw=(c.ROOT/path).read_bytes();return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    entry_ns,_=e.namespace_bundle.load(c.ROOT,[dynamic("tools/p09/preparation_attributed_entry_v1.py")],{})
    entry=entry_ns.preparation_attributed_entry_v1
    raw,_=e.namespace_bundle.load(c.ROOT,[entry.ENTRY,entry.POLICY_SOURCE]+entry.UTIL_PINS,{})
    raw.prepared_run_closure_v1.configure_host_policy(c);policy=raw.preparation_attributed_cpu_v1
    code,_=e.namespace_bundle.load(c.ROOT,[BASELINE,OLD_ENCODE,OLD,XZ],{})
    baseline=code.owned_cpu_baseline_v1;xz=code.receipt_xz_envelope_v1;old=code.runtime_record_envelope_v2
    resource_summary={};phase_info=dict(value="bootstrap_policy")
    original_guard=observed_guard(raw.terminal_metadata_pressure_v1.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard)),resource_summary,phase_info)
    def preparation_guard():
        if phase_info["value"]=="bootstrap_policy":phase_info["value"]="bootstrap_connection"
        return observed_guard(baseline.guard_type(policy.guard_type(raw.distinct_final_sample_guard_v1.guard_type(a.Guard),role="whole_metadata_preflight")),resource_summary,phase_info)()
    bootstrap=[];guard=None;q=None;budget=None;counts={};started=time.monotonic()
    publisher=raw.successor_preparation_workspace_v1
    row=dict(state="FAILED_XZ_CORPUS_"+phase.upper()+"_NOT_ADOPTED",generation=generation,attempt=attempt,
        files_created=[],files_reused=[],completed_pairs=[],product_or_Native_executed=False,accepted_count_delta=0,
        GO_authorized=False,original_or_existing_derivative_rewritten=False,current_runtime_profile_changed=False,
        actual_binding_parent_worker_and_independent_oracle_NOT_RUN=True,automatic_retry=False)
    def stage(name):phase_info["value"]=name
    try:
        def verify_policy(q):
            entry.policy_witnesses(q,a,policy)
            for pin in (BASELINE,BASELINE_TEST):a.exact(q.pin(pin["path"]),pin,"MEASURED_CPU_BASELINE_CODE")
            from tests import test_owned_cpu_baseline_v1 as tests
            tests.MODULE=baseline
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            a.exact(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
                dict(run=3,errors=0,failures=0,skipped=0),"BASELINE3_BEFORE_PREPARATION_USE")
            row["baseline_contracts"]=3
        def verify_connection(q):
            stage("bootstrap_connection")
            entry.witnesses(q,a,policy,connection_attempt=10)
            for pin in (BASELINE,BASELINE_TEST,OLD_ENCODE,OLD,XZ,XZ_TEST,PHYSICAL):a.exact(q.pin(pin["path"]),pin,"ALL_EXACT_DELIVERY_DEPENDENCIES")
            for name in (SELF,TEST):q.pin(name)
            from tests import test_receipt_xz_envelope_v1 as codec_tests
            from tests import test_xz_corpus_delivery_v1 as delivery_tests
            codec_tests.MODULE=xz;delivery_tests.MODULE=sys.modules[__name__]
            suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module) for module in (codec_tests,delivery_tests))
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=17,errors=0,failures=0,skipped=0),"ALL_DELIVERY17")
        admission,proof=entry.closed_bootstrap(c.ROOT,a,original_guard,preparation_guard,verify_policy,verify_connection,bootstrap)
        row["bootstrap_policy_validation"]=proof
        stage("admission");guard=preparation_guard();guard.acquire()
        # The frozen original DecoderBudget is shared by both actual read boundaries.
        physical_ns,_=e.namespace_bundle.load(c.ROOT,[PHYSICAL],{"runtime_envelope_source_projection_v1":__import__("runtime_envelope_source_projection_v1"),"owned_source_read_pressure":bytes_policy})
        physical=physical_ns.runtime_envelope_physical_io_v1
        budget=physical.DecoderBudget(guard.check);q=a.AcceptanceReader(c.ROOT,guard.check)
        for pin in admission.snapshots.values():a.exact(q.pin(pin["path"]),pin,"FRESH_ALL_CLOSED_DELIVERY_SOURCES")
        measured=a.read_exact(q,MEASUREMENT);manifest=a.read_exact(q,measured["source_manifest_pin"])
        pairs=plan(manifest["descriptors"],measured,generation)
        row.update(baseline_manifest_pin=measured["source_manifest_pin"],measurement_pin=MEASUREMENT,
            ordinary_descriptor_digest=digest([r for r in pairs if is_xz(r)]),full68_descriptor_digest=digest(pairs))
        if args.publish:
            pacer=bytes_policy.OwnedPacer()
            row["seed_policy"]="fresh_exact_existing_lossless_bytes_or_exact_already_published_candidate_not_raw_original_replay"
            for pair in pairs:
                if not is_xz(pair):continue
                logical,new=pair["semantic_original_pin"],pair["physical_envelope_pin"]
                destination=c.ROOT/new["path"]
                require(not destination.is_symlink() and not destination.is_junction(),"DIRECT_NEW_DESTINATION")
                if destination.exists():row["files_reused"].append(new["path"])
                else:
                    stage("read_seed")
                    previous=next(r["physical_envelope_pin"] for r in manifest["descriptors"] if r["semantic_original_pin"]==logical)
                    pin,buffer=q._read(previous["path"],parse=True);q._bind(previous["path"],pin);a.exact(pin,previous,"FRESH_EXISTING_LOSSLESS_SEED")
                    original=decode_seed(bytes(buffer),logical,old.decode,budget);del buffer
                    stage("encode")
                    encoded=xz.encode(original,guard.check)
                    a.exact(dict(path=new["path"],bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest()),new,"EXACT_PREVIOUSLY_MEASURED_ENCODING")
                    stage("write")
                    physical.publish_exclusive(c.ROOT,encoded,new,guard.check,write_pacer=pacer)
                    row["files_created"].append(new["path"]);del encoded,original
                stage("read_candidate")
                pin,buffer=q._read(new["path"],parse=True);q._bind(new["path"],pin);a.exact(pin,new,"FRESH_PUBLISHED_OR_REUSED_BYTES")
                stage("decode_candidate")
                decoded=decode_seed(bytes(buffer),logical,xz.decode,budget)
                row["completed_pairs"].append(pair);del buffer,decoded
            require(len(row["completed_pairs"])==61,"ALL61_PUBLICATION_COMPLETE")
            delivery=dict(schema_version="hwpx-agent.p09-xz-corpus-delivery/v1",generation=generation,
                diagnostic_only_not_runtime_adoption=True,baseline_manifest_pin=measured["source_manifest_pin"],measurement_pin=MEASUREMENT,descriptors=pairs)
            manifest_pin=publisher.publish(c.ROOT,manifest_name,delivery,a)
            a.exact(q.pin(manifest_name),manifest_pin,"EXCLUSIVE_DELIVERY_MANIFEST")
            row.update(publication_manifest_pin=manifest_pin,two_fresh_decode_boundaries_NOT_RUN=True)
        else:
            pub_name=PREFIX+f"xz-corpus-publication-g{generation:03}-attempt{args.publication_attempt:03}.v1.json"
            publication=q.json(pub_name)
            a.fields(publication,dict(state=PUBLICATION,cleanup_confirmed=True,product_or_Native_executed=False,accepted_count_delta=0,
                GO_authorized=False,generation=generation,current_runtime_profile_changed=False),"CLOSED_PUBLICATION_NOT_RUNTIME")
            require(publication["fresh_inputs"]==publication["final_fresh_hashes"]>0 and len(publication["completed_pairs"])==61,"FULL61_CLOSED_PUBLICATION")
            for pin in publication["source_pins"]:
                if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"UNCHANGED_PUBLICATION_CODE")
            delivery=a.read_exact(q,publication["publication_manifest_pin"])
            a.fields(delivery,dict(schema_version="hwpx-agent.p09-xz-corpus-delivery/v1",generation=generation,
                diagnostic_only_not_runtime_adoption=True,baseline_manifest_pin=measured["source_manifest_pin"],measurement_pin=MEASUREMENT),"EXACT_DELIVERY_CONTEXT")
            a.exact(delivery["descriptors"],pairs,"INDEPENDENT_FULL68_RECONSTRUCTION")
            previous=q;Reader=reader_type(a.AcceptanceReader,pairs,budget,xz,old,counts,a.exact)
            q=Reader(c.ROOT,guard.check)
            for pin in previous.snapshots.values():a.exact(q.pin(pin["path"]),pin,"ALL_METADATA_IN_REAL_TWO_BOUNDARY_READER")
            for pair in pairs:a.exact(q.pin(pair["physical_envelope_pin"]["path"]),pair["physical_envelope_pin"],"FIRST_REAL_FULL68_DECODE")
            row.update(publication_receipt_pin=q.snapshots[pub_name],publication_manifest_pin=publication["publication_manifest_pin"])
        stage("finish");q.finish();guard.check(force=True)
        if args.verify:
            require(len(counts)==68 and all(v==2 for v in counts.values()) and budget.attempts==budget.completed==136
                and budget.active is None and budget.error is None,"ALL68_TWO_REAL_FRESH_DECODE_BOUNDARIES")
        row.update(state=PUBLICATION if args.publish else VERIFICATION,pair_count=68,ordinary_pair_count=61,preserved_special_count=7,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            decode_counts=counts,physical_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in pairs))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
        if q is not None:row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    finally:
        if guard is not None:guard.close()
        samples=[s for g in bootstrap for s in g.samples]+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=all(g.cleanup for g in bootstrap) and (guard is None or guard.cleanup),
            operation_phase_at_end=phase_info["value"],original_fresh_sample_resource_summary=resource_summary,
            resource_observer_extra_sampler_or_Windows_calls=False,
            decoder_budget=None if budget is None else budget.evidence(),elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    require(row["cleanup_confirmed"],"ALL_DELIVERY_GUARDS_CLOSED");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","contracts","pair_count","fresh_inputs","final_fresh_hashes","decoder_budget",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"] in (PUBLICATION,VERIFICATION) else 1


if __name__=="__main__":raise SystemExit(main())
