"""Opt-in diagnostic work only at the original >=75% warning.

Cold observer samples no longer collect/format PDH just to discard idle values.
One baseline remains in the original Probe constructor. Both PID bindings,
seven original counters and 50ms/2s budgets remain unchanged. This is NOT
runtime integration, instantaneous attribution or a CPU-freeze fix.
"""
import math

import serial_observer_attribution as original
import conservative_maintenance as c

SELF = "tools/p09/warning_only_serial_attribution_v1.py"
TEST = "tools/p09/tests/test_warning_only_serial_attribution_v1.py"
WARNING = 75


def require(ok, code):
    if not ok:
        raise ValueError("WARNING_ONLY_ATTRIBUTION_" + code)


def windows_type(base, objects, *, factory, clock):
    """Caller supplies the already-qualified early-budget Probe factory.

No global class replacement and no new observer/sampler thread. The caller
must arrange ownership and close(objects) in its original cleanup finally.
"""
    require(callable(factory) and callable(clock) and type(objects) is list,
        "EXPLICIT_FACTORY_CLOCK_OWNER")
    class Windows(base):
        def __init__(self):
            super().__init__()
            self.attribution_probe = factory(self.processors)
            self.warning_only_checks = 0
            self.warning_only_reads = 0
            self.warning_only_cold_skips = 0
            self.warning_only_hard_skips = 0
            objects.append(self)

        def sample(self):
            before = self.last
            row = super().sample()  # Original error/value/CPU interval retained.
            row["existing_system_time_breakdown"] = original.split(before, self.last)
            self.warning_only_checks += 1
            cpu = row["system_cpu_percent"]
            require(type(cpu) in (int, float) and math.isfinite(cpu) and
                0 <= cpu <= 100, "ORIGINAL_CPU_VALUE")
            # Cheap original hard RAM/commit decisions BEFORE optional PDH.
            # Count-dependent CPU emergency is still made by the ORIGINAL guard.
            _, reason = c.decision(row, 0)
            if reason is not None:
                self.warning_only_hard_skips += 1
                diagnostic = dict(available=False, values=None,
                    reason="ORIGINAL_HARD_RESOURCE_ALREADY_STOPPING",
                    fresh_for_this_original_resource_sample=False)
            elif cpu >= WARNING:
                diagnostic = self.attribution_probe.sample()
                self.warning_only_reads += 1
                diagnostic["fresh_for_this_original_resource_sample"] = True
            else:
                self.warning_only_cold_skips += 1
                diagnostic = dict(available=False, values=None,
                    reason="NO_WARNING_NO_PDH_COLLECT_OR_FORMAT",
                    fresh_for_this_original_resource_sample=False)
            diagnostic.update(interval_alignment_exact=False,
                cold_sample_cached_values_reused=False,
                long_interval_relabelled_as_K32_half_second=False,
                causal_trigger_attribution_established=False)
            row["serial_cpu_attribution"] = diagnostic
            return row
    return Windows


def close(objects):
    return original.close(objects)


def summary(objects):
    return dict(existing_observer_instances=len(objects),
        original_warning_percent=WARNING, no_cold_PDH_collect_or_formatted_read=True,
        same_original_Probe_constructor_baseline_required=True,
        original_seven_counter_PID_binding_and_cost_budget_retained=True,
        original_K32_CPU_RAM_decisions_replaced=False,
        second_sampler_thread_or_process=False, runtime_connection_qualified=False,
        measured_Native_CPU_or_PC_freeze_improvement_proven=False,
        probes=[dict(window.attribution_probe.summary(),
            warning_only_checks=window.warning_only_checks,
            warning_only_reads=window.warning_only_reads,
            cold_skips=window.warning_only_cold_skips,
            hard_resource_skips=window.warning_only_hard_skips) for window in objects])
