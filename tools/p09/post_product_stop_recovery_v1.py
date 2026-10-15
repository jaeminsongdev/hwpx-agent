"""Read-only classification of one closed post-product resource failure.

This is NOT retry dispatch, a replacement byte boundary, or acceptance. A new
full run still needs a separately qualified admission/graph and original guards.
"""
import hashlib
import json
import math

SELF="tools/p09/post_product_stop_recovery_v1.py"
TEST="tools/p09/tests/test_post_product_stop_recovery_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
CANDIDATE=dict(path=PREFIX+"current-runtime-run007.v1.json",bytes=4199057,
    sha256="3271eb9b07cd0eb1462630bb0f61e7ca7894545ec67f0c516ea8d898391a0f6c")
CASE="actual_import::source_review_locations::actual_original_stored_locations_match_direct_graph_without_state_defaults_or_writes"
RESPONSE="복구 경로 설계·검증 진행"
CODE_STATE="PASS_POST_PRODUCT_STOP_REVIEW_CODE8_NOT_RUNTIME_RETRY_OR_ACCEPTANCE"


def require(ok,label):
    if not ok:raise ValueError("POST_PRODUCT_STOP_"+label)


def fields(row,expected):
    require(type(row) is dict,"OBJECT")
    require(all(type(row.get(k)) is type(v) and row[k]==v for k,v in expected.items()),"EXACT_FIELDS")


def validate_candidate(row):
    fields(row,dict(state="STOPPED_NOT_ACCEPTED",task="case165-current-r007-tests",
        selected_test_index=165,operation_phase="final_source_freeze",
        stop_reason="STOP_NATIVE_SOURCE_PRESSURE_NO_COOLING",exit_code=0,
        worker_created=True,job_assigned=True,writer_authorized=True,heavy_work_started=True,
        product_body_observed=True,actual_product_child_executed=True,
        actual_Cargo_SQL_Hangul_run=False,product_complete=False,
        Native_source_frame_qualified=False,current_generation_runtime_candidate_qualified=False,
        accepted_count_delta=0,separate_queue_epoch_acceptance_required=True,
        full249_current_qualified=False,signed16_current_qualified=False,
        P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",cleanup_confirmed=True,owned_tree_empty=True))
    fields(row["terminal_summary"],dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248))
    require(row["selected_test_names"]==row["passed_test_names"]==[CASE],"ONE_EXACT_PRODUCT_CASE")
    window=row["strict_product_window"]
    fields(window,dict(maximum_GO_to_complete_capture_seconds=15,actual_GO_writes=1,
        actual_capture_count=1,actual_complete_capture_within_window=True,stopped=False))
    elapsed=window["GO_to_complete_capture_elapsed_seconds"]
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<=15,"COMPLETE_PRODUCT_CAPTURE_WINDOW")
    frame=row["source_frame"]
    fields(frame,dict(frame_state="CLOSED",registered_live_frame=False,input_count=3056,
        input_bytes=228558382,serialized_pin_reused_as_live_handle=False,input_exclusions_added=False))
    handles=frame["handles"]
    fields(handles,dict(input_lock_handles_opened=3428,input_lock_handles_closed=3428,
        input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,
        active_reader_bindings=0,active_byte_streams=0,handle_close_failed_attempts=0,
        file_write_or_delete_operation_executed=False))
    fields(row["parent_live_raw_access_policy"],dict(active_scope=False,
        all_original_open_function_identities_restored=True))
    boundaries=frame["actual_byte_boundaries"]
    require(type(boundaries) is list and len(boundaries)==1,"EXACT_INCOMPLETE_TWO_BOUNDARY_RUN")
    before=boundaries[0];fields(before,dict(role="before"))
    pins=before["actual_byte_pins"]
    require(type(pins) is list and len(pins)==3056 and all(type(p) is dict
        and set(p)=={"path","bytes","sha256"} and type(p["path"]) is str and bool(p["path"])
        and type(p["bytes"]) is int and p["bytes"]>0 and type(p["sha256"]) is str
        and len(p["sha256"])==64 and all(c in "0123456789abcdef" for c in p["sha256"]) for p in pins),"COMPLETE_BEFORE_PINS")
    require(len({p["path"] for p in pins})==len(pins) and sum(p["bytes"] for p in pins)==228558382,"UNIQUE_COMPLETE_BEFORE_BYTES")
    fields(before["reader_diagnostics"],dict(read_passes=3056,bytes_read=228558382))
    return dict(classification="CLOSED_POST_PRODUCT_RESOURCE_FAILURE_NOT_ACCEPTED",
        original_candidate_remains_not_qualified=True,completed_byte_boundaries=["before"],
        after_boundary_missing=True,after_boundary_reconstructed=False,
        product_result_reusable_as_full_PASS=False,eligible_for_retry_design=True,
        next_physical_run=8,new_full_source_frame_and_two_byte_boundaries_required=True,
        original_CPU_RAM_lock_IO_GO_and_oracle_guards_required=True,
        accepted_count_delta=0,queue_advance_authorized=False,GO_authorized=False,
        runtime_retry_admission_implemented=False,next_Native_start_authorized=False)


def review(raw,response):
    require(type(response) is str and response==RESPONSE,"EXPLICIT_USER_DESIGN_AUTHORIZATION")
    require(type(raw) is bytes and len(raw)==CANDIDATE["bytes"]
        and hashlib.sha256(raw).hexdigest()==CANDIDATE["sha256"],"EXACT_IMMUTABLE_FAILED_CANDIDATE")
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,"NO_DUPLICATE_JSON_KEYS");result[key]=value
        return result
    row=json.loads(raw.decode("utf-8"),object_pairs_hook=unique,
        parse_constant=lambda value:require(False,"FINITE_JSON_NUMBERS"))
    return dict(validate_candidate(row),candidate_pin=dict(CANDIDATE),
        authorization=dict(source="explicit_user_reply_in_current_chat",response=response,scope="design_and_verify_only"))


def main():
    import argparse,io,re,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    active_policy=host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--code",action="store_true");mode.add_argument("--review",action="store_true")
    parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--code-attempt",type=int,default=1)
    parser.add_argument("--human-response")
    args=parser.parse_args();require(1<=args.attempt<=8 and 1<=args.code_attempt<=8,"BOUNDED_REVIEW_ATTEMPT")
    output=PREFIX+f"post-product-recovery-{'code' if args.code else 'review'}{args.attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_REVIEW_RECORD")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic()
    row=dict(state="FAILED_POST_PRODUCT_STOP_REVIEW_NOT_ADOPTED",accepted_count_delta=0,
        GO_authorized=False,next_Native_start_authorized=False,host_resource_policy=active_policy)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,host.CLOSURE_SOURCE):q.pin(name)
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename and Path(filename).absolute().is_relative_to(c.ROOT/"tools/p09"):
                q.pin(Path(filename).absolute().relative_to(c.ROOT).as_posix())
        if args.code:
            from tests import test_post_product_stop_recovery_v1 as tests
            tests.MODULE=sys.modules[__name__]
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            fields(row["contracts"],dict(run=8,errors=0,failures=0,skipped=0));state=CODE_STATE
        else:
            code=q.json(PREFIX+f"post-product-recovery-code{args.code_attempt:03}.v1.json")
            fields(code,dict(state=CODE_STATE,cleanup_confirmed=True,GO_authorized=False,next_Native_start_authorized=False))
            fields(code["contracts"],dict(run=8,errors=0,failures=0,skipped=0))
            require(type(code["fresh_inputs"]) is int and code["fresh_inputs"]==code["final_fresh_hashes"]>0,"CLOSED_CODE_HASHES")
            for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_REVIEW_CODE_SOURCES")
            raw=q.text(CANDIDATE["path"]).encode("utf-8")
            a.exact(q.snapshots[CANDIDATE["path"]],CANDIDATE,"EXACT_FAILED_RUN7")
            row.update(review(raw,args.human_response));state="PASS_READ_ONLY_POST_PRODUCT_FAILURE_CLASSIFICATION_NOT_RETRY_DISPATCH_OR_ACCEPTANCE"
        q.finish();guard.check(force=True)
        row.update(state=state,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"REVIEW_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","next_Native_start_authorized")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
