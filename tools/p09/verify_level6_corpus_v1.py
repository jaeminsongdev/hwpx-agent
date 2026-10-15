"""Independent full68 coverage, fresh two-boundary decoding and cost model.

New paths are diagnostic only: this does not replace the runtime's canonical
descriptor/path policy, authorize a current-case alias, or dispatch a worker.
"""
from pathlib import Path
import sys

SELF = "tools/p09/verify_level6_corpus_v1.py"
TEST = "tools/p09/tests/test_verify_level6_corpus_v1.py"
CORPUS = dict(path="tools/p09/recompress_preparation_corpus_v1.py", bytes=10582,
    sha256="5f798d641401280bc8992bdafeb7978a18df636b2ba3c759c5dad47b2b854af2")
OLD = dict(path="tools/p09/case160_run007_controller.py", bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def coverage(baseline, batches, corpus):
    corpus.select(baseline, 1, 8)
    result = []; ordinal = 1
    for batch in batches:
        corpus.require(batch["state"] == corpus.PASS and batch["cleanup_confirmed"] is True
            and batch["product_or_Native_executed"] is False and batch["accepted_count_delta"] == 0
            and batch["original_or_existing_derivative_rewritten"] is False, "SUCCESSFUL_BATCH_ONLY")
        corpus.require(type(batch["first"]) is int and batch["first"] == ordinal
            and batch["fresh_inputs"] == batch["final_fresh_hashes"] > 0, "ORDERED_FINAL_BATCH")
        expected = corpus.select(baseline, ordinal, batch["count"])
        samples = batch["completed_samples"]
        corpus.require(len(samples) == len(expected), "COMPLETE_BATCH")
        for old, sample in zip(expected, samples):
            corpus.require(type(sample["ordinal"]) is int and sample["ordinal"] == ordinal
                and sample["baseline_descriptor"] == old, "INDEPENDENT_BASELINE_EXPECTATION")
            new = sample["level6_descriptor"]
            corpus.require(new == corpus.new_descriptor(old, new["physical_envelope_pin"]), "SEMANTIC_SCOPE_UNCHANGED")
            corpus.require(sample["bytes_saved"] == old["physical_envelope_pin"]["bytes"] - new["physical_envelope_pin"]["bytes"], "EXACT_RECORDED_BYTES")
            result.append(new); ordinal += 1
    corpus.require(ordinal == 69 and len(result) == 68, "FULL68_NO_GAP_OR_EXTRA")
    corpus.require(len({r["physical_envelope_pin"]["path"] for r in result}) == 68, "BIJECTIVE_LEVEL6")
    return result


def main():
    import argparse, hashlib, io, json, re, time, unittest
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as byte_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, required=True)
    parser.add_argument("--batches", required=True, help="Ordered explicit first:attempt pairs")
    args = parser.parse_args(); a.require(1 <= args.attempt <= 8, "LEVEL6_VERIFY_ATTEMPT")
    a.require(re.fullmatch(r"[0-9]{1,2}:[1-8](,[0-9]{1,2}:[1-8]){0,67}", args.batches), "LEVEL6_EXPLICIT_BATCHES")
    choices = [tuple(map(int, item.split(":"))) for item in args.batches.split(",")]
    namespaces, _ = envelope.namespace_bundle.load(c.ROOT, [CORPUS], {})
    corpus = namespaces.recompress_preparation_corpus_v1
    probe_ns, _ = envelope.namespace_bundle.load(c.ROOT, [corpus.PROBE], {})
    probe = probe_ns.probe_receipt_compression_level6_v1
    modules, _ = envelope.namespace_bundle.load(c.ROOT, probe.PINS + corpus.EXTRA,
        {"current_stored_runtime_scope": scope, "owned_source_read_pressure": byte_policy})
    output = corpus.PREFIX + f"level6-corpus-verification{args.attempt:03}.v1.json"
    manifest_name = corpus.PREFIX + f"level6-corpus-manifest{args.attempt:03}.v1.json"
    a.require(all(not (c.ROOT / p).exists() for p in (output, manifest_name)), "LEVEL6_EXCLUSIVE_VERIFICATION")
    guard = modules.terminal_metadata_pressure_v1.guard_type(
        modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    bindings = {}; counts = {}; budget = modules.runtime_envelope_physical_io_v1.DecoderBudget(guard.check)
    class Reader(a.AcceptanceReader):
        def _read(self, name, parse=False):
            if name not in bindings:
                return super()._read(name, parse=parse)
            pin, raw = super()._read(name, parse=True)
            pair = bindings[name]; a.exact(pin, pair["physical_envelope_pin"], "EXACT_FRESH_LEVEL6_INPUT")
            decoded = budget.run(lambda check: modules.runtime_record_envelope_v2.decode(bytes(raw), check))
            old = pair["semantic_original_pin"]
            a.require(len(decoded) == old["bytes"] and hashlib.sha256(decoded).hexdigest() == old["sha256"], "LEVEL6_BASELINE_ORIGINAL_DIGEST")
            counts[name] = counts.get(name, 0) + 1
            return pin, raw if parse else None
    started = time.monotonic(); q = None
    row = dict(state="FAILED_LEVEL6_CORPUS_VERIFICATION_NOT_ADOPTED", product_or_Native_executed=False,
        accepted_count_delta=0, current_runtime_descriptor_policy_UNCHANGED=True, runtime_adoption_NOT_RUN=True,
        whole_current_runtime_source_byte_inventory_rechecked=False)
    try:
        guard.acquire(); q = Reader(c.ROOT, guard.check)
        for name in (SELF, TEST): q.pin(name)
        for pin in [CORPUS, corpus.PROBE, OLD] + probe.PINS + corpus.EXTRA:
            a.exact(q.pin(pin["path"]), pin, "CURRENT_VERIFIER_COMPONENTS")
        tests, _ = envelope.namespace_bundle.load(c.ROOT, [q.snapshots[TEST]],
            {"verify_level6_corpus_v1": sys.modules[__name__], "recompress_preparation_corpus_v1": corpus})
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests.test_verify_level6_corpus_v1))
        contracts = dict(run=result.testsRun, errors=len(result.errors), failures=len(result.failures), skipped=len(result.skipped))
        row["contracts"] = contracts
        a.exact(contracts, dict(run=6, errors=0, failures=0, skipped=0), "LEVEL6_ALL_COVERAGE_CONTRACTS")
        graph = q.json(corpus.PREFIX + "successor-connections004.v9.json")
        a.fields(graph, dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            cleanup_confirmed=True, index=165), "ACTUAL_BASELINE_GRAPH")
        manifest = a.read_exact(q, graph["manifest_pin"])
        batches = []
        for first, attempt in choices:
            batch = q.json(corpus.PREFIX + f"level6-corpus-batch{first:03}-attempt{attempt:03}.v1.json")
            a.exact(batch["baseline_manifest_pin"], graph["manifest_pin"], "ONE_EXACT_BASELINE")
            inventory = scope.pins(batch["source_pins"])
            for pin in [CORPUS, corpus.PROBE] + probe.PINS + corpus.EXTRA:
                a.exact(inventory.get(pin["path"]), pin, "BATCH_CURRENT_IMPLEMENTATION")
            for pin in batch["source_pins"]:
                if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                    a.exact(q.pin(pin["path"]), pin, "UNCHANGED_BATCH_CODE_AND_TESTS")
            batches.append(batch)
        pairs = coverage(manifest["descriptors"], batches, corpus)
        bindings.update({p["physical_envelope_pin"]["path"]: p for p in pairs})
        for pair in pairs:
            a.exact(q.pin(pair["physical_envelope_pin"]["path"]), pair["physical_envelope_pin"], "FULL68_FRESH_INITIAL_DECODE")
        diagnostic = dict(schema_version="hwpx-agent.p09-level6-corpus-diagnostic/v1", diagnostic_only_not_runtime_adoption=True,
            baseline_manifest_pin=graph["manifest_pin"], descriptors=pairs,
            batch_receipt_pins=[q.snapshots[corpus.PREFIX + f"level6-corpus-batch{first:03}-attempt{attempt:03}.v1.json"] for first, attempt in choices])
        manifest_pin = modules.successor_preparation_workspace_v1.publish(c.ROOT, manifest_name, diagnostic, a)
        a.exact(q.pin(manifest_name), manifest_pin, "DIAGNOSTIC_MANIFEST_PUBLISHED")
        pref_name = corpus.PREFIX + "successor-preflight-run004-attempt008.v1.json"
        pref = q.json(pref_name)
        a.fields(pref, dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=165, physical_run=4, cleanup_confirmed=True, source_inputs=3016, Rust_inputs=787), "BASELINE_DECLARED_SCOPE")
        physical = scope.pins(pref["complete_physical_source_scope"])
        model_ns, _ = envelope.namespace_bundle.load(c.ROOT, [OLD], {"flat_current_queue_envelope_runtime_v25": envelope})
        cost = model_ns.case160_run007_controller.old.prior.DIRECT.runtime_budget
        requests = pref["whole_Rust_inventory"]["requests"]; a.exact(requests, 167, "FULL_RUST_RESERVATIONS")
        base = cost(physical, requests)
        a.exact(base["predicted_runtime_combined_seconds"] + 5.0,
            pref["complete_runtime_budget"]["predicted_runtime_combined_seconds"], "BASE_MODEL_EXACTLY_REPRODUCED")
        changed = dict(physical)
        for old, new in zip(manifest["descriptors"], pairs):
            previous = old["physical_envelope_pin"]
            a.exact(changed.pop(previous["path"], None), previous, "EVERY_OLD_PHYSICAL_SCOPE_PIN")
            current = new["physical_envelope_pin"]
            a.require(current["path"] not in changed, "NO_NEW_PHYSICAL_COLLISION")
            changed[current["path"]] = current
        a.exact(len(changed), len(physical), "EXACT_SCOPE_INPUT_COUNT")
        required = scope.extend(changed, dict(q.snapshots))
        # Old raw originals and old physical derivatives are not added as a
        # runtime replacement; only actual verifier inputs join this estimate.
        modeled = cost(required, requests)
        q.finish(); guard.check(force=True)
        a.require(len(counts) == 68 and all(n == 2 for n in counts.values())
            and budget.completed == budget.attempts == 136 and budget.active is None and budget.error is None,
            "TWO_FRESH_BOUNDARIES_ALL68_WITH_ONE_DECODER5")
        previous = sum(p["physical_envelope_pin"]["bytes"] for p in manifest["descriptors"])
        current = sum(p["physical_envelope_pin"]["bytes"] for p in pairs)
        row.update(state="PASS_FULL68_LEVEL6_CORPUS_AND_DECLARED_COST_NOT_CURRENT_ENTRY_OR_RUNTIME", pair_count=68,
            original_bytes=sum(p["semantic_original_pin"]["bytes"] for p in pairs), previous_encoded_bytes=previous,
            level6_bytes=current, bytes_saved=previous-current, diagnostic_manifest_pin=manifest_pin,
            baseline_declared_cost_seconds=base["predicted_runtime_combined_seconds"]+5.0,
            modeled_declared_cost_seconds=modeled["predicted_runtime_combined_seconds"]+5.0,
            modeled_scope_inputs=len(required), original_scope_inputs=len(physical),
            future_adoption_code_qualification_receipt_and_full_entry_cost_NOT_included=True,
            decode_counts=counts, decoder_budget=budget.evidence(), source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        row["error_type"] = type(error).__name__; row["decoder_budget"] = budget.evidence()
        if q is not None:
            row.update(source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]): row["error_code"] = error.args[0]
    finally:
        guard.close(); row.update(cleanup_confirmed=guard.cleanup, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    a.require(guard.cleanup, "LEVEL6_VERIFICATION_CLEANUP")
    modules.successor_preparation_workspace_v1.publish(c.ROOT, output, row, a)
    print(json.dumps({k:row.get(k) for k in ("state", "contracts", "pair_count", "bytes_saved", "modeled_declared_cost_seconds",
        "fresh_inputs", "final_fresh_hashes", "elapsed_seconds", "CPU_max", "RAM_min", "cleanup_confirmed", "error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
