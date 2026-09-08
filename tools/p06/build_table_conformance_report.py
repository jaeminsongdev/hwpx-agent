#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.p06.table_conformance import canonical_json, load_and_build, write_new
except ModuleNotFoundError:
    from table_conformance import canonical_json, load_and_build, write_new  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = "specs/feature-coverage-matrix.json"
DEFAULT_CONTRACTS = "specs/capability-contracts.generated.json"
DEFAULT_PROJECTION = "implementation/p06/p06-09-current-2020-automation-projection.json"
DEFAULT_EVIDENCE = "implementation/p06/p06-09-current-2020-direct-evidence.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic fail-closed P06 61-capability conformance matrix."
    )
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--contracts", default=DEFAULT_CONTRACTS)
    parser.add_argument("--projection", default=DEFAULT_PROJECTION)
    parser.add_argument("--evidence", default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_and_build(
        ROOT,
        catalog_path=args.catalog,
        contracts_path=args.contracts,
        projection_path=args.projection,
        evidence_path=args.evidence,
    )
    write_new(args.output.resolve(), canonical_json(report))
    summary = report["summary"]
    print(
        "P06_TABLE_CONFORMANCE_REPORT_CREATED "
        f"green={summary['green_rows']}/{summary['required_rows']} "
        f"gate={summary['required_matrix']} output={args.output.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
