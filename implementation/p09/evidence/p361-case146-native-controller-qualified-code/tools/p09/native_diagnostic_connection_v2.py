"""Successor connector propagates BOTH function globals and module namespaces.

원 wrappers는 __globals__뿐 아니라 vars(prior.prior)를 재구성한다.
모든 기존 bytecode/default/closure는 유지하고 private dependency namespace만
일치시킨다. v1의 실패와 실제146 legacy 기록은 변경하거나 재실행하지 않는다.
"""
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

import native_diagnostic_connection_v1 as prior

SELF = "tools/p09/native_diagnostic_connection_v2.py"
TEST = "tools/p09/tests/test_native_diagnostic_connection_v2.py"
BACKEND = prior.BACKEND
LEAF = prior.LEAF
definitions = prior.definitions
connect_entry = prior.connect_entry
validate = prior.validate


def require(ok, code):
    if not ok:
        raise ValueError("NATIVE_NAMESPACE_CONNECTION_V2_" + code)


def connect_run(function, backend):
    state = dict(actual_local_bindings=0, cloned_functions=[],
                 static_leaf_connections=0, namespace_dependency_projections=[])
    active = set()

    def clone(fn, depth=0):
        require(type(fn) is FunctionType and depth <= 12 and id(fn) not in active,
                "BOUNDED_ACYCLIC_RUN_CHAIN")
        active.add(id(fn))
        env = dict(fn.__globals__)
        if Path(fn.__code__.co_filename).name == LEAF:
            old = env.get("connection")
            require(old is not None and callable(getattr(old, "bind_entry", None)),
                    "EXACT_LEAF_BINDING")
            def bind(api, raw):
                return connect_entry(api, raw, old, backend, state)
            env["connection"] = NS(**{**vars(old), "bind_entry": bind})
            state["static_leaf_connections"] += 1
        else:
            children = []
            for key in ("source", "prior"):
                obj = env.get(key)
                child = getattr(obj, "run_owned", None)
                if key in fn.__code__.co_names and type(child) is FunctionType:
                    children.append(key)
                    connected = clone(child, depth + 1)
                    values = dict(vars(obj))
                    changed = []
                    # The original chunk/budget wrappers reconstruct functions
                    # from vars(module), including nested prior.prior namespaces.
                    # Keep those exact dependency references aligned with globals.
                    for dependency in ("source", "prior", "connection"):
                        if dependency in connected.__globals__:
                            replacement = connected.__globals__[dependency]
                            if replacement is not child.__globals__.get(dependency):
                                require(dependency in values, "DEPENDENCY_ALREADY_EXPORTED")
                                values[dependency] = replacement
                                changed.append(dependency)
                    values["run_owned"] = connected
                    require(set(values) == set(vars(obj)), "NO_NAMESPACE_FIELDS_ADDED_OR_HIDDEN")
                    require(all(values[name] is value for name, value in vars(obj).items()
                                if name not in changed and name != "run_owned"),
                            "ALL_OTHER_NAMESPACE_VALUES_RETAINED")
                    env[key] = NS(**values)
                    state["namespace_dependency_projections"].append(dict(
                        module=Path(child.__code__.co_filename).name,
                        fields=changed, original_namespace_not_mutated=True))
            require(len(children) == 1, "ONE_ORIGINAL_RUN_DEPENDENCY_PER_LEVEL")
        result = FunctionType(fn.__code__, env, argdefs=fn.__defaults__, closure=fn.__closure__)
        require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
                and result.__closure__ is fn.__closure__, "ALL_RUN_CODE_DEFAULTS_CLOSURES_RETAINED")
        state["cloned_functions"].append(dict(file=Path(fn.__code__.co_filename).name,
                                             function=fn.__name__, bytecode_unchanged=True))
        active.remove(id(fn))
        return result

    result = clone(function)
    require(state["static_leaf_connections"] == 1, "EXACTLY_ONE_NATIVE_OBSERVER_CONNECTION")
    return result, state

