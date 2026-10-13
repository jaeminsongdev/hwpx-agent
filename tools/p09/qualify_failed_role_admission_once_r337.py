"""Bounded component qualification only; no current controller or Native GO."""
import ctypes
import json
import sys
import unittest
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

SELF = "tools/p09/qualify_failed_role_admission_once_r337.py"


def main():
    guard = distinct.guard_type(a.Guard)()
    reader = None
    result = dict(state="FAILED_NOT_ACCEPTED", actual_product_or_Native_executed=False,
                  current_controller_connected=False, accepted_count_delta=0, P09_gate="OPEN")
    try:
        guard.acquire()
        reader = a.AcceptanceReader(a.c.ROOT, guard.check)
        paths = ("tools/p09/same_reader_failed_role_admission_v1.py",
                 "tools/p09/tests/test_same_reader_failed_role_admission_v1.py", SELF,
                 "tools/p09/same_reader_source_admission_once_v1.py")
        pins = [reader.pin(path) for path in paths]
        suite = unittest.defaultTestLoader.discover(str(a.c.ROOT / "tools/p09/tests"),
                    pattern="test_same_reader_failed_role_admission_v1.py")
        tests = unittest.TestResult(); suite.run(tests); guard.check()
        contracts = dict(run=tests.testsRun, errors=len(tests.errors),
                         failures=len(tests.failures), skipped=len(tests.skipped))
        result.update(contracts=contracts, new_code_pins=pins[:2], source_pins=pins)
        if tests.errors or tests.failures:
            result["failed_test_names"] = [t.id().split(".")[-1] for t, _ in tests.errors + tests.failures]
        a.exact(contracts, dict(run=11, errors=0, failures=0, skipped=0), "FAILED_ROLE_ONCE_CODE11")
        reader.finish(); guard.check(force=True)
        result.update(state="PASS_PRIVATE_FAILED_ROLE_SAME_READER_CODE11_NOT_CURRENT_RUNTIME_OR_GO",
                      fresh_inputs=len(reader.snapshots), final_fresh_hashes=reader.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        result["error_type"] = type(error).__name__
        if isinstance(error, ValueError):
            import re
            code = str(error)
            result["error_code"] = code if re.fullmatch("[A-Za-z0-9_]{1,256}", code) else "REDACTED_QUALIFICATION_FAILURE"
    finally:
        guard.close()
        result.update(cleanup_confirmed=guard.cleanup, original_resource_samples=guard.samples,
                      CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
                      RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None))
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
