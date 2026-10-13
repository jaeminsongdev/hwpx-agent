"""P148 evidence-negative checks; not additional Rust, SQL or native executions."""
import base64
import copy
import json
import unittest

import verify_formula_issuer_authority_current as audit


class AuthorityCurrentAudit(unittest.TestCase):
    @staticmethod
    def load(path):
        return json.loads((audit.ROOT / path).read_text(encoding="utf-8-sig"))

    def setUp(self):
        self.build = self.load(audit.BASE + "p143-issuer-product-build-r14.json")
        self.manifest = self.load(audit.EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
        self.original = self.load(audit.EVIDENCE + "p09-148-authority-consumer-run05.v1.json")

    def check(self, run):
        audit.validate_case(run, self.build, self.manifest, "trust", "original", "unchanged")

    def test_actual_four_cases_match_scope(self):
        for number, case, mode, outcome in audit.CASES:
            run = self.load(audit.EVIDENCE + f"p09-148-authority-consumer-run{number:02}.v1.json")
            audit.validate_case(run, self.build, self.manifest, case, mode, outcome)

    def test_missing_actual_live_check_rejected(self):
        bad = copy.deepcopy(self.original)
        bad["product_probe"]["result"]["checks"].pop()
        with self.assertRaises(ValueError):
            self.check(bad)
        bad = copy.deepcopy(self.original)
        bad["probe_runs"][1]["result"]["checks"] = []
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_native_product_or_unrelated_race_promotion_rejected(self):
        for key in ("native_application_executed", "product_complete", "all_36_source_inputs_qualified",
                    "issuer_provisioning_generation_race_qualified", "atomic_product_publication_qualified"):
            # Only a root field is replaced; retain all nested evidence without cloning it.
            bad = dict(self.original)
            bad[key] = True
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_derivative_cannot_be_relabelled_original(self):
        bad = copy.deepcopy(self.original)
        bad["product_probe"]["result"]["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_unexecuted_or_wrong_authority_rejected(self):
        for key in ("trust_revocation_consumer_component_executed", "policy_revocation_consumer_component_executed"):
            bad = dict(self.original)
            bad[key] = not bad[key]
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_wrong_history_resource_exit_and_cleanup_rejected(self):
        for mutation in ("history", "resource", "exit", "cleanup"):
            bad = copy.deepcopy(self.original)
            if mutation == "history":
                bad["final_history"]["current_source_policy_revocations"] = 1
            elif mutation == "resource":
                bad["resource_stop_reason"] = "STOP_SUSTAINED_SYSTEM_CPU"
            elif mutation == "exit":
                bad["product_probe"]["exit_code"] = 1
            else:
                bad["container_removed"] = False
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_weakened_resource_policy_rejected(self):
        for key, value in (("cpu_stop_percent", 99), ("minimum_available_ram_mib", 1024),
                           ("post_hash_idle_RAM_min_mib", 4096), ("logical_cpu_limit", 16)):
            bad = copy.deepcopy(self.original)
            bad["resource_policy"][key] = value
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_declared_authority_extension_preserves_whole_approval_consumer(self):
        archive = self.load("implementation/p09/source-archive/p09-148-pre-live-authority/source-preimages.v1.json")
        row = next(r for r in archive["files"] if r["path"] == audit.SOURCE)
        original = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        current = (audit.ROOT / audit.SOURCE).read_text(encoding="utf-8")
        audit.authenticate_authority_delta(current, original)
        bad = current.replace("before == after &&", "before != after &&", 1)
        self.assertNotEqual(bad, current)
        with self.assertRaises(ValueError):
            audit.authenticate_authority_delta(bad, original)


class AuthorityTimeoutAudit(unittest.TestCase):
    def setUp(self):
        self.build = AuthorityCurrentAudit.load(audit.BASE + "p143-issuer-product-build-r14.json")
        self.manifest = AuthorityCurrentAudit.load(audit.EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
        self.failed = AuthorityCurrentAudit.load(audit.EVIDENCE + "p09-148-authority-consumer-run08.v1.json")

    def check(self, run):
        audit.validate_timeout_failure(run, self.build, self.manifest)

    def test_actual_timeout_remains_failure(self):
        self.check(self.failed)

    def test_actual_cpu_stop_is_distinct_and_three_samples_required(self):
        stopped = AuthorityCurrentAudit.load(audit.EVIDENCE + "p09-148-authority-consumer-run09.v1.json")
        audit.validate_timeout_failure(stopped, self.build, self.manifest,
            error_code="STOP_SUSTAINED_SYSTEM_CPU", observation_count=4)
        with self.assertRaises(ValueError):
            self.check(stopped)
        stopped["resource_samples"][-1]["system_cpu_percent"] = 84.99
        with self.assertRaises(ValueError):
            audit.validate_timeout_failure(stopped, self.build, self.manifest,
                error_code="STOP_SUSTAINED_SYSTEM_CPU", observation_count=4)

    def test_failure_or_post_hash_success_relabelling_rejected(self):
        for key, value in (("state", "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"),
                           ("source_freeze_exact_after", True), ("protected_executables_exact_after", True),
                           ("error_code", None)):
            bad = dict(self.failed)
            bad[key] = value
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_previous_exit_zero_cannot_be_consumer_success(self):
        for key in ("original_product_consumer_executed", "policy_revocation_consumer_component_executed",
                    "real_Ed25519_approval_signature_executed", "product_complete", "native_application_executed"):
            bad = dict(self.failed)
            bad[key] = True
            with self.assertRaises(ValueError):
                self.check(bad)
        bad = dict(self.failed)
        bad["product_probe"] = {"exit_code": 0}
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_wrong_identity_or_missing_cleanup_rejected(self):
        for key, value in (("source_index", 1), ("live_case", "trust"), ("container_removed", False),
                           ("product_executable_pin", {}), ("frozen_original_source_pin", {})):
            bad = dict(self.failed)
            bad[key] = value
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_changed_resource_limit_or_invented_sqlstate_rejected(self):
        bad = copy.deepcopy(self.failed)
        bad["resource_policy"]["cpu_stop_percent"] = 99
        with self.assertRaises(ValueError):
            self.check(bad)
        bad = copy.deepcopy(self.failed)
        bad["sqlstate"] = "40001"
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_raw_diagnostics_or_coerced_wait_value_rejected(self):
        for field, value in (("query", "redacted_test_marker"), ("blocked_count", False)):
            bad = copy.deepcopy(self.failed)
            bad["live_wait_observations"][0]["rows"][0][field] = value
            with self.assertRaises(ValueError):
                self.check(bad)


class OwnedAbsenceAudit(unittest.TestCase):
    def setUp(self):
        self.receipt = AuthorityCurrentAudit.load(audit.EVIDENCE + "p09-148-owned-absence-run01.v1.json")
        self.runs = {n: AuthorityCurrentAudit.load(audit.EVIDENCE + f"p09-148-authority-consumer-run{n:02}.v1.json")
                     for n in range(1, 6)}

    def check(self, receipt):
        audit.validate_owned_absence(receipt, self.runs)

    def test_actual_five_owned_run_ids_and_names_match(self):
        self.check(self.receipt)

    def test_missing_or_duplicated_absence_rejected(self):
        for duplicate in (False, True):
            bad = copy.deepcopy(self.receipt)
            if duplicate:
                bad["independent_absence_checks"][-1] = copy.deepcopy(bad["independent_absence_checks"][0])
            else:
                bad["independent_absence_checks"].pop()
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_other_container_reference_rejected(self):
        bad = copy.deepcopy(self.receipt)
        bad["independent_absence_checks"][0]["reference"] = "0" * 64
        with self.assertRaises(ValueError):
            self.check(bad)

    def test_presence_success_or_coerced_boolean_rejected(self):
        for field, value in (("absent", False), ("absent", 1), ("inspect_exit_code", 0),
                             ("inspect_exit_code", True), ("run", True)):
            bad = copy.deepcopy(self.receipt)
            bad["independent_absence_checks"][0][field] = value
            with self.assertRaises(ValueError):
                self.check(bad)

    def test_scope_promotion_and_changed_limits_rejected(self):
        for field in ("current_authority_cases_qualified", "native_application_executed", "product_complete",
                      "build_test_SQL_native_started"):
            bad = copy.deepcopy(self.receipt)
            bad[field] = True
            with self.assertRaises(ValueError):
                self.check(bad)
        bad = copy.deepcopy(self.receipt)
        bad["limits"]["affinity_mask"] = 65535
        with self.assertRaises(ValueError):
            self.check(bad)


if __name__ == "__main__":
    unittest.main()
