"""Next current queue epoch using exact qualified112 engine definitions.

Only case/cursor/schema/path metadata is projected. Original Native/byte/GO/
Job/resource/cleanup statements are unchanged and their AST shape is checked.
No112 replay, compilation, SQL, Hangul, threshold/deadline relaxation or retry.
An immutable candidate must receive a separate distinct queue acceptance.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace as NS

import run_case112_current_stored as prior
import accept_case112_current_epoch as accepted112

c=prior.c
scope=prior.scope
native=prior.native
SELF="tools/p09/run_current_queue_native.py"
TEST="tools/p09/tests/test_current_queue_native.py"
INDEX=113
BEFORE=106
CASE="actual_import::policy_product::original_strict_envelope_rejects_injected_maps_policies_artifacts_approval_and_stale_scope"
PRIOR_ACCEPT_PIN=dict(path=accepted112.OUTPUT,bytes=272872,
    sha256="97b3df87038e5299a2bf824e82f1e91d0cbc25a505d7212f527aeafdc665c28b")
TEMPLATE_PIN=next(p for p in accepted112.CODE_PINS if p["path"]==prior.SELF)
SCHEMA="hwpx-agent.p09-current-queue-native-runtime-candidate/v1"
PASS="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE"
MARKER_ARGS=["current-queue-case113-runtime-only"]
TARGET=prior.TARGET


def require(ok,code):
    if not ok:raise ValueError("CURRENT_QUEUE_NATIVE_"+code)


def task_for(run):
    require(type(run) is int and 1<=run<=999,"RUN_RANGE")
    return f"case113-current-r{run:03}-tests"


def run_for(task):
    require(type(task) is str and re.fullmatch("case113-current-r[0-9]{3}-tests",task),"EXACT_TASK")
    run=int(task[-9:-6]);require(task_for(run)==task,"TASK_RUN");return run


def arguments():
    return [CASE,"--exact","--test-threads=1","--format=pretty","--color=never"]


def projection(source):
    """Closed, counted literal projection; safety/control flow is NOT rewritten."""
    require(type(source) is bytes and len(source)==TEMPLATE_PIN["bytes"]
        and hashlib.sha256(source).hexdigest()==TEMPLATE_PIN["sha256"],"QUALIFIED_TEMPLATE_BYTES")
    tree=ast.parse(source.decode("utf-8"));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)
        and n.name in ("run_owned","worker","terminal_api")]
    require(len(nodes)==3 and {n.name for n in nodes}=={"run_owned","worker","terminal_api"},"EXACT_ENGINE_DEFINITIONS")
    counts={"index":0,"before":0,"path":0,"schema":0}
    originals=[ast.dump(n,include_attributes=False) for n in nodes]
    class Project(ast.NodeTransformer):
        def visit_Constant(self,node):
            value=node.value
            if type(value) is int and value==112:
                counts["index"]+=1;node.value=INDEX
            elif type(value) is int and value==105:
                counts["before"]+=1;node.value=BEFORE
            elif value=="implementation/p09/evidence/p09-361-case112-current-runtime-run":
                counts["path"]+=1;node.value="implementation/p09/evidence/p09-361-case113-current-runtime-run"
            elif value=="hwpx-agent.p09-case112-current-native-runtime-candidate/v1":
                counts["schema"]+=1;node.value=SCHEMA
            return node
    projected=Project().visit(ast.Module(body=nodes,type_ignores=[]))
    require(counts==dict(index=3,before=1,path=1,schema=1),"CLOSED_LITERAL_PROJECTION_COUNTS")
    # Independently undo ONLY the exact changed constants. Every other AST node
    # must equal the original exact definition, including original safety logic.
    import copy
    class Undo(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is int and node.value==INDEX:node.value=112
            elif type(node.value) is int and node.value==BEFORE:node.value=105
            elif node.value=="implementation/p09/evidence/p09-361-case113-current-runtime-run":
                node.value="implementation/p09/evidence/p09-361-case112-current-runtime-run"
            elif node.value==SCHEMA:node.value="hwpx-agent.p09-case112-current-native-runtime-candidate/v1"
            return node
    restored=Undo().visit(copy.deepcopy(projected))
    require([ast.dump(n,include_attributes=False) for n in restored.body]==originals,"ORIGINAL_ALL_ENGINE_STATEMENTS_RETAINED")
    namespace=dict(prior.__dict__)
    namespace.update(SELF=SELF,TEST=TEST,PASS=PASS,FRESH_PIN=PRIOR_ACCEPT_PIN,MARKER_ARGS=MARKER_ARGS,
        task_for=task_for,run_for=run_for,arguments=arguments,binding=binding,
        scope=NS(**{**vars(scope),"CASE112":CASE}),require=require)
    exec(compile(ast.fix_missing_locations(projected),TEMPLATE_PIN["path"],"exec"),namespace)
    return NS(**{n.name:namespace[n.name] for n in nodes}),dict(metadata_only_literals=counts,
        original_engine_AST_restored_exactly=True,qualified_template_pin=TEMPLATE_PIN,
        Native_byte_GO_Job_resource_cleanup_statements_replaced=False)


def template():
    path=c.ROOT/TEMPLATE_PIN["path"]
    prior.build.direct_path(path,file_required=True)
    # Single23KiB bounded bootstrap read; original source pin is freshly checked
    # again inside the actual c.run before/after1710+ union's Native frame.
    require(path.stat().st_size==TEMPLATE_PIN["bytes"],"TEMPLATE_SIZE")
    with path.open("rb") as stream:raw=stream.read(TEMPLATE_PIN["bytes"]+1)
    return projection(raw)


def binding(q):
    parent=accepted112.read_exact(q,PRIOR_ACCEPT_PIN)
    accepted112.fields(parent,dict(schema_version="hwpx-agent.p09-case112-current-epoch-acceptance/v1",
        state=accepted112.PASS,accepted_count_before=105,accepted_count_delta=1,accepted_count_after=BEFORE,
        runtime_remaining_individual_cases=143,next_runtime_index=INDEX,
        runtime_candidate_pin=accepted112.ROOT_PIN,accepted_test_indices=[112],accepted_test_names=[scope.CASE112],
        prior105_historical_epochs_preserved=True,prior105_current_generation_rebased=False,
        accepted_current_generation_case_count=1,resource_cleanup_confirmed=True,
        product_child_executed=False,Native_frame_reexecuted=False,
        full249_current_qualified=False,signed16_current_qualified=False,P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN"),
        "IMMUTABLE_PRIOR106")
    prior_row=accepted112.read_exact(q,accepted112.ROOT_PIN)
    listing=accepted112.read_exact(q,scope.LIST_PIN)
    body=accepted112.read_exact(q,accepted112.BODY_PIN)
    fresh=prior.packed.unpack(accepted112.read_exact(q,accepted112.FRESH_PIN),q.checkpoint)
    accepted112.validate(prior_row,listing,body,fresh,q.checkpoint)
    current=scope.listing_inputs(listing)
    require(listing["source_test_names"][INDEX-1]==CASE and CASE!=scope.CASE112,"EXACT_NEXT113_NOT_REPLAY112")
    required=scope.pins(prior_row["source_freeze"],1710)
    previous_fresh=scope.pins(parent["fresh_input_pins"],823)
    accepted112.fields(parent,dict(final_fresh_hashes=823,fresh_read_passes=1646),"PRIOR_TWO_FRESH_PASSES")
    require(parent["fresh_bytes_read"]==2*sum(p["bytes"] for p in previous_fresh.values()),"PRIOR_ALL_FRESH_BYTES")
    for pin in accepted112.CODE_PINS:
        accepted112.exact(q.pin(pin["path"]),pin,"PRESERVED_QUALIFIED112_CODE")
    for name in (accepted112.SELF,accepted112.TEST):
        accepted112.exact(q.pin(name),previous_fresh[name],"PRESERVED_QUALIFIED_ACCEPT112_CODE")
    require(required[scope.EXE_PIN["path"]]==scope.EXE_PIN,"SAME_CURRENT_COMPILED_EXE")
    rust={n for n in current if n.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
    require(len(rust)==787,"WHOLE_CURRENT_RUST787")
    return required,rust


def worker(task):
    engine,_=template();return engine.worker(task)


def binding_attempt(q,run):
    # 이전 성공 body를 새 run 번호로 반복하지 않는다. 불완전/빈 receipt는
    # product 미실행 증거가 아니므로 별도 검토 전에는 자동 retry를 거부한다.
    for previous in range(1,run):
        name=f"implementation/p09/evidence/p09-361-case113-current-runtime-run{previous:03}.v1.json"
        row=q.json(name)
        require(row.get("product_body_observed") is False and row.get("passed_test_names")==[]
            and row.get("current_generation_runtime_candidate_qualified") is False
            and row.get("cleanup_confirmed") is True and row.get("owned_tree_empty") is True,
            "PREVIOUS_PASSED_OR_UNRESOLVED_BODY_NOT_REPLAYED")
    return binding(q)


def run_owned(run):
    engine,_=template()
    task_for(run)
    engine.run_owned.__globals__["binding"]=lambda q:binding_attempt(q,run)
    # The original engine owns the sole live observer, worker GO, Job and frame.
    # It writes an immutable candidate, NOT a queue advance.
    return engine.run_owned(run)


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run",type=int,required=True)
    return run_owned(parser.parse_args().run)


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_CURRENT_QUEUE_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)),file=sys.stderr,flush=True)
        raise SystemExit(2) from None
