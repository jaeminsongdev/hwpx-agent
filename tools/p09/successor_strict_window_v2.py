"""Exact160 metadata connection; retain every original fifteen second check."""
from types import FunctionType
import successor_strict_window_v1 as original

SELF="tools/p09/successor_strict_window_v2.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v28.py"


def connect(check):
    fn,proof=original.connect(check);code=fn.__code__
    if sum(type(x) is int and x==159 for x in code.co_consts)!=1:
        raise ValueError("SUCCESSOR160_WINDOW_ONE_EXACT_CASE")
    if any(type(x) is int and x==160 for x in code.co_consts):
        raise ValueError("SUCCESSOR160_WINDOW_UNAMBIGUOUS_INVERSE")
    changed=code.replace(co_consts=tuple(160 if type(x) is int and x==159 else x for x in code.co_consts))
    inverse=changed.replace(co_consts=tuple(159 if type(x) is int and x==160 else x for x in changed.co_consts))
    if inverse!=code:raise ValueError("SUCCESSOR160_WINDOW_ENTIRE_ORIGINAL_CODE_RESTORED")
    out=FunctionType(changed,dict(fn.__globals__),argdefs=fn.__defaults__,closure=fn.__closure__)
    out.__kwdefaults__=fn.__kwdefaults__
    return out,dict(proof,exact_case_literal_159_to_160=True,
        inverse_entire_original_code_equal=True,actual160_product_or_GO_qualified=False)
