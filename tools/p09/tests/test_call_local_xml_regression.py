import copy
import io
import json
import unittest
from unittest.mock import patch

import run_call_local_xml_regression as subject


class CallLocalXmlTests(unittest.TestCase):
    def binding(self):
        expected, originals, deltas = {}, [], []
        for name in sorted(subject.EXISTING):
            data = ("whole original " + name).encode()
            pin = {"path": name, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
            expected[name] = pin
            originals.append(dict(pin, base64=subject.base64.b64encode(data).decode()))
            deltas.append(dict(pin, bytes=pin["bytes"]+1, sha256="7"*64))
        deltas.append({"path": subject.NEW, "bytes": 1, "sha256": "8"*64})
        expected["unchanged.rs"] = {"path": "unchanged.rs", "bytes": 1, "sha256": "3"*64}
        candidate = {"schema_version": "hwpx-agent.p09-call-local-xml-reuse-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "preimage_archive": subject.ARCHIVE,
            "source_deltas": deltas, "added_sources": [subject.NEW]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.parent.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.PARENT_PIN, "files": originals}
        return candidate, archive, expected

    def output(self, task, names, filtered=0):
        count = subject.CASES[task][2]
        return f"running {count} tests\n" + "\n".join("test " + name + " ... ok" for name in sorted(names)) + \
            f"\ntest result: ok. {count} passed; 0 failed; 0 ignored; 0 measured; {filtered} filtered out; finished in 1.00s\n"

    def test_exact_four_deltas_one_addition_preserve_parent(self):
        candidate, archive, expected = self.binding()
        actual = subject.declared_sources(candidate, archive, expected)
        self.assertEqual(set(actual), set(expected) | {subject.NEW})
        self.assertEqual(actual["unchanged.rs"], expected["unchanged.rs"])

    def test_rejects_missing_foreign_or_already_existing_addition(self):
        candidate, archive, expected = self.binding()
        for key, value in (("parent_candidate_pin", {}), ("baseline_build_pin", {}),
                ("qualification", "PASS"), ("added_sources", []), ("added_sources", ["foreign.rs"]),
                ("source_deltas", candidate["source_deltas"][:-1]), ("preimage_archive", "foreign")):
            with self.assertRaises(ValueError):
                subject.declared_sources(dict(candidate, **{key: value}), archive, expected)
        with self.assertRaises(ValueError):
            subject.declared_sources(candidate, archive, dict(expected, **{subject.NEW: candidate["source_deltas"][-1]}))

    def test_rejects_partial_duplicate_corrupt_original_preimages(self):
        candidate, archive, expected = self.binding()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for changed in (bad, dict(archive, files=archive["files"][:-1]), dict(archive, files=[archive["files"][0]]*4)):
            with self.assertRaises(ValueError):
                subject.declared_sources(candidate, changed, expected)

    def test_complete_unit_and_each_full_target_require_exact_names_no_ignore(self):
        for task, (_, _, count) in subject.CASES.items():
            names = subject.UNIT_NAMES if task == subject.UNIT else {f"case{i}" for i in range(count)}
            filtered = 57 if task == subject.UNIT else 0
            text = self.output(task, names, filtered)
            self.assertEqual(subject.validate_output(text, task, names), filtered)
            for bad in (text.replace("0 ignored", "1 ignored"), text.replace("0 failed", "1 failed"), text+text,
                    text.replace(sorted(names)[0], "foreign::test"), " "*32769):
                with self.assertRaises(ValueError):
                    subject.validate_output(bad, task, names)

    def test_partial_filtered_integration_targets_are_never_complete(self):
        for task, (_, _, count) in subject.CASES.items():
            if task == subject.UNIT:
                continue
            names = {f"case{i}" for i in range(count)}
            with self.assertRaises(ValueError):
                subject.validate_output(self.output(task, names, 1), task, names)

    def test_real_original_worker_only_filters_unit_and_keeps_full_targets(self):
        from types import SimpleNamespace
        class Kernel:
            def GetCurrentProcess(self):
                return 1
            def IsProcessInJob(self, process, job, member):
                member._obj.value = True
                return True
        policy = copy.deepcopy(subject.maintenance.POLICY)
        for task in subject.CASES:
            calls = []
            def call(args, **kwargs):
                calls.append(args)
                self.assertEqual(kwargs["env"]["RUST_TEST_THREADS"], "1")
                return 0
            with patch.object(subject.maintenance, "Windows", return_value=SimpleNamespace(k=Kernel())), \
                    patch.object(subject.maintenance.sys, "stdin", io.StringIO("P149_GO\n")), \
                    patch.object(subject.maintenance.shutil, "which", return_value="cargo"), \
                    patch.object(subject.subprocess, "call", side_effect=call):
                self.assertEqual(subject.run_worker(task), 0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][-3:] if task == subject.UNIT else calls[0][-2:],
                ["--", subject.FILTER, "--test-threads=1"] if task == subject.UNIT else ["--", "--test-threads=1"])
        self.assertEqual(subject.maintenance.POLICY, policy)

    def test_missing_target_results_cannot_become_pass(self):
        captured = io.StringIO()
        def run(task, destination, seconds):
            json.dump({"task": task, "state": "PASS_SCOPED_NOT_GATE", "tests_passed": 7}, captured)
            return 0
        with patch.object(subject.maintenance, "run", side_effect=run):
            subject.run_owned("fixture", {}, subject.UNIT_NAMES, (), subject.UNIT, 180)
        row = json.loads(captured.getvalue())
        self.assertEqual(row["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(row["stop_reason"], "LOCAL_XML_RESULT_MISSING")
        self.assertFalse(row["whole_library_qualified"])

    def test_parent_unfiltered249_scope_and_failure_remain_unchanged(self):
        captured = io.StringIO()
        names, modules = ["one", "two"], ["bound.rs"]
        def run(destination, expected, actual_names, actual_modules, task, seconds):
            self.assertEqual((actual_names, actual_modules, task, seconds), (names, modules, "stored-form-tests", 1200))
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "stop_reason": "STOP_DURATION_LIMIT"}, captured)
            return 2
        with patch.object(subject.previous, "run_owned", side_effect=run):
            self.assertEqual(subject.run_owned("fixture", {}, names, modules, "stored-form-tests", 1200), 2)
        self.assertEqual(json.loads(captured.getvalue())["state"], "STOPPED_NOT_ACCEPTED")

    def test_new_targets_keep_original_finite_duration(self):
        for task in subject.CASES:
            with self.assertRaises(ValueError):
                subject.run_owned("fixture", {}, (), (), task, 181)
            with self.assertRaises(ValueError):
                subject.run_owned("fixture", {}, (), (), task, True)

    def test_inherited_profile_and_readback_tasks_keep_original_finite_duration(self):
        for task in subject.TASKS:
            subject.require_duration(task, 30)
            subject.require_duration(task, 1200 if task == "stored-form-tests" else 180)
            for seconds in (29, True, 1201 if task == "stored-form-tests" else 181):
                with self.assertRaises(ValueError):
                    subject.require_duration(task, seconds)
        with self.assertRaises(ValueError):
            subject.require_duration("foreign-tests", 180)

    def test_annotations_never_claim_SQL_native_speedup_or_gate(self):
        row = subject.annotate({"task": subject.UNIT}, subject.UNIT)
        for key in ("product_complete", "signed_SQL_native_or_Gate_qualified", "PC_freeze_resolved", "statistical_speedup_proven"):
            self.assertFalse(row[key])
        self.assertEqual(row["P09_gate"], "OPEN")
        with self.assertRaises(ValueError):
            subject.annotate({"task": "foreign"}, subject.UNIT)
