"""Explicit physical envelope publication + two-pass decoder connection.

No existing input is rewritten. The boundary reader returns PHYSICAL pins;
semantic hashes are additional evidence, never relabelled as original disk IO.
No product/Gate permission. Decoder work has one aggregate five-second budget
shared across both readers, with original guard first and no retry or cooling.
"""
import hashlib
import math
import os
from pathlib import Path
import threading
import time
import runtime_envelope_source_projection_v1 as source
import owned_source_read_pressure as bytes_policy

SELF = "tools/p09/runtime_envelope_physical_io_v1.py"
TEST = "tools/p09/tests/test_runtime_envelope_physical_io_v1.py"
CHUNK = 64 * 1024
DECODE_SECONDS = 5.0


def require(ok, code):
    if not ok: raise ValueError("ENVELOPE_PHYSICAL_IO_" + code)


def publish_exclusive(root, raw, pin, checkpoint, *, write_pacer=None):
    require(callable(checkpoint), "CHECKPOINT")
    checkpoint()
    write_pacer = bytes_policy.OwnedPacer() if write_pacer is None else write_pacer
    require(type(write_pacer) is bytes_policy.OwnedPacer, "ORIGINAL_BOUNDED_BYTE_PACER")
    write_pacer.select(pin["path"])
    require(write_pacer.rate == 2*1024*1024, "ENCODED_WRITE_RATE2MIB")
    expected = source.copy_pin(pin)
    require(expected["path"].startswith(source.PREFIX)
        and expected["path"].endswith(".envelope.v1.json"), "EXPLICIT_ENCODED_DESTINATION")
    require(type(raw) is bytes and 0 < len(raw) <= source.codec.MAX_BYTES
        and len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"], "EXACT_ENCODED_BYTES")
    root = Path(root).absolute(); destination = root / expected["path"]
    require(destination.is_relative_to(root), "SCOPED_DESTINATION")
    for parent in (destination.parent, *destination.parent.parents):
        checkpoint()
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), "DIRECT_ANCESTOR")
        if parent == root: break
    require(not destination.exists() and not destination.is_symlink() and not destination.is_junction(), "REFUSE_OVERWRITE")
    written = 0
    # Exclusive creation is the race check. A stopped/partial artifact remains
    # failed and cannot be silently overwritten or promoted after power loss.
    with destination.open("xb") as stream:
        for offset in range(0, len(raw), CHUNK):
            checkpoint()
            block = raw[offset:offset + CHUNK]
            write_pacer.reserve(checkpoint)
            count = stream.write(block)
            require(type(count) is int and count == len(block), "COMPLETE_CHUNK_WRITE")
            write_pacer.refund(count)
            written += count
        checkpoint(); stream.flush(); os.fsync(stream.fileno()); checkpoint()
    require(written == len(raw), "COMPLETE_FILE_WRITE")
    return dict(expected)


class DecoderBudget:
    def __init__(self, checkpoint, clock=time.monotonic, identity=lambda: (os.getpid(), threading.get_ident())):
        require(callable(checkpoint) and callable(clock) and callable(identity), "BUDGET_CALLBACKS")
        self.checkpoint, self.clock, self.identity = checkpoint, clock, identity
        self.owner = identity(); self.elapsed = 0.0; self.active = None
        self.attempts = self.completed = 0; self.error = None; self.last_clock = None

    def now(self):
        value = self.clock()
        require(type(value) in (int, float) and math.isfinite(value)
            and (self.last_clock is None or value >= self.last_clock), "MONOTONIC_DECODER_CLOCK")
        self.last_clock = value
        return value

    def check(self):
        self.checkpoint()  # Original hard/resource/lock failure takes priority.
        require(self.identity() == self.owner, "EXACT_DECODER_OWNER")
        if self.error is not None: raise self.error
        now = self.now()
        total = self.elapsed + (0.0 if self.active is None else now - self.active)
        if total > DECODE_SECONDS:
            self.error = ValueError("STOP_AGGREGATE_ENVELOPE_DECODER5")
            raise self.error

    def run(self, operation):
        self.check(); require(callable(operation) and self.active is None, "ONE_SERIAL_DECODER_OPERATION")
        self.active = self.now(); self.attempts += 1
        error = None; value = None
        try:
            value = operation(self.check); self.check()
        except BaseException as caught:
            error = caught
        try:
            end = self.now(); self.elapsed += end - self.active
        except BaseException as caught:
            if error is None: error = caught
        finally:
            self.active = None
        if error is not None:
            self.error = error; raise error
        self.completed += 1
        return value

    def evidence(self):
        return dict(aggregate_limit_seconds=DECODE_SECONDS, elapsed_decoder_work_seconds=self.elapsed,
            attempted_decodes=self.attempts, completed_decodes=self.completed,
            active_decode=self.active is not None, terminal_error_seen=self.error is not None,
            two_boundaries_share_one_budget=True, physical_read_waits_charged_by_original_IO_budget=True,
            original_guard_called_first=True, extra_sampler_or_thread=False,
            blocking_call_hard_preemption_guaranteed=False, GO_authorized=False)


def boundary_reader_type(original, projection, budget):
    require(type(original) is type and type(projection) is source.Projection
        and type(budget) is DecoderBudget, "EXACT_BOUNDARY_CONNECTION")
    reverse = {}
    for name, physical in projection._bindings.items():
        require(physical["path"] not in reverse, "BIJECTIVE_PHYSICAL_MAPPING")
        reverse[physical["path"]] = name
    class Reader(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.semantic_decode_counts = {}; self.semantic_decoded_bytes = 0

        def _read(self, name, parse=False):
            if name not in reverse: return super()._read(name, parse=parse)
            # Preserve the original full physical stream, pacer, identity check,
            # counter and error. A fresh encoded parse buffer is bounded by the
            # original reader's per-input 16MiB allocation budget.
            pin, buffer = super()._read(name, parse=True)
            logical = reverse[name]
            require(pin == projection.physical_pins[name], "ACTUAL_PHYSICAL_SOURCE_PIN")
            decoded = budget.run(lambda guard: projection.decode_fresh(logical, pin, bytes(buffer), guard))
            self.semantic_decode_counts[logical] = self.semantic_decode_counts.get(logical, 0) + 1
            self.semantic_decoded_bytes += len(decoded)
            del decoded
            return pin, buffer if parse else None

        def diagnostics(self):
            row = super().diagnostics()
            return dict(row, explicit_envelope_semantic_decode=dict(counts=dict(self.semantic_decode_counts),
                decoded_bytes=self.semantic_decoded_bytes, original_physical_pin_and_counter_retained=True,
                semantic_bytes_not_reported_as_disk_bytes=True, decoder_budget=budget.evidence()))
    return Reader
