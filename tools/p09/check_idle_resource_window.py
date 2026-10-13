"""P09 opt-in idle admission before heavy work; no build/test/DB/UI is started here."""
import argparse
import json
from pathlib import Path
import re
import time

from run_formula_issuer_registry_sql_checks import ROOT, Resources, pin, require

CPU_MAX = 50
RAM_MIN_MIB = 8192
REQUIRED = 3
SAMPLE_SECONDS = 2
MAX_SECONDS = 20
SOURCES = [
    "tools/p09/check_idle_resource_window.py",
    "tools/p09/run_formula_issuer_registry_sql_checks.py",
    "tools/p14/test_postgres_migrations.py",
]


def stable_count(previous, sample):
    return previous + 1 if sample["system_cpu_percent"] <= CPU_MAX and sample["available_ram_mib"] >= RAM_MIN_MIB else 0


def main(receipt_path):
    require(Path.cwd().resolve() == ROOT.resolve(), "wrong_root")
    require(re.fullmatch(r"target/p09-121-resource-optimized/p143-idle-preflight-r[1-9][0-9]*\.json", receipt_path), "receipt_scope")
    destination = ROOT / receipt_path
    require(destination.parent.is_dir() and not destination.parent.is_symlink()
        and not destination.parent.is_junction() and not destination.exists(), "fresh_local_receipt_required")
    freeze = [pin(path) for path in SOURCES]
    resources = Resources()
    start = time.monotonic()
    count = 0
    while time.monotonic() - start < MAX_SECONDS:
        time.sleep(SAMPLE_SECONDS)
        count = stable_count(count, resources.sample())
        if count >= REQUIRED or resources.stop.is_set():
            break
    exact = [pin(path) for path in SOURCES] == freeze
    admitted = count >= REQUIRED and exact and not resources.stop.is_set()
    result = {
        "schema_version": "hwpx-agent.p09-idle-resource-admission/v1",
        "state": "ADMITTED_IDLE_WINDOW_ONLY_NOT_BUILD_OR_PRODUCT" if admitted else "DEFERRED_RESOURCE_PRESSURE_NO_HEAVY_WORK_STARTED",
        "source_freeze": freeze, "source_freeze_exact_after": exact,
        "samples": resources.samples, "resource_stop_reason": resources.reason,
        "consecutive_stable_samples": count,
        "policy": {"system_cpu_max_percent": CPU_MAX, "available_ram_min_mib": RAM_MIN_MIB,
            "required_consecutive_samples": REQUIRED, "sample_seconds": SAMPLE_SECONDS, "maximum_seconds": MAX_SECONDS},
        "logical_cpu_limit": 1, "priority": "BelowNormal",
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "build_test_DB_or_native_started": False, "P09_gate": "OPEN", "product_complete": False,
    }
    with destination.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"state": result["state"], "samples": len(result["samples"]),
        "receipt": receipt_path, "elapsed_seconds": result["elapsed_seconds"]}))
    return 0 if admitted else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    try:
        raise SystemExit(main(args.receipt))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[a-zA-Z0-9_]+", str(error)) else "redacted"
        print(json.dumps({"state": "FAIL_CLOSED_NO_HEAVY_WORK_STARTED", "error_code": code}))
        raise SystemExit(1) from None
