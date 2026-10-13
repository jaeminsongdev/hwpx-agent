"""Private case159 connection of the original fifteen-second window oracle.

Only the exact case literal changes. The inverse must restore the complete
original code; all timing, frame, cleanup and resource predicates remain.
This connection grants neither product acceptance nor permission to issue GO.
"""
from types import FunctionType

SELF="tools/p09/successor_strict_window_v1.py"
TEST="tools/p09/tests/test_successor_strict_window_v1.py"


def connect(original):
    code=original.__code__
    if sum(type(x) is int and x==157 for x in code.co_consts)!=1:
        raise ValueError("SUCCESSOR_WINDOW_ONE_ORIGINAL_CASE_LITERAL")
    if any(type(x) is int and x==159 for x in code.co_consts):
        raise ValueError("SUCCESSOR_WINDOW_UNAMBIGUOUS_INVERSE")
    constants=tuple(159 if type(x) is int and x==157 else x for x in code.co_consts)
    changed=code.replace(co_consts=constants)
    inverse=changed.replace(co_consts=tuple(157 if type(x) is int and x==159 else x for x in changed.co_consts))
    if inverse!=code:
        raise ValueError("SUCCESSOR_WINDOW_ENTIRE_ORIGINAL_CODE_RESTORED")
    check=FunctionType(changed,dict(original.__globals__),argdefs=original.__defaults__,closure=original.__closure__)
    check.__kwdefaults__=original.__kwdefaults__
    return check,dict(exact_case_literal_157_to_159=True,inverse_entire_original_code_equal=True,
        original_defaults_closure_and_kwdefaults_retained=True,original_fifteen_second_checks_retained=True,
        original_default_namespace_mutated=False,actual159_product_or_GO_qualified=False)
