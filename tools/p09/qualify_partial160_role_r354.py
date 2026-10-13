"""Partial160 role CODE6 and actual in-memory25-pair projection only."""
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
import terminal_metadata_pressure_v1 as pressure
import runtime_failed160_partial_projection_v1 as role

SELF="tools/p09/qualify_partial160_role_r354.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        actual_manifest_or_physical_file_published=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (role.SELF,role.TEST,SELF,role.attempt.SELF,role.attempt.TEST,
            role.original.SELF,role.original.TEST,pressure.SELF,pressure.TEST)]
        tests=unittest.TestResult()
        unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_runtime_failed160_partial_projection_v1.py").run(tests)
        g.check();out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=6,errors=0,failures=0,skipped=0),"PARTIAL160_ROLE_CODE6")
        admitted=role.admission(q,a)
        import flat_current_queue_envelope_runtime_v28 as controller
        m=controller.M;m.base.configure(160);graph=m.graph_value()
        source=graph.binding_module.source
        retained=graph.binding_module.successor_failure_lineage
        originals=graph.binding.descriptors()
        original_projection=source.Projection.__init__.__code__
        original_decode=source.Projection.decode_fresh.__code__
        original_constructor=graph.binding_module.Binding.__init__.__code__
        connection=role.connect(source,graph.binding_module,admitted)
        a.require(graph.binding_module.successor_failure_lineage is retained and
            source.Projection.__init__.__code__ is original_projection and
            source.Projection.decode_fresh.__code__ is original_decode and
            graph.binding_module.Binding.__init__.__code__ is original_constructor,
            "ALL_ORIGINAL_PROJECTION_CODEC_CONSTRUCTOR_AND_PRIOR_LINEAGE_RETAINED")
        for desc in originals:
            a.exact(source.descriptor(desc["semantic_original_pin"],desc["physical_envelope_pin"],next_case=160),
                desc,"EVERY_ORIGINAL_TWENTY_FOUR_DESCRIPTOR_UNCHANGED")
        actual,raw=q._read(role.ROOT["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,role.ROOT,"ACTUAL_UNMODIFIED_FAILED160_SERIALIZER_BYTES")
        encoded=source.codec.encode(bytes(raw),q.checkpoint)
        physical=dict(path=role.PHYSICAL,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        descriptor=source.descriptor(role.ROOT,physical,next_case=160)
        rows=originals+[descriptor]
        required=m.base.scope.pins([d["semantic_original_pin"] for d in rows])
        projection=source.Projection(required,rows,next_case=160,checkpoint=q.checkpoint)
        for _ in range(2):
            a.exact(projection.decode_fresh(role.ROOT["path"],physical,encoded,q.checkpoint),bytes(raw),
                "TWO_MEMORY_EXACT_PARTIAL160_SOURCE_DECODES")
        a.require(len(projection.semantic_pins)==len(projection.physical_pins)==25,
            "BIJECTIVE_25_PAIR_MEMORY_PROJECTION_NOT_REAL_MANIFEST")
        for pin in controller.RAW_PINS+[controller.RAW_TEST_PIN]+m.old.NAMESPACE_SOURCE_PINS:
            a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_CONTROLLER_AND_PRIVATE_GRAPH_SOURCE_INPUTS")
        q.pin(m.SELF);q.pin(m.TEST)
        q.finish();g.check(force=True)
        out.update(state="PASS_PARTIAL160_FAILURE_ROLE_CODE6_TWO_MEMORY_DECODES_NOT_REAL_MANIFEST_NATIVE_OR_GO",
            source_pins=pins+controller.RAW_PINS+[controller.RAW_TEST_PIN]+m.old.NAMESPACE_SOURCE_PINS,
            new_code_pins=pins[:2],admission=admitted,connection_proof=connection,
            original_failed_runtime_pin=role.ROOT,memory_physical_pin=physical,
            memory_pair_count=25,memory_decode_passes=2,
            existing_actual_manifest_not_relabelled_as25_pairs=True,
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
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
