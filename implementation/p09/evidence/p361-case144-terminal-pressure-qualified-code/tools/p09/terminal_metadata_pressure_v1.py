"""Extend the existing 75% metadata warning to ALL original guard entry points.

동일 sampler의 마지막 표본만 O(1)로 확인한다. inventory/final force check에도
경고를 적용하며 원 hard guard, pacing, deadline, cleanup은 변경하지 않는다.
Published original guards and receipts remain immutable; this is opt-in only.
"""
import math
from types import SimpleNamespace as NS

SELF = "tools/p09/terminal_metadata_pressure_v1.py"
TEST = "tools/p09/tests/test_terminal_metadata_pressure_v1.py"
WARNING_PERCENT = 75


def require(ok, code):
    if not ok:
        raise ValueError("TERMINAL_METADATA_" + code)


def guard_type(original):
    class Guard(original):
        def __init__(self):
            super().__init__()
            self.terminal_pressure_checks = 0
            self.terminal_pressure_stops = 0
            self.terminal_pressure_latched = False

        def check(self, force=False):
            require(not self.terminal_pressure_latched, "STOP_LATCHED")
            # Original hard guard/sample/deadline errors always take precedence.
            result = super().check(force=force)
            require(type(self.samples) is list and bool(self.samples), "SAMPLE_MISSING")
            value = self.samples[-1].get("system_cpu_percent")
            require(type(value) in (int, float) and math.isfinite(value)
                    and 0 <= value <= 100, "SAMPLE_INVALID")
            self.terminal_pressure_checks += 1
            if value >= WARNING_PERCENT:
                self.terminal_pressure_stops += 1
                self.terminal_pressure_latched = True
                raise ValueError("STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK")
            return result

    return Guard


def runtime(original):
    Guard = guard_type(original.a.Guard)
    private = NS(**{**vars(original), "a": NS(**{**vars(original.a), "Guard": Guard})})
    return private, dict(all_original_guard_entry_points_covered=True,
                         original_guard_class_not_mutated=True,
                         warning_CPU_percent=WARNING_PERCENT,
                         original_hard_guard_and_sampling_first=True,
                         additional_sampler_or_thread_or_process=False,
                         cached_last_sample_only=True,
                         byte_read_or_source_or_final_hash_skipped=False,
                         original_cleanup_not_pressure_guarded=True)


def summary(guard):
    return dict(warning_CPU_percent=WARNING_PERCENT,
                checks=guard.terminal_pressure_checks,
                warning_stops=guard.terminal_pressure_stops,
                latched=guard.terminal_pressure_latched,
                all_guard_entry_points_including_inventory_and_final_force=True,
                additional_sampler_or_thread_or_process=False,
                original_hard_guard_and_cleanup_unchanged=True,
                automatic_retry_or_resume=False, PC_freeze_resolved=False)
