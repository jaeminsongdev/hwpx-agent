"""Private fixed-eight session/resource successor, not a native CLI/permit.

Trusted controller callbacks only. The original backend requires a genuinely
jobless native caller and assigns its original limited Job AT creation. This
adapter never creates a COM instance, binds a ROT object, opens a document or
claims qualification. A future qualified worker must attach to the exact started
owner and report its window; the original backend verifies that handle/identity.
"""
import copy

import crossref_native_startup as startup
import crossref_native_host_channel as original

PROFILE='hwpx-agent.private.crossref-preassigned-session-scope/v1'


def require(ok,code):
    if not ok:raise ValueError('XREF_PREASSIGNED_SCOPE_'+code)


class PreassignedSessionScope:
    """Sixteen nonoverlapping original startups, exact order, no effect retry.

    This module installs no one-percent worker Job and grants no execution
    authority. Merely importing/constructing it cannot start a process. An actual
    fixed-eight controller still requires the complete original qualification.
    """
    def __init__(self,guard,fresh_executable_pin):
        require(callable(getattr(guard,'check',None))and callable(fresh_executable_pin)
            and not hasattr(guard,'preparation_CPU')and type(getattr(guard,'windows',None))is startup.limits.c.Windows,
            'ORIGINAL_NATIVE_GUARD_REQUIRED')
        self.guard,self.fresh_executable_pin=guard,fresh_executable_pin
        self.case_index=1;self.cursor=0;self.current=None;self.label=None
        self.pending_admission=False;self.stopped=False;self.finish_attempted=False;self.closed=False
        self.seen=set();self.sessions=[];self.finished=[]

    def _work(self,case_index):
        require(not self.closed and not self.stopped and not self.finish_attempted,'STOPPED_NO_RETRY')
        require(type(case_index)is int and 1<=case_index<=8 and case_index==self.case_index,'EXACT_CASE_ORDER')

    def _retire(self):
        if self.current is None:return
        # No resource admission/deadline here. The original backend checks actual
        # process exit and an empty tree; a live/uncertain owner retains all handles.
        self.current.close()
        require(self.current.closed and self.current.profile['cleanup_confirmed']is True,'ORIGINAL_CLEANUP_REQUIRED')
        self.sessions.append(dict(case_index=self.case_index,session_label=self.label,
            startup_profile=copy.deepcopy(self.current.profile)))
        self.current=None;self.label=None;self.pending_admission=False

    def checkpoint(self,case_index,step):
        try:
            self._work(case_index)
            require(type(step)is str and self.cursor<len(original.STEPS)
                and step==original.STEPS[self.cursor]and not self.pending_admission,'EXACT_STEP_OR_PENDING_OWNER')
            # Prior save/reopen Close/Quit must have completed before the next
            # session. Do not call observe() on an already-exited process first.
            if step in('create_reopen_session','final_source_check'):self._retire()
            if self.current is None:self.guard.check()
            else:self.current.observe()
            if step in('create_save_session','create_reopen_session'):
                require(self.current is None,'NO_OVERLAPPING_SESSION')
                self.label='save'if step=='create_save_session'else'reopen'
                self.current=startup.PreassignedNativeStartup(self.guard,self.fresh_executable_pin)
                # Retain this exact backend even when create/resume fails or an
                # observation is uncertain. There is no fallback COM activation.
                self.current.create_suspended()
                require(self.current.profile['pre_run_verified']is True
                    and self.current.profile['assigned_before_initial_thread']is True,'PREASSIGNMENT_BEFORE_RESUME')
                key=(self.current.pid,self.current.birth,self.current.session)
                require(type(key[0])is int and 0<key[0]<=0xffffffff and type(key[1])is int and key[1]>0
                    and type(key[2])is int and 0<=key[2]<=0xffffffff and key not in self.seen,'UNIQUE_KERNEL_LIFETIME')
                self.seen.add(key)
                self.current.resume()
                require(self.current.profile['resumed']is True,'ORIGINAL_SINGLE_RESUME_RETURNED')
                self.pending_admission=True
            self.cursor+=1
        except BaseException:
            self.stopped=True
            raise

    def pending_owner_descriptor(self,case_index):
        """Current exact started owner DATA; no COM pointer or reusable permit."""
        try:
            self._work(case_index)
            require(self.current is not None and self.pending_admission,'PENDING_PREASSIGNED_OWNER_ONLY')
            self.current.observe()
            return dict(profile=PROFILE,case_index=self.case_index,session_label=self.label,
                process_id=self.current.pid,session_id=self.current.session,
                created_at_utc=startup.utc_identity(self.current.birth),
                executable_sha256=startup.limits.EXECUTABLE_SHA,
                source='current_exact_preassigned_process_handle',
                COM_owner_bound=False,native_execution_authorized=False,native_startup_qualified=False,P09_complete=False)
        except BaseException:
            self.stopped=True
            raise

    def admit_owner(self,case_index,identity,window_handle):
        try:
            self._work(case_index)
            require(self.current is not None and self.pending_admission,'SINGLE_PENDING_OWNER_ADMISSION')
            # bind_owner uses the same already-assigned process handle. It never
            # calls AssignProcessToJobObject on a COM-created process.
            result=self.current.bind_owner(identity,window_handle)
            require(self.current.profile['owner_bound']is True,'ORIGINAL_WINDOW_HANDLE_BINDING_RETURNED')
            self.pending_admission=False
            return result
        except BaseException:
            self.stopped=True
            raise

    def finish(self,case_index,case_status):
        try:
            require(not self.closed and not self.finish_attempted and type(case_index)is int
                and case_index==self.case_index and 1<=case_index<=8,'SINGLE_CASE_FINISH')
            self.finish_attempted=True
            require(type(case_status)is str and case_status in('returned','failed'),'CLOSED_FINISH_STATUS')
            if case_status=='returned':
                require(not self.stopped and self.cursor==len(original.STEPS)and self.current is None
                    and not self.pending_admission,'ALL_STEPS_AND_EXIT_BEFORE_RETURNED')
            else:self.stopped=True
            self._retire()
            self.finished.append(dict(case_index=case_index,case_status=case_status))
            if case_status=='returned':self.case_index+=1;self.cursor=0;self.finish_attempted=False
        except BaseException:
            self.stopped=True
            raise

    def close(self):
        # Re-observation of cleanup for the retained exact owner is allowed;
        # it is not a start, resume, bind or product retry. Live owners still reject.
        if self.closed:return
        self._retire();self.closed=True

    def summary(self):
        return dict(profile=PROFILE,next_case_index=self.case_index,next_step_index=self.cursor,
            stopped=self.stopped,pending_owner_admission=self.pending_admission,closed=self.closed,
            retired_sessions=copy.deepcopy(self.sessions),finished_cases=copy.deepcopy(self.finished),
            all_eight_callback_cases_returned=self.case_index==9 and not self.stopped,
            native_execution_authorized=False,native_startup_qualified=False,native_execution_attested=False,
            native_cleanup_qualified=False,accepted_count_delta=0,P09_complete=False)
