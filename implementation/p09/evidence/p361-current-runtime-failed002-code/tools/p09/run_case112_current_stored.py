"""Exact112 current-generation runtime candidate with the complete Native union.

Preserves FRESH131/105, both binaries, all historical archive bytes and current
compiled787 Rust scope. Original c.run owns the only GO/Job/resource sampler.
No retries, Cargo build, old111 replay, queue advance, Hangul or OS changes.
A separate immutable candidate/queue-epoch acceptance must follow this run.
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
from types import SimpleNamespace as NS
from unittest.mock import patch

import build_case112_current_stored as build
import current_stored_runtime_scope as scope
import current_stored_native_bridge as native
import owned_source_read_pressure as byte_policy
import packed_receipt_json as packed
from bounded_process_progress import BoundedProcessCapture

c=build.c
SELF="tools/p09/run_case112_current_stored.py"
TEST="tools/p09/tests/test_case112_current_stored_runtime.py"
PASS="PASS_EXACT112_CURRENT_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE"
BODY_PIN=dict(path="implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json",bytes=565807,
    sha256="b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72")
FRESH_PIN=dict(path="implementation/p09/evidence/locked-r07/p340-light-review-run131.v1.json",bytes=94990,
    sha256="6d05cb6bf810ff5c19c61d1bc2d76921a00abb00d0f959c51e5fed9402a782ff")
TERMINAL_PIN=dict(path="tools/p09/resumable_current_r07.py",bytes=14014,
    sha256="18fe998bee7287bbe557755b554125d420f26aaeb021df9ad14824ed75f1d0ff")
MARKER_ARGS=["case112-current-runtime-only"]
TARGET=build.TARGET


def require(ok,code):
    if not ok:raise ValueError("CURRENT_STORED_RUNTIME_"+code)


def task_for(run):
    require(type(run) is int and 1<=run<=999,"RUN_RANGE")
    return f"case112-current-r{run:03}-tests"


def run_for(task):
    require(type(task) is str and re.fullmatch("case112-current-r[0-9]{3}-tests",task),"EXACT_TASK")
    run=int(task[-9:-6]);require(task_for(run)==task,"TASK_RUN");return run


def arguments():
    return [scope.CASE112,"--exact","--test-threads=1","--format=pretty","--color=never"]


def worker(task):
    run_for(task);raw_call=subprocess.call
    build.direct_path(c.ROOT/scope.EXE_PIN["path"],file_required=True)
    def call(argv,**kwargs):
        require(argv[1:]==[*MARKER_ARGS,"--locked","--offline","--jobs","1","--color=never",
            "--target-dir",str(TARGET)],"ORIGINAL_WORKER_ARGUMENTS")
        require(kwargs.get("cwd")==c.ROOT and kwargs.get("stdin")==subprocess.DEVNULL,"ORIGINAL_WORKER_CALL_SCOPE")
        env=dict(kwargs["env"])
        require(all(env.get(k)==v for k,v in dict(RUST_TEST_THREADS="1",CARGO_PROFILE_TEST_DEBUG_ASSERTIONS="true",
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS="true").items()),"ORIGINAL_ASSERTIONS_ENVIRONMENT")
        env["RUST_TEST_NOCAPTURE"]="0";kwargs["env"]=env
        return raw_call([str(c.ROOT/scope.EXE_PIN["path"]),*arguments()],**kwargs)
    with patch.object(c,"TARGET",TARGET),patch.object(c,"TASKS",{task:list(MARKER_ARGS)}),patch.object(subprocess,"call",call):
        return c.worker(task)


def terminal_api(q):
    text=q.text(TERMINAL_PIN["path"]);require(q.snapshots[TERMINAL_PIN["path"]]==TERMINAL_PIN,"EXACT_TERMINAL_ORACLE")
    api=native.definitions(text,("arguments","terminal"),dict(require=require,re=re,
        NAME=re.compile(r"[A-Za-z_][A-Za-z0-9_:]*"),SUMMARY=re.compile(
        r"(?m)^test result: ok\. ([0-9]+) passed; ([0-9]+) failed; ([0-9]+) ignored; "
        r"([0-9]+) measured; ([0-9]+) filtered out;[^\r\n]*\r?$")))
    require(api.arguments(scope.CASE112)==arguments(),"ORIGINAL_ARGUMENTS_EXACT")
    return api


def binding(q):
    listing=q.json(scope.LIST_PIN["path"]);require(q.snapshots[scope.LIST_PIN["path"]]==scope.LIST_PIN,"PINNED_ACTUAL_LIST")
    current=scope.listing_inputs(listing)
    fresh=packed.unpack(q.json(FRESH_PIN["path"]),q.checkpoint)
    require(q.snapshots[FRESH_PIN["path"]]==FRESH_PIN and fresh["state"]=="PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT"
        and fresh["selected_test_index"]==112 and fresh["selected_test_name"]==scope.CASE112
        and fresh["resource_watcher_cleanup_confirmed"] is True and fresh["resource_stop_reason"] is None,
        "AUTHORITATIVE_FRESH131_EXACT112")
    plan=fresh["prior_runtime_plan"]
    require(plan["runtime_source_qualified_individual_cases"]==105 and plan["runtime_remaining_individual_cases"]==144
        and plan["next_runtime_index"]==112 and plan["P09_gate"]=="OPEN"
        and plan["full249_current_qualified"] is False,"UNCHANGED105_CURSOR")
    body=q.json(BODY_PIN["path"]);require(q.snapshots[BODY_PIN["path"]]==BODY_PIN,"IMMUTABLE_OLD_BODY")
    required=scope.compose(body["source_freeze"],list(current.values()))
    rust={name for name in current if name.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (name.endswith(".rs") or name.endswith("/Cargo.toml"))}
    require(len(rust)==787,"COMPLETE_CURRENT_RUST")
    return required,rust


def runtime_budget(required,inventory_requests):
    require(type(inventory_requests) is int and inventory_requests>0,"MEASURED_INVENTORY_PACING_COUNT")
    # 原 source-only model omits actual product/preGO/final-inventory/commit.
    # Charge these explicitly; do not hide them inside the60-second margin.
    extra=20+3+inventory_requests/20+11+5
    for rate in range(9,15):
        model=scope.cost(required,rate);total=model["predicted_combined_seconds"]+extra
        if total<600:
            return dict(**model,predicted_runtime_combined_seconds=total,
                product_allowance_seconds=20,pre_GO_and_assignment_allowance_seconds=3,
                final_inventory_checkpoint_count=inventory_requests,final_inventory_pacing_seconds=inventory_requests/20,
                additional_early_source_wait_allowance_seconds=11,post_cleanup_identity_allowance_seconds=5,
                unknown_pressure_waits_included=False,actual_completion_guaranteed=False)
    raise ValueError("CURRENT_STORED_RUNTIME_NO_SAFE_COMPLETE_RUNTIME_BUDGET")


class BoundaryReader(byte_policy.WeightedReader):
    def __init__(self,root,guard,*,owner,api):
        super().__init__(root,guard)
        self.pressure=api.PressureCheckpoint(self.checkpoint,owner);self.checkpoint=self.pressure
    def diagnostics(self):
        return dict(read_passes=self.read_passes,bytes_read=self.bytes_read,
            read_rates_by_kind=dict(binary=1048576,other=2097152),bytes_read_by_kind=dict(self.pacer.bytes_by_kind),
            near_saturation_read_backpressure=self.pressure.summary(),original_owned_read_operations_preserved=True,
            extra_sampler_or_native_query_started=False)


def parent_snapshot(windows,raw_sample,last_parent):
    """Same successful build003 parent CPU/private-memory sampling API."""
    row=dict(raw_sample(windows));now=time.monotonic();cpu=time.process_time()
    memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
    require(windows.k.K32GetProcessMemoryInfo(windows.k.GetCurrentProcess(),ctypes.byref(memory),memory.size),
        "PARENT_MEMORY_SAMPLE")
    normalized=None
    if last_parent is not None:
        wall=now-last_parent[0];delta=cpu-last_parent[1]
        require(wall>0 and delta>=0,"OWN_CPU_CLOCK")
        normalized=100*delta/wall/windows.processors
        require(math.isfinite(normalized) and 0<=normalized<=100,"OWN_CPU_VALUE")
    row.update(parent_cpu_machine_percent=normalized,parent_private_mib=memory.private/1048576,
        parent_private_percent=100*memory.private/windows.total_ram)
    require(row["parent_private_percent"]<c.POLICY["job_memory_stop_percent"],"OWN_PARENT_MEMORY")
    return row,(now,cpu)


def run_owned(run):
    task=task_for(run);destination=c.ROOT/f"implementation/p09/evidence/p09-361-case112-current-runtime-run{run:03}.v1.json"
    require(not destination.exists(),"FRESH_RECEIPT")
    owner=NS(lock=threading.Lock(),samples=[]);context=NS(phase="admission")
    raw_sample=c.Windows.sample;raw_dump=json.dump
    frame=api=expected=rust=budget=terminal=None;accepted=False;captures=[];guards=[];metadata={};inventory=[]
    windows_instance=None;last_parent=None;worker_imports=None;post_samples=[];post_time=0;last_progress=0
    global_deadline=time.monotonic()+720
    def progress(stage,count=0):
        nonlocal last_progress
        now=time.monotonic()
        if now-last_progress>=15:
            print(json.dumps(dict(stage=stage,completed=count,case=112,product_acceptance_delta=0)),flush=True)
            last_progress=now
    def sampled(windows):
        nonlocal windows_instance,last_parent
        windows_instance=windows
        require(time.monotonic()<global_deadline,"ORIGINAL_SHARED_METADATA_DEADLINE")
        if frame is not None and frame.held.acquired and not frame.held.closed:
            require(time.monotonic()-frame.held.started<=600,"NATIVE_LOCK_DEADLINE")
        row,last_parent=parent_snapshot(windows,raw_sample,last_parent)
        with owner.lock:owner.samples[:]=[row]
        require(row["parent_private_percent"]<c.POLICY["job_memory_stop_percent"],"OWN_PARENT_MEMORY")
        return row
    class Capture(BoundedProcessCapture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.terminal=None;captures.append(self)
        def communicate(self,timeout):
            output,errors=super().communicate(timeout)
            if self.process.returncode==0:
                require(terminal is not None,"TERMINAL_ORACLE_PREPARED")
                self.terminal=terminal.terminal(output,errors,scope.CASE112)
            return output,errors
    def imported():
        names={SELF,TEST,native.SELF,native.TEST,scope.SELF,scope.TEST}
        for module in tuple(sys.modules.values()):
            name=getattr(module,"__file__",None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":names.add(path.relative_to(c.ROOT).as_posix())
        require(len(names)<=64,"LEAN_IMPORTED_HELPER_BOUND")
        return names
    def input_pins(checkpoint=None):
        nonlocal frame,api,expected,rust,budget,terminal,worker_imports
        require(callable(checkpoint),"ORIGINAL_RESOURCE_CHECKPOINT")
        def guarded():
            checkpoint();require(time.monotonic()<global_deadline,"ORIGINAL_SHARED_METADATA_DEADLINE")
        context.phase="metadata_hash" if frame is None else "final_fresh_hash"
        owner.checkpoint_io=guarded
        if frame is None:
            q=build.BuildReader(c.ROOT,guarded)
            q.pacer=byte_policy.OwnedPacer()
            early_read=build.pressure.PreSaturationReadCheckpoint(q,owner)
            try:
                required,rust=binding(q);terminal=terminal_api(q)
                worker_imports=imported()
                for name in sorted(worker_imports):q.pin(name)
                for pin in native.SOURCES:
                    q.pin(pin["path"]);require(q.snapshots[pin["path"]]==pin,"NATIVE_DEFINITION_PIN")
                required=scope.extend(required,q.snapshots)
                pacer=build.QueryPacer(lambda:q.checkpoint())
                require(build.base.inputs.rust_inputs(c.ROOT,pacer.reserve)==rust,"CURRENT_RUST_INVENTORY")
                inventory.append(pacer.summary());budget=runtime_budget(required,pacer.requests)
                api=native.load(q,budget["selected_acquisition_rate_per_second"],c)
                expected={name:required[name] for name in sorted(required)}
                require(all(expected[n]==p for n,p in q.snapshots.items()),"ALL_BOOTSTRAP_PINS_IN_FRAME")
                metadata.update(input_pins=list(q.snapshots.values()),bytes_read=q.bytes_read,read_passes=q.read_passes,
                    early_pressure=build.pressure_summary(early_read),file_open_pacing=q.open_pacer.summary())
            finally:
                early_read.restore();metadata.update(early_pressure=build.pressure_summary(early_read),
                    input_pins=list(q.snapshots.values()),bytes_read=q.bytes_read,read_passes=q.read_passes,
                    file_open_pacing=q.open_pacer.summary())
            early=api.EarlySourceCheckpoint(lambda:owner.checkpoint_io(),owner)
            class ProgressLocks(api.InputLocks):
                def take(self,*a,**kw):
                    value=super().take(*a,**kw);progress("native_acquisition",len(self.owned));return value
            held=ProgressLocks(c.ROOT,early,owner,context)
            frame=native.frames.Frame(native.frames.Registry(),expected,early,held=held)
            held.mark("before_acquire");frame.acquire();held.mark("after_acquire")
        else:
            require(imported()==worker_imports,"IMPORTED_HELPER_DRIFT")
        def factory(guard):return BoundaryReader(c.ROOT,guard,owner=owner,api=api)
        result=api.read_with_held_path_guards(frame,factory,guarded,guards)
        progress(context.phase,len(result))
        if len(frame.boundaries)==2:
            pacer=build.QueryPacer(lambda:frame.check())
            require(build.base.inputs.rust_inputs(c.ROOT,pacer.reserve)==rust,"FINAL_CURRENT_RUST_INVENTORY")
            require(pacer.requests==inventory[0]["requests"],"FINAL_INVENTORY_PACING_COUNT")
            inventory.append(pacer.summary())
        else:frame.held.mark("before_parent")
        return result
    def pins(checkpoint=None):
        try:return input_pins(checkpoint)
        except (KeyError,TypeError,AttributeError,IndexError) as error:
            raise ValueError("CURRENT_STORED_RUNTIME_INPUT_SETUP_FAILURE") from None
    def write(row,file,**kw):
        nonlocal accepted,post_time
        cap=captures[-1] if captures else None
        product=cap is not None and cap.terminal is not None
        final_frame=None;closing_error=None
        try:
            if row["state"]=="PASS_SCOPED_NOT_GATE":
                require(product and row["cleanup_confirmed"] is True and row["owned_tree_empty"] is True
                    and row.get("owned_limits_readback",{}).get("verified") is True,"OWNED_PRODUCT_CLEANUP_BEFORE_COMMIT")
                # 原 c.run Job is now closed. Continue its same Windows sampler
                # serially without querying the closed Job handle or spawning a
                # second sampler; original system/parent limits still apply.
                hot=0
                for sample in row["samples"]:hot=hot+1 if sample["system_cpu_percent"]>=98 else 0
                def post_guard():
                    nonlocal hot,post_time
                    require(time.monotonic()<global_deadline,"ORIGINAL_SHARED_METADATA_DEADLINE")
                    require(time.monotonic()-frame.held.started<=600,"NATIVE_LOCK_DEADLINE")
                    if time.monotonic()-post_time>=.5:
                        sample=sampled(windows_instance);post_time=time.monotonic()
                        hot,reason=c.decision(sample,hot);post_samples.append(sample)
                        require(reason is None,reason)
                owner.checkpoint_io=post_guard
                context.phase="final_fresh_hash";frame.held.mark("after_parent");frame.held.mark("before_release")
                final_frame=frame.commit(row)
                accepted=True
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            closing_error=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_NATIVE_CLOSING_FAILURE"
        finally:
            if frame is not None:
                if not frame.close():accepted=False;closing_error="NATIVE_CLEANUP_FAILED"
                final_frame=frame.summary()
        if row["state"]=="PASS_SCOPED_NOT_GATE":row["state"]=PASS if accepted else "STOPPED_NOT_ACCEPTED"
        row.update(schema_version="hwpx-agent.p09-case112-current-native-runtime-candidate/v1",
            prior_queue_fresh_pin=FRESH_PIN,current_compiled_listing_pin=scope.LIST_PIN,
            compiled_test_executable_pin=scope.EXE_PIN,selected_test_index=112,selected_test_names=[scope.CASE112],
            test_arguments=arguments(),passed_test_names=[scope.CASE112] if product else [],
            terminal_summary=cap.terminal if cap else None,capture_diagnostics=cap.diagnostics() if cap else None,
            product_body_observed=product,actual_product_child_executed=True if product else (None if row["writer_authorized"] else False),
            actual_Cargo_SQL_Hangul_run=False,bootstrap_metadata=metadata,complete_runtime_budget=budget,
            imported_worker_source_paths=sorted(worker_imports or []),current_Rust_input_count=787,
            current_Rust_inventory_observations=inventory,source_frame=final_frame,source_path_guard_diagnostics=guards,
            Native_source_frame_qualified=accepted,current_generation_runtime_candidate_qualified=accepted,
            closing_error_code=closing_error,post_Job_cleanup_resource_samples=post_samples,
            prior_queue_cases=105,accepted_count_delta=0,next_case=112,
            separate_queue_epoch_acceptance_required=True,full249_current_qualified=False,signed16_current_qualified=False,
            A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False)
        if closing_error:row["stop_reason"]=closing_error
        return raw_dump(row,file,**kw)
    with patch.object(c,"__file__",str(c.ROOT/SELF)),patch.object(c,"TARGET",TARGET), \
        patch.object(c,"TASKS",{task:list(MARKER_ARGS)}),patch.object(c,"pins",pins), \
        patch("bounded_process_progress.BoundedProcessCapture",Capture),patch.object(c.Windows,"sample",sampled), \
        patch.object(json,"dump",write):
        code=c.run(task,destination,1200)
    return 0 if accepted else (code or 2)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=int,required=True)
    return run_owned(parser.parse_args().run)


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_CURRENT_RUNTIME_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
