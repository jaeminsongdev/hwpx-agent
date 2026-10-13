"""Opt-in probe factory in the unchanged sole-observer wrapper.

Only the local entry namespace's attribution dependency is replaced. Original
Windows.sample, cold8s/warning75 schedule, source/Job/GO guards, close and summary
remain. No extra observer/thread/query, file edits, retries or queue writes.
"""
from types import SimpleNamespace as NS

import serial_observer_attribution as original
import serial_cpu_attribution_budget_v1 as budget

SELF = "tools/p09/serial_observer_budget_connection_v1.py"
TEST = "tools/p09/tests/test_serial_observer_budget_connection_v1.py"
OBSERVER_PIN = dict(path=original.SELF, bytes=2556,
    sha256="7dbe15f7b13b748801884f794d0a1b59c23f259fbb2283e562fde6576f27f931")


def require(ok, code):
    if not ok:
        raise ValueError("BUDGET_OBSERVER_CONNECTION_" + code)


def view(probe_type, proof):
    require(isinstance(probe_type, type) and issubclass(probe_type, budget.BudgetMixin)
        and issubclass(probe_type, budget.original.Probe), "EXACT_BUDGET_PROBE_TYPE")
    original_factory = original.windows_type
    original_close = original.close
    original_summary = original.summary

    def windows_type(base, objects):
        return original_factory(base, objects, factory=probe_type)

    def summary(objects):
        row = original_summary(objects)
        count = sum(isinstance(w.attribution_probe, probe_type) for w in objects)
        row["early_budget_probe_connection"] = dict(
            existing_observer_instances=len(objects), budget_probe_instances=count,
            same_original_windows_factory=True, original_sample_CPU_RAM_values_retained=True,
            original_cold8_warning75_schedule_retained=True, original_close_and_summary_retained=True,
            second_sampler_thread_or_process=False, additional_PDH_query=False,
            original_K32_decisions_replaced=False,
            instance_binding_observed=bool(objects) and count == len(objects),
            original_probe_sample_AST_projection=proof,
            runtime_product_connection_qualified=False, PC_freeze_resolved=False)
        return row

    # 모듈 자체와 원 factory의 default/global은 변경하지 않는다.
    return NS(**{**vars(original), "windows_type": windows_type,
        "close": original_close, "summary": summary})


def make_view(raw):
    cls, proof = budget.make_probe(raw)
    return view(cls, proof)


def bind_entry(api, raw):
    env = api.run_owned.__globals__
    require(env.get("attribution") is original, "ORIGINAL_LOCAL_ATTRIBUTION_DEPENDENCY")
    before = dict(env)
    code = api.run_owned.__code__
    updated = make_view(raw)
    env["attribution"] = updated
    require(set(env) == set(before) and all(env[k] is v for k, v in before.items()
        if k != "attribution"), "ONE_LOCAL_DEPENDENCY_ONLY")
    require(api.run_owned.__code__ is code and original.windows_type is before["attribution"].windows_type,
        "ORIGINAL_ENTRY_AND_MODULE_NOT_MUTATED")
    return dict(entry_function_bytecode_unchanged=True, local_dependency_changes=1,
        original_attribution_module_not_mutated=True, new_probe_factory_only=True,
        original_GO_Job_Native_bytes_resources_and_cleanup_not_replaced=True,
        new_observer_thread_or_query=False, runtime_product_connection_qualified=False)
