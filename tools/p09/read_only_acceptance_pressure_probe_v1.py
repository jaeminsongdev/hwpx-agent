"""Read-only full preparation probe; never publishes queue acceptance.

기존 sampler/guard/deadline/byte reads를 그대로 유지한다. 이미 검증된
single-snapshot source predicate를 수용 준비 reader에도 연결하고, 중단 시
같은 sampler의 수치만 보존한다. 새 watcher, process query, retry는 없다.
Native/product/accept 함수를 호출하지 않으며 공식 완료 수는 바꾸지 않는다.
"""
import argparse
import json
import math
import re
import sys
import threading
import time
from types import SimpleNamespace as NS

SELF = "tools/p09/read_only_acceptance_pressure_probe_v1.py"
TEST = "tools/p09/tests/test_read_only_acceptance_pressure_probe_v1.py"
SAMPLE_FIELDS = ("time_utc", "system_cpu_percent", "available_ram_percent",
                 "commit_used_percent", "parent_cpu_machine_percent",
                 "parent_private_mib", "parent_private_percent")


def closed_error(error):
    value = str(error) if isinstance(error, ValueError) else "REDACTED_PROBE_FAILURE"
    return value if re.fullmatch(r"[A-Z0-9_]{1,256}", value) else "REDACTED_PROBE_FAILURE"


def resource_diagnostics(guard, decision):
    """Only already-collected samples; no OS/file/process query or invented data."""
    rows = guard.samples
    if type(rows) is not list or len(rows) > 4096:
        raise ValueError("PROBE_RESOURCE_HISTORY_BOUND")
    hot = 0
    first_stop = None
    for index, row in enumerate(rows):
        hot, reason = decision(row, hot)
        if reason is not None and first_stop is None:
            first_stop = dict(index=index, reason=reason, hot=hot)
    def extreme(key, function):
        values = [r[key] for r in rows if type(r.get(key)) in (int, float)
                  and math.isfinite(r[key])]
        return function(values) if values else None
    return dict(original_sample_count=len(rows), first_original_policy_stop=first_stop,
                CPU_max=extreme("system_cpu_percent", max),
                available_RAM_min=extreme("available_ram_percent", min),
                commit_max=extreme("commit_used_percent", max),
                parent_private_max=extreme("parent_private_percent", max),
                last_original_samples=[{k: r[k] for k in SAMPLE_FIELDS if k in r}
                                       for r in rows[-8:]],
                extra_sampler_or_process_query_started=False)


def probe(runtime, root_pin):
    """Full frozen API.prepare, not acceptance and not a narrower oracle."""
    m = runtime
    m.require(root_pin.get("path") == m.source.root_path(m.base.CONFIG), "PROBE_EXACT_ROOT")
    m.base.scope.pins([root_pin], 1)
    g = m.a.Guard()
    q = binding = None
    out = dict(state="FAILED_READ_ONLY_ACCEPTANCE_PRESSURE_PROBE_NOT_ACCEPTED",
               index=m.base.CONFIG.index, runtime_pin=root_pin, stage="admission",
               accepted_count_before=m.base.CONFIG.before, accepted_count_delta=0,
               Native_frame_reexecuted=False, product_child_executed=False,
               queue_acceptance_called=False, retry_or_resume_performed=False,
               P09_gate="OPEN", P10_started=False, PC_freeze_resolved=False)
    started = time.monotonic()
    try:
        g.acquire()
        out["stage"] = "reader_factory"
        leaf = m.source.prior.leaf_bytes()
        Reader, proof = m.source.snapshot.reader_type(m.a.AcceptanceReader, leaf)
        q = Reader(m.c.ROOT, g.check)
        owner = NS(lock=threading.Lock(), samples=g.samples, checkpoint_io=g.check)
        binding = m.source.prior.prior.metadata.MetadataCheckpoint(q, owner)
        out["source_predicate_projection"] = proof
        out["stage"] = "original_full_prepare"
        row, listing, evidence, validation = m.API.prepare(q, root_pin)
        out.update(original_runtime_state=row["state"],
                   complete_original_runtime_validation=evidence,
                   original_validation_projection=validation)
        # Extra diagnostic source pins do not become claims about Native inputs.
        out["stage"] = "probe_source_binding"
        q.pin(SELF)
        q.pin(TEST)
        out["stage"] = "original_final_fresh_hashes"
        q.finish()
        out["stage"] = "distinct_original_final_sample"
        time.sleep(.5)
        g.check(force=True)
        out.update(state="PASS_FULL_PREPARE_SINGLE_SOURCE_STAT_NOT_QUEUE_ACCEPTANCE",
                   stage="complete", fresh_inputs=len(q.snapshots),
                   fresh_read_passes=q.read_passes, fresh_bytes_read=q.bytes_read,
                   final_fresh_hashes=q.final_fresh_hashes,
                   fresh_input_pins=list(q.snapshots.values()))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        out["error_code"] = closed_error(error)
    finally:
        # Cleanup never consults a pressure guard; no warning restart is allowed.
        if binding is not None:
            binding.restore()
            out["metadata_failfast"] = binding.summary()
        if q is not None:
            out["single_snapshot_source"] = q.source_snapshot_diagnostics()
            out.setdefault("fresh_inputs", len(q.snapshots))
            out.setdefault("fresh_read_passes", q.read_passes)
            out.setdefault("fresh_bytes_read", q.bytes_read)
            out.setdefault("final_fresh_hashes", q.final_fresh_hashes)
        g.close()
        out["cleanup_confirmed"] = g.cleanup
        out["resource_diagnostics"] = resource_diagnostics(g, m.c.decision)
        out["elapsed_seconds"] = time.monotonic() - started
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--root-bytes", type=int, required=True)
    parser.add_argument("--root-sha256", required=True)
    args = parser.parse_args()
    import flat_current_queue_direct_view_runtime_v4 as m
    m.data_path(args.case)
    m.base.configure(args.case)
    root = dict(path=m.source.root_path(m.base.CONFIG), bytes=args.root_bytes,
                sha256=args.root_sha256)
    result = probe(m, root)
    print(json.dumps(result))
    raise SystemExit(0 if result["state"].startswith("PASS_")
                     and result["cleanup_confirmed"] else 2)
