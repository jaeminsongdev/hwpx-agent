"""Fresh current-source stored-provider libtest build; never executes product tests.

원 owned GO/Job/CPU/RAM/cleanup과 전체 Cargo JSON stream 검사를 재사용한다.
통과한 current-library epoch 전체를 유지하고 격리된 check cache에 새 suffix를 만든다.
과거 제품 binary/pins, 사용자 source, 실패 증거를 수정하지 않는다.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from unittest.mock import patch

import check_case112_current_library as base
import run_aead_dependency_signed_tests as profile
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


class BuildReader(base.weighted.WeightedReader):
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
        helpers={SELF,TEST,PARENT_PIN["path"],Path(RAW_DRIVER).relative_to(c.ROOT).as_posix()}
        for module in tuple(sys.modules.values()):
            file=getattr(module,"__file__",None)
            if file:
                path=Path(file).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":helpers.add(path.relative_to(c.ROOT).as_posix())
        if selected_helpers is None:selected_helpers=set(helpers)
        else:require(helpers==selected_helpers,"IMPORTED_HELPER_INVENTORY_DRIFT")
        with patch.object(base.weighted,"BINARY_RATE",1048576),patch.object(base.weighted,"OTHER_RATE",2097152):
            q=BuildReader(c.ROOT,guard)
            parent=q.json(PARENT_PIN["path"])
            require(q.snapshots[PARENT_PIN["path"]]==PARENT_PIN,"EXACT_PARENT_PIN")
            expected,rust=parent_scope(parent);source_count=len(rust)
            require(base.inputs.rust_inputs(c.ROOT,guard)==rust,"WHOLE_RUST_INVENTORY_DRIFT")
            names=set(expected)|helpers;require(len(names)<=2048,"INPUT_COUNT_BUDGET")
            result=[q.pin(name) for name in sorted(names)]
            require(all(q.snapshots[name]==pin for name,pin in expected.items()),"PRESERVED_PARENT_INPUT_DRIFT")
            if captures and captures[-1].build is not None:
                require(captures[-1].build["executable_path"]==executable_name(run),"ARTIFACT_GENERATION")
                output_reader=BuildReader(c.ROOT,guard)
                artifact_pin=output_reader.pin(executable_name(run))
                require(0<artifact_pin["bytes"]<=1024**3,"BOUNDED_ARTIFACT_SIZE")
                output_reader.finish()  # Two paced byte reads of the exact newly compiled suffix.
            return result
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
            prior_queue_cases=105,next_case=112,accepted_count_delta=0,
            runtime_tests_executed=False,compiled249_listing_qualified=False,full249_current_qualified=False,
            current_library_bound_to_old_test_binary=False,source_overwritten_or_frozen_pins_rebased=False,
            assertions_and_overflow_checks_retained=True,PC_freeze_resolved=False,A12_gate="OPEN",A13_gate="OPEN")
        return raw_dump(row,file,**kwargs)
    with patch.object(c,"__file__",str(c.ROOT/SELF)),patch.object(c,"TARGET",TARGET), \
        patch.object(c,"TASKS",{task:list(ARGS)}),patch.object(c,"pins",pins),patch.object(c,"admitted_count",admission), \
        patch("bounded_process_progress.BoundedProcessCapture",Capture),patch.object(json,"dump",write):
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
