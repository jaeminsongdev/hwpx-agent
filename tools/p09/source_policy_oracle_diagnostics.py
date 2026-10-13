"""Owned P84 failure diagnostics: fixed BOOL/NULL keys, no raw logs or stored IDs."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 128 * 1024
CHECKS = tuple(["head_revision","head_generation","head_generation_nonnegative","source_metadata","source_available","source_verified","source_kind","source_digest","source_acl","receipt_metadata","receipt_available","receipt_verified","receipt_kind","receipt_digest","receipt_acl","revision_source","revision_plan","revision_verified","revision_subject","result_metadata","result_available","result_verified","result_kind","result_digest","result_acl","seal_kind","seal_generation","seal_receipt","seal_commit_id","seal_request","commit_branch","commit_previous","commit_expected_generation","commit_generation","commit_receipt","commit_subject","record_job_binding","record_in_progress","job_validating","lease_current_at_observation"])
SQL_PATH = "crates/product-cli/examples/stored_source_policy_postgres_probe/worker/oracle_snapshot.sql"
SQL_SHA256 = "d419410277addf88cfc2da51e15c08350db60ece823e8092e039c3ba5365b8b2"

@dataclass(frozen=True, repr=False)
class OwnedContext:
    case: int
    receipt: str
    def __repr__(self):
        return "OwnedOracleContext(<redacted>)"

def bounded(text):
    if not isinstance(text, str):
        return False
    try:
        return len(text.encode("utf-8")) <= MAX_BYTES
    except UnicodeEncodeError:
        return False

def parse_context(stderr):
    if not bounded(stderr):
        return None
    lines = [line for line in stderr.splitlines() if line.startswith("P84_ORACLE_CONTEXT ")]
    if len(lines) != 1:
        return None
    match = re.fullmatch(r"P84_ORACLE_CONTEXT case=([0-9]) receipt=([0-9a-f]{32})", lines[0])
    if match is None or match[2] == "0" * 32:
        return None
    return OwnedContext(int(match[1]), match[2])

def query(root, context):
    if (not isinstance(context, OwnedContext) or type(context.case) is not int or not 0 <= context.case < 10
            or not isinstance(context.receipt, str) or not re.fullmatch(r"[0-9a-f]{32}", context.receipt) or context.receipt == "0" * 32):
        raise ValueError("owned_oracle_context_rejected")
    path = root / SQL_PATH
    if not path.is_file() or path.is_symlink() or path.is_junction() or path.stat().st_size > 8192:
        raise ValueError("owned_oracle_query_source_rejected")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SQL_SHA256:
        raise ValueError("owned_oracle_query_source_drift")
    text = raw.decode("utf-8").rstrip()
    if text.endswith(";"):
        text = text[:-1]
    values = {1: f"'{1:032x}'::uuid", 2: f"'{2:032x}'::uuid", 3: "'" + "a" * 64 + "'",
              4: f"'{500+context.case:032x}'::uuid", 5: f"'{600+context.case:032x}'::uuid",
              6: f"'{200+context.case:032x}'::uuid", 7: f"'{context.receipt}'::uuid"}
    if set(re.findall(r"\$([1-7])\b", text)) != set("1234567"):
        raise ValueError("owned_oracle_query_parameters_drift")
    text = re.sub(r"\$([1-7])\b", lambda match: values[int(match[1])], text)
    if "$" in text:
        raise ValueError("owned_oracle_query_parameters_drift")
    return "SELECT row_to_json(observation)::text FROM (\n" + text + "\n) observation;"

def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("owned_oracle_duplicate_key")
        result[key] = value
    return result

def decode_snapshot(stdout):
    if not bounded(stdout):
        raise ValueError("owned_oracle_snapshot_budget")
    data = json.loads(stdout, object_pairs_hook=strict_object)
    if not isinstance(data, dict) or set(data) != set(CHECKS):
        raise ValueError("owned_oracle_snapshot_shape")
    if any(value is not None and type(value) is not bool for value in data.values()):
        raise ValueError("owned_oracle_snapshot_value")
    return {"schema": "hwpx-agent.p84-owned-oracle-observation/v1",
            "state": "observed_after_failure_NOT_original_atomic_oracle_or_cause",
            "checks": {key: data[key] for key in CHECKS},
            "original_atomic_oracle_verified": False, "root_cause_proven": False}

def capture(root, stderr, check_owner, execute_readonly):
    """Best-effort diagnostics never replace the caller's already recorded primary failure."""
    context = parse_context(stderr)
    if context is None:
        return {"state": "unavailable_context_NOT_cause", "root_cause_proven": False}
    try:
        check_owner()  # No query until the original owner/loopback/no-mount checks succeed.
        result = execute_readonly(query(root, context))
        if result.returncode != 0:
            return {"state": "unavailable_query_NOT_cause", "root_cause_proven": False}
        return decode_snapshot(result.stdout)
    except Exception:
        # No exception class/message, SQL text, UUID, token or path escapes this diagnostic boundary.
        return {"state": "unavailable_diagnostic_NOT_cause", "root_cause_proven": False}

def literal_reason_codes(texts):
    result = set()
    for text in texts:
        result.update(code for code in re.findall(r"(?:MESSAGE\s*=\s*|RAISE\s+EXCEPTION\s*)'([A-Z][A-Z_0-9]{2,96})'", text)
                      if code.startswith(("FORM_POLICY_", "TEST_POLICY_", "IDEMPOTENCY_", "TEST_AUTHORIZED_IR_")))
    return result

def closed_literal_reasons(stderr, allowed):
    if not bounded(stderr):
        return []
    # Only known literal codes from the pinned local SQL sources survive. No dynamic suffixes.
    tokens = set(re.findall(r"(?<![A-Z0-9_])(?:FORM_POLICY|TEST_POLICY|IDEMPOTENCY|TEST_AUTHORIZED_IR)_[A-Z0-9_]{1,96}(?![A-Z0-9_])", stderr))
    return sorted(tokens & set(allowed))
