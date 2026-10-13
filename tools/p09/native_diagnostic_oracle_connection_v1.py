"""Diagnostic version dispatch in unchanged six-layer FULL candidate oracle.

새146+ 결과에 legacy PDH provenance를 위조하지 않는다. 기존145 이하 결과는
원 진단 validator로 검증한다. 제품/전체source/Native bytes/resource/cleanup
validator bytecode와 direct/scoped dependencies는 그대로 둔다.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

import native_diagnostic_connection_v1 as diagnostic

SELF = "tools/p09/native_diagnostic_oracle_connection_v1.py"
TEST = "tools/p09/tests/test_native_diagnostic_oracle_connection_v1.py"
LEAF = "flat_current_queue_budget_acceptance_v1.py"


def require(ok, code):
    if not ok:
        raise ValueError("NATIVE_DIAGNOSTIC_ORACLE_" + code)


def dispatch(original, row):
    index = row.get("selected_test_index")
    require(type(index) is int and 115 <= index <= 249, "EXACT_RECORDED_RUNTIME_INDEX")
    backend = row.get("serial_CPU_attribution", {}).get("backend")
    if index >= 146:
        require(backend == diagnostic.BACKEND, "NEW_RUNTIME_MUST_HAVE_NATIVE_BACKEND")
        return diagnostic.validate(row)
    require(backend != diagnostic.BACKEND, "HISTORICAL_PROVENANCE_NOT_REBASED")
    return original(row)


def connect_candidate(function):
    state = dict(cloned_functions=[], diagnostic_leaf_changes=0)
    active = set()
    def clone(fn, depth=0):
        require(type(fn) is FunctionType and depth <= 12 and id(fn) not in active,
                "BOUNDED_ACYCLIC_CANDIDATE_CHAIN")
        active.add(id(fn)); env = dict(fn.__globals__)
        if Path(fn.__code__.co_filename).name == LEAF:
            old = env.get("actual_budget_binding")
            require(type(old) is FunctionType, "EXACT_ORIGINAL_DIAGNOSTIC_LEAF")
            env["actual_budget_binding"] = lambda row: dispatch(old, row)
            state["diagnostic_leaf_changes"] += 1
        children = 0
        for key in ("prior", "accepted", "metadata", "original"):
            obj = env.get(key); child = getattr(obj, "validate_candidate", None)
            if key in fn.__code__.co_names and type(child) is FunctionType:
                env[key] = NS(**{**vars(obj), "validate_candidate": clone(child, depth + 1)})
                children += 1
        require(children <= 1, "NO_AMBIGUOUS_ORACLE_BRANCH")
        result = FunctionType(fn.__code__, env, argdefs=fn.__defaults__, closure=fn.__closure__)
        require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
                and result.__closure__ is fn.__closure__, "WHOLE_VALIDATOR_BYTECODE_RETAINED")
        state["cloned_functions"].append(dict(file=Path(fn.__code__.co_filename).name,
                                             function=fn.__name__, bytecode_unchanged=True))
        active.remove(id(fn)); return result
    result = clone(function)
    require(state["diagnostic_leaf_changes"] == 1, "ONE_EXPLICIT_DIAGNOSTIC_VERSION_DISPATCH")
    return result, state
