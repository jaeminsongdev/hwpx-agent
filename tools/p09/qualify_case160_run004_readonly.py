"""Independent whole case160 oracle, no product replay or queue write."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

SELF = "tools/p09/qualify_case160_run004_readonly.py"
OUTPUT = "implementation/p09/evidence/p09-361-case160-run004-independent-oracle-r374.v1.json"
ROOT = dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run004.v1.json", bytes=4385867,
    sha256="0c75fc523072db2c4e27ca23178ccd848e440900bf583b2f015ead3664413087")
AUTHORITY159 = dict(path="implementation/p09/evidence/p09-361-case159-current-epoch-accept001.v1.json", bytes=436264,
    sha256="be740fc83c883f3e07e010299a9f05955da728911ad3e1c36a02ce1688f7947e")
PRIOR159 = dict(path="implementation/p09/evidence/p09-361-case159-current-runtime-run001.v1.json", bytes=4580676,
    sha256="090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2")


def bootstrap_requirements(q, c, native):
    """Expected paths from the unchanged checker, pins from accepted159 only."""
    a = c.a
    failed_path = selection(native, 4)[1]
    failed = q.json(failed_path)
    a.fields(failed, dict(error_code="CURRENT_EPOCH_ACCEPT_BOOTSTRAP_CONTROLLER", native_attempt=native,
        missing_bootstrap_path_list_complete=True, cleanup_confirmed=True,
        product_or_Native_reexecuted=False, queue_acceptance_called=False), "FULL_FROZEN_REQUIREMENT_PATHS")
    names = failed["missing_bootstrap_tool_paths"]
    a.require(type(names) is list and names == sorted(set(names)) and len(names) == 50
        and failed["missing_bootstrap_tool_path_count"] == len(names), "ALL50_INITIAL_REQUIREMENTS")
    authority = a.read_exact(q, AUTHORITY159)
    a.fields(authority, dict(accepted_count_after=153, runtime_candidate_pin=PRIOR159,
        resource_cleanup_confirmed=True), "UNCHANGED_ACCEPTED159_AUTHORITY")
    a.require(authority["state"].startswith("PASS_"), "ACCEPTED159_NOT_FAILED_CANDIDATE")
    prior = a.read_exact(q, PRIOR159)
    declared = c.old.base.scope.pins(prior["source_freeze"])
    pins = []
    for name in names:
        a.require(type(name) is str and name.startswith("tools/p09/") and name in declared,
            "PIN_FROM_ACCEPTED_PREDECESSOR_NOT_CURRENT_OBSERVATIONS")
        pin = dict(declared[name]); a.exact(q.pin(name), pin, "UNCHANGED_ORIGINAL_REQUIRED_TOOL_BYTES")
        pins.append(pin)
    return dict(bootstrap_requirement_schema="hwpx-agent.p09-case160-bootstrap-requirements/v1",
        bootstrap_required_tool_pins=pins, bootstrap_required_count=len(pins), authority_pin=AUTHORITY159,
        prior_runtime_pin=PRIOR159, requirement_diagnostic_pin=q.snapshots[failed_path],
        current_candidate_scope_used_to_derive_requirements=False,
        requirement_paths_from_entire_unchanged_frozen_checker=True)


def selection(run, attempt):
    if type(run) is not int or run not in (4, *range(7, 15)):
        raise ValueError("CLOSED_READONLY_NATIVE_ATTEMPT")
    if type(attempt) is not int or not 1 <= attempt <= 8:
        raise ValueError("CLOSED_READONLY_REPORT_ATTEMPT")
    path = ROOT["path"] if run == 4 else f"implementation/p09/evidence/p09-361-case160-current-runtime-run{run:03}.v1.json"
    output = OUTPUT if (run, attempt) == (4, 1) else f"implementation/p09/evidence/p09-361-case160-native{run:03}-independent-oracle-r392-attempt{attempt:03}.v1.json"
    return path, output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-attempt", type=int, default=4)
    parser.add_argument("--report-attempt", type=int, default=1)
    parser.add_argument("--prepare-bootstrap-requirements", action="store_true")
    args = parser.parse_args()
    root_path, output = selection(args.native_attempt, args.report_attempt)
    if args.prepare_bootstrap_requirements:
        output = f"implementation/p09/evidence/p09-361-case160-native{args.native_attempt:03}-bootstrap-requirements-r392.v1.json"
        if args.report_attempt != 1:
            output = output.removesuffix(".v1.json")+f"-attempt{args.report_attempt:03}.v1.json"
    module = importlib.import_module("case160_run004_controller" if args.native_attempt == 4 else "case160_run007_controller")
    c = module if args.native_attempt == 4 else module.CURRENT
    if c is None: raise ValueError("READONLY_NATIVE_CONFIG_REQUIRED")
    a = c.a
    destination = c.old.c.ROOT/output
    a.require(not destination.exists() and not destination.is_symlink(), "EXCLUSIVE_CURRENT160_READONLY_REPORT")
    guard = c.FIRST.terminal_metadata_pressure_v1.guard_type(c.FIRST.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started = time.monotonic()
    phase = "resource_admission"
    out = dict(state="FAILED_RUN004_INDEPENDENT_ORACLE_NOT_ACCEPTED", accepted_count_delta=0,
        product_or_Native_reexecuted=False, queue_acceptance_called=False, P09_gate="OPEN", PC_freeze_resolved=False)
    q = None
    root_pin = None
    script_pin = None
    try:
        guard.acquire()
        c.old.base.configure(160)
        # Oracle-only script is not retroactively inserted into the candidate's
        # Native source scope. Its own bytes are separately read before and after.
        source_reader = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        script_pin = source_reader.pin(SELF)
        # A separate reader prevents the observed candidate pin from seeding
        # the independent declaration scope before the whole oracle binds it.
        root_pin = source_reader.pin(root_path)
        if args.native_attempt == 4: a.exact(root_pin, ROOT, "ORIGINAL_RUN004_ROOT_BYTES")
        q = a.AcceptanceReader(c.old.c.ROOT, guard.check)
        if args.prepare_bootstrap_requirements:
            phase = "original_initial_requirements"
            out.update(bootstrap_requirements(q, c, args.native_attempt))
            q.finish(); source_reader.finish(); guard.check(force=True)
            out.update(state="PREPARED_ALL50_INITIAL_REQUIREMENTS_NOT_NATIVE_OR_ORACLE_OR_ACCEPTANCE",
                fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
            phase = "completed"
        else:
            phase = "independent_current160_whole_oracle"
            with patch("subprocess.Popen", side_effect=AssertionError("READONLY_NO_CHILD")), \
                 patch("subprocess.run", side_effect=AssertionError("READONLY_NO_CHILD")):
                row, listing, evidence, proof = c.API.prepare(q, root_pin)
            a.exact(q.snapshots[root_path], root_pin, "ACTUAL_UNMODIFIED_RUN004_BYTES")
            a.fields(row, dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
                selected_test_index=160, task=f"case160-current-r{args.native_attempt:03}-tests", Native_source_frame_qualified=True,
                current_generation_runtime_candidate_qualified=True, cleanup_confirmed=True, owned_tree_empty=True),
                "INDEPENDENT_CURRENT160_RUNTIME_NOT_GATE")
            a.fields(row["source_frame"], dict(frame_state="COMMITTED", registered_live_frame=False), "ACTUAL_COMMITTED_FRAME")
            a.require(len(row["source_frame"]["actual_byte_boundaries"]) == 2, "BOTH_ACTUAL_RUN004_BYTE_BOUNDARIES")
            a.exact(q.pin(SELF), script_pin, "READONLY_QUALIFIER_SOURCE_UNCHANGED")
            phase = "final_source_bytes"
            q.finish(); source_reader.finish(); guard.check(force=True)
            out.update(state="PASS_RUN004_INDEPENDENT_CURRENT160_WHOLE_ORACLE_NOT_QUEUE_OR_GATE",
                runtime_pin=root_pin, source_pins=[q.snapshots[SELF], q.snapshots[c.SELF], q.snapshots[c.TEST]],
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
        # Bounded source locations and missing tool paths only; no local values,
        # source text, command lines, exception messages or full logs.
        frames, missing = [], []
        tb = error.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            frames.append(dict(file=Path(frame.f_code.co_filename).name,
                function=frame.f_code.co_name, line=tb.tb_lineno))
            pin, bootstrap = frame.f_locals.get("pin"), frame.f_locals.get("bootstrap")
            if type(pin) is dict and type(bootstrap) is dict:
                name = pin.get("path")
                if type(name) is str and name.startswith("tools/p09/") and len(name) <= 256 and name not in bootstrap:
                    missing.append(name)
                required = frame.f_globals.get("CODE_PINS", [])
                native = frame.f_globals.get("native")
                sources = getattr(native, "SOURCES", ()) if native is not None else ()
                for group in (required, sources):
                    if type(group) not in (list, tuple): continue
                    for item in group:
                        if type(item) is not dict: continue
                        path = item.get("path")
                        if type(path) is str and path.startswith("tools/p09/") and len(path) <= 256 and path not in bootstrap:
                            missing.append(path)
            tb = tb.tb_next
        out["failure_frames"] = frames[-12:]
        all_missing = sorted(set(missing))
        out["missing_bootstrap_tool_path_count"] = len(all_missing)
        out["missing_bootstrap_path_list_complete"] = len(all_missing) <= 128
        out["missing_bootstrap_tool_paths"] = all_missing[:128]
    finally:
        guard.close()
        out.update(cleanup_confirmed=guard.cleanup, terminal_phase=phase, elapsed_seconds=time.monotonic()-started,
            native_attempt=args.native_attempt, report_attempt=args.report_attempt,
            qualifier_source_pin=script_pin, observed_runtime_pin=root_pin,
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
    prepared = out["state"].startswith("PREPARED_")
    if not out["state"].startswith("PASS_") and not prepared: a.require(len(raw) <= 65536, "SMALL_FAILURE_REPORT")
    for parent in (destination.parent, *destination.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DIRECT_READONLY_ANCESTORS")
        if parent == c.old.c.ROOT: break
    pacer = c.old._namespaces.runtime_envelope_physical_io_v1.bytes_policy.OwnedPacer()
    pacer.select(output)
    with destination.open("xb") as stream:
        for offset in range(0, len(raw), 65536):
            block = raw[offset:offset+65536]; pacer.reserve(lambda:None)
            size = stream.write(block); a.exact(size, len(block), "ALL_READONLY_REPORT_BYTES"); pacer.refund(size)
        stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state", "fresh_inputs", "final_fresh_hashes", "terminal_phase",
        "CPU_max", "RAM_min", "parent_CPU_max", "cleanup_confirmed", "error_code")}))
    return 0 if out["state"].startswith("PASS_") or prepared else 1


if __name__ == "__main__": raise SystemExit(main())
