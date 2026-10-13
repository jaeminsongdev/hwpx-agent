"""Qualified private review connection, complete Binding and count-only IO."""
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
import trace_adopted26_metadata_reads_r361 as trace
SELF="tools/p09/qualify_history_connection_binding_r363.py"
PINS=[dict(path="tools/p09/flat_current_queue_envelope_runtime_v30.py",bytes=13368,
    sha256="68299c21e702a49afe82986c66ddfd18422ac2225159425da8c4b956cd1adb4b"),
    dict(path="tools/p09/same_reader_failure_review_once_v1.py",bytes=3180,
    sha256="f9a962fb97db785c22c419640bfb79c4f5a3ded293db141a4b325481328516ab"),
    dict(path="tools/p09/failure_review_current_connection_v1.py",bytes=2958,
    sha256="9250a1a15ec80d71b43f2c3ecc6f95a19858c01f9be22b5c77f40db2c13914e7")]

PINS.append(dict(path="tools/p09/same_reader_history_declaration_once_v1.py",bytes=2461,sha256="5bf2309acbedfe130b7de8225997cc78c640588e757b5bc79e12c36d3eaea3cf"))

def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    restore=None;history_restore=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        new_controller_or_GO_qualified=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=trace.Reader(a.c.ROOT,g.check)
        pins=[q.pin(SELF),q.pin(trace.SELF),q.pin(pressure.SELF),q.pin(pressure.TEST)]
        import flat_current_queue_envelope_runtime_v25 as old
        bundle,proof=old.namespace_bundle.load(a.c.ROOT,PINS,{"flat_current_queue_envelope_runtime_v25":old})
        c=bundle.flat_current_queue_envelope_runtime_v30;m=c.M;m.base.configure(160)
        helper=bundle.same_reader_failure_review_once_v1;connection=bundle.failure_review_current_connection_v1
        for pin in PINS:a.exact(q.pin(pin["path"]),pin,"CURRENT_PRIVATE_CONNECTION_SOURCE")
        suites=[unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern=name)
            for name in ("test_same_reader_failure_review_once_v1.py","test_failure_review_current_connection_v1.py",
                "test_same_reader_history_declaration_once_v1.py","test_runtime_successor_binding_v1.py")]
        tests=unittest.TestResult();unittest.TestSuite(suites).run(tests);g.check()
        contracts=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        a.exact(contracts,dict(run=43,errors=0,failures=0,skipped=0),"WHOLE_REVIEW_CONNECTION_CODE22")
        original=c.attempt.reviewed_failure
        restore,counts,connected=connection.connect(c,q,helper)
        history=c._env["current_binding"].successor.original
        prior=c.PRIOR160.PRIOR160.PRIOR159
        a.require(history is prior.M.current_binding.successor and
            history is prior.SOURCE_NAMESPACES.runtime_successor_binding_v1 and
            history is c.bootstrap.original.successor.original,"ONE_PRIVATE_HISTORICAL_ADMISSION")
        source_before=history.admission
        expected=history.declaration([dict(schema_version=f.ADMISSION_SCHEMA,source_role=f.ROLE,
            failed_runtime_pin=f.ROOT,independent_review_pin=f.REVIEW,current_case=158,
            original_failure_promoted=False,current_product_or_GO_qualified=False)
            for f in (m.old.failed_role,m.old.failed004_role)])
        history.admission,history_counts=bundle.same_reader_history_declaration_once_v1.connect(source_before,expected)
        def restore_history():history.admission=source_before
        history_restore=restore_history
        q.pin(bundle.same_reader_history_declaration_once_v1.TEST)
        c._env["_execution_requested"]=True
        required,rust=m.binding(q)
        graph=m.graph_value()
        a.require(len(graph.binding.descriptors())==26 and len(rust)==787,"WHOLE_CURRENT26_BINDING_RUST787")
        a.require(counts["original_complete_reviews"]==1 and counts["duplicate_declarations_avoided"]>=2,
            "FIRST_WHOLE_REVIEW_AND_BOTH_CURRENT_DUPLICATE_CALL_SITES")
        a.require(history_counts["original_complete_admissions"]==1 and
            history_counts["duplicate_declarations_avoided"]>=1,"FIRST_COMPLETE_HISTORY_AND_CURRENT_DUPLICATE_REUSE")
        before=trace.summary(q)
        a.exact(before["read_bytes"],q.bytes_read,"EVERY_ORIGINAL_READ_COUNTED")
        restore();restore=None
        history_restore();history_restore=None
        a.require(history.admission is source_before,"ORIGINAL_HISTORY_ADMISSION_RESTORED")
        a.require(c.attempt.reviewed_failure is original,"PRIVATE_ORIGINAL_REVIEWER_RESTORED")
        q.finish();g.check(force=True)
        a.exact(trace.summary(q)["read_bytes"],q.bytes_read,"FINAL_FRESH_READS_COUNTED")
        out.update(state="PASS_CURRENT160_PRIVATE_HISTORY_AND_REVIEW_CODE43_WHOLE_BINDING_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=contracts,source_pins=pins+PINS+[q.snapshots[connection.TEST],q.snapshots[helper.TEST],q.snapshots[bundle.same_reader_history_declaration_once_v1.TEST]],
            namespace_AST_proofs=proof,connection_proof=connected,review_counts=dict(counts),history_admission_counts=dict(history_counts),
            binding_reads_before_final=before,all_reads_including_final=trace.summary(q),
            complete_scope_count=len(required),rust_source_count=len(rust),source_pairs=26,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            private_reviewer_restored=True,actual_DATA038_and_PREFLIGHT038_admitted=True,
            diagnostic_inputs_differ_from_actual_runtime_scope=True,
            shared720_runtime_completion_or_new_product_controller_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        if restore is not None:restore()
        if history_restore is not None:history_restore()
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
