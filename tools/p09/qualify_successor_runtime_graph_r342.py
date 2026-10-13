"""Actual shared parent/worker/oracle graph and original private engine, no GO."""
import ctypes
import json
from pathlib import Path
import re
import sys

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
import successor_runtime_graph_v1 as factory
import runtime_successor_binding_v1 as successor
import runtime_successor_worker_capsule_v1 as capsule

SELF="tools/p09/qualify_successor_runtime_graph_r342.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual159_Native_or_worker_or_product_executed=False,actual159_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (factory.SELF,SELF,successor.SELF,successor.TEST,capsule.SELF,capsule.TEST,
            "tools/p09/flat_current_queue_envelope_runtime_v25.py")]
        import flat_current_queue_envelope_runtime_v25 as old
        old.base.configure(159);g.check()
        qualified=q.json("implementation/p09/evidence/p09-361-case159-successor-capsule-code6-r733.v1.json")
        a.fields(qualified,dict(state="PASS_SUCCESSOR159_CAPSULE_CODE6_TWENTY_PAIRS_MEMORY_TRANSPORT_NOT_WORKER_DISPATCH_OR_PRODUCT",
            contracts=dict(run=6,errors=0,failures=0,skipped=0),source_pair_count=20,cleanup_confirmed=True),"QUALIFIED20_CAPSULE_ONLY")
        for p in qualified["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_QUALIFIED_CAPSULE_SOURCES")
        graph=factory.build(q,old,successor,capsule)
        engine,proof=old.prior.template()
        original_worker=engine.worker;original_engine=engine.run_owned
        connected,state=graph.parent.connect_engine(engine,graph.binding)
        a.require(connected.worker is original_worker and state.original is original_engine and
            connected.run_owned.__globals__ is original_engine.__globals__ and
            state.attempts==0 and state.frames==[],"ORIGINAL_ENGINE_WORKER_NO_FRAME_OR_BODY_EXECUTION")
        policy=graph.worker.raw_policy.Policy(a.c.ROOT,graph.binding,lambda:False,q.checkpoint)
        execute,worker_state=graph.worker.connect_worker(original_worker,policy)
        a.require(callable(execute) and worker_state.attempts==0 and worker_state.calls==0,
            "ORIGINAL_WORKER_CONNECTED_NOT_DISPATCHED")
        a.exact(graph.worker.TASK,"case159-current-r001-tests","EXACT159_TASK_NOT_REPLAY158")
        q.finish();g.check(force=True)
        out.update(state="PASS_SUCCESSOR159_UNIFIED_PARENT_WORKER_ORACLE_BINDING_AND_PRIVATE_ENGINE_NOT_NATIVE_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS,source_pair_count=20,private_core_ast_proofs=graph.ast_proof,
            worker_projection_proof=graph.worker_proof,capsule_transport_proof=graph.transport_proof,
            exact_shared_binding_type=True,original_engine_and_worker_not_replaced=True,
            actual_engine_calls=0,actual_frames=0,actual_worker_dispatches=0,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
