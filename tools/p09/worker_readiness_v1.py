"""Uninstalled candidate: bounded readiness before the original GO write.

The child signals at its real stdin.readline boundary, never synthesizes GO.
Parent must verify the same live owned Job member before and after readiness.
Wrap OUTSIDE the original strict-window Input so its unchanged clock starts
only at the actual original write. No product, source or policy installation.
"""
import ctypes
from ctypes import wintypes as w
import math
import time

SELF="tools/p09/worker_readiness_v1.py"
TEST="tools/p09/tests/test_worker_readiness_v1.py"
GO=b"P149_GO\n"
SECONDS=15


def require(ok,label):
    if not ok:raise ValueError("WORKER_READINESS_"+label)


class WindowsEvent:
    """One unnamed handle explicitly inherited by only the intended worker."""
    def __init__(self,handle=None):
        self.k=ctypes.WinDLL("kernel32",use_last_error=True)
        for name,args,result in (
            ("CreateEventW",[ctypes.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR],w.HANDLE),
            ("GetHandleInformation",[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
            ("SetHandleInformation",[w.HANDLE,w.DWORD,w.DWORD],w.BOOL),
            ("SetEvent",[w.HANDLE],w.BOOL),
            ("WaitForSingleObject",[w.HANDLE,w.DWORD],w.DWORD),
            ("CloseHandle",[w.HANDLE],w.BOOL)):
            fn=getattr(self.k,name);fn.argtypes=args;fn.restype=result
        self.handle=None;self.child=handle is not None
        if handle is None:
            self.handle=self.k.CreateEventW(None,True,False,None)
            require(bool(self.handle),"EVENT_CREATE")
        else:
            require(type(handle) is int and handle>0,"INHERITED_HANDLE_INTEGER")
            flags=w.DWORD()
            require(self.k.GetHandleInformation(handle,ctypes.byref(flags)) and flags.value&1,"INHERITED_EVENT_HANDLE")
            self.handle=handle
            try:self.inheritable(False)
            except BaseException:self.close();raise
    def inheritable(self,value):
        require(type(value) is bool and self.handle is not None,"OPEN_EVENT_INHERITANCE")
        require(self.k.SetHandleInformation(self.handle,1,int(value)),"SET_EVENT_INHERITANCE")
    def wait(self,milliseconds):
        require(not self.child and self.handle is not None and type(milliseconds) is int and 1<=milliseconds<=50,"BOUNDED_PARENT_WAIT")
        code=self.k.WaitForSingleObject(self.handle,milliseconds)
        require(code in (0,258),"EVENT_WAIT_FAILED")
        return code==0
    def signal_and_close(self):
        require(self.child and self.handle is not None,"ONE_CHILD_SIGNAL")
        try:require(self.k.SetEvent(self.handle),"EVENT_SIGNAL")
        finally:self.close()
    def close(self):
        if self.handle is not None:
            handle=self.handle;self.handle=None
            require(self.k.CloseHandle(handle),"EVENT_CLOSE")


class ReadyReader:
    """Private stdin dependency, exactly one original read and exact result."""
    def __init__(self,original,event):
        require(callable(getattr(original,"readline",None)) and callable(getattr(event,"signal_and_close",None)),"ORIGINAL_READER_AND_EVENT")
        self.original=original;self.event=event;self.used=False
    def __getattr__(self,name):return getattr(self.original,name)
    def readline(self,*args,**kwargs):
        require(not self.used,"ONE_ORIGINAL_READ")
        self.used=True;self.event.signal_and_close()
        return self.original.readline(*args,**kwargs)


class Gate:
    """Wrap the already-windowed stdin after Job assignment, never raw Popen.

    Caller owns event, process, original capture and original Job cleanup.
    Readiness failure never grants another write or disables cleanup.
    """
    def __init__(self,original,event,process,verify_owned,checkpoint,*,clock=time.monotonic,seconds=SECONDS):
        require(all(callable(v) for v in (verify_owned,checkpoint,clock)),"EXPLICIT_OWNERSHIP_GUARD_CLOCK")
        require(type(seconds) in (int,float) and math.isfinite(seconds) and 0<seconds<=SECONDS,"BOUNDED_READINESS_SECONDS")
        require(callable(getattr(event,"wait",None)) and callable(getattr(original,"write",None)),"EVENT_AND_ORIGINAL_INPUT")
        require(type(getattr(process,"pid",None)) is int and process.pid>0 and callable(getattr(process,"poll",None)),"ACTUAL_PROCESS_REQUIRED")
        self.original=original;self.event=event;self.process=process
        self.verify_owned=verify_owned;self.checkpoint=checkpoint;self.clock=clock;self.seconds=seconds
        self.last=None;self.attempted=False;self.ready=False;self.written=False;self.stopped=False
        self.elapsed=None;self.waits=0
    def __getattr__(self,name):return getattr(self.original,name)
    def now(self):
        value=self.clock()
        require(type(value) in (int,float) and math.isfinite(value) and (self.last is None or value>=self.last),"MONOTONIC_CLOCK")
        self.last=value;return value
    def owned(self):
        require(self.process.poll() is None and self.verify_owned(self.process) is True,"SAME_LIVE_OWNED_JOB_MEMBER")
    def write(self,value):
        require(not self.attempted and not self.stopped,"ONE_GO_ATTEMPT_NOT_STOPPED")
        self.attempted=True
        try:
            require(type(value) is bytes and value==GO,"EXACT_ORIGINAL_GO_BYTES")
            started=self.now();self.owned()
            while True:
                self.checkpoint();remaining=self.seconds-(self.now()-started)
                require(remaining>0,"PREPARATION_TIMEOUT")
                self.owned();ready=self.event.wait(max(1,min(50,int(remaining*1000))))
                self.waits+=1
                require(type(ready) is bool,"EXACT_EVENT_RESULT")
                self.elapsed=self.now()-started
                require(self.elapsed<self.seconds,"PREPARATION_TIMEOUT")
                if ready:
                    self.checkpoint();self.owned();self.elapsed=self.now()-started
                    require(self.elapsed<self.seconds,"PREPARATION_TIMEOUT")
                    self.ready=True;break
            count=self.original.write(value)
            require(type(count) is int and count==len(GO),"COMPLETE_ORIGINAL_GO_WRITE")
            self.written=True;return count
        except BaseException:
            self.stopped=True;raise
    def flush(self):
        require(self.written and not self.stopped,"WRITTEN_GO_REQUIRED")
        try:return self.original.flush()
        except BaseException:self.stopped=True;raise
    def close(self):return self.original.close()
    def diagnostics(self):
        return dict(readiness_limit_seconds=self.seconds,readiness_elapsed_seconds=self.elapsed,
            bounded_event_waits=self.waits,readiness_confirmed=self.ready,actual_original_GO_written=self.written,
            stopped=self.stopped,product_window_changed=False,source_or_Job_checks_replaced=False,
            owned_cleanup_is_callers_responsibility=True,installed_in_Native=False)
