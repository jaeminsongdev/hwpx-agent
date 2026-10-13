import copy
import io
import json
import unittest
from unittest.mock import patch

import run_output_stage_profile as subject


class OutputStageProfileTests(unittest.TestCase):
    def binding(self):
        data = b"whole original output source"
        pin = {"path": subject.SOURCE, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
        expected = {subject.SOURCE: pin, "unchanged.rs": {"path": "unchanged.rs", "bytes": 1, "sha256": "3"*64}}
        candidate = {"schema_version": "hwpx-agent.p09-output-stage-profile-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.previous.previous.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "preimage_archive": subject.ARCHIVE,
            "source_deltas": [dict(pin, bytes=pin["bytes"]+1, sha256="7"*64)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.previous.previous.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN,
            "files": [dict(pin, base64=subject.base64.b64encode(data).decode())]}
        return candidate, archive, expected

    def row(self):
        return {**subject.COUNTS, "schema_version": "hwpx-agent.p09-output-stage-timing/v1",
            "qualification": subject.QUALIFICATION, "native_or_SQL_qualified": False,
            "lowered_candidates": 10, "mathematically_unchanged": 6,
            "product_complete": False, "P09_gate": "OPEN", "stages":
            {name: {"calls": calls, "total_us": calls*10, "min_us": 10, "max_us": 10}
                for name in subject.STAGES for calls in [16 if name in {"fresh_source_reconstruction", "bind_and_pre_verify", "edits_and_protection"}
                    else (6 if name == "noop_fresh_source_verify" else 10)]}}

    def output(self, row=None):
        return "running 1 test\ntest " + subject.NAME + " ... ok\n\nP149_OUTPUT_STAGE_PROFILE=" + \
            json.dumps(self.row() if row is None else row) + \
            "\ntest result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 56 filtered out; finished in 1.00s\n"

    def test_exact_source_delta_retains_unchanged_parent(self):
        candidate, archive, expected = self.binding()
        actual = subject.declared_sources(candidate, archive, expected)
        self.assertEqual(actual["unchanged.rs"], expected["unchanged.rs"])
        self.assertEqual(actual[subject.SOURCE], candidate["source_deltas"][0])
        self.assertEqual(set(actual), set(expected))

    def test_rejects_foreign_parent_or_extra_delta(self):
        candidate, archive, expected = self.binding()
        for key, value in (("parent_candidate_pin", {}), ("baseline_build_pin", {}),
                ("qualification", "PASS"), ("preimage_archive", "foreign"),
                ("source_deltas", []), ("source_deltas", [expected[subject.SOURCE]]),
                ("source_deltas", candidate["source_deltas"]+[expected["unchanged.rs"]])):
            with self.assertRaises(ValueError):
                subject.declared_sources(dict(candidate, **{key: value}), archive, expected)

    def test_rejects_corrupt_or_partial_whole_source_preimage(self):
        candidate, archive, expected = self.binding()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for changed in (bad, dict(archive, files=[]), dict(archive, parent_candidate_pin={}),
                dict(archive, files=archive["files"]*2)):
            with self.assertRaises(ValueError):
                subject.declared_sources(candidate, changed, expected)

    def test_complete36_original16_changed_and_nine_stages_required(self):
        actual, filtered = subject.validate_output(self.output())
        self.assertEqual(filtered, 56)
        self.assertEqual(actual, self.row())
        for key in subject.COUNTS:
            for value in (True, 0, subject.COUNTS[key]-1):
                with self.assertRaises(ValueError):
                    subject.validate_output(self.output(dict(self.row(), **{key: value})))

    def test_rejects_missing_duplicate_foreign_ignored_and_bad_numeric_payload(self):
        text = self.output()
        bad_stage = copy.deepcopy(self.row())
        bad_stage["stages"][next(iter(subject.STAGES))]["calls"] = 15
        for bad in (text.replace(subject.NAME, "foreign::test"), text.replace("0 ignored", "1 ignored"),
                text.replace("1 passed", "0 passed"), text.replace("running 1 test", "running 2 test"),
                text + text, self.output(bad_stage), self.output(dict(self.row(), stages={})),
                self.output(dict(self.row(), extra="private")), self.output(dict(self.row(), P09_gate="PASS")),
                text.replace('"original_inputs": 36', '"original_inputs": 36, "original_inputs": 36'),
                " "*32769):
            with self.assertRaises(ValueError):
                subject.validate_output(bad)

    def test_worker_adds_only_exact_profile_and_show_output(self):
        policy = copy.deepcopy(subject.maintenance.POLICY)
        calls = []
        def worker(task):
            self.assertEqual(task, subject.TASK)
            args = ["cargo", *subject.ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
                "--target-dir", str(subject.maintenance.TARGET), "--", "--test-threads=1"]
            kwargs = {"cwd": subject.maintenance.ROOT, "stdin": subject.subprocess.DEVNULL,
                "env": {"RUST_TEST_THREADS": "1"}}
            with self.assertRaisesRegex(ValueError, "OUTPUT_PROFILE_WORKER_ARGUMENT_SCOPE"):
                subject.subprocess.call(args+['--ignored'], **kwargs)
            return subject.subprocess.call(args, **kwargs)
        def call(args, **kwargs):
            calls.append(args)
            return 0
        with patch.object(subject.maintenance, "worker", side_effect=worker), \
                patch.object(subject.subprocess, "call", side_effect=call):
            self.assertEqual(subject.run_worker(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-5:], ["--", subject.NAME, "--exact", "--show-output", "--test-threads=1"])
        self.assertEqual(subject.maintenance.POLICY, policy)

    def test_missing_profile_result_never_becomes_pass(self):
        captured = io.StringIO()
        def run(task, destination, seconds):
            json.dump({"task": task, "state": "PASS_SCOPED_NOT_GATE", "tests_passed": 1}, captured)
            return 0
        with patch.object(subject.maintenance, "run", side_effect=run):
            subject.run_owned("fixture", {}, (), (), subject.TASK, 180)
        row = json.loads(captured.getvalue())
        self.assertEqual(row["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(row["stop_reason"], "OUTPUT_PROFILE_RESULT_MISSING")
        self.assertFalse(row["whole_library_qualified"])
        self.assertFalse(row["stage_profile_qualified"])

    def test_parent_full_target_keeps_names_duration_and_failure(self):
        captured = io.StringIO()
        names, modules = ["one", "two"], ["bound.rs"]
        def run(destination, expected, actual_names, actual_modules, task, seconds):
            self.assertEqual((actual_names, actual_modules, task, seconds), (names, modules, "stored-form-tests", 1200))
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "stop_reason": "STOP_DURATION_LIMIT"}, captured)
            return 2
        with patch.object(subject.previous, "run_owned", side_effect=run):
            self.assertEqual(subject.run_owned("fixture", {}, names, modules, "stored-form-tests", 1200), 2)
        self.assertEqual(json.loads(captured.getvalue())["state"], "STOPPED_NOT_ACCEPTED")
        with self.assertRaises(ValueError):
            subject.run_owned("fixture", {}, (), (), subject.TASK, 181)

    def test_profile_never_claims_CPU_speedup_SQL_native_or_gate(self):
        row = subject.annotate({"task": subject.TASK}, subject.TASK)
        self.assertEqual(row["P09_gate"], "OPEN")
        for key in ("product_complete", "signed_SQL_native_or_Gate_qualified", "PC_freeze_resolved", "statistical_speedup_proven", "exact_CPU_profiler"):
            self.assertFalse(row[key])
        with self.assertRaises(ValueError):
            subject.annotate({"task": "foreign"}, subject.TASK)

    def test_product_view_requires_exact_test_gates_and_private_modules(self):
        body = "fn old_product() {\n"
        statements = ["let mut timer = stage_profile::Timer::new();", *(
            f'timer.record("{stage}");' for stage in sorted(subject.STAGES - {
                "fresh_source_reconstruction", "export_verified_candidate", "noop_fresh_source_verify"}))]
        instrumented = body + "".join("        #[cfg(test)]\n        " + s + "\n" for s in statements) + "}\n\n"
        instrumented += "// Private test-only observation. No product API, callback, receipt change or cache.\n"
        instrumented += '#[cfg(test)]\n#[path = "../../../../../tests/support/document_import_settings_inputs.rs"]\nmod output_profile_inputs;\n'
        instrumented += "#[cfg(test)]\nmod stage_profile {}\n#[derive(Debug, Error, Eq, PartialEq)]\nenum OldError {}\n"
        self.assertEqual(subject.product_view(instrumented), body + "}\n#[derive(Debug, Error, Eq, PartialEq)]\nenum OldError {}\n")
        with self.assertRaises(ValueError):
            subject.product_view(instrumented.replace("        #[cfg(test)]\n", "", 1))
        with self.assertRaises(ValueError):
            subject.product_view(instrumented.replace("#[cfg(test)]\nmod stage_profile", "mod stage_profile"))

    def test_actual_original_worker_builds_the_closed_test_arguments(self):
        from types import SimpleNamespace
        class Kernel:
            def GetCurrentProcess(self):
                return 1
            def IsProcessInJob(self, process, job, member):
                member._obj.value = True
                return True
        calls = []
        def call(args, **kwargs):
            calls.append((args, kwargs))
            return 0
        with patch.object(subject.maintenance, "Windows", return_value=SimpleNamespace(k=Kernel())), \
                patch.object(subject.maintenance.sys, "stdin", io.StringIO("P149_GO\n")), \
                patch.object(subject.maintenance.shutil, "which", return_value="cargo"), \
                patch.object(subject.subprocess, "call", side_effect=call):
            self.assertEqual(subject.run_worker(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][-5:], ["--", subject.NAME, "--exact", "--show-output", "--test-threads=1"])
        self.assertEqual(calls[0][1]["env"]["RUST_TEST_THREADS"], "1")
        self.assertEqual(calls[0][1]["env"]["CARGO_BUILD_JOBS"], "1")

    def test_numeric_derivatives_keep_both_noop_and_lowered_complete_branches(self):
        for lowered, unchanged in ((0, 16), (16, 0), (10, 5), (True, 15), (10, True)):
            with self.assertRaises(ValueError):
                subject.validate_output(self.output(dict(self.row(), lowered_candidates=lowered, mathematically_unchanged=unchanged)))
        missing = copy.deepcopy(self.row())
        del missing["stages"]["noop_fresh_source_verify"]
        with self.assertRaises(ValueError):
            subject.validate_output(self.output(missing))
