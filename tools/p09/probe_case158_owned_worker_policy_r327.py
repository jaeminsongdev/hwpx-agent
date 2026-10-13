"""Actual owned Python worker/GO/Job policy probe; product call intercepted.

The complete original worker bodies run, except their final subprocess call is
replaced by a diagnostic sink. No Rust test, Cargo, SQL or Native source frame
is executed. This cannot stand in for current158 product or full admission.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_worker_connection_v1 as connection
from bounded_process_progress import BoundedProcessCapture

SELF="tools/p09/probe_case158_owned_worker_policy_r327.py"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case158-worker-policy-capsule001.v1.json",
    bytes=6383,sha256="37279afffea965613e416cb951d17da4c2c1ec7656bd28d9c58ef8042930b04c")
CONFIG="implementation/p09/evidence/p09-361-case158-step-config001.v1.json"
CODE="implementation/p09/evidence/p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json"


def child():
    a=launch.a
    with (a.c.ROOT/CAPSULE["path"]).open("rb") as stream:data=stream.read(connection.MAX_BYTES+1)
    binding,_=connection.decode(data,{k:CAPSULE[k] for k in ("bytes","sha256")},lambda:None)
    import flat_current_queue_product_window_runtime_v18 as prior
    prior.M.base.configure(158)
    engine,_=prior.template();original=engine.worker
    a.exact(original.__code__.co_filename,"tools/p09/run_case112_current_stored.py","ENTIRE_QUALIFIED_WORKER_CODE")
    # Original worker has no independent CPU sampler. Its parent owns the Job
    # and original resource Guard throughout this bounded diagnostic dispatch.
    policy=connection.raw_policy.Policy(a.c.ROOT,binding,lambda:True,lambda:None)
    execute,state=connection.connect_worker(original,policy);sink=[]
    def diagnostic_call(argv,**kwargs):
        env=original.__globals__
        a.exact(argv,[str(a.c.ROOT/env["scope"].EXE_PIN["path"]),*env["arguments"]()],"UNCHANGED_FINAL_EXE_ARGUMENTS")
        a.exact(argv[1],"actual_import::source_review_assembly::stored_assembly_retains_complete_source_raw_typed_review_and_old_branches_without_publication","COMPILED158_ONLY")
        a.exact(kwargs["cwd"],a.c.ROOT,"ORIGINAL_CWD")
        a.exact(kwargs["stdin"],subprocess.DEVNULL,"ORIGINAL_CHILD_INPUT")
        for key in ("CARGO_PROFILE_TEST_DEBUG_ASSERTIONS","CARGO_PROFILE_TEST_OVERFLOW_CHECKS"):
            a.exact(kwargs["env"][key],"true","ORIGINAL_ASSERTIONS_ON")
        a.exact(kwargs["env"]["RUST_TEST_THREADS"],"1","ONE_TEST_THREAD")
        name=next(iter(binding.originals))
        try:(a.c.ROOT/name).open("rb")
        except ValueError as error:a.exact(str(error),"STOP_LIVE_RAW_ENVELOPE_RECEIPT_ACCESS","ACTUAL_WORKER_POLICY_DENIAL")
        else:raise ValueError("WORKER_RAW_READ_POLICY_MISSING")
        sink.append(True);return 0
    with patch.object(subprocess,"call",diagnostic_call):code=execute(connection.TASK)
    a.exact(code,0,"DIAGNOSTIC_WORKER_EXIT");a.exact(sink,[True],"ONE_INTERCEPTED_PRODUCT_CALL")
    a.require(policy.restored and policy.raw_attempts==1,"ACTUAL_WORKER_RESTORE_AND_DIAGNOSTIC_DENIAL")
    print(json.dumps(dict(state="PASS_ACTUAL_OWNED_PYTHON_WORKER_POLICY_PRODUCT_CALL_INTERCEPTED",
        product_child_executed=False,original_GO_and_IsProcessInJob_body_retained=True,
        original_worker_code_filename=original.__code__.co_filename,
        intercepted_product_subprocess_calls=1,deliberate_raw_access_attempts=1,
        worker_policy=connection.evidence(state,policy)),ensure_ascii=True,allow_nan=False))
    return 0


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)();process=capture=job=None;job_empty=False
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_product_or_Native_frame_executed=False,full_current158_worker_dispatch_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        qual=q.json(CODE)
        a.fields(qual,dict(state="PASS_WORKER_POLICY_CODE12_ACTUAL11_CAPSULE_NOT_WORKER_DISPATCH_OR_PRODUCT",
            cleanup_confirmed=True,contracts=dict(run=12,errors=0,failures=0,skipped=0)),"CURRENT_CODE12")
        for p in qual["source_pins"]:a.exact(q.pin(p["path"]),p,"EXACT_WORKER_COMPONENT_CODE")
        step=q.json(CONFIG)
        a.fields(step,dict(index=158,before=151,prior_queue_pin=connection.AUTHORITY,
            prior_candidate_pin=connection.ROOT),"EXACT_CURRENT158_STEP")
        a.exact(q.pin(CAPSULE["path"]),CAPSULE,"ACTUAL_FILE_CAPSULE_WITH_TERMINAL_LF")
        windows=g.windows;job=windows.job();limits=windows.verify_job_limits(job)
        process=subprocess.Popen([sys.executable,"-B",str(a.c.ROOT/SELF),"--diagnostic-child"],
            cwd=a.c.ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
        handle=windows.k.OpenProcess(0x101,False,process.pid)
        try:a.require(handle and windows.k.AssignProcessToJobObject(job,handle),"OWNED_DIAGNOSTIC_JOB_ASSIGN")
        finally:
            if handle:a.require(windows.k.CloseHandle(handle),"OWNED_DIAGNOSTIC_PROCESS_HANDLE_CLOSE")
        g.check();process.stdin.write(b"P149_GO\n");process.stdin.flush()
        capture=BoundedProcessCapture(process,output_limit=8192,parse_markers=False)
        deadline=time.monotonic()+15
        while process.poll() is None:
            time.sleep(.5);g.check(force=True)
            a.require(windows.accounting(job)["peak_job_private_percent"]<a.c.POLICY["job_memory_stop_percent"],"OWNED_DIAGNOSTIC_MEMORY_STOP")
            a.require(time.monotonic()<deadline,"OWNED_DIAGNOSTIC15_TIMEOUT")
        output,errors=capture.communicate(timeout=3)
        a.require(process.returncode==0 and not errors,"OWNED_DIAGNOSTIC_CHILD_TERMINAL")
        observed=json.loads(output)
        a.fields(observed,dict(state="PASS_ACTUAL_OWNED_PYTHON_WORKER_POLICY_PRODUCT_CALL_INTERCEPTED",
            product_child_executed=False,original_GO_and_IsProcessInJob_body_retained=True,
            intercepted_product_subprocess_calls=1,deliberate_raw_access_attempts=1),"ACTUAL_DIAGNOSTIC_NOT_PRODUCT")
        final=windows.accounting(job);job_empty=final["active_processes"]==0 and final["owned_processes"]==[]
        a.require(job_empty,"OWNED_DIAGNOSTIC_JOB_EMPTY")
        capture.close();capture=None
        a.require(windows.k.CloseHandle(job),"OWNED_DIAGNOSTIC_JOB_CLOSE");job=None
        q.finish();g.check(force=True)
        result.update(state="PASS_ACTUAL158_OWNED_WORKER_GO_JOB_RAW_POLICY_PRODUCT_CALL_INTERCEPTED_NOT_PRODUCT",
            owned_Job_limits=limits,owned_Job_final=final,child_diagnostic=observed,
            raw_capsule_file_pin=CAPSULE,canonical_capsule_bytes=6382,terminal_LF_separate_from_canonical_capsule=True,
            original_whole_Native_source_admission_not_claimed=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            source_pins=[q.snapshots[SELF],q.snapshots[CONFIG],q.snapshots[CAPSULE["path"]]],
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_OWNED_DIAGNOSTIC_FAILURE"
    finally:
        clean=True
        try:
            if process and process.poll() is None:process.kill();process.wait(timeout=5)
            if capture:capture.close()
            elif process:
                for stream in (process.stdin,process.stdout,process.stderr):
                    if stream:stream.close()
            if job:
                final=g.windows.accounting(job);job_empty=final["active_processes"]==0 and final["owned_processes"]==[]
                clean=bool(g.windows.k.CloseHandle(job)) and job_empty
        except (ValueError,OSError,subprocess.SubprocessError):clean=False
        g.close();result["cleanup_confirmed"]=g.cleanup and clean and (process is None or job_empty)
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") and result["cleanup_confirmed"] else 1


if __name__=="__main__":
    try:raise SystemExit(child() if sys.argv[1:]==["--diagnostic-child"] else main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        print(json.dumps(dict(state="FAILED_DIAGNOSTIC_CHILD_NOT_PRODUCT",error_type=type(error).__name__)))
        raise SystemExit(2) from None
