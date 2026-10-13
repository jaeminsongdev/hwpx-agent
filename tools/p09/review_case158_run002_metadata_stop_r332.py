"""Independent exact run002 pre-product STOP review, never GO or acceptance.

Read the immutable failed root twice using the original guarded Reader. Review
same-interval resource samples and explicit no-worker/no-Frame flags. No replay,
foreign process termination or CPU cause attribution is performed.
"""
import ctypes
import json
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path
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

SELF="tools/p09/review_case158_run002_metadata_stop_r332.py"
TEST="tools/p09/tests/test_case158_run002_metadata_stop_r332.py"
ROOT_PIN=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run002.v1.json",
    bytes=21201,sha256="956dbb5fb6723eeaac4b59ad6d4ffa7965583c17adcee318385f462d96b36dd4")


def validate(row):
    a.fields(row,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r002-tests",
        selected_test_index=158,stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
        product_body_observed=False,actual_product_child_executed=False,worker_created=False,
        job_assigned=False,Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False,source_frame=None,
        source_freeze=[],cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0,
        P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False),
        "EXACT158_RUN002_PRE_NATIVE_PRE_WORKER_FAILURE")
    metadata=row["bootstrap_metadata"]
    latch=metadata["early_pressure"]["metadata_failfast_connection"]
    a.fields(latch,dict(warning_CPU_percent=75,warning_stops=1,latched=True,active=False,
        original_checkpoint_restored=True,original_hard_guard_first=True,
        added_sampler_or_native_query=False,added_cooling_waits=0,
        automatic_retry_or_resume=False,complete_source_reads_or_deadlines_weakened=False),
        "RESTORED_TERMINAL_METADATA_LATCH")
    samples=row["samples"]
    a.resource_history(samples)
    a.require(samples[-1]["system_cpu_percent"]>=75,"ACTUAL_WARNING_SAMPLE")
    intervals=[(datetime.fromisoformat(right["time_utc"])-datetime.fromisoformat(left["time_utc"])).total_seconds()
        for left,right in zip(samples,samples[1:])]
    a.require(intervals and min(intervals)>=.5,"NO_SHORT_FORCED_CPU_INTERVAL_IN_THIS_RECEIPT")
    a.require(type(metadata["read_passes"]) is int and metadata["read_passes"]==len(metadata["input_pins"]),
        "ONE_FRESH_METADATA_PASS_PER_PIN")
    scratch=metadata["early_pressure"]["reusable_chunk_metadata_reader"]
    a.fields(scratch,dict(workspace_bytes=65536,workspace_allocations=1,active_lease=False),
        "BOUNDED_RETURNED_METADATA_SCRATCH")
    a.exact(scratch["leases"],scratch["lease_returns"],"NO_RETAINED_SCRATCH_LEASE")
    return dict(actual_product_or_Native_executed=False,accepted_count_delta=0,
        automatic_retry_or_GO_authorized=False,system_CPU_max=max(s["system_cpu_percent"] for s in samples),
        parent_CPU_max=max(s["parent_cpu_machine_percent"] or 0 for s in samples),
        parent_private_max_mib=max(s["parent_private_mib"] for s in samples),
        free_RAM_min_percent=min(s["available_ram_percent"] for s in samples),
        minimum_original_resource_interval_seconds=min(intervals),metadata_reads=metadata["read_passes"],
        metadata_bytes=metadata["bytes_read"],Defender_or_foreign_process_cause_proven=False,
        PC_freeze_resolved=False)


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(SELF),q.pin(TEST)]
        row=a.read_exact(q,ROOT_PIN)
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_case158_run002_metadata_stop_r332.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=7,errors=0,failures=0,skipped=0),"ALL_STOP_REVIEW_CODE7")
        proof=validate(row);q.finish();g.check(force=True)
        out.update(state="PASS_EXACT158_RUN002_METADATA_STOP_REVIEW_NOT_PRODUCT_OR_GO",original_runtime_pin=ROOT_PIN,
            failed_root_preserved=True,new_code_pins=pins,actual_stop_review=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_STOP_REVIEW_FAILURE"
    finally:
        g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
