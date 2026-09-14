from __future__ import annotations

from pathlib import Path
import unittest
from unittest import mock

from tools.p06 import finalize_table_pending_22_visual_review as finalizer
from tools.p06 import render_table_pending_22_target_batch as render


def manifest_case(feature_id: str, group_id: str) -> dict[str, object]:
    case_id = f"table-{feature_id.removeprefix('TABLE-').lower()}-fixture"
    return {
        "feature_id": feature_id,
        "case_id": case_id,
        "group_id": group_id,
        "pdf_file": f"{case_id}.hancom-2020-render.pdf",
        "pdf_sha256": "a" * 64,
        "pdf_metadata": {
            "pages": 1,
            "page_size_points": [595.0, 841.0],
            "page_rotation": 0,
            "encrypted": False,
            "pdf_version": "1.4",
            "creator": "Hwp 2020 11.0.0.9136",
            "producer": "Hancom PDF 1.3.0.550",
        },
        "png_file": f"rendered/{feature_id.lower()}-{case_id}.png",
        "bytes": 100,
        "sha256": "b" * 64,
        "pixel_size": [1190, 1682],
        "visual_review_state": "not_run",
    }


def success_manifest() -> dict[str, object]:
    return {
        "schema_version": render.OUTPUT_SCHEMA,
        "state": "rendered_not_reviewed",
        "scope": "current_pc_exact_hancom_2020_pending_22_review_candidates",
        "target": render.EXPECTED_TRACE_TARGET,
        "trace_sha256": "c" * 64,
        "oracle_receipt_sha256": "d" * 64,
        "renderer": "pdftoppm 26.07.0",
        "pdf_inspector": "pdfinfo 26.07.0",
        "dpi": 144,
        "case_count": 22,
        "cases": [
            manifest_case(feature_id, group_id)
            for feature_id, group_id in zip(
                render.EXPECTED_FEATURES, render.EXPECTED_GROUPS, strict=True
            )
        ],
        "visual_review": {
            "state": "not_run",
            "required_detail": "original",
            "all_pages_inspected": False,
            "clipping": "unverified",
            "overlap": "unverified",
            "blank_pages": "unverified",
            "black_boxes": "unverified",
        },
        "not_claimed": {
            "render_diff": False,
            "direct_oracle_promotion": False,
            "automation_runtime": False,
            "differential": False,
            "p06_09_complete": False,
            "p06_complete": False,
            "product_complete": False,
        },
    }


def success_observations(
    manifest: dict[str, object], manifest_sha256: str = "e" * 64
) -> dict[str, object]:
    cases = manifest["cases"]
    assert isinstance(cases, list)
    return {
        "schema_version": finalizer.OBSERVATION_SCHEMA,
        "state": "pass",
        "render_manifest_sha256": manifest_sha256,
        "review_actor": "assistant_visual_review",
        "inspection_detail": "original",
        "all_pages_inspected": True,
        "computer_use_click_or_type_invoked": False,
        "user_access_prompt_action": finalizer.ACCESS_PROMPT_ACTION,
        "cases": [
            {
                "feature_id": case["feature_id"],
                "case_id": case["case_id"],
                "png_sha256": case["sha256"],
                "png_bytes": case["bytes"],
                "pixel_size": case["pixel_size"],
                "state": "pass",
                "clipping": False,
                "overlap": False,
                "blank_page": False,
                "black_boxes": False,
                "finding": f"{case['feature_id']} table and text are visible.",
            }
            for case in cases
        ],
        "not_claimed": finalizer.NOT_CLAIMED,
    }


class Pending22VisualReviewFinalizerTests(unittest.TestCase):
    @staticmethod
    def artifact_digest(path: Path, *_: object) -> str:
        if path.name == finalizer.TRACE_NAME:
            return "c" * 64
        if path.name == finalizer.ORACLE_RECEIPT_NAME:
            return "d" * 64
        return "a" * 64

    def validate_manifest(self, manifest: dict[str, object]) -> list[dict[str, object]]:
        attempt = (
            render.TARGET_ROOT
            / "p06-09-table-pending-22-target-20990101-99"
        )
        with (
            mock.patch.object(render, "exact_group_root", return_value=Path("C:/group")),
            mock.patch.object(render, "bounded_existing", side_effect=lambda path, *_: path),
            mock.patch.object(render, "sha256_file", side_effect=self.artifact_digest),
            mock.patch.object(
                render,
                "png_identity",
                return_value={
                    "bytes": 100,
                    "sha256": "b" * 64,
                    "pixel_size": [1190, 1682],
                },
            ),
        ):
            return finalizer.validate_manifest(manifest, "e" * 64, attempt)

    def test_success_binds_all_22_and_builds_non_gate_receipt(self) -> None:
        manifest = success_manifest()
        cases = self.validate_manifest(manifest)
        observations = success_observations(manifest)
        reviews = finalizer.validate_observations(
            observations, "e" * 64, cases
        )
        receipt = finalizer.build_receipt(
            "p06-09-table-pending-22-target-20990101-99",
            "e" * 64,
            "f" * 64,
            manifest,
            cases,
            reviews,
        )
        self.assertEqual(receipt["case_count"], 22)
        self.assertEqual(receipt["feature_ids"], list(render.EXPECTED_FEATURES))
        self.assertEqual(
            receipt["gate_decision"]["direct_feature_stage"], "oracle_verified"
        )
        self.assertEqual(receipt["gate_decision"]["automation_runtime"], "not_run")
        self.assertEqual(receipt["gate_decision"]["p06"], "in_progress")
        self.assertFalse(
            receipt["review_observations"]["computer_use_click_or_type_invoked"]
        )
        self.assertEqual(
            receipt["review_observations"]["user_access_prompt_action"],
            "user_attested_allow_all",
        )

    def test_manifest_rejects_extra_key(self) -> None:
        manifest = success_manifest()
        manifest["unexpected"] = False
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "render_manifest_shape_mismatch"
        ):
            self.validate_manifest(manifest)

    def test_manifest_rejects_feature_reordering(self) -> None:
        manifest = success_manifest()
        cases = manifest["cases"]
        assert isinstance(cases, list)
        cases[0], cases[1] = cases[1], cases[0]
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "render_case_boundary_mismatch"
        ):
            self.validate_manifest(manifest)

    def test_manifest_rejects_png_identity_drift(self) -> None:
        manifest = success_manifest()
        attempt = render.TARGET_ROOT / "p06-09-table-pending-22-target-20990101-99"
        with (
            mock.patch.object(render, "exact_group_root", return_value=Path("C:/group")),
            mock.patch.object(render, "bounded_existing", side_effect=lambda path, *_: path),
            mock.patch.object(render, "sha256_file", side_effect=self.artifact_digest),
            mock.patch.object(
                render,
                "png_identity",
                return_value={
                    "bytes": 100,
                    "sha256": "9" * 64,
                    "pixel_size": [1190, 1682],
                },
            ),
        ):
            with self.assertRaisesRegex(
                finalizer.VisualReviewError, "png_identity_mismatch"
            ):
                finalizer.validate_manifest(manifest, "e" * 64, attempt)

    def test_artifact_recheck_rejects_late_png_drift(self) -> None:
        manifest = success_manifest()
        attempt = render.TARGET_ROOT / "p06-09-table-pending-22-target-20990101-99"
        with (
            mock.patch.object(render, "exact_group_root", return_value=Path("C:/group")),
            mock.patch.object(render, "bounded_existing", side_effect=lambda path, *_: path),
            mock.patch.object(render, "sha256_file", side_effect=self.artifact_digest),
            mock.patch.object(
                render,
                "png_identity",
                return_value={
                    "bytes": 100,
                    "sha256": "8" * 64,
                    "pixel_size": [1190, 1682],
                },
            ),
        ):
            with self.assertRaisesRegex(
                finalizer.VisualReviewError, "png_recheck_mismatch"
            ):
                finalizer.recheck_artifacts(attempt, manifest)

    def test_observations_require_all_pages(self) -> None:
        manifest = success_manifest()
        cases = self.validate_manifest(manifest)
        observations = success_observations(manifest)
        observations["all_pages_inspected"] = False
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "observations_boundary_mismatch"
        ):
            finalizer.validate_observations(observations, "e" * 64, cases)

    def test_observations_reject_any_visual_defect(self) -> None:
        manifest = success_manifest()
        cases = self.validate_manifest(manifest)
        observations = success_observations(manifest)
        review_cases = observations["cases"]
        assert isinstance(review_cases, list)
        review_cases[7]["clipping"] = True
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "observation_case_boundary_mismatch"
        ):
            finalizer.validate_observations(observations, "e" * 64, cases)

    def test_observations_reject_control_characters_in_findings(self) -> None:
        manifest = success_manifest()
        cases = self.validate_manifest(manifest)
        observations = success_observations(manifest)
        review_cases = observations["cases"]
        assert isinstance(review_cases, list)
        review_cases[0]["finding"] = "line one\nline two"
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "observation_case_boundary_mismatch"
        ):
            finalizer.validate_observations(observations, "e" * 64, cases)

    def test_attempt_file_boundary_is_exact(self) -> None:
        path = (
            render.TARGET_ROOT
            / "p06-09-table-pending-22-target-20990101-99"
            / finalizer.RENDER_MANIFEST_NAME
        )
        self.assertEqual(finalizer.require_exact_attempt_file(path, path.name), path.parent)
        with self.assertRaisesRegex(
            finalizer.VisualReviewError, "attempt_file_boundary_mismatch"
        ):
            finalizer.require_exact_attempt_file(path.with_name("other.json"), path.name)


if __name__ == "__main__":
    unittest.main()
