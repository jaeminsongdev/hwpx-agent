"""Bounded, observable work drain of ONLY the current exact Native Job.

Cleanup remains the original no-force-kill policy, even after work has stopped.
No process/Job is created or terminated here. No observe() on an exited root.
"""
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import hashlib
import time

SECONDS = 45


def require(ok, code):
    if not ok:
        raise ValueError('XREF_PREPARED631_DRAIN_'+code)


def identities(windows, job):
    """Enumerate that Job only; recheck held process membership and birth.

    Unknown executable names are hashed, never paths/command lines. A process
    disappearing during enumeration is uncertainty, not an invented identity.
    """
    from conservative_maintenance import ProcessList
    k = windows.k
    listing = ProcessList()
    require(k.QueryInformationJobObject(job, 3, ctypes.byref(listing), ctypes.sizeof(listing), None)
            and listing.count <= 64, 'JOB_LIST')
    rows = []
    for pid in listing.pids[:listing.count]:
        handle = k.OpenProcess(0x1000, False, pid)
        if not handle:
            rows.append(dict(pid=int(pid), identity_observed=False))
            continue
        try:
            member = w.BOOL()
            image, length = ctypes.create_unicode_buffer(32768), w.DWORD(32768)
            times = [w.FILETIME() for _ in range(4)]
            observed = bool(k.IsProcessInJob(handle, job, ctypes.byref(member)) and member.value
                            and k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length))
                            and k.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)))
            row = dict(pid=int(pid), identity_observed=observed)
            if observed:
                name = Path(image.value).name.casefold()
                row.update(created_100ns=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
                           role=name if name in ('hwp.exe', 'splwow64.exe', 'printfilterpipelinesvc.exe',
                                                  'conhost.exe', 'hpdf.exe') else 'other-owned',
                           image_basename_sha256=hashlib.sha256(name.encode()).hexdigest())
            rows.append(row)
        finally:
            require(k.CloseHandle(handle), 'QUERY_HANDLE_CLOSE')
    return rows


def wait(current, guard, worker, notify, records, *, clock=time.monotonic,
         sleep=time.sleep, observe_identities=identities):
    if current is None or current.closed:
        return
    start = last = clock()
    row = dict(process_id=current.pid, root_exited=False, closed=False, observations=[])
    records.append(row)
    require(len(records) <= 12, 'SINGLE_RETIREMENT_PER_SESSION')
    try:
        while True:
            guard.check()
            # Owner Job observes its limits/combined private budget even after
            # the held root is signaled. It does NOT require a live root.
            current.owner_job.observe()
            worker.observe()
            signaled = guard.windows.k.WaitForSingleObject(current.process, 0)
            require(signaled in (0, 258), 'EXACT_ROOT_WAIT_FAILED')
            row['root_exited'] = signaled == 0
            account = guard.windows.accounting(current.owner_job.job)
            elapsed = clock()-start
            if row['root_exited'] and account['active_processes'] == 0:
                row.update(closed=True, elapsed_seconds=round(elapsed, 3))
                return
            if not row['observations'] or clock()-last >= 5:
                sample = guard.samples[-1]
                item = dict(elapsed_seconds=round(elapsed, 3), root_exited=row['root_exited'],
                            active_processes=account['active_processes'],
                            owned_identities=observe_identities(guard.windows, current.owner_job.job),
                            system_CPU=sample['system_cpu_percent'], available_RAM_percent=sample['available_ram_percent'])
                row['observations'].append(item)
                notify(dict(state='DRAIN631_SAME_NATIVE_TREE_WORK_GUARDED', process_id=current.pid,
                            **{k: v for k, v in item.items() if k != 'owned_identities'}))
                last = clock()
            require(elapsed < SECONDS, 'WORK45_TIMEOUT_NO_RETRY')
            sleep(.2)
    except BaseException as error:
        row.update(work_stopped=True, cleanup_confirmed=False,
                   elapsed_seconds=round(clock()-start, 3), failure_type=type(error).__name__)
        raise
