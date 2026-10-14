"""Case160 facade for the unchanged qualified full acceptance engine.

No product replay; independent proof is mandatory. New facade witnesses are
read only after the whole Native scope check, never retroactive Native inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS

SELF = "tools/p09/accept_case160_current.py"
TEST = "tools/p09/tests/test_accept_case160_current.py"
ROOT = dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run011.v1.json",
    bytes=4399893, sha256="e2e6a45f4b7dec9751591f65e7956ff855c79abf4eda958321a1877a494bf34d")
ORACLE = "implementation/p09/evidence/p09-361-case160-native011-independent-oracle-r392-attempt001.v1.json"


def diagnostic_path(attempt):
    if type(attempt) is not int or not 1 <= attempt <= 8:
        raise ValueError("CLOSED_CASE160_ACCEPTANCE_ATTEMPT")
    return f"implementation/p09/evidence/p09-361-case160-optimized-acceptance-attempt{attempt:03}.v2.json"


def facade(m):
    m.require(m.base.CONFIG is not None and m.base.CONFIG.index == 160 and m.base.CONFIG.before == 153,
        "EXACT_CURRENT160_ACCEPTANCE_FACADE")
    source = m.old.API.accept.__globals__["source"]
    private = NS(**{**vars(source), "root_path":m.RETRY.root_path})
    return NS(**{**vars(m), "source":private})


def validated_prepare(q, root_pin, connection, m):
    # Derive/check the whole Native scope FIRST. Witness files must not seed it.
    result = connection.API.prepare(q, root_pin)
    proof = q.json(ORACLE)
    m.a.fields(proof, dict(state="PASS_RUN004_INDEPENDENT_CURRENT160_WHOLE_ORACLE_NOT_QUEUE_OR_GATE",
        native_attempt=11, runtime_pin=ROOT, accepted_count_delta=0, product_or_Native_reexecuted=False,
        queue_acceptance_called=False, cleanup_confirmed=True,
        two_actual_runtime_byte_boundaries_independently_checked=True), "QUALIFIED_CURRENT160_WHOLE_ORACLE")
    m.require(proof["fresh_inputs"] == proof["final_fresh_hashes"] and proof["fresh_inputs"] > 0,
        "ALL_INDEPENDENT_INPUTS_CLOSED")
    for pin in proof["source_pins"]:
        m.a.exact(q.pin(pin["path"]), pin, "UNCHANGED_INDEPENDENT_ORACLE_CODE")
    q.pin(SELF); q.pin(TEST)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-attempt", type=int, choices=(11,), required=True)
    parser.add_argument("--acceptance-attempt", type=int, default=1)
    args = parser.parse_args()
    diagnostic = diagnostic_path(args.acceptance_attempt)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()  # Apply the existing one-core/B below-normal process limits.
    import case160_run007_controller as controller
    import optimized_current_queue_acceptance_v3 as acceptance
    connection = controller.CURRENT
    controller.a.require(connection is not None, "CURRENT160_CONTROLLER_READY")
    m = connection.M; m.base.configure(160); runtime = facade(m)
    m.require(not (m.c.ROOT/"implementation/p09/evidence/p09-361-case160-current-epoch-accept001.v1.json").exists(),
        "REFUSE_EXISTING_CANONICAL_ACCEPTANCE")
    m.require(not (m.c.ROOT/diagnostic).exists(), "REFUSE_EXISTING_ACCEPTANCE_DIAGNOSTIC")
    runtime.API = NS(**{**vars(m.API), "prepare":lambda q, pin:validated_prepare(q, pin, connection, m),
        "accept":m.old.API.accept})
    def pin(path):
        m.base.stable.stable.prior.build.direct_path(m.c.ROOT/path, file_required=True)
        with (m.c.ROOT/path).open("rb") as stream: raw = stream.read(262145)
        m.require(0 < len(raw) <= 262144, "BOUNDED_ACCEPTANCE_QUALIFICATION_BOOTSTRAP")
        return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    row, receipt = acceptance.run(runtime, ROOT, pin(acceptance.prior.prior.QUAL_PATH),
        pin(acceptance.prior.QUAL_PATH), pin(acceptance.QUAL_PATH), diagnostic)
    print(json.dumps(dict(state=row["state"], error_code=row.get("error_code"), diagnostic_pin=receipt,
        accepted_count_delta=row.get("accepted_count_delta"), cleanup_confirmed=row.get("cleanup_confirmed"))))
    return 0 if row["state"].startswith("PASS_") and row.get("cleanup_confirmed") is True else 1


if __name__ == "__main__": raise SystemExit(main())
