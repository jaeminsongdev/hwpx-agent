#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tools.p06.table_conformance import (
        build_automation_projection,
        canonical_json,
        load_json_file,
        write_new,
    )
except ModuleNotFoundError:
    from table_conformance import (  # type: ignore[no-redef]
        build_automation_projection,
        canonical_json,
        load_json_file,
        write_new,
    )


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a redacted, exact-target projection of the P06 automation registry."
    )
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry, registry_digest = load_json_file(ROOT, args.registry)
    projection = build_automation_projection(registry, registry_digest)
    write_new(args.output.resolve(), canonical_json(projection))
    print(
        "P06_TABLE_AUTOMATION_PROJECTION_CREATED "
        f"rows={projection['row_count']} output={args.output.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
