import hashlib
import math
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_open_phase_timing_connection_v1 as m
import native_open_phase_timing_v2 as timing
import current_queue_acquisition_checkpoint as bridge
import native_pressure_failfast_v1 as pressure
import conservative_maintenance as c
from test_locked_runtime_inputs import FakeNative


class Reader:
    def __init__(self): self.snapshots = {}
    def text(self, name):
        raw = (c.ROOT/name).read_bytes()
        self.snapshots[name] = dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        return raw.decode("utf-8").replace("\r\n", "\n")


class Native(FakeNative):
    def __init__(self):
        super().__init__()
        self.pacer.sleeper = lambda delay: setattr(self, "now", math.nextafter(self.now+delay, math.inf))
        self.k = NS(CreateFileW=lambda path, directory: FakeNative.open(self, path, directory))
    def open(self, path, directory):
        self.pacer.reserve()
        return self.k.CreateFileW(path, directory)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original = bridge.load(Reader(), 14, c)
        cls.original = pressure.connect_api(original,
            (c.ROOT/pressure.PRESSURE_PIN["path"]).read_bytes(),
            (c.ROOT/pressure.EARLY_PIN["path"]).read_bytes(),
            acquisition_raw=(c.ROOT/pressure.ACQUISITION_PIN["path"]).read_bytes())
        cls.connected = m.connect_api(cls.original, timing)

    def held(self, cpu=20, stop=None):
        calls=[]
        def checkpoint():
            calls.append(True)
            if stop is not None: raise stop
        owner=NS(lock=threading.Lock(), samples=[dict(system_cpu_percent=cpu)])
        early=self.connected.EarlySourceCheckpoint(checkpoint, owner)
        native=Native(); native.pacer.checkpoint=early
        held=self.connected.InputLocks(c.ROOT,early,owner,NS(phase="metadata_hash"),api=native)
        return held,native,calls

    def rows(self): return {"tools/p09/mock.py":dict(path="tools/p09/mock.py",bytes=1,sha256="a"*64)}

    def test_every_original_pressure_alias_stays_identical(self):
        held,native,_=self.held()
        self.assertIs(held.phase_pacer,native.pacer)
        self.assertIs(held.api.pacer,native.pacer)
        self.assertIs(held.original_open_checkpoint,held.open_pressure)
        self.assertIs(held.phase_checkpoint,held.open_pressure)
        self.assertIs(held.saturation_checkpoint.checkpoint,held.open_pressure)

    def test_original_complete_acquisition_and_close_with_separate_phase_counts(self):
        held,native,calls=self.held(); held.acquire(self.rows())
        row=held.summary()["native_open_phase_timing"]
        for op in row["operations"].values():
            self.assertEqual((op["started"],op["completed"],op["failed"]),(4,4,0))
        self.assertEqual(native.pacer.rate,20); self.assertTrue(calls)
        self.assertTrue(held.close()); self.assertEqual(native.handles,{})

    def test_original_acquisition_warning_stops_before_any_native_open(self):
        held,native,_=self.held(cpu=90)
        with self.assertRaisesRegex(ValueError,"STOP_NATIVE_OPEN_AFTER_HOST_SATURATION"):
            held.acquire(self.rows())
        self.assertEqual(native.counter,0); self.assertEqual(held.owned,[])
        # The original ancestor-admission loop is before acquire's owned-handle
        # try/finally. The enclosing Frame owner performs close on that branch.
        self.assertFalse(held.acquired); self.assertTrue(held.close())

    def test_original_resource_exception_identity_precedes_native_call(self):
        error=ValueError("ORIGINAL_RAM_STOP");held,native,_=self.held(stop=error)
        with self.assertRaises(ValueError) as caught: held.acquire(self.rows())
        self.assertIs(caught.exception,error);self.assertEqual(native.counter,0)

    def test_original_partial_open_failure_closes_existing_handles(self):
        held,native,_=self.held();native.fail_name="mock.py"
        with self.assertRaisesRegex(ValueError,"MOCK_OPEN_FAILURE"):held.acquire(self.rows())
        self.assertTrue(held.closed);self.assertEqual(native.handles,{})
        self.assertEqual(held.summary()["native_open_phase_timing"]["operations"]["original_CreateFileW"]["failed"],1)

    def test_original_api_classes_and_acquire_check_close_methods_not_replaced(self):
        self.assertIs(self.connected.EarlySourceCheckpoint,self.original.EarlySourceCheckpoint)
        for name in ("acquire","check","take","close","verify_held_identities"):
            self.assertIs(getattr(self.connected.InputLocks,name),getattr(self.original.InputLocks,name))


if __name__ == "__main__": unittest.main()
