"""Pure admission-policy checks; no process sampling or heavy workload execution."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_idle_resource_window as window


class IdleAdmission(unittest.TestCase):
    def sample(self, cpu=30, ram=16000):
        return {"system_cpu_percent": cpu, "available_ram_mib": ram}

    def test_three_consecutive_low_load_samples(self):
        count = 0
        for _ in range(window.REQUIRED):
            count = window.stable_count(count, self.sample())
        self.assertEqual(count, 3)

    def test_CPU_pressure_resets_window(self):
        self.assertEqual(window.stable_count(2, self.sample(cpu=51)), 0)

    def test_memory_pressure_resets_window(self):
        self.assertEqual(window.stable_count(2, self.sample(ram=8191)), 0)

    def test_exact_thresholds_are_admissible(self):
        self.assertEqual(window.stable_count(2, self.sample(cpu=50, ram=8192)), 3)

    def test_a_single_spike_prevents_early_admission(self):
        count = 0
        for cpu in (30, 30, 90, 20, 20):
            count = window.stable_count(count, self.sample(cpu=cpu))
        self.assertLess(count, window.REQUIRED)

    def test_admission_does_not_run_build_or_DB(self):
        source = Path(window.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "cargo ", "docker ", "HwpObject", "Start-Process"):
            self.assertFalse(forbidden in source)


if __name__ == "__main__":
    unittest.main()
