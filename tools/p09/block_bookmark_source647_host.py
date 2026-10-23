"""Fixed one-document source schedule composed with original owned Native host.

No launcher, activation, CLI, saved permit, retry or guard-policy replacement.
The original sixteen checkpoints here are resource bookkeeping, not claims of
the historical cross-reference operations named by those checkpoints.
"""
import json
import re
import crossref_qualified_batch as base
import prepared_bookmark631_drain as drain

REQUEST='hwpx-agent.private.block-bookmark-source647-request/v1'
RESPONSE='hwpx-agent.private.block-bookmark-source647-response/v1'
STEPS=('prepare_slot','create_save_session','bind_blank_document','seed_document','create_bookmarks',
    'created_save','created_image','created_bind','save_ready_close','save_session_close',
    'create_reopen_session','fresh_created_open','reopened_save','reopened_image','reopen_session_close','final_source_check')
LEGACY=dict(zip(STEPS,base.original.original.STEPS))

def flow():
    rows=[]
    for step in STEPS:
        rows.append(('checkpoint',step,None))
        if step in('create_save_session','create_reopen_session'):rows.append(('admit_owner',None,None))
        if step=='seed_document':rows.extend(('pulse',p,0)for p in('seed_prepare','seed_execute','seed_returned'))
        if step=='create_bookmarks':
            rows.extend(('pulse',p,i)for i in range(1,9)for p in('bookmark_prepare','bookmark_select','bookmark_execute','bookmark_returned'))
    return tuple(rows)

FLOW=flow()

def require(ok,code):
    if not ok:raise ValueError('XREF_HOST_BLOCK647_'+code)

def safe_code(error):
    value=error.args[0]if error.args else None
    return value if type(value)is str and re.fullmatch(r'(?:XREF_|P09_BLOCK|P09_XREF_|P58_|STOP_)[A-Z0-9_]{1,140}',value)else'XREF_HOST_BLOCK647_FAILED_NO_RAW_VALUES'

def decode(raw):
    require(type(raw)is str and 0<len(raw.encode('utf-8'))<=4096 and '\n'not in raw and '\r'not in raw,'WIRE_BOUND')
    try:v=json.loads(raw,object_pairs_hook=base.original.original.unique_pairs)
    except(json.JSONDecodeError,RecursionError):raise ValueError('XREF_HOST_BLOCK647_INVALID_JSON')from None
    require(type(v)is dict and v.get('schema_version')==REQUEST,'SCHEMA')
    require(type(v.get('sequence'))is int and 1<=v['sequence']<=64
        and type(v.get('case_index'))is int and v['case_index']==1,'EXACT_ONE_DOCUMENT_SEQUENCE')
    common={'schema_version','sequence','case_index','operation'}
    op=v.get('operation')
    require(type(op)is str and op in('checkpoint','admit_owner','pulse','finish'),'OPERATION')
    extras={'checkpoint':{'step'},'admit_owner':{'identity','window_handle'},'pulse':{'phase','range_index'},'finish':{'case_status'}}[op]
    require(v.keys()==common|extras,'CLOSED_KEYS')
    if op=='pulse':
        require(type(v['phase'])is str and type(v['range_index'])is int and ('pulse',v['phase'],v['range_index'])in FLOW,'FIXED_PULSE')
    else:
        old=dict(v,schema_version=base.original.REQUEST)
        if op=='checkpoint':
            require(type(v['step'])is str and v['step']in LEGACY,'FIXED_STEP')
            old['step']=LEGACY[v['step']]
        base.original.decode_request(json.dumps(old,separators=(',',':')))
    return v

class Schedule:
    """Closed data/order machine. Trusted callback, never caller-supplied code."""
    def __init__(self,dispatch):
        require(callable(dispatch),'PROGRAM_CALLBACK')
        self.dispatch=dispatch;self.sequence=0;self.cursor=0;self.stopped=False
        self.finish_attempted=False;self.done=False;self.primary_error=None;self.cleanup_error=None

    def respond(self,raw):
        v=None;ack=False;descriptor=None;error=None;cleanup=False
        try:
            v=decode(raw)
            require(not self.finish_attempted and not self.done,'ONE_FINISH_NO_REPLAY')
            require(v['sequence']==self.sequence+1,'EXACT_SEQUENCE')
            self.sequence=v['sequence'];op=v['operation']
            if op=='finish':
                self.finish_attempted=True;cleanup=True
                if v['case_status']=='returned':require(not self.stopped and self.cursor==len(FLOW),'ALL_STEPS_AND_RANGES_BEFORE_RETURN')
                else:self.stopped=True
                descriptor=self.dispatch(v);require(descriptor is None,'NO_FINISH_DESCRIPTOR')
                self.done=v['case_status']=='returned';ack=True
            else:
                require(not self.stopped and self.cursor<len(FLOW),'STOP_LATCHED')
                observed=(op,v.get('step')if op=='checkpoint'else v.get('phase'),v.get('range_index'))
                require(observed==FLOW[self.cursor],'EXACT_STEP_RANGE_PHASE_ORDER')
                descriptor=self.dispatch(v)
                if op=='checkpoint'and v['step']in('create_save_session','create_reopen_session'):
                    label='save'if v['step']=='create_save_session'else'reopen'
                    descriptor=base.original.validate_descriptor(descriptor,1,label)
                else:
                    require(descriptor is None,'NO_UNEXPECTED_OWNER_DESCRIPTOR')
                self.cursor+=1;ack=True
        except(ValueError,OSError,KeyError,TypeError,AttributeError)as failure:
            self.stopped=True;error=safe_code(failure)
            if cleanup:self.cleanup_error=self.cleanup_error or error
            else:self.primary_error=self.primary_error or error
        return json.dumps(dict(schema_version=RESPONSE,sequence=0 if v is None else v['sequence'],
            case_index=0 if v is None else 1,acknowledged=ack,error_code=error,owner_descriptor=descriptor if ack else None,
            native_execution_authorized=False,p09_complete=False),separators=(',',':'))

    def summary(self):
        return dict(sequence=self.sequence,next_event=self.cursor,total_events=len(FLOW),stopped=self.stopped,
            finish_attempted=self.finish_attempted,one_document_returned=self.done,
            primary_error=self.primary_error,cleanup_error=self.cleanup_error,
            native_execution_authorized=False,P09_complete=False)

class Host(base.FixedEightHost):
    """Original live handoff, exact kernel worker, two original owned startups.

    Public construction still requires original Native guard/current lifecycle;
    model-only Schedule never supplies any of those capabilities.
    """
    def __init__(self,*args,notify,**kwargs):
        super().__init__(*args,**kwargs)
        require(callable(notify),'NOTICE_CALLBACK')
        self.notify=notify;self.drain_records=[];self.schedule=Schedule(self._dispatch)

    def _dispatch(self,v):
        require(self.ready and self.worker_lease is not None,'CURRENT_LIVE_WORKER')
        if v['operation']=='pulse':
            self.worker_lease.observe(refresh_image=False)
            current=self.scope.current
            require(not self.scope.stopped and not self.protocol.protocol.stopped and self.scope.case_index==1
                and self.source_case==1 and self.scope.label=='save'and not self.scope.pending_admission and current is not None
                and not current.closed and current.profile.get('owner_bound')is True,'BOUND_SOURCE_OWNER_DURING_PULSE')
            current.observe()
            return None
        old=dict(v,schema_version=base.original.REQUEST,sequence=self.protocol.protocol.sequence+1)
        if v['operation']=='checkpoint':
            old['step']=LEGACY[v['step']]
            if v['step']in('create_reopen_session','final_source_check'):
                drain.wait(self.scope.current,self.guard,self.worker,self.notify,self.drain_records)
        reply=json.loads(super().respond(json.dumps(old,separators=(',',':'))))
        if reply['acknowledged']is not True:raise ValueError(reply['error_code']or'XREF_HOST_BLOCK647_ORIGINAL_CALLBACK_DENIED')
        return reply['owner_descriptor']

    def respond(self,raw):
        response=self.schedule.respond(raw)
        if self.schedule.stopped:
            self.scope.stopped=True;self.protocol.protocol.stopped=True
        return response

    def close(self):
        # Transport owns the same exact Native-exit wait. No unguarded work loop
        # or force-kill is added here; original close retains uncertain handles.
        self.scope.close()
        if self.worker_lease is not None:self.worker_lease.close()

    def summary(self):
        return dict(super().summary(),block_source_schedule=self.schedule.summary(),drain_records=self.drain_records,
            purpose='one_fixed_source_document_eight_block_bookmarks_two_sessions_only',
            legacy_schedule_is_resource_bookkeeping_only=True,reference_semantics_qualified=False)
