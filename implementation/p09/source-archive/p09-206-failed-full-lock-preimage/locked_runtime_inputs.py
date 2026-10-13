"""P206: 원본을 변경하지 않는 제한된 Windows 입력 handle 보유.

FILE_SHARE_READ만 허용해 일반 Windows API의 쓰기/삭제 접근을 차단한다.
source 범위를 제외하지 않으며 검증 byte 읽기는 호출자가 기존 reader로 수행한다.
이 helper 자체는 제품 검증·공유 frame 수용·보안 sandbox를 증명하지 않는다.
"""
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import re
import time

ROOT=Path(__file__).resolve().parents[2]
SELF='tools/p09/locked_runtime_inputs.py'
TEST='tools/p09/tests/test_locked_runtime_inputs.py'
READ=0x80000000;WRITE=0x40000000;DELETE=0x00010000
SHARE_READ=1;SHARE_ALL=7;OPEN_EXISTING=3
OPEN_REPARSE=0x00200000;BACKUP_SEMANTICS=0x02000000
REPARSE=0x400;DIRECTORY=0x10;INHERIT=1
MAX_INPUTS=4096;MAX_HANDLES=8192;MAX_SECONDS=600


def require(ok,code):
    if not ok:raise ValueError('P206_LOCK_'+code)


def input_pins(rows):
    require(isinstance(rows,dict) and 0<len(rows)<=MAX_INPUTS,'INPUT_COUNT')
    result={}
    for name,pin in rows.items():
        require(isinstance(name,str) and bool(name) and not name.startswith('/')
            and not any(ch in name for ch in '\\:') and all(part not in ('','.', '..')
                and not part.endswith((' ','.')) for part in name.split('/')),'RELATIVE_INPUT_PATH')
        require(isinstance(pin,dict) and set(pin)=={'path','bytes','sha256'} and pin['path']==name
            and type(pin['bytes']) is int and 0<pin['bytes']<=512*1024*1024
            and isinstance(pin['sha256'],str) and re.fullmatch('[0-9a-f]{64}',pin['sha256']), 'INPUT_PIN')
        result[name]=dict(pin)
    return result


class FileInfo(ctypes.Structure):
    _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),
        ('volume',w.DWORD),('size_high',w.DWORD),('size_low',w.DWORD),('links',w.DWORD),
        ('index_high',w.DWORD),('index_low',w.DWORD)]


class Native:
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        for name,args,result in (
            ('CreateFileW',[w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE],w.HANDLE),
            ('GetFileInformationByHandle',[w.HANDLE,ctypes.POINTER(FileInfo)],w.BOOL),
            ('GetHandleInformation',[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
            ('GetFileType',[w.HANDLE],w.DWORD),('CloseHandle',[w.HANDLE],w.BOOL)):
            fn=getattr(self.k,name);fn.argtypes=args;fn.restype=result
        self.invalid=ctypes.c_void_p(-1).value

    def create(self,path,access,share,flags):
        # OPEN_EXISTING만 사용한다. 속성 설정·truncate·WriteFile·DeleteFile은 호출하지 않는다.
        ctypes.set_last_error(0)
        handle=self.k.CreateFileW('\\\\?\\'+str(path),access,share,None,OPEN_EXISTING,flags,None)
        return handle,ctypes.get_last_error()

    def open(self,path,directory):
        handle,error=self.create(path,0 if directory else READ,SHARE_READ,
            OPEN_REPARSE|(BACKUP_SEMANTICS if directory else 0))
        require(handle not in (None,self.invalid),'OPEN_SHARING_CONFLICT' if error==32 else 'OPEN_FAILED')
        return handle

    def inspect(self,handle):
        info=FileInfo();flags=w.DWORD()
        require(self.k.GetFileType(handle)==1 and self.k.GetFileInformationByHandle(handle,ctypes.byref(info))
            and self.k.GetHandleInformation(handle,ctypes.byref(flags)),'HANDLE_METADATA')
        return dict(identity=[int(info.volume),(int(info.index_high)<<32)|int(info.index_low)],
            size=(int(info.size_high)<<32)|int(info.size_low),directory=bool(info.attributes&DIRECTORY),
            reparse=bool(info.attributes&REPARSE),inheritable=bool(flags.value&INHERIT))

    def close(self,handle):return bool(self.k.CloseHandle(handle))

    def access_probe(self,path,access):
        """기존 파일의 접근 권한 취득만 시도한다. 성공해도 내용·속성은 바꾸지 않는다."""
        handle,error=self.create(path,access,SHARE_ALL,OPEN_REPARSE)
        if handle in (None,self.invalid):return dict(opened=False,win32_error=error)
        require(self.close(handle),'PROBE_HANDLE_CLOSE')
        return dict(opened=True,win32_error=0)


class InputLocks:
    def __init__(self,root,checkpoint,api=None,maximum_seconds=MAX_SECONDS):
        require(Path(root).resolve()==ROOT and callable(checkpoint),'ROOT_CHECKPOINT')
        require(type(maximum_seconds) is int and 1<=maximum_seconds<=MAX_SECONDS,'DEADLINE')
        self.root=Path(root).resolve();self.checkpoint=checkpoint;self.api=Native() if api is None else api
        self.maximum_seconds=maximum_seconds;self.started=time.monotonic();self.owned=[];self.files={}
        self.acquired=False;self.closed=False;self.closed_handles=0;self.metadata_checks=0;self.opened_handles=0

    def check(self):
        self.checkpoint();require(time.monotonic()-self.started<=self.maximum_seconds,'DEADLINE_EXCEEDED')

    def take(self,name,path,directory,pin=None):
        self.check();require(len(self.owned)<MAX_HANDLES,'HANDLE_COUNT')
        handle=self.api.open(path,directory);self.owned.append((name,path,handle,directory));self.opened_handles+=1
        info=self.api.inspect(handle);self.metadata_checks+=1
        require(info['directory'] is directory and info['reparse'] is False and info['inheritable'] is False,
            'DIRECT_NONINHERITABLE_HANDLE')
        if pin is not None:require(info['size']==pin['bytes'],'FILE_SIZE')
        return info

    def acquire(self,rows):
        require(not self.acquired and not self.closed and not self.owned,'ONE_ACQUISITION')
        inputs=input_pins(rows);directories={self.root}
        for name in inputs:
            path=self.root/name;current=path.parent
            while current!=self.root:
                require(current.is_relative_to(self.root) and current.parent!=current,'ANCESTOR_BOUNDARY')
                directories.add(current);current=current.parent
        require(len(directories)+len(inputs)<=MAX_HANDLES,'TOTAL_HANDLE_BOUND')
        try:
            for path in sorted(directories,key=lambda p:(len(p.parts),str(p))):
                info=self.take(path.relative_to(self.root).as_posix(),path,True)
                self.files[str(path)]=info
            for name,pin in inputs.items():self.files[str(self.root/name)]=self.take(name,self.root/name,False,pin)
            self.acquired=True;return self
        except BaseException:
            self.close();raise

    def verify_identities(self):
        require(self.acquired and not self.closed,'HELD_FRAME_REQUIRED')
        for name,path,handle,directory in list(self.owned):
            self.check();info=self.api.inspect(handle);self.metadata_checks+=1
            require(info==self.files[str(path)],'HELD_IDENTITY_DRIFT')
            # 현재 pathname도 같은 object를 가리키는지 확인한다. 새 handle은 즉시 닫는다.
            fresh=self.api.open(path,directory);self.opened_handles+=1
            try:
                current=self.api.inspect(fresh);self.metadata_checks+=1
                require(current==info,'CURRENT_PATH_IDENTITY_DRIFT')
            finally:
                closed=self.api.close(fresh)
                if closed:self.closed_handles+=1
                else:self.owned.append((name,path,fresh,directory))
                require(closed,'REOPEN_HANDLE_CLOSE')
        return dict(held_identity_checks_complete=True,pathname_identity_checks_complete=True,
            regular_file_count=sum(not row[3] for row in self.owned),directory_count=sum(row[3] for row in self.owned))

    def close(self):
        retained=[]
        for row in reversed(self.owned):
            if self.api.close(row[2]):self.closed_handles+=1
            else:retained.append(row)
        self.owned=list(reversed(retained));self.closed=not self.owned
        return self.closed

    def summary(self):
        return dict(input_lock_handles_opened=self.opened_handles,input_lock_handles_closed=self.closed_handles,
            input_lock_handles_remaining=len(self.owned),input_lock_cleanup_confirmed=self.closed,
            handle_metadata_checks=self.metadata_checks,maximum_lock_seconds=self.maximum_seconds,
            file_write_or_delete_operation_executed=False,input_scope_reduced=False,
            kernel_or_malicious_bypass_protection_claimed=False)
