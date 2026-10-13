"""CODE6 of full inherited API + fake owned lifecycle; no live full scope/GO."""
import ctypes
import json
from pathlib import Path
import sys
import unittest

kernel=ctypes.WinDLL("kernel32",use_last_error=True)
kernel.GetCurrentProcess.restype=ctypes.c_void_p
kernel.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
kernel.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
process=kernel.GetCurrentProcess()
if not (kernel.SetPriorityClass(process,0x4000) and kernel.SetProcessAffinityMask(process,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct

SELF="tools/p09/qualify_native_phase_timing_connection_r338.py"


def main():
    guard=distinct.guard_type(a.Guard)(); reader=None
    out=dict(state="FAILED_NOT_ACCEPTED",actual_product_or_full_live_Native_executed=False,
             current_controller_or_GO_qualified=False,accepted_count_delta=0,P09_gate="OPEN")
    try:
        guard.acquire(); reader=a.AcceptanceReader(a.c.ROOT,guard.check)
        import native_open_phase_timing_connection_v1 as connection
        import native_open_phase_timing_v2 as timing
        import current_queue_acquisition_checkpoint as bridge
        import native_pressure_failfast_v1 as pressure
        paths=(connection.SELF,connection.TEST,SELF,timing.SELF,timing.TEST,
               timing.original.SELF,bridge.SELF,bridge.original.SELF,pressure.SELF,
               "tools/p09/tests/test_locked_runtime_inputs.py")
        pins=[reader.pin(path) for path in paths]
        previous=reader.json("implementation/p09/evidence/p09-361-native-phase-timing-v2-alias-code8-and-fixture-r709.v1.json")
        a.fields(previous,dict(state="PASS_NATIVE_PHASE_TIMING_ALIAS_CODE8_AND_ONE_OWNED_FIXTURE_NOT_FULL_FRAME_OR_PRODUCT",
                 contracts=dict(run=8,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
                 pacer_kernel_and_checkpoint_object_identities_retained=True),"EXACT_ALIAS_COMPONENT_ONLY")
        for pin in previous["source_pins"]+list(bridge.SOURCES):
            a.exact(reader.pin(pin["path"]),pin,"CURRENT_INHERITED_NATIVE_GRAPH_SOURCES")
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
                pattern="test_native_open_phase_timing_connection_v1.py")
        tests=unittest.TestResult();suite.run(tests);guard.check()
        out.update(contracts=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped)),
                   new_code_pins=pins[:2],source_pins=pins)
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=6,errors=0,failures=0,skipped=0),"INHERITED_NATIVE_CONNECTION_CODE6")
        reader.finish();guard.check(force=True)
        out.update(state="PASS_INHERITED_NATIVE_TIMING_CONNECTION_CODE6_NOT_FULL_CURRENT_SCOPE_OR_GO",
                   fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
                   original_acquisition_pressure_rate_credit_aliases_and_close_retained=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            value=str(error);out["error_code"]=value if re.fullmatch("[A-Za-z0-9_]{1,256}",value) else "REDACTED_NATIVE_TIMING_CONNECTION_FAILURE"
    finally:
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup,original_resource_samples=guard.samples,
                   CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
                   RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
