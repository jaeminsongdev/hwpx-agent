"""Light P149 policy/boundary checks, plus an owned waiting-process Job Object smoke."""
import ctypes
import hashlib
import math
from pathlib import Path
import subprocess
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conservative_maintenance as c


class PolicyTests(unittest.TestCase):
    def row(self, cpu=10, ram=30, commit=40):
        return {"system_cpu_percent": cpu, "available_ram_percent": ram, "commit_used_percent": commit}

    def test_normal_background_cpu_does_not_block_admission(self):
        count = c.admitted_count(self.row(cpu=75), 0)
        self.assertLess(count, c.POLICY["start_consecutive_samples"])
        self.assertEqual(c.admitted_count(self.row(ram=9.99), count), 0)
        self.assertEqual(c.admitted_count(self.row(cpu=75, ram=10), count), 2)
        self.assertNotIn("start_cpu_max_percent", c.POLICY)
        self.assertNotIn("stop_ram_min_mib", c.POLICY)

    def test_cpu_emergency_is_not_a_normal_load_cutoff(self):
        self.assertEqual(c.decision(self.row(cpu=75), 0), (0, None))
        self.assertEqual(c.decision(self.row(cpu=98), 2), (3, None))
        self.assertEqual(c.decision(self.row(cpu=98), 3), (4, "STOP_SUSTAINED_SYSTEM_CPU"))
        self.assertEqual(c.decision(self.row(cpu=97.99), 3), (0, None))

    def test_ram_stops_and_invalid_observations_fail_closed(self):
        self.assertEqual(c.decision(self.row(ram=7.99), 0)[1], "STOP_LOW_AVAILABLE_RAM")
        self.assertIsNone(c.decision(self.row(ram=8), 0)[1])
        self.assertEqual(c.decision(self.row(commit=95), 0)[1], "STOP_SYSTEM_COMMIT_PRESSURE")
        row = dict(self.row(), peak_job_private_percent=7)
        self.assertEqual(c.decision(row, 0)[1], "STOP_OWNED_JOB_MEMORY_BUDGET")
        for cpu, ram in [(math.nan, 30), (101, 30), (-1, 30), (10, math.inf), (10, -1), (True, 30)]:
            with self.subTest(cpu=cpu, ram=ram), self.assertRaisesRegex(ValueError, "OBSERVATION_INVALID"):
                c.decision(self.row(cpu, ram), 0)

    def test_only_five_scoped_non_sql_non_native_tasks(self):
        self.assertEqual(set(c.TASKS), {"domain-check", "domain-tests", "formula-tests", "comment-tests", "product-check"})
        for command in c.TASKS.values():
            self.assertIn(command[0], {"test", "check"})
            self.assertNotIn("--workspace", command)
            self.assertNotIn("form_stored_provider", command)

    def test_metadata_first_checks_the_changed_test_without_link_or_run(self):
        self.assertEqual(c.TASKS["domain-check"],
            ["check", "-p", "domain-ir", "--lib", "--test", "document_graph"])
        self.assertEqual(c.POLICY["dev_debug_info"], "line-tables-only")
        self.assertTrue({"crates/domain-ir/Cargo.toml", "crates/hwpx-package/Cargo.toml",
            "crates/hwpx-package/tests/document_import_formula_evaluation.rs",
            "crates/hwpx-package/tests/support/document_import_formula_evaluation_fixture.rs",
            "crates/hwpx-package/tests/support/document_import_settings_inputs.rs",
            "crates/hwpx-package/tests/support/document_import_field_fixture.rs",
            "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json"
            }.issubset(c.SOURCES))
        self.assertTrue({"crates/product-cli/Cargo.toml", "crates/product-cli/src/lib.rs",
            "crates/product-cli/tests/comment_operation.rs",
            "crates/product-cli/tests/comment_operation/rich_bodies.rs"}.issubset(c.SOURCES))
        source = Path(c.__file__).read_text(encoding="utf-8")
        for binding in ['CARGO_PROFILE_DEV_DEBUG=POLICY["dev_debug_info"]',
                'CARGO_PROFILE_DEV_DEBUG_ASSERTIONS="true"',
                'CARGO_PROFILE_DEV_OVERFLOW_CHECKS="true"', 'CARGO_PROFILE_DEV_CODEGEN_UNITS="1"']:
            self.assertIn(binding, source)

    def test_compiler_debug_allocation_change_keeps_runtime_guards(self):
        self.assertEqual(c.POLICY["test_debug_info"], "line-tables-only")
        self.assertEqual(c.POLICY["test_opt_level"], 0)
        self.assertEqual(c.POLICY["test_codegen_units"], 16)
        self.assertIs(c.POLICY["debug_assertions"], True)
        self.assertIs(c.POLICY["overflow_checks"], True)
        source = Path(c.__file__).read_text(encoding="utf-8")
        for binding in ['CARGO_PROFILE_TEST_DEBUG=POLICY["test_debug_info"]',
                'CARGO_PROFILE_TEST_DEBUG_ASSERTIONS="true"',
                'CARGO_PROFILE_TEST_OVERFLOW_CHECKS="true"',
                'CARGO_PROFILE_TEST_OPT_LEVEL=str(POLICY["test_opt_level"])',
                'CARGO_PROFILE_TEST_CODEGEN_UNITS=str(POLICY["test_codegen_units"])']:
            self.assertIn(binding, source)

    def test_archive_exact_and_read_only_clones_removed(self):
        import base64
        import json
        archive = json.loads((c.ROOT / "implementation/p09/source-archive/p09-149-pre-optimization/source-preimages.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(len(archive["files"]), 9)
        for row in archive["files"]:
            before = base64.b64decode(row["base64"], validate=True)
            self.assertEqual(len(before), row["bytes"])
            self.assertEqual(hashlib.sha256(before).hexdigest(), row["sha256"])
        equation = (c.ROOT / c.SOURCES[4]).read_text(encoding="utf-8")
        self.assertNotIn("meanings.graph().clone().into_draft()", equation)
        comment = (c.ROOT / c.SOURCES[5]).read_text(encoding="utf-8")
        self.assertNotIn("let draft = graph.clone().into_draft();", comment)
        self.assertIn("let mut draft = context.graph.clone().into_draft();", comment)
        self.assertIn("FullDocumentFormContext::bind", comment)
        rich = (c.ROOT / c.SOURCES[6]).read_text(encoding="utf-8")
        self.assertNotIn("base.graph.clone().into_draft().metadata", rich)
        self.assertIn("CommentOperationContext::bind", rich)

    def test_full_admission_reuses_validated_draft_only_after_exact_equality(self):
        source = (c.ROOT / "crates/product-cli/src/form_value_operation/full_document.rs").read_text(encoding="utf-8")
        bind = source.split("pub fn bind", 1)[1].split("Ok(Self", 1)[0]
        self.assertNotIn("from_draft(draft.clone()", bind)
        self.assertLess(bind.index("GraphBudget(0)"), bind.index("graph.clone().into_draft()"))
        self.assertLess(bind.index("if &validated != graph"), bind.index("let draft = validated.into_draft()"))
        self.assertLess(bind.index("expected_graph_sha256"), bind.index("let draft = validated.into_draft()"))
        for guard in ["reject_partial_review_and_settings", "draft.security_state.protected",
                "draft.security_state.encrypted", "draft.security_state.signed", "FORM_OPERATION_PROFILE"]:
            self.assertIn(guard, bind)

    def test_stored_metadata_and_review_location_paths_keep_exact_checks(self):
        for name in ["crates/product-cli/src/form_stored_provider/comments.rs",
                "crates/product-cli/src/form_stored_provider/comments/rich_bodies.rs"]:
            source = (c.ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("let draft = graph.clone().into_draft();", source)
            self.assertIn(".metadata()", source)
            self.assertIn("!= json", source)
        location = (c.ROOT / "crates/hwpx-package/src/document_import/structure/review/locations.rs").read_text(encoding="utf-8")
        self.assertNotIn("self.graph.clone().into_draft()", location)
        self.assertIn("self.verify_source(fresh)", location)
        self.assertIn("for note in self.graph.notes()", location)
        self.assertIn("if binding.0 != start.paragraph_anchor", location)

    def test_canonical_digest_streaming_not_whole_json_allocation(self):
        source = (c.ROOT / c.SOURCES[2]).read_text(encoding="utf-8")
        digest = source.split("pub fn canonical_sha256", 1)[1].split("#[must_use]", 1)[0]
        self.assertIn("32 * 1024", digest)
        self.assertIn("serde_json::to_writer", digest)
        self.assertIn("into_inner()", digest)
        self.assertNotIn("canonical_json()?", digest)
        self.assertIn("Validator::new(limits).validate(&draft)?", source)
        self.assertIn("canonicalize_catalogs(&mut draft)", source)
        canonical = source.split("pub fn canonical_json", 1)[1].split("pub fn canonical_sha256", 1)[0]
        size = source.split("fn validate_serialized_size", 1)[1].split("#[derive", 1)[0]
        shared_writer = "&mut writer as &mut dyn io::Write"
        self.assertIn(shared_writer + ", &self.0", canonical)
        self.assertIn(shared_writer + ", &self.0", digest)
        self.assertIn(shared_writer + ", draft", size)
        self.assertNotIn("serde_json::to_vec", canonical)
        self.assertIn("if writer.exceeded", size)
        self.assertIn("Err(DocumentGraphError::LimitExceeded)", size)

    @unittest.skipUnless(sys.platform == "win32", "Windows Job Object only")
    def test_real_owned_waiting_worker_job_limits_and_cleanup(self):
        windows = c.Windows()
        job = windows.job()
        process = None
        try:
            # No Cargo, SQL or native operation. Parent assigns the job before authorizing this child.
            process = subprocess.Popen([sys.executable, "-c", "import sys,time;sys.stdin.readline();time.sleep(0.1)"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
            handle = windows.k.OpenProcess(0x501, False, process.pid)
            self.assertTrue(handle)
            try:
                self.assertTrue(windows.k.AssignProcessToJobObject(job, handle))
                allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
                self.assertTrue(windows.k.GetProcessAffinityMask(handle, ctypes.byref(allowed), ctypes.byref(system)))
                self.assertEqual(allowed.value, windows.mask)
                self.assertEqual(windows.k.GetPriorityClass(handle), 0x4000)
                limits = c.ExtendedLimit()
                self.assertTrue(windows.k.QueryInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits), None))
                self.assertEqual(limits.job_memory, windows.memory_limit)
                self.assertEqual(limits.basic.flags & 0x2000, 0x2000)
                rate = c.CpuRate()
                self.assertTrue(windows.k.QueryInformationJobObject(job, 15, ctypes.byref(rate), ctypes.sizeof(rate), None))
                self.assertEqual(rate.flags, 5)
                self.assertEqual(rate.rate, windows.cpu_rate)
                roles = windows.owned_processes(job)
                self.assertTrue(any(row["pid"] == process.pid and row["memory_observed"] for row in roles))
                self.assertTrue(all("path" not in row for row in roles))
            finally:
                windows.k.CloseHandle(handle)
            process.communicate(input=b"GO\n", timeout=3)
            self.assertEqual(process.returncode, 0)
            self.assertTrue(windows.verify_job_limits(job)["verified"])
            # Windows job accounting may lag the signalled process handle briefly.
            deadline = time.monotonic() + 2
            while windows.accounting(job)["active_processes"] and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(windows.accounting(job)["active_processes"], 0)
        finally:
            windows.k.TerminateJobObject(job, 1)
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            windows.k.CloseHandle(job)

    @unittest.skipUnless(sys.platform == "win32", "Windows Job Object only")
    def test_owned_descendant_tree_is_killed_without_foreign_processes(self):
        windows = c.Windows()
        job = windows.job()
        process = None
        self.owned_console_helper_bindings = []
        try:
            code = ("import sys,subprocess,time;sys.stdin.readline();"
                "subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],"
                "creationflags=subprocess.CREATE_NO_WINDOW);time.sleep(10)")
            process = subprocess.Popen([sys.executable, "-c", code], stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW)
            handle = windows.k.OpenProcess(0x101, False, process.pid)
            self.assertTrue(handle)
            try:
                self.assertTrue(windows.k.AssignProcessToJobObject(job, handle))
            finally:
                windows.k.CloseHandle(handle)
            process.stdin.write(b"GO\n")
            process.stdin.close()
            deadline = time.monotonic() + 2
            previous_inventory, stable_inventory_samples = None, 0
            while True:
                snapshot = windows.accounting(job)
                python = [row for row in snapshot["owned_processes"] if row["role"] == "python.exe"]
                inventory = (snapshot["active_processes"], tuple(sorted(
                    (row["pid"], row["role"]) for row in snapshot["owned_processes"])))
                stable_inventory_samples = stable_inventory_samples+1 if inventory == previous_inventory else 1
                previous_inventory = inventory
                if (len(python) == 2 and stable_inventory_samples >= 2) or time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
            # Observed Windows console-host membership is not an extra test worker.
            # Require exactly our two interpreters. Run05 observed one system helper per interpreter.
            # Helpers must be Job members with inherited limits AND the Windows system image below.
            self.assertEqual(len(python), 2)
            self.assertGreaterEqual(stable_inventory_samples, 2)
            self.assertTrue(any(row["pid"] == process.pid for row in python))
            console = [row for row in snapshot["owned_processes"] if row["role"] == "conhost.exe"]
            self.assertLessEqual(len(console), len(python))
            self.assertEqual(snapshot["active_processes"], len(python) + len(console))
            self.assertEqual(len(snapshot["owned_processes"]), len(python) + len(console))
            directory = ctypes.create_unicode_buffer(32768)
            windows.k.GetSystemDirectoryW.argtypes = [c.w.LPWSTR, c.w.UINT]
            windows.k.GetSystemDirectoryW.restype = c.w.UINT
            directory_length = windows.k.GetSystemDirectoryW(directory, len(directory))
            self.assertTrue(0 < directory_length < len(directory))
            console_image = Path(directory.value) / "conhost.exe"
            for row in snapshot["owned_processes"]:
                handle = windows.k.OpenProcess(0x400, False, row["pid"])
                self.assertTrue(handle)
                try:
                    allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
                    self.assertTrue(windows.k.GetProcessAffinityMask(handle, ctypes.byref(allowed), ctypes.byref(system)))
                    self.assertEqual(allowed.value, windows.mask)
                    self.assertEqual(windows.k.GetPriorityClass(handle), 0x4000)
                    if row["role"] == "conhost.exe":
                        image, length = ctypes.create_unicode_buffer(32768), c.w.DWORD(32768)
                        self.assertTrue(windows.k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length)))
                        matches = Path(image.value).resolve() == console_image.resolve()
                        self.owned_console_helper_bindings.append({"pid": row["pid"],
                            "system_image_match": matches, "affinity_matches": allowed.value == windows.mask,
                            "priority_matches": windows.k.GetPriorityClass(handle) == 0x4000})
                        self.assertTrue(matches)
                finally:
                    windows.k.CloseHandle(handle)
            self.assertTrue(windows.k.TerminateJobObject(job, 1))
            process.wait(timeout=2)
            deadline = time.monotonic() + 2
            while windows.accounting(job)["active_processes"] and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(windows.accounting(job)["active_processes"], 0)
        finally:
            try:
                self.assertTrue(windows.k.TerminateJobObject(job, 1))
                if process and process.poll() is None:
                    process.kill()
                    process.wait(timeout=2)
                deadline = time.monotonic() + 2
                while windows.accounting(job)["active_processes"] and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertEqual(windows.accounting(job)["active_processes"], 0)
            finally:
                windows.k.CloseHandle(job)


if __name__ == "__main__":
    unittest.main()
