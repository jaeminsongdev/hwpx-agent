"""P209: 잠긴 READ handle을 빌려 두 실제 byte 읽기의 pathname 재열기를 제거.

원본 P206/P208과 실패 증거는 수정하지 않는다. 복제 handle의 파일 위치는
공유되므로 단일 owner의 직렬 stream만 허용하고 매 읽기 시작에 seek(0)한다.
검증 범위, 원 resource guard, pacing, stream identity 검사는 유지한다.
"""
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
import os
import threading
import locked_runtime_inputs as locks

SELF='tools/p09/borrowed_locked_streams.py'
TEST='tools/p09/tests/test_borrowed_locked_streams.py'


def require(ok,code):locks.require(ok,'P209_BORROW_'+code)


class NativeBorrow:
    def __init__(self,native):
        import msvcrt
        self.native=native;self.crt=msvcrt;self.k=native.k
        self.k.GetCurrentProcess.argtypes=[];self.k.GetCurrentProcess.restype=w.HANDLE
        self.k.DuplicateHandle.argtypes=[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD]
        self.k.DuplicateHandle.restype=w.BOOL
    def duplicate(self,source):
        duplicate=w.HANDLE();current=self.k.GetCurrentProcess()
        # SAME_ACCESS=2만 사용. CLOSE_SOURCE=1은 원본 잠금을 해제하므로 금지.
        require(bool(self.k.DuplicateHandle(current,source,current,ctypes.byref(duplicate),0,False,2)),
            'DUPLICATE_FAILED')
        return duplicate.value
    def descriptor(self,handle):
        fd=self.crt.open_osfhandle(handle,os.O_RDONLY|os.O_BINARY|os.O_NOINHERIT)
        require(type(fd) is int and fd>=0,'DESCRIPTOR_FAILED')
        return fd
    def stream(self,fd):
        require(not os.get_inheritable(fd),'NONINHERITABLE_DESCRIPTOR')
        return os.fdopen(fd,'rb')
    def close_handle(self,handle):return self.native.close(handle)
    def close_fd(self,fd):os.close(fd);return True
    def close_stream(self,stream):stream.close();return stream.closed


class Borrower:
    def __init__(self,held,api=None,identity=lambda:(os.getpid(),threading.get_ident())):
        require(held.acquired and not held.closed and not held.releasing,'LIVE_LOCKS')
        self.held=held;self.identity=identity;self.owner=identity()
        self.api=NativeBorrow(held.api) if api is None else api
        self.handles={str(path):handle for name,path,handle,directory in held.owned if not directory}
        self.loan=None;self.active_binding=False;self.binding_token=None
        self.opened=0;self.closed=0;self.resets=0;self.close_failures=0
    def owner_check(self):require(self.identity()==self.owner,'ORIGINAL_OWNER_PROCESS_THREAD')
    def check(self):
        self.owner_check();self.held.check()
        require(self.held.acquired and not self.held.closed and not self.held.releasing,'LIVE_LOCKS')
    def release(self):
        self.owner_check()
        if self.loan is None:return True
        stage,value=self.loan
        try:
            released=getattr(self.api,'close_'+stage)(value)
        except BaseException:
            released=False
        if released:self.loan=None;self.closed+=1
        else:self.close_failures+=1
        return bool(released)
    @contextmanager
    def open(self,path,mode):
        self.check();require(mode=='rb' and self.active_binding,'BOUND_READ_BINARY_ONLY')
        require(self.loan is None and self.close_failures==0,'ONE_SERIAL_STREAM_NO_FAILED_CLEANUP')
        require(str(path) in self.handles,'EXACT_HELD_REGULAR_PATH')
        handle=self.api.duplicate(self.handles[str(path)])
        self.loan=('handle',handle);self.opened+=1
        try:
            info=self.held.api.inspect(handle)
            require(info==self.held.files[str(path)] and info['inheritable'] is False,'SAME_NONINHERITABLE_FILE_IDENTITY')
            fd=self.api.descriptor(handle);self.loan=('fd',fd)
            stream=self.api.stream(fd);self.loan=('stream',stream)
            require(stream.seek(0)==0,'SHARED_OFFSET_RESET');self.resets+=1
            self.check()
            yield stream
        finally:require(self.release(),'DUPLICATE_CLEANUP_FAILED')
    @contextmanager
    def sources(self,reader):
        self.check();require(not self.active_binding and self.loan is None,'ONE_SERIAL_READER_BINDING')
        original=reader._source;had_instance='_source' in vars(reader);owner=self;token=object()
        class Source:
            def __init__(self,path):self.path=path
            def __str__(self):return str(self.path)
            def relative_to(self,root):return self.path.relative_to(root)
            def open(self,mode):
                require(owner.binding_token is token,'EXACT_LIVE_BINDING_TOKEN')
                return owner.open(self.path,mode)
        def source(name):
            # 원 reader의 link/path/metadata guard를 먼저 실행한다.
            path=original(name)
            return Source(path) if str(path) in self.handles else path
        reader._source=source;self.active_binding=True;self.binding_token=token
        try:yield
        finally:
            self.active_binding=False;self.binding_token=None
            if had_instance:reader._source=original
            else:del reader._source
    def summary(self):
        return dict(duplicate_handles_opened=self.opened,duplicate_handles_closed=self.closed,
            duplicate_handles_remaining=int(self.loan is not None),duplicate_close_failed_attempts=self.close_failures,
            shared_offset_resets=self.resets,active_borrow_binding=self.active_binding,
            byte_stream_pathname_reopens=0,original_held_handles_closed_by_borrower=False,
            input_scope_reduced=False,original_resource_guards_and_pacing_retained=True,
            measured_CPU_or_freeze_improvement_claimed=False)


class BorrowedInputLocks(locks.InputLocks):
    def __init__(self,*args,borrow_api=None,**kw):
        super().__init__(*args,**kw);self.borrow_api=borrow_api;self.borrower=None
    @contextmanager
    def reader_sources(self,reader):
        if self.borrower is None:self.borrower=Borrower(self,self.borrow_api)
        with self.borrower.sources(reader),super().reader_sources(reader):yield
    def close(self):
        # 중단 후에도 checkpoint에 의존하지 않고 모든 소유 handle 정리를 시도.
        loan_closed=True
        if self.borrower is not None:
            require(not self.borrower.active_binding,'BORROW_READER_STILL_BOUND')
            loan_closed=self.borrower.release()
        held_closed=super().close()
        return loan_closed and held_closed
    def summary(self):
        result=super().summary()
        result['borrowed_byte_streams']=self.borrower.summary() if self.borrower is not None else None
        if self.borrower is not None and (self.borrower.loan is not None or self.borrower.close_failures):
            result['input_lock_cleanup_confirmed']=False
        return result
