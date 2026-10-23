"""Private v2 wire for the original fixed-eight flow + exact current owner data.

No CLI/launcher/worker or execution permit. Acknowledgement is callback return,
not Native authority. The unchanged v1 validator/order machine is composed with
the unchanged preassigned session scope; v1 callers/replies remain unchanged.
"""
import json
import re
import crossref_native_host_channel as original
import crossref_preassigned_session_scope as sessions

REQUEST='hwpx-agent.private.crossref-preassigned-host-request/v2'
RESPONSE='hwpx-agent.private.crossref-preassigned-host-response/v2'
KEYS={'profile','case_index','session_label','process_id','session_id','created_at_utc','executable_sha256','source',
    'COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete'}


def require(ok,code):
    if not ok:raise ValueError('XREF_HOST_V2_'+code)


def validate_descriptor(value,case_index,label):
    require(type(value)is dict and value.keys()==KEYS,'DESCRIPTOR_CLOSED_SCHEMA')
    require(value['profile']==sessions.PROFILE and type(value['case_index'])is int and value['case_index']==case_index
        and value['session_label']==label and label in('save','reopen')
        and value['source']=='current_exact_preassigned_process_handle','DESCRIPTOR_CONTEXT')
    require(type(value['process_id'])is int and 0<value['process_id']<=0x7fffffff
        and type(value['session_id'])is int and 0<=value['session_id']<=0x7fffffff
        and value['executable_sha256']==sessions.startup.limits.EXECUTABLE_SHA,'DESCRIPTOR_PROCESS_IDENTITY')
    sessions.startup.limits.creation_ticks(value['created_at_utc'])
    require(all(value[k]is False for k in('COM_owner_bound','native_execution_authorized','native_startup_qualified','P09_complete')),
        'DESCRIPTOR_NOT_NATIVE_AUTHORITY')
    return dict(value)


def decode_request(raw):
    require(type(raw)is str and 0<len(raw.encode('utf-8'))<=original.MAX_WIRE and '\n'not in raw and '\r'not in raw,'REQUEST_WIRE_BOUND')
    try:value=json.loads(raw,object_pairs_hook=original.unique_pairs)
    except(json.JSONDecodeError,RecursionError):raise ValueError('XREF_HOST_V2_JSON_INVALID')from None
    require(type(value)is dict and value.get('schema_version')==REQUEST,'REQUEST_VERSION')
    old=dict(value,schema_version=original.REQUEST)
    # Exact original shapes, numeric types, case/sequence limits, identity and
    # fixed16 steps are not reimplemented or relaxed for the new version.
    checked=original.decode_request(json.dumps(old,separators=(',',':')))
    checked['schema_version']=REQUEST
    return checked


def safe_code(error):
    value=error.args[0]if error.args else None
    return value if type(value)is str and re.fullmatch(
        r'(XREF_HOST_|XREF_NATIVE_STARTUP_|XREF_NATIVE_LIMITS_|XREF_PREASSIGNED_SCOPE_|STOP_)[A-Z0-9_]{1,120}',value)else'XREF_HOST_V2_CALLBACK_FAILED_NO_RAW_VALUES'


class PreassignedHostProtocol:
    """Descriptor only on the two creation acknowledgements; no new operation."""
    def __init__(self,scope):
        require(type(scope)is sessions.PreassignedSessionScope,'EXACT_PREASSIGNED_SCOPE')
        self.scope=scope;self.descriptor=None;self.scope_error=None
        self.protocol=original.HostProtocol(self._checkpoint,self._admit,self._finish)

    def _call(self,callback,*args):
        try:return callback(*args)
        except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
            self.scope_error=self.scope_error or safe_code(error)
            raise ValueError('XREF_HOST_PREASSIGNED_CALLBACK_REJECTED')from None

    def _checkpoint(self,case_index,step):
        self._call(self.scope.checkpoint,case_index,step)
        if step in('create_save_session','create_reopen_session'):
            label='save'if step=='create_save_session'else'reopen'
            self.descriptor=validate_descriptor(self._call(self.scope.pending_owner_descriptor,case_index),case_index,label)

    def _admit(self,case_index,identity,window_handle):
        expected=self._call(self.scope.pending_owner_descriptor,case_index)
        require(all(identity[k]==expected[k]for k in('process_id','session_id','created_at_utc','executable_sha256')),
            'EXACT_PENDING_CANONICAL_OWNER')
        self._call(self.scope.admit_owner,case_index,identity,window_handle)

    def _finish(self,case_index,case_status):
        self._call(self.scope.finish,case_index,case_status)

    def respond(self,raw):
        self.descriptor=None
        try:
            request=decode_request(raw)
            response=json.loads(self.protocol.respond(json.dumps(dict(request,schema_version=original.REQUEST),separators=(',',':'))))
        except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
            self.protocol.stopped=True
            code=safe_code(error);self.protocol.primary_error=self.protocol.primary_error or code
            response=dict(sequence=0,case_index=0,acknowledged=False,error_code=code)
        descriptor=self.descriptor if response['acknowledged']else None
        reply=dict(schema_version=RESPONSE,sequence=response['sequence'],case_index=response['case_index'],
            acknowledged=response['acknowledged'],error_code=response['error_code'],owner_descriptor=descriptor,
            native_execution_authorized=False,p09_complete=False)
        text=json.dumps(reply,separators=(',',':'))
        require(len(text.encode('utf-8'))<=original.MAX_WIRE,'REPLY_WIRE_BOUND')
        return text

    def summary(self):
        return dict(protocol=self.protocol.summary(),scope=self.scope.summary(),scope_error=self.scope_error,
            native_execution_authorized=False,native_startup_qualified=False,fixed_eight_execution_attested=False,
            accepted_count_delta=0,P09_complete=False)
