"""Private ordered case/host protocol and concrete resource adapter; no launcher.

Acknowledgement means a checkpoint callback returned, never native authority.
The public native entry remains denied. Full admission, a qualified native host
budget and independent producer/cleanup binding are still required.
"""
import json
import re

import crossref_native_host_limits as limits

REQUEST = 'hwpx-agent.private.crossref-host-request/v1'
RESPONSE = 'hwpx-agent.private.crossref-host-response/v1'
STEPS = ('prepare_slot', 'create_save_session', 'source_open', 'source_bind',
    'opened_save', 'opened_probe', 'sdk_insert', 'saved_save', 'saved_probe',
    'save_session_close', 'create_reopen_session', 'fresh_saved_open',
    'reopened_save', 'reopened_probe', 'reopen_session_close', 'final_source_check')
FLOW = tuple(item for step in STEPS for item in
    ([('checkpoint',step),('admit_owner',None)] if step in
        ('create_save_session','create_reopen_session') else [('checkpoint',step)]))
MAX_WIRE = 4096


def require(ok, code):
    if not ok:
        raise ValueError('XREF_HOST_' + code)


def safe_code(error):
    value = error.args[0] if error.args else None
    return value if type(value) is str and re.fullmatch(
        r'(XREF_HOST_|XREF_NATIVE_LIMITS_|STOP_|P09_XREF_|P58_)[A-Z_]{1,120}',value) else 'XREF_HOST_CALLBACK_FAILED_NO_RAW_VALUES'


def unique_pairs(pairs):
    value = {}
    for key,item in pairs:
        require(key not in value, 'DUPLICATE_JSON_KEY')
        value[key] = item
    return value


def decode_request(raw):
    require(type(raw) is str and 0 < len(raw.encode('utf-8')) <= MAX_WIRE and
        '\n' not in raw and '\r' not in raw, 'WIRE_BOUNDARY')
    try:
        value = json.loads(raw, object_pairs_hook=unique_pairs)
    except (json.JSONDecodeError, RecursionError):
        raise ValueError('XREF_HOST_JSON_INVALID') from None
    require(type(value) is dict and value.get('schema_version') == REQUEST, 'REQUEST_SCHEMA')
    base = {'schema_version','sequence','case_index','operation'}
    operation = value.get('operation')
    require(type(operation) is str and operation in ('checkpoint','admit_owner','finish'), 'OPERATION')
    extras = {'checkpoint':{'step'},'admit_owner':{'identity','window_handle'},'finish':{'case_status'}}[operation]
    require(value.keys() == base | extras, 'EXACT_REQUEST_KEYS')
    require(type(value['sequence']) is int and 1 <= value['sequence'] <= 256 and
        type(value['case_index']) is int and 1 <= value['case_index'] <= 8, 'SEQUENCE_CASE_TYPES')
    if operation == 'checkpoint':
        require(type(value['step']) is str and value['step'] in STEPS, 'FIXED_STEP')
    elif operation == 'admit_owner':
        limits.validate_identity(value['identity'], value['window_handle'])
    else:
        require(type(value['case_status']) is str and value['case_status'] in ('returned','failed'), 'FINISH_STATUS')
    return value


class HostProtocol:
    """Fixed eight-case order, two owner admissions per case and one finish.

    Program callbacks are trusted dependencies. Request data cannot supply code,
    arbitrary paths/commands, a guard policy, an acceptance result or approval.
    Failed work latches, but its one finish still reaches unguarded cleanup.
    """
    def __init__(self, checkpoint, admit_owner, finish):
        require(all(callable(c) for c in (checkpoint,admit_owner,finish)), 'PROGRAM_CALLBACKS')
        self.checkpoint,self.admit_owner,self.finish = checkpoint,admit_owner,finish
        self.sequence=0;self.case_index=1;self.cursor=0;self.stopped=False
        self.primary_error=None;self.cleanup_error=None;self.finish_attempted=False;self.finished=[]

    def respond(self, raw):
        request=None;acknowledged=False;error=None;cleanup_phase=False
        try:
            request=decode_request(raw)
            require(request['sequence']==self.sequence+1 and request['case_index']==self.case_index,
                'EXACT_SEQUENCE_CASE')
            self.sequence=request['sequence']
            operation=request['operation']
            require(not self.finish_attempted and self.case_index<=8, 'CASE_ALREADY_FINISHED')
            if operation=='finish':
                # A failed worker can finish before its next checkpoint; no work is retried.
                self.finish_attempted=True
                status=request['case_status']
                if status=='returned':
                    require(not self.stopped and self.cursor==len(FLOW), 'FINISH_BEFORE_ALL_STEPS')
                else:
                    self.stopped=True
                    self.primary_error=self.primary_error or 'XREF_HOST_WORKER_REPORTED_FAILURE'
                cleanup_phase=True
                self.finish(self.case_index,status)
                self.finished.append(dict(case_index=self.case_index,case_status=status))
                acknowledged=True
                if status=='returned':
                    self.case_index+=1;self.cursor=0;self.finish_attempted=False
            else:
                require(not self.stopped and self.cursor<len(FLOW), 'STOP_LATCHED')
                expected=FLOW[self.cursor]
                require(operation==expected[0] and (operation!='checkpoint' or request['step']==expected[1]),
                    'FIXED_OPERATION_ORDER')
                if operation=='checkpoint':
                    self.checkpoint(self.case_index,request['step'])
                else:
                    self.admit_owner(self.case_index,request['identity'],request['window_handle'])
                self.cursor+=1;acknowledged=True
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as failure:
            self.stopped=True;error=safe_code(failure)
            if cleanup_phase:self.cleanup_error=self.cleanup_error or error
            else:self.primary_error=self.primary_error or error
        reply=dict(schema_version=RESPONSE,
            sequence=0 if request is None else request['sequence'],
            case_index=0 if request is None else request['case_index'],
            acknowledged=acknowledged,error_code=error,native_execution_authorized=False,p09_complete=False)
        return json.dumps(reply,separators=(',',':'))

    def summary(self):
        return dict(sequence=self.sequence,completed_callback_cases=list(self.finished),
            stopped=self.stopped,primary_error=self.primary_error,cleanup_error=self.cleanup_error,
            all_eight_callback_cases_returned=(self.case_index==9 and not self.stopped),
            native_execution_authorized=False,native_execution_attested=False,
            native_cleanup_qualified=False,accepted_count_delta=0,p09_complete=False)


class NativeResourceScope:
    """Connect ordered program callbacks to the exact native resource backend.

    This adapter installs neither a host one-percent Job nor native authority.
    It cannot be used to replace actual admission or qualify COM startup limits.
    """
    def __init__(self, guard, fresh_executable_pin):
        require(callable(getattr(guard,'check',None)) and callable(fresh_executable_pin), 'ORIGINAL_HOST')
        require(not hasattr(guard,'preparation_CPU'), 'NO_PREPARATION_ONLY_NATIVE_GUARD')
        require(type(guard.windows) is limits.c.Windows, 'ORIGINAL_WINDOWS')
        self.guard=guard;self.fresh_executable_pin=fresh_executable_pin
        self.current=None;self.current_case=None;self.profiles=[]

    def _retire(self):
        if self.current is not None:
            self.current.close()  # No pressure check or forced close during cleanup.
            self.profiles.append(dict(self.current.profile))
            self.current=None

    def checkpoint(self, case_index, step):
        # Sample using the original host guard, including during outstanding native ownership.
        if self.current is not None:self.current.observe()
        else:self.guard.check()
        if step in ('create_reopen_session','final_source_check'):
            self._retire()  # The prior exact process must already have exited.
        if step in ('create_save_session','create_reopen_session'):
            require(self.current is None, 'NO_OVERLAPPING_NATIVE_JOB')
            self.current_case=case_index
            self.current=limits.NativeOwnerJob(self.guard.windows,self.guard.check,self.fresh_executable_pin)

    def admit_owner(self, case_index, identity, window_handle):
        require(self.current is not None and self.current_case==case_index, 'OWNED_JOB_BEFORE_ADMIT')
        self.current.admit(identity,window_handle)

    def finish(self, case_index, case_status):
        require(self.current is None or self.current_case==case_index, 'CLEANUP_CASE')
        self._retire()
        self.current_case=None

    def close(self):
        self._retire()
