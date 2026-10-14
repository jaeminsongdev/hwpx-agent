"""Read-only whole successor review; no worker, Native replay or queue writer.

Expected sources are derived from approved predecessor and sealed declarations
before reading the candidate. Reviewer code is not retroactive Native input.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

SELF="tools/p09/review_current_queue_successor.py"
TEST="tools/p09/tests/test_review_current_queue_successor.py"


def connect_prepare(legacy,checker,identity,step,raw):
    """Keep the entire frozen prepare projection, changing dependencies only."""
    original=legacy.source.prepare_projection(raw)
    env=original.__globals__
    env.update(validate_candidate=checker.validate_candidate,root_path=identity.root_path,
        r=NS(**{**vars(env["r"]),"CONFIG":step,"context":checker.environment["context"]}))
    return original


def prepare(q,ctx,qualification,old,a,runtime,scope,bytes_policy,dispatch,oracle,root_pin):
    dispatch.admit(q,ctx,a,qualification);dispatch.previous_stops(q,ctx,a)
    name=f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{ctx.run:03}.v1.json"
    report=q.json(name)
    hint=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-worker-bootstrap{ctx.run:03}.v1.json")
    pin,wire=q._read(report["capsule_pin"]["path"],parse=True);q._bind(pin["path"],pin)
    a.exact(pin,report["capsule_pin"],"REVIEW_EXACT_DECLARED_WIRE")
    graph,proof=runtime.reconstruct_worker_graph(q.root,old.old.namespace_bundle,scope,bytes_policy,hint,bytes(wire),q.checkpoint)
    step=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-step-config001.v1.json")
    a.exact(step,hint["step"],"REVIEW_SAME_CURRENT_STEP")
    a.exact(step,report["step"],"REVIEW_SAME_CURRENT_GRAPH_STEP")
    old.old.base.configure(ctx.index)
    template,identity,proof=runtime.connect_factory(q.root,old.old.namespace_bundle,old.old.prior,ctx.index,ctx.run,q.checkpoint)
    declared=dict(q.snapshots)
    expected,rust=runtime.current_input_scope(q,graph,step,q.snapshots[name],report["manifest_pin"],declared)
    expected=scope.extend(expected,q.snapshots)
    expected,aliases=graph.binding.semantic_union(expected,q.checkpoint)
    checker,proof=oracle.connect(old.CURRENT,graph,old.old.base.CONFIG,identity,expected,q.checkpoint)
    frozen=old.CURRENT.API.prepare.__globals__["predecessor"]._api_env["source"].prior.accepted.original
    raw=q.text(frozen.SELF).encode("utf-8")
    a.exact(q.snapshots[frozen.SELF],expected[frozen.SELF],"REVIEW_EXACT_ORIGINAL_FROZEN_PREPARE_SOURCE")
    # The independent scope is closed before the candidate is read by prepare.
    execute=connect_prepare(old.CURRENT,checker,identity,old.old.base.CONFIG,raw)
    row,listing,evidence,full_proof=execute(q,root_pin)
    a.fields(row,dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
        selected_test_index=ctx.index,task=f"case{ctx.index}-current-r{ctx.run:03}-tests",
        Native_source_frame_qualified=True,current_generation_runtime_candidate_qualified=True,
        cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"REVIEW_ACTUAL_NATIVE_PRODUCT_NOT_GATE")
    a.fields(row["source_frame"],dict(frame_state="COMMITTED",registered_live_frame=False),"REVIEW_COMMITTED_FRAME")
    a.require(len(row["source_frame"]["actual_byte_boundaries"])==2,"REVIEW_BOTH_ACTUAL_NATIVE_BYTE_BOUNDARIES")
    a.require(checker.projectors,"REVIEW_ACTUAL_WHOLE_CHECKER_NOT_ONLY_CONNECTION")
    return row,listing,evidence,dict(full_proof,successor_independent_scope_proof=proof,
        whole_frozen_prepare_retained=True,expected_scope_not_current_candidate_observations=True,
        product_or_Native_reexecuted=False,queue_acceptance_called=False)


def main(ctx,root_pin,attempt):
    import io,json,os,re,time,unittest
    from unittest.mock import patch
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import current_queue_successor_dispatch as dispatch
    import current_queue_successor_oracle as oracle
    import flat_current_queue_envelope_runtime_v25 as envelope
    namespaces,proof=envelope.namespace_bundle.load(c.ROOT,[dispatch.ORIGINAL_CONTROLLER_PIN],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    old=namespaces.case160_run007_controller
    a.require(type(attempt) is int and 1<=attempt<=8,"REVIEW_CLOSED_ATTEMPT")
    a.exact(root_pin["path"],ctx.root,"REVIEW_EXACT_CURRENT_ROOT")
    scope.pins([root_pin])
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-whole-review-run{ctx.run:03}-attempt{attempt:03}.v1.json"
    a.require(not output.exists(),"EXCLUSIVE_WHOLE_REVIEW")
    guards=old.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();q=None
    out=dict(state="FAILED_SUCCESSOR_WHOLE_REVIEW_NOT_ACCEPTED",index=ctx.index,physical_run=ctx.run,
        accepted_count_delta=0,product_or_Native_reexecuted=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        guard.acquire();source_reader=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST):source_reader.pin(name)
        a.exact(source_reader.pin(ctx.root),root_pin,"REVIEW_CURRENT_ROOT_BYTES_BEFORE_CHECKER")
        q=a.AcceptanceReader(c.ROOT,guard.check)
        qualification=q.json(ctx.qualification)
        runtime,controller,proof=dispatch.current_namespaces(q,ctx,a,old,scope,bytes_policy,qualification)
        suite=unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_review_current_queue_successor")
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        out["contracts"]=contracts
        a.exact(contracts,dict(run=2,errors=0,failures=0,skipped=0),"REVIEW_ALL_WRAPPER_CONTRACTS")
        with patch("subprocess.Popen",side_effect=AssertionError("REVIEW_NO_CHILD")),patch("subprocess.run",side_effect=AssertionError("REVIEW_NO_CHILD")):
            row,listing,evidence,proof=prepare(q,ctx,qualification,old,a,runtime,scope,bytes_policy,dispatch,oracle,root_pin)
        q.finish();source_reader.finish();guard.check(force=True)
        out.update(state="PASS_SUCCESSOR_INDEPENDENT_WHOLE_REVIEW_NOT_QUEUE_OR_GATE",runtime_pin=root_pin,
            original_frozen_prepare_and_entire_product_oracle_proof=proof,
            fresh_input_pins=list(q.snapshots.values()),reviewer_source_pins=list(source_reader.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_read_passes=q.read_passes,actual_bytes_read=q.bytes_read,
            reviewer_not_retroactive_Native_input=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
        frames=[];tb=error.__traceback__
        while tb is not None:
            frames.append(dict(file=Path(tb.tb_frame.f_code.co_filename).name,function=tb.tb_frame.f_code.co_name,line=tb.tb_lineno));tb=tb.tb_next
        out["failure_frames"]=frames[-12:]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"WHOLE_REVIEW_CLEANUP")
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=2*1048576,"BOUNDED_WHOLE_REVIEW_REPORT")
    for parent in (output.parent,*output.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_REVIEW_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:a.exact(stream.write(raw),len(raw),"ALL_REVIEW_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","elapsed_seconds",
        "CPU_max","RAM_min","cleanup_confirmed","error_code","error_type","failure_frames")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":
    import argparse
    import current_queue_successor_dispatch as dispatch
    parser=argparse.ArgumentParser()
    for name in ("case","run","code-attempt","preflight-attempt","qualification-attempt","review-attempt","root-bytes"):
        parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--root-sha256",required=True)
    args=parser.parse_args()
    ctx=dispatch.context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt)
    raise SystemExit(main(ctx,dict(path=ctx.root,bytes=args.root_bytes,sha256=args.root_sha256),args.review_attempt))
