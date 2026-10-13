"""Opt-in read-only views of held Native handles; NOT connected to runtime134.

No DuplicateHandle, CRT descriptor, pathname reopen, or content/hash/JSON cache.
Every actual read uses the existing held READ handle on its original owner thread.
The original source wrapper still verifies the same stream identity on each pass.
Views never own/close Native handles. All original physical-open and byte-rate
limits remain; only reservations for physically nonexistent duplicates disappear.
"""
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
from types import MappingProxyType, SimpleNamespace as NS

import retained_read_streams as original

SELF = "tools/p09/held_native_read_views_v1.py"
TEST = "tools/p09/tests/test_held_native_read_views_v1.py"
CHUNK_BYTES = 64 * 1024
LOCK_PIN = original.LOCK_PIN


def require(ok, code):
    if not ok:
        raise ValueError("HELD_READ_VIEW_" + code)


class NativeRead:
    """Synchronous READ/seek only. No allocating, duplicating, writing or closing."""
    def __init__(self, native):
        self.k = native.k
        self.k.ReadFile.argtypes = [w.HANDLE, w.LPVOID, w.DWORD,
                                   ctypes.POINTER(w.DWORD), w.LPVOID]
        self.k.ReadFile.restype = w.BOOL
        self.k.SetFilePointerEx.argtypes = [w.HANDLE, ctypes.c_longlong,
                                          ctypes.POINTER(ctypes.c_longlong), w.DWORD]
        self.k.SetFilePointerEx.restype = w.BOOL

    def reset(self, handle):
        result = ctypes.c_longlong()
        if not self.k.SetFilePointerEx(handle, 0, ctypes.byref(result), 0):
            raise ctypes.WinError(ctypes.get_last_error())
        return result.value

    def readinto(self, handle, buffer):
        # Caller owns this writable window until synchronous ReadFile returns.
        require(0 < len(buffer) <= CHUNK_BYTES, "NATIVE_CHUNK_BOUND")
        window = (ctypes.c_ubyte * len(buffer)).from_buffer(buffer)
        count = w.DWORD()
        if not self.k.ReadFile(handle, window, len(buffer), ctypes.byref(count), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(count.value)


class ReadView:
    """One non-owning serial lease. Closing it cannot release a held file lock."""
    def __init__(self, owner, path, handle):
        self.owner, self.path, self.handle = owner, path, handle
        self.closed = False

    def check(self):
        self.owner.check()
        require(not self.closed and self.owner.loan is self,
                "EXACT_LIVE_SERIAL_VIEW")
        require(self.owner.active_binding and self.owner.bound_reader is not None
                and id(self.owner.bound_reader) in self.owner.held.active_readers
                and getattr(self.owner.bound_reader, "_p206_input_lock_owner", None)
                is self.owner.held, "ORIGINAL_READER_BINDING_REQUIRED")
        require(self.owner.handles.get(str(self.path)) == self.handle,
                "EXACT_ORIGINAL_HELD_HANDLE")

    @property
    def native_handle(self):
        self.check()
        return self.handle

    def seek(self, offset, whence=0):
        self.check()
        require(type(offset) is int and offset == 0 and type(whence) is int
                and whence == 0, "ONLY_ORIGINAL_RESET_TO_ZERO")
        result = self.owner.api.reset(self.handle)
        require(type(result) is int and result == 0, "ORIGINAL_OFFSET_RESET")
        self.owner.resets += 1
        self.check()
        return 0

    def readinto(self, buffer):
        self.check()
        window = memoryview(buffer)
        require(not window.readonly and window.c_contiguous,
                "WRITABLE_CONTIGUOUS_WORKSPACE")
        window = window.cast("B")
        require(0 < len(window) <= CHUNK_BYTES, "BOUNDED_CHUNK_ONLY")
        self.owner.read_attempts += 1
        count = self.owner.api.readinto(self.handle, window)
        require(type(count) is int and 0 <= count <= len(window), "EXACT_READ_COUNT")
        self.owner.read_completed += 1
        self.owner.returned_bytes += count
        self.check()  # A protection stop cannot expose the completed bytes.
        return count

    def read(self, size):
        require(type(size) is int and 0 < size <= CHUNK_BYTES,
                "NO_UNBOUNDED_OR_OVERSIZED_READ")
        buffer = bytearray(size)
        count = self.readinto(buffer)
        return bytes(memoryview(buffer)[:count])

    def close(self):
        # No owner resource checkpoint and, crucially, no CloseHandle here.
        self.closed = True


class StreamIdentityRouter:
    """Delegate original Native API unchanged except trusted view handle extraction."""
    def __init__(self, native, held):
        self.original, self.held = native, held

    def __getattr__(self, name):
        return getattr(self.original, name)

    def stream_handle(self, stream):
        if type(stream) is ReadView:
            require(stream.owner.held is self.held
                    and self.held.borrower is stream.owner, "EXACT_STREAM_OWNER")
            return stream.native_handle
        return self.original.stream_handle(stream)


class ViewBorrower(original.b.Borrower):
    """Original owner/source binding, with zero physical duplicate handles."""
    def __init__(self, held, api=None, **kwargs):
        super().__init__(held, NativeRead(held.api) if api is None else api, **kwargs)
        self.handles = MappingProxyType(self.handles)
        self.authorized_path = None
        self.views_opened = self.views_closed = self.reservations = 0
        self.read_attempts = self.read_completed = self.returned_bytes = 0

    def reserve(self, reader, path):
        self.check()
        require(self.active_binding and self.bound_reader is reader
                and id(reader) in self.held.active_readers
                and getattr(reader, "_p206_input_lock_owner", None) is self.held,
                "EXACT_READER_RESERVATION")
        require(self.authorized_path is None and self.loan is None
                and self.close_failures == 0, "ONE_PENDING_SERIAL_VIEW")
        key = str(path)
        require(key in self.handles, "EXACT_HELD_REGULAR_PATH")
        # No new physical handle/open exists. Keep the ORIGINAL pressure callback
        # without changing its rate, clock, burst credit or sampler.
        self.held.api.pacer.checkpoint()
        self.reservations += 1
        self.authorized_path = key

    @contextmanager
    def open(self, path, mode):
        self.check()
        require(mode == "rb" and self.active_binding, "BOUND_READ_BINARY_ONLY")
        require(self.bound_reader is not None and id(self.bound_reader) in self.held.active_readers
                and getattr(self.bound_reader, "_p206_input_lock_owner", None) is self.held,
                "ORIGINAL_STREAM_WRAPPER_REQUIRED")
        require(self.loan is None and self.close_failures == 0, "ONE_SERIAL_VIEW_NO_FAILED_CLEANUP")
        key = str(path)
        require(key in self.handles and self.authorized_path == key,
                "EXACT_RESERVED_HELD_PATH")
        self.authorized_path = None
        stream = ReadView(self, path, self.handles[key])
        self.loan = stream
        self.views_opened += 1
        try:
            stream.seek(0)
            self.check()
            # The unchanged P206 wrapper verifies this SAME held handle before
            # yielding bytes. ReadView does not bypass that original predicate.
            yield stream
        finally:
            require(self.release(), "LOGICAL_VIEW_CLEANUP_FAILED")

    def release(self):
        self.owner_check()  # Cleanup deliberately does not sample/wait on CPU.
        self.authorized_path = None
        if self.loan is None:
            return True
        try:
            self.loan.close()
            released = self.loan.closed is True
        except BaseException:
            released = False
        if released:
            self.loan = None
            self.views_closed += 1
        else:
            self.close_failures += 1
        return released

    def summary(self):
        return dict(duplicate_handles_opened=0, duplicate_handles_closed=0,
                    duplicate_handles_remaining=0,
                    duplicate_close_failed_attempts=0,
                    CRT_descriptors_created=0, shared_offset_resets=self.resets,
                    active_borrow_binding=self.active_binding,
                    logical_views_opened=self.views_opened,
                    logical_views_closed=self.views_closed,
                    logical_views_remaining=int(self.loan is not None),
                    logical_view_close_failed_attempts=self.close_failures,
                    pending_view_reservation=self.authorized_path is not None,
                    existing_pressure_checkpoints=self.reservations,
                    direct_readinto_attempts=self.read_attempts,
                    direct_readinto_completed=self.read_completed,
                    direct_returned_bytes=self.returned_bytes,
                    byte_stream_pathname_reopens=0,
                    original_held_handles_closed_by_borrower=False,
                    original_pre_read_stream_identity_check_retained=True,
                    physical_open_pacer_not_mutated=True,
                    original_resource_and_byte_rate_guards_retained=True,
                    input_scope_reduced=False, file_byte_hash_or_JSON_cache=False,
                    product_or_Native_runtime_qualified=False,
                    measured_CPU_or_freeze_improvement_claimed=False)


def locks_type(base, reader_sources):
    class InputLocks(base):
        def __init__(self, *args, view_api=None, **kwargs):
            super().__init__(*args, **kwargs)
            self.view_api = view_api
            self.api = StreamIdentityRouter(self.api, self)

        @contextmanager
        def reader_sources(self, reader):
            if self.borrower is None:
                self.borrower = ViewBorrower(self, self.view_api)
            require(type(self.borrower) is ViewBorrower, "ONE_VIEW_OWNER")
            with self.borrower.sources(reader), reader_sources(self, reader):
                yield

        def summary(self):
            row = super().summary()
            row["held_native_read_views"] = self.borrower.summary() if self.borrower else None
            if self.borrower and (self.borrower.loan is not None or self.borrower.close_failures):
                row["input_lock_cleanup_confirmed"] = False
            return row

    return InputLocks


def load(reader, rate, c):
    # Preserve every acquisition/pressure/deadline/identity class in the original
    # bridge. Only byte-stream source/reservation routing differs.
    api = original.native.load(reader, rate, c)
    pin, raw = reader._read(LOCK_PIN["path"], parse=True)
    reader._bind(LOCK_PIN["path"], pin)
    require(pin == LOCK_PIN, "ORIGINAL_LOCK_PIN")
    projected, proof = original.reader_sources_projection(bytes(raw))
    return NS(**{**vars(api), "InputLocks": locks_type(api.InputLocks, projected),
                 "direct_view_binding_projection": proof})


def model(required, inventory_requests, *, PDH_seconds=2.05):
    import current_stored_runtime_scope as scope
    require(type(inventory_requests) is int and inventory_requests > 0, "INVENTORY_COUNT")
    require(type(PDH_seconds) in (int, float) and PDH_seconds == 2.05, "EXPLICIT_PDH_COST")
    result = scope.cost(required, 14)
    n = len(required)
    saved = 2 * n / 20
    # Physical-open ceilings and ALL actual byte costs/margins are unchanged.
    # No duplication/CRT stream exists on either pass, so no new-open cost exists.
    result.update(two_actual_byte_pass_native_reservations=0,
                  all_native_byte_open_pacing_seconds=0.0,
                  predicted_combined_seconds=result["predicted_combined_seconds"] - saved,
                  removed_first_duplicate_handle_reservations=n,
                  removed_first_duplicate_pacing_seconds=n / 20,
                  removed_second_duplicate_handle_reservations=n,
                  removed_second_duplicate_pacing_seconds=n / 20,
                  physical_byte_stream_duplicates_created=0,
                  actual_two_pass_byte_reads_retained=True,
                  byte_or_native_costs_assumed_overlapped=False,
                  parsed_JSON_hash_or_byte_cache=False)
    total = result["predicted_combined_seconds"] + 20 + 3 + inventory_requests / 20 + 11 + 5 + PDH_seconds
    result.update(predicted_runtime_combined_seconds=total,
                  nominal_fits_unchanged_deadline=total < 600,
                  product_allowance_seconds=20, pre_GO_and_assignment_allowance_seconds=3,
                  final_inventory_checkpoint_count=inventory_requests,
                  final_inventory_pacing_seconds=inventory_requests / 20,
                  additional_early_source_wait_allowance_seconds=11,
                  post_cleanup_identity_allowance_seconds=5,
                  additional_serial_PDH_maximum_sample_budget_seconds=PDH_seconds,
                  PDH_OS_call_latency_hard_preemption_guaranteed=False,
                  unknown_pressure_waits_included=False, actual_completion_guaranteed=False,
                  direct_view_connection_qualified=False, GO_authorized=False)
    require(total < 600, "WHOLE_CLOSURE_INSIDE_UNCHANGED600")
    return result
