"""Closed metadata-only export after whole preparation and final freshness.

This export is not a Native frame, product result, runtime admission or GO.
"""
import copy

SELF="tools/p09/prepared_input_checkpoint_v1.py"
TEST="tools/p09/tests/test_prepared_input_checkpoint_v1.py"
SCHEMA="hwpx-agent.p09-prepared-input-checkpoint/v1"

def require(ok,label):
    if not ok:raise ValueError("PREPARED_INPUT_CHECKPOINT_"+label)

def pin(value):
    require(type(value) is dict and set(value)=={"path","bytes","sha256"},"CLOSED_PIN")
    require(type(value["path"]) is str and value["path"] and type(value["bytes"]) is int and
        value["bytes"]>0 and type(value["sha256"]) is str and len(value["sha256"])==64 and
        all(c in "0123456789abcdef" for c in value["sha256"]),"EXACT_PIN_VALUES")
    return dict(value)

def export(q,scope,binding,*,context,data_pin,preflight_pin,authority_pin,prior_runtime_pin,whole_oracle_completed):
    require(whole_oracle_completed is True,"WHOLE_ORACLE_REQUIRED")
    require(type(context) is dict and context==dict(index=160,before=153,physical_product_run=3),
        "EXACT_PREPARED_CURRENT_CONTEXT")
    require(type(q.snapshots) is dict and 0<len(q.snapshots)<=4096 and
        type(q.final_fresh_hashes) is int and q.final_fresh_hashes==len(q.snapshots),"EVERY_FINAL_FRESH_HASH")
    require(type(scope) is dict and 0<len(scope)<=4096,"BOUNDED_COMPLETE_SCOPE")
    for path,value in scope.items():require(pin(value)["path"]==path,"SCOPE_KEY_MATCH")
    require(type(binding.next_case) is int and binding.next_case==160,"CURRENT_TYPED_BINDING")
    for value in (data_pin,preflight_pin,authority_pin,prior_runtime_pin):
        p=pin(value);require(scope.get(p["path"])==p and q.snapshots.get(p["path"])==p,"CURRENT_AUTHORITY_DATA_BOUND")
    require(scope.get(binding.manifest_pin["path"])==dict(binding.manifest_pin),"ACTUAL_MANIFEST_IN_SCOPE")
    projection,_=binding.project(scope,q.checkpoint)
    representation=binding.representation(projection)
    # Only source declarations are exported. No runtime row, payload or cached
    # computed file hashes become a replacement for future actual live reads.
    result=dict(schema_version=SCHEMA,context=dict(context),data_pin=pin(data_pin),
        preflight_pin=pin(preflight_pin),authority_pin=pin(authority_pin),prior_runtime_pin=pin(prior_runtime_pin),
        complete_scope=[pin(p) for _,p in sorted(scope.items())],representation=representation,
        final_fresh_inputs=[pin(p) for _,p in sorted(q.snapshots.items())],final_fresh_hashes=q.final_fresh_hashes,
        whole_predecessor_oracle_completed=True,product_or_Native_executed=False,
        runtime_admission_qualified=False,GO_authorized=False,queue_advance_authorized=False,
        future_actual_Native_two_byte_boundaries_and_independent_oracle_required=True,
        input_scope_reduction_or_rate_deadline_change=False)
    return copy.deepcopy(result)
