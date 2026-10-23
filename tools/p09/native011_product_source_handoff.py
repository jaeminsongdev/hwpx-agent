"""Parent source-handle transfer for an explicitly connected product worker.

No launch, GO or authority at construction. Uses the original source loan,
descriptor, live Frame coverage, original readiness Gate and original Job owner.
Post-spawn setup failure returns the child for original assignment/cleanup and
fails closed before START/GO. No Native or product runtime qualification here.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import threading
from types import SimpleNamespace as NS

SELF='tools/p09/native011_product_source_handoff.py'
TEST='tools/p09/tests/test_native011_product_source_handoff.py'
TASK='case165-current-r011-tests'


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_SOURCE_HANDOFF_'+code)


class Handoff:
    def __init__(self,root,entry_pin,frame,required,coverage,inheritance,bridge,protocol,checkpoint,*,frame_type):
        require(type(entry_pin) is dict and required.get(entry_pin.get('path'))==entry_pin,
            'EXPLICIT_WORKER_ENTRY_IN_WHOLE_SOURCE_DECLARATION')
        require(root==frame.held.root,'SAME_ACTUAL_HELD_FRAME_ROOT')
        require(callable(checkpoint),'ORIGINAL_RESOURCE_CHECKPOINT')
        self.root=root;self.entry_pin=dict(entry_pin);self.frame=frame;self.required={n:dict(p) for n,p in required.items()}
        self.coverage=coverage;self.inheritance=inheritance;self.bridge=bridge;self.protocol=protocol
        self.checkpoint=checkpoint;self.frame_type=frame_type;self.owner=(os.getpid(),threading.get_ident())
        self.phase='NEW';self.failed=False;self.attempts=0;self.process=None;self.raw_stdin=None;self.gate=None
        self.loan=self.descriptor=None;self.counts=self.identities=None;self.errors=[];self.started=False
    def owner_check(self):require((os.getpid(),threading.get_ident())==self.owner,'SAME_OWNER_PROCESS_THREAD')
    def live(self):
        self.owner_check()
        try:
            self.checkpoint();require(not self.failed,'FAILED_HANDOFF_NO_RESUME');self.frame.check()
            require(self.frame.state=='BEFORE_READ' and self.frame.registered and not self.frame.reading
                and self.frame.held.acquired and not self.frame.held.closed and not self.frame.held.releasing,
                'SAME_LIVE_FIRST_BOUNDARY_OWNER')
        except BaseException:self.failed=True;raise
    def cleanup_handles(self):
        self.owner_check()
        for label,instance,method in (('SOURCE_FLAGS',self.loan,'restore'),('DESCRIPTOR',self.descriptor,'close')):
            if instance is None:continue
            # Confirmed completed cleanup is a lifecycle fact, not fresh IO
            # credit. Never re-query source handles after the Frame closed.
            if label=='SOURCE_FLAGS' and instance.state=='RESTORED' and not instance.failed and not instance.restore_errors:continue
            if label=='DESCRIPTOR' and instance.writer is instance.reader is None and not instance.failed and instance.close_failures==0:continue
            try:ok=getattr(instance,method)() is True
            except BaseException:ok=False
            if not ok:self.failed=True;self.errors.append('UNCONFIRMED_'+label+'_RESTORE_OR_CLOSE')
        return not self.errors
    def spawn(self,factory,command,**kwargs):
        self.owner_check();self.checkpoint()
        require(self.phase=='NEW' and self.attempts==0 and not self.failed,'ONE_SPAWN_NO_RETRY')
        self.attempts=1;self.phase='SPAWNING'
        try:
            self.live()
            require(type(command) is list and len(command)==7 and command[:3]==[sys.executable,'-B',str(self.root/self.entry_pin['path'])]
                and command[3]=='--ready-handle' and command[5:]==['--task',TASK]
                and type(command[4]) is str and 1<=len(command[4])<=20 and command[4].isascii()
                and command[4].isdecimal() and 0<int(command[4])<2**64,
                'ONE_EXACT_ORIGINAL_WORKER_COMMAND')
            event=int(command[4]);startup=kwargs.get('startupinfo');attributes=getattr(startup,'lpAttributeList',None)
            require(set(kwargs)=={'cwd','stdin','stdout','stderr','creationflags','startupinfo','close_fds'}
                and all(kwargs[name]==subprocess.PIPE for name in ('stdin','stdout','stderr'))
                and kwargs['creationflags']==subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW
                and callable(factory) and kwargs.get('close_fds') is True and kwargs.get('cwd')==self.root
                and type(attributes) is dict and attributes==dict(handle_list=[event]),'ORIGINAL_EXPLICIT_EVENT_HANDLE_LIST')
            held=self.frame.held;self.counts=dict(held.stream_read_counts);self.identities=copy.deepcopy(held.files)
            rows=[]
            for name,path,handle,directory in held.owned:
                if not directory and name in self.required:
                    info=held.api.inspect(handle)
                    rows.append(dict(handle=handle,pin=dict(self.required[name]),identity=list(info['identity'])))
            self.bridge.rows_checked(rows)
            require({r['pin']['path'] for r in rows}==set(self.required),'EVERY_DECLARED_SOURCE_HAS_ONE_LIVE_HANDLE')
            packet=dict(schema_version=self.bridge.SCHEMA,parent_pid=os.getpid(),sources=rows)
            raw=json.dumps(packet,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')+b'\n'
            require(0<len(raw)<=262144,'BOUNDED_METADATA_NOT_SOURCE_BYTE_CACHE')
            self.loan=self.inheritance.SourceInheritance(self.frame,self.required,self.coverage,frame_type=self.frame_type)
            self.descriptor=self.bridge.DescriptorMapping(self.bridge.Kernel(),held.api.pacer.reserve)
            mapped=self.descriptor.prepare(raw);handles=self.loan.arm()
            inherited=[*handles,mapped,event]
            require(len(inherited)==len(set(inherited)) and all(type(h) is int and h>0 for h in inherited),
                'EXACT_DISTINCT_SOURCE_DESCRIPTOR_EVENT_HANDLES')
            selected=copy.copy(startup);selected.lpAttributeList=dict(handle_list=inherited)
            options=dict(kwargs,startupinfo=selected)
            child_command=[*command,'--source-mapping',str(mapped),str(len(raw)),hashlib.sha256(raw).hexdigest()]
            self.process=factory(child_command,**options)
            # Save the raw pipe BEFORE original Input10/Gate15 wrappers. START
            # must not start the product clock or recursively enter Gate.write.
            self.raw_stdin=self.process.stdin
            require(callable(getattr(self.raw_stdin,'write',None)) and callable(getattr(self.raw_stdin,'flush',None)),
                'ACTUAL_CHILD_RAW_START_PIPE')
        except BaseException:
            self.failed=True
            if self.process is None:raise
        finally:
            self.cleanup_handles()
            if self.process is None:self.phase='BROKEN'
            else:self.phase='SPAWNED'
        # Even failed post-spawn setup must return the actual process so the
        # original runner can assign its Job, then deny GO and clean it up.
        return self.process
    def bind_gate(self,gate):
        self.owner_check()
        require(self.gate is None and self.phase=='SPAWNED' and isinstance(gate,self.protocol.Gate)
            and gate.process is self.process and gate.seconds==15 and not gate.attempted
            and all(getattr(gate,name).__func__ is getattr(self.protocol.Gate,name)
                for name in ('write','owned','now','flush')),
            'ONE_ORIGINAL_GATE15_BEFORE_ANY_GO_ATTEMPT')
        self.gate=gate
    def verify_owned(self,process,original):
        try:
            self.live()
            require(self.phase=='SPAWNED' and process is self.process and callable(original)
                and original(process) is True,'ORIGINAL_SAME_LIVE_OWNED_JOB_MEMBER')
            require(self.loan is not None and self.loan.summary()['restore_confirmed'] is True,
                'RESTORED_SOURCE_INHERITANCE_FLAGS')
            return True
        except BaseException:self.failed=True;raise
    def gate_checkpoint(self):
        try:
            self.live();gate=self.gate
            require(gate is not None and gate.attempted and not gate.stopped and not gate.written
                and gate.process is self.process,'NO_START_BEFORE_OR_OUTSIDE_ORIGINAL_GATE15')
            # Gate.owned was already called after its real clock began; recheck
            # the same original Job immediately before the sole START write.
            gate.owned()
            if not self.started:
                # Full original coverage is checked at transfer/START, not on
                # every 50ms event wait. Every wait still checks the original
                # live Frame/guard/Job. No prior byte result is reused as IO.
                self.coverage.verify(self.frame,self.required,frame_type=self.frame_type,boundary='before')
                require(self.frame.held.stream_read_counts==self.counts and self.frame.held.files==self.identities,
                    'UNCHANGED_PARENT_READ_COUNTS_AND_IDENTITIES_BEFORE_START')
                require(self.raw_stdin.write(self.bridge.START)==len(self.bridge.START),'COMPLETE_PREPARATION_START_WRITE')
                self.raw_stdin.flush();self.started=True
        except BaseException:self.failed=True;raise
    def summary(self):
        self.owner_check()
        return dict(phase=self.phase,failed=self.failed,spawn_attempts=self.attempts,process_returned_for_original_cleanup=self.process is not None,
            source_flags_and_descriptor_cleanup_errors=list(self.errors),preparation_START_sent=self.started,
            original_Gate15_bound=self.gate is not None,raw_START_outside_original_product_Input10=True,
            source_bytes_hashes_JSON_or_AST_cached=False,original_parent_byte_read_credit_changed=False,
            original_Job_or_deadline_or_resource_policy_changed=False,product_GO_written_by_handoff=False,
            actual_worker_or_Native_or_product_qualified=False,GO_authorized=False)


def connect(handoff,launch,root,entry_pin,component,protocol,connection,factory,capture_type,subprocess,verify_owned,checkpoint,**options):
    """Original launch/readiness bodies; only explicit scoped dependencies."""
    original=connection.connect
    def ready(*args,**keywords):
        require(len(args)==7 and args[0] is component and args[1] is protocol and args[-1] is checkpoint,
            'ONE_ORIGINAL_READINESS_DEPENDENCY_SITE')
        return original(*args[:-1],handoff.gate_checkpoint,**keywords)
    api=launch.connect(root,entry_pin,component,protocol,NS(**{**vars(connection),'connect':ready}),
        lambda command,**kwargs:handoff.spawn(factory,command,**kwargs),capture_type,subprocess,
        lambda process:handoff.verify_owned(process,verify_owned),checkpoint,**options)
    previous=api.Popen
    def popen(*args,**kwargs):
        process=previous(*args,**kwargs)
        try:
            require(len(api.gates)==1,'ONE_ACTUAL_READINESS_GATE');handoff.bind_gate(api.gates[0])
        except BaseException:
            handoff.failed=True
            # Preserve the returned process; a failed handoff checkpoint/owned
            # predicate will deny the existing GO, not lose cleanup ownership.
        return process
    return NS(**{**vars(api),'Popen':popen,'source_handoff':handoff})
