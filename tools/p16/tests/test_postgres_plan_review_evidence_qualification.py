import importlib.util
import json
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "postgres_plan_review_evidence_qualification.py"
SPEC = importlib.util.spec_from_file_location("p16_plan_review_evidence_qualification", SOURCE)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


class PlanReviewEvidenceQualificationContract(unittest.TestCase):
    def test_sources_are_unique_existing_and_cover_the_v13_boundary(self) -> None:
        sources = qualification.RUNTIME_SOURCES
        self.assertEqual(len(sources), len(set(sources)))
        for path in sources + qualification.GUARD_SOURCES:
            self.assertTrue((qualification.ROOT / path).is_file(), path)
        for required in (
            "crates/mcp-control-plane/src/postgres_plan_review.rs",
            "crates/mcp-control-plane/examples/postgres_plan_review_evidence_probe.rs",
            "migrations/postgres/0013_p16_plan_review_evidence.up.sql",
            "migrations/postgres/0013_p16_plan_review_evidence.down.sql",
            "tools/p16/run_postgres_plan_review_evidence_checks.py",
        ):
            self.assertIn(required, sources)

    def test_contract_keeps_host_and_hangul_claims_open(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn('"durable_plan_review_evidence": True', text)
        self.assertIn('"registered_host": False', text)
        self.assertIn('"actual_hangul": False', text)
        self.assertIn('"phase_complete": False', text)

    def test_generated_contract_binds_current_sources_and_evidence(self) -> None:
        contract_path = qualification.QUALIFICATION / "contract.json"
        current_path = qualification.QUALIFICATION / "current-db.json"
        self.assertTrue(contract_path.is_file())
        self.assertTrue(current_path.is_file())
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["qualification_id"],
                         "p16.plan-review-evidence.v13.20260906.v1")
        self.assertEqual(contract["evidence"]["canonical_sha256"],
                         qualification.digest(current_path))
        for locked in contract["runtime_sources"] + contract["guard_sources"]:
            path = qualification.ROOT / locked["path"]
            self.assertEqual(path.stat().st_size, locked["bytes"], locked["path"])
            self.assertEqual(qualification.digest(path), locked["sha256"], locked["path"])
        canonical = qualification.canonical(
            json.loads(current_path.read_text(encoding="utf-8")))
        self.assertEqual(current_path.read_bytes(), canonical)


if __name__ == "__main__":
    unittest.main()
