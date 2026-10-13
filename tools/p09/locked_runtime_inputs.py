"""P206: 원본을 변경하지 않는 제한된 Windows 입력 handle 보유.

FILE_SHARE_READ만 허용해 일반 Windows API의 쓰기/삭제 접근을 차단한다.
source 범위를 제외하지 않으며 검증 byte 읽기는 호출자가 기존 reader로 수행한다.
이 helper 자체는 제품 검증·공유 frame 수용·보안 sandbox를 증명하지 않는다.
"""
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
import math
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
MAX_OPENS_PER_SECOND=32


def require(ok,code):
    if not ok:raise ValueError('P206_LOCK_'+code)


def input_pins(rows):
    require(isinstance(rows,dict) and 0<len(rows)<=MAX_INPUTS,'INPUT_COUNT')
    result={}
    for name,pin in rows.items():
        require(isinstance(name,str) and bool(name) and not name.startswith('/')
            and not any(ch in name for ch in '\\:*?<>|"') and not any(ord(ch)<32 for ch in name)
            and all(part not in ('','.', '..')
                and not part.endswith((' ','.')) for part in name.split('/')),'RELATIVE_INPUT_PATH')
        require(isinstance(pin,dict) and set(pin)=={'path','bytes','sha256'} and pin['path']==name
            and type(pin['bytes']) is int and 0<pin['bytes']<=512*1024*1024
            and isinstance(pin['sha256'],str) and re.fullmatch('[0-9a-f]{64}',pin['sha256']), 'INPUT_PIN')
        result[name]=dict(pin)
    return result


def open_budget(files,directories):
    require(type(files) is int and type(directories) is int and 1<=files<=MAX_INPUTS
        and directories>=1 and files+directories<=MAX_HANDLES,'OPEN_BUDGET_COUNTS')
    held=files+directories;byte_reads=2*files
    old=3*held+byte_reads;new=held+byte_reads
    return dict(input_files=files,ancestor_directories=directories,unchanged_byte_read_opens=byte_reads,
        before_source_scope_open_requests=old,optimized_source_scope_open_requests=new,
        redundant_pathname_open_requests_removed=old-new,
        modeled_open_request_reduction_percent=100*(old-new)/old,
        excludes_bootstrap_baseline_metadata_and_permission_probes=True,
        model_not_measured_CPU_RAM_or_wall_time_improvement=True)


class FileInfo(ctypes.Structure):
    _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),
        ('volume',w.DWORD),('size_high',w.DWORD),('size_low',w.DWORD),('links',w.DWORD),
        ('index_high',w.DWORD),('index_low',w.DWORD)]


class OpenPacer:
    """파일 open의 fan-out을 제한한다. idle 뒤에도 한 번 이상의 burst credit은 없다."""
    def __init__(self,checkpoint,rate=MAX_OPENS_PER_SECOND,clock=time.monotonic,sleeper=time.sleep):
        require(callable(checkpoint) and type(rate) is int and 1<=rate<=MAX_OPENS_PER_SECOND,'OPEN_RATE')
        self.checkpoint=checkpoint;self.rate=rate;self.clock=clock;self.sleeper=sleeper
        self.previous=None;self.opens=0;self.sleep_seconds=0.0
    def reserve(self):
        for attempt in range(64):
            self.checkpoint();now=self.clock()
            require(type(now) in (int,float) and math.isfinite(now)
                and (self.previous is None or now>=self.previous),'OPEN_CLOCK')
            delay=0 if self.previous is None else max(0.0,1/self.rate-(now-self.previous))
            if delay<=0:
                self.previous=now;self.opens+=1;return
            pause=min(0.05,delay);self.sleeper(pause);self.sleep_seconds+=pause
        require(False,'OPEN_CLOCK_NOT_ADVANCING')


class Native:
    def __init__(self,checkpoint=lambda:None):
        self.pacer=OpenPacer(checkpoint)
        self.probe_handles=set();self.probe_opened=0;self.probe_closed=0;self.probe_close_failures=0
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
        self.pacer.reserve()
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

    def stream_handle(self,stream):
        import msvcrt
        return msvcrt.get_osfhandle(stream.fileno())

    def access_probe(self,path,access):
        """기존 파일의 접근 권한 취득만 시도한다. 성공해도 내용·속성은 바꾸지 않는다."""
        handle,error=self.create(path,access,SHARE_ALL,OPEN_REPARSE)
        if handle in (None,self.invalid):return dict(opened=False,win32_error=error)
        self.probe_handles.add(handle);self.probe_opened+=1
        require(self.close_probe(handle),'PROBE_HANDLE_CLOSE')
        return dict(opened=True,win32_error=0)

    def close_probe(self,handle):
        # 권한 취득만 하는 probe도 소유 handle이다. close 실패 시 추적에서 지우지 않는다.
        try:released=self.close(handle)
        except Exception:released=False
        if released:self.probe_handles.remove(handle);self.probe_closed+=1
        else:self.probe_close_failures+=1
        return released

    def close_probes(self):
        for handle in tuple(self.probe_handles):self.close_probe(handle)
        return not self.probe_handles

    def probe_summary(self):
        return dict(probe_handles_opened=self.probe_opened,probe_handles_closed=self.probe_closed,
            probe_handles_remaining=len(self.probe_handles),probe_handle_close_failed_attempts=self.probe_close_failures)


class InputLocks:
    def __init__(self,root,checkpoint,api=None,maximum_seconds=MAX_SECONDS):
        require(Path(root).resolve()==ROOT and callable(checkpoint),'ROOT_CHECKPOINT')
        require(type(maximum_seconds) is int and 1<=maximum_seconds<=MAX_SECONDS,'DEADLINE')
        self.root=Path(root).resolve();self.checkpoint=checkpoint;self.api=Native(checkpoint) if api is None else api
        self.maximum_seconds=maximum_seconds;self.started=time.monotonic();self.owned=[];self.files={}
        self.acquired=False;self.closed=False;self.closed_handles=0;self.metadata_checks=0;self.opened_handles=0
        self.stream_identity_checks=0;self.stream_read_counts={}
        self.ancestor_walk_steps=0;self.close_failures=0;self.active_readers=set();self.active_streams=0;self.releasing=False

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
            self.check()
            path=self.root/name;current=path.parent
            # 이미 방문한 부모의 상위 경로도 등록되어 있다. 파일마다 같은 조상을 재순회하지 않는다.
            while current not in directories:
                require(current.is_relative_to(self.root) and current.parent!=current,'ANCESTOR_BOUNDARY')
                directories.add(current);self.ancestor_walk_steps+=1;current=current.parent
        require(len(directories)+len(inputs)<=MAX_HANDLES,'TOTAL_HANDLE_BOUND')
        try:
            for path in sorted(directories,key=lambda p:(len(p.parts),str(p))):
                info=self.take(path.relative_to(self.root).as_posix(),path,True)
                self.files[str(path)]=info
            for name,pin in inputs.items():self.files[str(self.root/name)]=self.take(name,self.root/name,False,pin)
            self.acquired=True;return self
        except BaseException:
            self.close();raise

    def acquisition_witness(self):
        require(self.acquired and not self.closed and not self.releasing,'HELD_FRAME_REQUIRED')
        return dict(held_identity_checks_complete=True,path_identities_confirmed_on_acquisition=True,
            regular_file_count=sum(not row[3] for row in self.owned),directory_count=sum(row[3] for row in self.owned))

    def verify_held_identities(self):
        require(self.acquired and not self.closed and not self.releasing,'HELD_FRAME_REQUIRED')
        for name,path,handle,directory in list(self.owned):
            self.check();info=self.api.inspect(handle);self.metadata_checks+=1
            require(info==self.files[str(path)],'HELD_IDENTITY_DRIFT')
        return dict(held_identity_checks_complete=True,separate_pathname_reopens=0,
            regular_file_count=sum(not row[3] for row in self.owned),directory_count=sum(row[3] for row in self.owned))

    def verify_stream(self,path,stream):
        self.check();require(self.acquired and not self.closed and not self.releasing,'HELD_FRAME_REQUIRED')
        expected=self.files.get(str(path))
        require(expected is not None and expected['directory'] is False,'LOCKED_REGULAR_STREAM_ONLY')
        # 이미 byte hash를 위해 열린 stream의 handle을 대조한다. pathname을 다시 열지 않는다.
        current=self.api.inspect(self.api.stream_handle(stream));self.metadata_checks+=1
        require(current==expected,'BYTE_STREAM_IDENTITY_DRIFT')
        name=path.relative_to(self.root).as_posix();self.stream_identity_checks+=1
        self.stream_read_counts[name]=self.stream_read_counts.get(name,0)+1

    @contextmanager
    def reader_sources(self,reader):
        require(self.acquired and not self.closed and not self.releasing,'HELD_FRAME_REQUIRED')
        require('_p206_input_lock_owner' not in vars(reader),'READER_ALREADY_BOUND')
        original=reader._source;had_instance_source='_source' in vars(reader)
        held=self
        class StreamSource:
            def __init__(self,path):self.path=path
            @contextmanager
            def open(self,mode):
                require(mode=='rb','READ_BINARY_ONLY')
                require(id(reader) in held.active_readers and getattr(reader,'_p206_input_lock_owner',None) is held,
                    'STREAM_READER_BINDING_REQUIRED')
                held.check()
                held.api.pacer.reserve()
                with self.path.open(mode) as stream:
                    held.verify_stream(self.path,stream)
                    held.active_streams+=1
                    try:yield stream
                    finally:held.active_streams-=1
        def source(name):
            path=original(name)
            return StreamSource(path) if str(path) in held.files and not held.files[str(path)]['directory'] else path
        reader._source=source;reader._p206_input_lock_owner=self;self.active_readers.add(id(reader))
        try:yield
        finally:
            try:
                if had_instance_source:reader._source=original
                else:del reader._source
            finally:
                del reader._p206_input_lock_owner
                self.active_readers.discard(id(reader))

    def verify_two_byte_passes(self,inputs):
        require(self.stream_read_counts=={name:2 for name in inputs},'TWO_ACTUAL_BYTE_STREAM_IDENTITY_PASSES')
        return dict(verified_byte_streams=self.stream_identity_checks,locked_inputs=len(inputs),
            each_input_hashed_twice_with_same_open_stream_identity=True,separate_pathname_reopens=0)

    def close(self):
        require(not self.active_readers and self.active_streams==0,'READER_STILL_BOUND')
        self.releasing=True
        retained=[]
        for row in reversed(self.owned):
            # 한 handle의 정리 오류 때문에 나머지 정리가 중단되어서는 안 된다.
            try:released=self.api.close(row[2])
            except Exception:released=False
            if released:self.closed_handles+=1
            else:retained.append(row);self.close_failures+=1
        self.owned=list(reversed(retained))
        probes_closed=self.api.close_probes() if hasattr(self.api,'close_probes') else True
        self.closed=not self.owned and probes_closed
        return self.closed

    def summary(self):
        out=dict(input_lock_handles_opened=self.opened_handles,input_lock_handles_closed=self.closed_handles,
            input_lock_handles_remaining=len(self.owned),input_lock_cleanup_confirmed=self.closed,
            handle_metadata_checks=self.metadata_checks,maximum_lock_seconds=self.maximum_seconds,
            ancestor_walk_steps=self.ancestor_walk_steps,handle_close_failed_attempts=self.close_failures,
            active_reader_bindings=len(self.active_readers),active_byte_streams=self.active_streams,release_started=self.releasing,
            byte_stream_identity_checks=self.stream_identity_checks,separate_pathname_reopens=0,
            file_write_or_delete_operation_executed=False,input_scope_reduced=False,
            kernel_or_malicious_bypass_protection_claimed=False)
        if hasattr(self.api,'pacer'):
            out['native_open_pacing']=dict(maximum_opens_per_second=self.api.pacer.rate,
                open_reservations=self.api.pacer.opens,requested_sleep_seconds=self.api.pacer.sleep_seconds,
                idle_time_cannot_accumulate_multiple_open_credits=True)
        if hasattr(self.api,'probe_summary'):out.update(self.api.probe_summary())
        return out
