"""Paced ordinary prior-receipt production from an independent full scope.

No current-case alias, Native/GO/worker or queue writer. Reuse the frozen
selection, full codec, projection and exclusive publisher; preserve originals.
"""
from pathlib import Path
import sys

SELF="tools/p09/expand_closed_preparation_receipts_v1.py"
PINS=[
    dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"),
    dict(path="tools/p09/runtime_envelope_source_projection_v1.py",bytes=6401,sha256="728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"),
    dict(path="tools/p09/runtime_envelope_physical_io_v1.py",bytes=7214,sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c"),
    dict(path="tools/p09/current_queue_successor_connections.py",bytes=19229,sha256="363d9665885eedc096a7c970098cd80568197e13930e13bc10347e044a687fa9"),
    dict(path="tools/p09/successor_preparation_workspace_v1.py",bytes=9656,sha256="003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98"),
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3")]
CODE="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"


def require(ok,label):
    if not ok:raise ValueError("EXTRA_CLOSED_RECEIPTS_"+label)


def main():
    import argparse,hashlib,json,re,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--preflight-attempt",type=int,required=True)
    parser.add_argument("--count",type=int,default=6)
    args=parser.parse_args()
    require(165<=args.case<=249 and 4<=args.run<=8 and all(1<=n<=8 for n in (args.attempt,args.preflight_attempt))
        and 1<=args.count<=6,"CLOSED_PRODUCTION_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
    output=prefix+f"extra-ordinary-receipts{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_RECEIPT_NO_REPLAY")
    modules,_=envelope.namespace_bundle.load(c.ROOT,PINS,{"current_stored_runtime_scope":scope,"owned_source_read_pressure":bytes_policy})
    physical=modules.runtime_envelope_physical_io_v1;source=physical.source
    publisher=modules.successor_preparation_workspace_v1
    guard=modules.terminal_metadata_pressure_v1.guard_type(modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic()
    row=dict(schema_version="hwpx-agent.p09-extra-ordinary-closed-preparation-receipts/v1",
        state="FAILED_EXTRA_ORDINARY_RECEIPTS_NOT_ADOPTED",index=args.case,physical_run=args.run,
        original_receipts_rewritten=False,product_or_Native_executed=False,accepted_count_delta=0,files_created=[])
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"FROZEN_SELECTION_CODEC_PUBLISHER_SOURCES")
        code=q.json(CODE)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_CODE13")
        require(code["fresh_inputs"]==code["final_fresh_hashes"]>0,"CODE13_FINAL_HASHES")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CODEC_QUALIFICATION")
        pref_name=prefix+f"successor-preflight-run{args.run:03}-attempt{args.preflight_attempt:03}.v1.json"
        pref=q.json(pref_name)
        a.fields(pref,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=args.case,physical_run=args.run,original_preflight_contracts=10,Rust_inputs=787,
            cleanup_confirmed=True,accepted_count_delta=0,product_worker_or_Native_frame_executed=False),"INDEPENDENT_WHOLE_DECLARED_SCOPE")
        require(pref["fresh_inputs"]==pref["final_fresh_hashes"]>0,"PREFLIGHT_FINAL_HASHES")
        graph_name=prefix+f"successor-connections{args.run:03}.v6.json"
        graph=q.json(graph_name)
        a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=args.case,cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"CURRENT_BASE_GRAPH")
        manifest=a.read_exact(q,graph["manifest_pin"])
        originals=modules.current_queue_successor_connections.select_extra_receipts(scope,pref["complete_semantic_source_scope"],manifest["descriptors"],args.case,args.count)
        pacer=bytes_policy.OwnedPacer();pairs=[]
        for pin in originals:
            actual,buffer=q._read(pin["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,pin,"ACTUAL_ORIGINAL_FROM_INDEPENDENT_SCOPE")
            require(type(json.loads(bytes(buffer).decode("utf-8"))) is dict,"ORIGINAL_JSON_OBJECT")
            raw=bytes(buffer);encoded=source.codec.encode(raw,guard.check)
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",pin["path"])
            require(match is not None and 112<=int(match[1])<args.case,"ORDINARY_PRIOR_ONLY")
            name=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{match[1]}-runtime-run{match[2]}.envelope.v1.json"
            encoded_pin=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            pair=source.descriptor(pin,encoded_pin,next_case=args.case)
            projection=source.Projection({pin["path"]:pin},[pair],next_case=args.case,checkpoint=guard.check)
            for _ in range(2):a.exact(projection.decode_fresh(pin["path"],encoded_pin,encoded,guard.check),raw,"WHOLE_EXACT_ORIGINAL_RESTORED")
            if (c.ROOT/name).exists():a.exact(q.fresh_pin(name),encoded_pin,"EXISTING_DERIVATIVE_MUST_MATCH")
            else:physical.publish_exclusive(c.ROOT,encoded,encoded_pin,guard.check,write_pacer=pacer);row["files_created"].append(name)
            a.exact(q.fresh_pin(name),encoded_pin,"FRESH_PUBLISHED_PHYSICAL_BYTES")
            pairs.append(pair)
            del raw,encoded,buffer
        q.finish();guard.check(force=True)
        old=sum(p["bytes"] for p in originals);new=sum(p["physical_envelope_pin"]["bytes"] for p in pairs)
        row.update(state="PREPARED_EXTRA_ORDINARY_RECEIPTS_NOT_RUNTIME_OR_PRODUCT",base_preflight_pin=q.snapshots[pref_name],
            base_graph_pin=q.snapshots[graph_name],base_manifest_pin=graph["manifest_pin"],expected_original_pins=originals,
            explicit_descriptors=pairs,original_bytes=old,encoded_bytes=new,bytes_saved=old-new,decode_passes=2*len(pairs),
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            selection_not_from_current_candidate_observations=True,whole_runtime_connection_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PRODUCTION_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","original_bytes","encoded_bytes","bytes_saved","decode_passes",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PREPARED_") else 1


if __name__=="__main__":raise SystemExit(main())
