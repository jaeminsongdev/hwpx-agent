"""Full inherited twelve-pair manifest admission, not current Native or product."""
import ctypes
import json
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct

SELF="tools/p09/qualify_failed003_manifest_r335.py"
EXTRA=[dict(path="tools/p09/runtime_failed_receipt_projection_v1.py",bytes=5576,
    sha256="de7ce248585f3fb6de2038bd208699e428c972f230de5e6a0b76bd317496d3a6"),
    dict(path="tools/p09/runtime_failed_receipt_manifest_v1.py",bytes=3880,
    sha256="66f69a01584c756bd406a18cb49291c0ab0c1baec54af11b618a89cabcd703c3")]


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        import flat_current_queue_envelope_runtime_v22 as m
        pins=[q.pin(p) for p in (SELF,EXTRA[0]["path"],EXTRA[1]["path"],"tools/p09/tests/test_runtime_failed_receipt_manifest_v1.py")]
        for pin in m.NAMESPACE_SOURCE_PINS+EXTRA:a.exact(q.pin(pin["path"]),pin,"EXACT_PRIVATE_GRAPH_SOURCE")
        graph,_=m.namespace_bundle.load(a.c.ROOT,m.NAMESPACE_SOURCE_PINS,{
            "current_stored_runtime_scope":m.base.scope,
            "owned_source_read_pressure":sys.modules["owned_source_read_pressure"],
            "strict_product_window_connection_v1":m.prior.WINDOW_LINK})
        extended,_=m.namespace_bundle.load(a.c.ROOT,EXTRA,{
            "runtime_envelope_source_manifest_v2":graph.runtime_envelope_source_manifest_v2})
        failed=extended.runtime_failed_receipt_projection_v1
        loader=extended.runtime_failed_receipt_manifest_v1
        admitted=failed.admission(q,a)
        failed.connect(graph.runtime_envelope_source_projection_v1,graph.runtime_envelope_scope_binding_v1,admitted)
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_runtime_failed_receipt_manifest_v1.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        a.exact(out["contracts"],dict(run=4,errors=0,failures=0,skipped=0),"MANIFEST_CODE4")
        manifest_pin=q.pin(loader.PATH)
        binding,inherited,proof=loader.load(q,manifest_pin,a)
        a.require(len(binding.rows)==12 and binding.originals[failed.ROOT["path"]]==failed.ROOT,"ALL_TWELVE_WITH_FAILED_ROLE")
        q.finish();g.check(force=True)
        out.update(state="PASS_FULL_INHERITED_TWELVE_PAIR_FAILED_MANIFEST_ADMISSION_CODE4_NOT_CURRENT_RUNTIME_OR_GO",
            manifest_pin=manifest_pin,new_code_pins=pins[1:],source_pins=[pins[0]]+m.NAMESPACE_SOURCE_PINS,
            source_pair_count=12,inherited_semantic_input_count=len(inherited),manifest_admission=proof,
            whole_current_controller_worker_Native_or_full_oracle_connected=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FAILED_MANIFEST_QUAL"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
