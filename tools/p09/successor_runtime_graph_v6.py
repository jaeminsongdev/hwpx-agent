"""Keep the original complete private graph; only wire and run004 task change."""
from types import FunctionType,SimpleNamespace as NS
import compact_worker_capsule_wire_v1 as compact
SELF="tools/p09/successor_runtime_graph_v6.py"
TEST="tools/p09/tests/test_successor_runtime_graph_v6.py"
TASK="case160-current-r004-tests"

def connect(base,bound):
    compact.require(type(bound) is base.binding_module.Binding and bound.next_case==160
        and len(bound.descriptors())==32,"EXACT_PRIVATE32_BINDING")
    worker,wire_proof=compact.connect(base.worker)
    original=worker.connect_worker
    execute=FunctionType(original.__code__,dict(original.__globals__,TASK=TASK),
        argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    worker=NS(**{**vars(worker),"TASK":TASK,"connect_worker":execute})
    compact.require(base.parent.access.source is base.binding_module and
        base.parent.original.frames.binding_module is base.binding_module and
        worker.source is base.binding_module and worker.raw_policy.source is base.binding_module and
        base.full_oracle.binding_module is base.binding_module,"ONE_ORIGINAL_PARENT_FRAME_WORKER_ORACLE_MODULE")
    graph=NS(**{**vars(base),"binding":bound,"worker":worker})
    return graph,dict(compact_wire_connection=wire_proof,original_worker_connector_code_defaults_closure_retained=True,
        original_parent_and_full_oracle_objects_retained=True,only_explicit_task_metadata_changed=True,
        actual_run004_engine_worker_Native_or_GO_qualified=False)
