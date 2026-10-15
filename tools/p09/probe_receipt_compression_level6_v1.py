"""Bounded encode-level experiment; decoder/wire/guards remain unchanged.

No derivative publication, graph adoption, Native/GO or queue write. Exact code
inverse for the single encoder compression literal, followed by full byte tests.
"""
from pathlib import Path
from types import FunctionType
import sys

SELF="tools/p09/probe_receipt_compression_level6_v1.py"
PINS=[
    dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"),
    dict(path="tools/p09/successor_preparation_workspace_v1.py",bytes=9656,sha256="003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98"),
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3")]


def require(ok,label):
    if not ok:raise ValueError("RECEIPT_LEVEL6_"+label)


def encoder(original):
    require(type(original) is FunctionType and original.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_FROZEN_ENCODER")
    code=original.__code__
    require(sum(type(v) is int and v==1 for v in code.co_consts)==1
        and not any(type(v) is int and v==6 for v in code.co_consts),"ONE_UNAMBIGUOUS_LEVEL_LITERAL")
    changed=code.replace(co_consts=tuple(6 if type(v) is int and v==1 else v for v in code.co_consts))
    inverse=changed.replace(co_consts=tuple(1 if type(v) is int and v==6 else v for v in changed.co_consts))
    require(inverse==code,"WHOLE_ENCODER_CODE_INVERSE")
    fn=FunctionType(changed,dict(original.__globals__),argdefs=original.__defaults__,closure=original.__closure__)
    fn.__kwdefaults__=original.__kwdefaults__
    return fn


def main():
    import argparse,hashlib,json,re,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    args=parser.parse_args();require(165<=args.case<=249 and 4<=args.run<=8 and 1<=args.attempt<=8,"CLOSED_PROBE_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
    output=prefix+f"level6-sample{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_SAMPLE_REPORT")
    modules,_=envelope.namespace_bundle.load(c.ROOT,PINS,{})
    codec=modules.runtime_record_envelope_v2;changed=encoder(modules.runtime_record_envelope_v1.encode)
    guard=modules.terminal_metadata_pressure_v1.guard_type(modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();row=dict(state="FAILED_LEVEL6_SAMPLE_NOT_ADOPTED",product_or_Native_executed=False,
        accepted_count_delta=0,original_or_derivative_files_rewritten=False,level6_derivatives_published=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"FROZEN_ENCODER_DECODER_AND_GUARDS")
        graph=q.json(prefix+f"successor-connections{args.run:03}.v9.json")
        a.fields(graph,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=args.case,cleanup_confirmed=True,product_or_Native_executed=False,accepted_count_delta=0),"CURRENT_EXPANDED_GRAPH")
        require(graph["fresh_inputs"]==graph["final_fresh_hashes"]>0,"GRAPH_FINAL_HASHES")
        manifest=a.read_exact(q,graph["manifest_pin"])
        eligible=[]
        for pair in manifest["descriptors"]:
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",pair["semantic_original_pin"]["path"])
            if match and 112<=int(match[1])<args.case:eligible.append(pair)
        eligible.sort(key=lambda pair:(-pair["semantic_original_pin"]["bytes"],pair["semantic_original_pin"]["path"]))
        require(len(eligible)>=3,"THREE_ORDINARY_PRIOR_SAMPLES")
        samples=[]
        for pair in eligible[:3]:
            old,new=pair["semantic_original_pin"],pair["physical_envelope_pin"]
            pin,buffer=q._read(old["path"],parse=True);q._bind(old["path"],pin);a.exact(pin,old,"ACTUAL_SAMPLE_ORIGINAL")
            raw=bytes(buffer)
            physical,existing=q._read(new["path"],parse=True);q._bind(new["path"],physical);a.exact(physical,new,"ACTUAL_EXISTING_ENVELOPE")
            a.exact(codec.decode(bytes(existing),guard.check),raw,"EXISTING_WHOLE_ORIGINAL_RESTORED")
            clock=time.process_time();level1=modules.runtime_record_envelope_v1.encode(raw,guard.check);cpu1=time.process_time()-clock
            clock=time.process_time();level6=changed(raw,guard.check);cpu6=time.process_time()-clock
            decode_started=time.process_time()
            for _ in range(2):a.exact(codec.decode(level6,guard.check),raw,"UNCHANGED_DECODER_FULL_LEVEL6_ROUNDTRIP")
            samples.append(dict(original_pin=old,existing_physical_pin=new,original_bytes=len(raw),
                existing_physical_bytes=len(existing),level1_current_bytes=len(level1),level6_bytes=len(level6),
                level6_sha256=hashlib.sha256(level6).hexdigest(),level1_encode_cpu_seconds=cpu1,
                level6_encode_cpu_seconds=cpu6,level6_two_decodes_cpu_seconds=time.process_time()-decode_started,
                existing_matches_current_level1=bytes(existing)==level1,bytes_saved_vs_current_level1=len(level1)-len(level6)))
            del raw,existing,buffer,level1,level6
        q.finish();guard.check(force=True)
        row.update(state="PASS_LEVEL6_THREE_REAL_PRIOR_SAMPLES_NOT_WHOLE_CORPUS_OR_RUNTIME",samples=samples,
            original_bytes=sum(s["original_bytes"] for s in samples),level1_current_bytes=sum(s["level1_current_bytes"] for s in samples),
            level6_bytes=sum(s["level6_bytes"] for s in samples),bytes_saved=sum(s["bytes_saved_vs_current_level1"] for s in samples),
            whole_encoder_code_inverse=True,decoder_source_and_wire_schema_unchanged=True,whole_current_scope_NOT_RUN=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"SAMPLE_CLEANUP");modules.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","original_bytes","level1_current_bytes","level6_bytes","bytes_saved",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
