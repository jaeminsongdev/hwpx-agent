"""Actual run002 shared graph with capsule002 and manifest026; no GO."""
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
import runtime_failed160_partial_projection_v2 as role
import runtime_successor_manifest_v4 as manifest
import runtime_successor_binding_v2 as successor
import runtime_successor_worker_capsule_v3 as capsule
import successor_runtime_graph_v3 as factory

SELF="tools/p09/qualify_run002_shared_graph_r356.py"
QUAL="implementation/p09/evidence/p09-361-case160-run002-capsule-code8-r793.v1.json"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        actual_engine_calls=0,actual_worker_dispatches=0,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (SELF,factory.SELF,capsule.SELF,capsule.TEST,role.SELF,role.TEST,
            manifest.SELF,successor.SELF,pressure.SELF,pressure.TEST)]
        code=q.json(QUAL)
        a.fields(code,dict(state="PASS_CURRENT160_RUN002_CAPSULE_CODE8_ACTUAL25_MANIFEST_TRANSPORT_NOT_DISPATCH_CONTROLLER_OR_GO",
            contracts=dict(run=8,errors=0,failures=0,skipped=0),source_pairs=25,
            task="case160-current-r002-tests",cleanup_confirmed=True),"QUALIFIED_CAPSULE_CODE8")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_QUALIFIED_CAPSULE_SOURCES")
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(159);old=m.old
        def admit(reader):return successor.admission(reader,a,old.failed_role,old.failed004_role)
        once,counts=old.admission_once.connect(admit)
        graph=factory.build(q,old,successor,capsule,role,context=once(q))
        def shared(reader,api,first,second):
            a.require(api is a and first is old.failed_role and second is old.failed004_role,
                "EXACT_SAME_READER_CONTEXT_DEPENDENCIES")
            return once(reader)
        current=NS(**{**vars(successor),"admission":shared})
        mf=q.pin(manifest.PATH)
        bound,scope,proof=manifest.load(q,mf,a,controller=m,new_module=graph.binding_module,successor=current)
        a.require(type(bound) is type(graph.binding),"SAME_ACTUAL25_MANIFEST_CAPSULE_BINDING_TYPE")
        a.exact(bound.descriptors(),graph.binding.descriptors(),"ALL_REAL25_MANIFEST_CAPSULE_PAIRS")
        a.exact(dict(bound.manifest_pin),dict(graph.binding.manifest_pin),"EXACT_REAL_MANIFEST026")
        raw,transport=graph.worker.encode(bound,successor.AUTHORITY,successor.ROOT,q.checkpoint)
        a.exact(transport,code["memory_transport_pin"],"SAME_ORIGINAL_CANONICAL_ENCODING")
        actual,stored=q._read(factory.CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(bytes(stored),raw+b"\n","ACTUAL_FILE_ONLY_ONE_LF_CANONICAL_DIFFERENCE")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_RUN002_SHARED25_PARENT_WORKER_ORACLE_GRAPH_NOT_ENGINE_PREFLIGHT_NATIVE_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS,capsule_pin=factory.CAPSULE,manifest_pin=mf,
            source_pairs=25,original_core_ast_proofs=graph.core_ast_proofs,
            manifest_admission=proof,same_reader_context_declaration_admissions=counts,
            canonical_capsule_file_one_LF_explicit=True,
            current160_engine_configuration_or_complete_scope_preflight_qualified=False,
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
