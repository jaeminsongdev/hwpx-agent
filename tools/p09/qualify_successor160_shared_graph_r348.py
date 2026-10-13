"""Actual24pair shared graph, no engine/body/GO; metadata warning75 retained."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
from types import SimpleNamespace as NS

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
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v2 as manifest
import runtime_successor_worker_capsule_v2 as capsule
import successor_runtime_graph_v2 as factory

SELF="tools/p09/qualify_successor160_shared_graph_r348.py"
QUAL="implementation/p09/evidence/p09-361-case160-capsule-code6-r758.v1.json"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual160_product_or_Native_executed=False,actual160_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (factory.SELF,SELF,successor.SELF,successor.TEST,manifest.SELF,
            capsule.SELF,capsule.TEST,pressure.SELF,pressure.TEST)]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;old=m.old;m.base.configure(159);g.check()
        code=q.json(QUAL)
        a.fields(code,dict(state="PASS_ACTUAL160_CAPSULE_CODE6_MANIFEST24_MEMORY_TRANSPORT_NOT_WORKER_DISPATCH_OR_PRODUCT",
            contracts=dict(run=6,errors=0,failures=0,skipped=0),source_pairs=24,cleanup_confirmed=True),"QUALIFIED160_CAPSULE_CODE6")
        for p in code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_QUALIFIED_CAPSULE_SOURCES")
        def admit(reader):return successor.admission(reader,a,old.failed_role,old.failed004_role)
        once,counts=old.admission_once.connect(admit)
        context=once(q)
        graph=factory.build(q,old,successor,capsule,context=context)
        def shared_admission(reader,api,first,second):
            a.require(api is a and first is old.failed_role and second is old.failed004_role,
                "EXACT_SAME_READER_CONTEXT_DEPENDENCIES")
            return once(reader)
        private=NS(**{**vars(successor),"admission":shared_admission})
        pin=q.pin(manifest.PATH)
        bound,inherited,proof=manifest.load(q,pin,a,controller=m,new_module=graph.binding_module,successor=private)
        a.require(type(bound) is type(graph.binding),"SAME_ACTUAL160_MANIFEST_CAPSULE_BINDING_TYPE")
        a.exact(bound.descriptors(),graph.binding.descriptors(),"ALL_ACTUAL160_MANIFEST_CAPSULE_PAIRS")
        a.exact(dict(bound.manifest_pin),dict(graph.binding.manifest_pin),"SAME_ACTUAL160_MANIFEST_PIN")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_SHARED_PARENT_WORKER_ORACLE_GRAPH_MANIFEST24_NOT_ENGINE_CONFIG_NATIVE_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS,source_pairs=24,manifest_pin=pin,
            original_core_ast_proofs=graph.core_ast_proofs,manifest_admission=proof,
            same_reader_context_declaration_admissions=counts,
            actual_engine_calls=0,actual_frames=0,actual_worker_dispatches=0,
            actual160_engine_configuration_or_complete_scope_preflight_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-10:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
