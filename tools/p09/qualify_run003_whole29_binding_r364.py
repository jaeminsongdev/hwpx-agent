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
SELF="tools/p09/qualify_run003_whole29_binding_r364.py"
PINS=[dict(path="tools/p09/flat_current_queue_envelope_runtime_v30.py",bytes=13368,
    sha256="68299c21e702a49afe82986c66ddfd18422ac2225159425da8c4b956cd1adb4b"),
    dict(path="tools/p09/same_reader_failure_review_once_v1.py",bytes=3180,
    sha256="f9a962fb97db785c22c419640bfb79c4f5a3ded293db141a4b325481328516ab"),
    dict(path="tools/p09/failure_review_current_connection_v1.py",bytes=2958,
    sha256="9250a1a15ec80d71b43f2c3ecc6f95a19858c01f9be22b5c77f40db2c13914e7")]

PINS.append(dict(path="tools/p09/same_reader_history_declaration_once_v1.py",bytes=2461,sha256="5bf2309acbedfe130b7de8225997cc78c640588e757b5bc79e12c36d3eaea3cf"))

NEW_PINS=[{"path":"tools/p09/runtime_successor_manifest_v6.py","bytes":3311,"sha256":"2e188f844e93555bfdfdd5601d34c1058f37b07d7ea4ed017041a67b5cb4bf4b"},{"path":"tools/p09/runtime_successor_worker_capsule_v5.py","bytes":1047,"sha256":"d4b09e41683d02f6165bbb62aa47a03cea845b69950baf6505d139a36f951479"},{"path":"tools/p09/successor_runtime_graph_v5.py","bytes":1097,"sha256":"70eceb2cbc86f1a6f621ea2491747eac5466ff153eac21435d565bca0b316fe9"},{"path":"tools/p09/successor_bounded_graph_bootstrap_v5.py","bytes":2392,"sha256":"4e80486c209c6d5138e52fe600e28fd49b17fc311356faf12fcf2c3f477b0673"},{"path":"tools/p09/successor_current_binding_v5.py","bytes":1118,"sha256":"d04454c473544157a9aa4a70c66e639e43d4d06466a36481b8014fff91f29b6b"}]

def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    restore=None;history_restore=None;q=None
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
        m.own_inputs(q)
        reuse={**vars(c.NEXT),"flat_current_queue_envelope_runtime_v25":old}
        nxt,new_proof=old.namespace_bundle.load(a.c.ROOT,NEW_PINS,reuse)
        for pin in NEW_PINS:a.exact(q.pin(pin["path"]),pin,"ALL_NEW_RUN003_BINDING_SOURCES")
        required,rust,fresh,live,whole=nxt.successor_current_binding_v5.bind(q,c.PRIOR160.PRIOR160.PRIOR159)
        graph,bootstrap_proof=nxt.successor_bounded_graph_bootstrap_v5.load(m.old,q.checkpoint)
        a.exact(live.descriptors(),graph.binding.descriptors(),"WHOLE_AND_BOUNDED_ACTUAL29_DESCRIPTORS")
        a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"ACTUAL_MANIFEST028_SAME_PIN")
        cost=live.runtime_budget(required,167,m.prior.DIRECT.runtime_budget,q.checkpoint)
        a.require(len(graph.binding.descriptors())==29 and len(rust)==787,"WHOLE_CURRENT26_BINDING_RUST787")
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
        out.update(state="PASS_RUN003_WHOLE29_BINDING_CODE43_BOUNDED21_AND_ORIGINAL600_COST_NOT_CONTROLLER_OR_GO",
            contracts=contracts,source_pins=pins+PINS+NEW_PINS+[q.snapshots[connection.TEST],q.snapshots[helper.TEST],q.snapshots[bundle.same_reader_history_declaration_once_v1.TEST]],
            namespace_AST_proofs=proof+new_proof,bounded_bootstrap=bootstrap_proof,
            complete_scope_cost=cost,whole_original_binding_proof=whole,connection_proof=connected,review_counts=dict(counts),history_admission_counts=dict(history_counts),
            binding_reads_before_final=before,all_reads_including_final=trace.summary(q),
            complete_scope_count=len(required),rust_source_count=len(rust),source_pairs=29,
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
        restoration_errors=[]
        for callback in (restore,history_restore):
            if callback is not None:
                try:callback()
                except (ValueError,AttributeError,TypeError) as error:
                    restoration_errors.append(type(error).__name__)
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None),
            private_restoration_errors=restoration_errors,
            partial_completed_read_summary=trace.summary(q) if q is not None else None)
        if restoration_errors:out["state"]="FAILED_PRIVATE_RESTORATION_NOT_ACCEPTED"
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
