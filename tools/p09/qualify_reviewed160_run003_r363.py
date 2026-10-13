"""Original identity8/new4 and actual160 run002 template; no product."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
import unittest
from types import FunctionType

k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import terminal_metadata_pressure_v1 as pressure
import reviewed_case160_attempt_v2 as attempt

SELF="tools/p09/qualify_reviewed160_run003_r363.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (attempt.SELF,attempt.TEST,SELF,
            attempt.original.SELF,attempt.original.TEST,attempt.original.original.SELF,attempt.original.original.TEST,
            attempt.original.original.prior.SELF,attempt.original.original.prior.TEST,"tools/p09/reviewed_runtime_attempt_v1.py",
            "tools/p09/reviewed_runtime_attempt_v2.py",pressure.SELF,pressure.TEST)]
        suite=unittest.TestSuite([unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern=name) for name in ("test_reviewed_case160_attempt_v1.py","test_reviewed_case160_attempt_v2.py")])
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
            out["safe_test_failure_tails"]=[s.splitlines()[-1][:160] for _,s in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=20,errors=0,failures=0,skipped=0),"ORIGINAL8_NEW4_IDENTITY")
        review=attempt.reviewed_failure(q,a)
        a.require(not (a.c.ROOT/attempt.ROOT).exists(),"RUN003_ROOT_ABSENT_BEFORE_PRODUCT")
        import flat_current_queue_envelope_runtime_v30 as controller
        m=controller.M;m.base.configure(160)
        for pin in controller.RAW_PINS+[controller.RAW_TEST_PIN]:
            a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_TEMPLATE_RAW_SOURCES")
        q.pin(m.SELF);q.pin(m.TEST)
        template,names,proof=attempt.connect_template(m.prior)
        a.require(names.physical_run(160)==3 and names.root_path(m.base.CONFIG)==attempt.ROOT and
            names.task(160)==attempt.TASK and names.public_run(160,3)==1,"ALL_REAL160_RUN002_IDENTITIES")
        engine,engine_proof=template()
        state=m.prior.ATTEMPT_STATES[-1]
        a.require(state.physical_product_run==3 and state.actual_engine_calls==0,"REAL_SINGLE_ADAPTER_NO_ENGINE_EXECUTION")
        a.require(engine.worker.__code__ is state.original_worker_code,"ORIGINAL_WORKER_BODY_RETAINED")
        seen=set();pending=[engine.run_owned];adapters=[];chain=[]
        while pending:
            a.require(len(seen)<16,"BOUNDED_ORIGINAL_RUN_WRAPPER_GRAPH")
            fn=pending.pop()
            if id(fn) in seen:continue
            seen.add(id(fn))
            closures=[cell.cell_contents for cell in fn.__closure__ or ()]
            captured=[v for v in closures if type(v) is FunctionType]
            matched=[v for v in captured if v.__code__ is state.original_engine_code]
            if any(v is state for v in closures):adapters.append((fn,matched))
            chain.append(dict(function=fn.__name__,closure_function_names=[v.__name__ for v in captured],
                captures_actual_adapter_state=any(v is state for v in closures),
                original_engine_code_matches=len(matched)))
            pending.extend(captured)
            old=fn.__globals__.get("original")
            if type(old) is FunctionType:pending.append(old)
        out["original_wrapper_chain"]=chain
        a.require(len(adapters)==1 and len(adapters[0][1])==1 and
            adapters[0][0].__globals__ is adapters[0][1][0].__globals__,
            "ONE_ADAPTER_SAME_ORIGINAL_RUN_OWNED_PRIVATE_ENVIRONMENT")
        q.finish();g.check(force=True)
        out.update(state="PASS_REVIEWED160_RUN003_IDENTITY_CODE20_ACTUAL_SINGLE_TEMPLATE_NOT_NATIVE_OR_GO",
            source_pins=pins+[q.snapshots[m.SELF],q.snapshots[m.TEST]]+controller.RAW_PINS+[controller.RAW_TEST_PIN],
            new_code_pins=pins[:2],failure_admission=review,template_proof=proof,
            original_engine_proof=engine_proof,physical_product_run=3,qualification_run=1,
            actual_engine_calls=0,actual_worker_calls=0,
            sole_adapter_and_original_run_owned_share_exact_private_globals=True,
            fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
