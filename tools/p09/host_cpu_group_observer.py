"""Legacy Process arrays: preserve every duplicate, report groups not fake PIDs.

No counter fallback or registry change. Stable complete PID sets are required
per group across samples. Duplicate-instance CPU cannot identify an individual
process: group identity/ambiguity is explicit. Call only inside owned Job.
"""
import ctypes
from ctypes import wintypes as w
import math
import os
import host_cpu_observer as old

PATHS=(r'\Process(*)\% Processor Time',r'\Process(*)\ID Process')


def require(ok,code):old.require(ok,'GROUP_'+code)


def decode(buffer,size,count):
    require(type(size) is int and 0<size<=old.MAX_BUFFER and size<=ctypes.sizeof(buffer),'ARRAY_SIZE')
    require(type(count) is int and 0<count<=old.MAX_ITEMS and count*ctypes.sizeof(old.Item)<=size,'ARRAY_COUNT')
    start=ctypes.addressof(buffer);end=start+size;names_start=start+count*ctypes.sizeof(old.Item)
    rows={};items=ctypes.cast(buffer,ctypes.POINTER(old.Item));unit=ctypes.sizeof(ctypes.c_wchar)
    for index in range(count):
        entry=items[index];ptr=entry.name
        require(ptr is not None and names_start<=ptr<end and (ptr-start)%unit==0,'NAME_POINTER')
        length=min(old.MAX_NAME,(end-ptr)//unit);require(length>0,'NAME_POINTER')
        chars=ctypes.wstring_at(ptr,length);nul=chars.find('\0');require(0<nul<old.MAX_NAME,'NAME_TERMINATION')
        name=chars[:nul].lower();valid=entry.value.CStatus in (0,1);value=entry.value.doubleValue if valid else None
        if valid:require(math.isfinite(value) and value>=0,'COUNTER_NUMBER')
        rows.setdefault(name,[]).append(value)
    return rows


def pid_sets(rows):
    result={}
    for name,values in rows.items():
        if name in ('idle','_total'):continue
        require(isinstance(values,list) and 0<len(values)<=old.MAX_ITEMS,'PID_GROUP')
        valid=[]
        for value in values:
            if value is None:continue
            require(type(value) is float and math.isfinite(value) and value.is_integer() and 1<=value<=0xffffffff,'PID_NUMBER')
            valid.append(int(value))
        require(len(valid)==len(set(valid)),'DUPLICATE_PID')
        result[name]=frozenset(valid) if len(valid)==len(values) else None
    known=[pid for pids in result.values() if pids is not None for pid in pids]
    require(len(known)==len(set(known)),'CROSS_GROUP_PID');return result


def select(cpu,pids,baseline,processors,owned=()):
    require(type(processors) is int and 1<=processors<=64,'PROCESSORS')
    require(all(type(pid) is int and 1<=pid<=0xffffffff for pid in owned),'OWNED_PID')
    current=pid_sets(pids);candidates=[];unavailable=unstable=stable=ambiguous=0
    total=sum(len(values) for values in cpu.values());require(0<total<=old.MAX_ITEMS,'ITEM_TOTAL')
    for name,values in cpu.items():
        if name in ('idle','_total'):continue
        require(isinstance(values,list) and 0<len(values)<=old.MAX_ITEMS,'CPU_GROUP')
        for value in values:
            if value is not None:require(type(value) is float and math.isfinite(value) and value>=0,'CPU_NUMBER')
        group=current.get(name)
        if group is None or any(value is None for value in values) or len(values)!=len(group):
            unavailable+=len(values);continue
        if baseline.get(name)!=group:unstable+=len(values);continue
        raw=math.fsum(values);require(math.isfinite(raw),'GROUP_SUM')
        stable+=len(values);duplicate=len(values)>1
        if duplicate:ambiguous+=len(values)
        candidates.append(dict(role=old.role(name),instance_count=len(values),
            pid=next(iter(group)) if not duplicate else None,
            identity_granularity='group' if duplicate else 'pid',
            owned_member_count=len(group.intersection(owned)),processor_time_raw_percent=raw,
            machine_cpu_percent=raw/processors))
    candidates.sort(key=lambda row:(-row['machine_cpu_percent'],row['role'],row['pid'] or 0))
    return dict(processor_count=processors,cpu_instance_count=total,
        pid_instance_count=sum(len(values) for values in pids.values()),stable_candidate_count=len(candidates),
        stable_instance_count=stable,unavailable_instances=unavailable,unstable_instances=unstable,
        ambiguous_instances=ambiguous,top=candidates[:old.TOP],causal_attribution=False,
        counterset='Process',duplicate_groups_explicit=True),current


class Observer(old.Observer):
    def __init__(self,processors,api=None):
        require(type(processors) is int and 1<=processors<=64,'PROCESSORS');require(os.name=='nt','WINDOWS_ONLY')
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
            require(old.status(self.api.PdhOpenQueryW(None,0,ctypes.byref(self.query)))==0 and self.query.value,'QUERY_OPEN')
            for path in PATHS:
                handle=w.HANDLE()
                require(old.status(self.api.PdhAddEnglishCounterW(self.query,path,0,ctypes.byref(handle)))==0 and handle.value,'COUNTER_ADD')
                self.handles.append(handle)
        except BaseException:self.close();raise

    def array(self,handle):
        size=w.DWORD();count=w.DWORD()
        require(old.status(self.api.PdhGetFormattedCounterArrayW(handle,old.FORMAT,ctypes.byref(size),ctypes.byref(count),None))==old.MORE_DATA,'ARRAY_SIZE_STATUS')
        require(0<size.value<=old.MAX_BUFFER and 0<count.value<=old.MAX_ITEMS,'ARRAY_BOUND')
        allocated=size.value;buffer=ctypes.create_string_buffer(allocated)
        require(old.status(self.api.PdhGetFormattedCounterArrayW(handle,old.FORMAT,ctypes.byref(size),ctypes.byref(count),buffer))==0,'ARRAY_READ_STATUS')
        require(size.value<=allocated,'ARRAY_GROWTH');return decode(buffer,size.value,count.value)

    def collect(self,owned=()):
        require(not self.closed and self.query.value,'QUERY_CLOSED')
        require(old.status(self.api.PdhCollectQueryData(self.query))==0,'COLLECT')
        pids=self.array(self.handles[1])
        if self.baseline is None:self.baseline=pid_sets(pids);return None
        cpu=self.array(self.handles[0]);row,self.baseline=select(cpu,pids,self.baseline,self.processors,owned);return row
