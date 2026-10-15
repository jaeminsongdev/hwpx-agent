"""Stricter 10-second product window for the proposed case165 full retry.

Original source/CPU/RAM/IO/600-second guards and capture/cleanup code remain.
No retry dispatch, product-result reuse, historical mutation or queue writer.
"""
import ast
import hashlib
from types import CellType,FunctionType,SimpleNamespace as NS

SELF="tools/p09/post_product_recovery_window_v1.py"
TEST="tools/p09/tests/test_post_product_recovery_window_v1.py"
WINDOW_PIN=dict(path="tools/p09/strict_product_window_v1.py",bytes=4696,
    sha256="cd35710cbd11e47cc0a83dd2f28c03772b86267713d52bb8129ed52c670cc701")
PREFIX="implementation/p09/evidence/p09-361-case165-"
SECONDS=10


def require(ok,label):
    if not ok:raise ValueError("RECOVERY_WINDOW_"+label)


def clone(fn,code=None,*,env=None,closure=None):
    require(type(fn) is FunctionType,"ORIGINAL_FUNCTION")
    result=FunctionType(fn.__code__ if code is None else code,
        fn.__globals__ if env is None else env,argdefs=fn.__defaults__,
        closure=fn.__closure__ if closure is None else closure)
    result.__kwdefaults__=fn.__kwdefaults__
    return result


def tighten_window(component,raw):
    require(type(raw) is bytes and len(raw)==WINDOW_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest()==WINDOW_PIN["sha256"],"EXACT_ORIGINAL_WINDOW_SOURCE")
    require(type(component.SECONDS) is int and component.SECONDS==15,"ORIGINAL_WINDOW15")
    # The frozen private loader compiles all Assign/FunctionDef/ClassDef nodes
    # without import statements. Python 3.14's imported-module optimization can
    # produce different bytecode for the same math.isfinite call. Reproduce
    # BOTH exact original compilation profiles, never mix methods or ignore
    # bytecode differences. A complete class+connect family must match one.
    tree=ast.parse(raw.decode("utf-8"))
    nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef))]
    profiles=(raw,ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))
    matched=False
    for source in profiles:
        verified=dict(__name__="p09_exact_verified_window",math=component.math,time=component.time,NS=component.NS)
        exec(compile(source,component.connect.__code__.co_filename,"exec"),verified)
        complete=component.connect.__code__==verified["connect"].__code__
        for name in ("Window","Input"):
            actual=getattr(component,name);expected=verified[name]
            complete=complete and type(actual) is type and actual.__bases__==expected.__bases__
            for method,value in vars(expected).items():
                if type(value) is FunctionType:
                    complete=complete and getattr(actual,method).__code__==value.__code__
        matched=matched or complete
    require(matched,"ENTIRE_ORIGINAL_CLASSES_AND_CAPTURE_CODE")
    old=component.Window
    env=dict(old.remaining.__globals__,SECONDS=SECONDS)
    attrs={k:(clone(v,env=env) if type(v) is FunctionType else v)
        for k,v in vars(old).items() if k not in ("__dict__","__weakref__")}
    revised=type(old.__name__,old.__bases__,attrs)
    # Input/GO/flush/close and the nested original capture remain untouched.
    connected=clone(component.connect,env=dict(component.connect.__globals__,Window=revised))
    return NS(**{**vars(component),"SECONDS":SECONDS,"Window":revised,"connect":connected})


def code_slots(fn,changes):
    """Full-code inverse by constant position, not ambiguous value reversal."""
    require(type(fn) is FunctionType,"MODEL_FUNCTION")
    before=fn.__code__;constants=list(before.co_consts);edits=[]
    for old,new in changes.items():
        positions=[i for i,v in enumerate(constants) if type(v) is int and v==old]
        require(len(positions)==1,"ONE_EXACT_PRODUCT_CONSTANT_SLOT")
        i=positions[0];edits.append((i,old));constants[i]=new
    changed=before.replace(co_consts=tuple(constants));undo=list(changed.co_consts)
    for i,value in edits:undo[i]=value
    require(changed.replace(co_consts=tuple(undo))==before,"ENTIRE_MODEL_CODE_INVERSE")
    return changed


def tighten_model(original):
    require(type(original) is FunctionType and original.__name__=="model"
        and original.__code__.co_filename.replace("\\","/").endswith("strict_product_window_model_v1.py")
        and original.__code__.co_freevars==("revised",),"EXACT_WINDOW15_MODEL_WRAPPER")
    revised=original.__closure__[0].cell_contents
    require(type(revised) is FunctionType and revised.__name__=="model"
        and revised.__code__.co_filename.replace("\\","/").endswith("held_native_read_views_v1.py"),"ORIGINAL_INNER_MODEL")
    inner=clone(revised,code_slots(revised,{15:SECONDS}))
    return clone(original,code_slots(original,{15:SECONDS,5:20-SECONDS}),closure=(CellType(inner),))


def owned_pipe_cases(c,guard,component):
    """Real original GO/capture APIs and serial, bounded owned Job cleanup."""
    import subprocess,sys,time
    from bounded_process_progress import BoundedProcessCapture
    cases=[]
    for delay in (0,11):
        windows=c.Windows();job=windows.job();process=None;capture=None;binding=None
        stopped=False;captured=False;terminal=None;assigned=False
        try:
            limits=windows.verify_job_limits(job)
            program="import sys,time;assert sys.stdin.buffer.readline()==b\"P149_GO\\n\";time.sleep(float(sys.argv[1]));print(\"RECOVERY_PIPE_DONE\")"
            binding=component.connect(subprocess.Popen,BoundedProcessCapture)
            process=binding.Popen([sys.executable,"-B","-c",program,str(delay)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                cwd=c.ROOT,creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW)
            handle=windows.k.OpenProcess(0x101,False,process.pid)
            try:
                require(handle and windows.k.AssignProcessToJobObject(job,handle),"OWNED_PIPE_JOB_ASSIGN")
                assigned=True
            finally:
                if handle:require(windows.k.CloseHandle(handle),"OWNED_PIPE_HANDLE_CLEANUP")
            guard.check(force=True)
            process.stdin.write(component.GO);process.stdin.flush()
            capture=binding.Capture(process)
            try:
                while process.poll() is None:
                    guard.check();capture.progress();time.sleep(.05)
                stdout,stderr=capture.communicate(2)
                require(stdout.strip()=="RECOVERY_PIPE_DONE" and stderr=="" and process.returncode==0,"COMPLETE_OWNED_PIPE_OUTPUT")
                captured=True
            except ValueError as error:
                require(error.args==("STOP_STRICT_PRODUCT_WINDOW",),"EXPECTED_REAL_WINDOW_TIMEOUT")
                stopped=True
            require((delay==0 and captured and not stopped) or (delay==11 and stopped and not captured),"SHORT_PASS_LONG_TIMEOUT")
        finally:
            require(windows.k.TerminateJobObject(job,1),"OWNED_PIPE_TERMINATE")
            if process is not None:
                # Only this exact helper may be outside the Job if assignment
                # failed. Never leave a child waiting forever for GO.
                if not assigned and process.poll() is None:process.terminate()
                process.wait(timeout=2)
            if capture is not None:capture.close()
            elif process is not None:
                for stream in (process.stdin,process.stdout,process.stderr):stream.close()
            terminal=windows.accounting(job)
            require(windows.k.CloseHandle(job),"OWNED_PIPE_JOB_CLOSE")
            require(terminal["active_processes"]==0,"OWNED_PIPE_TREE_EMPTY")
        diagnostics=binding.state.diagnostics()
        require(diagnostics["maximum_GO_to_complete_capture_seconds"]==10
            and diagnostics["actual_GO_writes"]==diagnostics["actual_capture_count"]==1,"REAL_ONE_GO_ONE_CAPTURE")
        cases.append(dict(requested_child_delay_seconds=delay,complete_capture=captured,
            strict_window_stop=stopped,window=diagnostics,owned_limits_readback=limits,
            active_processes_after_cleanup=terminal["active_processes"],cleanup_confirmed=True))
    return cases


def main():
    import argparse,io,json,re,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    policy=host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--pipe",action="store_true");parser.add_argument("--code-attempt",type=int,default=2)
    args=parser.parse_args();require(1<=args.attempt<=8 and 1<=args.code_attempt<=8,"BOUNDED_CODE_ATTEMPT")
    output=PREFIX+f"post-product-recovery-window-{'pipe' if args.pipe else 'code'}{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_CODE_RECORD")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic()
    row=dict(state="FAILED_RECOVERY_WINDOW_CODE_NOT_ADOPTED",accepted_count_delta=0,
        GO_authorized=False,next_Native_start_authorized=False,host_resource_policy=policy)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST,"tools/p09/bounded_process_progress.py"):q.pin(path)
        a.exact(q.pin(WINDOW_PIN["path"]),WINDOW_PIN,"ORIGINAL_WINDOW_SOURCE")
        def sources():
            for module in tuple(sys.modules.values()):
                filename=getattr(module,"__file__",None)
                if filename and Path(filename).absolute().is_relative_to(c.ROOT/"tools/p09"):
                    q.pin(Path(filename).absolute().relative_to(c.ROOT).as_posix())
        sources()
        if args.pipe:
            code=q.json(PREFIX+f"post-product-recovery-window-code{args.code_attempt:03}.v1.json")
            a.fields(code,dict(state="PASS_RECOVERY_PRODUCT_WINDOW10_CODE_NOT_RUNTIME_CONNECTION_OR_RETRY",
                contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_WINDOW10_CODE")
            require(type(code["fresh_inputs"]) is int and code["fresh_inputs"]==code["final_fresh_hashes"]>0,"CLOSED_WINDOW_CODE_HASHES")
            for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_WINDOW_CODE_SOURCES")
            import strict_product_window_v1 as original
            component=tighten_window(original,q.text(WINDOW_PIN["path"]).encode("utf-8"))
            row["owned_pipe_cases"]=owned_pipe_cases(c,guard,component)
            state="PASS_ACTUAL_OWNED_WINDOW10_SHORT_CAPTURE_AND_TIMEOUT_NOT_NATIVE_OR_RETRY"
        else:
            from tests import test_post_product_recovery_window_v1 as tests
            tests.MODULE=sys.modules[__name__]
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"ALL_WINDOW12_CONTRACTS")
            state="PASS_RECOVERY_PRODUCT_WINDOW10_CODE_NOT_RUNTIME_CONNECTION_OR_RETRY"
        sources();q.finish();guard.check(force=True)
        row.update(state=state,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_window_seconds=10,original_product_window_seconds=15,
            original_margin60_CPU_RAM_IO_and_600_deadline_unchanged=True,
            actual_window_binding_required_before_budget_credit=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"CODE_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
