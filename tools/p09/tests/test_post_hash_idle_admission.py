"""Pure fake-sampler checks. Does not sample Windows resources or execute heavy processes."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from idle_resource_admission import IdleResources


class PostHashIdle(unittest.TestCase):
    def fixture(self, cpus, stopped=False):
        value = object.__new__(IdleResources)
        value.reason = "STOP_SUSTAINED_SYSTEM_CPU" if stopped else None
        value.stop = SimpleNamespace(is_set=lambda: stopped)
        value.thread = SimpleNamespace(start=lambda: setattr(value, "started", True))
        value.started = False
        iterator = iter(cpus)
        value.sample = lambda: {"system_cpu_percent": next(iterator), "available_ram_mib": 16000}
        return value

    def run_start(self, value):
        with patch("idle_resource_admission.time.sleep"), patch("idle_resource_admission.time.monotonic", side_effect=range(100)):
            value.start()

    def test_requires_three_stable_samples(self):
        value = self.fixture([20, 30, 40])
        self.run_start(value)
        self.assertTrue(value.started)

    def test_pressure_after_hash_resets_then_requires_fresh_window(self):
        value = self.fixture([60, 20, 20, 51, 30, 30, 30])
        self.run_start(value)
        self.assertTrue(value.started)

    def test_sustained_pressure_denies_before_thread_or_process_start(self):
        value = self.fixture([70] * 100)
        with self.assertRaisesRegex(ValueError, "post_hash_idle_window_not_admitted"):
            self.run_start(value)
        self.assertFalse(value.started)

    def test_original_stop_guard_is_not_reset(self):
        value = self.fixture([20], stopped=True)
        with self.assertRaisesRegex(ValueError, "STOP_SUSTAINED_SYSTEM_CPU"):
            self.run_start(value)
        self.assertFalse(value.started)


if __name__ == "__main__":
    unittest.main()
