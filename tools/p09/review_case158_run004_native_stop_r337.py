"""Exact closed acquisition STOP review; partial handles are never a PASS.

Read immutable run004 twice with the original guarded reader. Prove explicit
cleanup counters and no product/byte-boundary evidence; authorize no retry/GO.
"""
import ctypes
import json
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct

SELF="tools/p09/review_case158_run004_native_stop_r337.py"
TEST="tools/p09/tests/test_case158_run004_native_stop_r337.py"
ROOT_PIN=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run004.v1.json",
    bytes=2287363,sha256="7adefac75a0c1755ea4761144dfed48df3ffae90622de601b2ccfc9cc3e48329")


def validate(row):
    a.fields(row,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r004-tests",selected_test_index=158,
        stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",product_body_observed=False,
        actual_product_child_executed=False,worker_created=False,job_assigned=False,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0,
        P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False),"EXACT_PARTIAL_ACQUISITION_NOT_PRODUCT")
    frame=row["source_frame"]
    a.fields(frame,dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[],
        original_owned_cleanup_confirmed_before_release=False),"CLOSED_NOT_COMMITTED_OR_TWO_BOUNDARIES")
    h=frame["handles"]
    a.fields(h,dict(input_lock_handles_opened=1281,input_lock_handles_closed=1281,input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,active_reader_bindings=0,
        active_byte_streams=0,byte_stream_identity_checks=0,probe_handles_opened=0,probe_handles_closed=0,
        probe_handles_remaining=0,probe_handle_close_failed_attempts=0,maximum_lock_seconds=600,
        file_write_or_delete_operation_executed=False,input_scope_reduced=False),"EXACT_ACTUAL_HANDLES_CLOSED")
    a.fields(h["all_acquisition_checkpoint_warning_fail_fast"],dict(original_warning_percent=90,
        warning_stops=1,latched=True,acquisition_active=False,original_hard_guards_called_first=True,
        acquisition_cooling_waits_added=0,sampler_thread_or_native_query_added=False),"REAL_SOURCE_WARNING_LATCH")
    policy=frame["parent_python_live_raw_access_policy"]
    a.fields(policy,dict(active_scope=False,all_original_open_function_identities_restored=True,
        unrelated_output_or_cleanup_opens_not_given_extra_live_Native_checkpoint=True,
        original_physical_reader_resource_Frame_and_decoder_guards_not_replaced=True),"RESTORED_RECEIPT_SAFE_POLICY")
    a.resource_history(row["samples"])
    a.require(max(s["system_cpu_percent"] for s in row["samples"])>=90,"ACTUAL_SOURCE_PRESSURE_SAMPLE")
    a.exact(row["source_freeze"],[],"NO_COMPLETED_BYTE_FREEZE_IN_PARTIAL_ACQUISITION")
    a.require(type(frame["input_count"]) is int and frame["input_count"]>1281,"PARTIAL_NOT_ALL_DECLARED_INPUTS")
    return dict(opened=1281,closed=1281,remaining=0,actual_byte_boundaries=0,
        original_failed_root_preserved=True,source_frame_committed=False,
        actual_product_or_Native_qualification_proven=False,accepted_count_delta=0,
        actual_Native_pressure_failure_receipt_written_and_policy_restored=True,
        automatic_retry_or_GO_authorized=False,CPU_cause_or_PC_freeze_resolution_proven=False)


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(SELF),q.pin(TEST)];row=a.read_exact(q,ROOT_PIN)
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_case158_run004_native_stop_r337.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=8,errors=0,failures=0,skipped=0),"ALL_NATIVE_STOP_REVIEW_CODE8")
        proof=validate(row);q.finish();g.check(force=True)
        out.update(state="PASS_EXACT158_RUN004_CLOSED_NATIVE_ACQUISITION_STOP_REVIEW_NOT_GO_OR_PRODUCT",
            original_runtime_pin=ROOT_PIN,new_code_pins=pins,actual_stop_review=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_NATIVE_STOP_REVIEW"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
