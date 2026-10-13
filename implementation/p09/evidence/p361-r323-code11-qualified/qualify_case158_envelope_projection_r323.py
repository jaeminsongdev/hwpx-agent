"""CODE11 + real157 lossless projection candidate; no product/adoption/advance."""
import ctypes
import json
import sys
import unittest
from pathlib import Path

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
kernel.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
process = kernel.GetCurrentProcess()
if not (kernel.SetPriorityClass(process, 0x4000) and kernel.SetProcessAffinityMask(process, 1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import runtime_envelope_source_projection_v1 as projection
import review_case158_inherited_cost_r323 as review

SELF = "tools/p09/qualify_case158_envelope_projection_r323.py"


def main():
    guard = distinct.guard_type(a.Guard)()
    result = dict(state="FAILED_NOT_ACCEPTED", next_case=158, accepted_count_delta=0,
        P09_gate="OPEN", Native_product_or_acceptance_executed=False,
        current_physical_source_scope_changed=False, original_files_rewritten=False)
    try:
        guard.acquire(); q = a.AcceptanceReader(a.c.ROOT, guard.check)
        sources = [SELF, projection.SELF, projection.TEST, review.REVIEW_SOURCE,
            projection.codec.SELF, projection.codec.TEST, "tools/p09/runtime_record_envelope_v1.py",
            "tools/p09/tests/test_runtime_record_envelope_v1.py", distinct.SELF, distinct.TEST,
            projection.scope.SELF, projection.scope.TEST]
        source_pins = [q.pin(path) for path in sources]
        suite = unittest.defaultTestLoader.discover(str(a.c.ROOT / "tools/p09/tests"),
            pattern="test_runtime_envelope_source_projection_v1.py")
        # Suppress traceback/log text; counts are sufficient and private-safe.
        tests = unittest.TestResult(); suite.run(tests)
        guard.check()
        result["contracts"] = dict(run=tests.testsRun, errors=len(tests.errors),
            failures=len(tests.failures), skipped=len(tests.skipped))
        a.exact(result["contracts"], dict(run=11, errors=0, failures=0, skipped=0), "CODE11")
        authority = a.read_exact(q, review.AUTHORITY_PIN)
        a.fields(authority, dict(accepted_count_after=151, next_runtime_index=158,
            resource_cleanup_confirmed=True), "OFFICIAL151_UNCHANGED")
        a.exact(authority["runtime_candidate_pin"], review.ROOT_PIN, "ACTUAL157")
        pin, raw = q._read(review.ROOT_PIN["path"], parse=True)
        q._bind(pin["path"], pin); a.exact(pin, review.ROOT_PIN, "CURRENT_ROOT")
        original = bytes(raw); row = json.loads(raw.decode("utf-8"))
        semantic = projection.scope.extend(projection.scope.pins(row["source_freeze"]),
            projection.scope.pins([review.ROOT_PIN]))
        encoded = projection.codec.encode(original, guard.check)
        encoded_path = projection.PREFIX + "case157-runtime-run001.envelope.v1.json"
        import hashlib
        physical_pin = dict(path=encoded_path, bytes=len(encoded), sha256=hashlib.sha256(encoded).hexdigest())
        descriptor = projection.descriptor(review.ROOT_PIN, physical_pin, next_case=158)
        candidate = projection.Projection(semantic, [descriptor], next_case=158, checkpoint=guard.check)
        for _ in range(2):
            a.exact(candidate.decode_fresh(review.ROOT_PIN["path"], physical_pin, encoded, guard.check),
                original, "REAL157_LOSSLESS_BYTES")
        semantic_model = review.model(semantic, row["complete_runtime_budget"]["final_inventory_checkpoint_count"])
        physical_model = review.model({n: dict(p) for n, p in candidate.physical_pins.items()},
            row["complete_runtime_budget"]["final_inventory_checkpoint_count"])
        q.finish(); guard.check(force=True)
        result.update(state="PASS_ENVELOPE_SOURCE_PROJECTION_CODE11_REAL157_CANDIDATE_NOT_NATIVE_PRODUCT_OR_ADOPTED",
            new_code_pins=[p for p in source_pins if p["path"] in (projection.SELF, projection.TEST)],
            source_pins=source_pins, authority151_pin=review.AUTHORITY_PIN, actual157_pin=review.ROOT_PIN,
            explicit_descriptor=descriptor, full_scope_candidate=candidate.evidence(),
            candidate_semantic_model=semantic_model, candidate_physical_model=physical_model,
            actual_in_memory_decode_passes=2, physical_envelope_file_written=False,
            Native_locks_fresh_physical_reads_or_original_oracle_connection_proven=False,
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in guard.samples),
            RAM_min=min(s["available_ram_percent"] for s in guard.samples))
    except (ValueError, OSError, KeyError, TypeError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            import re
            code = str(error)
            result["error_code"] = code if re.fullmatch("[A-Za-z0-9_]{1,256}", code) else "REDACTED_COMPONENT_FAILURE"
    finally:
        guard.close(); result["cleanup_confirmed"] = guard.cleanup
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
