"""Own-session read-only child cancellation event and additive resource bridge.

취소는 원래 stop latch에 추가할 뿐이다. 원래 sample/checkpoint/정리 정책을
우회하지 않으며 다른 작업, Docker daemon 또는 OS 설정을 변경하지 않는다.
"""
import ctypes
from ctypes import wintypes as w
import re
import uuid

import conservative_maintenance as c

PREFIX = "Local\\HwpxAgentP149SQLCancel-"
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0, WAIT_TIMEOUT = 0, 258
CANCEL_REASON = "STOP_ACCOUNTED_SQL_PARENT_CANCELLED"
OBSERVATION_FAILURE = "STOP_ACCOUNTED_SQL_CANCEL_OBSERVATION_FAILED"


def event_name(name):
    c.require(isinstance(name, str) and name.startswith(PREFIX), "SQL_CANCEL_NAME_SCOPE")
    suffix = name[len(PREFIX):]
    c.require(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", suffix),
        "SQL_CANCEL_NAME_SCOPE")
    return name


def kernel():
    dll = ctypes.WinDLL("kernel32", use_last_error=True)
    definitions = {"CreateEventW": ([ctypes.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR], w.HANDLE),
        "OpenEventW": ([w.DWORD, w.BOOL, w.LPCWSTR], w.HANDLE),
        "SetEvent": ([w.HANDLE], w.BOOL), "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
        "CloseHandle": ([w.HANDLE], w.BOOL)}
    for name, (arguments, returned) in definitions.items():
        function = getattr(dll, name)
        function.argtypes, function.restype = arguments, returned
    return dll


class CancelEvent:
    def __init__(self, name, *, create, native=None):
        self.name, self.owner = event_name(name), create
        c.require(type(create) is bool, "SQL_CANCEL_OWNER_TYPE")
        self.native = kernel() if native is None else native
        self.handle, self.closed = None, False
        try:
            if create:
                ctypes.set_last_error(0)
                self.handle = self.native.CreateEventW(None, True, False, self.name)
                duplicate = ctypes.get_last_error() == 183
                c.require(self.handle, "SQL_CANCEL_CREATE_FAILED")
                c.require(not duplicate, "SQL_CANCEL_ALREADY_EXISTS")
            else:
                self.handle = self.native.OpenEventW(SYNCHRONIZE, False, self.name)
                c.require(self.handle, "SQL_CANCEL_OPEN_FAILED")
        except (ValueError, OSError):
            if self.handle:
                self.close()
            raise

    @classmethod
    def create(cls, *, native=None):
        return cls(PREFIX+str(uuid.uuid4()), create=True, native=native)

    @classmethod
    def open(cls, name, *, native=None):
        return cls(name, create=False, native=native)

    def request(self):
        c.require(self.owner and not self.closed and self.handle, "SQL_CANCEL_SIGNAL_NOT_OWNED")
        c.require(self.native.SetEvent(self.handle), "SQL_CANCEL_SIGNAL_FAILED")

    def is_set(self):
        c.require(not self.closed and self.handle, "SQL_CANCEL_HANDLE_CLOSED")
        result = self.native.WaitForSingleObject(self.handle, 0)
        c.require(result in (WAIT_OBJECT_0, WAIT_TIMEOUT), "SQL_CANCEL_WAIT_FAILED")
        return result == WAIT_OBJECT_0

    def close(self):
        if self.closed:
            return
        c.require(self.handle and self.native.CloseHandle(self.handle), "SQL_CANCEL_CLOSE_FAILED")
        self.closed, self.handle = True, None


def cancellable_resource_type(original, cancel):
    class CooperativeResources(original):
        def _parent_cancel_checkpoint(self):
            try:
                requested = cancel.is_set()
                c.require(type(requested) is bool, "SQL_CANCEL_OBSERVATION_TYPE")
            except (ValueError, OSError):
                self._failed(OBSERVATION_FAILURE)
                raise ValueError(self.reason) from None
            if requested:
                self._failed(CANCEL_REASON)

        def sample(self, *args, **kwargs):
            row = super().sample(*args, **kwargs)
            self._parent_cancel_checkpoint()
            return row

        def checkpoint_io(self):
            self._parent_cancel_checkpoint()
            return super().checkpoint_io()
    return CooperativeResources
