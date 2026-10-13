"""Actual160 manifest24 and capsule transport; no worker/Native/product GO."""
import ctypes
import hashlib
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
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v2 as manifest
import runtime_successor_worker_capsule_v2 as capsule

SELF="tools/p09/qualify_successor160_capsule_r348.py"
QUAL="implementation/p09/evidence/p09-361-case160-binding-manifest-code10-r756.v1.json"
CAPSULE_PATH="implementation/p09/evidence/p09-361-case160-worker-policy-capsule001.v3.json"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual160_product_or_Native_executed=False,actual160_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (capsule.SELF,capsule.TEST,SELF,successor.SELF,successor.TEST,manifest.SELF)]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;old=m.old;m.base.configure(159);g.check()
        qualified=q.json(QUAL)
        a.fields(qualified,dict(state="PASS_ACTUAL160_BINDING_CODE10_MANIFEST24_OLD159_FULL_ADMISSION_NOT_CURRENT_CONTROLLER_OR_GO",
            contracts=dict(run=10,errors=0,failures=0,skipped=0),source_pairs=24,cleanup_confirmed=True),"QUALIFIED_ACTUAL160_MANIFEST24")
        for p in qualified["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_QUALIFIED160_MANIFEST_CODE")
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_runtime_successor_worker_capsule_v2.py")
        result=unittest.TestResult();suite.run(result);g.check()
        out["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        if result.errors or result.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in result.errors+result.failures]
        a.exact(out["contracts"],dict(run=6,errors=0,failures=0,skipped=0),"SUCCESSOR160_CAPSULE_CODE6")
        core=[p for p in old.NAMESPACE_SOURCE_PINS if p["path"] in (
            "tools/p09/runtime_record_envelope_v1.py","tools/p09/runtime_record_envelope_v2.py",
            "tools/p09/runtime_envelope_source_projection_v1.py","tools/p09/runtime_envelope_scope_binding_v1.py")]
        for p in core:a.exact(q.pin(p["path"]),p,"CURRENT_ORIGINAL_CORE4")
        ns,core_proof=old.namespace_bundle.load(a.c.ROOT,core,{"current_stored_runtime_scope":old.base.scope})
        module=ns.runtime_envelope_scope_binding_v1
        context=successor.admission(q,a,old.failed_role,old.failed004_role)
        successor.connect(module,context,old.failed_role,old.failed004_role)
        pin=q.pin(manifest.PATH)
        bound,inherited,admission=manifest.load(q,pin,a,controller=m,new_module=module,successor=successor)
        api,projection=capsule.connect(old.worker_policy,module,successor.AUTHORITY,successor.ROOT,successor)
        data,transport=api.encode(bound,successor.AUTHORITY,successor.ROOT,g.check)
        decoded,proof=api.decode(data,transport,g.check)
        a.require(type(decoded) is module.Binding,"EXACT160_SHARED_PARENT_WORKER_BINDING_TYPE")
        a.exact(decoded.descriptors(),bound.descriptors(),"ALL_TWENTY_FOUR_CAPSULE_PAIRS")
        a.exact(dict(decoded.manifest_pin),dict(bound.manifest_pin),"ACTUAL160_MANIFEST_PIN_NOT_PLACEHOLDER")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_CAPSULE_CODE6_MANIFEST24_MEMORY_TRANSPORT_NOT_WORKER_DISPATCH_OR_PRODUCT",
            new_code_pins=pins[:2],source_pins=pins+core,manifest_pin=pin,source_pairs=24,
            successor_context=context,manifest_admission=admission,private_core_ast_proofs=core_proof,
            worker_projection_proof=projection,transport_proof=proof,transport_pin=transport,
            future_file_pin=dict(path=CAPSULE_PATH,bytes=len(data)+1,sha256=hashlib.sha256(data+b"\n").hexdigest()),
            capsule_ascii=data.decode("ascii"),actual_worker_dispatch_executed=False,encoded_file_published=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-10:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
