from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.p09 import qualify_native_form_diagnostic_batch as q


class DiagnosticNativeBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = q.previous.verified_traces()
        cls.manifest = q.q.shared.lifecycle.checked_json(q.ROOT / q.MANIFEST, q.MANIFEST_SHA)
        # Actual new public file reader, OLD files only. No new native traces.
        cls.readback = q.rust_observations(q.previous.PREFIX)
        cls.component = {"cases": cls.readback["cases"][:6]}
        cls.component_records = [
            (row, path, trace, passed)
            for row, (_, path, trace, passed) in zip(cls.manifest["cases"][:6], cls.old, strict=True)
        ]

    def test_six_real_traces_keep_four_passes_two_failures_ten_sessions(self):
        for row, _, trace, passed in self.old:
            self.assertIs(q.verify_case_trace(trace, row), passed)
        self.assertEqual(q.session_inventory(self.old, 6), {
            "case_count": 6, "owned_session_count": 10, "passed_lifecycle_cases": 4,
            "failed_first_open_cases": 2, "all_cases_sequential": True,
            "all_owned_process_ids_unique": True,
        })

    def test_no_old_trace_matches_any_of_the_fifteen_new_inputs(self):
        for _, _, trace, _ in self.old:
            for row in self.manifest["cases"]:
                with self.subTest(case=row["case_id"]), self.assertRaises(ValueError):
                    q.verify_case_trace(trace, row)

    def test_utc_is_exact_including_seventh_fractional_digit(self):
        self.assertLess(q.utc("2026-10-02T01:02:03.0000001Z"), q.utc("2026-10-02T01:02:03.0000002+00:00"))
        self.assertEqual(q.utc("2026-10-02T01:02:03Z"), q.utc("2026-10-02T01:02:03.0000000+00:00"))
        for bad in (None, 1, "2026-02-30T00:00:00Z", "2026-10-02T01:02:03", "2026-10-02T01:02:03+09:00",
                    "2026-10-02 01:02:03Z", "2026-10-02T01:02:03.12345678Z", "2026-10-02T01:02:60Z"):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                q.utc(bad)

    def test_reversed_trace_time_rejects_even_one_hundred_nanoseconds(self):
        row, _, trace, _ = self.old[0]
        bad = copy.deepcopy(trace)
        bad["started_at_utc"] = "2026-10-02T01:02:03.0000002Z"
        bad["completed_at_utc"] = "2026-10-02T01:02:03.0000001Z"
        with self.assertRaisesRegex(ValueError, "diagnostic_trace_time_order_invalid"):
            q.verify_case_trace(bad, row)

    def test_trace_top_level_missing_extra_and_duplicate_fields_reject(self):
        row, _, trace, _ = self.old[0]
        for key in q.TRACE_KEYS:
            bad = copy.deepcopy(trace); del bad[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                q.verify_case_trace(bad, row)
        bad = copy.deepcopy(trace); bad["unchecked_claim"] = True
        with self.assertRaises(ValueError):
            q.verify_case_trace(bad, row)
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            json.loads('{"state":"pass","state":"fail"}', object_pairs_hook=q.q.shared.lifecycle.duplicate_guard)

    def test_nested_session_and_process_shape_is_closed(self):
        row, _, trace, _ = self.old[0]
        for location in ("session", "process"):
            keys = trace["sessions"][0] if location == "session" else trace["sessions"][0]["process"]
            for key in (*keys, "unchecked_claim"):
                bad = copy.deepcopy(trace)
                item = bad["sessions"][0] if location == "session" else bad["sessions"][0]["process"]
                if key == "unchecked_claim": item[key] = True
                else: del item[key]
                with self.subTest(location=location, key=key), self.assertRaises(ValueError):
                    q.verify_case_trace(bad, row)
        for sessions in (None, [], [None], ["session"], [{"process": {}}]):
            bad = copy.deepcopy(trace); bad["sessions"] = sessions
            with self.subTest(sessions=sessions), self.assertRaises(ValueError):
                q.verify_case_trace(bad, row)

    def test_trace_input_artifact_sizes_are_strict_and_bounded(self):
        row, _, trace, _ = self.old[0]
        for key in ("input_bytes", *(item[1] for item in q.ARTIFACTS.values())):
            for value in (True, 0, -1, "123", 33 * 1024 * 1024):
                bad = copy.deepcopy(trace); bad[key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    q.verify_case_trace(bad, row)
        for value in (True, 0, "123", 4 * 1024 * 1024 + 1):
            bad_row = copy.deepcopy(row); bad_row["package_bytes"] = value
            with self.assertRaises(ValueError): q.verify_case_trace(trace, bad_row)

    def test_actual_target_executable_module_and_privacy_stay_locked(self):
        row, _, trace, _ = self.old[0]
        changes = [
            ("target", "build", "11.0.0.0000"), ("target", "prog_id", "HWPFrame.HwpObject"),
            ("security_module", "sha256", "0" * 64), ("security_module", "preflight_state", "not_run"),
        ]
        for group, key, value in changes:
            bad = copy.deepcopy(trace); bad[group][key] = value
            with self.subTest(group=group, key=key), self.assertRaises(ValueError): q.verify_case_trace(bad, row)
        for key in q.q.shared.PRIVACY_KEYS:
            for value in (True, 0):
                bad = copy.deepcopy(trace); bad[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): q.verify_case_trace(bad, row)
        for key, value in (("executable_sha256", "0" * 64), ("command_line_sha256", "invalid"),
                           ("session_id", True), ("session_id", -1), ("process_id", True), ("process_id", 0)):
            bad = copy.deepcopy(trace); bad["sessions"][0]["process"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): q.verify_case_trace(bad, row)

    def test_partial_lifecycle_and_coerced_boolean_claims_reject(self):
        row, _, trace, _ = self.old[0]
        for key, value in ((*[(k, "not_run") for k in q.q.shared.lifecycle.LIFECYCLE_KEYS],
                           ("quit_invoked", 1), ("remaining_hwp_process_count", False), ("error_code", "ignored"))):
            bad = copy.deepcopy(trace); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): q.verify_case_trace(bad, row)
        bad = copy.deepcopy(trace); bad["sessions"][0]["register_module_return"] = 0
        with self.assertRaises(ValueError): q.verify_case_trace(bad, row)

    def test_first_open_failures_cannot_claim_outputs_or_pass(self):
        row, _, trace, _ = self.old[4]
        for key in (k for pair in q.ARTIFACTS.values() for k in pair[:2]):
            bad = copy.deepcopy(trace); bad[key] = "0" * 64 if key.endswith("sha256") else 1
            with self.subTest(key=key), self.assertRaises(ValueError): q.verify_case_trace(bad, row)
        for key, value in (("failed_phase", "first_save"), ("state", "pass"), ("quit_invoked", True),
                           ("first_open", "pass"), ("remaining_hwp_process_count", 1)):
            bad = copy.deepcopy(trace); bad[key] = value
            with self.assertRaises(ValueError): q.verify_case_trace(bad, row)

    def test_session_batch_reuse_windows_session_and_overlap_reject(self):
        bad = copy.deepcopy(self.old)
        bad[1][2]["sessions"][0]["process"]["process_id"] = bad[0][2]["sessions"][0]["process"]["process_id"]
        with self.assertRaisesRegex(ValueError, "diagnostic_all_sessions_not_independent"): q.session_inventory(bad, 6)
        bad = copy.deepcopy(self.old); bad[5][2]["sessions"][0]["process"]["session_id"] += 1
        with self.assertRaises(ValueError): q.session_inventory(bad, 6)
        bad = copy.deepcopy(self.old); bad[1][2]["started_at_utc"] = bad[0][2]["started_at_utc"]
        with self.assertRaisesRegex(ValueError, "diagnostic_cases_not_sequential"): q.session_inventory(bad, 6)
        bad = copy.deepcopy(self.old); bad[1][0]["case_id"] = bad[0][0]["case_id"]
        with self.assertRaises(ValueError): q.session_inventory(bad, 6)

    def test_batch_counts_and_lifecycle_types_reject(self):
        for records, count in ((self.old[:-1], 6), (self.old, 15), (self.old, True), ([], 0)):
            with self.assertRaises(ValueError): q.session_inventory(records, count)
        bad = list(self.old); row, path, trace, _ = bad[0]; bad[0] = (row, path, trace, 1)
        with self.assertRaises(ValueError): q.session_inventory(bad, 6)

    def test_batch_overlap_cannot_hide_in_datetime_microsecond_truncation(self):
        bad = copy.deepcopy(self.old[:2])
        bad[0][2]["started_at_utc"] = "2026-10-02T01:02:03.0000000Z"
        bad[0][2]["completed_at_utc"] = "2026-10-02T01:02:03.0000002Z"
        bad[1][2]["started_at_utc"] = "2026-10-02T01:02:03.0000001Z"
        bad[1][2]["completed_at_utc"] = "2026-10-02T01:02:03.0000003Z"
        with self.assertRaisesRegex(ValueError, "diagnostic_cases_not_sequential"):
            q.session_inventory(bad, 2)

    def test_all_six_exact_real_artifact_directories_have_22_files(self):
        total = 0
        for _, path, trace, passed in self.old:
            value = q.artifact_snapshot(path, trace, passed)
            self.assertEqual(set(value), set(q.ARTIFACTS) if passed else set())
            total += 1 + len(value)
        self.assertEqual(total, 22)

    def copied_attempt(self, temp, index=0):
        _, path, trace, passed = self.old[index]
        directory = Path(temp) / "attempt"
        shutil.copytree(path, directory)
        return directory, copy.deepcopy(trace), passed

    def test_missing_extra_artifacts_and_trace_replacement_reject(self):
        for mutation in ("missing", "extra", "trace"):
            with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
                directory, trace, passed = self.copied_attempt(temp)
                if mutation == "missing": (directory / "reopened.hwpx").unlink()
                elif mutation == "extra": (directory / "unchecked.bin").write_bytes(b"extra")
                else: trace["input_bytes"] += 1
                with self.subTest(mutation=mutation), self.assertRaises(ValueError): q.artifact_snapshot(directory, trace, passed)
        with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
            directory, trace, passed = self.copied_attempt(temp, 4)
            (directory / "saved.hwpx").write_bytes(b"unclaimed")
            with self.assertRaises(ValueError): q.artifact_snapshot(directory, trace, passed)

    def test_actual_hwpx_and_pdf_byte_drift_reject(self):
        for name in q.ARTIFACTS:
            with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
                directory, trace, passed = self.copied_attempt(temp)
                path = directory / name; path.write_bytes(path.read_bytes() + b"changed")
                with self.subTest(name=name), self.assertRaises(ValueError): q.artifact_snapshot(directory, trace, passed)

    def test_rehashed_pdf_without_real_signature_still_rejects(self):
        with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
            directory, trace, passed = self.copied_attempt(temp)
            path = directory / "saved.pdf"; raw = b"XXXXX" + path.read_bytes()[5:]; path.write_bytes(raw)
            trace["pdf_sha256"] = q.q.sha(raw)
            (directory / "target-trace.json").write_text(json.dumps(trace), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "diagnostic_native_pdf_signature_invalid"):
                q.artifact_snapshot(directory, trace, passed)

    def test_actual_linked_directory_and_linked_file_parent_reject(self):
        with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
            directory, trace, passed = self.copied_attempt(temp)
            link = Path(temp) / "linked-attempt"
            if os.name == "nt":
                # Junctions need no privilege/trust change; both endpoints are
                # explicit disposable directories in this one test workspace.
                script = "New-Item -ItemType Junction -Path '{}' -Target '{}' | Out-Null".format(
                    str(link).replace("'", "''"), str(directory).replace("'", "''"))
                result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                                        capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                self.assertEqual(result.returncode, 0, "disposable junction creation failed")
                self.assertTrue(link.is_junction())
            else:
                link.symlink_to(directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "linked_evidence_rejected"):
                q.artifact_snapshot(link, trace, passed)
            with self.assertRaises(ValueError):
                q.public.bounded_bytes(link / "saved.hwpx", 4 * 1024 * 1024)

    def test_evidence_boundary_and_boolean_lifecycle_reject(self):
        with self.assertRaises((ValueError, OSError)):
            q.q.shared.within(q.ROOT / "implementation/p09", q.ROOT / "fixtures/target-build")
        with self.assertRaises(ValueError): q.artifact_snapshot(self.old[0][1], self.old[0][2], 1)

    def test_source_snapshot_detects_changed_component_source_in_disposable_root(self):
        with tempfile.TemporaryDirectory(prefix="p09-36-test-") as temp:
            root = Path(temp)
            for relative in q.SOURCES:
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(q.public.bounded_bytes(q.ROOT / relative, 2 * 1024 * 1024))
            before = q.own_sources(root)
            self.assertEqual(before, q.own_sources())
            path = root / q.SOURCES[0]; path.write_bytes(path.read_bytes() + b"\n# changed test copy\n")
            self.assertNotEqual(before, q.own_sources(root))

    def test_prefix_inventory_and_missing_whole_batch_fail_closed(self):
        for prefix in ("../escape", "C:\\private", "UPPER", "", "a" * 41, None):
            with self.assertRaises(ValueError): q.attempt_paths(prefix)
        paths = q.attempt_paths("p09-35-not-dispatched")
        self.assertEqual(len(paths), 15); self.assertEqual(len(set(paths)), 15)
        self.assertTrue(all(not path.exists() for path in paths))
        with self.assertRaises((ValueError, OSError)):
            q.traces(self.manifest, "p09-35-not-dispatched")

    def test_real_file_reader_component_binds_old_artifacts_not_new_inputs(self):
        q.verify_rust(self.component, self.component_records)
        for result, (_, _, trace, passed) in zip(self.component["cases"], self.old, strict=True):
            for stage, digest_key in (("saved", "output_sha256"), ("reopened", "reopened_sha256")):
                if passed: self.assertEqual(result[stage]["package_sha256"], trace[digest_key])
                else: self.assertEqual(result[stage], q.MISSING)
        with self.assertRaises(ValueError):
            q.verify_case_trace(self.component_records[0][2], self.component_records[0][0])

    def test_readback_hash_size_shape_and_case_substitution_reject(self):
        for key, value in (("package_sha256", "0" * 64), ("package_bytes", True), ("green_rows", 1)):
            bad = copy.deepcopy(self.component); bad["cases"][0]["saved"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)
        for mutation in ("short", "reverse", "extra"):
            bad = copy.deepcopy(self.component)
            if mutation == "short": bad["cases"].pop()
            elif mutation == "reverse": bad["cases"].reverse()
            else: bad["cases"][0]["extra"] = 1
            with self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)
        for value in ([], None, {}, {"cases": [None] * 6}):
            with self.assertRaises(ValueError): q.verify_rust(value, self.component_records)
        bad = copy.deepcopy(self.component); bad["cases"][0]["saved"] = None
        with self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)

    def test_real_typed_hash_equality_flags_cannot_be_forged(self):
        indices = [i for i, row in enumerate(self.component["cases"]) if row["saved"].get("complete_public_reader") == "pass"]
        self.assertTrue(indices, "need actual historical artifact typed readback, not fabricated pass")
        for index in indices:
            for key in ("complete_target_state_exact", "target_control_fingerprints_exact", "document_flow_exact"):
                bad = copy.deepcopy(self.component); item = bad["cases"][index]["saved"]; item[key] = not item[key]
                with self.subTest(key=key), self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)
            for key, value in (("complete_package_bindings_exact", 0), ("target_controls_sha256", []), ("target_state_sha256", "invalid")):
                bad = copy.deepcopy(self.component); bad["cases"][index]["saved"][key] = value
                with self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)

    def test_failed_native_missing_outputs_and_reader_failures_stay_non_green(self):
        failed = self.component["cases"][0]["saved"]
        self.assertEqual(failed["complete_public_reader_or_policy_binding"], "fail")
        self.assertEqual(failed["green_rows"], 0)
        bad = copy.deepcopy(self.component); bad["cases"][4]["saved"] = copy.deepcopy(failed)
        with self.assertRaisesRegex(ValueError, "diagnostic_missing_native_stage_promoted"):
            q.verify_rust(bad, self.component_records)
        bad = copy.deepcopy(self.component); bad["cases"][0]["saved"]["complete_public_reader_or_policy_binding"] = "pass"
        with self.assertRaises(ValueError): q.verify_rust(bad, self.component_records)

    def test_full_preflight_reproduces_preparation_without_native_promotion(self):
        value = q.preflight()
        self.assertEqual(value["source_sha256"], q.own_sources())
        self.assertEqual(len(value["historical_trace_and_artifact_sha256"]), 22)
        self.assertEqual(value["prepared_case_count"], 15)
        self.assertEqual(value["new_native_batch"], {"state": "not_run", "cases": 15, "stages": 30})
        self.assertFalse(value["claims"]["historical_reverification_is_new_batch_proof"])
        self.assertFalse(value["claims"]["new_native_target_execution"])
        self.assertFalse(value["claims"]["p09_complete"])
        self.assertEqual(value["claims"]["green_rows"], 0)
        self.assertFalse(value["privacy"]["native_session_started"])
        self.assertFalse(value["privacy"]["trust_or_registry_changed"])
        raw = q.q.shared.lifecycle.canonical_bytes(value)
        self.assertNotIn(b"C:\\", raw); self.assertNotIn(b"D:\\", raw)


if __name__ == "__main__":
    unittest.main()
