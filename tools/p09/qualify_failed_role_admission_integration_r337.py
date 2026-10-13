"""Isolated real V23 private graph; no controller admission or product dispatch.

Calls the original failed003 admission once and its declaration again through
the same manifest namespace. Fresh final hashing stays on the original reader.
This disposable interpreter does not publish a V24/DATA/GO qualification.
"""
import ctypes
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
import distinct_final_sample_guard_v1 as distinct
import accept_case112_current_epoch as a

SELF = "tools/p09/qualify_failed_role_admission_integration_r337.py"


def main():
    guard = distinct.guard_type(a.Guard)(); reader = None
    result = dict(state="FAILED_NOT_ACCEPTED", accepted_count_delta=0, P09_gate="OPEN",
                  actual_product_or_Native_executed=False, current_controller_connected=False,
                  whole_controller_admission_executed=False, actual_manifest_full_load_executed=False)
    try:
        guard.acquire(); reader = a.AcceptanceReader(a.c.ROOT, guard.check)
        import same_reader_failed_role_admission_v1 as shared
        pins = [reader.pin(path) for path in (shared.SELF, shared.TEST, SELF,
                "tools/p09/flat_current_queue_envelope_runtime_v23.py")]
        import flat_current_queue_envelope_runtime_v23 as m
        guard.check()
        for pin in m.NAMESPACE_SOURCE_PINS + m.ROLE_PINS + [m.ADMISSION_PIN, m.BUNDLE_PIN,
                m.LEAN_PIN, m.PRIOR_WINDOW_PIN]:
            a.exact(reader.pin(pin["path"]), pin, "EXACT_EXISTING_PRIVATE_GRAPH_SOURCES")
        a.require(m.manifest.failed is m.failed_role, "ONE_PARENT_MANIFEST_FAILED_ROLE_NAMESPACE")
        original = m.failed_role.admission
        default = sys.modules.get("runtime_failed_receipt_projection_v1")
        default_admission = getattr(default, "admission", None)
        execute, proof = shared.connect(m.failed_role, m.a, m.admission_once)
        before_reads, before_bytes = reader.read_passes, reader.bytes_read
        admitted = execute(reader, m.a)
        a.exact(admitted, m.ROLE_DECLARATION, "REAL_ORIGINAL_FAILED003_DECLARATION")
        first_reads, first_bytes = reader.read_passes - before_reads, reader.bytes_read - before_bytes
        after_first = (reader.read_passes, reader.bytes_read)
        again = m.manifest.failed.admission(reader, m.a)
        a.exact(again, admitted, "SAME_MANIFEST_DECLARATION")
        a.exact((reader.read_passes, reader.bytes_read), after_first, "NO_DUPLICATE_PREPARATORY_READS")
        a.exact(proof["actual_admissions"], dict(actual_admissions=1, duplicate_admissions_avoided=1),
                "ONE_REAL_ROLE_ADMISSION_ONLY")
        a.require(proof["original_admission"] is original, "ORIGINAL_FUNCTION_RETAINED")
        a.require(getattr(default, "admission", None) is default_admission, "DEFAULT_MODULE_UNCHANGED")
        before_final = (reader.read_passes, reader.bytes_read)
        reader.finish(); guard.check(force=True)
        a.exact(reader.final_fresh_hashes, len(reader.snapshots), "EVERY_FINAL_FRESH_HASH_RETAINED")
        result.update(state="PASS_REAL_PRIVATE_FAILED003_DECLARATION_SHARED_ONCE_NOT_CURRENT_RUNTIME_OR_GO",
                      new_code_pins=pins[:3], source_pins=pins, first_actual_read_passes=first_reads,
                      first_actual_bytes_read=first_bytes, duplicate_actual_read_passes=0,
                      duplicate_actual_bytes_read=0, actual_admission_counts=proof["actual_admissions"],
                      fresh_inputs=len(reader.snapshots), final_fresh_hashes=reader.final_fresh_hashes,
                      final_actual_read_passes=reader.read_passes-before_final[0],
                      final_actual_bytes_read=reader.bytes_read-before_final[1],
                      original_failure_and_review_retained=True, default_namespace_modified=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            import re
            code = str(error)
            result["error_code"] = code if re.fullmatch("[A-Za-z0-9_]{1,256}", code) else "REDACTED_INTEGRATION_FAILURE"
    finally:
        guard.close()
        result.update(cleanup_confirmed=guard.cleanup, original_resource_samples=guard.samples,
                      CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
                      RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
