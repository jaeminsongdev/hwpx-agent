from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
P16_TOOLS = ROOT / "tools/p16"
sys.path.insert(0, str(P16_TOOLS))
import build_official_source_contract as builder  # noqa: E402
import validate_official_source_contract as validator  # noqa: E402


class OfficialSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_lock = json.loads(builder.SOURCE_LOCK_PATH.read_text(encoding="utf-8"))
        cls.contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))

    def errors(self, source_lock: dict | None = None, contract: dict | None = None) -> list[str]:
        return validator.validate(
            self.source_lock if source_lock is None else source_lock,
            self.contract if contract is None else contract,
        )

    def test_generated_artifacts_are_valid(self) -> None:
        self.assertEqual([], self.errors())

    def test_source_lock_matches_builder_exactly(self) -> None:
        self.assertEqual(builder.build_source_lock(), self.source_lock)

    def test_contract_matches_builder_exactly(self) -> None:
        self.assertEqual(builder.build_contract(self.source_lock), self.contract)

    def test_mutable_document_digest_drift_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["mutable_documents"][0]["sha256"] = "0" * 64
        self.assertIn("source_lock.exact", self.errors(changed))

    def test_non_official_mutable_document_host_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["mutable_documents"][0]["url"] = "https://example.invalid/plugin-ui"
        errors = self.errors(changed)
        self.assertIn("mutable_documents[0].url", errors)
        self.assertIn("source_lock.exact", errors)

    def test_duplicate_document_url_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["mutable_documents"][1]["url"] = changed["mutable_documents"][0]["url"]
        self.assertIn("mutable_documents.urls_unique", self.errors(changed))

    def test_unpinned_git_commit_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["immutable_sources"][0]["commit"] = "main"
        self.assertIn("immutable_sources[0].commit", self.errors(changed))

    def test_package_integrity_drift_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["package_locks"][0]["integrity"] = "unverified"
        self.assertIn("package_locks[0].integrity", self.errors(changed))

    def test_missing_requirement_is_rejected(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["requirements"].pop()
        errors = self.errors(changed)
        self.assertIn("requirements.count", errors)
        self.assertIn("requirements.order", errors)

    def test_window_openai_cannot_replace_portable_bridge(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["portable_bridge"] = "window.openai"
        self.assertIn("portable_bridge", self.errors(changed))

    def test_unverified_evidence_cannot_be_promoted(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["deferred_evidence"][0]["state"] = "pass"
        self.assertIn("deferred_evidence", self.errors(changed))

    def test_contract_cannot_claim_unimplemented_widget(self) -> None:
        changed = deepcopy(self.contract)
        changed["claims"]["widget_implemented"] = True
        errors = self.errors(contract=changed)
        self.assertIn("contract.claims.widget_implemented", errors)
        self.assertIn("contract.exact", errors)

    def test_requirements_cover_every_required_category(self) -> None:
        categories = {entry["category"] for entry in self.source_lock["requirements"]}
        self.assertEqual(validator.REQUIRED_CATEGORIES, categories)

    def test_csp_wildcard_is_rejected_without_confusing_ui_method_notation(self) -> None:
        self.assertTrue(any("ui/*" in entry["statement"] for entry in self.source_lock["requirements"]))
        changed = deepcopy(self.source_lock)
        changed["csp_policy"]["connect_domains"] = ["https://*"]
        self.assertIn("csp_policy.connect_domains.wildcard", self.errors(changed))

    def test_csp_entry_must_be_an_https_origin_without_a_path(self) -> None:
        changed = deepcopy(self.source_lock)
        changed["csp_policy"]["resource_domains"] = ["https://static.example.com/assets"]
        self.assertIn("csp_policy.resource_domains.origin", self.errors(changed))

    def test_local_source_lock_order_is_exact(self) -> None:
        self.assertEqual(builder.LOCAL_SOURCE_PATHS, [entry["path"] for entry in self.contract["source_locks"]])


if __name__ == "__main__":
    unittest.main()
