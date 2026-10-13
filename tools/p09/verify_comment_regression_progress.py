"""P128 current comment regression receipts; no native/SQL/whole-product promotion."""
import importlib.util
import json
import re
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("p127_preserved", Path(__file__).with_name("verify_comment_style_guard_progress.py"))
P127 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P127)
ROOT, BASE = P127.ROOT, P127.OLD.R.BASE
SUITES = {"Model": ("comment_model", 10), "Operation": ("comment_operation", 16), "Stored": ("stored_comment_provider", 24)}
COMMON = ["crates/domain-ir/src/comment_model.rs", "crates/product-cli/src/comment_operation.rs",
          "crates/product-cli/src/comment_operation/rich_bodies.rs", "crates/product-cli/src/form_stored_provider/comments.rs",
          "crates/product-cli/src/form_stored_provider/comments/rich_bodies.rs", "tools/p09/run_comment_regression.ps1"]
EXTRA = {"Model": ["crates/domain-ir/tests/comment_model.rs"],
         "Operation": ["crates/product-cli/tests/comment_operation.rs", "crates/product-cli/tests/comment_operation/rich_bodies.rs"],
         "Stored": ["crates/product-cli/tests/stored_comment_provider.rs", "crates/product-cli/tests/stored_comment_provider/rich_bodies.rs",
                    "crates/product-cli/tests/stored_comment_provider/comment_fixture.rs", "crates/product-cli/tests/stored_comment_provider/store_fixture.rs"]}


def require(value, code):
    if not value: raise ValueError(code)


def validate_runtime(doc, suite, mode):
    require(suite in SUITES and mode in ("Build", "Test"), "unsupported_scope")
    test, count = SUITES[suite]
    require(doc["schema_version"] == "hwpx-agent.p09-comment-regression/v1"
            and doc["state"] == "PASS_SOURCE_ONLY_NOT_GATE" and doc["suite"] == suite and doc["mode"] == mode
            and type(doc["expected_test_count"]) is int and doc["expected_test_count"] == count
            and doc["exit_code"] == 0 and doc["stop_reason"] is None and doc["source_freeze_exact_after"] is True,
            "runtime_not_accepted")
    require(doc["logical_cpu_limit"] == 1 and doc["affinity_mask"] == 1 and doc["priority"] == "BelowNormal"
            and doc["cargo_jobs"] == 1 and doc["sample_seconds"] == 2 and doc["cpu_stop_percent"] == 85
            and doc["cpu_stop_consecutive_samples"] == 3 and doc["minimum_available_ram_mib"] == 4096
            and doc["maximum_root_working_set_mib"] == 2048
            and 0 < doc["elapsed_seconds"] <= doc["maximum_seconds"], "resource_policy_drift")
    hot = 0
    require(doc["samples"], "resource_samples_missing")
    for sample in doc["samples"]:
        cpu = sample["system_cpu_percent"]
        hot = hot + 1 if cpu >= 85 else 0
        require(0 <= cpu <= 100 and hot < 3 and sample["available_ram_mib"] >= 4096
                and 0 <= sample["test_working_set_mib"] <= 2048, "observed_resource_guard_violated")
    rows = doc["source_freeze"]
    require(len(rows) == len(COMMON + EXTRA[suite]) and {r["path"] for r in rows} == set(COMMON + EXTRA[suite])
            and all(BASE.exact(r) for r in rows), "runtime_source_drift")
    require(doc["product_complete"] is False and doc["P09_gate"] == "OPEN", "scope_promoted")
    if mode == "Build":
        require(doc["build_marker"] is True and doc["tests"] is None, "build_marker_drift")
    else:
        tests, pin = doc["tests"], doc["executable_pin"]
        require(re.fullmatch(r"target/p09-121-resource-optimized/debug/deps/" + re.escape(test) + r"-[0-9a-f]{16}\.exe", pin["path"])
                and BASE.exact(pin), "test_executable_drift")
        summary = tests["terminal_summary"]
        require(summary["outcome"] == "ok" and summary["passed"] == count and summary["failed"] == 0
                and summary["ignored"] == 0 and summary["measured"] == 0 and summary["filtered"] == 0
                and len(tests["passed_test_names"]) == count and len(set(tests["passed_test_names"])) == count
                and not tests["failed_test_names"], "test_coverage_drift")
    return {"suite": suite, "mode": mode, "test_count": count if mode == "Test" else 0, "P09_gate": "OPEN"}


if __name__ == "__main__":
    try:
        P127.current()
        result = []
        for suite in SUITES:
            for mode in ("Build", "Test"):
                path = ROOT / f"target/p09-121-resource-optimized/p128-{suite.lower()}-{'build' if mode == 'Build' else 'tests'}-a.json"
                result.append(validate_runtime(json.loads(path.read_bytes()), suite, mode))
        print(json.dumps({"state": "PASS_COMMENT_REGRESSION50_NOT_NATIVE_OR_GATE", "results": result,
                          "P09_gate": "OPEN", "product_complete": False}, separators=(",", ":")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"state": "FAIL_CLOSED", "error_type": type(error).__name__, "P09_gate": "OPEN"}))
        raise SystemExit(1) from None
