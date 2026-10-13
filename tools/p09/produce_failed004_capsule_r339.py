"""New sixteen-pair full manifest admission; no current controller/Native GO."""
import ctypes
import json
from pathlib import Path
import sys
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

SELF="tools/p09/produce_failed004_capsule_r339.py"
ROLE_PINS=[{"path":"tools/p09/runtime_failed_receipt_projection_v2.py","bytes":5587,"sha256":"7887c2847247142140f408e0e4668a304f6990650506e011313250bd3ecf71b6"},{"path":"tools/p09/runtime_failed_receipt_manifest_v2.py","bytes":6462,"sha256":"b9a0c607017472b263a31ebb09f17b5cc368a5107b3a5f0bffeca9584a8bd399"}]


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",actual_product_or_Native_executed=False,
        current_controller_worker_or_full_oracle_connected=False,accepted_count_delta=0,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        q.pin("tools/p09/flat_current_queue_envelope_runtime_v24.py")
        import flat_current_queue_envelope_runtime_v24 as old
        g.check()
        for pin in ROLE_PINS+old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS:
            a.exact(q.pin(pin["path"]),pin,"CURRENT_RAW_CLASS_AND_MANIFEST_SOURCES")
        namespaces,namespace_proof=old.namespace_bundle.load(a.c.ROOT,ROLE_PINS,
            {"runtime_failed_receipt_manifest_v1":old.manifest})
        role=namespaces.runtime_failed_receipt_projection_v2
        manifest=namespaces.runtime_failed_receipt_manifest_v2
        pins=[q.pin(name) for name in (manifest.SELF,manifest.TEST,SELF,old.SELF,old.TEST)]
        admitted=role.admission(q,old.a)
        projection_proof=role.connect(old._namespaces.runtime_envelope_source_projection_v1,
            old._namespaces.runtime_envelope_scope_binding_v1,admitted)
        manifest_pin=q.pin(manifest.PATH)
        binding,inherited,proof=manifest.load(q,manifest_pin,old.a)
        a.exact(len(binding.descriptors()),16,"ALL_SIXTEEN_SOURCE_PAIRS")
        a.require(role.ROOT["path"] in inherited,"FAILED004_ORIGINAL_EXPLICIT_IN_SCOPE")
        data,transport_pin=old.worker_policy.encode(binding,old.worker_policy.AUTHORITY,old.worker_policy.ROOT,g.check)
        decoded,transport_proof=old.worker_policy.decode(data,transport_pin,g.check)
        a.exact(decoded.descriptors(),binding.descriptors(),"EXACT_ALL_SIXTEEN_CAPSULE_PAIRS")
        import hashlib
        file_data=data+b"\n"
        future_file_pin=dict(path="implementation/p09/evidence/p09-361-case158-worker-policy-capsule003.v1.json",
            bytes=len(file_data),sha256=hashlib.sha256(file_data).hexdigest())
        q.finish();g.check(force=True)
        out.update(state="PASS_SIXTEEN_PAIR_CAPSULE_MEMORY_TRANSPORT_NOT_CURRENT_WORKER_OR_PRODUCT_OR_FILE_PUBLICATION",
            new_code_pins=pins[:2],source_pins=pins+ROLE_PINS,manifest_pin=manifest_pin,
            explicit_failure004_admission=admitted,source_pair_count=16,
            inherited_semantic_count=len(inherited),manifest_admission_proof=proof,
            private_role_namespace_proofs=namespace_proof,projection_proof=projection_proof,
            transport_pin=transport_pin,future_file_pin=future_file_pin,capsule_ascii=data.decode("ascii"),
            transport_proof=transport_proof,encoded_file_published=False,actual_worker_dispatch_executed=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            value=str(error);out["error_code"]=value if re.fullmatch("[A-Za-z0-9_]{1,256}",value) else "REDACTED_SIXTEEN_PAIR_ADMISSION_FAILURE"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
