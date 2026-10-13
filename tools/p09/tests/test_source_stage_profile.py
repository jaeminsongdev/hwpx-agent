import copy
import io
import json
import unittest
from unittest.mock import patch

import run_source_stage_profile as subject


class SourceStageProfileTests(unittest.TestCase):
    def numeric_profile(self):
        return {"schema_version": "hwpx-agent.p09-source-stage-timing/v1",
            "qualification": subject.QUALIFICATION, "actual_historical_inputs": 36,
            "unchanged_whole_meaning_graphs": 36, "inputs_with_formula_targets": 16,
            "formula_targets": 64, "source_cell_bindings": 128,
            "stages": {name: {"calls": 36, "total_us": 360000, "min_us": 10000, "max_us": 10000}
                for name in subject.STAGES}, "native_or_SQL_qualified": False,
            "product_complete": False, "P09_gate": "OPEN"}

    def binding(self):
        data = b"original complete consumer"
        pin = {"path": subject.EXAMPLE, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
        expected = {subject.EXAMPLE: pin, "crates/fixture/src/unchanged.rs":
            {"path": "crates/fixture/src/unchanged.rs", "bytes": 1, "sha256": "4"*64}}
        candidate = {"schema_version": "hwpx-agent.p09-source-stage-profile-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "preimage_archive": subject.ARCHIVE,
            "source_deltas": [dict(pin, bytes=pin["bytes"]+1, sha256="6"*64)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN,
            "files": [dict(pin, base64=subject.base64.b64encode(data).decode())]}
        return candidate, archive, expected

    def test_complete_numeric_profile_preserves_exact36_stages_and_non_authority(self):
        row = self.numeric_profile()
        self.assertEqual(subject.validate_profile(json.dumps(row)), row)
        self.assertFalse(row["native_or_SQL_qualified"])
        self.assertFalse(row["product_complete"])

    def test_profile_rejects_extra_raw_receipt_fields_and_qualification_upgrade(self):
        row = self.numeric_profile()
        for field, value in (("receipts", []), ("raw", "private"), ("qualification", "PASS"),
                ("schema_version", "other"), ("native_or_SQL_qualified", True),
                ("product_complete", True), ("P09_gate", "PASS")):
            with self.assertRaisesRegex(ValueError, "PROFILE_OUTPUT_SCOPE"):
                subject.validate_profile(json.dumps(dict(row, **{field: value})))

    def test_profile_rejects_partial_or_coerced_complete_corpus_counts(self):
        row = self.numeric_profile()
        for key in ("actual_historical_inputs", "unchanged_whole_meaning_graphs",
                "inputs_with_formula_targets", "source_cell_bindings"):
            for value in (row[key]-1, True, str(row[key]), float(row[key]), None):
                with self.assertRaisesRegex(ValueError, "PROFILE_COMPLETE_CORPUS_REQUIRED"):
                    subject.validate_profile(json.dumps(dict(row, **{key: value})))

    def test_profile_requires_all_eight_original_complete_stages(self):
        row = self.numeric_profile()
        missing = copy.deepcopy(row)
        del missing["stages"][next(iter(subject.STAGES))]
        extra = copy.deepcopy(row)
        extra["stages"]["unknown"] = {"calls": 36}
        for bad in (missing, extra):
            with self.assertRaisesRegex(ValueError, "PROFILE_STAGE_COVERAGE"):
                subject.validate_profile(json.dumps(bad))

    def test_profile_rejects_stage_bounds_coercions_missing_calls_and_formulas(self):
        row = self.numeric_profile()
        name = next(iter(subject.STAGES))
        for field, value in (("calls", 35), ("calls", True), ("total_us", -1),
                ("max_us", 200000000), ("min_us", 20000), ("total_us", 1), ("max_us", None)):
            bad = copy.deepcopy(row)
            bad["stages"][name][field] = value
            with self.assertRaisesRegex(ValueError, "PROFILE_NUMERIC_STAGE_BOUNDS"):
                subject.validate_profile(json.dumps(bad))
        for value in (0, True, "64", 100001):
            with self.assertRaisesRegex(ValueError, "PROFILE_FORMULA_COVERAGE"):
                subject.validate_profile(json.dumps(dict(row, formula_targets=value)))

    def test_profile_rejects_duplicate_json_keys_invalid_json_and_output_overflow(self):
        for output in ('{"schema_version":1,"schema_version":2}', '{', ' '*4097):
            with self.assertRaises(ValueError):
                subject.validate_profile(output)

    def test_declared_profile_changes_only_example_and_preserves_parent_sources(self):
        candidate, archive, expected = self.binding()
        result = subject.profile_sources(candidate, archive, expected)
        self.assertEqual(set(result), set(expected))
        self.assertEqual(result[subject.EXAMPLE], candidate["source_deltas"][0])
        self.assertEqual(result["crates/fixture/src/unchanged.rs"], expected["crates/fixture/src/unchanged.rs"])

    def test_declared_profile_rejects_foreign_scope_extra_delta_and_wrong_whole_preimages(self):
        candidate, archive, expected = self.binding()
        for field, value in (("parent_candidate_pin", {}), ("baseline_build_pin", {}),
                ("preimage_archive", "foreign"), ("qualification", "PASS")):
            with self.assertRaises(ValueError):
                subject.profile_sources(dict(candidate, **{field: value}), archive, expected)
        for deltas in ([], [expected[subject.EXAMPLE]], candidate["source_deltas"]+
                [expected["crates/fixture/src/unchanged.rs"]]):
            with self.assertRaises(ValueError):
                subject.profile_sources(dict(candidate, source_deltas=deltas), archive, expected)
        corrupt = copy.deepcopy(archive)
        corrupt["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for bad in (corrupt, dict(archive, files=[]), dict(archive, parent_candidate_pin={})):
            with self.assertRaises(ValueError):
                subject.profile_sources(candidate, bad, expected)

    def test_worker_only_adds_timing_flag_to_frozen_locked_single_job_test_profile(self):
        policy = copy.deepcopy(subject.maintenance.POLICY)
        calls = []
        def fake_call(arguments, **kwargs):
            calls.append((arguments, kwargs))
            return 0
        def fake_worker(task):
            self.assertEqual(task, subject.TASK)
            self.assertEqual(subject.maintenance.TASKS, {task: subject.ARGS})
            self.assertEqual(subject.maintenance.POLICY, policy)
            arguments = ["cargo", *subject.ARGS, "--locked", "--offline", "--jobs", "1",
                "--color=never", "--target-dir", str(subject.maintenance.TARGET)]
            kwargs = {"cwd": subject.maintenance.ROOT, "stdin": subject.subprocess.DEVNULL,
                "env": {"RUST_TEST_THREADS": "1"}}
            with self.assertRaisesRegex(ValueError, "PROFILE_WORKER_ARGUMENT_SCOPE"):
                subject.subprocess.call([*arguments, "--release"], **kwargs)
            return subject.subprocess.call(arguments, **kwargs)
        with patch.object(subject.maintenance, "worker", side_effect=fake_worker), \
                patch.object(subject.subprocess, "call", side_effect=fake_call):
            self.assertEqual(subject.run_worker(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][-2:], ["--", "--timing-only"])
        self.assertEqual(subject.maintenance.POLICY, policy)

    def test_failed_or_missing_profile_is_not_upgraded_to_runtime_or_SQL_success(self):
        for state in ("STOPPED_NOT_ACCEPTED", "PASS_SCOPED_NOT_GATE"):
            captured = io.StringIO()
            def fake_run(task, destination, seconds):
                json.dump({"task": task, "state": state, "stop_reason": "STOP_DURATION_LIMIT"}, captured)
                return 2
            with patch.object(subject.maintenance, "run", side_effect=fake_run):
                subject.run_owned("fixture", {}, 180)
            receipt = json.loads(captured.getvalue())
            self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")
            self.assertFalse(receipt["stage_profile_qualified"])
            self.assertFalse(receipt["signed_SQL_native_or_Gate_qualified"])
            self.assertEqual(receipt["baseline_build_qualification"], "HISTORICAL_R4_NOT_NEW_SQL_BUILD")
        for invalid in (29, 181, True, 180.0, None):
            with self.assertRaisesRegex(ValueError, "PROFILE_DURATION_SCOPE"):
                subject.run_owned("fixture", {}, invalid)
