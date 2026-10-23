"""One bounded initial-input wait on the already-created held process; not COM readiness/authority."""
import ctypes,time
from ctypes import wintypes as w
BOUND_SECONDS=3.0
POLL_SECONDS=.05
def require(ok,code):
    if not ok:raise ValueError('XREF_NATIVE_STARTUP_INPUT_IDLE_'+code)
def _wait(startup,wait_idle,clock,sleep):
    require(not startup.closed and startup.process is not None and startup.profile.get('resumed')is True
        and not startup.profile.get('input_idle_wait_attempted',False),'ONE_RESUMED_HELD_PROCESS_WAIT_ONLY')
    startup.profile.update(input_idle_wait_attempted=True,input_idle_observed=False,input_idle_is_COM_readiness_or_authority=False)
    started=clock();polls=0
    try:
        while True:
            # Original Native guard, parent policy, exact held PID/birth/session/image and Job limits stay live.
            startup.observe();require(clock()-started<BOUND_SECONDS,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY')
            status=wait_idle(startup.process,0);polls+=1
            if status==0:
                startup.observe();startup._fresh_image()
                require(clock()-started<BOUND_SECONDS,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY')
                startup.profile.update(input_idle_observed=True,input_idle_poll_count=polls,input_idle_elapsed_seconds=round(clock()-started,6));return
            require(status==258,'WAIT_FAILED_NO_OWNER_OR_RETRY')
            sleep(POLL_SECONDS)
    except BaseException:
        startup.profile.update(input_idle_poll_count=polls,input_idle_state='failed_or_uncertain_no_owner_no_retry');raise
def wait(startup):
    # No new process, registration, activation, window lookup or owner binding.
    user=ctypes.WinDLL('user32',use_last_error=True);function=user.WaitForInputIdle
    function.argtypes,function.restype=[w.HANDLE,w.DWORD],w.DWORD
    return _wait(startup,function,time.monotonic,time.sleep)
