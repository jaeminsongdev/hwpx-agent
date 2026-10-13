"""Eight real receipts; full semantic union retained; no IO artifact or adoption.

The five-second decoder reservation below is explicitly hypothetical, not an
enforced deadline. No product/Native/acceptance or passed-case replay occurs.
"""
import ctypes
import hashlib
import json
import sys
from pathlib import Path
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
handle = kernel.GetCurrentProcess()
if not (kernel.SetPriorityClass(handle, 0x4000) and kernel.SetProcessAffinityMask(handle, 1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import runtime_envelope_source_projection_v1 as projection
import review_case158_inherited_cost_r323 as review
SELF = "tools/p09/review_case158_multi_envelope_candidate_r323.py"
QUAL = "implementation/p09/evidence/p09-361-case158-envelope-source-code11-actual157-candidate-r618.v1.json"


def main():
    g = distinct.guard_type(a.Guard)()
    result = dict(state="FAILED_NOT_ACCEPTED", next_case=158, accepted_count_delta=0,
        product_Native_or_acceptance_executed=False, encoded_files_written=False,
        current_Native_scope_changed=False, P09_gate="OPEN", P10_allowed=False)
    latched = False
    def check():
        nonlocal latched
        g.check()
        a.require(not latched, "STOP_LATCHED_REVIEW_PRESSURE")
        if g.samples and g.samples[-1]["system_cpu_percent"] >= 75:
            latched = True
            raise ValueError("STOP_REVIEW_PRESSURE_NO_RETRY_OR_COOLING")
    try:
        g.acquire(); check(); q = a.AcceptanceReader(a.c.ROOT, check)
        qual = q.json(QUAL)
        a.fields(qual, dict(state="PASS_ENVELOPE_SOURCE_PROJECTION_CODE11_REAL157_CANDIDATE_NOT_NATIVE_PRODUCT_OR_ADOPTED",
            contracts=dict(run=11, errors=0, failures=0, skipped=0), cleanup_confirmed=True), "CODE11")
        for pin in qual["source_pins"]: a.exact(q.pin(pin["path"]), pin, "CURRENT_QUALIFIED_SOURCE")
        q.pin(SELF)
        ar = a.read_exact(q, review.AUTHORITY_PIN)
        a.fields(ar, dict(accepted_count_after=151, next_runtime_index=158, resource_cleanup_confirmed=True), "CURRENT151")
        a.exact(ar["runtime_candidate_pin"], review.ROOT_PIN, "ACTUAL157")
        root = a.read_exact(q, review.ROOT_PIN)
        semantic = projection.scope.extend(projection.scope.pins(root["source_freeze"]), projection.scope.pins([review.ROOT_PIN]))
        descriptors = []; original_total = encoded_total = 0
        for index in range(150, 158):
            name = f"implementation/p09/evidence/p09-361-case{index}-current-runtime-run001.v1.json"
            actual, buffer = q._read(name, parse=True); q._bind(name, actual)
            a.exact(actual, semantic[name], "FRESH_ORIGINAL_RECEIPT")
            original = bytes(buffer); encoded = projection.codec.encode(original, check)
            physical = dict(path=projection.PREFIX+f"case{index}-runtime-run001.envelope.v1.json",
                bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())
            row = projection.descriptor(semantic[name], physical, next_case=158)
            one = projection.Projection(semantic, [row], next_case=158, checkpoint=check)
            for _ in range(2): a.exact(one.decode_fresh(name, physical, encoded, check), original, "ORIGINAL_BYTES")
            original_total += len(original); encoded_total += len(encoded); descriptors.append(row)
            del original, encoded, buffer, one
        candidate = projection.Projection(semantic, descriptors, next_case=158, checkpoint=check)
        transformed = {d["semantic_original_pin"]["path"] for d in descriptors}
        for name in semantic:
            if name not in transformed: a.exact(dict(candidate.physical_pins[name]), semantic[name], "ALL_UNTRANSFORMED_INPUTS")
        model = review.model({n: dict(p) for n,p in candidate.physical_pins.items()}, root["complete_runtime_budget"]["final_inventory_checkpoint_count"])
        q.finish(); g.check(force=True); check()
        result.update(state="PASS_EIGHT_REAL_RECEIPT_LOSSLESS_SOURCE_CANDIDATE_NOT_FULL_PREFLIGHT_NATIVE_PRODUCT_OR_ADOPTED",
            source_pins=[q.snapshots[SELF], *qual["new_code_pins"]], qualification_pin=q.snapshots[QUAL],
            authority151_pin=review.AUTHORITY_PIN, actual157_pin=review.ROOT_PIN,
            candidate=candidate.evidence(), original_indices=list(range(150,158)), descriptors=descriptors,
            original_receipt_bytes=original_total, candidate_encoded_bytes=encoded_total,
            bytes_saved=original_total-encoded_total, independent_in_memory_decode_passes=16,
            candidate_physical_IO_model=model, hypothetical_decode_budget_seconds=5,
            decode_budget_enforced_or_qualified=False, modeled_candidate_with_hypothetical_decode_seconds=model["modeled_seconds"]+5,
            new_controller_DATA_and_decoder_integration_cost_included=False,
            live_physical_Native_locks_and_whole_oracle_connected=False,
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples), RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError, OSError, KeyError, TypeError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            import re
            value = str(error)
            result["error_code"] = value if re.fullmatch("[A-Za-z0-9_]{1,256}", value) else "REDACTED_MULTI_REVIEW_FAILURE"
    finally:
        g.close(); result["cleanup_confirmed"] = g.cleanup
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
