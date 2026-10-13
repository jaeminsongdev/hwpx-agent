"""Current-r4 published original targets only; readonly six-reference absence."""
import re

import conservative_maintenance as c
import current_authority_sql_receipts as receipts
import bounded_container_absence as bounded
from sql_container_ownership import CASES, uuid_value
from sql_runtime_supervision import LOCAL_DOCKER_HOST
from run_formula_issuer_registry_sql_checks import IMAGE

AUDIT_PIN = {"path": "implementation/p09/evidence/p09-149-current-authority-owned.actual-run01.v1.json",
    "bytes": 74539, "sha256": "70f3441a7d8805bba76ca47e9b9ca70e5bbb8e2718c3ecb8723b565f18ece36b"}
ERROR = "CURRENT_ABSENCE_NOT_ALL_SIX_REFERENCES_PROVED"


def reference_inventory(proof, runs):
    c.require(isinstance(proof, dict) and proof["source_freeze_exact_after"] is True
        and proof["resource_watcher_cleanup_confirmed"] is True and proof["resource_stop_reason"] is None
        and proof["product_complete"] is False and proof["P09_gate"] == "OPEN",
        "CURRENT_ABSENCE_AUDIT_SCOPE")
    slots = proof["original_audit_summary"]["validated_current_cases"]
    c.require(len(slots) == 3 and {(row["case"], row["input_mode"]) for row in slots} == set(receipts.CURRENT_RUNS)
        and isinstance(runs, dict) and set(runs) == {"approval", "trust", "policy"}, "CURRENT_ABSENCE_CASE_INVENTORY")
    published = {row["case"]: row["receipt_pin"] for row in slots}
    descriptors, references = [], []
    for case in ("approval", "trust", "policy"):
        run = runs[case]
        uuid_value(run["run_id"])
        identifier, name = run["container_id"], run["container_name"]
        c.require(run["live_case"] == case and run["input_mode"] == "original"
            and type(run["source_index"]) is int and run["source_index"] == 0
            and run["expected_formula_outcome"] == "unchanged" and run["container_removed"] is True,
            "CURRENT_ABSENCE_RECEIPT_SELECTION")
        c.require(isinstance(identifier, str) and re.fullmatch(r"[0-9a-f]{64}", identifier)
            and name == CASES[case][0]+run["run_id"], "CURRENT_ABSENCE_IDENTITY")
        c.require(run["image"] == IMAGE and run["image_id"] == IMAGE.split("@", 1)[1], "CURRENT_ABSENCE_IMAGE_IDENTITY")
        c.require(published[case]["path"] == receipts.CURRENT_RUNS[(case, "original")], "CURRENT_ABSENCE_RECEIPT_PATH")
        descriptors.append({"case": case, "receipt_pin": published[case], "run_id": run["run_id"],
            "container_name": name, "container_id": identifier})
        references.extend((identifier, name))
    bounded.references_checked(references)
    c.require(len(references) == 6, "CURRENT_ABSENCE_REFERENCE_INVENTORY")
    return descriptors, references


def bind_inputs(reader):
    c.require(reader.pin(AUDIT_PIN["path"]) == AUDIT_PIN, "CURRENT_ABSENCE_AUDIT_BYTE_DRIFT")
    proof = reader.json(AUDIT_PIN["path"])
    contract = receipts.build_contract
    c.require(reader.pin(contract.CURRENT_BUILD_PIN["path"]) == contract.CURRENT_BUILD_PIN,
        "CURRENT_ABSENCE_BUILD_BYTE_DRIFT")
    build, manifest = reader.json(contract.CURRENT_BUILD_PIN["path"]), reader.json(receipts.MANIFEST)
    expected = {row["case"]: row["receipt_pin"] for row in proof["original_audit_summary"]["validated_current_cases"]}
    runs = {}
    for (case, mode), name in receipts.CURRENT_RUNS.items():
        c.require(mode == "original" and reader.pin(name) == expected[case], "CURRENT_ABSENCE_RECEIPT_BYTE_DRIFT")
        run = reader.json(name)
        receipts.validate_current_case(run, build, manifest, case, mode, "unchanged")
        runs[case] = run
    return reference_inventory(proof, runs)


def query_arguments(docker, references):
    c.require(len(references) == 6, "CURRENT_ABSENCE_REFERENCE_INVENTORY")
    raw = bounded.inspect_arguments(docker, references)
    return [raw[0], "--host", LOCAL_DOCKER_HOST, *raw[1:]]


def validate_response(result, references):
    # Docker TemplateInspector.Flush writes exactly one LF when its object buffer
    # is empty (cli/command/inspect/inspector.go). Transport framing is not object
    # output: only this exact form with inspect's error exit 1 is decoded. Never
    # strip arbitrary whitespace or alter stderr/the shared strict validator.
    stdout = result.stdout
    if stdout == "\n":
        c.require(type(result.returncode) is int and result.returncode == 1, ERROR)
        stdout = ""
    return bounded.validate_absence(result.returncode, stdout, result.stderr, references, ERROR)


def response_diagnostics(result, references):
    """Known references and bounded numeric categories only; never raw daemon text."""
    bounded.references_checked(references)
    c.require(isinstance(result.stdout, str) and isinstance(result.stderr, str)
        and len(result.stdout.encode("utf-8")) <= 16384 and len(result.stderr.encode("utf-8")) <= 16384,
        "CURRENT_ABSENCE_DIAGNOSTIC_BUDGET")
    missing, other, daemon, blank = [], 0, 0, 0
    for line in result.stderr.splitlines():
        match = re.fullmatch(r"Error: No such (?:object|container): (.+)", line, re.I)
        if match is not None and match[1] in references:
            missing.append(match[1])
        else:
            other += 1
        daemon += bool(re.match(r"Error response from daemon:", line, re.I))
        blank += not bool(line)
    return {"stdout_bytes": len(result.stdout.encode("utf-8")), "stdout_line_count": len(result.stdout.splitlines()),
        "stdout_exact_empty_template_flush": result.stdout == "\n",
        "stdout_only_whitespace": bool(result.stdout) and not bool(result.stdout.strip()),
        "stdout_known_ID_line_count": sum(line in references for line in result.stdout.splitlines()),
        "stderr_bytes": len(result.stderr.encode("utf-8")), "stderr_line_count": len(result.stderr.splitlines()),
        "known_missing_references": missing, "stderr_other_line_count": other,
        "stderr_daemon_error_line_count": daemon, "stderr_blank_line_count": blank}
