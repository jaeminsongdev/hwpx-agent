"""Bounded, read-only next-case review; never launches a product or accepts a case.

한국어: 실제157의 원자료를 새로 읽고 기존 비용식과 독립 대조한다.
158 DATA/controller가 아직 없으므로 inherited-only 수치만 보고한다.
"""
import ctypes
import json
import sys
from pathlib import Path

# Apply local limits before importing the historical controller namespaces.
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
import current_stored_runtime_scope as scope
import runtime_record_envelope_v2 as envelope

ROOT_PIN = dict(path="implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json",
    bytes=2510393, sha256="b69f11fba45c67ba367e9226bf1df5e40f95b3bfd1135574f600ed125418812b")
AUTHORITY_PIN = dict(path="implementation/p09/evidence/p09-361-case157-current-epoch-accept001.v1.json",
    bytes=471501, sha256="9233d5bab4e2986b0993b1700a8d5fac945a3e439e5b72b13aca45bed41ea04d")
REVIEW_SOURCE = "tools/p09/review_case158_inherited_cost_r323.py"
TEST_SOURCE = "crates/product-cli/tests/form_stored_provider/actual_import/source_review_assembly.rs"


def model(rows, requests):
    # Independent literal arithmetic from the qualified original equations.
    cost = scope.cost(rows, 14)
    total = cost["predicted_combined_seconds"] - 2 * len(rows) / 20 - 4
    total = total + 15 + 3 + requests / 20 + 11 + 5 + 2.05 + .5
    return dict(inputs=len(rows), bytes=sum(p["bytes"] for p in rows.values()),
        acquisition_seconds=cost["native_acquisition_seconds"],
        two_actual_byte_seconds=cost["two_actual_byte_pass_nominal_seconds"],
        modeled_seconds=total, fits_original600=total < 600)


def main():
    guard = distinct.guard_type(a.Guard)()
    result = dict(state="FAILED_NOT_ACCEPTED", next_case=158, accepted_count_delta=0,
        product_Native_or_acceptance_executed=False, input_scope_changed=False,
        original_receipts_rewritten=False, P09_gate="OPEN", P10_allowed=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(a.c.ROOT, guard.check)
        authority = a.read_exact(q, AUTHORITY_PIN)
        a.fields(authority, dict(accepted_count_after=151, next_runtime_index=158,
            resource_cleanup_confirmed=True, P09_gate="OPEN"), "CURRENT151")
        a.exact(authority["runtime_candidate_pin"], ROOT_PIN, "ACTUAL157")
        pin, raw = q._read(ROOT_PIN["path"], parse=True)
        q._bind(pin["path"], pin); a.exact(pin, ROOT_PIN, "IMMUTABLE157")
        row = json.loads(raw.decode("utf-8"))
        old = scope.pins(row["source_freeze"])
        budget = row["complete_runtime_budget"]
        requests = budget["final_inventory_checkpoint_count"]
        actual = model(old, requests)
        a.exact(actual["modeled_seconds"], budget["predicted_runtime_combined_seconds"], "ORIGINAL_EQUATION")
        a.require(ROOT_PIN["path"] not in old, "NO_SELF_SOURCE")
        inherited = scope.extend(old, scope.pins([ROOT_PIN]))
        future = model(inherited, requests)
        # Experiment is entirely in memory. Physical scope remains unchanged.
        original = bytes(raw)
        encoded = envelope.encode(original, guard.check)
        a.exact(envelope.decode(encoded, guard.check), original, "LOSSLESS157")
        guard.check()
        listing = a.read_exact(q, scope.LIST_PIN)
        scope.listing_inputs(listing)
        names = listing["source_test_names"]
        a.require(type(names) is list and len(names) == 249, "EXACT_LISTING")
        result["next_test_name"] = names[157]
        sources = [REVIEW_SOURCE, TEST_SOURCE, envelope.SELF, envelope.TEST,
            "tools/p09/runtime_record_envelope_v1.py", "tools/p09/tests/test_runtime_record_envelope_v1.py",
            distinct.SELF, distinct.TEST, scope.SELF]
        result["review_source_pins"] = [q.pin(n) for n in sources]
        q.finish(); guard.check(force=True)
        result.update(state="PASS_CURRENT151_CASE158_INHERITED_COST_AND_LOSSLESS157_REVIEW_NOT_PRODUCT",
            authority151_pin=AUTHORITY_PIN, actual157_pin=ROOT_PIN, actual157_scope=actual,
            next158_inherited_scope=future, current158_DATA_or_controller_included=False,
            future_envelope_candidate=dict(original_bytes=len(original), encoded_bytes=len(encoded),
                bytes_saved=len(original)-len(encoded), adopted_for_current_Native_scope=False),
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(x["system_cpu_percent"] for x in guard.samples),
            RAM_min=min(x["available_ram_percent"] for x in guard.samples))
    except (ValueError, OSError, KeyError, TypeError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            import re
            code = str(error)
            result["error_code"] = code if re.fullmatch("[A-Za-z0-9_]{1,256}", code) else "REDACTED_REVIEW_FAILURE"
    finally:
        guard.close(); result["cleanup_confirmed"] = guard.cleanup
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
