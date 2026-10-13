"""Closed target/whole test inventory and source binding; no actual Cargo."""
import copy
import io
import json
import unittest
from unittest.mock import patch

import run_stored_comment_regression as subject


class StoredCommentRegressionTests(unittest.TestCase):
    def names(self):
        return [f"test_case_{index}" for index in range(24)]

    def output(self, names=None, counts="24 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"):
        return "".join("test "+name+" ... ok\n" for name in (self.names() if names is None else names)) \
            +"test result: ok. "+counts+" finished in 0.1s\n"

    def test_exact_target_is_full_stored_comment_suite_without_filter_or_SQL(self):
        self.assertEqual(subject.CARGO_ARGUMENTS,
            ["test", "-p", "hwpx-agent-cli", "--test", "stored_comment_provider"])
        self.assertEqual(subject.EXPECTED_COUNT, 24)
        self.assertEqual(set(subject.TEST_FILES.values()), {""})

    def test_all_named_tests_and_unfiltered_clean_summary_are_accepted(self):
        subject.validate_output(self.output(), self.names())

    def test_wrong_missing_duplicate_or_foreign_names_are_rejected(self):
        for names in (self.names()[:-1], self.names()[:1]*24, self.names()[:-1]+["foreign"]):
            with self.assertRaises(ValueError):
                subject.validate_output(self.output(names), self.names())

    def test_ignored_measured_filtered_or_extra_summary_is_rejected(self):
        for counts in ("23 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out;",
                "24 passed; 0 failed; 0 ignored; 1 measured; 0 filtered out;",
                "24 passed; 0 failed; 0 ignored; 0 measured; 1 filtered out;"):
            with self.assertRaises(ValueError):
                subject.validate_output(self.output(counts=counts), self.names())
        with self.assertRaises(ValueError):
            subject.validate_output(self.output()+self.output(), self.names())

    def test_source_definition_parser_rejects_ignored_or_unrecognized_attributes(self):
        paths = [next(iter(subject.TEST_FILES)), "crates/product-cli/tests/stored_comment_provider/rich_bodies.rs"]
        texts = {paths[0]: '#[path = "stored_comment_provider/rich_bodies.rs"]\nmod rich_bodies;\n'
            +"".join(f"#[test]\nfn test_{i}() {{}}\n" for i in range(16)),
            paths[1]: "".join(f"#[test]\nfn test_{i}() {{}}\n" for i in range(8))}
        self.assertEqual(len(subject.test_names(texts)), 24)
        for suffix in ("#[ignore]\n", "#[test]\n#[cfg(feature=\"extra\")] fn other() {}"):
            with self.assertRaises(ValueError):
                subject.test_names(dict(texts, **{paths[0]: texts[paths[0]]+suffix}))

    def test_full_expected_pin_inventory_is_required_even_if_runtime_passed(self):
        pin = {"path": "crates/fixture/src/lib.rs", "bytes": 10, "sha256": "0"*64}
        subject.require_pins([pin], {pin["path"]: pin})
        for actual in ([], [dict(pin, bytes=9)], [dict(pin, sha256="1"*64)]):
            with self.assertRaises(ValueError):
                subject.require_pins(actual, {pin["path"]: pin})

    def test_composition_restores_original_globals_and_does_not_change_policy(self):
        original = {name: getattr(subject.maintenance, name) for name in ("__file__", "TASKS", "SOURCES", "pins")}
        capture = subject.bounded.BoundedProcessCapture
        policy = copy.deepcopy(subject.maintenance.POLICY)
        def run(task, destination, seconds):
            self.assertEqual(task, subject.TASK)
            self.assertEqual(subject.maintenance.TASKS, {subject.TASK: subject.CARGO_ARGUMENTS})
            self.assertIn(subject.SELF, subject.maintenance.SOURCES)
            self.assertEqual(subject.maintenance.__file__, str(subject.maintenance.ROOT/subject.SELF))
            return 2
        with patch.object(subject.maintenance, "run", side_effect=run) as call:
            self.assertEqual(subject.run_owned("fixture", {}, self.names(), 120), 2)
        call.assert_called_once_with(subject.TASK, "fixture", 120)
        for name, value in original.items():
            self.assertIs(getattr(subject.maintenance, name), value)
        self.assertIs(subject.bounded.BoundedProcessCapture, capture)
        self.assertEqual(subject.maintenance.POLICY, policy)

    def test_composition_failure_still_restores_original_launcher_and_capture(self):
        original, capture = subject.maintenance.__file__, subject.bounded.BoundedProcessCapture
        with patch.object(subject.maintenance, "run", side_effect=ValueError("FIXTURE_FAILURE")):
            with self.assertRaises(ValueError):
                subject.run_owned("fixture", {}, self.names(), 120)
        self.assertEqual(subject.maintenance.__file__, original)
        self.assertIs(subject.bounded.BoundedProcessCapture, capture)

    def test_all_three_targets_are_entire_unfiltered_named_cargo_tests(self):
        expected = {"stored-comment-tests": ("stored_comment_provider", 24),
            "import-source-tests": ("document_import_source", 12),
            "form-value-tests": ("form_value_operation", 18), "stored-form-tests": ("form_stored_provider", 249),
            "import-forms-tests": ("document_import_forms", 10),
            "import-fields-tests": ("document_import_fields", 12),
            "import-meanings-tests": ("document_import_field_semantics", 13),
            "import-formula-evaluation-tests": ("document_import_formula_evaluation", 10),
            "import-formula-output-tests": ("document_import_formula_output", 6)}
        self.assertEqual(set(subject.CASES), set(expected))
        for task, (target, count) in expected.items():
            arguments, files, total = subject.CASES[task]
            package = "hwpx-package" if task.startswith("import-") else "hwpx-agent-cli"
            self.assertEqual(arguments, ["test", "-p", package, "--test", target])
            self.assertEqual(total, count)
            self.assertTrue(files)

    def test_each_scope_requires_its_own_full_count_and_foreign_scope_is_denied(self):
        for task, (_, _, count) in subject.CASES.items():
            names = [f"test_case_{index}" for index in range(count)]
            subject.validate_output(self.output(names, f"{count} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"), names, task)
            with self.assertRaises(ValueError):
                subject.validate_output(self.output(names[:-1], f"{count-1} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"), names, task)
        with self.assertRaisesRegex(ValueError, "REGRESSION_TASK_SCOPE"):
            subject.run_owned("fixture", {}, self.names(), 120, "foreign-tests")

    def test_composition_authorizes_only_selected_form_target_not_parallel_other_targets(self):
        def run(task, destination, seconds):
            self.assertEqual(subject.maintenance.TASKS, {task: subject.CASES[task][0]})
            self.assertEqual(task, "form-value-tests")
            return 2
        with patch.object(subject.maintenance, "run", side_effect=run):
            self.assertEqual(subject.run_owned("fixture", {}, [], 120, "form-value-tests"), 2)

    def nested(self):
        root = next(iter(subject.TEST_FILES))
        child = "crates/product-cli/tests/child.rs"
        grandchild = "crates/product-cli/tests/grandchild.rs"
        tests = lambda count: "".join(f"#[test]\nfn case_{i}() {{}}\n" for i in range(count))
        return {root: '#[path = "child.rs"]\nmod child;\n'+tests(16),
            child: '#[path = "grandchild.rs"]\nmod grandchild;\n'+tests(4), grandchild: tests(4)}

    def test_recursive_grandchildren_are_included_with_full_names(self):
        texts = self.nested()
        names, modules = subject.recursive_names(texts.__getitem__)
        self.assertEqual(len(names), 24)
        self.assertIn("child::grandchild::case_0", names)
        self.assertEqual(len(modules), 3)
        self.assertEqual(subject.test_names(texts), names)
        root = next(iter(subject.TEST_FILES))
        for visibility in ("pub ", "pub(super) ", "pub(crate) ", "pub(self) "):
            public = dict(texts)
            public[root] = texts[root].replace("mod child;", visibility+"mod child;")
            self.assertEqual(subject.test_names(public), names)

    def test_missing_nested_module_is_not_silently_omitted(self):
        texts = self.nested()
        del texts["crates/product-cli/tests/grandchild.rs"]
        with self.assertRaisesRegex(ValueError, "REGRESSION_TEST_FILE_INVENTORY"):
            subject.test_names(texts)

    def test_unreachable_extra_source_is_not_counted(self):
        texts = self.nested()
        texts["crates/product-cli/tests/foreign.rs"] = "#[test]\nfn extra() {}"
        with self.assertRaisesRegex(ValueError, "REGRESSION_TEST_FILE_INVENTORY"):
            subject.test_names(texts)

    def test_aliases_of_one_source_keep_distinct_module_names(self):
        root = next(iter(subject.TEST_FILES))
        texts = {root: '#[path = "shared.rs"]\nmod first;\n#[path = "shared.rs"]\nmod second;',
            "crates/product-cli/tests/shared.rs": "".join(f"#[test]\nfn case_{i}() {{}}\n" for i in range(12))}
        names, modules = subject.recursive_names(texts.__getitem__)
        self.assertEqual(len(modules), 3)
        self.assertIn("first::case_0", names)
        self.assertIn("second::case_0", names)
        self.assertEqual(len(names), 24)

    def test_module_cycle_fails_before_repeated_read(self):
        root = next(iter(subject.TEST_FILES))
        texts = {root: '#[path = "stored_comment_provider.rs"]\nmod cycle;'}
        with self.assertRaisesRegex(ValueError, "REGRESSION_MODULE_CYCLE"):
            subject.recursive_names(texts.__getitem__)

    def test_depth_and_module_budgets_fail_closed(self):
        for constant, value in (("MODULE_LIMIT", 2), ("DEPTH_LIMIT", 1)):
            with patch.object(subject, constant, value):
                with self.assertRaisesRegex(ValueError, "REGRESSION_MODULE_BUDGET"):
                    subject.recursive_names(self.nested().__getitem__)

    def test_implicit_inline_and_duplicate_module_declarations_fail_closed(self):
        root = next(iter(subject.TEST_FILES))
        for text in ('mod hidden;', 'mod hidden { #[test] fn example() {} }',
                '#[path = "child.rs"]\nmod same;\n#[path = "other.rs"]\nmod same;'):
            with self.assertRaises(ValueError):
                subject.recursive_names({root: text}.__getitem__)

    def test_literal_module_paths_are_repo_scoped_and_normalized(self):
        root = "crates/product-cli/tests/form_stored_provider/actual_import/formula_evaluation.rs"
        self.assertEqual(subject.module_path(root, "../../../../hwpx-package/tests/support/fixture.rs"),
            "crates/hwpx-package/tests/support/fixture.rs")
        for relative in ("../../../../../../outside.rs", "/outside.rs", "C:/outside.rs", "child\\file.rs", "../bad.txt"):
            with self.assertRaisesRegex(ValueError, "REGRESSION_MODULE_PATH_SCOPE"):
                subject.module_path(root, relative)

    def test_compiled_listing_is_exact_and_not_runtime_output(self):
        names = [f"case_{i}" for i in range(249)]
        output = "".join(name+": test\n" for name in names)
        subject.validate_listing(output, names, "stored-form-list")
        subject.validate_listing(output+"\n249 tests, 0 benchmarks\n", names, "stored-form-list")
        with self.assertRaises(ValueError):
            subject.validate_output(output, names, "stored-form-tests")

    def test_listing_rejects_partial_duplicate_foreign_benchmark_and_raw_text(self):
        names = [f"case_{i}" for i in range(249)]
        good = "".join(name+": test\n" for name in names)
        bad = ("".join(name+": test\n" for name in names[:-1]), good+"case_0: test\n",
            good+"foreign: test\n", good.replace("case_0: test", "case_0: benchmark"),
            good+"unexpected secret or log\n", good+"249 tests, 0 benchmarks\n"*2,
            "x"*(subject.bounded.LIMIT+1))
        for output in bad:
            with self.assertRaises(ValueError):
                subject.validate_listing(output, names, "stored-form-list")

    def test_waiting_worker_appends_list_only_after_original_cargo_arguments(self):
        original_tasks = subject.maintenance.TASKS
        original_call = subject.subprocess.call
        def fake_worker(task):
            arguments = ["cargo", *subject.maintenance.TASKS[task], "--locked", "--offline", "--jobs", "1",
                "--color=never", "--target-dir", str(subject.maintenance.TARGET)]
            return subject.subprocess.call(arguments, cwd=subject.maintenance.ROOT,
                stdin=subject.subprocess.DEVNULL, env={"RUST_TEST_THREADS": "1"})
        with patch.object(subject.subprocess, "call", return_value=0) as call, \
                patch.object(subject.maintenance, "worker", side_effect=fake_worker):
            self.assertEqual(subject.run_worker("stored-form-list"), 0)
        arguments = call.call_args.args[0]
        self.assertEqual(arguments[-4:], ["--", "--list", "--format", "terse"])
        self.assertNotIn("--test-threads=1", arguments)
        self.assertIs(subject.maintenance.TASKS, original_tasks)
        self.assertIs(subject.subprocess.call, original_call)

    def test_listing_receipt_does_not_claim_runtime_pass_and_preserves_failure(self):
        original_dump = json.dump
        for state in ("PASS_SCOPED_NOT_GATE", "STOPPED_NOT_ACCEPTED"):
            captured = io.StringIO()
            def fake_run(task, destination, seconds):
                json.dump({"task": task, "state": state, "heavy_work_started": True}, captured)
                return 0 if state == "PASS_SCOPED_NOT_GATE" else 2
            with patch.object(subject.maintenance, "run", side_effect=fake_run):
                subject.run_owned("fixture", {}, [f"case_{i}" for i in range(249)], 120, "stored-form-list")
            receipt = json.loads(captured.getvalue())
            self.assertEqual(receipt["state"], state)
            self.assertEqual(receipt["execution_mode"], "compiled_inventory_only")
            self.assertFalse(receipt["runtime_tests_executed"])
            self.assertNotIn("tests_passed", receipt)
            self.assertEqual(receipt["compiled_inventory_exact"], state == "PASS_SCOPED_NOT_GATE")
        self.assertIs(json.dump, original_dump)
        captured = io.StringIO()
        def fake_incomplete(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_incomplete):
            subject.run_owned("fixture", {}, self.names(), 120)
        receipt = json.loads(captured.getvalue())
        self.assertIsNone(receipt["runtime_tests_executed"])
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")

    def test_runtime_progress_tracks_whitelisted_pending_and_completed_names(self):
        now = [10.0]
        progress = subject.RuntimeProgress(["first", "nested::second"], clock=lambda: now[0])
        progress.observe("running 2 tests\ntest first ... ")
        now[0] = 14.0
        progress.observe("running 2 tests\ntest first ... ")
        self.assertEqual(progress.snapshot()["pending_observed_seconds"], 4.0)
        now[0] = 15.0
        output = "running 2 tests\ntest first ... ok\ntest nested::second ... "
        progress.observe(output)
        snapshot = progress.snapshot()
        self.assertEqual(snapshot["completed_observed"], 1)
        self.assertEqual(snapshot["pending_test"], "nested::second")
        self.assertEqual(snapshot["events"][0]["pending_observed_seconds_at_completion"], 5.0)
        progress.observe(output)
        self.assertEqual(len(progress.snapshot()["events"]), 1)
        now[0] = 16.0
        progress.observe(output+"ok\n")
        self.assertEqual(progress.snapshot()["completed_observed"], 2)
        self.assertIsNone(progress.snapshot()["pending_test"])

    def test_runtime_progress_never_saves_raw_foreign_secret_or_path_text(self):
        progress = subject.RuntimeProgress(["allowed"], clock=lambda: 1.0)
        progress.observe("SECRET_SENTINEL /private/path\ntest foreign ... ok\ntest allowed ... ")
        serialized = json.dumps(progress.snapshot())
        self.assertNotIn("SECRET_SENTINEL", serialized)
        self.assertNotIn("/private/path", serialized)
        self.assertNotIn("foreign", serialized)
        self.assertEqual(progress.snapshot()["completed_observed"], 0)
        self.assertEqual(progress.snapshot()["pending_test"], "allowed")

    def test_runtime_progress_observes_failed_and_ignored_without_claiming_pass(self):
        progress = subject.RuntimeProgress(["first", "second", "third"], clock=lambda: 1.0)
        progress.observe("test first ... ok\r\ntest second ... FAILED\r\ntest third ... ignored\r\n")
        snapshot = progress.snapshot()
        self.assertEqual(snapshot["completed_observed"], 3)
        self.assertEqual(snapshot["passed_observed"], 1)
        self.assertEqual(snapshot["failed_observed"], 1)
        self.assertEqual(snapshot["ignored_observed"], 1)
        self.assertNotIn("tests_passed", snapshot)
        self.assertEqual(snapshot["scope"], "source_whitelisted_libtest_progress_not_full_runtime_pass")

    def test_runtime_progress_rejects_duplicate_status_drift_buffer_loss_and_oversize(self):
        progress = lambda: subject.RuntimeProgress(["first"], clock=lambda: 1.0)
        with self.assertRaisesRegex(ValueError, "REGRESSION_PROGRESS_DUPLICATE_NAME"):
            progress().observe("test first ... ok\ntest first ... ok\n")
        for output in ("test first ... FAILED\n", ""):
            instance = progress()
            instance.observe("test first ... ok\n")
            with self.assertRaises(ValueError):
                instance.observe(output)
        with self.assertRaisesRegex(ValueError, "REGRESSION_PROGRESS_OUTPUT_BUDGET"):
            progress().observe("x"*(subject.bounded.LIMIT+1))

    def test_runtime_progress_clock_and_name_scope_are_bounded(self):
        for names in (["same", "same"], ["/private/path"], [f"case_{i}" for i in range(250)]):
            with self.assertRaisesRegex(ValueError, "REGRESSION_PROGRESS_SCOPE"):
                subject.RuntimeProgress(names)
        for value in (float("nan"), float("inf"), True):
            with self.assertRaisesRegex(ValueError, "REGRESSION_PROGRESS_CLOCK"):
                subject.RuntimeProgress(["first"], clock=lambda: value)
        now = [2.0]
        progress = subject.RuntimeProgress(["first"], clock=lambda: now[0])
        now[0] = 1.0
        with self.assertRaisesRegex(ValueError, "REGRESSION_PROGRESS_CLOCK"):
            progress.observe("")

    def test_runtime_progress_receipt_addition_preserves_original_timeout(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED",
                "stop_reason": "STOP_DURATION_LIMIT", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, self.names(), 120)
        receipt = json.loads(captured.getvalue())
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(receipt["stop_reason"], "STOP_DURATION_LIMIT")
        self.assertEqual(receipt["runtime_progress"]["expected_tests"], 24)
        self.assertEqual(receipt["runtime_progress"]["completed_observed"], 0)
        self.assertIsNone(receipt["runtime_tests_executed"])

    def reconstruction(self):
        files, sources = [], {}
        for path in sorted(subject.RECONSTRUCTION_DELTAS|{subject.SELF, subject.TEST}):
            data = ("original "+path).encode()
            pin = {"path": path, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
            files.append(dict(pin, base64=subject.base64.b64encode(data).decode()))
            if path in subject.RECONSTRUCTION_DELTAS:
                sources[path] = pin
        sources["crates/fixture/src/unchanged.rs"] = {"path": "crates/fixture/src/unchanged.rs", "bytes": 1, "sha256": "1"*64}
        candidate = {"schema_version": "hwpx-agent.p09-form-reconstruction-source-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "preimage_archive": subject.RECONSTRUCTION_ARCHIVE,
            "source_deltas": [dict(sources[name], bytes=sources[name]["bytes"]+1, sha256="2"*64)
                for name in sorted(subject.RECONSTRUCTION_DELTAS)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1", "files": files}
        return candidate, archive, sources

    def test_reconstruction_candidate_updates_only_exact_four_reviewed_sources(self):
        candidate, archive, sources = self.reconstruction()
        result = subject.reconstruction_sources(candidate, archive, sources)
        self.assertEqual(set(result), set(sources))
        self.assertEqual(result["crates/fixture/src/unchanged.rs"], sources["crates/fixture/src/unchanged.rs"])
        for pin in candidate["source_deltas"]:
            self.assertEqual(result[pin["path"]], pin)

    def test_reconstruction_candidate_rejects_missing_extra_unchanged_or_wrong_baseline(self):
        candidate, archive, sources = self.reconstruction()
        invalid = [dict(candidate, source_deltas=candidate["source_deltas"][:-1]),
            dict(candidate, source_deltas=candidate["source_deltas"]+[sources["crates/fixture/src/unchanged.rs"]]),
            dict(candidate, source_deltas=[sources[name] for name in sorted(subject.RECONSTRUCTION_DELTAS)]),
            dict(candidate, baseline_build_pin=dict(candidate["baseline_build_pin"], sha256="3"*64))]
        for item in invalid:
            with self.assertRaises(ValueError):
                subject.reconstruction_sources(item, archive, sources)

    def test_reconstruction_archive_requires_exact_baseline_preimages_not_hash_only_claim(self):
        candidate, archive, sources = self.reconstruction()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for item in (bad, dict(archive, files=archive["files"][:-1]),
                dict(archive, files=archive["files"]+[archive["files"][0]])):
            with self.assertRaises(ValueError):
                subject.reconstruction_sources(candidate, item, sources)
        changed = copy.deepcopy(sources)
        changed[next(iter(subject.RECONSTRUCTION_DELTAS))]["sha256"] = "3"*64
        with self.assertRaisesRegex(ValueError, "REGRESSION_RECONSTRUCTION_BASELINE_DRIFT"):
            subject.reconstruction_sources(candidate, archive, changed)

    def test_new_source_variant_receipt_does_not_relabel_historical_r4_sql_build(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, self.names(), 120, source_variant="reconstruction-r1")
        receipt = json.loads(captured.getvalue())
        self.assertEqual(receipt["source_variant"], "reconstruction-r1")
        self.assertEqual(receipt["baseline_build_qualification"], "HISTORICAL_R4_NOT_NEW_SQL_BUILD")
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")

    def stored_reconstruction(self):
        candidate, archive, sources = self.reconstruction()
        data = {item["path"]: subject.base64.b64decode(item["base64"]) for item in archive["files"]}
        candidate["source_deltas"] = []
        for name in sorted(subject.RECONSTRUCTION_DELTAS):
            data[name] += b" r1"
            candidate["source_deltas"].append({"path": name, "bytes": len(data[name]),
                "sha256": subject.hashlib.sha256(data[name]).hexdigest()})
        parent = subject.reconstruction_sources(candidate, archive, sources)
        for name in subject.STORED_RECONSTRUCTION_DELTAS - subject.RECONSTRUCTION_DELTAS:
            data[name] = ("original " + name).encode()
            parent[name] = {"path": name, "bytes": len(data[name]),
                "sha256": subject.hashlib.sha256(data[name]).hexdigest()}
        files = [{"path": name, "bytes": len(data[name]), "sha256": subject.hashlib.sha256(data[name]).hexdigest(),
            "base64": subject.base64.b64encode(data[name]).decode()}
            for name in sorted(subject.STORED_RECONSTRUCTION_DELTAS | {subject.SELF, subject.TEST})]
        next_candidate = {"schema_version": "hwpx-agent.p09-stored-reconstruction-source-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.RECONSTRUCTION_PARENT_PIN,
            "preimage_archive": subject.STORED_RECONSTRUCTION_ARCHIVE,
            "source_deltas": [dict(parent[name], bytes=parent[name]["bytes"]+1, sha256="4"*64)
                for name in sorted(subject.STORED_RECONSTRUCTION_DELTAS)]}
        next_archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.RECONSTRUCTION_PARENT_PIN, "files": files}
        return next_candidate, next_archive, parent

    def test_stored_reconstruction_chain_changes_only_exact_eight_reviewed_sources(self):
        candidate, archive, parent = self.stored_reconstruction()
        result = subject.stored_reconstruction_sources(candidate, archive, parent)
        self.assertEqual(set(result), set(parent))
        self.assertEqual(result["crates/fixture/src/unchanged.rs"], parent["crates/fixture/src/unchanged.rs"])
        for pin in candidate["source_deltas"]:
            self.assertEqual(result[pin["path"]], pin)

    def test_stored_reconstruction_missing_extra_or_unchanged_delta_is_rejected(self):
        candidate, archive, parent = self.stored_reconstruction()
        for deltas in (candidate["source_deltas"][:-1],
                candidate["source_deltas"]+[parent["crates/fixture/src/unchanged.rs"]],
                [parent[name] for name in sorted(subject.STORED_RECONSTRUCTION_DELTAS)]):
            with self.assertRaisesRegex(ValueError, "REGRESSION_STORED_RECONSTRUCTION_DELTA_SCOPE"):
                subject.stored_reconstruction_sources(dict(candidate, source_deltas=deltas), archive, parent)

    def test_stored_reconstruction_rejects_wrong_parent_baseline_or_archive_identity(self):
        candidate, archive, parent = self.stored_reconstruction()
        for field, value in (("baseline_build_pin", {}), ("parent_candidate_pin", {}),
                ("preimage_archive", subject.RECONSTRUCTION_ARCHIVE)):
            with self.assertRaisesRegex(ValueError, "REGRESSION_STORED_RECONSTRUCTION_CANDIDATE_SCOPE"):
                subject.stored_reconstruction_sources(dict(candidate, **{field: value}), archive, parent)
        for field in ("baseline_build_pin", "parent_candidate_pin"):
            with self.assertRaisesRegex(ValueError, "REGRESSION_STORED_RECONSTRUCTION_ARCHIVE_SCOPE"):
                subject.stored_reconstruction_sources(candidate, dict(archive, **{field: {}}), parent)

    def test_stored_reconstruction_requires_exact_preimage_bytes_and_parent_source_pins(self):
        candidate, archive, parent = self.stored_reconstruction()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for item in (bad, dict(archive, files=archive["files"][:-1]),
                dict(archive, files=archive["files"]+[archive["files"][0]])):
            with self.assertRaises(ValueError):
                subject.stored_reconstruction_sources(candidate, item, parent)
        changed = copy.deepcopy(parent)
        changed[next(iter(subject.STORED_RECONSTRUCTION_DELTAS))]["sha256"] = "5"*64
        with self.assertRaisesRegex(ValueError, "REGRESSION_STORED_RECONSTRUCTION_PARENT_DRIFT"):
            subject.stored_reconstruction_sources(candidate, archive, changed)

    def test_stored_reconstruction_runtime_receipt_keeps_r4_historical_and_failed_run_failed(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED",
                "stop_reason": "STOP_DURATION_LIMIT", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, self.names(), 120, source_variant="reconstruction-r2")
        receipt = json.loads(captured.getvalue())
        self.assertEqual(receipt["source_variant"], "reconstruction-r2")
        self.assertEqual(receipt["baseline_build_qualification"], "HISTORICAL_R4_NOT_NEW_SQL_BUILD")
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")
        self.assertEqual(receipt["stop_reason"], "STOP_DURATION_LIMIT")
        self.assertIsNone(receipt["runtime_tests_executed"])

    def test_extended_duration_is_finite_and_only_full_current_stored_suite(self):
        subject.require_duration("stored-form-tests", "reconstruction-r2", 1200)
        for task in (*subject.CASES, *subject.LIST_TASKS):
            for variant in subject.SOURCE_VARIANTS:
                subject.require_duration(task, variant, 180)
                if not (task == "stored-form-tests" and variant in ("reconstruction-r2", "reconstruction-r3", "anchor-prefix-r4")):
                    with self.assertRaisesRegex(ValueError, "REGRESSION_DURATION_SCOPE"):
                        subject.require_duration(task, variant, 181)
        for invalid in (29, 1201, True, 1200.0, None):
            with self.assertRaisesRegex(ValueError, "REGRESSION_DURATION_SCOPE"):
                subject.require_duration("stored-form-tests", "reconstruction-r2", invalid)

    def test_extended_duration_preserves_full_target_and_original_resource_policy(self):
        policy = copy.deepcopy(subject.maintenance.POLICY)
        def fake_run(task, destination, seconds):
            self.assertEqual((task, seconds), ("stored-form-tests", 1200))
            self.assertEqual(subject.maintenance.TASKS,
                {task: ["test", "-p", "hwpx-agent-cli", "--test", "form_stored_provider"]})
            self.assertEqual(subject.maintenance.POLICY, policy)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            self.assertEqual(subject.run_owned("fixture", {}, [f"case_{i}" for i in range(249)],
                1200, "stored-form-tests", source_variant="reconstruction-r2"), 2)
        self.assertEqual(subject.maintenance.POLICY, policy)

    def formula_reconstruction(self):
        _, _, parent = self.stored_reconstruction()
        files = []
        for name in sorted(subject.FORMULA_RECONSTRUCTION_DELTAS | {subject.SELF, subject.TEST}):
            data = ("r2 original " + name).encode()
            pin = {"path": name, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
            files.append(dict(pin, base64=subject.base64.b64encode(data).decode()))
            if name in subject.FORMULA_RECONSTRUCTION_DELTAS:
                parent[name] = pin
        candidate = {"schema_version": "hwpx-agent.p09-formula-reconstruction-source-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.FORMULA_RECONSTRUCTION_PARENT_PIN,
            "preimage_archive": subject.FORMULA_RECONSTRUCTION_ARCHIVE,
            "source_deltas": [dict(parent[name], bytes=parent[name]["bytes"]+1, sha256="6"*64)
                for name in sorted(subject.FORMULA_RECONSTRUCTION_DELTAS)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.FORMULA_RECONSTRUCTION_PARENT_PIN, "files": files}
        return candidate, archive, parent

    def test_formula_reconstruction_preserves_r2_and_changes_exact_six_reviewed_sources(self):
        candidate, archive, parent = self.formula_reconstruction()
        result = subject.formula_reconstruction_sources(candidate, archive, parent)
        self.assertEqual(set(result), set(parent))
        for name in subject.STORED_RECONSTRUCTION_DELTAS:
            self.assertEqual(result[name], parent[name])
        for pin in candidate["source_deltas"]:
            self.assertEqual(result[pin["path"]], pin)

    def test_formula_reconstruction_rejects_missing_extra_or_unchanged_delta(self):
        candidate, archive, parent = self.formula_reconstruction()
        for deltas in (candidate["source_deltas"][:-1], candidate["source_deltas"]+
                [parent["crates/fixture/src/unchanged.rs"]],
                [parent[name] for name in sorted(subject.FORMULA_RECONSTRUCTION_DELTAS)]):
            with self.assertRaisesRegex(ValueError, "REGRESSION_FORMULA_RECONSTRUCTION_DELTA_SCOPE"):
                subject.formula_reconstruction_sources(dict(candidate, source_deltas=deltas), archive, parent)

    def test_formula_reconstruction_rejects_foreign_parent_baseline_or_preimage_identity(self):
        candidate, archive, parent = self.formula_reconstruction()
        for field, value in (("baseline_build_pin", {}), ("parent_candidate_pin", {}),
                ("preimage_archive", subject.STORED_RECONSTRUCTION_ARCHIVE)):
            with self.assertRaisesRegex(ValueError, "REGRESSION_FORMULA_RECONSTRUCTION_CANDIDATE_SCOPE"):
                subject.formula_reconstruction_sources(dict(candidate, **{field: value}), archive, parent)
        for field in ("baseline_build_pin", "parent_candidate_pin"):
            with self.assertRaisesRegex(ValueError, "REGRESSION_FORMULA_RECONSTRUCTION_ARCHIVE_SCOPE"):
                subject.formula_reconstruction_sources(candidate, dict(archive, **{field: {}}), parent)

    def test_formula_reconstruction_requires_whole_original_bytes_and_exact_parent_pins(self):
        candidate, archive, parent = self.formula_reconstruction()
        bad = copy.deepcopy(archive)
        bad["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for item in (bad, dict(archive, files=archive["files"][:-1]),
                dict(archive, files=archive["files"]+[archive["files"][0]])):
            with self.assertRaises(ValueError):
                subject.formula_reconstruction_sources(candidate, item, parent)
        changed = copy.deepcopy(parent)
        changed[next(iter(subject.FORMULA_RECONSTRUCTION_DELTAS))]["sha256"] = "7"*64
        with self.assertRaisesRegex(ValueError, "REGRESSION_FORMULA_RECONSTRUCTION_PARENT_DRIFT"):
            subject.formula_reconstruction_sources(candidate, archive, changed)

    def test_formula_variant_keeps_failed_full_runtime_failed_and_r4_SQL_historical(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED",
                "stop_reason": "STOP_DURATION_LIMIT", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, self.names(), 120, source_variant="reconstruction-r3")
        receipt = json.loads(captured.getvalue())
        self.assertEqual(receipt["source_variant"], "reconstruction-r3")
        self.assertEqual(receipt["baseline_build_qualification"], "HISTORICAL_R4_NOT_NEW_SQL_BUILD")
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")
        self.assertIsNone(receipt["runtime_tests_executed"])

    def anchor_prefix_fixture(self):
        parent, files = {}, []
        for name in sorted(subject.ANCHOR_PREFIX_DELTAS | {subject.SELF, subject.TEST}):
            data = name.encode()
            pin = {"path": name, "bytes": len(data), "sha256": subject.hashlib.sha256(data).hexdigest()}
            files.append(dict(pin, base64=subject.base64.b64encode(data).decode()))
            if name in subject.ANCHOR_PREFIX_DELTAS:
                parent[name] = pin
        for name in subject.STORED_RECONSTRUCTION_DELTAS | subject.FORMULA_RECONSTRUCTION_DELTAS:
            parent[name] = {"path": name, "bytes": 4, "sha256": "3"*64}
        parent["crates/fixture/src/unchanged.rs"] = {"path": "crates/fixture/src/unchanged.rs", "bytes": 1, "sha256": "4"*64}
        candidate = {"schema_version": "hwpx-agent.p09-source-anchor-prefix-candidate/v1",
            "qualification": "SOURCE_CANDIDATE_ONLY_NOT_BUILD_RUNTIME_SQL_OR_GATE",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.ANCHOR_PREFIX_PARENT_PIN,
            "preimage_archive": subject.ANCHOR_PREFIX_ARCHIVE,
            "source_deltas": [dict(parent[name], bytes=parent[name]["bytes"]+1, sha256="6"*64)
                for name in sorted(subject.ANCHOR_PREFIX_DELTAS)]}
        archive = {"schema_version": "hwpx-agent.p09-stored-regression-source-preimages/v1",
            "baseline_build_pin": subject.contract.CURRENT_BUILD_PIN,
            "parent_candidate_pin": subject.ANCHOR_PREFIX_PARENT_PIN, "files": files}
        return candidate, archive, parent

    def test_anchor_prefix_changes_exact_two_sources_and_preserves_all_fourteen_parent_deltas(self):
        candidate, archive, parent = self.anchor_prefix_fixture()
        result = subject.anchor_prefix_sources(candidate, archive, parent)
        self.assertEqual(set(result), set(parent))
        for name in subject.STORED_RECONSTRUCTION_DELTAS | subject.FORMULA_RECONSTRUCTION_DELTAS:
            self.assertEqual(result[name], parent[name])
        for pin in candidate["source_deltas"]:
            self.assertEqual(result[pin["path"]], pin)
        self.assertEqual(subject.CASES["import-source-tests"][2], 12)
        self.assertEqual(subject.CASES["stored-form-tests"][2], 249)

    def test_anchor_prefix_rejects_missing_extra_duplicate_and_unchanged_deltas(self):
        candidate, archive, parent = self.anchor_prefix_fixture()
        deltas = candidate["source_deltas"]
        for changed in (deltas[:-1], deltas+[parent["crates/fixture/src/unchanged.rs"]],
                deltas+[deltas[0]], [parent[name] for name in sorted(subject.ANCHOR_PREFIX_DELTAS)]):
            with self.assertRaises(ValueError):
                subject.anchor_prefix_sources(dict(candidate, source_deltas=changed), archive, parent)

    def test_anchor_prefix_rejects_foreign_parent_baseline_archive_and_qualification(self):
        candidate, archive, parent = self.anchor_prefix_fixture()
        for field, value in (("parent_candidate_pin", {}), ("baseline_build_pin", {}),
                ("preimage_archive", subject.FORMULA_RECONSTRUCTION_ARCHIVE), ("qualification", "PASS")):
            with self.assertRaisesRegex(ValueError, "REGRESSION_ANCHOR_PREFIX_CANDIDATE_SCOPE"):
                subject.anchor_prefix_sources(dict(candidate, **{field: value}), archive, parent)
        for field in ("parent_candidate_pin", "baseline_build_pin"):
            with self.assertRaisesRegex(ValueError, "REGRESSION_ANCHOR_PREFIX_ARCHIVE_SCOPE"):
                subject.anchor_prefix_sources(candidate, dict(archive, **{field: {}}), parent)

    def test_anchor_prefix_requires_exact_whole_preimages_and_parent_source_identity(self):
        candidate, archive, parent = self.anchor_prefix_fixture()
        corrupt = copy.deepcopy(archive)
        corrupt["files"][0]["base64"] = subject.base64.b64encode(b"different").decode()
        for item in (corrupt, dict(archive, files=archive["files"][:-1]),
                dict(archive, files=archive["files"]+[archive["files"][0]])):
            with self.assertRaises(ValueError):
                subject.anchor_prefix_sources(candidate, item, parent)
        foreign = copy.deepcopy(parent)
        foreign[next(iter(subject.ANCHOR_PREFIX_DELTAS))]["sha256"] = "7"*64
        with self.assertRaisesRegex(ValueError, "REGRESSION_ANCHOR_PREFIX_PARENT_DRIFT"):
            subject.anchor_prefix_sources(candidate, archive, foreign)

    def test_anchor_prefix_variant_keeps_failed_runtime_failed_and_old_SQL_historical(self):
        captured = io.StringIO()
        def fake_run(task, destination, seconds):
            json.dump({"task": task, "state": "STOPPED_NOT_ACCEPTED",
                "stop_reason": "STOP_DURATION_LIMIT", "heavy_work_started": True}, captured)
            return 2
        with patch.object(subject.maintenance, "run", side_effect=fake_run):
            subject.run_owned("fixture", {}, self.names(), 120, source_variant="anchor-prefix-r4")
        receipt = json.loads(captured.getvalue())
        self.assertEqual(receipt["source_variant"], "anchor-prefix-r4")
        self.assertEqual(receipt["baseline_build_qualification"], "HISTORICAL_R4_NOT_NEW_SQL_BUILD")
        self.assertEqual(receipt["state"], "STOPPED_NOT_ACCEPTED")
        self.assertIsNone(receipt["runtime_tests_executed"])
