"""Parent-only scoped inheritance flags for exact live held source handles.

No CreateFile/DuplicateHandle/ReadFile/CloseHandle, worker launch, byte-read
delegation, READY or GO. The caller must restore flags before its original
held-identity checks resume. Child inheritance and two fresh child reads are
separate unqualified boundaries, not serialized-pin or cache credit.
"""
import ctypes
from ctypes import wintypes as w
import os
import threading

SELF='tools/p09/native011_worker_source_inheritance.py'
TEST='tools/p09/tests/test_native011_worker_source_inheritance.py'


def require(ok,code):
    if not ok:raise ValueError('WORKER_SOURCE_INHERITANCE_'+code)


class WindowsFlags:
    def __init__(self,native):
        self.k=native.k
        self.k.GetHandleInformation.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)]
        self.k.GetHandleInformation.restype=w.BOOL
        self.k.SetHandleInformation.argtypes=[w.HANDLE,w.DWORD,w.DWORD]
        self.k.SetHandleInformation.restype=w.BOOL
    def flags(self,handle):
        flags=w.DWORD()
        require(self.k.GetHandleInformation(handle,ctypes.byref(flags)),'GET_EXACT_HANDLE_FLAGS')
        return int(flags.value)
    def inheritable(self,handle,value):
        require(type(value) is bool,'EXACT_INHERITANCE_BOOLEAN')
        require(self.k.SetHandleInformation(handle,1,int(value)),'SET_INHERITANCE_BIT_ONLY')


class SourceInheritance:
    def __init__(self,frame,required,coverage,*,frame_type,api=None,
                 identity=lambda:(os.getpid(),threading.get_ident())):
        require(callable(identity),'EXPLICIT_OWNER_IDENTITY')
        self.frame=frame;self.identity=identity;self.owner=identity()
        self.proof=coverage.verify(frame,required,frame_type=frame_type,boundary='before')
        rows=[(name,handle) for name,path,handle,directory in frame.held.owned if not directory and name in required]
        selected=dict(rows)
        require(len(rows)==len(required) and set(selected)==set(required) and 0<len(selected)<=4096
            and all(type(handle) is int and handle>0 for handle in selected.values())
            and len(set(selected.values()))==len(selected),'EXACT_DISTINCT_LIVE_REGULAR_HANDLES')
        self.handles=tuple(selected.values());self.api=WindowsFlags(frame.held.api) if api is None else api
        self.original_flags={};self.state='NEW';self.failed=False;self.restore_errors=[]
        self.arm_attempts=0;self.armed_count=0;self.restored_count=0
    def check(self):
        require(self.identity()==self.owner,'SAME_OWNER_PROCESS_THREAD')
        self.frame.check()
        require(self.frame.state=='BEFORE_READ' and not self.frame.reading
            and self.frame.held.acquired and not self.frame.held.closed and not self.frame.held.releasing,
            'SAME_LIVE_FIRST_BOUNDARY_NO_ACTIVE_READ_OR_RELEASE')
    def arm(self):
        require(self.state=='NEW' and not self.failed and self.arm_attempts==0,'ONE_ARM_ATTEMPT_ONLY')
        self.arm_attempts=1;self.state='ARMING'
        try:
            self.check()
            # All snapshots precede ANY mutation. A partial API failure still
            # restores every selected handle, including the failing handle.
            for handle in self.handles:
                self.check();flags=self.api.flags(handle)
                require(type(flags) is int and flags>=0 and flags&1==0,'ORIGINAL_NONINHERITABLE_FLAGS')
                self.original_flags[handle]=flags
            for handle in self.handles:
                self.check();self.api.inheritable(handle,True)
                require(self.api.flags(handle)==self.original_flags[handle]|1,'ONLY_INHERITANCE_BIT_CHANGED')
                self.armed_count+=1
            self.state='ARMED';return self.handle_list()
        except BaseException:
            self.failed=True;self.restore();raise
    def handle_list(self):
        self.check();require(self.state=='ARMED' and not self.failed,'ONLY_LIVE_ARMED_EXPLICIT_LIST')
        require(all(self.api.flags(handle)==self.original_flags[handle]|1 for handle in self.handles),
            'EXACT_ARMED_FLAGS_NO_EXTERNAL_DRIFT')
        return self.handles
    def restore(self):
        # Cleanup deliberately does not call a stopped resource guard. It may
        # restore only this owner's exact saved flags; it cannot grant reuse.
        if self.identity()!=self.owner:
            self.failed=True;self.state='BROKEN';self.restore_errors=['FOREIGN_OWNER_CLEANUP_DENIED'];return False
        errors=[];restored=0
        for handle,original in self.original_flags.items():
            try:
                current=self.api.flags(handle)
                require(type(current) is int and current&~1==original&~1,'OTHER_FLAGS_NOT_SILENTLY_REWRITTEN')
                if current!=original:self.api.inheritable(handle,bool(original&1))
                require(self.api.flags(handle)==original,'ORIGINAL_FLAGS_FRESH_READBACK')
                restored+=1
            except (ValueError,OSError):errors.append('ORIGINAL_FLAG_RESTORE_UNCONFIRMED')
        self.restored_count=restored;self.restore_errors=errors
        if errors:self.failed=True
        self.state='BROKEN' if errors else 'RESTORED'
        return not errors
    def summary(self):
        return dict(parent_source_handles=len(self.handles),arm_attempts=self.arm_attempts,
            armed_handles=self.armed_count,restored_handles=self.restored_count,
            restore_confirmed=self.state=='RESTORED' and not self.restore_errors,
            failed=self.failed,state=self.state,parent_handles_closed_by_loan=0,
            new_pathname_opens=0,DuplicateHandle_calls=0,source_bytes_read_or_cached=0,
            original_Frame_methods_or_saved_OS_identities_mutated=False,
            explicit_child_STARTUPINFO_handle_list_still_required=True,
            actual_child_handle_inheritance_or_two_byte_reads_qualified=False,
            original_READY15_or_Native_or_product_qualified=False,GO_authorized=False)
