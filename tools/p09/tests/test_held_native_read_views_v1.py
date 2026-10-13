"""Guarded direct-view component contracts; never runtime134 acceptance."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import held_native_read_views_v1 as tested
import accept_case112_current_epoch as a
import test_locked_runtime_inputs as fake

CHECKPOINT = lambda: None


class FakeRead:
    def __init__(self):
        self.data = bytearray(b"abc")
        self.position = {}
        self.calls = []
        self.fail = None

    def reset(self, handle):
        self.calls.append(("reset", handle))
        if self.fail == "reset":
            raise OSError("MOCK_RESET")
        self.position[handle] = 0
        return 0

    def readinto(self, handle, buffer):
        self.calls.append(("readinto", handle))
        if self.fail == "read":
            raise OSError("MOCK_READ")
        if self.fail == "count":
            return True
        start = self.position[handle]
        count = min(len(buffer), len(self.data) - start)
        buffer[:count] = self.data[start:start + count]
        self.position[handle] = start + count
        return count


class ViewContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        q = a.AcceptanceReader(tested.original.b.locks.ROOT, CHECKPOINT)
        pin, raw = q._read(tested.LOCK_PIN["path"], parse=True)
        q._bind(pin["path"], pin)
        a.exact(pin, tested.LOCK_PIN, "ORIGINAL_LOCK_SOURCE")
        cls.raw = bytes(raw)
        projected, cls.proof = tested.original.reader_sources_projection(cls.raw)
        cls.Locks = tested.locks_type(tested.original.b.BorrowedInputLocks, projected)
        q.finish()

    def setUp(self):
        CHECKPOINT()
        self.pin = dict(path="tools/p09/mock.py", bytes=1, sha256="a" * 64)
        self.native = fake.FakeNative()
        self.native.pacer.rate = 20
        self.io = FakeRead()
        self.held = self.Locks(tested.original.b.locks.ROOT, CHECKPOINT,
                               api=self.native, view_api=self.io)
        self.held.acquire({self.pin["path"]: self.pin})
        self.reader = NS(_source=lambda name: tested.original.b.locks.ROOT / name)

    def tearDown(self):
        self.native.close_fail = False
        self.held.checkpoint = CHECKPOINT
        if self.held.borrower:
            self.held.borrower.identity = lambda: self.held.borrower.owner
            if self.held.borrower.loan:
                self.held.borrower.loan.close = lambda: setattr(self.held.borrower.loan, "closed", True)
        self.held.close()
        CHECKPOINT()

    def read(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                return stream.read(tested.CHUNK_BYTES)

    def test_two_fresh_reads_same_original_identity_no_physical_duplicate(self):
        original = set(self.native.handles)
        counter = self.native.counter
        self.assertEqual(self.read(), b"abc")
        self.assertEqual(self.read(), b"abc")
        self.assertEqual(set(self.native.handles), original)
        self.assertEqual(self.native.counter, counter)
        self.held.verify_two_byte_passes({self.pin["path"]: self.pin})
        row = self.held.borrower.summary()
        self.assertEqual((row["duplicate_handles_opened"], row["CRT_descriptors_created"]), (0, 0))
        self.assertEqual((row["logical_views_opened"], row["logical_views_closed"]), (2, 2))
        self.assertEqual(row["shared_offset_resets"], 2)
        self.assertTrue(self.held.close())
        self.assertEqual(self.native.handles, {})

    def test_original_binding_AST_and_identity_guards_preserved(self):
        self.assertTrue(self.proof["original_reader_binding_AST_restored_exactly"])
        self.assertFalse(self.proof["original_path_identity_binding_and_active_stream_guards_replaced"])
        with self.assertRaises(ValueError):
            tested.original.reader_sources_projection(self.raw[:-1])

    def test_no_pathname_open_no_cached_bytes(self):
        with patch.object(Path, "open", side_effect=AssertionError("NO_PATHNAME_OPEN")):
            self.assertEqual(self.read(), b"abc")
            self.io.data[:] = b"xyz"
            self.assertEqual(self.read(), b"xyz")

    def test_original_pressure_callback_without_physical_open_credit(self):
        calls = []
        self.native.pacer.checkpoint = lambda: calls.append(True)
        before = (self.native.pacer.opens, self.native.pacer.previous, self.native.pacer.rate)
        self.read()
        self.read()
        self.assertEqual(len(calls), 2)
        self.assertEqual((self.native.pacer.opens, self.native.pacer.previous, self.native.pacer.rate), before)

    def test_pressure_stop_before_reset_or_read(self):
        self.native.pacer.checkpoint = lambda: (_ for _ in ()).throw(ValueError("CPU_STOP"))
        with self.assertRaisesRegex(ValueError, "CPU_STOP"):
            self.read()
        self.assertEqual(self.io.calls, [])

    def test_original_path_guard_before_view_creation(self):
        self.reader._source = lambda _: (_ for _ in ()).throw(ValueError("PATH_STOP"))
        with self.assertRaisesRegex(ValueError, "PATH_STOP"):
            self.read()
        self.assertEqual(self.io.calls, [])

    def test_identity_or_inheritability_drift_rejected_on_second_read(self):
        self.read()
        handle = self.held.owned[-1][2]
        old = copy.deepcopy(self.native.handles[handle])
        for key, value in (("identity", [9, 9]), ("inheritable", True)):
            self.native.handles[handle] = dict(old, **{key: value})
            with self.assertRaisesRegex(ValueError, "BYTE_STREAM_IDENTITY_DRIFT"):
                self.read()
        self.native.handles[handle] = old

    def test_readinto_short_and_EOF_never_exposes_stale_workspace_tail(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                buffer = bytearray(b"!" * 8)
                self.assertEqual(stream.readinto(buffer), 3)
                self.assertEqual(buffer, b"abc!!!!!")
                self.assertEqual(stream.readinto(buffer), 0)

    def test_invalid_buffer_and_unbounded_read_rejected(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                for buffer in (b"immutable", bytearray(), bytearray(tested.CHUNK_BYTES + 1)):
                    with self.assertRaises(ValueError):
                        stream.readinto(buffer)
                with self.assertRaises(ValueError):
                    stream.read(-1)
                with self.assertRaises(ValueError):
                    stream.seek(1)

    def test_read_error_or_invalid_count_returns_lease_without_closing_handle(self):
        original = set(self.native.handles)
        for stage in ("read", "count", "reset"):
            self.io.fail = stage
            with self.assertRaises((ValueError, OSError)):
                self.read()
            self.assertIsNone(self.held.borrower.loan)
            self.assertEqual(set(self.native.handles), original)
        self.io.fail = None

    def test_stale_view_and_source_rejected_across_bindings(self):
        with self.held.reader_sources(self.reader):
            source = self.reader._source(self.pin["path"])
            with source.open("rb") as stream:
                view = stream
                self.assertEqual(stream.read(8), b"abc")
        with self.assertRaises(ValueError):
            view.read(8)
        with self.held.reader_sources(self.reader):
            with self.assertRaises(ValueError):
                with source.open("rb"):
                    pass

    def test_nested_view_binding_and_wrong_thread_rejected(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb"):
                with self.assertRaises(ValueError):
                    with self.reader._source(self.pin["path"]).open("rb"):
                        pass
            with self.assertRaises(ValueError):
                with self.held.reader_sources(NS(_source=self.reader._source)):
                    pass
        self.held.borrower.identity = lambda: ("wrong", 0)
        with self.assertRaises(ValueError):
            self.read()

    def test_closed_view_cannot_continue_reading_or_close_original_handle(self):
        original = set(self.native.handles)
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                stream.close()
                with self.assertRaises(ValueError):
                    stream.read(8)
                self.assertEqual(set(self.native.handles), original)

    def test_post_read_resource_stop_never_returns_bytes(self):
        read = self.io.readinto
        def stop_after_read(handle, buffer):
            count = read(handle, buffer)
            self.held.checkpoint = lambda: (_ for _ in ()).throw(ValueError("POST_READ_STOP"))
            return count
        self.io.readinto = stop_after_read
        with self.assertRaisesRegex(ValueError, "POST_READ_STOP"):
            self.read()
        self.assertIsNone(self.held.borrower.loan)

    def test_original_held_close_failure_never_becomes_cleanup_success(self):
        self.read()
        self.native.close_fail = True
        self.assertFalse(self.held.close())
        self.assertFalse(self.held.summary()["input_lock_cleanup_confirmed"])
        self.native.close_fail = False
        self.assertTrue(self.held.close())
        # Exact old InputLocks reports successful eventual physical cleanup;
        # it separately retains failed-attempt history for the full oracle.
        # Do not redefine that old meaning or erase the prior failure count.
        self.assertTrue(self.held.summary()["input_lock_cleanup_confirmed"])
        self.assertGreater(self.held.summary()["handle_close_failed_attempts"], 0)

    def test_router_fallback_keeps_original_ordinary_stream_extraction(self):
        self.assertEqual(self.held.api.stream_handle(NS(native_handle=123)), 123)
        other = tested.StreamIdentityRouter(self.native, NS(borrower=None))
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                with self.assertRaisesRegex(ValueError, "EXACT_STREAM_OWNER"):
                    other.stream_handle(stream)

    def test_view_open_cannot_bypass_original_reservation(self):
        self.read()
        borrower = self.held.borrower
        with borrower.sources(self.reader):
            self.reader._p206_input_lock_owner = self.held
            self.held.active_readers.add(id(self.reader))
            try:
                with self.assertRaisesRegex(ValueError, "EXACT_RESERVED_HELD_PATH"):
                    with borrower.open(tested.original.b.locks.ROOT / self.pin["path"], "rb"):
                        pass
            finally:
                del self.reader._p206_input_lock_owner
                self.held.active_readers.clear()

    def test_partial_read_exception_restores_original_source_and_keeps_handles(self):
        source = self.reader._source
        handles = set(self.native.handles)
        with self.assertRaises(RuntimeError):
            with self.held.reader_sources(self.reader):
                with self.reader._source(self.pin["path"]).open("rb") as stream:
                    self.assertEqual(stream.read(1), b"a")
                    raise RuntimeError("PARTIAL_READ")
        self.assertIs(self.reader._source, source)
        self.assertFalse(self.held.active_readers)
        self.assertIsNone(self.held.borrower.loan)
        self.assertEqual(set(self.native.handles), handles)
        with self.assertRaises(ValueError):
            self.held.verify_two_byte_passes({self.pin["path"]: self.pin})

    def test_logical_close_failure_is_latched_and_original_cleanup_still_attempted(self):
        def fail_close():
            raise OSError("LOGICAL_CLOSE")
        with self.assertRaisesRegex(ValueError, "LOGICAL_VIEW_CLEANUP_FAILED"):
            with self.held.reader_sources(self.reader):
                with self.reader._source(self.pin["path"]).open("rb") as stream:
                    stream.close = fail_close
        borrower = self.held.borrower
        self.assertIsNotNone(borrower.loan)
        self.assertFalse(self.held.close())
        self.assertEqual(self.native.handles, {})
        borrower.loan.close = lambda: setattr(borrower.loan, "closed", True)
        self.assertTrue(self.held.close())
        self.assertFalse(self.held.summary()["input_lock_cleanup_confirmed"])

    def test_held_handle_mapping_is_not_mutable(self):
        self.read()
        with self.assertRaises(TypeError):
            self.held.borrower.handles[str(tested.original.b.locks.ROOT / self.pin["path"])] = 999

    def test_noncontiguous_buffer_cannot_be_copied_or_read_as_success(self):
        with self.held.reader_sources(self.reader):
            with self.reader._source(self.pin["path"]).open("rb") as stream:
                with self.assertRaisesRegex(ValueError, "WRITABLE_CONTIGUOUS_WORKSPACE"):
                    stream.readinto(memoryview(bytearray(8))[::2])

    def test_model_still_rejects_unchanged600_overflow_and_modified_PDH_cost(self):
        rows = {self.pin["path"]: self.pin,
                "bin.exe": dict(path="bin.exe", bytes=512 * 1048576, sha256="a" * 64)}
        with self.assertRaisesRegex(ValueError, "WHOLE_CLOSURE_INSIDE_UNCHANGED600"):
            tested.model(rows, 167)
        with self.assertRaisesRegex(ValueError, "EXPLICIT_PDH_COST"):
            tested.model(rows, 167, PDH_seconds=0)

    def test_model_removes_only_nonexistent_physical_duplicate_cost(self):
        import current_stored_runtime_scope as scope
        rows = {self.pin["path"]: self.pin,
                "bin.exe": dict(path="bin.exe", bytes=1048576, sha256="a" * 64)}
        baseline = scope.cost(rows, 14)
        retained = tested.original.model(rows, 167)
        model = tested.model(rows, 167)
        self.assertEqual(model["two_actual_byte_pass_native_reservations"], 0)
        self.assertEqual(model["two_actual_byte_pass_nominal_seconds"], baseline["two_actual_byte_pass_nominal_seconds"])
        self.assertEqual(model["unallocated_margin_seconds"], 60)
        self.assertEqual(model["unchanged_lock_deadline_seconds"], 600)
        self.assertEqual(model["unchanged_byte_native_ceiling_per_second"], 20)
        self.assertAlmostEqual(model["predicted_runtime_combined_seconds"], retained["predicted_runtime_combined_seconds"] - len(rows) / 20)
        self.assertFalse(model["direct_view_connection_qualified"])
        self.assertFalse(model["GO_authorized"])


if __name__ == "__main__":
    guard = a.Guard()
    result = None
    try:
        guard.acquire()
        CHECKPOINT = guard.check
        result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(ViewContracts))
    finally:
        guard.close()
    print(json.dumps(dict(contract_count=result.testsRun if result else 0,
                          passed=bool(result and result.wasSuccessful()), cleanup_confirmed=guard.cleanup,
                          actual_product_or_full_Native_test=False, synthetic_component_only=True)))
    raise SystemExit(0 if result and result.wasSuccessful() and guard.cleanup else 2)
