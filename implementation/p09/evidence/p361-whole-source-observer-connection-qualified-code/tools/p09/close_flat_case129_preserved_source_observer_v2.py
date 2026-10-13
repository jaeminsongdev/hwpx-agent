"""Connect the qualified warning-only observer to the UNCHANGED full source run.

Original v1 run/init bytecode, Native/byte oracle, guards/rates/600s stay intact.
All prior1904 inputs retained. Never replay the product or promote old failures.
Only source/preflight002 is permitted; no retry loop or global class mutation.
"""
import argparse
import json
import time
from types import FunctionType, SimpleNamespace as NS

import close_flat_case129_preserved_source_v1 as original
import serial_cpu_attribution_budget_v1 as budget
import warning_only_serial_attribution_v1 as observer

a, c, scope = original.a, original.c, original.scope
SELF = "tools/p09/close_flat_case129_preserved_source_observer_v2.py"
TEST = "tools/p09/tests/test_close_flat_case129_preserved_source_observer_v2.py"
QUAL = "implementation/p09/evidence/p09-361-whole-source-observer-connection-code-r317.v1.json"
SOURCE_QUAL = dict(path=original.QUALIFICATION, bytes=5602,
    sha256="dd1229bfb6b438a0ec3be3a798170897f70bad75b26f7bf1ede0c6e57f00997b")
OBS_QUAL = dict(path="implementation/p09/evidence/p09-361-warning-only-observer-code15-r312.v1.json",
    bytes=3296, sha256="f178efd3f9fe39f1a83e2230f486f202a9255447a76232a088b5a8b782300d65")
OBS_REAL = dict(path="implementation/p09/evidence/p09-361-warning-only-observer-real-light-r313.v1.json",
    bytes=5796, sha256="baff2d0bcfc10746a16999f66262592010b5a4851b404abfdf623bf4f594d581")
PREVIOUS_SOURCE = dict(path="implementation/p09/evidence/p09-361-case129-independent-full-source-run001.v1.json",
    bytes=500493, sha256="5acd00d741b421a51f40e514d2b53a191d451716b8132f52dd012c661bcdd8ba")
CODE_PASS = "PASS_WHOLE_SOURCE_OBSERVER_CONNECTION_CODE_NOT_ACTUAL_SOURCE_OR_QUEUE"


def require(ok, code):
    if not ok:
        raise ValueError("SOURCE_OBSERVER_CONNECTION_" + code)


def retain_previous_scope(required, previous):
    a.fields(previous, dict(state="FAILED_NOT_QUALIFIED",
        error_code="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", accepted_count_after=122,
        accepted_count_delta=0, independent_source_frame_qualified=False,
        original_product_body_replayed=False, resource_cleanup_confirmed=True,
        source_frame_cleanup_confirmed=True), "CONNECTION_PREVIOUS_FAILED_SOURCE")
    a.fields(previous["source_frame"], dict(frame_state="CLOSED", registered_live_frame=False,
        actual_byte_boundaries=[]), "CONNECTION_CLOSED_PREVIOUS_ACQUISITION")
    a.fields(previous["source_frame"]["handles"], dict(input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
        active_reader_bindings=0, active_byte_streams=0), "CONNECTION_PREVIOUS_NO_LIVE_HANDLES")
    prior = scope.pins(previous["required_source_pins"])
    require(len(prior) == 1904, "EXACT_PREVIOUS1904")
    merged = scope.extend(prior, required)
    require(all(merged[name] == pin for name, pin in prior.items()), "ALL_PREVIOUS_INPUTS_RETAINED")
    return merged


def guard_type(base, windows, objects, closed):
    initializer = base.__init__
    environment = dict(initializer.__globals__, c=NS(**{**vars(c), "Windows": windows}))
    class Guard(base):
        def close(self):
            try:
                super().close()
            finally:
                closed["PDH_cleanup_confirmed"] = observer.close(objects)
    Guard.__init__ = FunctionType(initializer.__code__, environment,
        argdefs=initializer.__defaults__)
    require(Guard.__init__.__code__ is initializer.__code__, "EXACT_ORIGINAL_INIT_CODE")
    return Guard


def decorate_document(out, objects, closed, pins):
    """Add explicit observer epoch; NEVER turn a failure into a success."""
    clean = closed.get("PDH_cleanup_confirmed", False)
    out["source_observer_epoch"] = dict(
        schema_version="hwpx-agent.p09-full-source-warning-only-observer/v2",
        qualification_pin=pins["connection_qualification_pin"],
        observer_qualification_pin=OBS_QUAL, real_light_observer_pin=OBS_REAL,
        prior_failed_source_pin=PREVIOUS_SOURCE, original_run_and_guard_init_bytecode=True,
        default_module_classes_mutated=False, previous1904_source_inputs_retained=True,
        PDH_cleanup_confirmed=clean, observer=observer.summary(objects),
        original_PDH_allowance_seconds=2.05, old_failed_root_promoted=False,
        product_body_replayed=False, causal_trigger_or_freeze_fix_established=False)
    if not clean and out["state"] in (original.PASS, original.PREFLIGHT_PASS):
        out.update(state="FAILED_NOT_QUALIFIED", independent_source_frame_qualified=False,
            error_code="SOURCE_OBSERVER_PDH_CLEANUP_FAILED")
    return out


def project_run(guard, prepare, decorate):
    def dump(out, *args, **kwargs):
        return json.dump(decorate(out), *args, **kwargs)
    environment = dict(original.run.__globals__, a=NS(**{**vars(a), "Guard": guard}),
        prepare=prepare, json=NS(**{**vars(json), "dump": dump}))
    return FunctionType(original.run.__code__, environment,
        argdefs=original.run.__defaults__)


def bind_connection(q, pin):
    qual = a.read_exact(q, pin)
    a.fields(qual, dict(state=CODE_PASS, accepted_count_after=122,
        accepted_count_delta=0, cleanup_confirmed=True), "CONNECTION_CODE_QUAL")
    a.exact(qual["contracts"], dict(run=10, errors=0, failures=0, skipped=0), "CONNECTION_CODE10")
    require(set(scope.pins(qual["new_code_pins"], 2)) == {SELF, TEST}, "EXACT_CONNECTION_CODE2")
    for sourcepin in qual["new_code_pins"]:
        a.exact(q.pin(sourcepin["path"]), sourcepin, "CONNECTION_CODE_BYTES")
    observed = a.read_exact(q, OBS_QUAL)
    a.exact(observed["contracts"], dict(run=15, errors=0, failures=0, skipped=0), "CONNECTION_OBSERVER15")
    for sourcepin in observed["new_code_pins"] + observed["unchanged_dependency_pins"]:
        a.exact(q.pin(sourcepin["path"]), sourcepin, "CONNECTION_OBSERVER_CODE_BYTES")
    real = a.read_exact(q, OBS_REAL)
    a.fields(real, dict(state="PASS_REAL_WARNING_ONLY_OBSERVER_LIGHT_CONNECTION_NOT_FULL_SOURCE_OR_QUEUE",
        exact_original_Guard_init_code=True, default_Windows_and_Guard_classes_mutated=False,
        preparation_cleanup_confirmed=True, real_guard_cleanup_confirmed=True,
        PDH_cleanup_confirmed=True, actual_Native_source_executed=False), "CONNECTION_REAL_PROTOTYPE")
    for sourcepin in real["bound_source_pins"]:
        a.exact(q.pin(sourcepin["path"]), sourcepin, "CONNECTION_REAL_BOUND_CODE_BYTES")
    return a.read_exact(q, PREVIOUS_SOURCE)


def run(mode, run_number, code_pin):
    require(mode in ("preflight", "source") and type(run_number) is int and run_number == 2,
        "ONE_EXPLICIT_SECOND_ATTEMPT")
    # Fully guarded bootstrap; closed BEFORE the new full-source observer exists.
    g = a.Guard(); q = None; bridge = None
    try:
        g.acquire()
        q = a.AcceptanceReader(c.ROOT, g.check)
        owner = NS(lock=original.threading.Lock(), samples=g.samples, checkpoint_io=g.check)
        bridge = original.runtime.prior.prior.metadata.MetadataCheckpoint(q, owner)
        bind_connection(q, code_pin)
        rawpin, raw = q._read(budget.ORIGINAL_PIN["path"], parse=True)
        q._bind(rawpin["path"], rawpin)
        a.exact(rawpin, budget.ORIGINAL_PIN, "CONNECTION_ORIGINAL_PROBE_SOURCE")
        factory, _ = budget.make_probe(bytes(raw))
        q.finish()
    finally:
        if bridge:
            bridge.restore()
        g.close()
    require(g.cleanup, "BOOTSTRAP_CLEANUP")
    objects = []; closed = {}
    default_windows, default_guard = c.Windows, a.Guard
    Windows = observer.windows_type(default_windows, objects, factory=factory, clock=time.monotonic)
    Guard = guard_type(default_guard, Windows, objects, closed)
    def prepare(reader, source_pin):
        previous = bind_connection(reader, code_pin)
        prepared = original.prepare(reader, source_pin)
        required = retain_previous_scope(prepared[2], previous)
        return (*prepared[:2], required, *prepared[3:])
    def decorate(out):
        require(c.Windows is default_windows and a.Guard is default_guard, "DEFAULT_CLASSES_UNCHANGED")
        return decorate_document(out, objects, closed, dict(connection_qualification_pin=code_pin))
    execute = project_run(Guard, prepare, decorate)
    require(execute.__code__ is original.run.__code__, "EXACT_ORIGINAL_FULL_SOURCE_RUN_CODE")
    return execute(mode, run_number, SOURCE_QUAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--source", action="store_true")
    parser.add_argument("--qualification-bytes", type=int, required=True)
    parser.add_argument("--qualification-sha256", required=True)
    args = parser.parse_args()
    require(args.preflight != args.source, "ONE_MODE")
    pin = dict(path=QUAL, bytes=args.qualification_bytes, sha256=args.qualification_sha256)
    scope.pins([pin], 1)
    raise SystemExit(run("preflight" if args.preflight else "source", 2, pin))
