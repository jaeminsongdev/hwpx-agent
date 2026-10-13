import copy
import io
import json
import unittest
from unittest.mock import patch

import run_xml_roundtrip_regression as subject


class XmlRoundtripRegressionTests(unittest.TestCase):
    def binding(self):
        data = b"whole original XML verifier"
        pin = {"path": subject.XML, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
        expected = {subject.XML: pin, "crates/unchanged/src/lib.rs":
            {"path": "crates/unchanged/src/lib.rs", "bytes": 1, "sha256": "3"*64}}
        candidate = {"schema_version": "hwpx-agent.p09-streaming-xml-roundtrip-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "preimage_archive": subject.ARCHIVE,
            "source_deltas": [dict(pin, bytes=pin["bytes"]+1, sha256="7"*64)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN,
            "files": [dict(pin, base64=subject.base64.b64encode(data).decode())]}
        return candidate, archive, expected

    def output(self):
        return "running 13 tests\n" + "\n".join("test " + name + " ... ok" for name in sorted(subject.XML_NAMES)) + \
            "\ntest result: ok. 13 passed; 0 failed; 0 ignored; 0 measured; 400 filtered out; finished in 1.00s\n"

    def test_exact_one_source_delta_preserves_every_other_parent_pin(self):
        candidate, archive, expected = self.binding()
        result = subject.declared_sources(candidate, archive, expected)
        self.assertEqual(set(result), set(expected))
        self.assertEqual(result[subject.XML], candidate["source_deltas"][0])
        self.assertEqual(result["crates/unchanged/src/lib.rs"], expected["crates/unchanged/src/lib.rs"])

    def test_rejects_foreign_baseline_parent_archive_qualification_and_delta(self):
        candidate, archive, expected = self.binding()
        for key, value in (("baseline_build_pin", {}), ("parent_candidate_pin", {}),
                ("preimage_archive", "foreign"), ("qualification", "PASS"),
                ("source_deltas", []), ("source_deltas", [expected[subject.XML]]),
                ("source_deltas", candidate["source_deltas"]+[expected["crates/unchanged/src/lib.rs"]])):
            with self.assertRaises(ValueError):
                subject.declared_sources(dict(candidate, **{key: value}), archive, expected)

    def test_rejects_partial_or_corrupt_whole_original_preimages(self):
        candidate, archive, expected = self.binding()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for changed in (bad, dict(archive, files=[]), dict(archive, parent_candidate_pin={}),
                dict(archive, files=archive["files"]*2)):
            with self.assertRaises(ValueError):
                subject.declared_sources(candidate, changed, expected)

    def test_component_complete_original7_plus_new6_not_whole_library(self):
        self.assertEqual(len(subject.XML_NAMES), 13)
        self.assertEqual(sum("::streaming_round_trip_" in name for name in subject.XML_NAMES), 6)
        self.assertEqual(subject.validate_xml_output(self.output()), 400)

    def test_rejects_missing_duplicate_foreign_ignored_failed_and_wrong_component_summary(self):
        text = self.output()
        first = sorted(subject.XML_NAMES)[0]
        for bad in (text.replace("test " + first + " ... ok\n", ""),
                text.replace(first, "unbound::test"), text.replace("running 13", "running 12"),
                text.replace("13 passed", "12 passed"), text.replace("0 ignored", "1 ignored"),
                text.replace("0 failed", "1 failed"), text + "\ntest " + first + " ... ok\n"):
            with self.assertRaises(ValueError):
                subject.validate_xml_output(bad)
        with self.assertRaises(ValueError):
            subject.validate_xml_output(" "*32769)

    def test_component_worker_adds_only_exact_component_filter_with_locked_single_job(self):
        original_policy = copy.deepcopy(subject.maintenance.POLICY)
        calls = []
        def fake_call(args, **kwargs):
            calls.append((args, kwargs))
            return 0
        def fake_worker(task):
            self.assertEqual(task, subject.XML_TASK)
            self.assertEqual(subject.maintenance.POLICY, original_policy)
            args = ["cargo", *subject.XML_ARGS, "--locked", "--offline", "--jobs", "1", "--color=never",
                "--target-dir", str(subject.maintenance.TARGET), "--", "--test-threads=1"]
            kwargs = {"cwd": subject.maintenance.ROOT, "stdin": subject.subprocess.DEVNULL,
                "env": {"RUST_TEST_THREADS": "1"}}
            with self.assertRaisesRegex(ValueError, "XML_WORKER_ARGUMENT_SCOPE"):
                subject.subprocess.call(args+['--ignored'], **kwargs)
            return subject.subprocess.call(args, **kwargs)
        with patch.object(subject.maintenance, "worker", side_effect=fake_worker), \
                patch.object(subject.subprocess, "call", side_effect=fake_call):
            self.assertEqual(subject.run_worker(), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][-3:], ["--", subject.XML_FILTER, "--test-threads=1"])
        self.assertEqual(subject.maintenance.POLICY, original_policy)

    def test_finite_duration_only_complete_stored249_gets_original1200_budget(self):
        subject.require_duration("stored-form-tests", 1200)
        for task in subject.TASKS:
            subject.require_duration(task, 180)
        for task, value in ((subject.XML_TASK, 181), (subject.profile.TASK, 181),
                ("stored-form-tests", 1201), ("foreign", 180), (subject.XML_TASK, True),
                (subject.XML_TASK, 180.0), (subject.XML_TASK, 29)):
            with self.assertRaises(ValueError):
                subject.require_duration(task, value)

    def test_missing_component_result_cannot_become_pass_or_gate(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "PASS_SCOPED_NOT_GATE", "tests_passed": 13}, captured)
            return 0
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, (), (), subject.XML_TASK, 180)
        result = json.loads(captured.getvalue())
        self.assertEqual(result["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(result["stop_reason"], "XML_COMPONENT_RESULT_MISSING")
        self.assertFalse(result["whole_library_qualified"])
        self.assertFalse(result["product_complete"])
        self.assertEqual(result["P09_gate"], "OPEN")

    def test_parent_complete_target_keeps_original_names_modules_duration_and_failed_state(self):
        captured = io.StringIO()
        names, modules = ["one", "two"], ["bound.rs"]
        def fake_run(destination, expected, actual_names, seconds, task, actual_modules, variant):
            self.assertEqual((actual_names, seconds, actual_modules, variant), (names, 1200, modules, "anchor-prefix-r4"))
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "stop_reason": "STOP_DURATION_LIMIT"}, captured)
            return 2
        with patch.object(subject.parent, "run_owned", side_effect=fake_run):
            self.assertEqual(subject.run_owned("fixture", {}, names, modules, "stored-form-tests", 1200), 2)
        result = json.loads(captured.getvalue())
        self.assertEqual(result["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(result["source_variant"], "streaming-xml-r6")
        self.assertFalse(result["signed_SQL_native_or_Gate_qualified"])
        self.assertFalse(result["statistical_speedup_proven"])

    def test_original_profile_requires_original_numeric_scope_and_labels_actual_source(self):
        captured = io.StringIO()
        def fake_profile(destination, expected, seconds):
            self.assertEqual(seconds, 180)
            json.dump({"task": subject.profile.TASK, "state": "PASS_SCOPED_NOT_GATE",
                "qualification": subject.profile.QUALIFICATION, "stage_profile_qualified": True}, captured)
            return 0
        with patch.object(subject.profile, "run_owned", side_effect=fake_profile):
            self.assertEqual(subject.run_owned("fixture", {}, (), (), subject.profile.TASK, 180), 0)
        result = json.loads(captured.getvalue())
        self.assertEqual(result["qualification"], subject.profile.QUALIFICATION)
        self.assertEqual(result["source_variant"], "streaming-xml-r6")
        self.assertFalse(result["PC_freeze_resolved"])
        self.assertFalse(result["signed_SQL_native_or_Gate_qualified"])
        with self.assertRaises(ValueError):
            subject.annotate({"task": "foreign"}, subject.XML_TASK)
