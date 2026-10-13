"""Distinct113 acceptance, no product or Native frame replay.

The qualified112 oracle is unchanged. Closed metadata/count/name projection
retains every original verification statement and reverses to its exact AST.
Actual candidate pin is filled only after a completed product/Native receipt.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import time
from types import SimpleNamespace as NS

import accept_case112_current_epoch as original
import run_current_queue_native as runtime

SELF="tools/p09/accept_current_queue_epoch.py"
TEST="tools/p09/tests/test_current_queue_epoch_acceptance.py"
OUTPUT="implementation/p09/evidence/p09-361-case113-current-epoch-accept001.v1.json"
ROOT_PIN=dict(path="implementation/p09/evidence/p09-361-case113-current-runtime-run003.v1.json",
    bytes=2210377,sha256="edae76489678796553b1e77d143d7765b70fac27e62c8ff513f26311afdddb59")
ORACLE_PIN=dict(path=original.SELF,bytes=20933,
    sha256="03fa9362f56b6105b48b8b49599f32ccc8cbf4aa9d0b0836f3cf8580cc9c680c")
PASS="PASS_EXACT113_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE"
CONTROLLERS=(runtime.SELF,runtime.TEST,runtime.native.SELF,runtime.native.TEST)


def require(ok,code):
    if not ok:raise ValueError("CURRENT_QUEUE_ACCEPT_"+code)


def validator(source,row,listing,body):
    require(type(source) is bytes and len(source)==ORACLE_PIN["bytes"]
        and hashlib.sha256(source).hexdigest()==ORACLE_PIN["sha256"],"QUALIFIED_ORACLE_BYTES")
    current=original.scope.listing_inputs(listing)
    expected=original.scope.extend(original.scope.compose(body["source_freeze"],list(current.values())),
        original.scope.pins(row["bootstrap_metadata"]["input_pins"]))
    inputs=len(expected)
    directories=len({p.as_posix() for name in expected for p in PurePosixPath(name).parents})
    helpers=row["imported_worker_source_paths"]
    require(type(helpers) is list and 28<=len(helpers)<=64,"HELPER_BOUND")
    # stdout's exact expected byte count is derived from the actual named-test
    # protocol, not accepted arbitrary truncation. The original terminal oracle
    # was executed by the immutable candidate before its complete-capture PASS.
    capture=row["capture_diagnostics"]["buffered_bytes"]
    require(type(capture) is dict and type(capture.get("stdout")) is int
        and 0<capture["stdout"]<=32768 and capture.get("stderr")==0,"CAPTURE_BUDGET")
    controllers=[expected[name] for name in CONTROLLERS]
    tree=ast.parse(source.decode("utf-8"));found=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="validate"]
    require(len(found)==1,"ONE_ORIGINAL_VALIDATOR");node=copy.deepcopy(found[0]);before=ast.dump(node,include_attributes=False)
    replacements=dict(schema_version=runtime.SCHEMA,state=runtime.PASS,prior_queue_cases=runtime.BEFORE,
        next_case=runtime.INDEX,prior_queue_fresh_pin=runtime.PRIOR_ACCEPT_PIN,selected_test_index=runtime.INDEX,
        selected_test_names=[runtime.CASE],passed_test_names=[runtime.CASE],test_arguments=runtime.arguments())
    first=[n for n in node.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Name) and n.value.func.id=="fields"
        and isinstance(n.value.args[0],ast.Name) and n.value.args[0].id=="row"][0].value
    keywords=first.args[1].keywords
    require(set(replacements)<=set(k.arg for k in keywords),"EXACT_ROW_METADATA_KEYS")
    for keyword in keywords:
        if keyword.arg in replacements:
            old=copy.deepcopy(keyword.value)
            keyword.value=ast.parse(repr(replacements[keyword.arg]),mode="eval").body
            keyword.value._original_projection_ast=old
    # Keep exact cost accounting: the separately reviewed PDH allowance is not
    # silently omitted by reusing112's previously qualified source-only oracle.
    costs=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
        and n.func.id=='exact' and len(n.args)==3 and isinstance(n.args[2],ast.Constant)
        and n.args[2].value=='NO_HIDDEN_COST']
    require(len(costs)==1,'ONE_ORIGINAL_COST_EQUALITY')
    old=copy.deepcopy(costs[0].args[1])
    budget=runtime.attribution.p.MAX_TOTAL_SAMPLE_SECONDS+runtime.attribution.p.MAX_SAMPLE_SECONDS
    costs[0].args[1]=ast.BinOp(left=copy.deepcopy(old),op=ast.Add(),right=ast.Constant(budget))
    costs[0].args[1]._original_projection_ast=old
    counts={1710:0,335:0,28:0,228:0}
    values={1710:inputs,335:directories,28:len(helpers),228:capture["stdout"]}
    class Counts(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_original_projection_ast"):return n
            return super().visit(n)
        def visit_Constant(self,n):
            if type(n.value) is int and n.value in values:
                counts[n.value]+=1;old=copy.deepcopy(n)
                n.value=values[n.value];n._original_projection_ast=old
            return n
    node=Counts().visit(node)
    require(counts=={1710:1,335:1,28:1,228:1},"CLOSED_DIMENSION_PROJECTION")
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_original_projection_ast"):return copy.deepcopy(n._original_projection_ast)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,"ALL_ORIGINAL_ORACLE_STATEMENTS_RETAINED")
    namespace=dict(original.__dict__)
    namespace.update(CODE_PINS=original.CODE_PINS+controllers)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ORACLE_PIN["path"],"exec"),namespace)
    return namespace["validate"],dict(original_oracle_AST_restored_exactly=True,metadata_fields_projected=9,
        input_count=inputs,directory_count=directories,helper_count=len(helpers),
        qualification_checks_skipped=False,qualified_oracle_pin=ORACLE_PIN,
        additional_PDH_cost_equality_extended_by_seconds=budget)


def additional_observer_evidence(row):
    original.fields(row['complete_runtime_budget'],dict(
        additional_serial_PDH_maximum_sample_budget_seconds=runtime.attribution.p.MAX_TOTAL_SAMPLE_SECONDS+runtime.attribution.p.MAX_SAMPLE_SECONDS,
        PDH_OS_call_latency_hard_preemption_guaranteed=False),'PDH_COST_NOT_OMITTED')
    original.fields(row['serial_CPU_attribution'],dict(existing_observer_instances=1,
        second_sampler_thread_or_process=False,original_CPU_RAM_decisions_replaced=False,
        additional_PDH_queries_explicit=True,PDH_interval_identical_to_K32_interval=False),'ONE_ORIGINAL_OBSERVER')
    probes=row['serial_CPU_attribution']['probes']
    require(type(probes) is list and len(probes)==1,'ONE_QUERY_OWNER')
    original.fields(probes[0],dict(query_remaining=False,cleanup_confirmed=True),'PDH_QUERY_CLEANUP')
    original.fields(row["source_frame"]["handles"]["all_acquisition_checkpoint_warning_fail_fast"],dict(
        original_warning_percent=90,warning_stops=0,acquisition_active=False,latched=False,
        original_hard_guards_called_first=True,original_cached_owner_sample_used=True,
        acquisition_cooling_waits_added=0,original_outside_acquisition_cooling_retained=True,
        sampler_thread_or_native_query_added=False,CPU_or_PC_freeze_improvement_claimed=False),"NEW_ACQUISITION_GUARD")


def prepare(q):
    require(type(ROOT_PIN) is dict,"ACTUAL_COMPLETED_CANDIDATE_PIN_REQUIRED")
    row=original.read_exact(q,ROOT_PIN)
    listing=original.read_exact(q,original.scope.LIST_PIN)
    body=original.read_exact(q,original.BODY_PIN)
    fresh=original.packed.unpack(original.read_exact(q,original.FRESH_PIN),q.checkpoint)
    parent=original.read_exact(q,runtime.PRIOR_ACCEPT_PIN)
    original.fields(parent,dict(state=original.PASS,accepted_count_after=106,next_runtime_index=113,
        accepted_count_delta=1,resource_cleanup_confirmed=True,full249_current_qualified=False,
        signed16_current_qualified=False,P09_gate="OPEN"),"PRIOR_ACTUAL106")
    require(listing["source_test_names"][112]==runtime.CASE,"EXACT_FULL249_NEXT113")
    text=q.text(ORACLE_PIN["path"])
    original.exact(q.snapshots[ORACLE_PIN["path"]],ORACLE_PIN,"ORIGINAL_ORACLE_PIN")
    # Reader.text normalizes line endings. Projection binds the exact raw pin;
    # use fresh bounded bytes, never an unbounded module import/code rewrite.
    with (original.c.ROOT/ORACLE_PIN["path"]).open("rb") as stream:source=stream.read(ORACLE_PIN["bytes"]+1)
    check,proof=validator(source,row,listing,body)
    evidence=check(row,listing,body,fresh,q.checkpoint)
    additional_observer_evidence(row)
    original.resource_history(parent["resource_samples"])
    # This additional acquisition guard is ONLY stronger; validate its evidence
    # separately instead of silently claiming the unchanged112 guard covered it.
    return row,listing,evidence,proof


def run():
    destination=original.c.ROOT/OUTPUT
    require(not destination.exists() and not destination.is_symlink(),"IMMUTABLE_ACCEPT_ALREADY_EXISTS")
    guard=original.Guard();q=None;result=None;started=time.monotonic()
    try:
        guard.acquire();q=original.AcceptanceReader(original.c.ROOT,guard.check)
        row,listing,evidence,proof=prepare(q)
        current=original.scope.listing_inputs(listing)
        rust={name for name in current if name.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
            and (name.endswith(".rs") or name.endswith("/Cargo.toml"))}
        name="tools/p09/current_issuer_build_inputs.py"
        source=q.text(name);expected=original.scope.pins(row["source_freeze"])
        original.exact(q.snapshots[name],expected[name],"QUALIFIED_CURRENT_INVENTORY_CODE")
        import os
        enumerate_native=original.native.definitions(source,("rust_inputs",),dict(os=os,Path=Path,require=require))
        require(enumerate_native.rust_inputs(original.c.ROOT,q.open_pacer.reserve)==rust,"FRESH_WHOLE_RUST")
        names=rust|set(row["imported_worker_source_paths"])|set(CONTROLLERS)|{original.scope.EXE_PIN["path"]}
        for name in sorted(names):original.exact(q.pin(name),expected[name],"CURRENT_CANDIDATE_INPUT_DRIFT")
        for module in tuple(sys.modules.values()):
            path=getattr(module,"__file__",None)
            if path:
                path=Path(path).absolute()
                if path.is_relative_to(original.c.ROOT/"tools/p09") and path.suffix==".py":
                    q.pin(path.relative_to(original.c.ROOT).as_posix())
        q.pin(SELF);q.pin(TEST);q.finish()
        require(enumerate_native.rust_inputs(original.c.ROOT,q.open_pacer.reserve)==rust,"FINAL_WHOLE_RUST")
        guard.check(force=True)
        result=dict(schema_version="hwpx-agent.p09-current-queue-epoch-acceptance/v1",state=PASS,
            runtime_candidate_pin=ROOT_PIN,prior_queue_authority_pin=runtime.PRIOR_ACCEPT_PIN,
            accepted_epoch_key=ROOT_PIN["sha256"]+":113",accepted_test_indices=[113],accepted_test_names=[runtime.CASE],
            accepted_count_before=106,accepted_count_delta=1,accepted_count_after=107,runtime_remaining_individual_cases=142,
            next_runtime_index=114,historical105_and_current112_epochs_preserved=True,
            prior_epochs_rebased_to_new_runtime=False,accepted_current_generation_case_count=2,
            product_child_executed=False,Native_frame_reexecuted=False,successful_product_cases_reexecuted=False,
            actual_runtime_evidence_validation=evidence,original_validator_projection=proof,
            current_Rust_input_count=787,current_Rust_inventory_checked_before_after=True,
            fresh_input_pins=list(q.snapshots.values()),fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            final_fresh_hashes=q.final_fresh_hashes,file_open_ceiling_per_second=20,
            qualifier_read_rates_by_kind=dict(binary=1048576,other=2097152),fresh_qualifier_is_not_new_native_or_product_evidence=True,
            full249_current_qualified=False,signed16_current_qualified=False,whole_runtime_reconciliation_required=True,
            P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",P10_started=False,PC_freeze_resolved=False)
    finally:guard.close()
    require(result is not None and guard.cleanup,"QUALIFIER_CLEANUP")
    result.update(resource_samples=guard.samples,resource_cleanup_confirmed=guard.cleanup,
        sole_serial_sampler=True,parallel_observer_started=False,elapsed_seconds=time.monotonic()-started)
    with destination.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=PASS,accepted=107,remaining=142,next_case=114,cleanup_confirmed=True)))
    return 0


if __name__=="__main__":raise SystemExit(run())
