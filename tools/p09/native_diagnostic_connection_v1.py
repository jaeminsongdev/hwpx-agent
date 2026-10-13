"""Private NO_PDH dependency connection and closed diagnostic schema validator.

원 run_owned/GO/Job/source/two-byte/resource/cleanup bytecode는 유지한다.
진단 backend가 다른데 기존 PDH였다며 필드를 위조하지 않는다. 기존 기록은
기존 oracle로 검증하고 새 형식만 명시적인 native 진단 규칙을 적용한다.
이 모듈의 import/가짜 실행기 tests는 실제 Native/product qualification이 아니다.
"""
import ast
import copy
import hashlib
import math
from pathlib import Path
from types import FunctionType, SimpleNamespace as NS

SELF = "tools/p09/native_diagnostic_connection_v1.py"
TEST = "tools/p09/tests/test_native_diagnostic_connection_v1.py"
BACKEND = "NATIVE_TOOLHELP_PROCESS_TIMES_V2"
LEAF = "flat_current_queue_budget_runtime_v1.py"


def require(ok, code):
    if not ok:
        raise ValueError("NATIVE_DIAGNOSTIC_CONNECTION_" + code)


def definitions(raw, pin, environment, *, initialization=False):
    """Exact AST namespace; no module registration/removal or hidden imports."""
    require(type(raw) is bytes and len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"], "EXACT_NAMESPACE_RAW")
    tree = ast.parse(raw.decode("utf-8"))
    def selected(node):
        if isinstance(node, (ast.Assign, ast.FunctionDef, ast.ClassDef)):
            return True
        if initialization and isinstance(node, ast.For):
            return True
        return (initialization and isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "_env" and node.value.func.attr == "update")
    original = [node for node in tree.body if selected(node)]
    nodes = copy.deepcopy(original)
    require(nodes and [ast.dump(n, include_attributes=False) for n in nodes]
            == [ast.dump(n, include_attributes=False) for n in original], "ALL_SELECTED_AST_UNCHANGED")
    env = {**environment, "__file__": pin["path"], "__name__": "p09_exact_native_diagnostic_namespace"}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 pin["path"], "exec"), env)
    return NS(**env), dict(source_pin=pin, exact_selected_definition_AST=True,
                           full_module_or_CLI_import_executed=False,
                           sys_modules_hidden_or_removed=False,
                           default_source_module_mutated=False)


def connect_entry(api, raw, old_connection, backend, state):
    """Retain original bind/projection checks, then switch ONE local dependency."""
    require(getattr(backend, "SELF", None) == "tools/p09/native_process_cpu_attribution_v2.py",
            "EXACT_NATIVE_V2_BACKEND")
    require(all(callable(getattr(backend, key, None)) for key in ("windows_type", "close", "summary")),
            "FULL_BACKEND_INTERFACE")
    original_code = api.run_owned.__code__
    old_connection.bind_entry(api, raw)  # exact old AST/pin proof, no OS probe construction
    env = api.run_owned.__globals__
    previous = dict(env)
    require("attribution" in previous, "LOCAL_OBSERVER_DEPENDENCY")
    def summary(objects):
        result = backend.summary(objects)
        require(result.get("backend") == BACKEND, "REAL_NATIVE_BACKEND_SUMMARY")
        result["native_backend_connection"] = dict(
            original_entry_bytecode_retained=True, local_dependency_changes=1,
            original_GO_Job_source_byte_resource_and_cleanup_unchanged=True,
            old_PDH_default_module_not_mutated=True,
            PDH_factory_instantiated=False, second_sampler_thread_or_process=False,
            actual_factory_instances=len(objects), native_backend_source=backend.SELF,
            runtime_product_connection_qualified=False, PC_freeze_resolved=False)
        return result
    env["attribution"] = NS(**{**vars(backend), "summary": summary})
    require(api.run_owned.__code__ is original_code and set(env) == set(previous)
            and all(env[k] is value for k, value in previous.items() if k != "attribution"),
            "ONLY_ONE_LOCAL_DEPENDENCY_NO_BYTECODE_CHANGE")
    state["actual_local_bindings"] += 1


def connect_run(function, backend):
    """Copy only source/prior run_owned chain. Never mutate public namespaces."""
    state = dict(actual_local_bindings=0, cloned_functions=[], static_leaf_connections=0)
    active = set()
    def clone(fn, depth=0):
        require(type(fn) is FunctionType and depth <= 12 and id(fn) not in active, "BOUNDED_ACYCLIC_RUN_CHAIN")
        active.add(id(fn)); env = dict(fn.__globals__)
        if Path(fn.__code__.co_filename).name == LEAF:
            old = env.get("connection")
            require(old is not None and callable(getattr(old, "bind_entry", None)), "EXACT_LEAF_BINDING")
            def bind(api, raw): return connect_entry(api, raw, old, backend, state)
            env["connection"] = NS(**{**vars(old), "bind_entry": bind})
            state["static_leaf_connections"] += 1
        else:
            children = []
            for key in ("source", "prior"):
                obj = env.get(key)
                child = getattr(obj, "run_owned", None)
                if key in fn.__code__.co_names and type(child) is FunctionType:
                    children.append(key)
                    env[key] = NS(**{**vars(obj), "run_owned": clone(child, depth + 1)})
            require(len(children) == 1, "ONE_ORIGINAL_RUN_DEPENDENCY_PER_LEVEL")
        result = FunctionType(fn.__code__, env, argdefs=fn.__defaults__, closure=fn.__closure__)
        require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
                and result.__closure__ is fn.__closure__, "ALL_RUN_BYTECODE_DEFAULTS_CLOSURES_RETAINED")
        state["cloned_functions"].append(dict(file=Path(fn.__code__.co_filename).name,
                                             function=fn.__name__, bytecode_unchanged=True))
        active.remove(id(fn)); return result
    result = clone(function)
    require(state["static_leaf_connections"] == 1, "EXACTLY_ONE_NATIVE_OBSERVER_CONNECTION")
    return result, state


def finite(value, minimum=0., maximum=None):
    return (type(value) in (int, float) and math.isfinite(value) and value >= minimum
            and (maximum is None or value <= maximum))


def validate(row):
    """Diagnostic-only schema, not a replacement for ANY product/source oracle."""
    info = row["serial_CPU_attribution"]
    require(info.get("backend") == BACKEND and type(info.get("existing_observer_instances")) is int
            and info["existing_observer_instances"] == 1,
            "EXACT_NATIVE_BACKEND_SINGLE_OWNER")
    for key, value in dict(cold_counter_interval_seconds=8., original_warning_for_forced_read_percent=75,
                          original_CPU_RAM_decisions_replaced=False, additional_PDH_queries_explicit=False,
                          additional_native_process_queries_explicit=True, second_sampler_thread_or_process=False,
                          interval_identical_to_K32_interval=False, runtime_connection_qualified=False,
                          PC_freeze_resolved=False).items():
        actual = info.get(key)
        require(type(actual) is type(value) and actual == value, "CLOSED_NATIVE_OBSERVER_POLICY")
    connection = info["native_backend_connection"]
    for key, value in dict(original_entry_bytecode_retained=True, local_dependency_changes=1,
                          original_GO_Job_source_byte_resource_and_cleanup_unchanged=True,
                          old_PDH_default_module_not_mutated=True, PDH_factory_instantiated=False,
                          second_sampler_thread_or_process=False, actual_factory_instances=1,
                          native_backend_source="tools/p09/native_process_cpu_attribution_v2.py",
                          runtime_product_connection_qualified=False, PC_freeze_resolved=False).items():
        actual = connection.get(key)
        require(type(actual) is type(value) and actual == value, "CLOSED_ACTUAL_NATIVE_CONNECTION")
    probes = info["probes"]
    require(type(probes) is list and len(probes) == 1, "ONE_NATIVE_PROBE")
    probe = probes[0]
    for key, value in dict(backend=BACKEND, maximum_sample_budget_seconds=.05,
                          total_added_sample_budget_seconds=2., setup_included_in_same_cost_budget=True,
                          maximum_query_calls=128, query_remaining=False, cleanup_confirmed=True,
                          PDH_or_WMI_called=False, original_CPU_RAM_guards_replaced=False,
                          second_sampler_thread_or_process=False, DPC_and_interrupt_counters_unavailable_not_zero=True,
                          runtime_connection_qualified=False, PC_freeze_resolved=False,
                          capture_failure_cleanup_unknown=False, native_capture_handle_cleanup_status="CONFIRMED",
                          capture_error_never_promoted_to_successful_cleanup=True,
                          automatic_retry_or_resume=False).items():
        actual = probe.get(key)
        require(type(actual) is type(value) and actual == value, "EXACT_NATIVE_PROBE_POLICY_AND_CLEANUP")
    require(type(probe.get("query_calls")) is int and 1 <= probe["query_calls"] <= 128,
            "ACTUAL_QUERY_COUNT_NOT_IMPORTED_ONLY")
    require(type(probe.get("samples")) is int and 0 <= probe["samples"] <= probe["query_calls"], "ACTUAL_SAMPLE_COUNT")
    require(finite(probe.get("maximum_added_sample_seconds")) and finite(probe.get("total_added_sample_seconds")),
            "FINITE_ACTUAL_COST")
    # A closed over-budget call is explicit UNAVAILABLE, not fabricated valid data.
    reason = probe.get("disabled_reason")
    require(reason in (None, "MEASUREMENT_COST_BUDGET_EXCEEDED", "QUERY_COUNT_BOUND"), "CLOSED_DISABLE_REASON")
    if reason is None:
        require(probe["maximum_added_sample_seconds"] <= .05 and probe["total_added_sample_seconds"] <= 2.,
                "UNCHANGED_COST_LIMITS")
    samples = row["samples"]
    require(type(samples) is list and 0 < len(samples) <= 4096, "BOUNDED_ORIGINAL_SAMPLES")
    available = 0
    for sample in samples:
        diagnostic = sample["serial_cpu_attribution"]
        require(type(diagnostic.get("available")) is bool and type(diagnostic.get("fresh_for_this_original_resource_sample")) is bool,
                "REAL_SAMPLE_FLAGS")
        if not diagnostic["available"]:
            require(diagnostic.get("values") is None and diagnostic.get("reason") in (
                "NOT_SAMPLED_COLD_INTERVAL", "MEASUREMENT_COST_BUDGET_EXCEEDED", "QUERY_COUNT_BOUND", "BASELINE_UNAVAILABLE"),
                "CLOSED_UNAVAILABLE_NOT_ZERO")
            require(diagnostic["fresh_for_this_original_resource_sample"]
                    == (diagnostic["reason"] != "NOT_SAMPLED_COLD_INTERVAL"), "CORRECT_FRESHNESS_LABEL")
            continue
        available += 1; values = diagnostic["values"]
        require(diagnostic["fresh_for_this_original_resource_sample"] and diagnostic.get("coverage_complete") is False
                and diagnostic.get("PDH_or_WMI_called") is False
                and diagnostic.get("total_cpu_from_original_K32_not_a_second_query") is True,
                "PARTIAL_SUPPORTED_NATIVE_OBSERVATION_ONLY")
        require(values["total_cpu"] == sample["system_cpu_percent"] and finite(values["total_cpu"], maximum=100)
                and values["DPC_cpu"] is None and values["interrupt_cpu"] is None
                and diagnostic.get("DPC_and_interrupt_counters_unavailable_not_zero") is True,
                "EXACT_ORIGINAL_K32_AND_EXPLICIT_UNSUPPORTED_COUNTERS")
        require(finite(diagnostic.get("interval_seconds"), minimum=0.000000001)
                and diagnostic.get("identical_to_original_K32_interval") is False
                and diagnostic.get("causal_trigger_attribution_established") is False,
                "NO_FALSE_INTERVAL_OR_CAUSAL_CLAIM")
        delta = diagnostic["process_deltas"]
        require(finite(delta.get("window_seconds"), minimum=0.000000001)
                and delta["window_seconds"] == diagnostic["interval_seconds"]
                and delta.get("complete_system_CPU_attribution") is False
                and finite(delta.get("matched_machine_CPU_sum")), "PARTIAL_DELTA_WINDOW")
        for key in ("matched_processes", "new_or_reused_pid_no_baseline", "negative_delta_unresolved", "unavailable_current"):
            require(type(delta.get(key)) is int and 0 <= delta[key] <= 512, "BOUNDED_PROCESS_COUNTS")
        require(type(delta.get("process_list_truncated")) is bool, "TRUNCATION_NOT_HIDDEN")
        top = delta["top_processes"]
        require(type(top) is list and len(top) <= 8, "BOUNDED_TOP_PROCESS_LIST")
        roles = {"other", "git.exe", "python.exe", "python3.exe", "codex.exe", "chatgpt.exe", "msmpeng.exe",
                 "compattelrunner.exe", "vmmemwsl", "vmmem", "system", "radeonsoftware.exe", "node.exe",
                 "rustc.exe", "cargo.exe", "powershell.exe", "pwsh.exe", "wmiprvse.exe"}
        seen = set()
        for item in top:
            require(type(item) is dict and set(item) == {"pid", "parent", "role", "machine_CPU_percent"}
                    and type(item["pid"]) is int and 0 < item["pid"] <= 0xffffffff
                    and item["pid"] not in seen and type(item["parent"]) is int and 0 <= item["parent"] <= 0xffffffff
                    and item["role"] in roles and finite(item["machine_CPU_percent"]), "CLOSED_REDACTED_PROCESS_ROW")
            seen.add(item["pid"])
        for label in ("MsMpEng", "System"):
            item = values[label]
            require(type(item.get("pid_stable")) is bool and item.get("creation_identity_bound") is item["pid_stable"],
                    "PID_AND_CREATION_BINDING")
            if item["pid_stable"]:
                require(type(item.get("pid")) is int and 0 < item["pid"] <= 0xffffffff
                        and (label != "System" or item["pid"] == 4)
                        and finite(item.get("machine_cpu_percent"), maximum=100) and item.get("status") == "OBSERVED",
                        "VALID_OBSERVED_PROCESS")
            else:
                require(item.get("machine_cpu_percent") is None and item.get("status") == "UNAVAILABLE_OR_NEW_PID",
                        "UNKNOWN_PID_NOT_ZERO")
    return dict(backend=BACKEND, original_sample_count=len(samples), available_native_diagnostics=available,
                full_product_source_resource_oracle_replaced=False,
                explicit_diagnostic_format_migration_not_legacy_PDH_provenance_forgery=True)
