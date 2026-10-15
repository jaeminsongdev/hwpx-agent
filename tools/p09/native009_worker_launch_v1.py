"""Closed production launch/readiness binding; not installed in Native yet.

One inherited event, original 10-second Input/Capture and original owned Job.
Creation success always returns the process, even when inheritance restoration
fails: the original owner receives it and the GO boundary fails closed.
"""
import ctypes
from ctypes import wintypes as w
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native009_worker_launch_v1.py'
TEST='tools/p09/tests/test_native009_worker_launch_v1.py'
ENTRY='tools/p09/native009_worker_entry_v1.py'
TASK='case165-current-r009-tests'


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_LAUNCH_'+label)


def source(root,pin):
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==ENTRY
        and type(pin['bytes']) is int and 0<pin['bytes']<=65536,'ONE_EXACT_PRODUCTION_ENTRY_PIN')
    path=root/ENTRY
    require(path.is_file() and not path.is_symlink() and not path.is_junction(),'DIRECT_ENTRY')
    for ancestor in (path.parent,*path.parent.parents):
        require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),'DIRECT_ENTRY_ANCESTORS')
        if ancestor==root:break
    with path.open('rb') as stream:raw=stream.read(pin['bytes']+1)
    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'CURRENT_EXACT_ENTRY_BYTES')


def connect(root,entry_pin,component,protocol,connection,factory,capture_type,subprocess,verify_owned,checkpoint,*,event_factory=None,clock=None):
    require(callable(verify_owned) and callable(checkpoint),'ACTUAL_OWNER_AND_ORIGINAL_GUARD')
    expected=[sys.executable,str(root/'tools/p09/current_queue_successor_runtime.py'),'--owned-worker','--task',TASK]
    state=NS(launches=0,postspawn_inheritance_error=False,actual=None,command=None)
    def launch(original,event,*args,**kwargs):
        require(state.launches==0 and list(args)==[expected],'EXACT_ORIGINAL_WORKER_COMMAND_ONCE')
        require(set(kwargs)=={'cwd','stdin','stdout','stderr','creationflags'} and kwargs['cwd']==root
            and all(kwargs[k]==subprocess.PIPE for k in ('stdin','stdout','stderr'))
            and kwargs['creationflags']==subprocess.BELOW_NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW,
            'ORIGINAL_WORKER_PIPES_ROOT_AND_FLAGS')
        source(root,entry_pin);checkpoint();state.launches+=1
        event.inheritable(True)
        startup=subprocess.STARTUPINFO();startup.lpAttributeList={'handle_list':[event.handle]}
        command=[sys.executable,'-B',str(root/ENTRY),'--ready-handle',str(event.handle),'--task',TASK]
        try:process=original(command,startupinfo=startup,close_fds=True,**kwargs)
        except BaseException:
            try:event.inheritable(False)
            except BaseException:pass
            raise
        # No exception may lose a successfully-created process before the
        # original runner receives/assigns/cleans it. Reject at GO instead.
        state.actual=process;state.command=command
        try:event.inheritable(False)
        except BaseException:state.postspawn_inheritance_error=True
        return process
    def owned(process):
        require(not state.postspawn_inheritance_error,'POSTSPAWN_EVENT_INHERITANCE_RESTORE_FAILED')
        return process is state.actual and verify_owned(process) is True
    api=connection.connect(component,protocol,factory,capture_type,launch,owned,checkpoint,
        event_factory=event_factory,clock=clock,seconds=15)
    return NS(**{**vars(api),'launch_state':state,'production_entry_pin':dict(entry_pin),
        'Native_full_source_or_dispatch_qualified':False})


def same_owned_job(windows,job,expected,actual):
    """The actual caller supplies the original Job handle, not any-Job proof."""
    require(job is not None and actual is expected,'SAME_ORIGINAL_JOB_AND_PROCESS')
    member=w.BOOL()
    return bool(windows.k.IsProcessInJob(int(actual._handle),job,ctypes.byref(member))) and bool(member.value)
