"""P208: 실제 전후 전체 읽기를 보존하는 단일 사례의 소유 입력 frame.

등록/수명은 이 프로세스의 단일 owner thread에 한정한다. 직렬화된 pin이나
이전 frame 결과로 살아 있는 handle을 대신하지 않는다. 보안 sandbox가 아니다.
"""
import os
import copy
import threading
from types import MappingProxyType
import locked_runtime_inputs as locks

SELF='tools/p09/runtime_input_frame.py'
TEST='tools/p09/tests/test_runtime_input_frame.py'


def require(ok,code):locks.require(ok,'P208_FRAME_'+code)


class Registry:
    def __init__(self,identity=lambda:(os.getpid(),threading.get_ident())):
        self.identity=identity;self.owner=identity();self.active=None
    def check(self):require(self.identity()==self.owner,'ORIGINAL_OWNER_PROCESS_THREAD')
    def claim(self,frame):
        self.check();require(self.active is None,'ONE_LIVE_FRAME');self.active=frame
    def require_active(self,frame):
        self.check();require(self.active is frame,'EXACT_LIVE_FRAME_REFERENCE')
    def release(self,frame):
        self.require_active(frame);self.active=None


class Counters:
    """기존 metadata reader와 각 실제 경계 reader의 누적값. 표본에서 reset하지 않는다."""
    def __init__(self,initial,readers):self.initial=initial;self.readers=readers;self.metadata=[]
    @property
    def bytes_read(self):return self.initial.bytes_read+sum(r.bytes_read for r in (*self.readers,*self.metadata))
    @property
    def read_passes(self):return self.initial.read_passes+sum(r.read_passes for r in (*self.readers,*self.metadata))


class Frame:
    def __init__(self,registry,required,checkpoint,held=None):
        rows=locks.input_pins(required)
        self.inputs=MappingProxyType({n:MappingProxyType(p) for n,p in rows.items()})
        self.registry=registry;self.checkpoint=checkpoint
        self.held=locks.InputLocks(locks.ROOT,checkpoint) if held is None else held
        self.state='NEW';self.readers=[];self.boundaries=[];self.reading=False;self.registered=False
        self.owned_cleanup_seen=False;self.identity_after=None
    def check(self):
        self.registry.require_active(self);require(self.state not in ('NEW','BROKEN','CLOSED','COMMITTED'),'LIVE_STATE')
        self.held.check()
    def acquire(self):
        require(self.state=='NEW','ONE_ACQUISITION');self.registry.claim(self);self.registered=True;self.state='ACQUIRING'
        try:
            self.held.acquire({n:dict(pin) for n,pin in self.inputs.items()});self.state='HELD';return self
        except BaseException:
            self.state='BROKEN';self.close();raise
    def read_boundary(self,reader_factory,checkpoint):
        self.check();require(callable(reader_factory) and callable(checkpoint) and not self.reading,'REAL_READER_AND_PARENT_GUARD')
        require(self.state==('HELD' if len(self.boundaries)==0 else 'BEFORE_READ') and len(self.boundaries)<2,
            'EXACT_TWO_ORDERED_BOUNDARIES')
        def guarded():checkpoint();self.check()
        reader=reader_factory(guarded)
        require(reader.read_passes==reader.bytes_read==0,'FRESH_BOUNDARY_READER')
        self.readers.append(reader);self.reading=True
        try:
            actual=[]
            with self.held.reader_sources(reader):
                for name,pin in self.inputs.items():
                    current=reader.fresh_pin(name);require(current==pin,'FULL_ACTUAL_BYTE_HASH');actual.append(dict(current))
            diagnostic=reader.diagnostics()
            require(diagnostic['read_passes']==len(self.inputs)
                and diagnostic['bytes_read']==sum(p['bytes'] for p in self.inputs.values()),'COMPLETE_BOUNDARY_BYTE_ACCOUNTING')
            self.boundaries.append(dict(role='before' if len(self.boundaries)==0 else 'after',
                actual_byte_pins=actual,reader_diagnostics=diagnostic))
            self.state='BEFORE_READ' if len(self.boundaries)==1 else 'AFTER_READ'
            return copy.deepcopy(actual)
        except BaseException:
            self.state='BROKEN';raise
        finally:self.reading=False
    def commit(self,owned):
        self.check();require(self.state=='AFTER_READ' and not self.reading and len(self.boundaries)==2,'COMPLETE_TWO_BYTE_BOUNDARIES')
        require(owned['cleanup_confirmed'] is True and owned['owned_tree_empty'] is True
            and type(owned['job_final']['active_processes']) is int and owned['job_final']['active_processes']==0
            and owned['job_final']['owned_processes']==[],'ORIGINAL_JOB_CLEANUP_BEFORE_FRAME_RELEASE')
        self.owned_cleanup_seen=True
        self.held.verify_two_byte_passes(self.inputs)
        self.identity_after=self.held.verify_held_identities()
        require(self.close(),'ALL_FRAME_HANDLES_RELEASED')
        self.state='COMMITTED';return self.summary()
    def close(self):
        if self.registered:self.registry.require_active(self)
        require(not self.reading,'NO_CLOSE_DURING_BYTE_READ')
        closed=self.held.close()
        if closed and self.registered:self.registry.release(self);self.registered=False
        if closed and self.state!='COMMITTED':self.state='CLOSED'
        return closed
    def summary(self):
        return dict(frame_state=self.state,registered_live_frame=self.registered,input_count=len(self.inputs),
            input_bytes=sum(p['bytes'] for p in self.inputs.values()),actual_byte_boundaries=copy.deepcopy(self.boundaries),
            original_owned_cleanup_confirmed_before_release=self.owned_cleanup_seen,
            held_identity_after_owned_cleanup=self.identity_after,handles=self.held.summary(),
            original_two_actual_per_case_byte_reads_retained=True,serialized_pin_reused_as_live_handle=False,
            input_exclusions_added=False,security_sandbox_claimed=False)
