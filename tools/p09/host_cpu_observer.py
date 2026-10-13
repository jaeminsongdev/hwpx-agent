"""Bounded, redacted native PDH observations; call ONLY inside owned Job.

PDH provider calls may block: the external parent resource/timeout guard must
remain outside this collector. Counter snapshots identify candidates, not causes.
No command lines, paths, arbitrary process names, shell, WMI, threads or children.
"""
import ctypes
from ctypes import wintypes as w
import math
import os
import re

MAX_BUFFER=1024*1024
MAX_ITEMS=2048
MAX_NAME=256
TOP=8
MORE_DATA=0x800007D2
FORMAT=0x200|0x8000  # DOUBLE | NOCAP100: preserve multi-core values above100.
# Process legacy array returned duplicate names on this PC: never silently
# overwrite them. Windows11 Process V2 carries PID in the instance name.
# No legacy fallback/registry edit; unavailable V2 must fail closed.
PATHS=(r'\Process V2(*)\% Processor Time',r'\Process V2(*)\ID Process')
ROLES=frozenset({'defender','windows_compatibility','system','git','wsl','codex',
    'wmi','python','console','rustc','cargo','stored_test','other'})


def require(ok,code):
    if not ok:raise ValueError('P153_'+code)


def status(value):return int(value)&0xffffffff


class Number(ctypes.Union):
    _fields_=[('longValue',ctypes.c_int32),('doubleValue',ctypes.c_double),
        ('largeValue',ctypes.c_int64),('pointer',ctypes.c_void_p)]


class Value(ctypes.Structure):
    _anonymous_=('number',)
    _fields_=[('CStatus',w.DWORD),('number',Number)]


class Item(ctypes.Structure):
    _fields_=[('name',ctypes.c_void_p),('value',Value)]


def role(name):
    base=re.sub(r'#[0-9]+$','',name).lower()
    known={'msmpeng':'defender','compattelrunner':'windows_compatibility','system':'system',
        'git':'git','vmmemwsl':'wsl','vmmem':'wsl','chatgpt':'codex','codex':'codex',
        'wmiprvse':'wmi','python':'python','python3':'python','conhost':'console',
        'rustc':'rustc','cargo':'cargo'}
    if re.fullmatch(r'form_stored_provider-[a-z0-9-]{1,100}',base):return 'stored_test'
    return known.get(base,'other')


def decode(buffer,size,count):
    """Read every bounded item; never dereference an unvalidated name pointer."""
    require(type(size) is int and 0<size<=MAX_BUFFER and size<=ctypes.sizeof(buffer),'ARRAY_SIZE')
    require(type(count) is int and 0<count<=MAX_ITEMS and count*ctypes.sizeof(Item)<=size,'ARRAY_COUNT')
    start=ctypes.addressof(buffer);end=start+size;names_start=start+count*ctypes.sizeof(Item)
    rows={};items=ctypes.cast(buffer,ctypes.POINTER(Item))
    for i in range(count):
        entry=items[i];ptr=entry.name;unit=ctypes.sizeof(ctypes.c_wchar)
        require(ptr is not None and names_start<=ptr<end and (ptr-start)%unit==0,'NAME_POINTER')
        length=min(MAX_NAME,(end-ptr)//unit)
        require(length>0,'NAME_POINTER')
        # Fixed-length read is within buffer; no unbounded wstring_at.
        chars=ctypes.wstring_at(ptr,length);nul=chars.find('\0')
        require(0<nul<MAX_NAME,'NAME_TERMINATION');name=chars[:nul].lower()
        require(name not in rows,'DUPLICATE_INSTANCE')
        valid=entry.value.CStatus in (0,1)
        value=entry.value.doubleValue if valid else None
        if valid:require(math.isfinite(value) and value>=0,'COUNTER_NUMBER')
        rows[name]=value
    return rows


def pid_map(rows):
    out={}
    for name,value in rows.items():
        if name in ('idle','_total'):continue
        if value is None:out[name]=None;continue
        require(value.is_integer() and 1<=value<=0xffffffff,'PID_NUMBER');out[name]=int(value)
    return out


def select(cpu,pids,baseline,processors,owned=()):
    require(type(processors) is int and 1<=processors<=64,'PROCESSORS')
    require(all(type(pid) is int and 1<=pid<=0xffffffff for pid in owned),'OWNED_PID')
    current=pid_map(pids);candidates=[];unavailable=unstable=0;seen=set()
    for name,value in cpu.items():
        if name in ('idle','_total'):continue
        pid=current.get(name)
        if value is None or pid is None:unavailable+=1;continue
        require(isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value) and value>=0,'CPU_NUMBER')
        if baseline.get(name)!=pid:unstable+=1;continue
        require(pid not in seen,'DUPLICATE_PID');seen.add(pid)
        candidates.append(dict(pid=pid,role=role(name),owned=pid in owned,
            processor_time_raw_percent=value,machine_cpu_percent=value/processors))
    candidates.sort(key=lambda row:(-row['machine_cpu_percent'],row['pid']))
    return dict(processor_count=processors,cpu_instance_count=len(cpu),pid_instance_count=len(pids),
        stable_candidate_count=len(candidates),unavailable_instances=unavailable,
        unstable_instances=unstable,top=candidates[:TOP],causal_attribution=False),current


class Observer:
    def __init__(self,processors,api=None):
        require(type(processors) is int and 1<=processors<=64,'PROCESSORS')
        require(os.name=='nt','WINDOWS_ONLY')
        self.processors=processors;self.query=w.HANDLE();self.closed=False;self.baseline=None;self.handles=[]
        self.api=api or ctypes.WinDLL('pdh.dll',use_last_error=True)
        if api is None:
            for name,args in (
                ('PdhOpenQueryW',[w.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(w.HANDLE)]),
                ('PdhAddEnglishCounterW',[w.HANDLE,w.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(w.HANDLE)]),
                ('PdhCollectQueryData',[w.HANDLE]),
                ('PdhGetFormattedCounterArrayW',[w.HANDLE,w.DWORD,ctypes.POINTER(w.DWORD),ctypes.POINTER(w.DWORD),ctypes.c_void_p]),
                ('PdhCloseQuery',[w.HANDLE])):
                fn=getattr(self.api,name);fn.argtypes=args;fn.restype=ctypes.c_int32
        try:
            require(status(self.api.PdhOpenQueryW(None,0,ctypes.byref(self.query)))==0 and self.query.value,'QUERY_OPEN')
            for path in PATHS:
                handle=w.HANDLE()
                require(status(self.api.PdhAddEnglishCounterW(self.query,path,0,ctypes.byref(handle)))==0 and handle.value,'COUNTER_ADD')
                self.handles.append(handle)
        except BaseException:
            self.close();raise

    def array(self,handle):
        size=w.DWORD(0);count=w.DWORD(0)
        require(status(self.api.PdhGetFormattedCounterArrayW(handle,FORMAT,ctypes.byref(size),ctypes.byref(count),None))==MORE_DATA,'ARRAY_SIZE_STATUS')
        require(0<size.value<=MAX_BUFFER and 0<count.value<=MAX_ITEMS,'ARRAY_BOUND')
        allocated=size.value;buffer=ctypes.create_string_buffer(allocated)
        require(status(self.api.PdhGetFormattedCounterArrayW(handle,FORMAT,ctypes.byref(size),ctypes.byref(count),buffer))==0,'ARRAY_READ_STATUS')
        require(size.value<=allocated,'ARRAY_GROWTH');return decode(buffer,size.value,count.value)

    def collect(self,owned=()):
        require(not self.closed and self.query.value,'QUERY_CLOSED')
        require(status(self.api.PdhCollectQueryData(self.query))==0,'COLLECT')
        pids=self.array(self.handles[1])
        if self.baseline is None:
            self.baseline=pid_map(pids);return None
        cpu=self.array(self.handles[0]);result,self.baseline=select(cpu,pids,self.baseline,self.processors,owned)
        return result

    def close(self):
        if self.closed:return
        self.closed=True
        if self.query.value:
            result=status(self.api.PdhCloseQuery(self.query));self.query=w.HANDLE()
            require(result==0,'QUERY_CLOSE')
