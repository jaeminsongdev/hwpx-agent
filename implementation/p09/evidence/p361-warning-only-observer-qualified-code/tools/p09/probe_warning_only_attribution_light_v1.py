"""One bounded real-Windows observer probe; never full source/product replay."""
import argparse
import json
import re
import threading
import time
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_source_stat_runtime_v2 as r
import serial_cpu_attribution_budget_v1 as budget
import warning_only_serial_attribution_v1 as observer

SELF = "tools/p09/probe_warning_only_attribution_light_v1.py"
QUAL = "implementation/p09/evidence/p09-361-warning-only-observer-code15-r312.v1.json"


def run(pin):
    r.base.configure(129)
    out = dict(state="FAILED_NOT_OBSERVED", accepted_count_after=122, accepted_count_delta=0,
        actual_Native_source_executed=False, product_child_replayed=False,
        original_source_failure_retried=False, runtime_source_connection_qualified=False,
        PC_freeze_resolved=False)
    preparation = r.a.Guard(); q = bridge = real = None; objects = []
    try:
        preparation.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, preparation.check)
        bridge = r.prior.prior.metadata.MetadataCheckpoint(q, NS(
            lock=threading.Lock(), samples=preparation.samples, checkpoint_io=preparation.check))
        codequal = r.a.read_exact(q, pin)
        r.a.fields(codequal, dict(
            state="PASS_WARNING_ONLY15_AND_EXACT_ORIGINAL_PDH_BUDGET_PROJECTION_NOT_RUNTIME_SOURCE_OR_QUEUE",
            accepted_count_after=122, accepted_count_delta=0, cleanup_confirmed=True),
            "LIGHT_OBSERVER_QUAL")
        r.a.exact(codequal["contracts"], dict(run=15, errors=0, failures=0, skipped=0),
            "LIGHT_OBSERVER_CODE15")
        for sourcepin in codequal["new_code_pins"] + codequal["unchanged_dependency_pins"]:
            r.a.exact(q.pin(sourcepin["path"]), sourcepin, "LIGHT_OBSERVER_EXACT_CODE")
        q.pin("tools/p09/accept_case112_current_epoch.py")
        q.pin(SELF)
        authority = r.a.read_exact(q, codequal["prior_authority_pin"])
        r.a.fields(authority, dict(accepted_count_after=122, next_runtime_index=129,
            accepted_count_delta=1, accepted_current_generation_case_count=17), "LIGHT_OBSERVER_CURSOR")
        rawpin, raw = q._read(budget.ORIGINAL_PIN["path"], parse=True)
        q._bind(rawpin["path"], rawpin)
        r.a.exact(rawpin, budget.ORIGINAL_PIN, "LIGHT_ORIGINAL_PROBE_BYTES")
        factory, proof = budget.make_probe(bytes(raw))
        q.finish()
        out.update(bound_source_pins=list(q.snapshots.values()),
            original_budget_projection=proof, preparation_inputs=len(q.snapshots),
            preparation_read_passes=q.read_passes, preparation_bytes_read=q.bytes_read,
            preparation_final_fresh_hashes=q.final_fresh_hashes)
        bridge.restore(); preparation.close()
        r.a.require(preparation.cleanup, "LIGHT_PREPARATION_CLEANUP")

        default_windows, default_guard = r.c.Windows, r.a.Guard
        Windows = observer.windows_type(default_windows, objects, factory=factory, clock=time.monotonic)
        # Exact original Guard init bytecode, isolated globals; no default class mutation.
        initializer = r.a.Guard.__init__
        environment = dict(initializer.__globals__,
            c=NS(**{**vars(r.c), "Windows": Windows}))
        class ObservedGuard(r.a.Guard):
            pass
        ObservedGuard.__init__ = FunctionType(initializer.__code__, environment,
            argdefs=initializer.__defaults__)
        r.a.require(ObservedGuard.__init__.__code__ is initializer.__code__,
            "LIGHT_ORIGINAL_GUARD_INIT")
        real = ObservedGuard()
        real.acquire()
        for _ in range(4):
            time.sleep(.5); real.check(force=True)
        # Explicit optional feasibility read, not a manufactured high-CPU sample.
        # Same observer thread/owner, same original seven counters and cost gate.
        real.check()
        diagnostic = real.windows.attribution_probe.sample()
        time.sleep(.5); real.check(force=True)
        r.a.require(len(objects) == 1, "LIGHT_ONE_ORIGINAL_OBSERVER")
        r.a.require(r.c.Windows is default_windows and r.a.Guard is default_guard,
            "LIGHT_DEFAULT_CLASSES_UNCHANGED")
        out.update(state="PASS_REAL_WARNING_ONLY_OBSERVER_LIGHT_CONNECTION_NOT_FULL_SOURCE_OR_QUEUE",
            exact_original_Guard_init_code=True, default_Windows_and_Guard_classes_mutated=False,
            real_resource_samples=len(real.samples),
            CPU_max=max(x["system_cpu_percent"] for x in real.samples),
            RAM_min=min(x["available_ram_percent"] for x in real.samples),
            explicit_PDH_feasibility_not_triggered_by_real_warning=True,
            explicit_PDH_observation=diagnostic,
            historical_CPU_spike_attributed=False, actual_warning_native_run_qualified=False,
            original_warning_percent=75, original_PDH_sample_seconds=.05,
            original_PDH_total_seconds=2.0)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        out["error_code"] = str(exc) if isinstance(exc, ValueError) and re.fullmatch(
            "[A-Z0-9_]{1,256}", str(exc)) else "REDACTED_LIGHT_OBSERVER_FAILURE"
    finally:
        if bridge:
            bridge.restore()
        preparation.close()
        if real:
            real.close()
        pdh_clean = observer.close(objects)
        out.update(preparation_cleanup_confirmed=preparation.cleanup,
            real_guard_cleanup_confirmed=None if real is None else real.cleanup,
            PDH_cleanup_confirmed=pdh_clean, warning_only_observer=observer.summary(objects))
        if not preparation.cleanup or (real and not real.cleanup) or not pdh_clean:
            out["state"] = "FAILED_NOT_OBSERVED"
    print(json.dumps(out))
    return 0 if out["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification-bytes", type=int, required=True)
    parser.add_argument("--qualification-sha256", required=True)
    args = parser.parse_args()
    pin = dict(path=QUAL, bytes=args.qualification_bytes, sha256=args.qualification_sha256)
    r.base.scope.pins([pin], 1)
    raise SystemExit(run(pin))
