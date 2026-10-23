"""Closed dual-representation record validation, not physical admission/authority.

Compatibility CIM data stays unmodified. Canonical birth must equal the recorded
100ns kernel value exactly; no tolerance/projection of the CIM clock is used.
The original native backend must independently verify any candidate's live handle.
"""
import re

import crossref_native_host_limits as native

KEYS={'schema_version','compatibility_kind','compatibility_identity','kernel_identity',
    'kernel_creation_filetime_100ns','kernel_process_image','kernel_window_verified',
    'kernel_before_after_same_handle_equal','compatibility_fresh_check_returned',
    'kernel_creation_not_derived_from_cim','native_provenance_qualified',
    'native_execution_authorized','p09_complete'}
BASE={'process_id','session_id','created_at_utc'}


def require(ok,code):
    if not ok:raise ValueError('XREF_DUAL_IDENTITY_'+code)


def decode_record(value):
    require(type(value) is dict and value.keys()==KEYS,'CLOSED_RECORD_SCHEMA')
    require(value['schema_version']=='hwpx-agent.private.crossref-dual-owner-identity/v1'
        and type(value['compatibility_kind']) is str and value['compatibility_kind'] in
        ('original_p58_identity','current_process_cim_only'),'RECORD_KIND')
    full=value['compatibility_kind']=='original_p58_identity'
    fields=BASE | ({'executable_sha256','window_handle_binds_exact_process'} if full else set())
    compat,kernel=value['compatibility_identity'],value['kernel_identity']
    for identity in (compat,kernel):
        require(type(identity) is dict and identity.keys()==fields,'EXACT_IDENTITY_FIELDS')
        require(type(identity['process_id']) is int and 0<identity['process_id']<=0xffffffff
            and type(identity['session_id']) is int and 0<=identity['session_id']<=0xffffffff,'IDENTITY_NUMERIC_TYPES')
        native.creation_ticks(identity['created_at_utc'])  # Validate calendar; do not use CIM as canonical birth.
        if full:native.validate_identity(identity,1)  # Schema only, not a physical-window check.
    require(all(compat[k]==kernel[k] for k in fields-{'created_at_utc'}),'UNMODIFIED_NONCLOCK_FIELDS')
    raw=value['kernel_creation_filetime_100ns']
    require(type(raw) is str and re.fullmatch('[1-9][0-9]{0,18}',raw) is not None
        and int(raw)<2**63,'LOSSLESS_KERNEL_FILETIME')
    require(native.creation_ticks(kernel['created_at_utc'])==int(raw),'EXACT_KERNEL_CLOCK_NO_TOLERANCE')
    require(type(value['kernel_process_image']) is str and 0<len(value['kernel_process_image'])<=32768
        and '\x00' not in value['kernel_process_image'],'IMAGE_BOUNDARY')
    require(type(value['kernel_window_verified']) is bool,'WINDOW_OBSERVATION_TYPE')
    for key in ('kernel_before_after_same_handle_equal','compatibility_fresh_check_returned',
            'kernel_creation_not_derived_from_cim'):
        require(value[key] is True,'OBSERVATION_NOT_RETURNED')
    for key in ('native_provenance_qualified','native_execution_authorized','p09_complete'):
        require(value[key] is False,'NO_RECORD_PROMOTION')
    return dict(compatibility_identity=dict(compat),kernel_identity=dict(kernel),
        kernel_filetime_100ns=int(raw),physical_native_admission_qualified=False)


def canonical_native_candidate(value):
    observed=decode_record(value)
    require(value['compatibility_kind']=='original_p58_identity' and value['kernel_window_verified']
        and value['kernel_process_image'].casefold()==native.EXECUTABLE.casefold(),
        'OWN_PROCESS_INSPECTION_CANNOT_BE_NATIVE_CANDIDATE')
    # This is candidate DATA, never a startup permit or native provenance proof.
    return dict(observed['kernel_identity'])
