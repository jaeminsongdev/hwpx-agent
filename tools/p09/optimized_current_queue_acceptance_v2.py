"""Reusable acceptance scratch and persistent bounded terminal diagnostics.

기존 v1/original oracle, guard, rate, 두 읽기 및 final hash는 보존한다.
이미 검증된 64KiB workspace만 private reader MRO에 연결한다. 내용 캐시는
아니며 원 Native 증거를 소급 변경하지 않는다. 종료 후 작은 진단을 직접
exclusive 파일로 저장해 관찰 세션/재부팅으로 stdout이 유실되어도 보존한다.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import optimized_current_queue_acceptance_v1 as prior
import reusable_audit_chunk_v1 as chunk

SELF = "tools/p09/optimized_current_queue_acceptance_v2.py"
TEST = "tools/p09/tests/test_optimized_current_queue_acceptance_v2.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case143-optimized-acceptance-persistent-code-r418g.v1.json"
QUAL_STATE = "PASS_ACCEPTANCE_REUSABLE_SCRATCH_AND_PERSISTENT_DIAGNOSTIC_CODE_NOT_ACCEPTANCE"
MAX_DIAGNOSTIC_BYTES = 256 * 1024


def require(ok, code):
    if not ok:
        raise ValueError("PERSISTENT_ACCEPTANCE_" + code)


def reader_runtime(m, leaf):
    Reader, proof = chunk.reader_type(m.a.AcceptanceReader, leaf)
    return NS(**{**vars(m), "a": NS(**{**vars(m.a), "AcceptanceReader": Reader})}), proof


def qualify(q, m, pin):
    require(pin.get("path") == QUAL_PATH, "EXACT_QUALIFICATION_PATH")
    m.base.scope.pins([pin], 1)
    row = m.a.read_exact(q, pin)
    m.a.fields(row, dict(state=QUAL_STATE, accepted_count_delta=0,
                         product_or_Native_or_acceptance_executed=False,
                         cleanup_confirmed=True), "QUALIFIED_CODE_NOT_PRODUCT")
    tests = row["contracts"]
    m.a.exact(tests, dict(run=33, errors=0, failures=0, skipped=0),
              "ALL_NEW_AND_ORIGINAL_CHUNK33_CONTRACTS")
    pins = m.base.scope.pins(row["new_code_pins"], 2)
    require(set(pins) == {SELF, TEST}, "BOTH_NEW_CODE_PINS")
    for name in (SELF, TEST):
        m.a.exact(q.pin(name), pins[name], "CURRENT_QUALIFIED_PERSISTENT_CODE")
    for p in row["original_chunk_code_pins"]:
        m.a.exact(q.pin(p["path"]), p, "ORIGINAL_CHUNK_CODE_UNCHANGED")
    return row


def projection(m, raw, root_pin, old_pin, new_pin, leaf):
    private, proof = reader_runtime(m, leaf)
    execute, state = prior.projection(private, raw, root_pin, old_pin, leaf)
    original_prepare = execute.__globals__["prepare"]
    def prepare(q):
        result = original_prepare(q)
        qualify(q, m, new_pin)
        return result
    # Copy globals, not code; never mutate a published/default runner.
    execute = FunctionType(execute.__code__, {**execute.__globals__, "prepare": prepare},
                           argdefs=execute.__defaults__, closure=execute.__closure__)
    state.reusable_chunk_projection = proof
    return execute, state


def diagnostic_destination(root, index, name):
    require(type(index) is int and 134 <= index <= 249, "CURRENT_CASE_RANGE")
    require(type(name) is str and re.fullmatch(
        rf"implementation/p09/evidence/p09-361-case{index}-optimized-acceptance-attempt[0-9]{{3}}\.v2\.json", name),
        "EXACT_BOUNDED_DIAGNOSTIC_PATH")
    root = Path(root).absolute()
    path = root / name
    require(path.parent.is_dir(), "DIAGNOSTIC_PARENT_EXISTS")
    for parent in (path.parent, *path.parent.parents):
        require(not parent.is_symlink() and not parent.is_junction(), "DIAGNOSTIC_ANCESTOR_LINK")
        if parent == root:
            break
    require(not path.exists() and not path.is_symlink() and not path.is_junction(),
            "REFUSE_DIAGNOSTIC_OVERWRITE")
    return path


def publish(path, name, row):
    require(type(row) is dict, "CLOSED_DIAGNOSTIC_OBJECT")
    raw = (json.dumps(row, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")
    require(0 < len(raw) <= MAX_DIAGNOSTIC_BYTES, "DIAGNOSTIC_SIZE_BOUND")
    # Exclusive creation prevents races from overwriting an earlier attempt.
    # A power-loss partial stays partial and is never silently promoted to PASS.
    with path.open("xb") as stream:
        written = stream.write(raw)
        require(written == len(raw), "COMPLETE_DIAGNOSTIC_WRITE")
        stream.flush()
        os.fsync(stream.fileno())
    return dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def run(m, root_pin, old_pin, new_pin, diagnostic_name):
    destination = diagnostic_destination(m.c.ROOT, m.base.CONFIG.index, diagnostic_name)
    states = []
    def projected(runtime, raw, rp, qp, leaf):
        execute, state = projection(runtime, raw, rp, qp, new_pin, leaf)
        states.append(state)
        return execute, state
    runner = FunctionType(prior.run.__code__, {**prior.run.__globals__, "projection": projected},
                          argdefs=prior.run.__defaults__, closure=prior.run.__closure__)
    try:
        row = runner(m, root_pin, old_pin)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        # Even a diagnostic-only failure must not lose the closed error code.
        # If the canonical receipt already exists, never report delta0 or retry.
        canonical = m.c.ROOT / f"implementation/p09/evidence/p09-361-case{m.base.CONFIG.index}-current-epoch-accept001.v1.json"
        published = canonical.exists()
        row = dict(state="FAILED_PERSISTENT_ACCEPTANCE_UNRESOLVED_NOT_RETRIED",
                   error_code=prior.diagnostics.closed_error(error),
                   accepted_count_delta=None if published else 0,
                   canonical_receipt_exists_requires_inspection_not_retry=published,
                   cleanup_confirmed=states[0].guards[0].cleanup if states and states[0].guards else None,
                   Native_frame_reexecuted=False, product_child_executed=False)
    row["persistent_code_qualification_pin"] = new_pin
    row["validation_code_and_original_guards_unchanged"] = True
    row["diagnostic_is_not_additional_product_or_Native_evidence"] = True
    if states:
        row["reusable_chunk_projection"] = states[0].reusable_chunk_projection
        row["reusable_acceptance_workspaces"] = [chunk.summary(reader)
            for reader in states[0].readers if hasattr(reader, chunk.ATTRIBUTE)]
    pin = publish(destination, diagnostic_name, row)
    return row, pin


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--root-bytes", type=int, required=True)
    parser.add_argument("--root-sha256", required=True)
    parser.add_argument("--qualification-bytes", type=int, required=True)
    parser.add_argument("--qualification-sha256", required=True)
    parser.add_argument("--persistent-qualification-bytes", type=int, required=True)
    parser.add_argument("--persistent-qualification-sha256", required=True)
    parser.add_argument("--diagnostic", required=True)
    args = parser.parse_args()
    import flat_current_queue_direct_view_runtime_v4 as m
    m.data_path(args.case)
    m.base.configure(args.case)
    root = dict(path=m.source.root_path(m.base.CONFIG), bytes=args.root_bytes, sha256=args.root_sha256)
    old = dict(path=prior.QUAL_PATH, bytes=args.qualification_bytes, sha256=args.qualification_sha256)
    new = dict(path=QUAL_PATH, bytes=args.persistent_qualification_bytes, sha256=args.persistent_qualification_sha256)
    row, pin = run(m, root, old, new, args.diagnostic)
    print(json.dumps(dict(state=row["state"], error_code=row.get("error_code"), diagnostic_pin=pin,
                          accepted_count_delta=row.get("accepted_count_delta"), cleanup_confirmed=row.get("cleanup_confirmed"))))
    raise SystemExit(0 if row["state"].startswith("PASS_") and row.get("cleanup_confirmed") is True else 2)
