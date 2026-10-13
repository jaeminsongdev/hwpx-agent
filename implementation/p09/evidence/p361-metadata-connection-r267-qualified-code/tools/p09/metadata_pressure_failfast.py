"""Opt-in metadata fail-fast; frozen qualified runners remain unchanged.

Reuse the owner's original hard guard and cached CPU sample. At the original
75% warning, permanently end this binding instead of entering cooling/resume.
No sampler, sleep, child, source cache, read skip or deadline extension. Cleanup
restores the exact original callback without consulting resource pressure.
"""
import math


def require(ok, code):
    if not ok:
        raise ValueError('METADATA_FAILFAST_' + code)


class Checkpoint:
    WARNING_PERCENT = 75

    def __init__(self, reader, owner):
        require(callable(reader.checkpoint) and callable(owner.checkpoint_io)
                and hasattr(owner, 'lock') and hasattr(owner, 'samples'), 'OWNER')
        self.reader = reader
        self.owner = owner
        self.original = reader.checkpoint
        self.hard = owner.checkpoint_io
        self.active = True
        self.latched = False
        self.checks = 0
        self.warning_stops = 0
        self.restored = False
        reader.checkpoint = self

    def __call__(self):
        require(self.active and self.reader.checkpoint is self, 'EXACT_BINDING')
        # No work, sampling or waiting may resume after a warning in this scope.
        require(not self.latched, 'STOP_LATCHED_METADATA_PRESSURE')
        self.hard()  # Original CPU/RAM/commit/deadline errors take precedence.
        self.checks += 1
        with self.owner.lock:
            require(bool(self.owner.samples), 'SAMPLE_MISSING')
            value = self.owner.samples[-1].get('system_cpu_percent')
        require(type(value) in (int, float) and math.isfinite(value)
                and 0 <= value <= 100, 'SAMPLE_INVALID')
        if value >= self.WARNING_PERCENT:
            self.latched = True
            self.warning_stops += 1
            raise ValueError('STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME')
        # Below the warning, retain the original complete reader checkpoint.
        self.original()

    def restore(self):
        if not self.active:
            return
        require(self.reader.checkpoint is self, 'RESTORE_EXACT_BINDING')
        self.reader.checkpoint = self.original
        self.active = False
        self.restored = self.reader.checkpoint is self.original

    def summary(self):
        return dict(warning_CPU_percent=self.WARNING_PERCENT, checks=self.checks,
                    warning_stops=self.warning_stops, latched=self.latched,
                    active=self.active, original_checkpoint_restored=self.restored,
                    original_hard_guard_first=True, original_cool_checkpoint_retained=True,
                    added_sampler_or_native_query=False, added_cooling_waits=0,
                    automatic_retry_or_resume=False, cleanup_guarded=False,
                    complete_source_reads_or_deadlines_weakened=False,
                    runtime_connection_qualified=False, PC_freeze_resolved=False)
