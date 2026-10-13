"""Exact159 capsule metadata projection; preserve all original worker code.

New closed wire/v2 uses authority_pin/prior_runtime_pin rather than falsely
labelling152/158 as151/157. Encoder/decoder metadata inverse restores the entire
original code; worker dispatch bytecode itself is unmodified. No GO inferred.
"""
from types import FunctionType, SimpleNamespace as NS

SELF="tools/p09/runtime_successor_worker_capsule_v1.py"
TEST="tools/p09/tests/test_runtime_successor_worker_capsule_v1.py"
SCHEMA="hwpx-agent.p09-envelope-worker-policy-capsule/v2"
TASK="case159-current-r001-tests"


def require(ok,label):
    if not ok:raise ValueError("SUCCESSOR_WORKER_CAPSULE_"+label)


def constant(value,reverse=False):
    if type(value) is tuple:return tuple(constant(x,reverse) for x in value)
    if type(value) is int:
        pairs={159:158,152:151} if reverse else {158:159,151:152}
        return pairs.get(value,value)
    if type(value) is str:
        pairs={"authority_pin":"authority151_pin","prior_runtime_pin":"actual157_pin"} if reverse else {
            "authority151_pin":"authority_pin","actual157_pin":"prior_runtime_pin"}
        return pairs.get(value,value)
    return value


def project(fn,env):
    code=fn.__code__
    require(sum(type(x) is int and x==158 for x in code.co_consts)==1 and
        sum(type(x) is int and x==151 for x in code.co_consts)==1,"ONE_CASE_AND_ONE_COUNT_LITERAL")
    revised=code.replace(co_consts=tuple(constant(x) for x in code.co_consts))
    require(revised.replace(co_consts=tuple(constant(x,True) for x in revised.co_consts))==code,
        "ALL_ORIGINAL_METADATA_CODE_RESTORED")
    changed=FunctionType(revised,dict(fn.__globals__,**env),argdefs=fn.__defaults__,closure=fn.__closure__)
    changed.__kwdefaults__=fn.__kwdefaults__
    return changed


def connect(original,binding,authority_pin,runtime_pin,successor):
    require(hasattr(binding,"successor_failure_lineage") and
        binding.successor_failure_lineage["next_case"]==159,"QUALIFIED_PRIVATE159_BINDING")
    binding.exact(authority_pin,successor.AUTHORITY,"EXACT_AUTHORITY152")
    binding.exact(runtime_pin,successor.ROOT,"EXACT_RUNTIME158")
    env=dict(source=binding,AUTHORITY=dict(authority_pin),ROOT=dict(runtime_pin),SCHEMA=SCHEMA,TASK=TASK)
    encode=project(original.encode,env);decode=project(original.decode,env)
    worker=FunctionType(original.connect_worker.__code__,dict(original.connect_worker.__globals__,**env),
        argdefs=original.connect_worker.__defaults__,closure=original.connect_worker.__closure__)
    worker.__kwdefaults__=original.connect_worker.__kwdefaults__
    namespace=NS(**{**vars(original),**env,"encode":encode,"decode":decode,"connect_worker":worker})
    return namespace,dict(encoder_decoder_inverse_code_equal=True,
        original_worker_code_defaults_closure_retained=True,
        old_default_namespace_mutated=False,wire_keys_explicit_current_authority=True,
        maximum_capsule_bytes=original.MAX_BYTES,actual159_worker_or_GO_qualified=False)
