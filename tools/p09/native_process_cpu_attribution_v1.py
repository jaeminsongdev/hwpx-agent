"""Opt-in native diagnostic successor; NO PDH/WMI/provider activation.

기존 K32 CPU/RAM 표본과8초/75% 스케줄, 같은 observer/thread만 사용한다.
GetProcessTimes PID+creation identity를 확인하고50ms/누적2초 원 비용 제한을
setup에도 적용한다. 보호된 process 및 DPC/IRQ는 unavailable, 0으로 위조하지
않는다. 기존 qualified PDH 코드·결과는 변경하지 않는다. Import != runtime.
"""
import math
import os
import threading
import time

import bounded_cpu_attribution_probe_v1 as native
import serial_observer_attribution as prior

SELF = "tools/p09/native_process_cpu_attribution_v1.py"
TEST = "tools/p09/tests/test_native_process_cpu_attribution_v1.py"
MAX_SAMPLE_SECONDS = .05
MAX_TOTAL_SECONDS = 2.0
MAX_QUERIES = 128


def require(ok, code):
    if not ok:
        raise ValueError("NATIVE_ATTRIBUTION_" + code)


class Probe:
    def __init__(self, processors, *, api=None, clock=time.monotonic,
                 identity=lambda: (os.getpid(), threading.get_ident())):
        require(type(processors) is int and 1 <= processors <= 64, "PROCESSORS")
        self.processors = processors; self.clock = clock; self.identity = identity
        self.owner = identity(); self.api = api if api is not None else native.Snapshot()
        self.previous = None; self.queries = 0; self.samples = 0
        self.maximum_latency = 0.; self.total_latency = 0.
        self.disabled_reason = None; self.cleanup = True
        self.previous = self.capture()  # Setup has SAME50ms/total2s budget.

    def capture(self):
        require(self.identity() == self.owner, "SAME_OBSERVER_OWNER")
        if self.disabled_reason:
            return None
        if self.queries >= MAX_QUERIES:
            self.disabled_reason = "QUERY_COUNT_BOUND"; self.close(); return None
        started = self.clock(); self.queries += 1
        try:
            result = self.api.capture()
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            self.disabled_reason = "NATIVE_PROCESS_QUERY_UNAVAILABLE"
            self.close(); return None
        elapsed = self.clock() - started
        require(math.isfinite(elapsed) and elapsed >= 0, "CLOCK")
        self.maximum_latency = max(self.maximum_latency, elapsed)
        self.total_latency += elapsed
        if elapsed > MAX_SAMPLE_SECONDS or self.total_latency > MAX_TOTAL_SECONDS:
            self.disabled_reason = "MEASUREMENT_COST_BUDGET_EXCEEDED"
            self.close(); return None  # No further queries or value publication.
        return result

    def sample(self, original_sample):
        require(self.identity() == self.owner, "SAME_OBSERVER_OWNER")
        if self.disabled_reason:
            return dict(available=False, reason=self.disabled_reason, values=None)
        current = self.capture(); self.samples += 1
        if current is None:
            return dict(available=False, reason=self.disabled_reason, values=None)
        old = self.previous; self.previous = current
        if old is None:
            return dict(available=False, reason="BASELINE_UNAVAILABLE", values=None)
        delta = native.compare(old, current, self.processors)
        values = dict(total_cpu=original_sample["system_cpu_percent"],
                      DPC_cpu=None, interrupt_cpu=None)
        for label, expected_role in (("MsMpEng", "msmpeng.exe"), ("System", "system")):
            matches = [row for row in current["rows"].values() if row["role"] == expected_role]
            row = matches[0] if len(matches) == 1 else None
            previous = old["rows"].get(row["pid"]) if row else None
            bound = bool(row and previous and row["creation"] == previous["creation"]
                         and (label != "System" or row["pid"] == 4)
                         and row["ticks"] >= previous["ticks"])
            cpu = (100 * (row["ticks"] - previous["ticks"]) / 10000000
                   / delta["window_seconds"] / self.processors) if bound else None
            if cpu is not None and not (math.isfinite(cpu) and 0 <= cpu <= 100):
                cpu = None; bound = False
            values[label] = dict(pid=row["pid"] if row else None,
                                 pid_stable=bound, creation_identity_bound=bound,
                                 machine_cpu_percent=cpu,
                                 status="OBSERVED" if bound else "UNAVAILABLE_OR_NEW_PID")
        return dict(available=True, coverage_complete=False, values=values,
                    process_deltas=delta, interval_seconds=delta["window_seconds"],
                    identical_to_original_K32_interval=False,
                    total_cpu_from_original_K32_not_a_second_query=True,
                    DPC_and_interrupt_counters_unavailable_not_zero=True,
                    PDH_or_WMI_called=False, causal_trigger_attribution_established=False,
                    added_wall_seconds=current["collection_seconds"],
                    OS_call_hard_preemption_guaranteed=False)

    def close(self):
        # Snapshot.capture closes each native handle before returning.
        self.previous = None; self.cleanup = True
        return True

    def summary(self):
        return dict(backend="NATIVE_TOOLHELP_PROCESS_TIMES_V1", query_calls=self.queries,
                    samples=self.samples, maximum_added_sample_seconds=self.maximum_latency,
                    total_added_sample_seconds=self.total_latency,
                    maximum_sample_budget_seconds=MAX_SAMPLE_SECONDS,
                    total_added_sample_budget_seconds=MAX_TOTAL_SECONDS,
                    setup_included_in_same_cost_budget=True, maximum_query_calls=MAX_QUERIES,
                    disabled_reason=self.disabled_reason, query_remaining=False,
                    cleanup_confirmed=self.cleanup, PDH_or_WMI_called=False,
                    original_CPU_RAM_guards_replaced=False,
                    second_sampler_thread_or_process=False,
                    DPC_and_interrupt_counters_unavailable_not_zero=True,
                    runtime_connection_qualified=False, PC_freeze_resolved=False)


def windows_type(original, objects, *, factory=Probe, clock=time.monotonic):
    class Windows(original):
        def __init__(self):
            super().__init__()
            self.attribution_probe = factory(self.processors)
            self.attribution_last = None; objects.append(self)

        def sample(self):
            before = self.last
            row = super().sample()  # Exact ORIGINAL K32 values and errors first.
            row["existing_system_time_breakdown"] = prior.split(before, self.last)
            now = clock()
            if (self.attribution_last is None or now - self.attribution_last >= prior.COLD_SECONDS
                    or row["system_cpu_percent"] >= prior.WARNING):
                diagnostic = self.attribution_probe.sample(row); self.attribution_last = now
                diagnostic["fresh_for_this_original_resource_sample"] = True
            else:
                diagnostic = dict(available=False, reason="NOT_SAMPLED_COLD_INTERVAL", values=None,
                                  fresh_for_this_original_resource_sample=False)
            row["serial_cpu_attribution"] = diagnostic
            return row
    return Windows


def close(objects):
    clean = True
    for window in objects:
        clean = window.attribution_probe.close() and clean
    return clean


def summary(objects):
    return dict(backend="NATIVE_TOOLHELP_PROCESS_TIMES_V1", existing_observer_instances=len(objects),
                cold_counter_interval_seconds=prior.COLD_SECONDS,
                original_warning_for_forced_read_percent=prior.WARNING,
                original_CPU_RAM_decisions_replaced=False,
                additional_PDH_queries_explicit=False,
                additional_native_process_queries_explicit=True,
                second_sampler_thread_or_process=False,
                interval_identical_to_K32_interval=False,
                probes=[window.attribution_probe.summary() for window in objects],
                runtime_connection_qualified=False, PC_freeze_resolved=False)
