import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import terminal_metadata_pressure_v1 as pressure


class Original:
    def __init__(self):
        self.samples = []
        self.calls = []
        self.value = 10
        self.error = None
        self.cleanup = False

    def check(self, force=False):
        self.calls.append(force)
        if self.error:
            raise ValueError(self.error)
        self.samples.append(dict(system_cpu_percent=self.value))
        return "original-result"

    def close(self):
        self.cleanup = True


class Tests(unittest.TestCase):
    def guard(self):
        return pressure.guard_type(Original)()

    def test_below_warning_original_return(self):
        g = self.guard()
        self.assertEqual(g.check(), "original-result")
        self.assertEqual(g.calls, [False])

    def test_exact_warning_latches(self):
        g = self.guard(); g.value = 75
        with self.assertRaisesRegex(ValueError, "STOP_TERMINAL_METADATA_WARNING"):
            g.check()
        self.assertTrue(g.terminal_pressure_latched)

    def test_force_final_check_covered(self):
        g = self.guard(); g.value = 100
        with self.assertRaisesRegex(ValueError, "STOP_TERMINAL_METADATA_WARNING"):
            g.check(force=True)
        self.assertEqual(g.calls, [True])

    def test_inventory_original_guard_entry_covered(self):
        g = self.guard(); g.value = 80
        reserve = g.check
        with self.assertRaisesRegex(ValueError, "STOP_TERMINAL_METADATA_WARNING"):
            reserve()

    def test_original_error_precedes_warning(self):
        g = self.guard(); g.value = 100; g.error = "ORIGINAL_RAM_STOP"
        with self.assertRaisesRegex(ValueError, "^ORIGINAL_RAM_STOP$"):
            g.check()
        self.assertEqual(g.terminal_pressure_checks, 0)

    def test_no_resume_after_latch(self):
        g = self.guard(); g.value = 90
        with self.assertRaises(ValueError): g.check()
        g.value = 0
        with self.assertRaisesRegex(ValueError, "STOP_LATCHED"): g.check()
        self.assertEqual(len(g.calls), 1)

    def test_cleanup_after_warning_unconditional(self):
        g = self.guard(); g.value = 100
        with self.assertRaises(ValueError): g.check()
        g.close()
        self.assertTrue(g.cleanup)
        self.assertIs(type(g).close, Original.close)

    def test_invalid_cpu_values_rejected(self):
        for value in (True, None, "100", float("nan"), float("inf"), -1, 101):
            with self.subTest(value=repr(value)):
                g = self.guard(); g.value = value
                with self.assertRaisesRegex(ValueError, "SAMPLE_INVALID"): g.check()

    def test_missing_sample_rejected(self):
        class Missing(Original):
            def check(self, force=False): return None
        with self.assertRaisesRegex(ValueError, "SAMPLE_MISSING"):
            pressure.guard_type(Missing)().check()

    def test_cached_sample_never_adds_sampler(self):
        class Cached(Original):
            def check(self, force=False): self.calls.append(force)
        g = pressure.guard_type(Cached)()
        g.samples = [dict(system_cpu_percent=40)]
        g.check(); g.check()
        self.assertEqual(len(g.samples), 1)
        self.assertEqual(g.calls, [False, False])

    def test_runtime_private_default_unchanged(self):
        api = NS(Guard=Original, token=object()); original = NS(a=api, untouched=object())
        private, proof = pressure.runtime(original)
        self.assertIs(original.a.Guard, Original)
        self.assertIs(private.a.token, api.token)
        self.assertIs(private.untouched, original.untouched)
        self.assertIsNot(private.a.Guard, Original)
        self.assertFalse(proof["additional_sampler_or_thread_or_process"])

    def test_summary_truthful_stops(self):
        g = self.guard(); g.check(); g.value = 100
        with self.assertRaises(ValueError): g.check()
        s = pressure.summary(g)
        self.assertEqual((s["checks"], s["warning_stops"], s["latched"]), (2, 1, True))
        self.assertFalse(s["PC_freeze_resolved"])


if __name__ == "__main__": unittest.main()
