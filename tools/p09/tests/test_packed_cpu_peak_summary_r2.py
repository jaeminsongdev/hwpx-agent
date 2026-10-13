"""P224 진단 요약 계약. synthetic 숫자만 사용하고 제품/원장 재실행 없음."""
import math
import unittest
import review_packed_cpu_peak_r2 as m


def row(cpu, **extra):
    return dict(system_cpu_percent=cpu, **extra)


class Summary(unittest.TestCase):
    def test_missing_job_remains_unknown(self):
        result = m.summarize([row(100)])
        self.assertIsNone(result['job_CPU_max_at_warning'])
        self.assertEqual(result['job_CPU_samples_at_warning'], 0)
        self.assertFalse(result['missing_value_reported_as_zero'])

    def test_observed_zero_is_not_missing(self):
        result = m.summarize([row(100, owned_job_cpu_machine_percent=0.0)])
        self.assertEqual(result['job_CPU_max_at_warning'], 0.0)
        self.assertEqual(result['job_CPU_samples_at_warning'], 1)

    def test_two_hot_windows_and_job_presence(self):
        result = m.summarize([row(70), row(100, active_processes=1, owned_job_cpu_machine_percent=.4),
            row(100, active_processes=1, owned_job_cpu_machine_percent=.5), row(30)])
        self.assertEqual(result['maximum_consecutive98_samples'], 2)
        self.assertEqual(result['active_job_process_counts_at_warning'], {'1': 2})
        self.assertEqual(result['job_CPU_max_at_warning'], .5)

    def test_four_consecutive_not_dropped(self):
        result = m.summarize([row(98)] * 4)
        self.assertEqual(result['maximum_consecutive98_samples'], 4)
        self.assertEqual(result['samples_at_or_above98'], 4)

    def test_warning_and_emergency_counts_distinct(self):
        result = m.summarize([row(95, phase_at_sample='admission'), row(97), row(0), row(99)])
        self.assertEqual(result['samples_at_or_above95'], 3)
        self.assertEqual(result['samples_at_or_above98'], 1)
        self.assertEqual(result['warning_phase_counts']['admission'], 1)

    def test_numeric_neighbors_are_bounded_no_raw_fields(self):
        result = m.summarize([row(30, raw_secret='not_output'), row(100), row(40)] * 10)
        self.assertEqual(len(result['first_warning_numeric_neighbors']), 3)
        self.assertNotIn('raw_secret', result['first_warning_numeric_neighbors'][0])
        self.assertFalse(result['all_samples_or_raw_logs_output'])

    def test_invalid_cpu_values_closed(self):
        for value in (True, math.nan, math.inf, -1, 101, '100'):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                m.summarize([row(value)])

    def test_exact_sample_budget_closed(self):
        for values in ([], [row(0)] * 1441, None):
            with self.assertRaises(ValueError):
                m.summarize(values)


if __name__ == '__main__':
    unittest.main()
