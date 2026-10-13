"""Run002 capsule connection; preserve all original worker dispatch code."""
from types import FunctionType
import runtime_successor_worker_capsule_v2 as original

SELF="tools/p09/runtime_successor_worker_capsule_v3.py"
TEST="tools/p09/tests/test_runtime_successor_worker_capsule_v3.py"
SCHEMA="hwpx-agent.p09-envelope-worker-policy-capsule/v4"
TASK="case160-current-r002-tests"
constant=original.constant
project=original.project


def connect(worker,binding,authority_pin,runtime_pin,successor):
    fn=original.connect
    execute=FunctionType(fn.__code__,dict(fn.__globals__,SCHEMA=SCHEMA,TASK=TASK),
        argdefs=fn.__defaults__,closure=fn.__closure__)
    execute.__kwdefaults__=fn.__kwdefaults__
    api,proof=execute(worker,binding,authority_pin,runtime_pin,successor)
    binding.exact(api.TASK,TASK,"EXACT_RUN002_WORKER_TASK_DEPENDENCY")
    return api,dict(proof,original_capsule_connector_code_defaults_closure_retained=True,
        explicit_current160_physical_run002_task=True,
        actual160_run002_worker_or_GO_qualified=False)
