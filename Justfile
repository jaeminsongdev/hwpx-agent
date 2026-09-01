set shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]

bootstrap:
    ./tools/bootstrap.ps1

generate:
    cargo run --locked -p xtask -- generate

generate-check:
    cargo run --locked -p xtask -- generate --check

test-unit:
    python ./tools/p01/run_ci.py --lane linux-core

test-fixtures:
    python ./tools/p01/validate_foundation.py

validate-design:
    python ./tools/design-validation/validate_design.py

ci lane="all":
    python ./tools/p01/run_ci.py --lane {{lane}}

security:
    python ./tools/p01/run_ci.py --lane security
