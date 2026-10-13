"""CODE9 plus fresh actual152/158 lineage and twenty-pair private projection."""
import ctypes
import json
from pathlib import Path
import re
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
import runtime_successor_binding_v1 as successor
import runtime_failed_receipt_projection_v1 as first
import runtime_failed_receipt_projection_v2 as second
import runtime_envelope_namespace_bundle_v1 as bundle
import current_stored_runtime_scope as scope

SELF="tools/p09/qualify_successor_binding_r340.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        P09_gate="OPEN",actual159_product_or_Native_executed=False,current159_whole_scope_or_GO_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(successor.SELF,successor.TEST,SELF,first.SELF,first.TEST,second.SELF,second.TEST,bundle.SELF)
        pins=[q.pin(path) for path in paths]
        admitted=successor.admission(q,a,first,second)
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_runtime_successor_binding_v1.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"SUCCESSOR_PRIVATE_BINDING_CODE9")
        core=[q.pin(path) for path in ("tools/p09/runtime_record_envelope_v1.py","tools/p09/runtime_record_envelope_v2.py",
            "tools/p09/runtime_envelope_source_projection_v1.py","tools/p09/runtime_envelope_scope_binding_v1.py")]
        ns,ast_proof=bundle.load(a.c.ROOT,core,{"current_stored_runtime_scope":scope})
        module=ns.runtime_envelope_scope_binding_v1
        installed=successor.connect(module,admitted,first,second)
        prior=a.read_exact(q,successor.ROOT)
        produced=q.json("implementation/p09/evidence/p09-361-case159-four-envelope-producer-r728.v1.json")
        a.fields(produced,dict(state="PASS_FOUR_SUCCESSOR159_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_RUNTIME_OR_GO",
            authority152_pin=successor.AUTHORITY,actual158_pin=successor.ROOT,decode_passes=8,
            original_receipts_rewritten=False,write_rate_bytes_per_second=2097152,cleanup_confirmed=True),"FOUR_ACTUAL_DERIVATIVES_NOT_PRODUCT")
        for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_FOUR_PRODUCER_SOURCES")
        old=prior["source_input_representation"]
        descriptors=[module.source.descriptor(r["semantic_original_pin"],r["physical_envelope_pin"],next_case=159)
                     for r in old["descriptors"]]+produced["explicit_descriptors"]
        manifest=dict(path="implementation/p09/evidence/p09-361-case159-future-source-manifest.v1.json",bytes=1,sha256="0"*64)
        semantic=scope.extend(scope.pins(old["semantic_source_freeze"]),scope.pins([successor.ROOT,successor.AUTHORITY,manifest]))
        for desc in descriptors:
            original,physical=desc["semantic_original_pin"],desc["physical_envelope_pin"]
            a.exact(q.fresh_pin(original["path"]),original,"FRESH_ALL_TWENTY_ORIGINALS")
            a.exact(q.fresh_pin(physical["path"]),physical,"FRESH_ALL_TWENTY_DERIVATIVES")
        bound=module.Binding(descriptors,manifest,next_case=159);projected,_=bound.project(semantic,g.check)
        a.exact(len(bound.descriptors()),20,"ALL_TWENTY_PAIRS")
        a.exact(bound.representation(projected)["prior_failure_lineage"],admitted,"EXPLICIT_PRIOR_FAILURES_STAY_FAILURES")
        q.finish();g.check(force=True)
        out.update(state="PASS_SUCCESSOR159_BINDING_CODE9_FRESH_TWENTY_PAIRS_NOT_CURRENT_RUNTIME_OR_GO",
            new_code_pins=pins[:2],source_pins=pins+core,explicit_prior_failure_lineage=admitted,
            source_pair_count=20,explicit_descriptors=descriptors,
            future_manifest_placeholder_not_published=True,future_manifest_placeholder_not_runtime_input=True,
            semantic_count=len(projected.semantic_pins),physical_count=len(projected.physical_pins),
            original_constructor_inverse_code_equal=True,private_core_ast_proofs=ast_proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
