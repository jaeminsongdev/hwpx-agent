"""Explicit run003 wire; original worker and complete connector code retained."""
from types import FunctionType
import runtime_successor_worker_capsule_v4 as original
SELF="tools/p09/runtime_successor_worker_capsule_v5.py"
TEST="tools/p09/tests/test_runtime_successor_worker_capsule_v5.py"
SCHEMA="hwpx-agent.p09-envelope-worker-policy-capsule/v6"
TASK="case160-current-r003-tests"
constant=original.constant
project=original.project

def connect(worker,binding,authority_pin,runtime_pin,successor):
    first=original.original.original.connect
    execute=FunctionType(first.__code__,dict(first.__globals__,SCHEMA=SCHEMA,TASK=TASK),
        argdefs=first.__defaults__,closure=first.__closure__)
    execute.__kwdefaults__=first.__kwdefaults__
    api,proof=execute(worker,binding,authority_pin,runtime_pin,successor)
    binding.exact(api.TASK,TASK,"EXACT_RUN003_WORKER_TASK")
    return api,dict(proof,original_connector_code_defaults_closure_retained=True,
        explicit_run003_wire_schema=True,current_run003_worker_or_GO_qualified=False)
