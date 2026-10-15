"""Preserve the failed Native008; publish one explicit lossless candidate.

This same-case failure is NOT an ordinary prior-case descriptor. Nothing is
installed into the qualified full68 mapping, worker, Native or acceptance.
Both fresh carrier reads decode every original byte; no raw/hash/JSON cache.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

SELF="tools/p09/prepare_native008_carrier_v1.py"
TEST="tools/p09/tests/test_prepare_native008_carrier_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
ORIGINAL=dict(path=PREFIX+"current-runtime-run008.v1.json",bytes=3999022,
    sha256="53e27ba4e2f9555ecfa47d942fcbfe4319e3b91e91f7e5180ac18585a02e9df2")
CODEC=dict(path="tools/p09/receipt_xz_envelope_v1.py",bytes=4012,
    sha256="21daa1b06dd82af0a374923ecdefcdde245aafd88f2c218bcdae11f8211b5f09")
PHYSICAL=dict(path="tools/p09/runtime_envelope_physical_io_v1.py",bytes=7214,
    sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c")


def require(ok,label):
    if not ok:raise ValueError("NATIVE008_CARRIER_"+label)


def identifier(value):
    require(type(value) is int and 1<=value<=8,"FINITE_PREPARATION_IDENTIFIER")
    return value


def destination(generation):
    return "implementation/p09/evidence/p361-lossless-runtime-inputs/"+\
        f"case165-runtime-run008.failed.strict-window.xz8m-g{identifier(generation):03}.envelope.v1.json"


def exact_original(pin,raw):
    require(type(pin) is dict and pin==ORIGINAL,"ONE_IMMUTABLE_ORIGINAL_PIN")
    require(type(raw) is bytes and len(raw)==ORIGINAL["bytes"]
        and hashlib.sha256(raw).hexdigest()==ORIGINAL["sha256"],"ALL_ORIGINAL_BYTES_AND_HASH")


def failed_state(row):
    require(type(row) is dict and row.get("selected_test_index")==165
        and type(row.get("selected_test_index")) is int and row.get("state")=="STOPPED_NOT_ACCEPTED"
        and row.get("stop_reason")=="STOP_STRICT_PRODUCT_WINDOW","ORIGINAL_FAILURE_NOT_PASS")
    require(row.get("product_complete") is False and row.get("current_generation_runtime_candidate_qualified") is False
        and row.get("actual_product_child_executed") is None,"UNRESOLVED_PRODUCT_EXECUTION_NOT_RECLASSIFIED")
    window=row.get("strict_product_window")
    require(type(window) is dict and window.get("maximum_GO_to_complete_capture_seconds")==10
        and window.get("actual_GO_writes")==1 and window.get("actual_complete_capture_within_window") is False,
        "UNCHANGED_FAILED_STRICT_WINDOW")


def proposal(encoded,generation):
    require(type(encoded) is bytes and 0<len(encoded)<=16*1024*1024,"BOUNDED_ENCODED_BYTES")
    return dict(path=destination(generation),bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())


def decoder_reader(original,carrier,budget,codec,counts):
    class Reader(original):
        def _read(self,name,parse=False):
            pin,raw=super()._read(name,parse=parse or name==carrier)
            if name==carrier:
                decoded=budget.run(lambda check:codec.decode(bytes(raw),check))
                exact_original(ORIGINAL,decoded);counts.append(pin)
                # Return only the original physical bytes/buffer semantics.
                if not parse:raw=None
            return pin,raw
    return Reader


def main():
    import argparse,importlib.util,io,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import runtime_envelope_physical_io_v1 as physical
    import receipt_xz_envelope_v1 as codec
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--generation",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True);args=parser.parse_args()
    generation=identifier(args.generation);attempt=identifier(args.attempt)
    carrier=destination(generation);output=PREFIX+f"native008-carrier-g{generation:03}-attempt{attempt:03}.v1.json"
    for name in (carrier,output):
        path=c.ROOT/name
        require(not path.exists() and not path.is_symlink() and not path.is_junction(),"EXCLUSIVE_PREPARATION_OUTPUT")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic();q=None;budget=None;counts=[]
    row=dict(state="FAILED_NATIVE008_CARRIER_NOT_ADOPTED",generation=generation,attempt=attempt,
        product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
        automatic_retry=False,original_overwritten_or_deleted=False,current_runtime_profile_changed=False,
        same_case_failed_candidate_not_ordinary_prior_descriptor=True,
        full69_mapping_shared_decoder_or_Native_binding_qualified=False)
    try:
        guard.acquire();budget=physical.DecoderBudget(guard.check)
        Reader=decoder_reader(a.AcceptanceReader,carrier,budget,codec,counts)
        q=Reader(c.ROOT,guard.check)
        for pin in (CODEC,PHYSICAL):a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CODEC_AND_PHYSICAL_PUBLISHER")
        for name in (SELF,TEST):q.pin(name)
        pin,raw=q._read(ORIGINAL["path"],parse=True);q._bind(ORIGINAL["path"],pin)
        raw=bytes(raw);exact_original(pin,raw);failed_state(json.loads(raw))
        spec=importlib.util.spec_from_file_location("native008_carrier_contracts",c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.RAW=raw
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(row["contracts"],dict(run=7,errors=0,failures=0,skipped=0),"ALL_CARRIER7")
        encoded=codec.encode(raw,guard.check);proposed=proposal(encoded,generation)
        exact_original(ORIGINAL,codec.decode(encoded,guard.check))
        # Release first-read data before both fresh disk decoder boundaries.
        tests.RAW=None;del raw;del tests
        physical.publish_exclusive(c.ROOT,encoded,proposed,guard.check)
        row["published_carrier_pin"]=proposed;del encoded
        a.exact(q.pin(carrier),proposed,"FIRST_REAL_PHYSICAL_CARRIER_READ")
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        require(counts==[proposed,proposed] and budget.attempts==budget.completed==2,"TWO_FRESH_PHYSICAL_DECODES")
        row.update(state="PASS_NATIVE008_LOSSLESS_CARRIER_TWO_FRESH_READS_NOT_RUNTIME_BINDING",
            original_pin=ORIGINAL,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,physical_decode_boundaries=2,
            original_bytes=ORIGINAL["bytes"],carrier_bytes=proposed["bytes"],
            reduced_physical_bytes=ORIGINAL["bytes"]-proposed["bytes"],
            two_other_byte_pass_nominal_saved_seconds=(ORIGINAL["bytes"]-proposed["bytes"])/1048576,
            read_rates=dict(binary_bytes_per_second=1048576,other_bytes_per_second=2097152),
            parsed_JSON_hash_or_byte_cache=False,independent_full_successor_model_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            decoder_budget_for_this_pair_only=None if budget is None else budget.evidence(),
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PREPARATION_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","original_bytes","carrier_bytes","reduced_physical_bytes",
        "physical_decode_boundaries","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
