"""Raw CIM trace + canonical admission sidecar + original parent/file checks.

Never rewrites a trace, launches a process or attests native provenance. Only
seven explicitly checked identity fields are projected in a temporary copy.
The original exact verifier checks that copy against canonical parent evidence.
"""
import copy
import hashlib
import json
from pathlib import PurePosixPath

import crossref_dual_owner_identity as dual
import crossref_producer_records as original

SCHEMA='hwpx-agent.private.crossref-owner-identity-sidecar/v1'
ENTRY_KEYS={'observation','channel_message_attempted','channel_message_returned','error_code',
    'native_provenance_qualified','native_execution_authorized','p09_complete'}
SIDECAR_KEYS={'schema_version','case_id','state','original_trace','admissions',
    'native_provenance_qualified','native_execution_authorized','p09_complete'}
MAX_TRACE=1048576
MAX_SIDECAR=65536


def require(ok,code):
    if not ok:raise ValueError('XREF_CANONICAL_EVIDENCE_'+code)


def trace_path(index):
    return str(PurePosixPath(original.artifact_path(index,'opened')).parent/'target-trace.json')


def sidecar_path(index):
    return str(PurePosixPath(original.artifact_path(index,'opened')).parent/'owner-identities.json')


def unique_pairs(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'DUPLICATE_JSON_KEY');result[key]=value
    return result


def parse_bytes(value,maximum):
    require(type(value) is bytes and 0<len(value)<=maximum,'BOUNDED_RAW_BYTES')
    try:return json.loads(value.decode('utf-8'),object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError,json.JSONDecodeError,RecursionError):
        raise ValueError('XREF_CANONICAL_EVIDENCE_INVALID_JSON_BYTES') from None


def raw_pin(index,value):
    require(type(value) is bytes and 0<len(value)<=MAX_TRACE,'BOUNDED_RAW_TRACE')
    return dict(path=trace_path(index),bytes=len(value),sha256=hashlib.sha256(value).hexdigest())


def canonical_projection(index,raw_trace_bytes,sidecar):
    expected=original.case_id(index)
    require(type(sidecar) is dict and sidecar.keys()==SIDECAR_KEYS and sidecar['schema_version']==SCHEMA
        and sidecar['case_id']==expected and sidecar['state']=='owner_identity_sidecar_unqualified','SIDECAR_SCHEMA_CASE')
    for key in ('native_provenance_qualified','native_execution_authorized','p09_complete'):
        require(sidecar[key] is False,'NO_SIDECAR_PROMOTION')
    actual=raw_pin(index,raw_trace_bytes);pin=sidecar['original_trace']
    require(type(pin) is dict and pin.keys()=={'path','bytes','sha256'} and type(pin['bytes']) is int
        and pin==actual,'EXACT_ORIGINAL_TRACE_BYTES_SHA')
    raw=parse_bytes(raw_trace_bytes,MAX_TRACE)
    require(type(raw) is dict and raw.get('case_id')==expected,'ORIGINAL_TRACE_CASE')
    entries=sidecar['admissions']
    require(type(entries) is list and len(entries)==2,'EXACT_TWO_DUAL_ADMISSIONS')
    sessions=raw.get('sessions');events=raw.get('producer_events');cleanup=raw.get('cleanup_events')
    require(type(sessions) is list and len(sessions)==2 and type(events) is list and len(events)==3
        and type(cleanup) is list and len(cleanup)==2,'ORIGINAL_IDENTITY_LOCATIONS')
    require([e['stage'] for e in events]==list(original.STAGES),'ORIGINAL_STAGE_ORDER')
    projected=copy.deepcopy(raw);compat=[];canonical=[]
    for offset,label in enumerate(('save','reopen')):
        entry=entries[offset]
        require(type(entry) is dict and entry.keys()=={'session_label','evidence'}
            and entry['session_label']==label and sessions[offset]['label']==label,'ADMISSION_SESSION_ORDER')
        evidence=entry['evidence']
        require(type(evidence) is dict and evidence.keys()==ENTRY_KEYS
            and evidence['channel_message_attempted'] is True and evidence['channel_message_returned'] is True
            and evidence['error_code'] is None,'COMPLETED_CANONICAL_CHANNEL_CALL')
        for key in ('native_provenance_qualified','native_execution_authorized','p09_complete'):
            require(evidence[key] is False,'NO_ADMISSION_RECORD_PROMOTION')
        observation=evidence['observation'];decoded=dual.decode_record(observation)
        owner=dual.canonical_native_candidate(observation)
        require(original.identity(sessions[offset]['process'])==decoded['compatibility_identity']
            and original.identity(cleanup[offset]['session_identity'])==decoded['compatibility_identity'],
            'EXACT_UNMODIFIED_SESSION_COMPATIBILITY')
        compat.append(decoded['compatibility_identity']);canonical.append(owner)
        projected['sessions'][offset]['process']=dict(owner)
        projected['cleanup_events'][offset]['session_identity']=dict(owner)
    for offset,stage in enumerate(original.STAGES):
        owner_offset=1 if stage=='reopened' else 0
        require(original.identity(events[offset]['observed_owner_identity'])==compat[owner_offset],
            'EXACT_UNMODIFIED_PRODUCER_COMPATIBILITY')
        projected['producer_events'][offset]['observed_owner_identity']=dict(canonical[owner_offset])
    return projected,actual


def compare_case_bytes(index,raw_trace_bytes,sidecar,parent,artifact_pins):
    projected,pin=canonical_projection(index,raw_trace_bytes,sidecar)
    result=original.compare_completed_case(index,projected,parent,artifact_pins)
    return dict(result,comparison_kind='raw_compatibility_plus_canonical_sidecar',original_trace_pin=pin,
        projected_identity_fields=7,original_trace_rewritten=False,canonical_native_admission_qualified=False)


def compare_whole_batch(raw_traces,sidecars,parents,artifact_pins):
    require(all(type(v) is list and len(v)==8 for v in (raw_traces,sidecars,parents,artifact_pins)),
        'WHOLE_EIGHT_REQUIRED')
    projections=[];trace_pins=[]
    for index,(raw,sidecar,parent,pins) in enumerate(zip(raw_traces,sidecars,parents,artifact_pins,strict=True),1):
        projected,pin=canonical_projection(index,raw,sidecar)
        projections.append(projected);trace_pins.append(pin)
    # Preserve the old whole-eight ordering and cross-case lifetime uniqueness checks.
    whole=original.compare_whole_batch(projections,parents,artifact_pins)
    cases=[dict(result,comparison_kind='raw_compatibility_plus_canonical_sidecar',original_trace_pin=pin,
        projected_identity_fields=7,original_trace_rewritten=False,canonical_native_admission_qualified=False)
        for result,pin in zip(whole['cases'],trace_pins,strict=True)]
    return dict(whole,cases=cases,comparison_kind='raw_compatibility_plus_canonical_sidecars',
        original_traces_rewritten=False,canonical_native_admission_qualified=False)


def read_case(reader,index,parent,artifact_pins):
    """Use the existing paced actual-byte reader; caller retains final freshness."""
    require(callable(getattr(reader,'_read',None)) and callable(getattr(reader,'_bind',None))
        and type(getattr(reader,'maximum_parse_bytes',None)) is int and reader.maximum_parse_bytes>0,
        'ORIGINAL_PACED_READER')
    values=[]
    for path,maximum in ((trace_path(index),MAX_TRACE),(sidecar_path(index),MAX_SIDECAR)):
        before=reader.maximum_parse_bytes
        try:
            reader.maximum_parse_bytes=min(before,maximum)
            pin,buffer=reader._read(path,parse=True);reader._bind(path,pin)
        finally:reader.maximum_parse_bytes=before
        value=bytes(buffer);require(0<len(value)<=maximum,'ACTUAL_EVIDENCE_BYTE_BOUNDARY');values.append(value)
    return compare_case_bytes(index,values[0],parse_bytes(values[1],MAX_SIDECAR),parent,artifact_pins)
