"""Fresh physical metadata IO with exact lossless semantic restoration.

Candidate only: does not replace a Native Frame, source scope or acceptor.
Physical byte counters remain physical; decoded bytes are reported separately.
"""
import hashlib
from types import MappingProxyType

SELF="tools/p09/fresh_lossless_metadata_reader_v1.py"
TEST="tools/p09/tests/test_fresh_lossless_metadata_reader_v1.py"


def require(ok,label):
    if not ok:raise ValueError("FRESH_METADATA_"+label)


def reader_type(base,projection,descriptors):
    require(isinstance(base,type) and callable(getattr(base,"_read",None)),"ORIGINAL_READER")
    require(type(descriptors) is list and 0<len(descriptors)<=249,"CLOSED_BINDING_COUNT")
    pairs={}
    for row in descriptors:
        require(type(row) is dict and set(row)=={"schema_version","semantic_original_pin","physical_envelope_pin","next_case"},"EXPLICIT_DESCRIPTOR")
        old,new=row["semantic_original_pin"],row["physical_envelope_pin"]
        require(old==dict(projection.semantic_pins.get(old["path"],{}))
            and new==dict(projection.physical_pins.get(new["path"],{})) and old["path"] not in pairs
            and type(row["next_case"]) is int and row["next_case"]==projection.next_case,"EXACT_VALIDATED_PROJECTION_PAIR")
        pairs[old["path"]]=(MappingProxyType(dict(old)),MappingProxyType(dict(new)))
    pairs=MappingProxyType(pairs)
    class Reader(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.lossless_metadata_attempts=self.lossless_metadata_completed=0
            self.lossless_metadata_physical_bytes=self.lossless_metadata_decoded_bytes=0
        def _read(self,name,parse=False):
            if name not in pairs:return base._read(self,name,parse=parse)
            self.checkpoint();old,new=pairs[name]
            if parse:require(old["bytes"]<=self.maximum_parse_bytes,"ORIGINAL_PARSE_BUDGET")
            self.lossless_metadata_attempts+=1
            actual,buffer=base._read(self,new["path"],parse=True)
            require(actual==dict(new),"ACTUAL_FRESH_PHYSICAL_PIN")
            raw=bytes(buffer)
            decoded=projection.decode_fresh(name,actual,raw,self.checkpoint)
            require(type(decoded) is bytes and len(decoded)==old["bytes"]
                and hashlib.sha256(decoded).hexdigest()==old["sha256"],"EXACT_FRESH_SEMANTIC_BYTES")
            self.checkpoint()
            self.lossless_metadata_completed+=1
            self.lossless_metadata_physical_bytes+=len(raw)
            self.lossless_metadata_decoded_bytes+=len(decoded)
            return dict(old),bytearray(decoded) if parse else None
    return Reader


def summary(reader):
    require(reader.lossless_metadata_completed<=reader.lossless_metadata_attempts,"DECODE_ACCOUNTING")
    return dict(mapped_read_attempts=reader.lossless_metadata_attempts,mapped_read_completed=reader.lossless_metadata_completed,
        mapped_physical_bytes_read=reader.lossless_metadata_physical_bytes,
        mapped_semantic_bytes_restored=reader.lossless_metadata_decoded_bytes,
        decoded_bytes_not_added_to_physical_counter=True,byte_hash_or_JSON_cache=False,
        fresh_physical_read_and_decode_per_request=True,original_unmapped_reader_retained=True,
        Native_or_product_or_acceptance_qualified=False)


def main():
    import argparse,io,json,os,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import runtime_envelope_namespace_bundle_v1 as loader
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args();require(164<=args.case<=249 and 1<=args.attempt<=8,"CLOSED_PROBE_CONTEXT")
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{args.case}-fresh-lossless-metadata-probe{args.attempt:03}.v1.json"
    require(not output.exists(),"EXCLUSIVE_PROBE")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic();q=None
    row=dict(state="FAILED_FRESH_LOSSLESS_METADATA_PROBE_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False,full_metadata_runtime_or_acceptance_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);own=q.pin(SELF);test=q.pin(TEST)
        test_names,proof=loader.load(c.ROOT,[test],{"fresh_lossless_metadata_reader_v1":sys.modules[__name__]})
        tests=test_names.test_fresh_lossless_metadata_reader_v1
        tests.Tests.setUp.__globals__["CHECKPOINT"]=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts;require(contracts==dict(run=8,errors=0,failures=0,skipped=0),"ALL_READER8_CONTRACTS")
        prepared=q.json(f"implementation/p09/evidence/p09-361-case{args.case}-successor-binding001.v1.json")
        a.fields(prepared,dict(state="PREPARED_REAL_SUCCESSOR_BINDING_ALL_PAIRS_NOT_WHOLE_RUNTIME_OR_GO",cleanup_confirmed=True),"ACTUAL_DECLARED_BINDING")
        manifest=a.read_exact(q,prepared["manifest_pin"])
        descriptors=manifest["descriptors"]
        prior_manifest=a.read_exact(q,manifest["prior_manifest_pin"])
        module,proof=bindings.connect(c.ROOT,loader,scope,args.case,manifest["historical_predecessor_provenance"],prior_manifest["descriptors"])
        for pin in bindings.PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_LOSSLESS_DEPENDENCY")
        q.pin(bindings.SELF);q.pin(bindings.TEST);q.pin(loader.SELF)
        bound=module.Binding(descriptors,prepared["manifest_pin"],next_case=args.case)
        required={d["semantic_original_pin"]["path"]:d["semantic_original_pin"] for d in descriptors}
        required[prepared["manifest_pin"]["path"]]=prepared["manifest_pin"]
        projection,proof=bound.project(required,guard.check)
        chosen=sorted(descriptors,key=lambda d:(-d["semantic_original_pin"]["bytes"],d["semantic_original_pin"]["path"]))[:2]
        Reader=reader_type(a.AcceptanceReader,projection,descriptors)
        baseline=a.AcceptanceReader(c.ROOT,guard.check);candidate=Reader(c.ROOT,guard.check)
        before=[]
        for descriptor in chosen:
            pin=descriptor["semantic_original_pin"];name=pin["path"]
            left=baseline.json(name);right=candidate.json(name)
            a.exact(right,left,"SAME_FRESH_ORIGINAL_JSON")
            a.exact(baseline.snapshots[name],pin,"ACTUAL_RAW_ORIGINAL_PIN")
            a.exact(candidate.snapshots[name],pin,"EXACT_RESTORED_SEMANTIC_PIN")
            before.append(dict(semantic_pin=pin,physical_pin=descriptor["physical_envelope_pin"]))
        baseline.finish();candidate.finish();q.finish();guard.check(force=True)
        row.update(state="PASS_BOUNDED_FRESH_LOSSLESS_METADATA_READER_NOT_RUNTIME_OR_PRODUCT",
            descriptor_count=len(descriptors),actual_originals_compared=len(chosen),selected_pairs=before,
            baseline_physical_bytes_read=baseline.bytes_read,candidate_physical_bytes_read=candidate.bytes_read,
            physical_bytes_saved=baseline.bytes_read-candidate.bytes_read,physical_read_passes=candidate.read_passes,
            semantic_pins=list(candidate.snapshots.values()),candidate_final_fresh_hashes=candidate.final_fresh_hashes,
            actual_reader=summary(candidate),source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PROBE_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    require(0<len(raw)<=262144,"BOUNDED_PROBE_RECEIPT")
    for parent in (output.parent,*output.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_PROBE_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:
        require(stream.write(raw)==len(raw),"COMPLETE_PROBE_RECEIPT");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:row.get(k) for k in ("state","contracts","descriptor_count","actual_originals_compared",
        "baseline_physical_bytes_read","candidate_physical_bytes_read","physical_bytes_saved","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
