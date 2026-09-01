#!/usr/bin/env sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_root"

python3 ./tools/p01/toolchain_preflight.py
python3 ./tools/p01/run_ci.py --lane linux-core
python3 ./tools/p01/run_ci.py --lane widget
python3 ./tools/p01/run_ci.py --lane docs
python3 ./tools/p01/run_ci.py --lane security
