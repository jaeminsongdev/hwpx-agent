"""Full68 unchanged + one failed same-case carrier, two real disk decodes.

Layer the existing full68 physical reader and exact Native008 carrier reader;
share one original five-second DecoderBudget. No descriptor-policy weakening,
Native source mapping installation, product execution or acceptance authority.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF="tools/p09/verify_native008_full69_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
PUBLICATION=dict(path=PREFIX+"native008-carrier-g001-attempt001.v1.json",bytes=6985,
    sha256="08693e9b6b1dcb98c9f739516e84d005eacafa577abf0394c5f503835dda9732")
PRIOR=dict(path=PREFIX+"xz-corpus-verification-g001-attempt001.v1.json",bytes=49841,
    sha256="1131c6351cc662a9ab23ca28c1c689a62ef4525c92c429ede5adb9a6349a1f6e")
PRIOR_TABLE="c858a48e5c4d615e8aac8709b5e214b09a35d5533860370a035204b63fdc8026"


def require(ok,label):
    if not ok:raise ValueError("FULL69_PHYSICAL_"+label)


def main():
    import argparse,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import runtime_envelope_physical_io_v1 as physical
    import receipt_xz_envelope_v1 as xz
    import runtime_record_envelope_v2 as old
    import xz_corpus_delivery_v1 as delivery
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt)
    output=PREFIX+f"native008-full69-physical-attempt{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_NEW_VERIFICATION")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic();q=None;budget=None;old_counts={};new_counts=[]
    row=dict(state="FAILED_FULL69_PHYSICAL_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,automatic_retry=False,
        original_full68_mapping_or_descriptor_policy_changed=False,
        actual_Native_binding_or_full_successor_scope_qualified=False)
    try:
        guard.acquire();budget=physical.DecoderBudget(guard.check)
        seed=a.AcceptanceReader(c.ROOT,guard.check)
        pub=a.read_exact(seed,PUBLICATION);prior=a.read_exact(seed,PRIOR)
        a.fields(pub,dict(state="PASS_NATIVE008_LOSSLESS_CARRIER_TWO_FRESH_READS_NOT_RUNTIME_BINDING",
            contracts=dict(run=7,errors=0,failures=0,skipped=0),fresh_inputs=27,final_fresh_hashes=27,
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
            original_overwritten_or_deleted=False,current_runtime_profile_changed=False),"EXACT_CARRIER_PUBLICATION")
        a.exact(pub["original_pin"],producer.ORIGINAL,"IMMUTABLE_NATIVE008_FAILURE")
        a.fields(prior,dict(state=delivery.VERIFICATION,pair_count=68,ordinary_pair_count=61,
            preserved_special_count=7,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),"ORIGINAL_FULL68_PROOF")
        manifest=a.read_exact(seed,prior["publication_manifest_pin"]);pairs=manifest["descriptors"]
        require(type(pairs) is list and len(pairs)==68 and delivery.digest(pairs)==PRIOR_TABLE,"WHOLE_UNCHANGED_PRIOR68")
        carrier=pub["published_carrier_pin"]
        require(all(p["physical_envelope_pin"]["path"]!=carrier["path"] and
            p["semantic_original_pin"]["path"]!=producer.ORIGINAL["path"] for p in pairs),"NEW_PAIR_NOT_REPLACEMENT")
        Parent=delivery.reader_type(a.AcceptanceReader,pairs,budget,xz,old,old_counts,a.exact)
        Reader=producer.decoder_reader(Parent,carrier["path"],budget,xz,new_counts)
        q=Reader(c.ROOT,guard.check)
        for pin in seed.snapshots.values():a.exact(q.pin(pin["path"]),pin,"REOPEN_ALL_SEED_METADATA")
        producer.failed_state(q.json(producer.ORIGINAL["path"]))
        for proof in (pub,prior):
            for pin in proof["source_pins"]:
                if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                    a.exact(q.pin(pin["path"]),pin,"UNCHANGED_REVIEWED_PUBLISHER_AND_DECODER_CODE")
        q.pin(SELF)
        for pair in pairs:a.exact(q.pin(pair["physical_envelope_pin"]["path"]),pair["physical_envelope_pin"],"FIRST_REAL_PRIOR68_DISK_DECODE")
        a.exact(q.pin(carrier["path"]),carrier,"FIRST_REAL_NEW_FAILURE_DISK_DECODE")
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        require(len(old_counts)==68 and all(type(v) is int and v==2 for v in old_counts.values())
            and new_counts==[carrier,carrier] and budget.attempts==budget.completed==138,
            "ALL69_TWO_REAL_DECODES_ONE_AGGREGATE_BUDGET")
        row.update(state="PASS_FULL69_TWO_FRESH_PHYSICAL_BOUNDARIES_NOT_NATIVE_BINDING_OR_ACCEPTANCE",
            prior_verification_pin=PRIOR,publication_pin=PUBLICATION,full68_descriptor_digest=PRIOR_TABLE,
            new_failed_semantic_pin=producer.ORIGINAL,new_failed_physical_pin=carrier,
            same_case_role="failed_capture_unknown_product_execution_not_accepted",
            pair_count=69,decode_count=138,prior_decode_counts=old_counts,new_decode_count=len(new_counts),
            physical_corpus_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in pairs)+carrier["bytes"],
            semantic_corpus_bytes=sum(p["semantic_original_pin"]["bytes"] for p in pairs)+producer.ORIGINAL["bytes"],
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            all_original_physical_pin_hashes_and_semantic_original_hashes_retained=True,
            original_failure_execution_unknown_not_changed_to_pre_product_stop=True,
            ordinary_prior_case_descriptor_still_rejects_current_case=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            decoder_budget=None if budget is None else budget.evidence(),
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"VERIFIER_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","pair_count","decode_count","physical_corpus_bytes",
        "fresh_inputs","final_fresh_hashes","decoder_budget","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
