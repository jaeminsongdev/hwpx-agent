"""Current SQL receipt negatives: no SQL, compiler, formatter or subprocess."""
import ast
import base64
import copy
import hashlib
import json
import unittest

import conservative_maintenance as c
import current_authority_sql_receipts as subject


class CurrentAuthoritySQLReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def load(name):
            return json.loads((c.ROOT/name).read_text(encoding="utf-8-sig"))
        cls.build = load(subject.build_contract.CURRENT_BUILD_PIN["path"])
        cls.manifest = load(subject.MANIFEST)
        cls.runs = {slot: load(name) for slot, name in subject.CURRENT_RUNS.items()}
        cls.legacy = load("implementation/p09/evidence/p09-148-authority-consumer-run05.v1.json")
        cls.legacy_build = load("target/p09-121-resource-optimized/p143-issuer-product-build-r14.json")

    def check(self, run, case="trust", mode="original", outcome="unchanged"):
        subject.validate_current_case(run, self.build, self.manifest, case, mode, outcome)

    def bad(self):
        return copy.deepcopy(self.runs[("trust", "original")])

    def test_actual_current_three_original_cases_are_valid(self):
        for (case, mode), run in self.runs.items():
            self.check(run, case, mode)

    def test_exact_six_slots_preserved_and_three_changed_missing(self):
        self.assertEqual(len(subject.REQUIRED), 6)
        missing = subject.missing_replays(self.runs)
        self.assertEqual({(row["case"], row["input_mode"]) for row in missing},
            {(case, "numeric_derivative") for case in ("approval", "trust", "policy")})
        self.assertTrue(all(row["expected_outcome"] == "changed" for row in missing))

    def test_original_three_cannot_pass_required_replay_completion(self):
        with self.assertRaisesRegex(ValueError, "CURRENT_AUTHORITY_REQUIRED_REPLAYS_MISSING"):
            subject.require_all_replays(self.runs, self.build, self.manifest)

    def test_original_or_fake_receipts_cannot_fill_changed_slots(self):
        all_slots = {**self.runs, **{(case, "numeric_derivative"): self.runs[(case, "original")]
            for case in ("approval", "trust", "policy")}}
        with self.assertRaises(ValueError):
            subject.require_all_replays(all_slots, self.build, self.manifest)

    def test_old_r14_sql_receipt_is_not_current_r4(self):
        with self.assertRaises(ValueError):
            self.check(self.legacy)

    def test_unknown_scheme_or_case_rejected(self):
        import verify_formula_issuer_authority_current as audit
        with self.assertRaises(ValueError):
            audit.validate_case(self.runs[("trust", "original")], self.build, self.manifest,
                "trust", "original", "unchanged", scheme="future")
        with self.assertRaises(ValueError):
            self.check(self.runs[("trust", "original")], "future")

    def test_legacy_resource_branch_remains_unmodified(self):
        import verify_formula_issuer_authority_current as audit
        audit.validate_case(self.legacy, self.legacy_build, self.manifest, "trust", "original", "unchanged")
        with self.assertRaises(ValueError):
            audit.validate_case(self.runs[("trust", "original")], self.build, self.manifest,
                "trust", "original", "unchanged")

    def test_wrong_build_receipt_pin_and_executable_rejected(self):
        for target in ("receipt", "executable"):
            run = self.bad()
            if target == "receipt":
                run["compiled_build_binding"]["receipt_pin"]["sha256"] = "0"*64
            else:
                run["product_executable_pin"]["sha256"] = "0"*64
            with self.assertRaises(ValueError):
                self.check(run)

    def test_missing_source_or_helper_or_protected_coverage_rejected(self):
        for field, name in (("source_freeze", self.build["source_freeze"][0]["path"]),
                ("source_freeze", self.build["build_helper_freeze"][0]["path"]),
                ("protected_executables", self.build["executable_pin"]["path"])):
            run = self.bad()
            run[field] = [pin for pin in run[field] if pin["path"] != name]
            with self.assertRaises(ValueError):
                self.check(run)

    def test_current_percentage_policy_cannot_be_weakened_or_promoted(self):
        for key, value in (("minimum_available_ram_percent", 1), ("maximum_commit_used_percent", 100),
                ("host_child_aggregate_job_enforced", True), ("cpu_stop_percent", 100),
                ("container_memory_bytes", 1073741824)):
            run = self.bad()
            run["resource_policy"][key] = value
            with self.assertRaises(ValueError):
                self.check(run)

    def test_bool_integer_coercions_and_extra_policy_key_rejected(self):
        for mutation in ("bool", "extra", "sample"):
            run = self.bad()
            if mutation == "bool":
                run["resource_policy"]["logical_cpu_limit"] = True
            elif mutation == "extra":
                run["resource_policy"]["allow_unlimited"] = True
            else:
                run["pre_hash_stable_samples"] = True
            with self.assertRaises(ValueError):
                self.check(run)

    def test_unlimited_CPU_wrong_affinity_or_breakaway_rejected(self):
        for key, value in (("cpu_hard_cap_machine_percent", 100.0), ("affinity_mask", 65535),
                ("breakaway_disabled", False), ("verified", False)):
            run = self.bad()
            run["owned_host_job_profiles"][0]["limits_readback"][key] = value
            with self.assertRaises(ValueError):
                self.check(run)

    def test_job_memory_or_negative_peak_rejected(self):
        for key, value in (("job_private_limit_mib", 99999), ("peak_job_private_mib", -1)):
            run = self.bad()
            profile = run["owned_host_job_profiles"][0]
            profile["limits_readback" if key.startswith("job_private") else "last_job_accounting"][key] = value
            with self.assertRaises(ValueError):
                self.check(run)

    def test_missing_job_cleanup_or_watcher_rejected(self):
        for mutation in ("job", "watcher", "active", "absent"):
            run = self.bad()
            if mutation == "job":
                run["owned_host_job_profiles"][0]["job_handle_closed"] = False
            elif mutation == "watcher":
                run["resource_watcher_cleanup_confirmed"] = False
            elif mutation == "active":
                run["owned_host_job_profiles"][0]["last_job_accounting"]["active_processes"] = 1
            else:
                run["owned_host_job_profiles"] = []
            with self.assertRaises(ValueError):
                self.check(run)

    def test_nonfinite_resource_samples_rejected(self):
        for value in (float("nan"), float("inf"), True):
            run = self.bad()
            run["resource_samples"][0]["available_ram_percent"] = value
            with self.assertRaises(ValueError):
                self.check(run)

    def test_metadata_controls_and_security_fingerprint_rejected(self):
        for mutation in ("metadata", "fingerprint", "mutation"):
            run = copy.deepcopy(self.runs[("approval", "original")])
            if mutation == "metadata":
                run["probe_runs"][1]["result"]["checks"] = []
            elif mutation == "fingerprint":
                run["schema_controls"]["wrong_fingerprint"] = "1"*64
            else:
                run["schema_controls"]["schema_identity_or_triggers_mutated"] = True
            with self.assertRaises(ValueError):
                self.check(run, "approval")

    def test_component_native_product_or_Gate_promotion_rejected(self):
        for key in ("product_complete", "native_application_executed", "all_36_source_inputs_qualified"):
            run = self.bad()
            run[key] = True
            with self.assertRaises(ValueError):
                self.check(run)

    def test_pin_union_rejects_conflict_but_preserves_exact_unique_inputs(self):
        pin = self.build["source_freeze"][0]
        self.assertEqual(subject.merge_pins([[pin], [pin]]), {pin["path"]: pin})
        with self.assertRaisesRegex(ValueError, "CURRENT_AUTHORITY_PIN_CONFLICT"):
            subject.merge_pins([[pin], [{**pin, "sha256": "0"*64}]])

    def test_backend_and_original_receipt_failures_are_not_current_success(self):
        raw = json.loads((c.ROOT/"implementation/p09/evidence/p09-146-corpus-consumer-run10.v1.json").read_text())
        with self.assertRaises((ValueError, KeyError)):
            self.check(raw, "approval", "numeric_derivative", "changed")

    def test_whole_legacy_validator_changes_only_explicit_resource_branch(self):
        archive = json.loads((c.ROOT/subject.ARCHIVE).read_text(encoding="utf-8"))
        row = archive["files"][0]
        original = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        self.assertEqual(len(original), row["bytes"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), row["sha256"])
        expected = original.decode().replace("\r\n", "\n")
        expected = expected.replace("def validate_case(run, build, manifest, case, mode, outcome):\n",
            "def validate_case(run, build, manifest, case, mode, outcome, *, scheme=\"legacy\"):\n"
            "    require(scheme in {\"legacy\", \"current_r4\"}, \"authority_build_scheme_invalid\")\n", 1)
        expected = expected.replace('    policy = run["resource_policy"]\n',
            '    policy = run["resource_policy"]\n'
            '    if scheme == "current_r4":\n'
            '        from current_authority_sql_receipts import validate_current_resources\n'
            '        validate_current_resources(run, build)\n'
            '        return\n', 1)
        self.assertEqual(ast.dump(ast.parse((c.ROOT/row["path"]).read_text(encoding="utf-8"))), ast.dump(ast.parse(expected)))

    def test_replay_flag_cannot_override_failed_final_hash_watcher_or_state(self):
        from verify_current_authority_sql_receipts import receipt_exit_code
        row = {"state": "CURRENT_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE",
            "all_six_current_replays_validated": True, "source_freeze_exact_after": True,
            "resource_watcher_cleanup_confirmed": True, "resource_stop_reason": None}
        self.assertEqual(receipt_exit_code(row), 0)
        for key, value in (("state", "FAILED_NOT_ACCEPTED"), ("source_freeze_exact_after", False),
                ("resource_watcher_cleanup_confirmed", False), ("resource_stop_reason", "STOP_FIXTURE"),
                ("all_six_current_replays_validated", False)):
            self.assertEqual(receipt_exit_code({**row, key: value}), 3)
        self.assertEqual(receipt_exit_code({**row, "state": "PARTIAL_CURRENT_SQL_RECEIPT_AUDIT_REQUIRED_REPLAYS_MISSING"}), 3)
