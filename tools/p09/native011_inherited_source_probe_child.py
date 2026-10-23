"""Read inherited source handles twice, no source reopen/worker/READY/GO.

Small mechanism probe only. A serialized handle or pin is insufficient: each
actual inherited disk handle must match the parent's OS identity and size.
"""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

SELF='tools/p09/native011_inherited_source_probe_child.py'
START=b'P09_SOURCE_HANDLE_PROBE_V1\n'
SCHEMA='hwpx-agent.p09-inherited-source-probe/v1'
CHUNK=65536
RATE=2*1048576


def require(ok,label):
    if not ok:raise ValueError('INHERITED_SOURCE_CHILD_'+label)


def rows_checked(rows):
    require(type(rows) is list and 0<len(rows)<=4096,'BOUNDED_EXPLICIT_SOURCE_LIST')
    names=set();handles=set();result=[]
    for row in rows:
        require(type(row) is dict and set(row)=={'handle','pin','identity'},'SOURCE_DESCRIPTOR_SHAPE')
        handle=row['handle'];pin=row['pin'];identity=row['identity']
        require(type(handle) is int and 0<handle<2**64 and handle not in handles,'DISTINCT_ACTUAL_HANDLE_INTEGER')
        require(type(pin) is dict and set(pin)=={'path','bytes','sha256'},'EXACT_SOURCE_PIN')
        name=pin['path']
        require(type(name) is str and name and not name.startswith('/') and name not in names
            and not any(c in name for c in '\\:*?<>|"') and not any(ord(c)<32 for c in name)
            and all(part not in ('','.','..') and not part.endswith((' ','.')) for part in name.split('/')),
            'DISTINCT_DIRECT_SOURCE_PATH')
        require(type(pin['bytes']) is int and 0<pin['bytes']<=16*1048576
            and type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}',pin['sha256']), 'BOUNDED_SOURCE_PIN_VALUES')
        require(type(identity) is list and len(identity)==2
            and type(identity[0]) is int and 0<=identity[0]<2**32
            and type(identity[1]) is int and 0<=identity[1]<2**64,'EXACT_OS_FILE_IDENTITY')
        names.add(name);handles.add(handle);result.append(dict(handle=handle,pin=dict(pin),identity=list(identity)))
    return result


class FileInfo(ctypes.Structure):
    _fields_=[('attributes',w.DWORD),('created',w.FILETIME),('accessed',w.FILETIME),('written',w.FILETIME),
        ('volume',w.DWORD),('size_high',w.DWORD),('size_low',w.DWORD),('links',w.DWORD),
        ('index_high',w.DWORD),('index_low',w.DWORD)]


class Kernel:
    def __init__(self):
        self.k=ctypes.WinDLL('kernel32',use_last_error=True)
        for name,args,result in (
            ('GetHandleInformation',[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
            ('GetFileType',[w.HANDLE],w.DWORD),('GetFileInformationByHandle',[w.HANDLE,ctypes.POINTER(FileInfo)],w.BOOL),
            ('SetHandleInformation',[w.HANDLE,w.DWORD,w.DWORD],w.BOOL),
            ('SetFilePointerEx',[w.HANDLE,ctypes.c_longlong,ctypes.POINTER(ctypes.c_longlong),w.DWORD],w.BOOL),
            ('ReadFile',[w.HANDLE,w.LPVOID,w.DWORD,ctypes.POINTER(w.DWORD),w.LPVOID],w.BOOL),
            ('CreateFileMappingW',[w.HANDLE,w.LPVOID,w.DWORD,w.DWORD,w.DWORD,w.LPCWSTR],w.HANDLE),
            ('MapViewOfFile',[w.HANDLE,w.DWORD,w.DWORD,w.DWORD,ctypes.c_size_t],w.LPVOID),
            ('UnmapViewOfFile',[w.LPCVOID],w.BOOL),
            ('GetCurrentProcess',[],w.HANDLE),
            ('DuplicateHandle',[w.HANDLE,w.HANDLE,w.HANDLE,ctypes.POINTER(w.HANDLE),w.DWORD,w.BOOL,w.DWORD],w.BOOL),
            ('CloseHandle',[w.HANDLE],w.BOOL)):
            fn=getattr(self.k,name);fn.argtypes=args;fn.restype=result
    def info(self,handle):
        flags=w.DWORD();value=FileInfo()
        require(self.k.GetFileType(handle)==1 and self.k.GetHandleInformation(handle,ctypes.byref(flags))
            and self.k.GetFileInformationByHandle(handle,ctypes.byref(value)),'ACTUAL_INHERITED_DISK_HANDLE')
        return dict(identity=[int(value.volume),(int(value.index_high)<<32)|int(value.index_low)],
            size=(int(value.size_high)<<32)|int(value.size_low),directory=bool(value.attributes&0x10),
            reparse=bool(value.attributes&0x400),inheritable=bool(flags.value&1))
    def clear_inheritance(self,handle):require(self.k.SetHandleInformation(handle,1,0),'CHILD_INHERITANCE_CLEAR')
    def reset(self,handle):
        offset=ctypes.c_longlong()
        require(self.k.SetFilePointerEx(handle,0,ctypes.byref(offset),0) and offset.value==0,'ACTUAL_OFFSET_ZERO')
    def readinto(self,handle,buffer):
        require(0<len(buffer)<=CHUNK,'BOUNDED_READ_WORKSPACE')
        window=(ctypes.c_ubyte*len(buffer)).from_buffer(buffer);count=w.DWORD()
        require(self.k.ReadFile(handle,window,len(buffer),ctypes.byref(count),None),'ACTUAL_FRESH_READFILE')
        return int(count.value)
    def close(self,handle):return bool(self.k.CloseHandle(handle))
    def flags(self,handle):
        flags=w.DWORD();require(self.k.GetHandleInformation(handle,ctypes.byref(flags)),'DESCRIPTOR_HANDLE_FLAGS')
        return int(flags.value)
    def create_descriptor(self,raw):
        handle=self.k.CreateFileMappingW(w.HANDLE(-1),None,4,0,len(raw),None)
        require(bool(handle),'ANONYMOUS_METADATA_MAPPING_CREATED')
        view=None;valid=False
        try:
            view=self.k.MapViewOfFile(handle,2,0,0,len(raw));require(bool(view),'METADATA_WRITER_VIEW')
            ctypes.memmove(view,raw,len(raw));valid=True
        finally:
            if view and not self.k.UnmapViewOfFile(view):
                self.k.CloseHandle(handle);raise ValueError('INHERITED_SOURCE_CHILD_METADATA_WRITER_UNMAP')
            if not valid:self.k.CloseHandle(handle)
        return int(handle)
    def duplicate_descriptor_reader(self,handle):
        current=self.k.GetCurrentProcess();reader=w.HANDLE()
        require(self.k.DuplicateHandle(current,handle,current,ctypes.byref(reader),4,True,0),
            'EXPLICIT_READ_ONLY_DUPLICATE_NOT_SAME_ACCESS')
        return int(reader.value)
    def deny_descriptor_write(self,handle,size):
        ctypes.set_last_error(0);view=self.k.MapViewOfFile(handle,2,0,0,size);code=ctypes.get_last_error()
        if view:
            require(self.k.UnmapViewOfFile(view),'UNEXPECTED_WRITER_VIEW_UNMAPPED')
            raise ValueError('INHERITED_SOURCE_CHILD_DESCRIPTOR_NOT_READ_ONLY')
        require(code==5,'DESCRIPTOR_WRITE_VIEW_ACCESS_DENIED')
    def read_descriptor(self,handle,size):
        view=self.k.MapViewOfFile(handle,4,0,0,size);require(bool(view),'METADATA_READ_ONLY_VIEW')
        try:return ctypes.string_at(view,size)
        finally:require(self.k.UnmapViewOfFile(view),'METADATA_READER_UNMAP')


def descriptor_arguments(args):
    require(type(args) is list and len(args)==4 and args[0]=='--source-mapped-probe',
        'CLOSED_MAPPED_DESCRIPTOR_ARGUMENTS')
    require(all(type(value) is str for value in args)
        and re.fullmatch('[1-9][0-9]{0,19}',args[1])
        and re.fullmatch('[1-9][0-9]{0,5}',args[2])
        and re.fullmatch('[0-9a-f]{64}',args[3]),'BOUNDED_DESCRIPTOR_ARGUMENT_VALUES')
    handle,size=int(args[1]),int(args[2])
    require(handle<2**64 and 0<size<=262144,'BOUNDED_DESCRIPTOR_HANDLE_AND_LENGTH')
    return handle,size,args[3]


class DescriptorMapping:
    """Bounded declarations only; never source bytes or qualified read credit."""
    def __init__(self,api,reserve):
        self.api=api;self.reserve=reserve;self.writer=None;self.reader=None
        self.prepared=False;self.failed=False;self.close_failures=0;self.reservations=0
        self.creation_calls=0;self.duplicate_calls=0
    def prepare(self,raw):
        require(not self.prepared and not self.failed and self.writer is None and self.reader is None,
            'ONE_DESCRIPTOR_PREPARATION')
        require(type(raw) is bytes and 0<len(raw)<=262144,'BOUNDED_METADATA_NOT_SOURCE_CONTENT')
        try:
            self.reserve();self.reservations+=1;self.creation_calls+=1;self.writer=self.api.create_descriptor(raw)
            self.reserve();self.reservations+=1;self.duplicate_calls+=1;self.reader=self.api.duplicate_descriptor_reader(self.writer)
            require(self.api.close(self.writer),'ORIGINAL_DESCRIPTOR_WRITER_CLOSED');self.writer=None
            self.api.deny_descriptor_write(self.reader,len(raw))
            require(self.api.flags(self.reader)==1,'ONLY_INHERITANCE_FLAG_FOR_METADATA')
            self.prepared=True;return self.reader
        except BaseException:self.failed=True;raise
    def close(self):
        for name in ('reader','writer'):
            handle=getattr(self,name)
            if handle is None:continue
            try:
                if name=='reader':self.api.clear_inheritance(handle)
            except (OSError,ValueError):self.failed=True;self.close_failures+=1
            try:ok=self.api.close(handle)
            except (OSError,ValueError):ok=False
            if ok:setattr(self,name,None)
            else:self.failed=True;self.close_failures+=1
        return self.writer is None and self.reader is None and self.close_failures==0
    def summary(self):
        return dict(metadata_only=True,maximum_bytes=262144,kernel_creation_reservations=self.reservations,
            CreateFileMapping_calls=self.creation_calls,DuplicateHandle_calls=self.duplicate_calls,
            source_byte_or_hash_cache=False,writer_remaining=self.writer is not None,
            reader_remaining=self.reader is not None,failed=self.failed,close_failures=self.close_failures)


def mapped_descriptor(api,args,checkpoint):
    handle,size,digest=descriptor_arguments(args);claimed=False;primary=None;raw=None
    try:
        checkpoint();require(api.flags(handle)==1,'REAL_INHERITED_METADATA_READER');claimed=True
        api.clear_inheritance(handle);require(api.flags(handle)==0,'METADATA_CHILD_FLAGS_CLEARED')
        api.deny_descriptor_write(handle,size);checkpoint();raw=api.read_descriptor(handle,size);checkpoint()
        require(type(raw) is bytes and len(raw)==size and hashlib.sha256(raw).hexdigest()==digest,
            'EXACT_DESCRIPTOR_LENGTH_AND_HASH_NOT_SOURCE_READ_CREDIT')
    except BaseException as error:primary=error
    finally:
        if claimed:
            try:closed=api.close(handle)
            except (OSError,ValueError):closed=False
            if not closed and primary is None:primary=ValueError('INHERITED_SOURCE_CHILD_METADATA_CHILD_CLOSE')
    if primary is not None:raise primary
    return raw


def bootstrap_capability(source,name,pace):
    """One fresh small bootstrap source, not a cache or serialized namespace."""
    rows=[row for row in source.rows if row['pin']['path']==name]
    require(len(rows)==1 and rows[0]['pin']['bytes']<=32768,'EXPLICIT_SMALL_CAPABILITY_SOURCE')
    row=rows[0];api=source.api;handle=row['handle'];source.check()
    require(api.info(handle)==source.expected(row,False),'CAPABILITY_BOOTSTRAP_OS_IDENTITY')
    api.reset(handle);raw=bytearray()
    while True:
        wanted=min(CHUNK,row['pin']['bytes']+1-len(raw));require(wanted>0,'CAPABILITY_SOURCE_SIZE_BOUND')
        pace(wanted);source.check();buffer=bytearray(wanted);source.read_attempts+=1
        count=api.readinto(handle,memoryview(buffer));source.physical_bytes+=count;source.check()
        require(type(count) is int and 0<=count<=wanted,'CAPABILITY_REAL_BYTE_COUNT')
        if not count:break
        raw.extend(memoryview(buffer)[:count])
    require(len(raw)==row['pin']['bytes'] and hashlib.sha256(raw).hexdigest()==row['pin']['sha256']
        and api.info(handle)==source.expected(row,False),'FRESH_CAPABILITY_BYTES_HASH_AND_OS_IDENTITY')
    env=dict(__name__='_p09_inherited_audit_capability',__file__=name)
    exec(compile(raw,name,'exec',dont_inherit=True),env)
    return env


def worker_ready_main():
    """Original worker/ReadyReader with real EOF, never a product GO writer."""
    import io
    from types import SimpleNamespace as NS
    args=sys.argv[1:]
    require(len(args)==5 and args[0]=='--worker-ready-probe'
        and re.fullmatch('[1-9][0-9]{0,19}',args[1]) and int(args[1])<2**64,
        'CLOSED_WORKER_READY_EOF_ONLY_INVOCATION')
    mapping_args=['--source-mapped-probe',*args[2:]]
    descriptor_arguments(mapping_args)
    source=cap=finder=q=None;denied=[];terminal=[];prepared=[];times={};project_opens=[]
    primary=None;clean=False;started=time.monotonic();root=Path(__file__).resolve().parents[2]
    def checkpoint():require(time.monotonic()-started<600,'ORIGINAL600_WORKER_PREPARATION')
    def deny_process(event,values):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('INHERITED_SOURCE_CHILD_PRODUCT_PROCESS_DENIED')
    sys.addaudithook(deny_process)
    row=dict(state='FAILED_ORIGINAL_WORKER_INHERITED_SOURCE_EOF_NOT_NATIVE',GO_authorized=False,
        actual_product_GO_received=False,accepted_count_delta=0,actual_product_processes=0)
    try:
        start=bytearray()
        while len(start)<len(START):
            value=os.read(sys.stdin.fileno(),1);require(bool(value),'REAL_PARENT_WORKER_START')
            start.extend(value)
        require(bytes(start)==START,'EXACT_PARENT_START_NOT_PRODUCT_GO')
        packet=json.loads(mapped_descriptor(Kernel(),mapping_args,checkpoint))
        require(type(packet) is dict and set(packet)=={'schema_version','parent_pid','sources'}
            and packet['schema_version']==SCHEMA and packet['parent_pid']==os.getppid()
            and type(packet['parent_pid']) is int,'EXACT_CURRENT_PARENT_SOURCE_DESCRIPTOR')
        pace=BytePacer(checkpoint);source=SourceReader(packet['sources'],Kernel(),checkpoint,pace.reserve)
        source.admit();times['actual_source_admission']=time.monotonic()-started
        capabilities=bootstrap_capability(source,'tools/p09/native011_inherited_audit_reader.py',pace.reserve)
        cap=capabilities['HeldSources'](source);finder=capabilities['SourceImports'](root,cap,pace.reserve)
        sys.meta_path.insert(0,finder)
        def audit_open(event,values):
            if event!='open' or not values or not isinstance(values[0],(str,bytes)):return
            path=Path(os.fsdecode(values[0])).absolute()
            if not path.is_relative_to(root):return
            name=path.relative_to(root).as_posix();mode=values[1] if len(values)>1 else None
            flags=values[2] if len(values)>2 else 0
            require(name in cap.rows and not(isinstance(mode,str) and any(v in mode for v in 'wax+'))
                and not(isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),
                'READONLY_DECLARED_PROJECT_PATH_OPEN_ONLY')
            cap.read_bytes(name,16*1048576,pace.reserve);project_opens.append(name)
        sys.addaudithook(audit_open)
        import accept_case112_current_epoch as a,conservative_maintenance as c
        import prepared_run_closure_v1 as host,current_stored_runtime_scope as scope
        import owned_source_read_pressure as pressure,audit_evidence_io as audit
        import native011_ready_worker as entry
        host.configure_host_policy(c);require(c.ROOT==root,'EXACT_ORIGINAL_REPOSITORY')
        Reader=capabilities['reader_type'](a.AcceptanceReader,audit,pressure,cap)
        q=Reader(root,checkpoint)
        for name in (entry.SELF,entry.LOADER['path'],SELF,'tools/p09/native011_inherited_audit_reader.py',
            'tools/p09/native011_worker_source_inheritance.py'):q.pin(name)
        import runtime_envelope_namespace_bundle_v1 as loader
        paths=('tools/p09/native011_preparation.py','tools/p09/native011_worker_transport.py',
            'tools/p09/native011_zlib_binding.py','tools/p09/native011_worker_preparation.py')
        pins=[q.pin(name) for name in paths]+[entry.ORIGINAL,entry.COMMON,entry.PROTOCOL,entry.PUBLISHER]
        allowed={pin['path']:pin for pin in pins}
        class Source:
            def __init__(self,name):self.name=name
            def __fspath__(self):return os.fspath(root/self.name)
            def open(self,mode):
                require(mode=='rb' and self.name in allowed,'EXACT_DECLARED_NAMESPACE_SOURCE')
                pin=allowed[self.name];before=q.maximum_parse_bytes
                try:
                    q.maximum_parse_bytes=min(before,pin['bytes']+1)
                    actual,raw=q._read(self.name,parse=True);q._bind(self.name,actual)
                finally:q.maximum_parse_bytes=before
                a.exact(actual,pin,'FRESH_WHOLE_NAMESPACE_BYTES');return io.BytesIO(raw)
        class Root:
            def __fspath__(self):return os.fspath(root)
            def __truediv__(self,name):return Source(name)
        libraries,_=loader.load(Root(),pins,{})
        worker=libraries.native011_worker_preparation;protocol=libraries.worker_readiness_v1
        api=libraries.batch_worker_launch.family(libraries.native009_worker_entry_v1,
            dict(__file__=str(root/SELF),SELF=SELF,TASK=entry.TASK,STEP=worker.STEP))
        def prepare(actual):
            require(actual==root and not prepared,'ONE_ORIGINAL_WORKER_CONSTRUCTION')
            prepared.append(None);times['constructor_start']=time.monotonic()-started
            result=worker.prepare(root,q,a,scope,pressure,loader)
            times['constructor_return']=time.monotonic()-started
            q.finish();checkpoint();require(q.final_fresh_hashes==len(q.snapshots)
                and set(q.snapshots)==set(cap.rows) and result.linked.state.calls==0,
                'WHOLE_DECLARED_CLOSING_BEFORE_REAL_READY')
            prepared[0]=result;times['closing_before_ready']=time.monotonic()-started
            return result.linked,protocol
        eof=entry.EOFOnly(sys.stdin)
        def measured(value,**options):
            require(not terminal and len(prepared)==1 and prepared[0] is not None,'ONE_ORIGINAL_TERMINAL')
            terminal.append(value);return json.dumps(value,**options)
        api.main.__globals__.update(prepare=prepare,json=NS(**{**vars(json),'dumps':measured}))
        original_argv=sys.argv;original_stdin=sys.stdin
        try:
            sys.argv=[str(root/SELF),'--ready-handle',args[1],'--task',entry.TASK];sys.stdin=eof
            exit_code=api.main()
        finally:sys.argv=original_argv;sys.stdin=original_stdin
        require(exit_code==1 and len(terminal)==1 and terminal[0]['terminal']=='WORKER_NOT_AUTHORIZED'
            and terminal[0]['actual_worker_attempts']==terminal[0]['actual_worker_calls']==1
            and terminal[0]['raw_policy_restored'] is True and eof.reads==1 and not denied,
            'ORIGINAL_WORKER_REAL_EOF_REJECTED_WITHOUT_PRODUCT')
        row.update(state='PASS_ORIGINAL_WORKER_INHERITED_SOURCE_REAL_EOF_NOT_NATIVE',terminal=terminal[0],
            actual_EOF_reads=eof.reads,preparation=prepared[0].proof,fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,source_pins=list(q.snapshots.values()),
            original_hash_parse_bind_finish_methods_retained=True,source_read_pathname_opens=q.open_pacer.opens,
            byte_rate_ceiling=pressure.OTHER_RATE,default_helper_count=q.worker_default_helper_count)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError,ImportError,RuntimeError) as error:
        value=error.args[0] if error.args else None
        primary=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_WORKER_READY_SOURCE_FAILURE'
        import traceback
        row['error_frames']=[dict(file=Path(frame.filename).name,function=frame.name,line=frame.lineno)
            for frame in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        if finder is not None:
            require(sys.meta_path and sys.meta_path[0] is finder,'RESTORE_EXACT_SCOPED_IMPORT_HOOK')
            sys.meta_path.pop(0)
        clean=source is not None and source.close()
        row.update(error_code=primary,cleanup_confirmed=clean,phase_times=times,process_creation_attempts=len(denied),
            pid=os.getpid(),parent_pid=os.getppid(),elapsed_seconds=time.monotonic()-started,
            source={} if source is None else source.summary(),capability={} if cap is None else cap.summary(),
            project_pathname_opens=project_opens,imported_fresh_source_count=0 if finder is None else len(finder.loaded),
            Native_Frame_or_product_or_GO_qualified=False)
        print(json.dumps(row),flush=True)
    return 0 if row['state'].startswith('PASS_') and clean else 2


class BytePacer:
    def __init__(self,checkpoint,*,clock=time.perf_counter,sleep=time.sleep):
        self.checkpoint=checkpoint;self.clock=clock;self.sleep=sleep;self.next=None;self.reserved_bytes=0
    def reserve(self,count):
        require(type(count) is int and 0<count<=CHUNK,'BOUNDED_BYTE_RESERVATION')
        self.checkpoint();now=self.clock();due=max(now,now if self.next is None else self.next)+count/RATE
        while True:
            self.checkpoint();remaining=due-self.clock()
            if remaining<=0:break
            self.sleep(min(.01,remaining))
        self.next=due;self.reserved_bytes+=count


class SourceReader:
    def __init__(self,rows,api,checkpoint,pace,*,identity=lambda:(os.getpid(),threading.get_ident())):
        self.rows=rows_checked(rows);self.api=api;self.checkpoint=checkpoint;self.pace=pace
        self.identity=identity;self.owner=identity();self.claimed=[];self.admitted=False;self.failed=False
        self.passes=[];self.read_attempts=0;self.physical_bytes=0;self.closed=0;self.close_failed=0;self.closing=False
    def check(self):
        require(self.identity()==self.owner and not self.failed,'SAME_LIVE_CHILD_OWNER_NOT_FAILED')
        self.checkpoint()
    def expected(self,row,inherited):
        return dict(identity=row['identity'],size=row['pin']['bytes'],directory=False,reparse=False,inheritable=inherited)
    def admit(self):
        require(not self.admitted and not self.claimed and not self.closing,'ONE_INHERITED_HANDLE_ADMISSION')
        try:
            for row in self.rows:
                self.check();require(self.api.info(row['handle'])==self.expected(row,True),'EXACT_INHERITED_OS_ID_NOT_PIN_ONLY')
                self.claimed.append(row['handle']);self.api.clear_inheritance(row['handle'])
                require(self.api.info(row['handle'])==self.expected(row,False),'CHILD_FLAGS_CLEARED_ONLY')
            self.admitted=True
        except BaseException:self.failed=True;raise
    def read_pass(self):
        require(self.admitted and not self.closing and len(self.passes)<2,'TWO_LIVE_FRESH_PASSES_ONLY')
        found=[]
        try:
            for row in self.rows:
                self.check();handle=row['handle'];pin=row['pin']
                require(self.api.info(handle)==self.expected(row,False),'FRESH_PRE_READ_OS_IDENTITY')
                self.api.reset(handle);digest=hashlib.sha256();total=0;workspace=bytearray(CHUNK)
                while True:
                    wanted=min(CHUNK,pin['bytes']+1-total);require(wanted>0,'SOURCE_SIZE_CEILING')
                    self.pace(wanted);self.check();self.read_attempts+=1
                    window=memoryview(workspace)[:wanted];count=self.api.readinto(handle,window);self.check()
                    require(type(count) is int and 0<=count<=wanted,'ACTUAL_BOUNDED_BYTE_COUNT')
                    self.physical_bytes+=count;total+=count
                    if not count:break
                    digest.update(window[:count])
                require(total==pin['bytes'] and digest.hexdigest()==pin['sha256'],'FRESH_ENTIRE_SOURCE_BYTES_AND_HASH')
                require(self.api.info(handle)==self.expected(row,False),'FRESH_POST_READ_OS_IDENTITY')
                found.append(dict(pin))
            self.passes.append(found);return found
        except BaseException:self.failed=True;raise
    def close(self):
        self.closing=True
        remaining=[]
        for handle in self.claimed:
            try:ok=self.api.close(handle)
            except OSError:ok=False
            if ok:self.closed+=1
            else:self.close_failed+=1;self.failed=True;remaining.append(handle)
        self.claimed=remaining;return not remaining and self.close_failed==0
    def summary(self):
        return dict(source_files=len(self.rows),actual_passes=len(self.passes),actual_byte_pins=self.passes,
            physical_bytes=self.physical_bytes,readinto_attempts=self.read_attempts,
            inherited_source_handles_closed=self.closed,inherited_source_handles_remaining=len(self.claimed),
            source_handle_close_failures=self.close_failed,new_source_pathname_opens=0,DuplicateHandle_calls=0,
            source_byte_or_hash_cache=False,actual_original_worker_READY15_or_Native_qualified=False,GO_authorized=False)


def main():
    args=sys.argv[1:];mapped=args!=['--source-probe']
    if mapped:descriptor_arguments(args)
    root=Path(__file__).resolve().parents[2];denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('INHERITED_SOURCE_CHILD_NO_PROCESS')
        if event=='open' and args and isinstance(args[0],(str,bytes)):
            path=Path(os.fsdecode(args[0])).absolute()
            if path.is_relative_to(root):
                denied.append('project_open');raise ValueError('INHERITED_SOURCE_CHILD_NO_PROJECT_PATH_OPEN')
    sys.addaudithook(deny)
    reader=None;primary=None;clean=False;started=time.monotonic();phase_times={}
    try:
        require(sys.stdin.buffer.readline(len(START)+1)==START,'REAL_PARENT_START_NOT_PRODUCT_GO')
        def checkpoint():require(time.monotonic()-started<10,'SOURCE_PROBE10_NOT_READY_GATE')
        if mapped:raw=mapped_descriptor(Kernel(),args,checkpoint)
        else:raw=sys.stdin.buffer.readline(262145)
        require(len(raw)<=262144 and raw.endswith(b'\n'),'BOUNDED_PARENT_DESCRIPTOR')
        packet=json.loads(raw)
        require(type(packet) is dict and set(packet)=={'schema_version','parent_pid','sources'}
            and packet['schema_version']==SCHEMA and type(packet['parent_pid']) is int
            and packet['parent_pid']==os.getppid(),'EXACT_CURRENT_PARENT_PROCESS')
        phase_times['parent_start_and_descriptor_seconds']=time.monotonic()-started
        pacer=BytePacer(checkpoint);reader=SourceReader(packet['sources'],Kernel(),checkpoint,pacer.reserve)
        reader.admit();phase_times['admission_seconds_from_start']=time.monotonic()-started
        reader.read_pass();phase_times['first_read_seconds_from_start']=time.monotonic()-started
        reader.read_pass();phase_times['second_read_seconds_from_start']=time.monotonic()-started
        require(not denied,'NO_CHILD_SOURCE_REOPEN_OR_PROCESS')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,MemoryError) as error:
        value=error.args[0] if error.args else None
        primary=value if type(value) is str and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_INHERITED_SOURCE_CHILD_FAILURE'
    finally:
        clean=reader is not None and reader.close()
        summary={} if reader is None else reader.summary()
        valid=primary is None and clean and summary.get('actual_passes')==2
        print(json.dumps(dict(state='PASS_INHERITED_SOURCE_TWO_FRESH_HASH_PASSES_NOT_READY_OR_NATIVE' if valid else
            'FAILED_INHERITED_SOURCE_PROBE_NOT_READY_OR_NATIVE',error_code=primary,cleanup_confirmed=clean,
            pid=os.getpid(),parent_pid=os.getppid(),source=summary,denied_operations=len(denied),
            descriptor_transport='inherited_read_only_mapping' if mapped else 'bounded_stdin',
            phase_times=phase_times,byte_pacer_clock='perf_counter',
            byte_pacer_clock_resolution=time.get_clock_info('perf_counter').resolution,
            byte_rate_ceiling=RATE,GO_authorized=False,accepted_count_delta=0)),flush=True)
    return 0 if valid else 2


if __name__=='__main__':
    raise SystemExit(worker_ready_main() if sys.argv[1:2]==['--worker-ready-probe'] else main())
