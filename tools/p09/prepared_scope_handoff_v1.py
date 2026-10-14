"""Reconstruct an exact prepared declaration without granting runtime admission.

전체 준비 결과와 현재 명시적 입력·Rust 집합·manifest를 일치시킨다.
이 함수는 Native frame을 열거나 GO를 허용하지 않는다. 실제 연결에는
반환 scope 전체와 checkpoint 원본의 두 Native 바이트 경계가 필요하다.
"""
import prepared_input_checkpoint_v1 as prepared

SELF="tools/p09/prepared_scope_handoff_v1.py"
TEST="tools/p09/tests/test_prepared_scope_handoff_v1.py"
CURRENT_KEYS=frozenset(("data_pin","preflight_pin","authority_pin","prior_runtime_pin"))
MAX_CHECKPOINT_BYTES=4*1024*1024

def same(actual,expected):
    if type(actual) is not type(expected):return False
    if type(expected) is dict:
        return set(actual)==set(expected) and all(same(actual[k],v) for k,v in expected.items())
    if type(expected) in (list,tuple):
        return len(actual)==len(expected) and all(same(x,y) for x,y in zip(actual,expected))
    return actual==expected

def require(ok,code):
    if not ok:raise ValueError("PREPARED_SCOPE_HANDOFF_"+code)

def pins(rows):
    require(type(rows) is list and 0<len(rows)<=4096,"BOUNDED_PIN_LIST")
    result={}
    for value in rows:
        value=prepared.pin(value);name=value["path"]
        require(name not in result,"NO_DUPLICATE_PIN_PATH")
        result[name]=value
    return result

def rust_inputs(scope):
    return frozenset(n for n in scope if n.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (n.endswith(".rs") or n.endswith("/Cargo.toml")))

def load(q,checkpoint_pin,binding,*,expected_context,expected_current_pins,expected_rust,expected_source_paths):
    checkpoint_pin=prepared.pin(checkpoint_pin)
    require(checkpoint_pin["bytes"]<=MAX_CHECKPOINT_BYTES,"BOUNDED_CHECKPOINT_BYTES")
    require(type(expected_context) is dict and expected_context==dict(index=160,before=153,physical_product_run=3),
        "EXACT_CURRENT_PREPARATION_CONTEXT")
    require(type(expected_current_pins) is dict and set(expected_current_pins)==CURRENT_KEYS,"CLOSED_CURRENT_PINS")
    for value in expected_current_pins.values():prepared.pin(value)
    require(type(expected_rust) is frozenset and 0<len(expected_rust)<=4096,"EXPLICIT_RUST_SET")
    require(type(expected_source_paths) is frozenset and 0<len(expected_source_paths)<=16
        and all(type(n) is str and n for n in expected_source_paths),"EXPLICIT_PRODUCER_SOURCES")
    row=q.json(checkpoint_pin["path"])
    require(q.snapshots.get(checkpoint_pin["path"])==checkpoint_pin,"ACTUAL_CHECKPOINT_BYTE_PIN")
    require(type(row) is dict and row.get("state")=="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO"
        and row.get("cleanup_confirmed") is True,"COMPLETED_PREPARATION_NOT_STOP")
    for key in ("Native_or_product_executed","GO_authorized","queue_advance_authorized","product_entrypoint_called"):
        require(row.get(key) is False,"NO_EXISTING_PRODUCT_OR_GO_CLAIM")
    require(type(row.get("accepted_count_delta")) is int and row["accepted_count_delta"]==0,"NO_QUEUE_ADVANCE")
    checkpoint=row.get("checkpoint")
    require(type(checkpoint) is dict and checkpoint.get("schema_version")==prepared.SCHEMA
        and checkpoint.get("context")==expected_context,"EXACT_CHECKPOINT_SCHEMA_CONTEXT")
    require(checkpoint.get("whole_predecessor_oracle_completed") is True
        and checkpoint.get("future_actual_Native_two_byte_boundaries_and_independent_oracle_required") is True,
        "ORIGINAL_WHOLE_PREPARATION_AND_FUTURE_NATIVE_REQUIRED")
    for key in ("product_or_Native_executed","runtime_admission_qualified","GO_authorized",
        "queue_advance_authorized","input_scope_reduction_or_rate_deadline_change"):
        require(checkpoint.get(key) is False,"NO_RUNTIME_ADMISSION_OR_RELAXATION")
    scope=pins(checkpoint.get("complete_scope"))
    fresh=pins(checkpoint.get("final_fresh_inputs"))
    final=checkpoint.get("final_fresh_hashes")
    require(type(final) is int and final==len(fresh)
        and type(row.get("fresh_inputs")) is int and row["fresh_inputs"]==final
        and type(row.get("final_fresh_hashes")) is int and row["final_fresh_hashes"]==final,"EVERY_RECORDED_FINAL_HASH")
    for key,value in expected_current_pins.items():
        require(checkpoint.get(key)==value and scope.get(value["path"])==value
            and fresh.get(value["path"])==value,"EXACT_CURRENT_PINS_IN_BOTH_SCOPES")
    observed=checkpoint.get("scope_inputs_final_fresh_read_here")
    declared=checkpoint.get("scope_inputs_declared_not_final_fresh_read_here")
    require(type(observed) is list and type(declared) is list,"EXPLICIT_FRESH_AND_DECLARED_LISTS")
    observed=pins(observed) if observed else {}
    declared=pins(declared) if declared else {}
    actual_observed={n:p for n,p in scope.items() if n in fresh}
    require(all(fresh[n]==p for n,p in actual_observed.items()) and observed==actual_observed
        and declared=={n:p for n,p in scope.items() if n not in fresh},"EXACT_FRESH_DECLARED_PARTITION")
    require(checkpoint.get("every_complete_scope_input_final_fresh_read_here") is (not declared),"HONEST_SCOPE_FRESHNESS")
    source_pins=pins(row.get("source_pins"))
    require(set(source_pins)==set(expected_source_paths)
        and all(scope.get(n)==p and fresh.get(n)==p for n,p in source_pins.items()),"EXACT_BOUND_PRODUCER_SOURCES")
    require(type(binding.next_case) is int and binding.next_case==160
        and scope.get(binding.manifest_pin["path"])==dict(binding.manifest_pin),"CURRENT_TYPED_MANIFEST")
    frozen_scope={n:dict(p) for n,p in scope.items()}
    live_pins={n:dict(p) for n,p in q.snapshots.items()}
    projection,_=binding.project(scope,q.checkpoint)
    representation=binding.representation(projection)
    require(same(scope,frozen_scope) and same(q.snapshots,live_pins),"DECLARATION_PROJECTION_MUST_NOT_MUTATE_INPUTS")
    require(same(representation,checkpoint.get("representation")),"ENTIRE_ORIGINAL_SCOPE_REPRESENTATION")
    rust=rust_inputs(scope)
    require(rust==expected_rust and type(row.get("current_Rust_input_count")) is int
        and row["current_Rust_input_count"]==len(rust),"ALL_EXACT_CURRENT_RUST_INPUTS")
    require(type(row.get("source_pairs")) is int and row["source_pairs"]==len(binding.descriptors()),"ALL_MANIFEST_PAIRS")
    require(checkpoint_pin["path"] not in scope,"CHECKPOINT_NOT_SELF_REFERENTIAL")
    # The checkpoint itself joins, rather than replaces, the entire declaration.
    result={**scope,checkpoint_pin["path"]:checkpoint_pin}
    return result,rust,dict(prepared_scope_reconstructed_exactly=True,
        source_scope_reduced=False,checkpoint_original_added_to_required_scope=True,
        actual_two_Native_byte_boundaries_and_independent_product_oracle_still_required=True,
        runtime_handoff_connected_or_qualified=False,GO_authorized=False,
        original_rates_deadlines_and_resource_guards_must_be_retained=True)
