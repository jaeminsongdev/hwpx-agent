"""Fresh run00226-pair wire schema; all original connector code retained."""
from types import FunctionType
import runtime_successor_worker_capsule_v3 as original
SELF="tools/p09/runtime_successor_worker_capsule_v4.py"
SCHEMA="hwpx-agent.p09-envelope-worker-policy-capsule/v5"
TASK=original.TASK
constant=original.constant
project=original.project


def connect(worker,binding,authority_pin,runtime_pin,successor):
    first=original.original.connect
    execute=FunctionType(first.__code__,dict(first.__globals__,SCHEMA=SCHEMA,TASK=TASK),
        argdefs=first.__defaults__,closure=first.__closure__)
    execute.__kwdefaults__=first.__kwdefaults__
    api,proof=execute(worker,binding,authority_pin,runtime_pin,successor)
    binding.exact(api.TASK,TASK,"EXACT_RUN002_TASK_NOT_NEW_PHYSICAL_ATTEMPT")
    return api,dict(proof,original_connector_code_defaults_closure_retained=True,
        new_wire_schema_explicit_for26_pairs=True,actual_worker_or_GO_qualified=False)
