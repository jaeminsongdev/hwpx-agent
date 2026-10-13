"""Nine failed-role contracts and real memory projection, no Native adoption."""
import ctypes
import hashlib
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
import runtime_failed_receipt_projection_v2 as failed
import runtime_failed_receipt_projection_v1 as prior_failed
import runtime_envelope_namespace_bundle_v1 as bundle
import current_stored_runtime_scope as scope

SELF="tools/p09/qualify_failed004_projection_r339.py"
PINS=[dict(path="tools/p09/runtime_record_envelope_v1.py",bytes=3596,sha256="59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"),
    dict(path="tools/p09/runtime_record_envelope_v2.py",bytes=2891,sha256="9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"),
    dict(path="tools/p09/runtime_envelope_source_projection_v1.py",bytes=6401,sha256="728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"),
    dict(path="tools/p09/runtime_envelope_scope_binding_v1.py",bytes=10750,sha256="0105881d365213e70bd047b5c7fa8de6fda842f3103b71870c8f2224b3e4db3b")]


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(p) for p in (failed.SELF,failed.TEST,SELF,bundle.SELF)]
        admitted=failed.admission(q,a)
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"ORIGINAL_PRIVATE_CLASS_SOURCE_BYTES")
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_runtime_failed_receipt_projection_v2.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"FAILED_ROLE_CODE9")
        graph,graph_proof=bundle.load(a.c.ROOT,PINS,{"current_stored_runtime_scope":scope})
        source=graph.runtime_envelope_source_projection_v1;binding=graph.runtime_envelope_scope_binding_v1
        for name in (prior_failed.SELF,prior_failed.TEST):q.pin(name)
        prior_admitted=prior_failed.admission(q,a)
        prior_failed.connect(source,binding,prior_admitted)
        proof=failed.connect(source,binding,admitted)
        pin,raw=q._read(failed.ROOT["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,failed.ROOT,"CURRENT_ORIGINAL_FAILED_BYTES")
        encoded=source.codec.encode(bytes(raw),g.check)
        encoded_pin=dict(path=failed.PHYSICAL,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        desc=source.descriptor(failed.ROOT,encoded_pin,next_case=158)
        row=json.loads(raw.decode("utf-8"));previous=row["source_input_representation"]
        descriptors=previous["descriptors"]+[desc]
        manifest=previous["manifest_pin"]
        logical=scope.extend(scope.pins(previous["semantic_source_freeze"]),scope.pins([failed.ROOT,failed.REVIEW]))
        obj=binding.Binding(descriptors,manifest,next_case=158);projected,_=obj.project(logical,g.check)
        for _ in range(2):a.exact(projected.decode_fresh(failed.ROOT["path"],encoded_pin,encoded,g.check),bytes(raw),"ACTUAL_LOSSLESS_FAILED_ROLE")
        representation=obj.representation(projected)
        a.exact(representation["same_case_failed004_receipt_provenance"],admitted,"EXPLICIT_FAILURE_ROLE_NOT_PRIOR_SUCCESS")
        a.require(scope.pins(representation["semantic_source_freeze"]).get(failed.ROOT["path"])==failed.ROOT,
            "ORIGINAL_FAILED_PIN_RETAINED")
        q.finish();g.check(force=True)
        out.update(state="PASS_EXACT_FAILED004_ROLE_CODE9_AND_TWO_MEMORY_PROJECTION_DECODES_NOT_CURRENT_RUNTIME_OR_GO",
            new_code_pins=pins[:2],source_pins=pins[2:]+PINS+[q.snapshots[prior_failed.SELF],q.snapshots[prior_failed.TEST]],explicit_failure_admission=admitted,
            projection_proof=proof,private_graph_AST_proofs=graph_proof,
            memory_candidate=dict(original_bytes=failed.ROOT["bytes"],physical_bytes=len(encoded),
                physical_pin=encoded_pin,descriptors_count=len(descriptors),fresh_decode_passes=2,
                semantic_count=len(projected.semantic_pins),physical_count=len(projected.physical_pins),
                encoded_file_published=False,physical_scope_adopted=False,
                current_controller_worker_or_full_oracle_connected=False),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FAILED_ROLE_QUAL"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
