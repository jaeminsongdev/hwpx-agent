"""Exact34 graph through the entire original32 connector code."""
from types import FunctionType,SimpleNamespace as NS
import successor_runtime_graph_v6 as original
SELF="tools/p09/successor_runtime_graph_v7.py"
TEST="tools/p09/tests/test_successor_runtime_graph_v7.py"
TASK=original.TASK
fn=original.connect
code=fn.__code__
if sum(type(x) is int and x==32 for x in code.co_consts)!=1:raise ValueError("ONE_ORIGINAL_GRAPH_COUNT32")
changed=code.replace(co_consts=tuple(34 if type(x) is int and x==32 else x for x in code.co_consts))
if changed.replace(co_consts=code.co_consts)!=code:raise ValueError("WHOLE_ORIGINAL_GRAPH_CODE_INVERSE")
def single_wire(api):
    compact=original.compact
    encode_json=api.encode.__globals__.get("json")
    decode_json=api.decode.__globals__.get("json")
    if encode_json is compact.JSON or decode_json is compact.JSON:
        compact.require(encode_json is compact.JSON and decode_json is compact.JSON and api.MAX_BYTES==16384,
            "EXACT_ALREADY_COMPACT_ENCODER_AND_DECODER")
        return api,dict(original_encode_decode_code_defaults_closure_retained=True,
            original_semantic_schema_context_binding_and_hash_checks_retained=True,
            original_worker_body_not_replaced=True,original_namespace_not_mutated=True,
            maximum_wire_bytes=16384,all_descriptor_rows_reconstructed=True,
            wire_schema=compact.SCHEMA,exact_existing_compact_interface_reused_not_stacked=True,
            actual_worker_Native_or_GO_qualified=False)
    return compact.connect(api)
private_compact=NS(**{**vars(original.compact),"connect":single_wire})
connect=FunctionType(changed,dict(fn.__globals__,compact=private_compact),argdefs=fn.__defaults__,closure=fn.__closure__)
connect.__kwdefaults__=fn.__kwdefaults__
