"""Opt-in early PDH cost stop; immutable seven-counter probe stays unchanged.

Preserve the complete original sample AST, adding cost checks after collect and
before formatted reads. A slow OS call cannot be preempted; once it returns,
stop further value queries, close the query and discard values. No new sampler,
thread, retries, source cache, changed CPU/RAM decision or enlarged budget.
This module is not connected to the product runtime merely by being imported.
"""
import ast
import copy
import hashlib
import math

import serial_cpu_attribution as original

SELF = "tools/p09/serial_cpu_attribution_budget_v1.py"
TEST = "tools/p09/tests/test_serial_cpu_attribution_budget_v1.py"
ORIGINAL_PIN = dict(path="tools/p09/serial_cpu_attribution.py", bytes=7906,
    sha256="28bd418112ede9cdec445a70e40b0c41c0f1f077faad8b8e4de4891a6ce082ea")


def require(ok, code):
    if not ok:
        raise ValueError("EARLY_PDH_BUDGET_" + code)


class BudgetMixin:
    def __init__(self, *args, **kwargs):
        self.early_budget_checks = 0
        self.early_budget_stops = 0
        super().__init__(*args, **kwargs)

    def _stop_if_budget(self, start, previous, status):
        self.early_budget_checks += 1
        elapsed = self.clock() - start
        require(math.isfinite(elapsed) and elapsed >= 0, "CLOCK")
        # 기존 50ms / 누적 2s 제한 그대로. OS 호출 내부의 강제 중단 아님.
        if elapsed <= original.MAX_SAMPLE_SECONDS and self.total_latency + elapsed <= original.MAX_TOTAL_SAMPLE_SECONDS:
            return None
        self.maximum_latency = max(self.maximum_latency, elapsed)
        self.total_latency += elapsed
        self.early_budget_stops += 1
        self.disabled_reason = "MEASUREMENT_COST_BUDGET_EXCEEDED"
        self.close()  # 원 close/실패 상태를 유지; 이후 collect/value 재개 없음.
        return dict(available=False, collect_status=int(status), values=None,
            added_wall_seconds=elapsed,
            interval_seconds=None if previous is None else self.last - previous,
            identical_to_original_K32_interval=False, first_counter_sample_used_as_rate=False,
            raw_process_commands_or_paths_recorded=False, causal_trigger_attribution_established=False,
            reason=self.disabled_reason, early_formatted_read_stop=True,
            OS_call_hard_preemption_guaranteed=False)

    def summary(self):
        row = super().summary()
        row.update(early_budget_checks=self.early_budget_checks,
            early_budget_stops=self.early_budget_stops,
            cost_checked_before_formatted_reads=True,
            original_seven_counter_PID_status_and_final_cost_checks_retained=True,
            original_CPU_RAM_guards_replaced=False,
            runtime_connection_qualified=False, PC_freeze_resolved=False)
        return row


def projection(raw):
    require(type(raw) is bytes and len(raw) == ORIGINAL_PIN["bytes"] and
        hashlib.sha256(raw).hexdigest() == ORIGINAL_PIN["sha256"], "EXACT_ORIGINAL_BYTES")
    tree = ast.parse(raw.decode("utf-8"))
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Probe"]
    require(len(classes) == 1, "ONE_ORIGINAL_CLASS")
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == "sample"]
    require(len(methods) == 1, "ONE_ORIGINAL_SAMPLE")
    node = copy.deepcopy(methods[0])
    before = ast.dump(node, include_attributes=False)
    require(not any(isinstance(n, ast.Name) and n.id == "_budget_gate" for n in ast.walk(node)), "FRESH_LOCAL")
    reads = results = 0

    def guards():
        additions = ast.parse("_budget_gate = self._stop_if_budget(start, previous, status)\n"
            "if _budget_gate is not None: return _budget_gate").body
        for item in additions:
            item._budget_added = True
        return additions

    class Add(ast.NodeTransformer):
        def visit_Assign(self, item):
            nonlocal reads, results
            is_read = (isinstance(item.value, ast.Call) and
                isinstance(item.value.func, ast.Attribute) and
                isinstance(item.value.func.value, ast.Name) and
                item.value.func.value.id == "self" and item.value.func.attr == "read")
            is_result = (len(item.targets) == 1 and isinstance(item.targets[0], ast.Name)
                and item.targets[0].id == "result" and isinstance(item.value, ast.Call)
                and isinstance(item.value.func, ast.Name) and item.value.func.id == "dict")
            if is_read:
                reads += 1
                return guards() + [item]
            if is_result:
                results += 1
                return [item] + guards()
            return self.generic_visit(item)

    node = Add().visit(node)
    require(reads == 3 and results == 1, "FOUR_EXPLICIT_COST_SITES")

    class Undo(ast.NodeTransformer):
        def visit(self, item):
            if hasattr(item, "_budget_added"):
                return None
            return super().visit(item)

    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
        "ALL_ORIGINAL_SAMPLE_STATEMENTS_RETAINED")
    namespace = dict(vars(original))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
        ORIGINAL_PIN["path"], "exec"), namespace)
    return namespace["sample"], dict(original_sample_AST_restored_exactly=True,
        original_native_collect_value_PID_status_close_and_final_budget_checks_retained=True,
        added_cost_sites=4, additional_clock_reads_only=True,
        extra_CPU_RAM_query_sampler_or_thread=False,
        original_maximum_sample_seconds=original.MAX_SAMPLE_SECONDS,
        original_maximum_total_seconds=original.MAX_TOTAL_SAMPLE_SECONDS,
        OS_call_hard_preemption_guaranteed=False,
        runtime_connection_qualified=False, PC_freeze_resolved=False)


def make_probe(raw):
    sample, proof = projection(raw)
    class Probe(BudgetMixin, original.Probe):
        pass
    Probe.sample = sample
    return Probe, proof
