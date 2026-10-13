"""Entire V1 parent connector retained; explicit receipt-safe policy dependency."""
from types import FunctionType
import runtime_envelope_parent_connection_v1 as original
import runtime_envelope_raw_access_policy_v2 as access
SELF="tools/p09/runtime_envelope_parent_connection_v2.py"
TEST="tools/p09/tests/test_runtime_envelope_raw_access_policy_v2.py"


def connect_engine(engine,binding):
    fn=original.connect_engine
    connected=FunctionType(fn.__code__,dict(fn.__globals__,access=access),
        argdefs=fn.__defaults__,closure=fn.__closure__)
    connected.__kwdefaults__=fn.__kwdefaults__
    access.source.require(connected.__code__ is fn.__code__,"ENTIRE_PARENT_CONNECTOR_CODE_RETAINED")
    return connected(engine,binding)


evidence=original.evidence
