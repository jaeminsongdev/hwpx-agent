"""Run002 bounded bootstrap7 and original whole25 binding with final fresh."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
import unittest
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
import successor_current_binding_v3 as binding
import successor_bounded_graph_bootstrap_v3 as bootstrap

SELF="tools/p09/qualify_run002_bootstrap_binding_r357.py"
TEST="tools/p09/tests/test_successor_bounded_graph_bootstrap_v3.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,TEST,binding.SELF,bootstrap.SELF,binding.shared.SELF,binding.manifest.SELF,
            binding.capsule.SELF,binding.capsule.TEST,binding.partial.SELF,binding.partial.TEST,binding.factory.SELF,
            pressure.SELF,pressure.TEST)
        pins=[q.pin(path) for path in paths]
        import flat_current_queue_envelope_runtime_v28 as controller
        controller.M.base.configure(160)
        tests=unittest.TestResult()
        unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_successor_bounded_graph_bootstrap_v3.py").run(tests)
        g.check();out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=7,errors=0,failures=0,skipped=0),"RUN002_BOOTSTRAP_CODE7")
        graph,bounded=bootstrap.load(controller.M.old,q.checkpoint)
        complete,rust,fresh,live,proof=binding.bind(q,controller.PRIOR159)
        a.exact(live.descriptors(),graph.binding.descriptors(),"WHOLE_BINDING_AND_BOUNDED25_IDENTICAL")
        a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"SAME_ACTUAL26_MANIFEST")
        a.require(len(rust)==787 and controller.M.base.CONFIG.index==160,"CURRENT160_AND_ALL_RUST787")
        q.finish();g.check(force=True)
        out.update(state="PASS_RUN002_BOOTSTRAP_CODE7_ORIGINAL_WHOLE25_BINDING_NOT_CONTROLLER_PREFLIGHT_OR_GO",
            source_pins=pins,source_pairs=25,rust_source_count=len(rust),complete_scope_count=len(complete),
            bounded_bootstrap=bounded,full_binding_proof=proof,manifest_pin=dict(live.manifest_pin),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
                if s.get("parent_cpu_machine_percent") is not None),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
