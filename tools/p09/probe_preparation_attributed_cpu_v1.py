"""Controlled no-child source-reader probe, not installation in P09 runtime."""
import argparse
import json
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch

SELF="tools/p09/probe_preparation_attributed_cpu_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host_policy=host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as old
    import preparation_attributed_cpu_v1 as candidate
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--code-attempt",type=int,default=1);args=parser.parse_args()
    candidate.require(all(type(n) is int and 1<=n<=8 for n in (args.attempt,args.code_attempt)),"BOUNDED_PROBE_CONTEXT")
    output=PREFIX+f"preparation-attributed-CPU-probe{args.attempt:03}.v1.json"
    candidate.require(not(c.ROOT/output).exists(),"EXCLUSIVE_PROBE_RECORD")
    def absent():
        try:(c.ROOT/(PREFIX+"current-runtime-run008.v1.json")).lstat()
        except FileNotFoundError:return True
        return False
    candidate.require(absent(),"NO_EXISTING_NATIVE008")
    baseline=old.guard_type(distinct.guard_type(a.Guard))();guard=None;q=None;started=time.monotonic()
    row=dict(state="FAILED_CONTROLLED_PREPARATION_CPU_PROBE_NOT_INSTALLED",accepted_count_delta=0,
        GO_authorized=False,actual_Native_or_product_executed=False,actual_P09_preflight_executed=False,
        runtime_policy_installed=False,host_resource_policy=host_policy)
    try:
        # Design closure must pass the unchanged 75% guard before the
        # candidate is used even for this controlled, no-child probe.
        baseline.acquire();admission=a.AcceptanceReader(c.ROOT,baseline.check)
        admission.pin(SELF)
        code_name=PREFIX+f"preparation-attributed-CPU-design-code{args.code_attempt:03}.v1.json"
        code=admission.json(code_name)
        a.fields(code,dict(state=candidate.CODE_STATE,contracts=dict(run=20,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True,runtime_policy_installed=False,next_preflight_start_authorized=False,
            GO_authorized=False,accepted_count_delta=0),"CLOSED_PREPARATION_DESIGN_NOT_RUNTIME_AUTHORITY")
        candidate.require(type(code["fresh_inputs"]) is int and code["fresh_inputs"]==code["final_fresh_hashes"]>0,"ALL_DESIGN_FINAL_HASHES")
        for pin in code["source_pins"]:a.exact(admission.pin(pin["path"]),pin,"CURRENT_DESIGN_SOURCE_BEFORE_CONTROLLED_PROBE")
        admission.finish();baseline.close();candidate.require(baseline.cleanup,"ORIGINAL_ADMISSION_CLEANUP")
        guard=candidate.guard_type(distinct.guard_type(a.Guard),role="whole_metadata_preflight")()
        with patch("subprocess.Popen",side_effect=AssertionError("NO_PROBE_CHILD")), \
                patch("subprocess.run",side_effect=AssertionError("NO_PROBE_CHILD")):
            guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            for pin in admission.snapshots.values():a.exact(q.pin(pin["path"]),pin,"CONTROLLED_REAL_READER_SOURCES")
            # Repeated source checkpoints retain one sampled observation.
            before=len(guard.samples)
            for _ in range(100):guard.check()
            row["cached_checkpoint_loop_added_samples"]=len(guard.samples)-before
            for _ in range(8):time.sleep(.5);guard.check(force=True)
            q.finish();guard.check(force=True)
        candidate.require(absent(),"NATIVE_ABSENT_AFTER_CONTROLLED_PROBE")
        row.update(state="PASS_CONTROLLED_PREPARATION_CPU_GUARD_SOURCE_READS_NOT_RUNTIME_INSTALLATION",
            code_pin=q.snapshots[code_name],source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_owned_limits_readback=guard.preparation_limits,
            CPU_policy_evidence=guard.preparation_CPU.summary(),
            subprocess_construction_blocked=True,Native008_absent_before_after=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        baseline.close()
        if guard is not None:
            guard.close();row["CPU_policy_evidence"]=guard.preparation_CPU.summary()
        samples=baseline.samples+([] if guard is None else guard.samples)
        row.update(cleanup_confirmed=baseline.cleanup and (guard is None or guard.cleanup),
            elapsed_seconds=time.monotonic()-started,CPU_max=max((s["system_cpu_percent"] for s in samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in samples),default=None))
    candidate.require(row["cleanup_confirmed"],"ALL_CONTROLLED_PROBE_CLEANUP")
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","fresh_inputs","final_fresh_hashes","cached_checkpoint_loop_added_samples",
        "CPU_max","RAM_min","cleanup_confirmed","elapsed_seconds","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
