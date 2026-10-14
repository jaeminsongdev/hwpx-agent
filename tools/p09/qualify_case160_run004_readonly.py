"""Independent whole run004 oracle, no product replay or queue write."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import case160_run004_controller as controller

SELF = "tools/p09/qualify_case160_run004_readonly.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-run004-independent-oracle-r374.v1.json"
ROOT = dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run004.v1.json", bytes=4385867,
    sha256="0c75fc523072db2c4e27ca23178ccd848e440900bf583b2f015ead3664413087")


def main():
    c = controller
    a = c.a
    destination = c.old.c.ROOT/OUTPUT
    a.require(not destination.exists() and not destination.is_symlink(), "EXCLUSIVE_CURRENT160_READONLY_REPORT")
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started = time.monotonic()
    phase = "resource_admission"
    out = dict(state="FAILED_RUN004_INDEPENDENT_ORACLE_NOT_ACCEPTED", accepted_count_delta=0,
        product_or_Native_reexecuted=False, queue_acceptance_called=False, P09_gate="OPEN", PC_freeze_resolved=False)
    q = None
    try:
        guard.acquire()
        c.old.base.configure(160)
        # Oracle-only script is not retroactively inserted into the candidate's
        # Native source scope. Its own bytes are separately read before and after.
        source_reader = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        script_pin = source_reader.pin(SELF)
        q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        phase = "independent_current160_whole_oracle"
        with patch("subprocess.Popen", side_effect=AssertionError("READONLY_NO_CHILD")), \
             patch("subprocess.run", side_effect=AssertionError("READONLY_NO_CHILD")):
            row, listing, evidence, proof = c.API.prepare(q, ROOT)
        a.exact(q.snapshots[ROOT["path"]], ROOT, "ACTUAL_UNMODIFIED_RUN004_BYTES")
        a.fields(row, dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
            selected_test_index=160, task="case160-current-r004-tests", Native_source_frame_qualified=True,
            current_generation_runtime_candidate_qualified=True, cleanup_confirmed=True, owned_tree_empty=True),
            "INDEPENDENT_CURRENT160_RUNTIME_NOT_GATE")
        a.fields(row["source_frame"], dict(frame_state="COMMITTED", registered_live_frame=False), "ACTUAL_COMMITTED_FRAME")
        a.require(len(row["source_frame"]["actual_byte_boundaries"]) == 2, "BOTH_ACTUAL_RUN004_BYTE_BOUNDARIES")
        a.exact(q.pin(SELF), script_pin, "READONLY_QUALIFIER_SOURCE_UNCHANGED")
        phase = "final_source_bytes"
        q.finish(); source_reader.finish(); guard.check(force=True)
        out.update(state="PASS_RUN004_INDEPENDENT_CURRENT160_WHOLE_ORACLE_NOT_QUEUE_OR_GATE",
            runtime_pin=ROOT, source_pins=[q.snapshots[SELF], q.snapshots[c.SELF], q.snapshots[c.TEST]],
            fresh_input_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes, fresh_read_passes=q.read_passes, fresh_bytes_read=q.bytes_read,
            original_frozen_prepare_and_entire_product_oracle_proof=proof,
            two_actual_runtime_byte_boundaries_independently_checked=True,
            current160_prepare_called_once=True, oracle_script_not_retroactive_Native_source=True)
        phase = "completed"
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        out["error_type"] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}", error.args[0]):
            out["error_code"] = error.args[0]
    finally:
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup, terminal_phase=phase, elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples), default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples), default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in guard.samples
                if s.get("parent_cpu_machine_percent") is not None), default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in guard.samples
                if s.get("parent_private_mib") is not None), default=None),
            metadata_progress=dict(fresh_inputs=len(q.snapshots) if q else 0,
                fresh_read_passes=q.read_passes if q else 0, fresh_bytes_read=q.bytes_read if q else 0))
    a.require(guard.cleanup, "READONLY160_CLEANUP")
    raw = (json.dumps(out, ensure_ascii=True, allow_nan=False, indent=2)+"\n").encode("utf-8")
    a.require(0 < len(raw) <= 2*1024*1024, "BOUNDED_READONLY160_REPORT")
    if not out["state"].startswith("PASS_"): a.require(len(raw) <= 65536, "SMALL_FAILURE_REPORT")
    for parent in (destination.parent, *destination.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DIRECT_READONLY_ANCESTORS")
        if parent == c.old.c.ROOT: break
    pacer = c.old._namespaces.runtime_envelope_physical_io_v1.bytes_policy.OwnedPacer()
    pacer.select(OUTPUT)
    with destination.open("xb") as stream:
        for offset in range(0, len(raw), 65536):
            block = raw[offset:offset+65536]; pacer.reserve(lambda:None)
            size = stream.write(block); a.exact(size, len(block), "ALL_READONLY_REPORT_BYTES"); pacer.refund(size)
        stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state", "fresh_inputs", "final_fresh_hashes", "terminal_phase",
        "CPU_max", "RAM_min", "parent_CPU_max", "cleanup_confirmed", "error_code")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__ == "__main__": raise SystemExit(main())
