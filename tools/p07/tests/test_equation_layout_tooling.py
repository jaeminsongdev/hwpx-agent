from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError("script import failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_script(
    "p07_layout_qualification_builder",
    "implementation/p07/tools/build-equation-layout-qualification.py",
)
RASTER = load_script(
    "p07_layout_raster_verifier",
    "implementation/p07/tools/verify-equation-layout-pdfs.py",
)


class EquationLayoutToolingTests(unittest.TestCase):
    def test_fixed_point_linear_fit_is_deterministic_and_exact(self) -> None:
        self.assertEqual(BUILDER.fit_linear([(2, 2000), (4, 3000)], 10_000), (0, 500, 1000))
        self.assertEqual(BUILDER.fit_linear([(2, 2001), (4, 2999)], 10_000), (0, 499, 1003))

    def test_mode_specific_baseline_fit_uses_predicted_height(self) -> None:
        samples = []
        for layout, percent in [("inline", 84), ("display", 86)]:
            for levels in range(1, 5):
                samples.append({
                    "layout": layout,
                    "height_hwpunit": 1000 + levels * 400,
                    "baseline_percent": percent,
                    "metrics": {
                        "above_levels": levels - 1,
                        "below_levels": 0,
                    },
                })
        self.assertEqual(BUILDER.fit_baseline("inline", samples, 1000, 400), (0, 84))
        self.assertEqual(BUILDER.fit_baseline("display", samples, 1000, 400), (0, 86))

    def test_duplicate_json_key_and_output_escape_fail_closed(self) -> None:
        with self.assertRaises(BUILDER.DuplicateKey):
            BUILDER.duplicate_guard([("a", 1), ("a", 2)])
        with tempfile.TemporaryDirectory() as directory:
            boundary = Path(directory).resolve()
            escaped = boundary.parent / "escape.json"
            with self.assertRaises(RASTER.VerificationError):
                RASTER.ensure_new_child(escaped, boundary, ".json", "EXPECTED")

    def test_target_scripts_keep_manual_review_as_a_separate_gate(self) -> None:
        raster = (ROOT / "implementation/p07/tools/verify-equation-layout-pdfs.py").read_text()
        builder = (
            ROOT / "implementation/p07/tools/build-equation-layout-qualification.py"
        ).read_text()
        self.assertIn('"manual_review_state": "not_run"', raster)
        self.assertIn('"qualification_eligible": False', raster)
        self.assertIn('manual.get("all_pages_inspected") is not True', builder)
        self.assertIn('"exact_sample_qualification_candidate": True', builder)
        self.assertIn('"verified_estimator_candidate": (', builder)

    def test_target_children_resolve_equation_parameter_set_after_document_activation(self) -> None:
        for relative in (
            "implementation/p07/tools/run-hancom-2020-equation-tier-b-child.ps1",
            "implementation/p07/tools/run-hancom-2020-equation-layout-child.ps1",
        ):
            with self.subTest(relative=relative):
                script = (ROOT / relative).read_text(encoding="utf-8")
                document_add = script.index("$document = $documents.Add($false)")
                document_activate = script.index("[void]$document.SetActive_XHwpDocument()")
                parameter_resolve = script.index(
                    "$parameterSet = Resolve-ParameterSetObject $parameters 'EqEdit'"
                )
                window_visible = script.index("$window.Visible = $true")
                save_as = script.index("$document.SaveAs($outputPath, 'HWPX', '')")
                self.assertLess(document_add, document_activate)
                self.assertLess(document_activate, parameter_resolve)
                self.assertLess(window_visible, save_as)
                self.assertEqual(script.count("Resolve-ParameterSetObject $parameters 'EqEdit'"), 2)
                self.assertIn("($DocumentedId + 'E')", script)
                self.assertIn("('H' + $DocumentedId)", script)
                self.assertIn("('H' + $DocumentedId + 'E')", script)
                self.assertIn("$hwp.RegisterModule(", script)
                self.assertIn("'FilePathCheckDLL', $securityModuleName", script)
                self.assertIn(
                    "9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6",
                    script,
                )
                self.assertIn("Clear-ComObject $window", script)
                self.assertIn("[void]$hwp.Clear(1)", script)
                self.assertIn("$hwp.Open($outputPath, 'HWPX'", script)
                self.assertEqual(script.count("$reopenSucceeded = $hwp.Open("), 1)
                self.assertNotIn("$document.Open($outputPath, 'HWPX'", script)
                self.assertIn("$documents.Item(([int]$documents.Count) - 1)", script)
                self.assertIn("$document = $documents.Item(0)", script)
                if relative.endswith("equation-layout-child.ps1"):
                    self.assertIn("$document.Close($false)", script)
                    self.assertIn("saved_waiting_readback", script)
                    self.assertIn("readback_pass_waiting_session_close", script)
                    self.assertIn("$trace.hwp_session_count = 3", script)
                    self.assertIn("display_register_state", script)
                    self.assertIn("P07_LAYOUT_DISPLAY_CREATE_SESSION_STARTED", script)
                    self.assertIn(
                        "$(if ($Layout -ceq 'inline') { 0 } else { 1 })", script
                    )
                else:
                    self.assertNotIn("$document.Close($false)", script)
                    self.assertIn("saved_waiting_create_session_close", script)
                    self.assertIn("readback_pass_waiting_session_close", script)
                self.assertIn("reopen_document_count_before", script)
                self.assertIn("reopen_document_count_after", script)
                self.assertGreaterEqual(
                    script.count("[void]$document.SetActive_XHwpDocument()"), 3
                )
                self.assertIn("$trace.hwp_session_count = 2", script)
                self.assertIn("create_session_quit_invoked = $false", script)
                self.assertIn("READBACK_SESSION_STARTED", script)
                self.assertNotIn("Get-FileHash", script)
                self.assertIn("$algorithm.ComputeHash($stream)", script)

    def test_target_parents_bound_timeout_cleanup_to_owned_automation_processes(self) -> None:
        for relative, timeout_error in (
            (
                "implementation/p07/tools/run-hancom-2020-equation-tier-b.ps1",
                "TIER_B_CHILD_TIMEOUT_EFFECT_UNKNOWN",
            ),
            (
                "implementation/p07/tools/run-hancom-2020-equation-layout.ps1",
                "LAYOUT_CHILD_TIMEOUT_EFFECT_UNKNOWN",
            ),
        ):
            with self.subTest(relative=relative):
                script = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("$childStartedAt = $childProcess.StartTime", script)
                self.assertIn("$childProcess.WaitForExit($TimeoutSeconds * 1000)", script)
                self.assertIn(timeout_error, script)
                self.assertIn("Stop-Process -Id ([int]$ChildProcess.Id)", script)
                self.assertIn("Stop-Process -Id ([int]$process.ProcessId)", script)
                self.assertIn("[datetime]$_.CreationDate -ge $cutoff", script)
                self.assertIn("-Automation", script)
                self.assertIn("-Embedding", script)
                self.assertNotIn("Get-Process Hwp | Stop-Process", script)

    def test_exact_evidence_chain_builds_a_loader_compatible_candidate(self) -> None:
        private = ROOT / "implementation/p07/evidence/private"
        with tempfile.TemporaryDirectory(prefix="p07-07-test-", dir=private) as directory:
            run = Path(directory)
            plan_samples = []
            target_samples = []
            raster_samples = []
            manual_samples = []
            for index in range(8):
                layout = "inline" if index < 4 else "display"
                mode_index = index % 4 + 1
                sample_id = f"{layout}-{mode_index:03d}"
                metrics = {
                    "advance_units": mode_index + 1,
                    "above_levels": mode_index - 1,
                    "below_levels": 0,
                    "nodes": mode_index,
                    "depth": mode_index,
                    "matrix_rows": 0,
                    "matrix_columns": 0,
                }
                semantic = hashlib.sha256(f"semantic-{mode_index}".encode()).hexdigest()
                plan_samples.append({
                    "id": sample_id, "ordinal": index, "layout": layout, "base_unit": 1000,
                    "semantic_sha256": semantic, "metrics": metrics,
                })
                target_samples.append({
                    "id": sample_id, "layout": layout,
                    "width_hwpunit": metrics["advance_units"] * 500 + 1000,
                    "height_hwpunit": (metrics["above_levels"] + 1) * 400 + 1000,
                    "baseline_percent": 84 if layout == "inline" else 86,
                    "native_readback_sha256": hashlib.sha256(f"native-{index}".encode()).hexdigest(),
                    "metrics": metrics,
                })
                png_sha = hashlib.sha256(f"png-{index}".encode()).hexdigest()
                raster_samples.append({
                    "id": sample_id, "ordinal": index, "layout": layout, "png_sha256": png_sha,
                    "ink_box": {
                        "page_width_pixels": 1190, "page_height_pixels": 1682,
                        "left": 100, "top": 100, "width": 200, "height": 80, "dpi": 144,
                    },
                })
                manual_samples.append({
                    "id": sample_id, "ordinal": index, "png_sha256": png_sha,
                    "clipping": False, "overlap": False, "silent_fallback": False,
                })

            plan = {
                "schema_version": BUILDER.PLAN_SCHEMA, "profile_version": BUILDER.PROFILE,
                "plan_sha256": "a" * 64, "samples": plan_samples,
            }
            plan_path = run / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            plan_file_sha = BUILDER.sha256_file(plan_path)
            target = {
                "schema_version": BUILDER.TARGET_SCHEMA, "profile_version": BUILDER.PROFILE,
                "state": "native_pass_visual_not_run", "plan_file_sha256": plan_file_sha,
                "samples": target_samples,
            }
            target_path = run / "target-evidence.json"
            target_path.write_text(json.dumps(target), encoding="utf-8")
            target_sha = BUILDER.sha256_file(target_path)
            raster = {
                "schema_version": BUILDER.RASTER_SCHEMA, "profile_version": BUILDER.PROFILE,
                "state": "structural_pass_manual_not_run", "manual_review_state": "not_run",
                "qualification_eligible": False, "all_pages_rasterized": True,
                "edge_contact_count": 0, "plan_file_sha256": plan_file_sha,
                "target_evidence_sha256": target_sha, "samples": raster_samples,
            }
            raster_path = run / "raster-evidence.json"
            raster_path.write_text(json.dumps(raster), encoding="utf-8")
            raster_sha = BUILDER.sha256_file(raster_path)
            manual = {
                "schema_version": BUILDER.MANUAL_SCHEMA, "profile_version": BUILDER.PROFILE,
                "plan_sha256": plan["plan_sha256"], "target_evidence_sha256": target_sha,
                "raster_evidence_sha256": raster_sha, "state": "pass",
                "inspection_detail": "original", "sample_count": 8,
                "samples": manual_samples, "all_pages_inspected": True,
                "clipping_count": 0, "overlap_count": 0, "silent_fallback_count": 0,
                "user_document_opened": False, "computer_use_click_or_type_invoked": False,
                "product_complete": False,
            }
            manual_path = run / "manual-review.json"
            manual_path.write_text(json.dumps(manual), encoding="utf-8")
            namespace = SimpleNamespace(
                run_directory=str(run), plan=str(plan_path), expected_plan_sha256=plan_file_sha,
                target_evidence=str(target_path), expected_target_evidence_sha256=target_sha,
                raster_evidence=str(raster_path), expected_raster_evidence_sha256=raster_sha,
                manual_review=str(manual_path),
                expected_manual_review_sha256=BUILDER.sha256_file(manual_path),
                output=str(run / "qualification.json"),
            )
            qualification, output = BUILDER.build(namespace)
            self.assertEqual(output, (run / "qualification.json").resolve())
            self.assertEqual(qualification["validation"]["extent_max_error_hwpunit"], 0)
            self.assertEqual(qualification["validation"]["baseline_max_error_hwpunit"], 0)
            self.assertEqual(len(qualification["exact_samples"]), 8)


if __name__ == "__main__":
    unittest.main()
