"""Read-only current-vs-accepted-build byte binding; no build/SQL/child or Gate PASS."""
import argparse
import json
from pathlib import Path
import re
import time

from conservative_maintenance import ROOT, require
from sql_percentage_resources import PercentageResources
from live_sql_evidence_reader import LiveSQLReader
from verify_live_sql_reader_light import freeze as helper_freeze
from verify_audit_evidence_io import self_resource


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", required=True)
    parser.add_argument("--run", type=int, choices=range(1, 100), default=1)
    args = parser.parse_args()
    resources = PercentageResources()
    require(Path.cwd().resolve() == ROOT and re.fullmatch(
        r"target/p09-121-resource-optimized/p143-issuer-product-build-r[1-9][0-9]*\.json", args.build), "binding_audit_scope")
    destination = ROOT/f"implementation/p09/evidence/p09-149-live-SQL-build-binding.run{args.run:02}.v1.json"
    require(not destination.exists() and destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction(), "fresh_build_binding_receipt_required")
    started, reader = time.monotonic(), None
    row = {"schema_version": "hwpx-agent.p09-live-SQL-build-binding/v1", "state": "NOT_RUN",
        "build_receipt": args.build, "source_inventory": 0, "protected_inventory": 0,
        "source_checked": 0, "protected_checked": 0, "source_drift_count": 0, "protected_drift_count": 0,
        "missing_or_link_count": 0, "public_code_drift_paths": [], "helper_freeze": [], "helper_freeze_exact_after": False,
        "observed_inputs_fresh_after": False, "compiler_build_binding_accepted": False,
        "actual_build_SQL_Docker_Cargo_native_or_child_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    row["self_resource_before"] = self_resource(resources.windows)
    try:
        resources.admit()
        row["helper_freeze"] = helper_freeze()
        script = Path(__file__).resolve()
        reader = LiveSQLReader(resources)
        row["audit_script_pin"] = reader.pin(script)
        build = reader.json(args.build)
        require(build["state"] == "PASS_PROBE_BUILD_ONLY_NOT_DB_OR_GATE" and build["exit_code"] == 0
            and build["source_freeze_exact_after"] and build["protected_executables_exact_after"]
            and len(build["source_freeze"]) == 842 and len(build["protected_executables"]) >= 37, "binding_build_contract_invalid")
        row["source_inventory"], row["protected_inventory"] = len(build["source_freeze"]), len(build["protected_executables"])
        for role, expected_rows in (("source", build["source_freeze"]), ("protected", build["protected_executables"]+[build["executable_pin"]])):
            for expected in expected_rows:
                require(set(expected) == {"path", "bytes", "sha256"}, "binding_pin_shape_invalid")
                try:
                    actual = reader.pin(expected["path"])
                except ValueError as error:
                    if str(error) != "sql_source_link_or_missing":
                        raise
                    row["missing_or_link_count"] += 1
                    continue
                row[role+"_checked"] += 1
                if actual != expected:
                    row[role+"_drift_count"] += 1
                    path = expected["path"]
                    if (path.startswith(("crates/", "tools/")) and path.endswith((".rs", ".py", ".toml"))) \
                            or path in {"Cargo.toml", "Cargo.lock"}:
                        require(len(row["public_code_drift_paths"]) < 128, "binding_drift_inventory_budget")
                        row["public_code_drift_paths"].append(path)
        reader.finish()
        row["observed_inputs_fresh_after"] = True
        row["helper_freeze_exact_after"] = row["helper_freeze"] == helper_freeze()
        require(row["helper_freeze_exact_after"], "binding_helper_source_drift")
        changed = row["source_drift_count"]+row["protected_drift_count"]+row["missing_or_link_count"]
        row["compiler_build_binding_accepted"] = changed == 0
        row["state"] = "INPUT_CHANGED_REBUILD_REQUIRED_NOT_SQL_OR_GATE" if changed else "PASS_CURRENT_BUILD_BYTES_ONLY_NOT_SQL_OR_GATE"
    except (OSError, ValueError, KeyError, KeyboardInterrupt) as error:
        row["state"] = "STOPPED_OR_FAILED_NOT_ACCEPTED"
        code = str(error) if isinstance(error, ValueError) else "binding_audit_observation_or_input_failure"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "redacted"
    finally:
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["resource_samples"] = resources.samples
        row["resource_stop_reason"] = resources.reason
        row["self_resource_after"] = self_resource(resources.windows)
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as output:
            json.dump(row, output, indent=2)
    print(json.dumps({key: row[key] for key in ("state", "source_checked", "source_drift_count", "protected_checked", "protected_drift_count", "missing_or_link_count", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
