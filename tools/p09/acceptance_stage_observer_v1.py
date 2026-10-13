"""Bounded stage labels on existing acceptance calls, with no new sampler.

Original guard/read/inventory/finish calls, arguments, return values and errors
are delegated once. Only eight non-path labels and one original sample survive.
Diagnostics are published by the original exclusive writer after cleanup.
"""
from collections import deque
from types import FunctionType, SimpleNamespace as NS

SELF = "tools/p09/acceptance_stage_observer_v1.py"
TEST = "tools/p09/tests/test_acceptance_stage_observer_v1.py"

class Tracker:
    def __init__(self):
        self.current = "outside_io"
        self.final_hash = False
        self.history = deque(maxlen=8)
        self.read_attempts = self.read_completed = self.inventory_attempts = 0
        self.inventory_completed = self.finish_completed = 0
        self.first_stop = None

    def enter(self, stage):
        before = self.current
        self.current = stage
        self.history.append(stage)
        return before

    def stop(self, error, guard):
        if self.first_stop is None:
            samples = getattr(guard, "samples", [])
            sample = dict(samples[-1]) if samples else None
            self.first_stop = dict(stage=self.current, error_type=type(error).__name__,
                original_sample=sample, read_attempts=self.read_attempts,
                read_completed=self.read_completed, inventory_attempts=self.inventory_attempts,
                inventory_completed=self.inventory_completed, finish_completed=self.finish_completed)

    def summary(self):
        return dict(current_stage=self.current, last_stage_labels=list(self.history),
            read_attempts=self.read_attempts, read_completed=self.read_completed,
            inventory_attempts=self.inventory_attempts, inventory_completed=self.inventory_completed,
            finish_completed=self.finish_completed, first_stop=self.first_stop,
            history_bound=8, recorded_file_paths=False, added_sampler_or_process_query=False,
            original_checks_or_byte_reads_skipped=False, original_errors_retained=True,
            original_exclusive_writer_after_cleanup=True, PC_freeze_resolved=False)

def kind(name):
    if name.startswith(("crates/", "protocol/generated/rust/", "tools/xtask/")):
        return "rust_source"
    if name.endswith(".exe"):
        return "binary"
    if name.startswith("implementation/"):
        return "evidence"
    if name.startswith("tools/"):
        return "helper_code"
    return "other"

def projection(execute, tracker):
    original = execute.__globals__["original"]
    guards = []
    class Guard(original.Guard):
        def __init__(self):
            super().__init__()
            guards.append(self)
        def check(self, force=False):
            try:
                return super().check(force=force)
            except Exception as error:
                tracker.stop(error, self)
                raise
    class Reader(original.AcceptanceReader):
        def _read(self, name, parse=False):
            before = tracker.enter(("final_hash:" if tracker.final_hash else "fresh_read:") + kind(name))
            tracker.read_attempts += 1
            try:
                result = super()._read(name, parse=parse)
                tracker.read_completed += 1
                return result
            finally:
                tracker.current = before
        def finish(self):
            before = tracker.enter("final_hash_all")
            previous = tracker.final_hash
            tracker.final_hash = True
            try:
                result = super().finish()
                tracker.finish_completed += 1
                return result
            finally:
                tracker.final_hash = previous
                tracker.current = before
    before_definitions = original.native.definitions
    def definitions(text, names, namespace):
        result = before_definitions(text, names, namespace)
        if names != ("rust_inputs",):
            return result
        inventory = result.rust_inputs
        def rust_inputs(root, checkpoint):
            previous = tracker.enter("rust_inventory")
            tracker.inventory_attempts += 1
            try:
                result = inventory(root, checkpoint)
                tracker.inventory_completed += 1
                return result
            finally:
                tracker.current = previous
        return NS(rust_inputs=rust_inputs)
    native = NS(**{**vars(original.native), "definitions": definitions})
    private = NS(**{**vars(original), "Guard": Guard, "AcceptanceReader": Reader, "native": native})
    return FunctionType(execute.__code__, dict(execute.__globals__, original=private),
        argdefs=execute.__defaults__, closure=execute.__closure__)

def connect_fanout(fanout, tracker):
    acceptance = fanout.prior
    def projected(*args, **kwargs):
        execute, state = acceptance.projection(*args, **kwargs)
        return projection(execute, tracker), state
    original_publish = acceptance.prior.publish
    def publish(path, name, row):
        return original_publish(path, name, {**row, "acceptance_stage_diagnostics": tracker.summary()})
    private_v2 = NS(**{**vars(acceptance.prior), "publish": publish})
    private_run = FunctionType(acceptance.run.__code__,
        dict(acceptance.run.__globals__, prior=private_v2),
        argdefs=acceptance.run.__defaults__, closure=acceptance.run.__closure__)
    private = NS(**{**vars(acceptance), "projection": projected, "run": private_run})
    return FunctionType(fanout.run.__code__, dict(fanout.run.__globals__, prior=private),
        argdefs=fanout.run.__defaults__, closure=fanout.run.__closure__)
