"""Fresh stored249 --list only, current-source/EXE closure, original owned limits.

Product test bodies, old passed cases, Cargo compilation, SQL/Hangul are not run.
The current build819 is preserved; an independently pinned original pure parser
compares all249 names/59 modules. No historical runner import graph is loaded.
"""
import argparse
import ctypes
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import build_case112_current_stored as build
import current_stored_listing_catalog as catalog
from bounded_process_progress import BoundedProcessCapture

c=build.c
SELF="tools/p09/list_case112_current_stored.py"
TEST="tools/p09/tests/test_case112_current_stored_listing.py"
BUILD_PIN=dict(path="implementation/p09/evidence/p09-361-case112-current-stored-build-run003.v1.json",
    bytes=888052,sha256="848c2b600e1db596c5ed29d74c38baeb2809c8bf6944ec04bfc3a7d8575da8ab")
EXE_PIN=dict(path=build.executable_name(3),bytes=14216704,
    sha256="188144dfa1e758ae3a88d3d9c881df03037a6164cef1ef16de9901b2c1b4cff8")
PASS="PASS_CURRENT_COMPILED_STORED249_LIST_ONLY_NOT_TEST_RUNTIME_OR_GATE"
MARKER_ARGS=["case112-current-list-only"]
RAW_DRIVER=c.__file__


def require(ok,code):
    if not ok:raise ValueError("CURRENT_STORED_LIST_"+code)


def task_for(run):
    require(type(run) is int and 1<=run<=999,"GENERATION_RANGE")
    return f"case112-current-list-r{run:03}"


def run_for(task):
    require(type(task) is str and re.fullmatch(r"case112-current-list-r[0-9]{3}",task),"TASK_SCOPE")
    run=int(task[-3:]);require(task==task_for(run),"TASK_GENERATION");return run


def parent_scope(row):
    require(row.get("state")==build.PASS and row.get("current_build_binding_accepted") is True
        and row.get("current_test_executable_built") is True and row.get("exit_code")==0
        and row.get("cleanup_confirmed") is True and row.get("owned_tree_empty") is True
        and row.get("source_input_bytes_checked_before_after") is True
        and row.get("compiled_test_artifact_pin")==EXE_PIN and row.get("compiled_artifact_byte_passes")==2
        and row.get("current_library_parent_pin")==build.PARENT_PIN
        and row.get("current_test_package_profile_config")==list(build.profile.CONFIG)
        and row.get("compile_recipe")==build.recipe(3) and row.get("policy")==c.POLICY
        and row.get("owned_limits_readback",{}).get("verified") is True
        and row.get("runtime_tests_executed") is False and row.get("compiled249_listing_qualified") is False
        and row.get("full249_current_qualified") is False
        and row.get("prior_queue_cases")==105 and row.get("next_case")==112
        and row.get("accepted_count_delta")==0,"CURRENT_BUILD_ONLY_PARENT")
    binding=row.get("catalog_binding",{})
    build.profile_scope(binding.get("catalog_profile"))
    require(binding.get("executable_path")==EXE_PIN["path"] and binding.get("catalog_profile")==build.EXPECTED_PROFILE
        and binding.get("build_finished_success") is True
        and binding.get("validated_stream",{}).get("all_records_validated") is True,"EXACT_BUILD_CATALOG")
    expected=build.base.inputs.inventory(row["source_freeze"],819)
    rust={name for name in expected if name.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (name.endswith(".rs") or name.endswith("/Cargo.toml"))}
    require(type(row.get("whole_workspace_Rust_input_count")) is int
        and row["whole_workspace_Rust_input_count"]==len(rust)==787
        and {build.base.epoch.MODULE,build.base.epoch.LIBRARY,catalog.ROOT}<=rust,"WHOLE_CURRENT_RUST_SCOPE")
    require(EXE_PIN["path"] not in expected,"FRESH_OUTPUT_NOT_OLD_INPUT")
    return expected,rust


def worker(task):
    run_for(task);raw_call=subprocess.call
    build.direct_path(c.ROOT/EXE_PIN["path"],file_required=True)
    def call(argv,**kwargs):
        require(argv[1:]==[*MARKER_ARGS,"--locked","--offline","--jobs","1","--color=never",
            "--target-dir",str(build.TARGET)],"ORIGINAL_WORKER_ARGUMENT_SCOPE")
        require(kwargs.get("cwd")==c.ROOT and kwargs.get("stdin")==subprocess.DEVNULL,"ORIGINAL_WORKER_CALL_SCOPE")
        env=dict(kwargs["env"])
        require(env.get("RUST_TEST_THREADS")=="1" and env.get("CARGO_PROFILE_TEST_DEBUG_ASSERTIONS")=="true"
            and env.get("CARGO_PROFILE_TEST_OVERFLOW_CHECKS")=="true","ORIGINAL_WORKER_ENVIRONMENT")
        env["RUST_TEST_NOCAPTURE"]="0";kwargs["env"]=env
        return raw_call([str(c.ROOT/EXE_PIN["path"]),"--list","--format=terse"],**kwargs)
    with patch.object(c,"TARGET",build.TARGET),patch.object(c,"TASKS",{task:list(MARKER_ARGS)}), \
            patch.object(subprocess,"call",call):
        return c.worker(task)  # Original stdin GO, verified Job membership, inherited ownership.


def run_owned(run):
    require(Path.cwd().resolve()==c.ROOT,"REPOSITORY_ROOT")
    task=task_for(run)
    destination=c.ROOT/"implementation/p09/evidence"/f"p09-361-case112-current-stored-list-run{run:03}.v1.json"
    require(not destination.exists(),"FRESH_RECEIPT")
    build.direct_path(c.ROOT/EXE_PIN["path"],file_required=True)
    accepted=False;captures=[];phases=[];source_names=None;modules=None;parser=None;helpers_before=None
    owner=SimpleNamespace(lock=threading.Lock(),samples=[])
    raw_sample=c.Windows.sample;last_parent=None;raw_dump=json.dump
    def sampled(windows):
        nonlocal last_parent
        row=dict(raw_sample(windows));now=time.monotonic();cpu=time.process_time()
        memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
        require(windows.k.K32GetProcessMemoryInfo(windows.k.GetCurrentProcess(),ctypes.byref(memory),memory.size),
            "PARENT_MEMORY_SAMPLE")
        normalized=None
        if last_parent is not None:
            wall=now-last_parent[0];delta=cpu-last_parent[1]
            require(wall>0 and delta>=0,"PARENT_CPU_INTERVAL")
            normalized=100*delta/wall/windows.processors
            require(math.isfinite(normalized) and 0<=normalized<=100,"PARENT_CPU_VALUE")
        last_parent=(now,cpu)
        row.update(parent_cpu_machine_percent=normalized,parent_private_mib=memory.private/1048576,
            parent_private_percent=100*memory.private/windows.total_ram)
        with owner.lock:owner.samples[:]=[row]
        require(row["parent_private_percent"]<c.POLICY["job_memory_stop_percent"],"PARENT_MEMORY_BUDGET")
        return row
    class Capture(BoundedProcessCapture):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.listing=None;captures.append(self)
        def communicate(self,timeout):
            output,errors=super().communicate(timeout)
            if self.process.returncode==0:
                require(errors=="" and parser is not None and source_names is not None,"CLEAN_PREPARED_LISTING")
                parser.validate(output,source_names)
                self.listing=dict(full_names_validated=True,test_count=len(source_names),
                    stdout_bytes=len(output.encode("utf-8")),stdout_sha256=hashlib.sha256(output.encode("utf-8")).hexdigest(),
                    stderr_bytes=0,raw_logs_included=False)
            return output,errors
    def pins(checkpoint=None):
        nonlocal source_names,modules,parser,helpers_before
        callback=(lambda:None) if checkpoint is None else checkpoint;deadline=time.monotonic()+600
        def guard():
            callback();require(time.monotonic()<deadline,"INPUT_SCOPE_LIMIT")
        owner.checkpoint_io=guard
        helpers={SELF,TEST,catalog.SELF,catalog.TEST,catalog.PARSER_PIN["path"],BUILD_PIN["path"],EXE_PIN["path"],
            Path(RAW_DRIVER).relative_to(c.ROOT).as_posix()}
        for module in tuple(sys.modules.values()):
            name=getattr(module,"__file__",None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":helpers.add(path.relative_to(c.ROOT).as_posix())
        if helpers_before is None:helpers_before=set(helpers)
        else:require(helpers==helpers_before,"IMPORTED_HELPER_INVENTORY_DRIFT")
        with patch.object(build.base.weighted,"BINARY_RATE",1048576),patch.object(build.base.weighted,"OTHER_RATE",2097152):
            q=build.BuildReader(c.ROOT,guard)
            early=build.pressure.PreSaturationReadCheckpoint(q,owner)
            inventory_pacer=build.QueryPacer(lambda:q.checkpoint())
            phase=dict(phase="build_binding",whole_source_completed=False)
            try:
                row=q.json(BUILD_PIN["path"])
                require(q.snapshots[BUILD_PIN["path"]]==BUILD_PIN,"EXACT_BUILD_PARENT_PIN")
                expected,rust=parent_scope(row)
                q.pin(SELF);q.pin(TEST)
                require(q.pin(EXE_PIN["path"])==EXE_PIN,"CURRENT_COMPILED_EXE_PIN")
                phase["phase"]="current_inventory"
                require(build.base.inputs.rust_inputs(c.ROOT,inventory_pacer.reserve)==rust,"WHOLE_RUST_INVENTORY_DRIFT")
                text=q.text(catalog.PARSER_PIN["path"])
                require(q.snapshots[catalog.PARSER_PIN["path"]]==catalog.PARSER_PIN,"EXACT_ORIGINAL_PARSER_PIN")
                candidate=catalog.Catalog(text)
                phase["phase"]="source_catalog"
                def read(name):
                    require(name in expected and name in rust,"MODULE_INSIDE_CURRENT_BUILD")
                    text=q.text(name);require(q.snapshots[name]==expected[name],"CURRENT_MODULE_PIN");return text
                names,instances=candidate.names(read)
                if source_names is None:source_names=names;modules=instances;parser=candidate
                else:require(names==source_names and instances==modules,"CURRENT_SOURCE_CATALOG_DRIFT")
                names_to_pin=set(expected)|helpers;require(len(names_to_pin)<=2048,"WHOLE_INPUT_BUDGET")
                phase["phase"]="whole_input_hashing"
                result=[q.pin(name) for name in sorted(names_to_pin)]
                require(all(q.snapshots[name]==pin for name,pin in expected.items()),"PRESERVED_BUILD_INPUT_DRIFT")
                require(q.snapshots[EXE_PIN["path"]]==EXE_PIN,"EXE_CLOSING_DRIFT")
                phase.update(phase="completed",whole_source_completed=True)
                return result
            except ValueError as error:
                if str(error).endswith("_STOP_EARLY_READ_PRESSURE_NOT_COOLING"):
                    raise ValueError("STOP_EARLY_READ_PRESSURE_NOT_COOLING") from None
                raise
            finally:
                early.restore()
                phase.update(completed_input_pins=list(q.snapshots.values()),bytes_read=q.bytes_read,reader_passes=q.read_passes,
                    inventory_checkpoint_pacing=inventory_pacer.summary(),file_open_pacing=q.open_pacer.summary(),
                    early_pressure=build.pressure_summary(early))
                phases.append(phase)
    def write(row,file,**kwargs):
        nonlocal accepted
        listing=captures[-1].listing if captures else None
        accepted=(row["state"]=="PASS_SCOPED_NOT_GATE" and row["cleanup_confirmed"] is True
            and row["owned_tree_empty"] is True and listing is not None)
        if row["state"]=="PASS_SCOPED_NOT_GATE":row["state"]=PASS if accepted else "STOPPED_NOT_ACCEPTED"
        row.update(schema_version="hwpx-agent.p09-case112-current-stored-listing/v1",
            current_build_parent_pin=BUILD_PIN,compiled_test_executable_pin=EXE_PIN,
            whole_workspace_Rust_input_count=787,source_test_names=source_names or [],source_module_instances=modules or [],
            original_pure_parser_pin=catalog.PARSER_PIN,original_parser_functions=list(catalog.SELECTED),
            historical_runner_module_imported=False,source_input_bytes_checked_before_after=accepted,
            current_compiled249_qualified=accepted,compiled249_listing_qualified=accepted,
            listing_observed=listing is not None,listing_observation=listing,input_phase_observations=phases,
            current_listing_executable_argv=[EXE_PIN["path"],"--list","--format=terse"],
            actual_EXE_list_executed=True if listing is not None else (None if row["writer_authorized"] else False),
            EXE_list_worker_authorized=row["writer_authorized"],Cargo_compilation_started=False,
            product_test_bodies_executed=False,runtime_tests_executed=False,full249_current_qualified=False,
            signed16_current_qualified=False,current_library_bound_to_old_test_binary=False,
            source_overwritten_or_frozen_pins_rebased=False,Native_source_frame_qualified=False,
            prior_queue_cases=105,next_case=112,accepted_count_delta=0,
            PC_freeze_resolved=False,A12_gate="OPEN",A13_gate="OPEN")
        return raw_dump(row,file,**kwargs)
    with patch.object(c,"__file__",str(c.ROOT/SELF)),patch.object(c,"TARGET",build.TARGET), \
        patch.object(c,"TASKS",{task:list(MARKER_ARGS)}),patch.object(c,"pins",pins), \
        patch("bounded_process_progress.BoundedProcessCapture",Capture),patch.object(c.Windows,"sample",sampled), \
        patch.object(json,"dump",write):
        code=c.run(task,destination,180)
    return 0 if accepted else (code or 2)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=int,required=True)
    return run_owned(parser.parse_args().run)


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) else "CURRENT_STORED_LIST_REDACTED_FAILURE"
        closed=code if re.fullmatch(r"[A-Z_]{1,160}",code) else "CURRENT_STORED_LIST_REDACTED_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=closed)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
