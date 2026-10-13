import copy
import io
import json
import unittest
from unittest.mock import patch

import run_readback_buffer_regression as subject


class ReadbackBufferTests(unittest.TestCase):
    def binding(self):
        data = b"whole original readback source"
        pin = {"path": subject.SOURCE, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
        expected = {subject.SOURCE: pin, "unchanged.rs": {"path": "unchanged.rs", "bytes": 1, "sha256": "3"*64}}
        candidate = {"schema_version": "hwpx-agent.p09-moved-readback-buffer-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.previous.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "preimage_archive": subject.ARCHIVE,
            "source_deltas": [dict(pin, bytes=pin["bytes"]+1, sha256="7"*64)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.previous.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN,
            "files": [dict(pin, base64=subject.base64.b64encode(data).decode())]}
        return candidate, archive, expected

    def output(self):
        return "running 4 tests\n" + "\n".join("test " + name + " ... ok" for name in sorted(subject.NAMES)) + \
            "\ntest result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 52 filtered out; finished in 1.00s\n"

    def test_exact_one_delta_preserves_unchanged_parent(self):
        candidate, archive, expected = self.binding()
        actual = subject.declared_sources(candidate, archive, expected)
        self.assertEqual(actual["unchanged.rs"], expected["unchanged.rs"])
        self.assertEqual(actual[subject.SOURCE], candidate["source_deltas"][0])
        self.assertEqual(set(actual), set(expected))

    def test_rejects_foreign_parent_scope_or_extra_delta(self):
        candidate, archive, expected = self.binding()
        for key, value in (("parent_candidate_pin", {}), ("baseline_build_pin", {}),
                ("qualification", "PASS"), ("preimage_archive", "foreign"),
                ("source_deltas", []), ("source_deltas", [expected[subject.SOURCE]]),
                ("source_deltas", candidate["source_deltas"]+[expected["unchanged.rs"]])):
            with self.assertRaises(ValueError):
                subject.declared_sources(dict(candidate, **{key: value}), archive, expected)

    def test_rejects_corrupt_partial_or_foreign_preimage(self):
        candidate, archive, expected = self.binding()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for changed in (bad, dict(archive, files=[]), dict(archive, parent_candidate_pin={}),
                dict(archive, files=archive["files"]*2)):
            with self.assertRaises(ValueError):
                subject.declared_sources(candidate, changed, expected)

    def test_complete_four_results_no_ignore_or_foreign_tests(self):
        text = self.output()
        self.assertEqual(subject.validate_output(text), 52)
        first = sorted(subject.NAMES)[0]
        for bad in (text.replace("test " + first + " ... ok\n", ""), text.replace(first, "foreign::test"),
                text.replace("running 4", "running 3"), text.replace("4 passed", "3 passed"),
                text.replace("0 ignored", "1 ignored"), text.replace("0 failed", "1 failed"),
                text + "\ntest " + first + " ... ok\n", " "*32769):
            with self.assertRaises(ValueError):
                subject.validate_output(bad)

    def test_unit_worker_only_adds_closed_filter_keeps_original_limits(self):
        policy = copy.deepcopy(subject.maintenance.POLICY)
        calls = []
        def fake_worker(task):
            self.assertEqual(task, subject.UNIT)
            args = ["cargo", *subject.previous.XML_ARGS, "--locked", "--offline", "--jobs", "1",
                "--color=never", "--target-dir", str(subject.maintenance.TARGET), "--", "--test-threads=1"]
            kwargs = {"cwd": subject.maintenance.ROOT, "stdin": subject.subprocess.DEVNULL,
                "env": {"RUST_TEST_THREADS": "1"}}
            with self.assertRaisesRegex(ValueError, "READBACK_WORKER_ARGUMENT_SCOPE"):
                subject.subprocess.call(args+['--ignored'], **kwargs)
            return subject.subprocess.call(args, **kwargs)
        def call(args, **kwargs):
            calls.append(args)
            return 0
        with patch.object(subject.maintenance, "worker", side_effect=fake_worker), \
                patch.object(subject.subprocess, "call", side_effect=call):
            self.assertEqual(subject.run_worker(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-3:], ["--", subject.FILTER, "--test-threads=1"])
        self.assertEqual(subject.maintenance.POLICY, policy)
        with self.assertRaises(ValueError):
            subject.run_owned("fixture", {}, (), (), subject.UNIT, 181)

    def test_missing_unit_result_never_becomes_pass(self):
        captured = io.StringIO()
        def run(task, destination, seconds):
            json.dump({"task": task, "state": "PASS_SCOPED_NOT_GATE", "tests_passed": 4}, captured)
            return 0
        with patch.object(subject.maintenance, "run", side_effect=run):
            subject.run_owned("fixture", {}, (), (), subject.UNIT, 180)
        row = json.loads(captured.getvalue())
        self.assertEqual(row["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(row["stop_reason"], "READBACK_UNIT_RESULT_MISSING")
        self.assertFalse(row["whole_library_qualified"])

    def test_full_parent_keeps_unfiltered_scope_and_failed_result(self):
        captured = io.StringIO()
        names, modules = ["one", "two"], ["bound.rs"]
        def run(destination, expected, actual_names, actual_modules, task, seconds):
            self.assertEqual((actual_names, actual_modules, task, seconds), (names, modules, "stored-form-tests", 1200))
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "stop_reason": "STOP_DURATION_LIMIT"}, captured)
            return 2
        with patch.object(subject.previous, "run_owned", side_effect=run):
            self.assertEqual(subject.run_owned("fixture", {}, names, modules, "stored-form-tests", 1200), 2)
        row = json.loads(captured.getvalue())
        self.assertEqual(row["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(row["source_variant"], "moved-readback-buffer-r7")

    def test_annotations_never_claim_speedup_SQL_native_or_gate(self):
        row = subject.annotate({"task": subject.UNIT}, subject.UNIT)
        self.assertEqual(row["P09_gate"], "OPEN")
        for key in ("product_complete", "signed_SQL_native_or_Gate_qualified", "PC_freeze_resolved", "statistical_speedup_proven"):
            self.assertFalse(row[key])
        with self.assertRaises(ValueError):
            subject.annotate({"task": "foreign"}, subject.UNIT)
