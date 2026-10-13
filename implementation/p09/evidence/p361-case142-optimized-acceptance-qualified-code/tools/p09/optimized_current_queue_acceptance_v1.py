"""Opt-in metadata-only acceptance; unchanged full frozen Native/product oracle.

기존 immutable acceptor AST와 모든 읽기/최종 hash/큐 조건을 보존한다.
검증된 source predicate factory와 더 강한 metadata fail-fast만 연결한다.
새 코드는 Native142 증거인 척하지 않고 별도 수용경계에서 fresh bind한다.
중단 시 같은 original sampler의 진단만 남기며 자동 retry는 하지 않는다.
"""
import argparse
import json
import sys
import threading
from types import SimpleNamespace as NS

import read_only_acceptance_pressure_probe_v1 as diagnostics

SELF = "tools/p09/optimized_current_queue_acceptance_v1.py"
TEST = "tools/p09/tests/test_optimized_current_queue_acceptance_v1.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case142-optimized-acceptance-code-r410.v1.json"
QUAL_STATE = "PASS_OPTIMIZED_ACCEPTANCE_CODE46_AND_ACTUAL142_READ_ONLY_PREPARE_NOT_ACCEPTANCE"
CODE_PATHS = (diagnostics.SELF, diagnostics.TEST, SELF, TEST)


def require(ok, code):
    if not ok:
        raise ValueError("OPTIMIZED_ACCEPTANCE_" + code)


def factories(m, leaf):
    """Private wrappers only; default modules/classes/globals remain unchanged."""
    Snapshot, proof = m.source.snapshot.reader_type(m.a.AcceptanceReader, leaf)
    guards, readers, bindings = [], [], []

    class CaptureGuard(m.a.Guard):
        def __init__(self):
            require(not guards, "ONE_ORIGINAL_SAMPLER")
            super().__init__()
            guards.append(self)

        def close(self):
            # Restore without pressure checks even when the original guard stops.
            for binding in bindings:
                binding.restore()
            super().close()

    class Reader(Snapshot):
        def __init__(self, root, checkpoint):
            require(not readers and len(guards) == 1, "ONE_READER_AND_OWNER")
            require(getattr(checkpoint, "__self__", None) is guards[0], "SAME_ORIGINAL_OWNER")
            super().__init__(root, checkpoint)
            readers.append(self)
            owner = NS(lock=threading.Lock(), samples=guards[0].samples,
                       checkpoint_io=checkpoint)
            bindings.append(m.source.prior.prior.metadata.MetadataCheckpoint(self, owner))

    return CaptureGuard, Reader, NS(guards=guards, readers=readers,
                                   bindings=bindings, source_projection=proof)


def qualify(q, m, pin):
    require(pin.get("path") == QUAL_PATH, "EXACT_QUALIFICATION_PATH")
    m.base.scope.pins([pin], 1)
    row = m.a.read_exact(q, pin)
    m.a.fields(row, dict(state=QUAL_STATE,
                         contracts=dict(run=46, errors=0, failures=0, skipped=0),
                         accepted_count_delta=0, cleanup_confirmed=True,
                         product_or_Native_or_acceptance_executed=False), "CODE46_NOT_PRODUCT")
    pins = m.base.scope.pins(row["new_code_pins"], 4)
    require(set(pins) == set(CODE_PATHS), "ALL_FOUR_CURRENT_CODE_PINS")
    for name in CODE_PATHS:
        m.a.exact(q.pin(name), pins[name], "CURRENT_TESTED_ACCEPTANCE_CODE")
    proof_pin = row["actual_read_only_prepare_pin"]
    m.base.scope.pins([proof_pin], 1)
    proof = m.a.read_exact(q, proof_pin)
    m.a.fields(proof, dict(state="PASS_FULL_PREPARE_SINGLE_SOURCE_STAT_NOT_QUEUE_ACCEPTANCE",
                           index=142, accepted_count_delta=0,
                           Native_frame_reexecuted=False, product_child_executed=False,
                           queue_acceptance_called=False, cleanup_confirmed=True), "ACTUAL_READ_ONLY_PREPARE")
    m.a.fields(proof["single_snapshot_source"], dict(
        source_requests=200, fresh_no_follow_stat_attempts=200,
        ordinary_windows_snapshot_decisions=200, exact_original_fallback_requests=0,
        ordinary_nonfile_rejections=0, original_logical_source_predicates_retained=True,
        stat_result_cached_or_reused_between_source_requests=False,
        original_default_reader_mutated=False, held_Native_path_guard_replaced=False), "REAL_SOURCE200")
    return row


def projection(m, raw, root_pin, qualification_pin, leaf):
    require(root_pin.get("path") == m.source.root_path(m.base.CONFIG), "EXACT_CURRENT_ROOT")
    m.base.scope.pins([root_pin], 1)
    # This is precisely the frozen v4 inherited accept dependency path. All
    # queue literals, waits, statements, and the full prepare oracle remain.
    source = m.API.accept.__globals__["source"]
    files = m.API.accept.__globals__["FILES"]
    controllers = tuple(dict.fromkeys(source.CONTROLLERS + files))
    flat = source.prior.accepted.original
    execute, original_proof = flat.run_projection(raw, root_pin)
    Guard, Reader, state = factories(m, leaf)
    def prepare(q):
        result = m.API.prepare(q, root_pin)
        # Original whole Native scope is checked first. These additional files
        # are acceptance witnesses, not retroactively inserted Native inputs.
        qualify(q, m, qualification_pin)
        return result
    original_code = execute.__code__
    execute.__globals__.update(
        SELF=m.SELF, TEST=m.TEST, runtime=m.API.context(m.base.CONFIG),
        CONTROLLERS=tuple(dict.fromkeys(execute.__globals__["CONTROLLERS"] + controllers)),
        prepare=prepare,
        original=NS(**{**vars(m.a), "Guard": Guard, "AcceptanceReader": Reader}))
    require(execute.__code__ is original_code, "ALL_ORIGINAL_ACCEPTOR_BYTECODE_RETAINED")
    state.original_projection = original_proof
    return execute, state


def run(m, root_pin, qualification_pin):
    state = None
    out = dict(state="FAILED_OPTIMIZED_ACCEPTANCE_NOT_ACCEPTED",
               index=m.base.CONFIG.index, accepted_count_before=m.base.CONFIG.before,
               runtime_pin=root_pin, qualification_pin=qualification_pin,
               Native_frame_reexecuted=False, product_child_executed=False,
               automatic_retry_or_resume=False, PC_freeze_resolved=False)
    try:
        pin = m.source.prior.accepted.original.candidate.ACCEPTOR_PIN
        m.base.stable.stable.prior.build.direct_path(m.c.ROOT / pin["path"], file_required=True)
        with (m.c.ROOT / pin["path"]).open("rb") as stream:
            raw = stream.read(pin["bytes"] + 1)
        execute, state = projection(m, raw, root_pin, qualification_pin,
                                    m.source.prior.leaf_bytes())
        status = execute()
        require(status == 0, "ORIGINAL_TERMINAL_SUCCESS")
        out.update(state="PASS_ORIGINAL_IMMUTABLE_ACCEPTANCE_WITH_QUALIFIED_METADATA_READER",
                   accepted_count_after=m.base.CONFIG.before + 1, accepted_count_delta=1,
                   original_acceptor_projection=state.original_projection,
                   source_predicate_projection=state.source_projection)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        out["error_code"] = diagnostics.closed_error(error)
        out["accepted_count_delta"] = 0
    finally:
        if state is not None and state.guards:
            guard = state.guards[0]
            out["cleanup_confirmed"] = guard.cleanup
            out["resource_diagnostics"] = diagnostics.resource_diagnostics(guard, m.c.decision)
            out["metadata_failfast"] = [b.summary() for b in state.bindings]
            out["single_snapshot_source"] = [r.source_snapshot_diagnostics() for r in state.readers]
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--root-bytes", type=int, required=True)
    parser.add_argument("--root-sha256", required=True)
    parser.add_argument("--qualification-bytes", type=int, required=True)
    parser.add_argument("--qualification-sha256", required=True)
    args = parser.parse_args()
    import flat_current_queue_direct_view_runtime_v4 as m
    m.data_path(args.case)
    m.base.configure(args.case)
    root = dict(path=m.source.root_path(m.base.CONFIG), bytes=args.root_bytes,
                sha256=args.root_sha256)
    qualification = dict(path=QUAL_PATH, bytes=args.qualification_bytes,
                         sha256=args.qualification_sha256)
    result = run(m, root, qualification)
    print(json.dumps(result))
    raise SystemExit(0 if result["state"].startswith("PASS_")
                     and result.get("cleanup_confirmed") is True else 2)
