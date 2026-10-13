"""P148 admission diagnostics only. No resource sampling, DB, Rust or native execution."""
import base64
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_formula_issuer_authority_sql_probe as driver
import verify_formula_issuer_authority_current as audit


class AuthorityAdmissionDiagnostics(unittest.TestCase):
    def resources(self, ram, cpu):
        return SimpleNamespace(samples=[{"available_ram_mib": r, "system_cpu_percent": c}
                                       for r, c in zip(ram, cpu, strict=True)])

    def test_admitted_original_result_is_unchanged(self):
        resources = self.resources([9000], [30])
        with patch.object(driver, "admit", return_value=3) as admit:
            self.assertEqual(driver.admit_or_explain(resources), 3)
            admit.assert_called_once_with(resources)

    def test_low_RAM_is_explained_without_starting_work(self):
        resources = self.resources([4200, 3072], [25, 36])
        with patch.object(driver, "admit", side_effect=ValueError("STOP_LOW_AVAILABLE_RAM")):
            with self.assertRaises(driver.AdmissionRefusal) as caught:
                driver.admit_or_explain(resources)
        self.assertEqual(str(caught.exception), "STOP_LOW_AVAILABLE_RAM")
        self.assertEqual(caught.exception.diagnostics["available_RAM_min_mib"], 3072)
        self.assertEqual(caught.exception.diagnostics["system_CPU_max_percent"], 36)
        self.assertIs(caught.exception.diagnostics["heavy_work_started"], False)

    def test_unstable_window_keeps_original_thresholds(self):
        resources = self.resources([8300, 7000, 8200], [25, 62, 30])
        with patch.object(driver, "admit", side_effect=ValueError("bootstrap_idle_window_not_admitted")):
            with self.assertRaises(driver.AdmissionRefusal) as caught:
                driver.admit_or_explain(resources)
        data = caught.exception.diagnostics
        self.assertEqual(data["samples"], 3)
        self.assertEqual(data["available_RAM_min_mib"], 7000)
        self.assertEqual(data["required_idle_RAM_min_mib"], 8192)
        self.assertEqual(data["required_idle_CPU_max_percent"], 50)
        self.assertEqual(data["required_consecutive_samples"], 3)
        self.assertEqual(data["maximum_admission_seconds"], 20)

    def test_arbitrary_error_and_resource_fields_are_not_disclosed(self):
        marker = "private_credential_ABC123"
        resources = self.resources([7000], [20])
        resources.samples[0]["private"] = marker
        with patch.object(driver, "admit", side_effect=ValueError(marker)):
            with self.assertRaises(driver.AdmissionRefusal) as caught:
                driver.admit_or_explain(resources)
        self.assertEqual(str(caught.exception), "redacted")
        self.assertNotIn(marker, json.dumps(caught.exception.diagnostics))
        self.assertNotIn("private", caught.exception.diagnostics)

    def test_whole_original_driver_retained_and_undeclared_change_rejected(self):
        path = driver.ROOT / "implementation/p09/source-archive/p09-148-pre-admission-diagnostics/source-preimages.v1.json"
        row = json.loads(path.read_text(encoding="utf-8"))["files"][0]
        original = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        current = (driver.ROOT / audit.DRIVER).read_text(encoding="utf-8")
        streaming_path = driver.ROOT / "implementation/p09/source-archive/p09-148-pre-streaming-progress/source-preimages.v1.json"
        streaming_row = json.loads(streaming_path.read_text(encoding="utf-8"))["files"][0]
        pre_streaming = base64.b64decode("".join(streaming_row["base64_chunks"]), validate=True)
        audit.authenticate_streaming_driver_delta(current, pre_streaming)
        audit.authenticate_admission_driver_delta(pre_streaming.decode("utf-8"), original)
        bad = current.replace('"container_memory_bytes": 536870912', '"container_memory_bytes": 1073741824', 1)
        self.assertNotEqual(bad, current)
        with self.assertRaises(ValueError):
            audit.authenticate_streaming_driver_delta(bad, pre_streaming)


if __name__ == "__main__":
    unittest.main()
