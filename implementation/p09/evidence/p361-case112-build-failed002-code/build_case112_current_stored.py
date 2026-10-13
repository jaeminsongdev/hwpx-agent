"""Fresh current-source stored-provider libtest build; never executes product tests.

원 owned GO/Job/CPU/RAM/cleanup과 전체 Cargo JSON stream 검사를 재사용한다.
통과한 current-library epoch 전체를 유지하고 격리된 check cache에 새 suffix를 만든다.
과거 제품 binary/pins, 사용자 source, 실패 증거를 수정하지 않는다.
"""
import argparse
import ctypes
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

import check_case112_current_library as base
import run_aead_dependency_signed_tests as profile
import resume_preserved106_queue_runtime as pressure
import signed_durable_build_stream as stream
from bounded_process_progress import BoundedProcessCapture

c = base.owned
SELF = "tools/p09/build_case112_current_stored.py"
TEST = "tools/p09/tests/test_case112_current_stored_build.py"
PARENT_PIN = dict(path="implementation/p09/evidence/p09-361-case112-current-lib-check-run001.v1.json",
    bytes=425444, sha256="afda1589e83a4364d0dc27e76bc7aa9531cc9b38e4f7cba81d154db277fb9e18")
TARGET = base.target_for(1)
ARGS = ["rustc", "-p", "hwpx-agent-cli", "--test", "form_stored_provider", "--profile", "test"]
EXPECTED_PROFILE = dict(opt_level="1", debuginfo="line-tables-only", debug_assertions=True,
                        overflow_checks=True, test=True)
PASS = "PASS_CURRENT_STORED_TEST_BUILD_ONLY_NOT_LISTING_RUNTIME_OR_GATE"
RAW_STREAM = stream.CargoStream
RAW_DRIVER = c.__file__
FAILED_PIN = dict(path="implementation/p09/evidence/p09-361-case112-current-stored-build-run001.v1.json",
    bytes=26656,sha256="b840587c4398cb6d91991ca11241977fa677d30012558c96cb52a4f2f04c7a64")
FAILED_CODE = (
    dict(path="implementation/p09/evidence/p361-case112-build-failed001-code/build_case112_current_stored.py",
         bytes=16158,sha256="783ff76bcf7aa86ab156d42cbf5caadbeae0652f354fa8365107415aa06f6715"),
    dict(path="implementation/p09/evidence/p361-case112-build-failed001-code/test_case112_current_stored_build.py",
         bytes=8741,sha256="048d156a789f6065cd8def692086e5fc0db6d0b602b4f7acaa7e29ec23c8c9f8"))


def require(ok, code):
    if not ok:raise ValueError("P_CURRENT_STORED_BUILD_" + code)


def task_for(run):
    require(type(run) is int and 1 <= run <= 999, "GENERATION_RANGE")
    return f"case112-stored-build-r{run:03}"


def run_for(task):
    require(type(task) is str and re.fullmatch(r"case112-stored-build-r[0-9]{3}",task),"TASK_SCOPE")
    run=int(task[-3:]);require(task==task_for(run),"TASK_GENERATION");return run


def executable_name(run):
    task_for(run)
    return (TARGET/"debug/deps"/f"form_stored_provider-p361-case112-r{run:03}.exe").relative_to(c.ROOT).as_posix()


def direct_path(path, *, file_required=False):
    require(path.is_relative_to(c.ROOT),"PATH_OUTSIDE_REPOSITORY")
    for member in (path,*path.parents):
        require(not member.is_symlink() and not member.is_junction(),"PATH_LINK")
        if member==c.ROOT:break
    if file_required:require(path.is_file(),"OUTPUT_MISSING")


def profile_scope(value):
    require(type(value) is dict and value==EXPECTED_PROFILE
        and all(type(value[k]) is bool for k in ("debug_assertions","overflow_checks","test")),
        "EXACT_ASSERTION_TEST_PROFILE")


def recipe(run):
    profile.config_contract(profile.CONFIG)
    task_for(run)
    return [*[v for entry in profile.CONFIG for v in ("--config",entry)], *ARGS,
        "--locked","--offline","--jobs","1","--color=never","--target-dir",str(TARGET),
        "--message-format=json","--","-C",f"extra-filename=-p361-case112-r{run:03}"]


class CargoStream(RAW_STREAM):
    def accept(self, raw):
        # Original stream validates/hashes EVERY record, never filters errors into success.
        super().accept(raw)
        if not raw.strip():return
        item=json.loads(raw.decode("utf-8"),object_pairs_hook=stream.unique_object)
        if item.get("reason")!="compiler-artifact":return
        name=item.get("target",{}).get("name")
        require(name!="formula_issuer_product_postgres_probe","UNRELATED_PROBE_TARGET")
        if name!="form_stored_provider":return
        require(self.artifact is None and item["target"].get("kind")==["test"]
            and item["target"].get("src_path")==str(c.ROOT/"crates/product-cli/tests/form_stored_provider.rs")
            and item.get("fresh") is False,"EXACT_FRESH_TEST_TARGET")
        raw_profile=item.get("profile");require(type(raw_profile) is dict,"PROFILE_SHAPE")
        observed={key:raw_profile.get(key) for key in EXPECTED_PROFILE};profile_scope(observed)
        self.artifact=dict(reason="compiler-artifact",target=dict(name="form_stored_provider"),
            profile=observed,executable=item.get("executable"))


def parse_build(output,run,*,require_file=True):
    task_for(run)
    require(type(output) is str and len(output.encode("utf-8"))<=stream.LIMIT,"CLOSED_OUTPUT_LIMIT")
    try:rows=[json.loads(line,object_pairs_hook=stream.unique_object) for line in output.splitlines() if line.strip()]
    except (ValueError,UnicodeError):raise ValueError("P_CURRENT_STORED_BUILD_CLOSED_JSON") from None
    require(len(rows)==3 and all(type(row) is dict for row in rows),"CLOSED_PROOF_COUNT")
    artifact,finished,proof=rows
    require(set(artifact)=={"reason","target","profile","executable"}
        and artifact["reason"]=="compiler-artifact"
        and artifact["target"]==dict(name="form_stored_provider"),"CLOSED_TEST_ARTIFACT")
    profile_scope(artifact["profile"])
    raw=artifact["executable"];require(type(raw) is str,"EXECUTABLE_PATH_SHAPE")
    announced=Path(raw);exact=c.ROOT/executable_name(run)
    canonical=announced.parent==TARGET/"debug/deps" and re.fullmatch(r"form_stored_provider-[0-9a-f]{16}\.exe",announced.name)
    require(announced.is_absolute() and (announced==exact or bool(canonical)),"EXACT_OUTPUT_PATH")
    if require_file:direct_path(exact,file_required=True)
    require(finished==dict(reason="build-finished",success=True) and type(finished["success"]) is bool,
            "SUCCESSFUL_BUILD_FINISH")
    require(set(proof)=={"reason","all_records_validated","raw_stdout_bytes","raw_stdout_sha256",
        "messages","maximum_record_bytes","raw_stderr_bytes","stdout_record_buffer_limit",
        "stdout_total_JSON_IO_budget","stderr_total_limit","raw_output_truncated","raw_logs_included"},
        "EXACT_VALIDATED_STREAM_PROTOCOL")
    require(proof["reason"]=="p150-validated-stream" and proof["all_records_validated"] is True
        and proof["raw_output_truncated"] is False and proof["raw_logs_included"] is False
        and proof["stdout_record_buffer_limit"]==stream.LIMIT
        and proof["stderr_total_limit"]==stream.LIMIT
        and proof["stdout_total_JSON_IO_budget"]==stream.TOTAL_JSON_BYTES
        and type(proof["raw_stdout_sha256"]) is str
        and re.fullmatch(r"[0-9a-f]{64}",proof["raw_stdout_sha256"]),"RAW_STREAM_LIMITS")
    for key,limit in (("raw_stdout_bytes",stream.TOTAL_JSON_BYTES),("raw_stderr_bytes",stream.LIMIT),
                      ("messages",stream.MAX_MESSAGES),("maximum_record_bytes",stream.LIMIT)):
        require(type(proof[key]) is int and 0<=proof[key]<=limit,"RAW_STREAM_COUNTERS")
    require(proof["messages"]>=2,"COMPLETE_STREAM_RECORDS")
    require(proof["raw_stdout_bytes"]>0 and proof["maximum_record_bytes"]>0,"NONEMPTY_RAW_RECORDS")
    return dict(executable_path=executable_name(run),catalog_profile=artifact["profile"],
        Cargo_announcement_kind="canonical_name_with_fresh_suffix" if canonical else "exact_fresh_suffix",
        validated_stream=proof,build_finished_success=True)


def worker(task):
    run=run_for(task);exact=c.ROOT/executable_name(run)
    direct_path(TARGET);require(TARGET.is_dir(),"QUALIFIED_CHECK_CACHE_MISSING")
    direct_path(exact);require(not exact.exists(),"FRESH_SUFFIX_REQUIRED")
    def call(argv,**kwargs):
        require(argv[1:]==[*ARGS,"--locked","--offline","--jobs","1","--color=never",
                             "--target-dir",str(TARGET)],"ORIGINAL_WORKER_ARGUMENTS")
        require(kwargs.get("cwd")==c.ROOT and kwargs.get("stdin")==subprocess.DEVNULL,"WORKER_CALL_SCOPE")
        env=dict(kwargs["env"])
        require(all(not env.get(name) for name in base.OVERRIDES),"AMBIENT_COMPILER_OVERRIDE")
        require(all(env.get(k)==v for k,v in dict(CARGO_BUILD_JOBS="1",RUSTUP_AUTO_INSTALL="0",
            CARGO_PROFILE_TEST_OPT_LEVEL="0",CARGO_PROFILE_TEST_CODEGEN_UNITS="16",
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS="true",CARGO_PROFILE_TEST_OVERFLOW_CHECKS="true",
            RUST_TEST_THREADS="1").items()),"ORIGINAL_WORKER_ENVIRONMENT")
        env["CARGO_INCREMENTAL"]="0"
        for name in ("P150_BLOB_ROOT","P150_BLOB_RUN_ID","P150_BLOB_MODE"):env.pop(name,None)
        kwargs["env"]=env
        with patch.object(stream,"CargoStream",CargoStream):
            return stream.run_command([argv[0],*recipe(run)],kwargs,lambda out:parse_build(out,run))
    with patch.object(c,"TARGET",TARGET),patch.object(c,"TASKS",{task:list(ARGS)}),patch.object(subprocess,"call",call):
        return c.worker(task)


def parent_scope(row):
    require(row.get("state")==base.PASS and row.get("exit_code")==0
        and row.get("cleanup_confirmed") is True and row.get("owned_tree_empty") is True
        and row.get("current_CLI_library_typecheck_qualified") is True
        and row.get("source_input_bytes_checked_before_after") is True
        and row.get("current_test_executable_built") is False and row.get("runtime_tests_executed") is False
        and row.get("full249_current_qualified") is False
        and row.get("source_epoch_audit_pin")==base.AUDIT_PIN
        and row.get("selected_target_directory")==TARGET.relative_to(c.ROOT).as_posix()
        and row.get("policy")==c.POLICY and row.get("owned_limits_readback",{}).get("verified") is True
        and row.get("prior_queue_cases")==105 and row.get("next_case")==112
        and row.get("accepted_count_delta")==0,"QUALIFIED_CURRENT_LIBRARY_PARENT")
    expected=base.inputs.inventory(row["source_freeze"],806)
    rust={name for name in expected if name.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
          and (name.endswith(".rs") or name.endswith("/Cargo.toml"))}
    require(type(row.get("whole_workspace_Rust_input_count")) is int
        and row["whole_workspace_Rust_input_count"]==len(rust)==787
        and {base.epoch.MODULE,base.epoch.LIBRARY}<=rust,"CURRENT_RUST_INPUT_SCOPE")
    return expected,rust


class QueryPacer:
    """Bound file-read/metadata-request frequency, independently of byte pacing."""
    def __init__(self,checkpoint,clock=time.monotonic,sleep=time.sleep):
        self.checkpoint=checkpoint;self.clock=clock;self.sleep=sleep
        self.next=clock();self.requests=0;self.wait_seconds=0
    def reserve(self):
        self.checkpoint()
        while True:
            remaining=self.next-self.clock()
            if remaining<=0:break
            delay=min(.05,remaining);self.sleep(delay);self.wait_seconds+=delay;self.checkpoint()
        self.next=self.clock()+.05;self.requests+=1  # 20 entries/sec, no accumulated idle burst.
    def summary(self):
        return dict(request_limit_per_second=20,requests=self.requests,requested_wait_seconds=self.wait_seconds,
                    requests_skipped=False,cleanup_paced=False)


def pressure_summary(guard):
    # The shared class originally labels P340's90/95/98 graph. This runner owns
    # the original P14998 guard instead; do not mislabel its observed callbacks.
    return dict(warning_system_CPU_percent=guard.WARNING_PERCENT,
        cool_distinct_samples=guard.COOL_SAMPLES,maximum_pause_windows=guard.MAX_WINDOWS,
        warning_entries=guard.warning_entries,completed_pause_windows=guard.pause_windows,
        original_checkpoint_restored=guard.restored,original_owned_hard_guards_retained=True,
        existing_system_samples_reused=True,new_sampler_or_thread_started=False,
        source_reads_hashes_or_path_checks_skipped=False)


class BuildReader(base.weighted.WeightedReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.open_pacer=QueryPacer(lambda:self.checkpoint())
    def _read(self,name,parse=False):
        self.open_pacer.reserve()
        return super()._read(name,parse=parse)
    def _source(self,name):
        base.inputs.pin_shape(dict(path=name,bytes=0,sha256="0"*64))
        path=super()._source(name);direct_path(path,file_required=True);return path


def run_owned(run):
    require(Path.cwd().resolve()==c.ROOT,"REPOSITORY_ROOT")
    task=task_for(run);exact=c.ROOT/executable_name(run)
    destination=c.ROOT/"implementation/p09/evidence"/f"p09-361-case112-current-stored-build-run{run:03}.v1.json"
    require(not destination.exists(),"FRESH_RECEIPT_REQUIRED")
    direct_path(TARGET);require(TARGET.is_dir(),"QUALIFIED_CHECK_CACHE_MISSING")
    direct_path(exact);require(not exact.exists(),"FRESH_SUFFIX_REQUIRED")
    captures=[]; selected_helpers=None; source_count=0; artifact_pin=None; accepted=False
    input_phases=[]
    owner=SimpleNamespace(lock=threading.Lock(),samples=[])
    raw_sample=c.Windows.sample
    last_parent_cpu=None
    def sampled(windows):
        nonlocal last_parent_cpu
        row=dict(raw_sample(windows));now=time.monotonic();cpu=time.process_time()
        memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
        require(windows.k.K32GetProcessMemoryInfo(windows.k.GetCurrentProcess(),ctypes.byref(memory),memory.size),
                "PARENT_MEMORY_SAMPLE")
        normalized=None
        if last_parent_cpu is not None:
            wall=now-last_parent_cpu[0];delta=cpu-last_parent_cpu[1]
            require(wall>0 and delta>=0,"PARENT_CPU_INTERVAL")
            normalized=100*delta/wall/windows.processors
            require(math.isfinite(normalized) and 0<=normalized<=100,"PARENT_CPU_VALUE")
        last_parent_cpu=(now,cpu)
        row.update(parent_cpu_machine_percent=normalized,parent_private_mib=memory.private/1048576,
                   parent_private_percent=100*memory.private/windows.total_ram)
        with owner.lock:owner.samples[:]=[row]
        require(row["parent_private_percent"]<c.POLICY["job_memory_stop_percent"],"STOP_OWNED_PARENT_MEMORY_BUDGET")
        return row
    raw_dump=json.dump;original_admitted=c.admitted_count
    class Capture(BoundedProcessCapture):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.build=None;captures.append(self)
        def communicate(self,timeout):
            out,err=super().communicate(timeout)
            if self.process.returncode==0:
                require(err=="","CLEAN_OWNED_WORKER_STDERR")
                self.build=parse_build(out,run)
            return out,err
    def pins(checkpoint=None):
        nonlocal selected_helpers,source_count,artifact_pin
        callback=(lambda:None) if checkpoint is None else checkpoint
        deadline=time.monotonic()+600
        def guard():
            callback();require(time.monotonic()<deadline,"INPUT_HASH_SCOPE_LIMIT")
        owner.checkpoint_io=guard
        helpers={SELF,TEST,PARENT_PIN["path"],FAILED_PIN["path"],*(p["path"] for p in FAILED_CODE),
                 Path(RAW_DRIVER).relative_to(c.ROOT).as_posix()}
        for module in tuple(sys.modules.values()):
            file=getattr(module,"__file__",None)
            if file:
                path=Path(file).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":helpers.add(path.relative_to(c.ROOT).as_posix())
        if selected_helpers is None:selected_helpers=set(helpers)
        else:require(helpers==selected_helpers,"IMPORTED_HELPER_INVENTORY_DRIFT")
        with patch.object(base.weighted,"BINARY_RATE",1048576),patch.object(base.weighted,"OTHER_RATE",2097152):
            q=BuildReader(c.ROOT,guard)
            read_pressure=pressure.PreSaturationReadCheckpoint(q,owner)
            inventory_pacer=QueryPacer(lambda:q.checkpoint())
            phase=dict(phase="parent_binding",whole_source_completed=False,output_hashing_completed=False)
            output_reader=None
            try:
                parent=q.json(PARENT_PIN["path"])
                require(q.snapshots[PARENT_PIN["path"]]==PARENT_PIN,"EXACT_PARENT_PIN")
                expected,rust=parent_scope(parent);source_count=len(rust)
                failed=q.json(FAILED_PIN["path"])
                require(q.snapshots[FAILED_PIN["path"]]==FAILED_PIN
                    and failed["state"]=="DEFERRED_NOT_STARTED" and failed["operation_phase"]=="source_freeze"
                    and failed["stop_reason"]=="STOP_SUSTAINED_SYSTEM_CPU" and failed["heavy_work_started"] is False
                    and failed["worker_created"] is False and failed["cleanup_confirmed"] is True
                    and failed["owned_tree_empty"] is True,"PRESERVED_FAILED_ATTEMPT")
                for pin in FAILED_CODE:require(q.pin(pin["path"])==pin,"FAILED_CODE_ARCHIVE_DRIFT")
                # Bind this new wrapper before broad inventory/reads; partial hashes are never PASS.
                q.pin(SELF);q.pin(TEST)
                phase["phase"]="inventory_discovery"
                require(base.inputs.rust_inputs(c.ROOT,inventory_pacer.reserve)==rust,"WHOLE_RUST_INVENTORY_DRIFT")
                names=set(expected)|helpers;require(len(names)<=2048,"INPUT_COUNT_BUDGET")
                phase["phase"]="input_hashing"
                result=[q.pin(name) for name in sorted(names)]
                require(all(q.snapshots[name]==pin for name,pin in expected.items()),"PRESERVED_PARENT_INPUT_DRIFT")
                phase["whole_source_completed"]=True
                if captures and captures[-1].build is not None:
                    phase["phase"]="output_hashing"
                    require(captures[-1].build["executable_path"]==executable_name(run),"ARTIFACT_GENERATION")
                    output_reader=BuildReader(c.ROOT,lambda:q.checkpoint())
                    candidate=output_reader.pin(executable_name(run))
                    require(0<candidate["bytes"]<=1024**3,"BOUNDED_ARTIFACT_SIZE")
                    output_reader.finish()  # Two paced byte reads of the exact newly compiled suffix.
                    artifact_pin=candidate;phase["output_hashing_completed"]=True
                phase["phase"]="completed"
                return result
            except ValueError as error:
                if str(error).endswith("_STOP_EARLY_READ_PRESSURE_NOT_COOLING"):
                    raise ValueError("STOP_EARLY_READ_PRESSURE_NOT_COOLING") from None
                raise
            finally:
                read_pressure.restore()
                phase.update(completed_input_pins=list(q.snapshots.values()),bytes_read=q.bytes_read,
                    reader_passes=q.read_passes,inventory_query_pacing=inventory_pacer.summary(),
                    file_open_pacing=q.open_pacer.summary(),early_pressure=pressure_summary(read_pressure))
                if output_reader is not None:
                    phase["output_reader"]=dict(bytes_read=output_reader.bytes_read,
                        read_passes=output_reader.read_passes,final_fresh_hashes=output_reader.final_fresh_hashes)
                input_phases.append(phase)
    def admission(row,count):
        headroom=c.POLICY["stop_ram_min_percent"]+c.POLICY["job_memory_stop_percent"]
        return original_admitted(row,count) if row["available_ram_percent"]>=headroom else 0
    def write(row,file,**kwargs):
        nonlocal accepted
        build=captures[-1].build if captures else None
        accepted=(row["state"]=="PASS_SCOPED_NOT_GATE" and row["cleanup_confirmed"] is True
            and row["owned_tree_empty"] is True and build is not None and artifact_pin is not None)
        if row["state"]=="PASS_SCOPED_NOT_GATE":row["state"]=PASS if accepted else "STOPPED_NOT_ACCEPTED"
        row.update(schema_version="hwpx-agent.p09-case112-current-stored-build/v1",
            current_library_parent_pin=PARENT_PIN,whole_workspace_Rust_input_count=source_count,
            current_test_executable_built=accepted,current_build_binding_accepted=accepted,
            compiled_test_artifact_pin=artifact_pin,compiled_artifact_byte_passes=2 if artifact_pin else 0,
            catalog_binding=build,source_input_bytes_checked_before_after=accepted,
            selected_target_directory=TARGET.relative_to(c.ROOT).as_posix(),compile_recipe=recipe(run),
            current_test_package_profile_config=list(profile.CONFIG),
            compile_admission_RAM_percent=c.POLICY["stop_ram_min_percent"]+c.POLICY["job_memory_stop_percent"],
            dependency_cache_reuse_planned=True,dependency_cache_hit_or_speedup_proven=False,
            preserved_failed_attempt_pin=FAILED_PIN,preserved_failed_code_pins=list(FAILED_CODE),
            input_phase_observations=input_phases,metadata_and_file_open_pacing_enabled=True,
            early_input_read_pressure_reuses_original_observer=True,
            same_sample_parent_CPU_and_private_memory_observations=True,
            last_same_sample_parent_observation=owner.samples[-1] if owner.samples else None,
            prior_queue_cases=105,next_case=112,accepted_count_delta=0,
            runtime_tests_executed=False,compiled249_listing_qualified=False,full249_current_qualified=False,
            current_library_bound_to_old_test_binary=False,source_overwritten_or_frozen_pins_rebased=False,
            assertions_and_overflow_checks_retained=True,PC_freeze_resolved=False,A12_gate="OPEN",A13_gate="OPEN")
        return raw_dump(row,file,**kwargs)
    with patch.object(c,"__file__",str(c.ROOT/SELF)),patch.object(c,"TARGET",TARGET), \
        patch.object(c,"TASKS",{task:list(ARGS)}),patch.object(c,"pins",pins),patch.object(c,"admitted_count",admission), \
        patch("bounded_process_progress.BoundedProcessCapture",Capture),patch.object(json,"dump",write), \
        patch.object(c.Windows,"sample",sampled):
        code=c.run(task,destination,600)
    return 0 if accepted else (code or 2)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=int,required=True)
    return run_owned(parser.parse_args().run)


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) else "CURRENT_STORED_BUILD_REDACTED_FAILURE"
        closed=code if re.fullmatch(r"[A-Z_]{1,160}",code) else "CURRENT_STORED_BUILD_REDACTED_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=closed)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
