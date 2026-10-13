"""Exclusive bounded container intent before original owned Docker launcher GO.

암호/전체 명령행/env/원문 로그는 기록하지 않는다. flush/fsync 뒤 readback까지
성공해야 원래 factory를 호출한다. 전원 장애 복구나 실제 Docker 증명은 별도다.
"""
import hashlib
import json
import os
from pathlib import Path
import re

import conservative_maintenance as c
from run_formula_issuer_registry_sql_checks import IMAGE

MAX_JOURNAL_BYTES = 4096
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
SCHEMA = "hwpx-agent.p09-owned-SQL-container-intent/v1"
CASES = {"approval": ("hwpx-p146-", "hwpx-agent.p09-146-owned-corpus-signature-product-test"),
    "trust": ("hwpx-p148-", "hwpx-agent.p09-148-owned-authority-product-test"),
    "policy": ("hwpx-p148-", "hwpx-agent.p09-148-owned-authority-product-test")}
FIELDS = {"schema_version", "parent_nonce", "case", "run_id", "container_name", "label_key", "image_pin", "image_id"}


def uuid_value(value):
    c.require(isinstance(value, str) and re.fullmatch(UUID, value), "SQL_OWNED_INTENT_UUID_SCOPE")
    return value


def make_intent(nonce, case, run_id):
    uuid_value(nonce)
    uuid_value(run_id)
    c.require(case in CASES, "SQL_OWNED_INTENT_CASE_SCOPE")
    prefix, label = CASES[case]
    return {"schema_version": SCHEMA, "parent_nonce": nonce, "case": case, "run_id": run_id,
        "container_name": prefix+run_id, "label_key": label, "image_pin": IMAGE, "image_id": IMAGE.split("@", 1)[1]}


def validate_intent(row, nonce, case):
    c.require(isinstance(row, dict) and set(row) == FIELDS, "SQL_OWNED_INTENT_FIELD_SCOPE")
    c.require(row == make_intent(nonce, case, row["run_id"]), "SQL_OWNED_INTENT_BINDING_MISMATCH")
    return dict(row)


def journal_path(nonce):
    uuid_value(nonce)
    path = c.ROOT/f"implementation/p09/evidence/p09-149-SQL-owned-intent-{nonce}.v1.json"
    for ancestor in (path, *path.parents):
        c.require(not ancestor.is_symlink() and not ancestor.is_junction(), "SQL_OWNED_INTENT_PATH_LINK")
        if ancestor == c.ROOT:
            break
    c.require(path.parent.is_dir() and path.resolve().is_relative_to(c.ROOT.resolve()), "SQL_OWNED_INTENT_PATH_SCOPE")
    return path


def unique_object(pairs):
    row = {}
    for key, value in pairs:
        c.require(key not in row, "SQL_OWNED_INTENT_DUPLICATE_JSON_KEY")
        row[key] = value
    return row


def load_intent(nonce, case):
    path = journal_path(nonce)
    c.require(path.is_file(), "SQL_OWNED_INTENT_MISSING")
    with path.open("rb") as stream:
        raw = stream.read(MAX_JOURNAL_BYTES+1)
    c.require(len(raw) <= MAX_JOURNAL_BYTES, "SQL_OWNED_INTENT_READ_BUDGET")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("SQL_OWNED_INTENT_JSON_INVALID") from None
    row = validate_intent(value, nonce, case)
    return {"intent": row, "journal_pin": {"path": path.relative_to(c.ROOT).as_posix(),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}}


def write_intent(row):
    row = validate_intent(row, row["parent_nonce"], row["case"])
    path = journal_path(row["parent_nonce"])
    c.require(not path.exists(), "SQL_OWNED_INTENT_EXCLUSIVE_REQUIRED")
    raw = (json.dumps(row, sort_keys=True, separators=(",", ":"))+"\n").encode("utf-8")
    c.require(len(raw) <= MAX_JOURNAL_BYTES, "SQL_OWNED_INTENT_WRITE_BUDGET")
    with path.open("xb") as stream:
        c.require(stream.write(raw) == len(raw), "SQL_OWNED_INTENT_SHORT_WRITE")
        stream.flush()
        os.fsync(stream.fileno())
    checked = load_intent(row["parent_nonce"], row["case"])
    c.require(checked["intent"] == row and checked["journal_pin"]["bytes"] == len(raw)
        and checked["journal_pin"]["sha256"] == hashlib.sha256(raw).hexdigest(), "SQL_OWNED_INTENT_READBACK_MISMATCH")
    checked["journal_fsync_before_delegate_completed"] = True
    return checked


def run_arguments(docker, row):
    return [docker, "run", "--detach", "--pull", "never", "--name", row["container_name"],
        "--label", row["label_key"]+"="+row["run_id"], "--network", "bridge", "--publish", "127.0.0.1::5432",
        "--read-only", "--memory", "512m", "--memory-swap", "512m", "--cpus", "1", "--pids-limit", "64",
        "--tmpfs", "/var/lib/postgresql:rw,noexec,nosuid,size=512m", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "--tmpfs", "/var/run/postgresql:rw,noexec,nosuid,size=16m", "--env", "POSTGRES_PASSWORD", IMAGE]


def intent_from_run(nonce, case, args, docker):
    c.require(isinstance(args, (list, tuple)) and len(args) == 31 and all(isinstance(arg, str) for arg in args),
        "SQL_OWNED_INTENT_RUN_ARGUMENT_SCOPE")
    c.require(case in CASES, "SQL_OWNED_INTENT_CASE_SCOPE")
    prefix, _ = CASES[case]
    c.require(args[6].startswith(prefix), "SQL_OWNED_INTENT_CONTAINER_NAME_SCOPE")
    row = make_intent(nonce, case, args[6][len(prefix):])
    c.require(list(args) == run_arguments(docker, row), "SQL_OWNED_INTENT_RUN_ARGUMENT_DRIFT")
    return row


def journalled_factory_type(original, nonce, case, *, writer=None):
    uuid_value(nonce)
    c.require(case in CASES, "SQL_OWNED_INTENT_CASE_SCOPE")
    class JournalledFactory(original):
        def __call__(self, args, **kwargs):
            if isinstance(args, (list, tuple)) and len(args) >= 2 and args[0] == self.docker and args[1] == "run":
                row = intent_from_run(nonce, case, args, self.docker)
                checked = (write_intent if writer is None else writer)(row)
                c.require(checked.get("journal_fsync_before_delegate_completed") is True
                    and checked.get("intent") == row, "SQL_OWNED_INTENT_BEFORE_GO_NOT_CONFIRMED")
            return super().__call__(args, **kwargs)
    return JournalledFactory
