"""Borrow inherited OS streams; retain the complete original audit algorithms.

No source/hash cache or pathname fallback. Scope, parent locks and same-Job
admission are the caller's duty. This is not a Native or GO qualification.
"""
import hashlib
import importlib.abc
import importlib.util
from pathlib import Path
import time

SELF='tools/p09/native011_inherited_audit_reader.py'
CHUNK=65536


def require(ok,label):
    if not ok:raise ValueError('INHERITED_AUDIT_'+label)


class HeldSources:
    def __init__(self,source_reader):
        require(source_reader.admitted and not source_reader.failed and not source_reader.closing,
            'ACTUAL_ADMITTED_SOURCE_READER')
        source_reader.check();self.source=source_reader;self.busy=None
        self.rows={row['pin']['path']:row for row in source_reader.rows}
        require(len(self.rows)==len(source_reader.rows),'ONE_DECLARED_ROW_PER_NAME')
        self.completed={};self.actual_bytes=0;self.actual_reads=0
    def check(self):self.source.check()
    def stream(self,name):
        self.check();require(type(name) is str and name in self.rows,'NO_PATHNAME_FALLBACK')
        return Stream(self,name)
    def read_bytes(self,name,maximum,pace):
        require(type(maximum) is int and 0<maximum<=16*1048576,'BOUNDED_SOURCE_ALLOCATION')
        require(name in self.rows and self.rows[name]['pin']['bytes']<=maximum,'SOURCE_WITHIN_PARSE_BUDGET')
        raw=bytearray()
        with self.stream(name) as stream:
            while True:
                wanted=min(CHUNK,self.rows[name]['pin']['bytes']+1-len(raw))
                require(wanted>0,'SOURCE_SIZE_BOUND');pace(wanted);chunk=stream.read(wanted)
                if not chunk:break
                raw.extend(chunk);require(len(raw)<=maximum,'ORIGINAL_PARSE_LIMIT')
        return bytes(raw)
    def summary(self):
        return dict(actual_streams=sum(self.completed.values()),actual_source_bytes=self.actual_bytes,
            actual_ReadFile_calls=self.actual_reads,completed_reads_by_name=dict(self.completed),
            live_stream=self.busy is not None,new_source_pathname_opens=0,
            source_byte_hash_or_AST_cache=False,Native_or_GO_qualified=False)


class Stream:
    def __init__(self,owner,name):
        self.owner=owner;self.name=name;self.row=owner.rows[name];self.used=False;self.closed=False
        self.total=0;self.digest=hashlib.sha256();self.eof=False
    def open(self,mode):
        require(mode=='rb','READONLY_BINARY_STREAM');return self
    def __enter__(self):
        cap=self.owner;source=cap.source
        require(not self.used and not self.closed and cap.busy is None,'ONE_SAME_OWNER_STREAM')
        cap.check()
        try:
            require(source.api.info(self.row['handle'])==source.expected(self.row,False),'LIVE_PRE_READ_OS_IDENTITY')
            source.api.reset(self.row['handle']);self.used=True;cap.busy=self;return self
        except BaseException:source.failed=True;raise
    def read(self,count):
        cap=self.owner;source=cap.source
        try:
            cap.check();require(self.used and not self.closed and cap.busy is self and not self.eof,
                'SINGLE_LIVE_STREAM_NOT_REENTERED')
            require(type(count) is int and 0<count<=CHUNK,'BOUNDED_RAW_READ')
            workspace=bytearray(count);source.read_attempts+=1;cap.actual_reads+=1
            found=source.api.readinto(self.row['handle'],memoryview(workspace));cap.check()
            require(type(found) is int and 0<=found<=count,'ACTUAL_BOUNDED_READ_COUNT')
            self.total+=found;source.physical_bytes+=found;cap.actual_bytes+=found
            require(self.total<=self.row['pin']['bytes'],'NO_APPEND_OR_OVERFLOW')
            raw=bytes(memoryview(workspace)[:found]);self.digest.update(raw);self.eof=found==0;return raw
        except BaseException:source.failed=True;raise
    def __exit__(self,kind,error,tb):
        cap=self.owner;source=cap.source;self.closed=True
        try:
            require(cap.busy is self,'EXACT_STREAM_RELEASE')
            if kind is not None:source.failed=True;return False
            cap.check();require(self.eof and self.total==self.row['pin']['bytes']
                and self.digest.hexdigest()==self.row['pin']['sha256'],'FRESH_ENTIRE_BYTES_AND_REAL_EOF')
            require(source.api.info(self.row['handle'])==source.expected(self.row,False),'LIVE_POST_READ_OS_IDENTITY')
            cap.completed[self.name]=cap.completed.get(self.name,0)+1
        except BaseException:source.failed=True;raise
        finally:cap.busy=None
        return False


def reader_type(base,audit,pressure,cap):
    """Exact original _read/bind/pin/parse/finish, different scoped IO source.

    The open20 reservation is not charged for an OS handle already inherited.
    Each original byte reservation/refund, hash, parse bound and closing read
    remains in the unchanged original method; the byte pacer uses precise time.
    """
    require(issubclass(base,audit.AuditEvidenceReader),'ORIGINAL_AUDIT_READER_BASE')
    original=audit.AuditEvidenceReader._read
    class Reader(base):
        def __init__(self,root,checkpoint):
            super().__init__(root,checkpoint)
            self.pacer=pressure.OwnedPacer(clock=time.perf_counter)
        def _source(self,name):return cap.stream(name)
        def _read(self,name,parse=False):
            self.pacer.select(name)
            return original(self,name,parse=parse)
    require(all(getattr(Reader,name) is getattr(base,name) for name in
        ('_bind','pin','json','text','fresh_pin','finish')),'COMPLETE_ORIGINAL_BIND_PARSE_AND_CLOSING_METHODS')
    return Reader


class SourceImports(importlib.abc.MetaPathFinder,importlib.abc.Loader):
    """Normal Python modules from fresh declared handles, never pyc or hiding."""
    def __init__(self,root,cap,pace):
        self.root=Path(root);self.cap=cap;self.pace=pace;self.loaded=[]
        self.names={name[len('tools/p09/'):-3]:name for name in cap.rows
            if name.startswith('tools/p09/') and name.endswith('.py') and '/' not in name[len('tools/p09/'): ]}
    def find_spec(self,fullname,path=None,target=None):
        if fullname not in self.names:return None
        require(path is None and target is None,'NO_PACKAGE_OR_RELOAD_ALIAS')
        spec=importlib.util.spec_from_loader(fullname,self,origin=str(self.root/self.names[fullname]))
        spec.has_location=True;return spec
    def create_module(self,spec):return None
    def exec_module(self,module):
        name=self.names[module.__name__];raw=self.cap.read_bytes(name,16*1048576,self.pace)
        self.loaded.append(name)
        exec(compile(raw,str(self.root/name),'exec',dont_inherit=True),module.__dict__)
