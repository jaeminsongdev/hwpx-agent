"""P147 evidence-negative checks; not additional Rust/SQL/native executions."""
import base64
import copy
import json
import unittest

import verify_formula_issuer_live_current as audit


class LiveCurrentAudit(unittest.TestCase):
    def setUp(self):
        self.build = self.load(audit.BASE + "p143-issuer-product-build-r11.json")
        self.manifest = self.load(audit.EVIDENCE + "p09-77-document-import-active-security.source-progress.v1.json")
        self.original = self.load(audit.EVIDENCE + "p09-146-corpus-consumer-run05.v1.json")

    @staticmethod
    def load(path):
        return json.loads((audit.ROOT / path).read_text(encoding="utf-8-sig"))

    def test_actual_original_and_RAM_changed_receipts_match_scope(self):
        audit.validate_case(self.original, self.build, self.manifest, "original", "unchanged")
        changed = self.load(audit.EVIDENCE + "p09-146-corpus-consumer-run06.v1.json")
        audit.validate_case(changed, self.build, self.manifest, "numeric_derivative", "changed")

    def test_missing_live_check_is_rejected(self):
        bad = copy.deepcopy(self.original)
        bad["product_probe"]["result"]["checks"].pop()
        with self.assertRaises(ValueError):
            audit.validate_case(bad, self.build, self.manifest, "original", "unchanged")

    def test_product_native_or_unrelated_race_promotion_is_rejected(self):
        for key in ("product_complete", "native_application_executed", "issuer_provisioning_generation_race_qualified",
            "trust_revocation_consumer_qualified", "atomic_product_publication_qualified"):
            bad = copy.deepcopy(self.original)
            bad[key] = True
            with self.assertRaises(ValueError):
                audit.validate_case(bad, self.build, self.manifest, "original", "unchanged")

    def test_derivative_cannot_be_reported_as_original(self):
        bad = copy.deepcopy(self.original)
        bad["product_probe"]["result"]["source_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            audit.validate_case(bad, self.build, self.manifest, "original", "unchanged")

    def test_unexecuted_live_boundary_is_rejected(self):
        bad = copy.deepcopy(self.original)
        bad["actual_consumer_SQL_approval_revocation_and_duplicate_race_executed"] = False
        with self.assertRaises(ValueError):
            audit.validate_case(bad, self.build, self.manifest, "original", "unchanged")

    def test_wrong_history_or_resource_stop_is_rejected(self):
        for mutation in ("history", "resource", "exit", "cleanup"):
            bad = copy.deepcopy(self.original)
            if mutation == "history":
                bad["final_history"]["approval_revocations"] = 2
            elif mutation == "resource":
                bad["resource_stop_reason"] = "STOP_SUSTAINED_SYSTEM_CPU"
            elif mutation == "exit":
                bad["product_probe"]["exit_code"] = 1
            else:
                bad["container_removed"] = False
            with self.assertRaises(ValueError):
                audit.validate_case(bad, self.build, self.manifest, "original", "unchanged")

    def test_declared_extension_preserves_whole_original_consumer(self):
        archive = self.load("implementation/p09/source-archive/p09-146-pre-live-sql-consumer/source-preimages.v1.json")
        row = next(item for item in archive["files"] if item["path"] == audit.SOURCE)
        original = base64.b64decode("".join(row["base64_chunks"]), validate=True)
        current = (audit.ROOT / audit.SOURCE).read_text(encoding="utf-8")
        audit.authenticate_baseline(current, original)
        bad = current.replace("before == after &&", "before != after &&", 1)
        self.assertNotEqual(bad, current)
        with self.assertRaises(ValueError):
            audit.authenticate_baseline(bad, original)


if __name__ == "__main__":
    unittest.main()
