"""CODE8_ALIAS and one owned existing-fixture Native call, not full Frame/product."""
import ctypes
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

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

SELF="tools/p09/qualify_native_open_phase_timing_v2_r338.py"
FIXTURE="tools/p09/tests/fixtures/p206-input-lock-probe.txt"


def main():
    guard=distinct.guard_type(a.Guard)(); reader=None; handle=None; native=None
    opened=closed=0
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
             full_Native_frame_or_product_executed=False,current_controller_connected=False)
    try:
        guard.acquire(); reader=a.AcceptanceReader(a.c.ROOT,guard.check)
        import native_open_phase_timing_v2 as timing
        import locked_runtime_inputs as locks
        pins=[reader.pin(path) for path in (timing.SELF,timing.TEST,SELF,locks.SELF,FIXTURE,
                timing.original.SELF,timing.original.TEST)]
        previous=reader.json("implementation/p09/evidence/p09-361-native-phase-timing-code14-and-fixture-r706.v1.json")
        a.fields(previous,dict(state="PASS_NATIVE_PHASE_TIMING_CODE14_AND_ONE_OWNED_FIXTURE_NOT_FULL_FRAME_OR_PRODUCT",
            contracts=dict(run=14,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"PRESERVED_TIMING_CODE14_COMPONENT")
        for pin in previous["source_pins"]:a.exact(reader.pin(pin["path"]),pin,"UNCHANGED_ORIGINAL_TIMING_COMPONENT_SOURCES")
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
                   pattern="test_native_open_phase_timing_v2.py")
        tests=unittest.TestResult(); suite.run(tests); guard.check()
        contracts=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        out.update(contracts=contracts,new_code_pins=pins[:2],source_pins=pins)
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(contracts,dict(run=8,errors=0,failures=0,skipped=0),"NATIVE_PHASE_TIMING_CODE8_ALIAS")
        native=locks.Native(guard.check); native.pacer.rate=14
        original_open=type(native).open; original_create=type(native).create
        original_reserve=type(native.pacer).reserve
        pacer_alias=native.pacer;kernel_alias=native.k;checkpoint_alias=native.pacer.checkpoint
        phase=NS(current=None)
        clocks,proof=timing.connect(native,phase)
        phase.current=dict(ordinal=1,kind="regular")
        try:
            handle=native.open(a.c.ROOT/FIXTURE,False); opened+=1
            info=native.inspect(handle)
            a.require(info["size"]==pins[-1]["bytes"] and not info["directory"] and
                      not info["reparse"] and not info["inheritable"],"ACTUAL_ORIGINAL_DIRECT_NATIVE_METADATA")
        finally:
            phase.current=None
            if handle is not None:
                a.require(native.close(handle),"OWNED_NATIVE_HANDLE_CLOSED")
                closed+=1; handle=None
        a.require(type(native).open is original_open and type(native).create is original_create and
                  type(proof["original_pacer"]).reserve is original_reserve,"ORIGINAL_NATIVE_PACER_METHOD_IDENTITIES")
        a.require(not clocks.accounting_unavailable,"COMPLETE_TIMING_ACCOUNTING_REQUIRED")
        a.require(native.pacer is pacer_alias and native.k is kernel_alias and
                  native.pacer.checkpoint is checkpoint_alias,"ALL_PACER_KERNEL_CHECKPOINT_OBJECT_IDENTITIES")
        for row in clocks.rows.values():
            a.fields(row,dict(started=1,completed=1,failed=0,measured=1,unknown=0),"ONE_REAL_NATIVE_PHASE_MEASURED")
        reader.finish(); guard.check(force=True)
        out.update(state="PASS_NATIVE_PHASE_TIMING_ALIAS_CODE8_AND_ONE_OWNED_FIXTURE_NOT_FULL_FRAME_OR_PRODUCT",
                   phase_timing=clocks.summary(),fresh_inputs=len(reader.snapshots),
                   final_fresh_hashes=reader.final_fresh_hashes,original_native_class_method_identities_retained=True,
                   pacer_kernel_and_checkpoint_object_identities_retained=True,
                   preserved_CODE14_not_reexecuted=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            value=str(error)
            out["error_code"]=value if re.fullmatch("[A-Za-z0-9_]{1,256}",value) else "REDACTED_TIMING_QUALIFICATION_FAILURE"
    finally:
        if handle is not None and native is not None:
            try:
                if native.close(handle):closed+=1; handle=None
            except Exception:pass
        guard.close()
        out.update(handles_opened=opened,handles_closed=closed,handle_remaining=handle is not None,
                   cleanup_confirmed=guard.cleanup and handle is None,
                   original_resource_samples=guard.samples,
                   CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
                   RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") and out["cleanup_confirmed"] else 1


if __name__=="__main__":raise SystemExit(main())
