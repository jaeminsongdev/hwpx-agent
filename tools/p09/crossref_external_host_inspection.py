"""External jobless-root observations, not a Native/session permit or launcher.

Only the current process, original prerequisites and two EMPTY resource Jobs are
examined. Never starts/assigns a child, COM, a document or the fixed-eight batch.
The original Native startup factory and its jobless condition remain unchanged.
"""
import ctypes
from ctypes import wintypes as w
import os
from pathlib import Path

import crossref_startup_prerequisites as prerequisites
import crossref_owned_host_process as host
import crossref_native_host_limits as native
import crossref_preassigned_readonly as fixed

PROFILE='hwpx-agent.crossref-external-host-inspection/readonly-v1'
RUNTIME_SHA='dea78bb78043f0d53ef4a475f85fa0312b90fa93c136a0686d17946781c60e16'


def require(ok,code):
    if not ok:raise ValueError('XREF_EXTERNAL_HOST_'+code)


def current_identity(windows):
    """One live kernel pseudo-handle, exact FILETIME/session/image, no CIM clock."""
    k=windows.k
    for name,args,result in (
        ('GetProcessId',[w.HANDLE],w.DWORD),
        ('GetProcessTimes',[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4,w.BOOL),
        ('GetExitCodeProcess',[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
        ('ProcessIdToSessionId',[w.DWORD,ctypes.POINTER(w.DWORD)],w.BOOL)):
        fn=getattr(k,name);fn.argtypes,fn.restype=args,result
    handle=k.GetCurrentProcess();pid=int(k.GetProcessId(handle))
    image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
    times=[w.FILETIME()for _ in range(4)];session,code=w.DWORD(),w.DWORD()
    affinity,system=ctypes.c_size_t(),ctypes.c_size_t()
    require(pid==os.getpid() and k.QueryFullProcessImageNameW(handle,0,image,ctypes.byref(size))
        and image.value.casefold()==str(fixed.PYTHON).casefold(),'FIXED_LIVE_KERNEL_IMAGE')
    require(k.GetProcessTimes(handle,*(ctypes.byref(t)for t in times))
        and k.ProcessIdToSessionId(pid,ctypes.byref(session))
        and k.GetExitCodeProcess(handle,ctypes.byref(code)) and code.value==259,'LIVE_KERNEL_IDENTITY')
    birth=times[0].dwLowDateTime | times[0].dwHighDateTime<<32
    require(birth>0 and k.GetProcessAffinityMask(handle,ctypes.byref(affinity),ctypes.byref(system))
        and affinity.value==windows.mask and k.GetPriorityClass(handle)==0x4000,'EXACT_SELF_LIMITS')
    return dict(process_id=pid,session_id=int(session.value),creation_filetime_100ns=str(birth),
        process_image=image.value,affinity_mask=int(affinity.value),priority_class=0x4000,
        kernel_handle_observation=True)


def runtime_pin_matches(pin):
    # Newly observed Python 3.12.14 image; old root-anchor sources/pins stay intact.
    require(type(pin)is dict and type(pin.get('bytes'))is int and pin['bytes']==107312
        and pin.get('path')==fixed.PYTHON.name
        and pin.get('sha256')==RUNTIME_SHA,
        'FIXED_PYTHON_RUNTIME_BYTES')


def empty_resource_layout(windows,checkpoint,fresh_executable_pin):
    """Read original 7/1 partitions; close empty Jobs even after a guard STOP.

    Empty configuration proves neither child preassignment nor COM ownership.
    No constructor here has a Native start or admission method invoked.
    """
    owner=worker=None;result=None
    try:
        checkpoint()
        owner=native.NativeOwnerJob(windows,checkpoint,fresh_executable_pin)
        worker=host.OwnedHostProcess(windows,checkpoint)
        native_readback=owner.readback();worker_readback=worker.readback()
        owner_accounting=windows.accounting(owner.job);worker_accounting=windows.accounting(worker.job)
        require(owner_accounting['active_processes']==worker_accounting['active_processes']==0,'EMPTY_JOBS_ONLY')
        require(owner.plan['memory_limit']>0 and worker.plan['memory_limit']>0
            and owner.plan['memory_limit']+worker.plan['memory_limit']<=windows.memory_limit
            and owner.plan['affinity']==worker.plan['affinity']==windows.mask
            and owner.plan['cpu_rate']==worker.plan['cpu_rate']==windows.cpu_rate,'UNCHANGED_SHARED_BUDGET')
        for value in (native_readback,worker_readback):
            require(value['verified']is True and value['kill_on_close']is False
                and value['breakaway_disabled']is True and value['time_limit_installed']is False,
                'NO_KILL_TIME_OR_BREAKAWAY_POLICY')
        checkpoint()
        result=dict(native_empty_job=native_readback,worker_empty_job=worker_readback,
            aggregate_private_limit_bytes=owner.plan['memory_limit']+worker.plan['memory_limit'],
            original_eight_percent_limit_bytes=windows.memory_limit,
            both_jobs_empty=True,child_started_or_assigned=False,
            native_preassignment_or_COM_owner_qualified=False)
    finally:
        # Original close methods use actual active-process accounting, not guards.
        # Neither object has admitted a process; failures never authorize force-close.
        try:
            if worker is not None:worker.close()
        finally:
            if owner is not None:owner.close()
    require(owner.profile['cleanup_confirmed']is True and worker.profile['cleanup_confirmed']is True,
        'EMPTY_JOBS_CLEANUP')
    result['empty_jobs_closed']=True
    return result


def inspect(windows,checkpoint,fresh_executable_pin,fresh_runtime_pin):
    """Current invocation only; serialized success cannot authorize a later run."""
    checkpoint();before=current_identity(windows)
    runtime_pin_matches(fresh_runtime_pin())
    observed=prerequisites.inspect(windows,checkpoint,fresh_executable_pin)
    layout=None
    if observed['all_observed_prerequisites_passed']:
        # Recheck genuinely jobless membership, not just immediate-Job flags.
        prerequisites.startup.parent_without_prompt_kill(windows)
        layout=empty_resource_layout(windows,checkpoint,fresh_executable_pin)
    checkpoint();after=current_identity(windows)
    require(after==before,'CALLER_KERNEL_IDENTITY_CHANGED')
    runtime_pin_matches(fresh_runtime_pin())
    if layout is not None:prerequisites.startup.parent_without_prompt_kill(windows)
    return dict(profile=PROFILE,caller_identity=before,same_kernel_identity_before_after=True,
        prerequisites=observed,empty_resource_layout=layout,
        external_jobless_prerequisites_observed=observed['all_observed_prerequisites_passed'],
        future_invocation_must_revalidate_all_live_conditions=True,
        process_created=False,COM_activated=False,document_opened=False,permission_dialog_requested=False,
        fixed_eight_executed=False,native_startup_qualified=False,
        native_execution_authorized=False,accepted_count_delta=0,P09_complete=False)
