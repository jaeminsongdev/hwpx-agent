"""Exact34 graph through the entire original32 connector code."""
from types import FunctionType
import successor_runtime_graph_v6 as original
SELF="tools/p09/successor_runtime_graph_v7.py"
TEST="tools/p09/tests/test_successor_runtime_graph_v7.py"
TASK=original.TASK
fn=original.connect
code=fn.__code__
if sum(type(x) is int and x==32 for x in code.co_consts)!=1:raise ValueError("ONE_ORIGINAL_GRAPH_COUNT32")
changed=code.replace(co_consts=tuple(34 if type(x) is int and x==32 else x for x in code.co_consts))
if changed.replace(co_consts=code.co_consts)!=code:raise ValueError("WHOLE_ORIGINAL_GRAPH_CODE_INVERSE")
connect=FunctionType(changed,dict(fn.__globals__),argdefs=fn.__defaults__,closure=fn.__closure__)
connect.__kwdefaults__=fn.__kwdefaults__
