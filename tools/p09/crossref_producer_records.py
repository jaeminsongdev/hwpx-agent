"""Independent parent/file/child record comparison; NOT native causal proof.

No launcher, authority, source rewrite or evidence writer. Models and consistent
records cannot attest physical execution, COM startup safety or product success.
"""
import copy
import re
from pathlib import Path

import crossref_native_host_limits as limits
from crossref_native_host_channel import FLOW

SOURCE_SHA='64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184'
STAGES=('opened','saved','reopened')
PREFIX='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c'


def require(ok,code):
    if not ok:raise ValueError('XREF_PRODUCER_'+code)


def case_id(index):
    require(type(index) is int and 1<=index<=8,'FIXED_CASE')
    return f'P09-XREF-BOOK-C{index:02}'


def artifact_path(index,stage):
    case_id(index);require(type(stage) is str and stage in STAGES,'FIXED_STAGE')
    return f'{PREFIX}{index:02}-attempt01/{stage}.hwpx'


def identity(value):
    # Shape only; physical ownership still requires the original runtime backend.
    limits.validate_identity(value,1)
    return dict(value)


def pin(value,index,stage):
    require(type(value) is dict and value.keys()=={'path','bytes','sha256'},'PIN_SCHEMA')
    require(value['path']==artifact_path(index,stage) and type(value['bytes']) is int and
        0<value['bytes']<=4194304 and type(value['sha256']) is str and
        re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'PIN_IDENTITY')
    return dict(value)


class ParentObservations:
    """Decorate the concrete resource scope, recording only closed observations.

    The artifact reader performs paced fresh reads with its original checkpoint.
    These records deliberately retain unqualified native provenance flags.
    """
    def __init__(self,resource_scope,artifact_reader):
        require(all(callable(getattr(resource_scope,n,None)) for n in
            ('checkpoint','admit_owner','finish')) and callable(getattr(artifact_reader,'pin',None)),
            'TRUSTED_PROGRAM_DEPENDENCIES')
        self.scope,self.reader=resource_scope,artifact_reader
        self.records=[];self.current=None;self.cursor=0;self.stopped=False;self.finishing=False

    def _start(self,index):
        case_id(index)
        require(index==len(self.records)+1,'CASE_ORDER')
        if self.current is None:
            self.current=dict(schema_version='hwpx-agent.private.crossref-parent-observations/v1',
                case_id=case_id(index),owner_admissions=[],artifacts=[],finish_status=None,cleanup_profiles=[],
                native_provenance_qualified=False,native_execution_authorized=False,p09_complete=False)
            self.profile_start=len(self.scope.profiles)
        return self.current

    def _expect(self,index,operation,step=None):
        record=self._start(index)
        require(not self.stopped and not self.finishing and self.cursor<len(FLOW) and
            FLOW[self.cursor]==(operation,step),'OPERATION_ORDER_OR_STOP')
        return record

    def checkpoint(self,index,step):
        try:
            record=self._expect(index,'checkpoint',step)
            self.scope.checkpoint(index,step)
            stages={'opened_probe':'opened','saved_probe':'saved','reopened_probe':'reopened'}
            if step in stages:
                stage=stages[step]
                owner=identity(self.scope.current.identity)
                require(self.scope.current.profile['native_process_assigned'] is True,'RESOURCE_OWNER_NOT_ASSIGNED')
                require(record['owner_admissions'] and owner==record['owner_admissions'][-1]['identity'],
                    'OWNER_CHANGED_BEFORE_ARTIFACT_READ')
                actual=pin(self.reader.pin(artifact_path(index,stage)),index,stage)
                record['artifacts'].append(dict(stage=stage,pin=actual,identity=owner))
            self.cursor+=1
        except (ValueError,OSError,KeyError,TypeError,AttributeError):
            self.stopped=True;raise

    def admit_owner(self,index,observed_identity,window_handle):
        try:
            record=self._expect(index,'admit_owner')
            self.scope.admit_owner(index,observed_identity,window_handle)
            actual=identity(self.scope.current.identity)
            require(actual==identity(observed_identity) and
                self.scope.current.profile['native_process_assigned'] is True,'ADMITTED_OWNER_MISMATCH')
            count=len(record['owner_admissions']);require(count<2,'EXACT_TWO_ADMISSIONS')
            record['owner_admissions'].append(dict(label=('save','reopen')[count],identity=actual))
            self.cursor+=1
        except (ValueError,OSError,KeyError,TypeError,AttributeError):
            self.stopped=True;raise

    def finish(self,index,status):
        record=self._start(index)
        require(not self.finishing and status in ('returned','failed'),'ONE_FINISH')
        self.finishing=True
        if status=='returned':require(not self.stopped and self.cursor==len(FLOW),'INCOMPLETE_RETURN')
        else:self.stopped=True
        # Never pressure-guard cleanup, even after an observation/read failure.
        self.scope.finish(index,status)
        profiles=self.scope.profiles[self.profile_start:]
        for profile in profiles:
            record['cleanup_profiles'].append(dict(
                native_process_assigned=profile['native_process_assigned'],
                limits_verified=profile['limits_readback']['verified'],cleanup_confirmed=profile['cleanup_confirmed'],
                remaining_processes=profile['last_job_accounting']['active_processes']))
        record['finish_status']=status;self.records.append(copy.deepcopy(record))
        self.current=None;self.cursor=0;self.finishing=False


def compare_completed_case(index,trace,parent,actual_pins):
    expected=case_id(index)
    require(type(trace) is dict and type(parent) is dict and type(actual_pins) is dict,'RECORD_OBJECTS')
    require(trace.get('schema_version')=='hwpx-agent.private.crossref-native-case-trace/v1' and
        trace.get('case_id')==expected and trace.get('source_sha256')==SOURCE_SHA and
        trace.get('state')=='lifecycle_callbacks_returned_semantics_unqualified' and
        trace.get('source_identity_preserved') is True,'CHILD_COMPLETED_SOURCE_RECORD')
    for key in ('producer_binding_qualified','native_host_guard_qualified','p09_complete'):
        require(trace.get(key) is False,'CHILD_UNQUALIFIED_FLAGS')
    require(parent.get('schema_version')=='hwpx-agent.private.crossref-parent-observations/v1' and
        parent.get('case_id')==expected and parent.get('finish_status')=='returned','PARENT_COMPLETED_RECORD')
    for key in ('native_provenance_qualified','native_execution_authorized','p09_complete'):
        require(parent.get(key) is False,'PARENT_UNQUALIFIED_FLAGS')
    sessions=trace.get('sessions');admissions=parent.get('owner_admissions');cleanups=parent.get('cleanup_profiles')
    require(type(sessions) is list and len(sessions)==2 and type(admissions) is list and len(admissions)==2 and
        type(cleanups) is list and len(cleanups)==2,'EXACT_TWO_SESSIONS')
    owners=[]
    for offset,label in enumerate(('save','reopen')):
        session,admitted,cleanup=sessions[offset],admissions[offset],cleanups[offset]
        require(session['label']==admitted['label']==label and session['version']=='11.0.0.9136' and
            type(session['register_module_return']) is bool,'SESSION_LABEL_VERSION')
        owner=identity(session['process']);require(owner==identity(admitted['identity']),'PARENT_CHILD_OWNER')
        require(session['cleanup_error'] is None and session['close_without_dirty_prompt_returned'] is True and
            session['quit_invoked'] is True and type(session['remaining_owned_process_count']) is int and
            session['remaining_owned_process_count']==0,'CHILD_CLEANUP')
        require(cleanup['native_process_assigned'] is True and cleanup['limits_verified'] is True and
            cleanup['cleanup_confirmed'] is True and type(cleanup['remaining_processes']) is int and
            cleanup['remaining_processes']==0,'PARENT_RESOURCE_CLEANUP')
        owners.append(owner)
    require(owners[0]['session_id']==owners[1]['session_id'] and
        limits.creation_ticks(owners[1]['created_at_utc'])>limits.creation_ticks(owners[0]['created_at_utc']),
        'FRESH_REOPEN_BIRTH_NOT_PID_ONLY')
    child_events=trace.get('producer_events');parent_events=parent.get('artifacts');artifacts=trace.get('artifacts')
    require(type(child_events) is list and len(child_events)==3 and type(parent_events) is list and
        len(parent_events)==3 and type(artifacts) is dict and set(artifacts)==set(STAGES) and
        set(actual_pins)==set(STAGES),'EXACT_THREE_ARTIFACTS')
    for offset,stage in enumerate(STAGES):
        observed=pin(actual_pins[stage],index,stage);event=child_events[offset];witness=parent_events[offset]
        owner=owners[0 if stage!='reopened' else 1]
        require(type(artifacts[stage]) is dict and artifacts[stage].keys()=={'bytes','sha256'} and
            type(artifacts[stage]['bytes']) is int and artifacts[stage]=={'bytes':observed['bytes'],'sha256':observed['sha256']} and
            event['stage']==witness['stage']==stage and event['artifact_sha256']==observed['sha256'] and
            type(event['artifact_bytes']) is int and event['artifact_bytes']==observed['bytes'] and
            pin(witness['pin'],index,stage)==observed,'ACTUAL_PARENT_CHILD_ARTIFACT')
        require(identity(event['observed_owner_identity'])==identity(witness['identity'])==owner and
            event['producer_binding_qualified'] is False and event['source_observation_only'] is False,
            'ARTIFACT_OWNER_AND_UNQUALIFIED_FLAGS')
    probes=trace.get('probe_observations')
    require(type(probes) is dict and set(probes)==set(STAGES),'EXACT_THREE_PROBE_RECORDS')
    for stage in STAGES:
        probe=probes[stage]
        require(probe['schema_version']=='hwpx-agent.private.crossref-worker-source-probe/v1' and
            probe['state']=='source_probe_completed_not_native_attestation' and
            type(probe['candidate_count']) is int and probe['candidate_count']==8 and
            probe['observed_output_sha256']==actual_pins[stage]['sha256'] and
            probe['selected_case']['case_id']==expected and probe['selected_case']['phase']==stage,
            'PROBE_CASE_PHASE_OUTPUT')
        for field in ('native_execution_attested','native_execution_authorized','p09_complete'):
            require(probe[field] is False,'PROBE_FALSE_CLAIMS')
    events=trace.get('cleanup_events')
    require(type(events) is list and len(events)==2,'EXACT_TWO_CLEANUP_EVENTS')
    for offset,event in enumerate(events):
        require(identity(event['session_identity'])==owners[offset] and event['close_attempted'] is True and
            event['close_returned'] is True and event['document_release_returned'] is True,'CLEANUP_EVENT_OWNER')
    operations=trace.get('operations');require(type(operations) is dict,'OPERATION_RECORDS')
    for name,flag in (('opened_save','save_invoked'),('sdk_insert','execute_invoked'),
            ('saved_save','save_invoked'),('fresh_saved_open','open_invoked'),('reopened_save','save_invoked')):
        operation=operations[name]
        require(operation.get(flag) is True and operation.get('error_code') is None,'OPERATION_INTENT_AND_ERROR')
        if name=='sdk_insert':require(operation.get('execute_returned') is True,'SDK_RETURN_NOT_UNCERTAIN')
        if name in ('saved_save','fresh_saved_open','reopened_save'):
            require(operation.get('helper_returned') is True,'INDIRECT_HELPER_RETURN')
    completion=trace.get('completion');require(type(completion) is dict and
        completion.get('cleanup_error_code') is None and completion.get('trace_write_error_code') is None and
        trace.get('trace_write_attempted') is True,'COMPLETION_ERRORS')
    # trace_write_returned may be false in the serialized pre-return snapshot.
    return dict(case_id=expected,state='parent_child_file_records_consistent_native_provenance_unqualified',
        compared_artifacts=3,native_provenance_qualified=False,native_execution_attested=False,
        causal_insertion_or_preservation_proved=False,accepted_count_delta=0,p09_complete=False)


def compare_whole_batch(traces,parents,pins):
    require(all(type(value) is list and len(value)==8 for value in (traces,parents,pins)), 'WHOLE_EIGHT_REQUIRED')
    cases=[];lifetimes=set()
    for index,(trace,parent,actual) in enumerate(zip(traces,parents,pins,strict=True),1):
        cases.append(compare_completed_case(index,trace,parent,actual))
        for admitted in parent['owner_admissions']:
            owner=identity(admitted['identity']);key=(owner['process_id'],owner['created_at_utc'])
            require(key not in lifetimes,'PRODUCER_LIFETIME_REUSED_ACROSS_CASES');lifetimes.add(key)
    return dict(state='whole_eight_records_consistent_native_provenance_unqualified',cases=cases,
        native_provenance_qualified=False,native_execution_attested=False,accepted_count_delta=0,p09_complete=False)


def current_inventory(reader):
    """Full fixed-eight existence inventory only; no fabricated runtime evidence."""
    rows=[]
    for index in range(1,9):
        reader.checkpoint()
        run=reader.root/Path(artifact_path(index,'opened')).parent
        ancestor=run.parent
        while True:
            require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),'OUTPUT_ANCESTOR')
            if ancestor==reader.root:break
            require(ancestor!=ancestor.parent,'OUTPUT_ROOT');ancestor=ancestor.parent
        try:
            run.lstat();exists=True
            require(run.is_dir() and not run.is_symlink() and not run.is_junction(),'RUN_DIRECTORY')
        except FileNotFoundError:exists=False
        rows.append(dict(case_id=case_id(index),state='PRESENT_UNVERIFIED' if exists else 'NOT_RUN',
            native_provenance_qualified=False))
    return dict(state='fixed_eight_existence_inventory_not_runtime_qualification',cases=rows,
        native_execution_attested=False,accepted_count_delta=0,p09_complete=False)
