"""Resumable, serial level6 corpus production; not runtime adoption.

Each bounded batch has an exclusive receipt and full fresh closing hashes.
Originals and level1 derivatives remain untouched. No GO/Native/queue writes.
"""
from pathlib import Path
import re
import sys

SELF = "tools/p09/recompress_preparation_corpus_v1.py"
TEST = "tools/p09/tests/test_recompress_preparation_corpus_v1.py"
PROBE = dict(path="tools/p09/probe_receipt_compression_level6_v1.py", bytes=7585,
    sha256="bed30cdb1e775e643c33ffb4186021fb88b527b7c04332c4f8454b8128ed9fdd")
EXTRA = [
    dict(path="tools/p09/runtime_envelope_source_projection_v1.py", bytes=6401,
        sha256="728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"),
    dict(path="tools/p09/runtime_envelope_physical_io_v1.py", bytes=7214,
        sha256="b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c")]
PREFIX = "implementation/p09/evidence/p09-361-case165-"
PASS = "PASS_LEVEL6_CORPUS_BATCH_NOT_RUNTIME_OR_PRODUCT"


def require(ok, code):
    if not ok:
        raise ValueError("LEVEL6_CORPUS_" + code)


def select(rows, first, count):
    require(type(rows) is list and len(rows) == 68, "EXACT_FULL68_BASELINE")
    originals = set(); physical = set()
    for row in rows:
        require(type(row) is dict and set(row) == {"schema_version", "next_case",
            "semantic_original_pin", "physical_envelope_pin"}, "CLOSED_DESCRIPTOR")
        require(row["schema_version"] == "hwpx-agent.p09-lossless-runtime-source-projection/v1"
            and type(row["next_case"]) is int and row["next_case"] == 165, "EXACT_CONTEXT")
        old, encoded = row["semantic_original_pin"], row["physical_envelope_pin"]
        match = re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json", old["path"])
        require(match is not None and 112 <= int(match[1]) <= 165 and 1 <= int(match[2]) <= 999
            and (int(match[1]) < 165 or int(match[2]) in (2, 3)), "ONLY_DECLARED_PRIOR_OR_CLOSED_PREBODY")
        expected = f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{match[1]}-runtime-run{match[2]}.envelope.v1.json"
        require(encoded["path"] in (expected, expected.replace(".envelope.v1.json", ".failed.envelope.v1.json")), "EXACT_OLD_PHYSICAL_PATH")
        require(old["path"] not in originals and encoded["path"] not in physical, "BIJECTIVE_BASELINE")
        originals.add(old["path"]); physical.add(encoded["path"])
    require(type(first) is int and type(count) is int and 1 <= first <= 68
        and 1 <= count <= 8 and first + count - 1 <= 68, "BOUNDED_BATCH")
    return rows[first - 1:first - 1 + count]


def destination(old):
    match = re.fullmatch(r"implementation/p09/evidence/p361-lossless-runtime-inputs/(case[0-9]{3}-runtime-run[0-9]{3}(?:\.failed)?)\.envelope\.v1\.json", old)
    require(match is not None, "CANONICAL_OLD_DESTINATION")
    return f"implementation/p09/evidence/p361-lossless-runtime-inputs/{match[1]}.level6.envelope.v1.json"


def new_descriptor(old, pin):
    require(pin["path"] == destination(old["physical_envelope_pin"]["path"]), "EXPLICIT_LEVEL6_DESTINATION")
    return dict(old, physical_envelope_pin=dict(pin))


def main():
    import argparse, hashlib, io, json, time, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    require(1 <= args.attempt <= 8, "BOUNDED_ATTEMPT")
    output = PREFIX + f"level6-corpus-batch{args.first:03}-attempt{args.attempt:03}.v1.json"
    require(not (c.ROOT / output).exists(), "EXCLUSIVE_BATCH_NO_REPLAY")
    probe_ns, _ = envelope.namespace_bundle.load(c.ROOT, [PROBE], {})
    probe = probe_ns.probe_receipt_compression_level6_v1
    modules, _ = envelope.namespace_bundle.load(c.ROOT, probe.PINS + EXTRA,
        {"current_stored_runtime_scope": scope, "owned_source_read_pressure": bytes_policy})
    codec = modules.runtime_record_envelope_v2
    encode = probe.encoder(modules.runtime_record_envelope_v1.encode)
    physical = modules.runtime_envelope_physical_io_v1
    guard = modules.terminal_metadata_pressure_v1.guard_type(
        modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started = time.monotonic(); q = None
    row = dict(state="FAILED_LEVEL6_CORPUS_BATCH_NOT_ADOPTED", first=args.first, count=args.count,
        product_or_Native_executed=False, accepted_count_delta=0, original_or_existing_derivative_rewritten=False,
        runtime_adoption_NOT_RUN=True, files_created=[], completed_samples=[])
    try:
        guard.acquire(); q = a.AcceptanceReader(c.ROOT, guard.check)
        for name in (SELF, TEST): q.pin(name)
        for pin in [PROBE] + probe.PINS + EXTRA:
            a.exact(q.pin(pin["path"]), pin, "CURRENT_FROZEN_COMPONENTS")
        tests, _ = envelope.namespace_bundle.load(c.ROOT, [q.snapshots[TEST]],
            {"recompress_preparation_corpus_v1": sys.modules[__name__]})
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests.test_recompress_preparation_corpus_v1))
        contracts = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row["contracts"] = contracts
        a.exact(contracts, dict(run=7, errors=0, failures=0, skipped=0), "ALL_SEVEN_BATCH_CONTRACTS")
        graph = q.json(PREFIX + "successor-connections004.v9.json")
        a.fields(graph, dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=165, cleanup_confirmed=True, product_or_Native_executed=False, accepted_count_delta=0), "BASELINE_GRAPH")
        require(graph["fresh_inputs"] == graph["final_fresh_hashes"] > 0, "GRAPH_FINAL_HASHES")
        manifest = a.read_exact(q, graph["manifest_pin"])
        selected = select(manifest["descriptors"], args.first, args.count)
        sample_name = PREFIX + "level6-sample001.v1.json"
        sample = q.json(sample_name)
        a.fields(sample, dict(state="PASS_LEVEL6_THREE_REAL_PRIOR_SAMPLES_NOT_WHOLE_CORPUS_OR_RUNTIME",
            cleanup_confirmed=True, whole_encoder_code_inverse=True, decoder_source_and_wire_schema_unchanged=True), "QUALIFIED_SAMPLE")
        require(sample["fresh_inputs"] == sample["final_fresh_hashes"] > 0, "SAMPLE_FINAL_HASHES")
        require(PROBE in sample["source_pins"], "SAME_SAMPLE_ENCODER_IMPLEMENTATION")
        budget = physical.DecoderBudget(guard.check); pacer = bytes_policy.OwnedPacer()
        for offset, pair in enumerate(selected, args.first):
            old, previous = pair["semantic_original_pin"], pair["physical_envelope_pin"]
            pin, buffer = q._read(old["path"], parse=True); q._bind(old["path"], pin)
            a.exact(pin, old, "FRESH_WHOLE_ORIGINAL"); raw = bytes(buffer); del buffer
            pin, buffer = q._read(previous["path"], parse=True); q._bind(previous["path"], pin)
            a.exact(pin, previous, "FRESH_EXISTING_ENVELOPE")
            a.exact(codec.decode(bytes(buffer), guard.check), raw, "EXISTING_WHOLE_BYTES"); del buffer
            clock = time.process_time(); encoded = encode(raw, guard.check); cpu = time.process_time() - clock
            name = destination(previous["path"])
            pin = dict(path=name, bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())
            for _ in range(2):
                a.exact(budget.run(lambda checkpoint: codec.decode(encoded, checkpoint)), raw, "NEW_WHOLE_BYTES_TWICE")
            if (c.ROOT / name).exists():
                a.exact(q.fresh_pin(name), pin, "EXISTING_NEW_FILE_EXACT_NO_OVERWRITE")
            else:
                physical.publish_exclusive(c.ROOT, encoded, pin, guard.check, write_pacer=pacer)
                row["files_created"].append(name)
            a.exact(q.fresh_pin(name), pin, "FRESH_PUBLISHED_LEVEL6")
            row["completed_samples"].append(dict(ordinal=offset, baseline_descriptor=pair,
                level6_descriptor=new_descriptor(pair, pin), level6_encode_cpu_seconds=cpu,
                bytes_saved=previous["bytes"] - len(encoded)))
            del raw, encoded
        q.finish(); guard.check(force=True)
        row.update(state=PASS, baseline_manifest_pin=graph["manifest_pin"], sample_qualification_pin=q.snapshots[sample_name],
            original_bytes=sum(p["semantic_original_pin"]["bytes"] for p in selected),
            previous_encoded_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in selected),
            level6_bytes=sum(s["level6_descriptor"]["physical_envelope_pin"]["bytes"] for s in row["completed_samples"]),
            bytes_saved=sum(s["bytes_saved"] for s in row["completed_samples"]), decoder_budget=budget.evidence(),
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        row["error_type"] = type(error).__name__
        if q is not None:
            row.update(source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]):
            row["error_code"] = error.args[0]
    finally:
        guard.close(); row.update(cleanup_confirmed=guard.cleanup, elapsed_seconds=time.monotonic() - started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    require(guard.cleanup, "BATCH_CLEANUP")
    modules.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k: row.get(k) for k in ("state", "first", "count", "bytes_saved", "contracts",
        "fresh_inputs", "final_fresh_hashes", "elapsed_seconds", "CPU_max", "RAM_min", "cleanup_confirmed", "error_code")}))
    return 0 if row["state"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
