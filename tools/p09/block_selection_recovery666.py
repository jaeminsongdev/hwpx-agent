"""Bind retained 664 observations without replay or historical closure claims."""
import re
import block_selection_probe664 as original

RECEIPT='implementation/p09/evidence/p09-361-block-selection-probe664-native001.v1.json'
RECEIPT_SHA='20027de30f0248fdebcf54de81f639f244cae09c9728b161e5b96b7c9e4eea31'
TRACE=original.DIRECTORY+'/case-trace.json'
TRACE_SHA='ab0a95b0789881ab5da29b4dc5c68b5fbda0458b237178369565857711117f32'

def require(ok,code):
    if not ok:raise ValueError('PROBE666_'+code)

def validate(receipt,trace):
    require(receipt['state']=='FAILED664_SELECTION_DIAGNOSTICS'
        and receipt['error_code']=='XREF_PROBE664_ONE_COMPLETE_DIAGNOSTIC_STOP_NOT_CAPTURE_SUCCESS'
        and receipt['cleanup']is True and receipt['source_capture_executed']is False
        and receipt['native_claim_created']is True and receipt['same_invocation_handoff_consumed']is True,
        'PRESERVED_ORIGINAL_FAILURE')
    qualification=receipt['qualification_worker'];worker=receipt['capture_worker'];result=worker['result']
    require(qualification['exit_code']==0 and qualification['cleanup']is True
        and worker['exit_code']==2 and worker['requests']==13 and worker['cleanup']is True
        and worker['cleanup_pending']is False and worker['io_threads_joined']is True
        and result['error_code']==original.worker_code.EXPECTED_STOP
        and result['diagnostic_only']is True and result['probe_complete']is True
        and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0
        and result['source_capture_executed']is False,'INTENTIONAL_STOP_WITH_CLOSED_NATIVE_ONLY')
    host=worker['handler_summary'];scope=host['protocol']['scope'];schedule=host['block_source_schedule']
    require(host['ready']is True and host['source_case']==1 and host['source_error']is None
        and host['source_primary_error']is None and host['worker_lease_closed']is True
        and scope['closed']is True and scope['stopped']is True and scope['pending_owner_admission']is False
        and scope['finished_cases']==[dict(case_index=1,case_status='failed')]
        and schedule['stopped']is True and schedule['finish_attempted']is True
        and schedule['one_document_returned']is False and schedule['primary_error']is None
        and schedule['cleanup_error']is None,'STOPPED_DIAGNOSTIC_NOT_SOURCE_SUCCESS')
    require(receipt['case_source_boundaries']==[]
        and receipt['capture_boundary']['closed']is False
        and receipt['partial_case_source_boundary']['label']=='case1'
        and receipt['partial_case_source_boundary']['closed']is False,
        'HISTORICAL_CASE_AND_CAPTURE_BOUNDARIES_REMAIN_OPEN')
    require(trace['schema_version']=='hwpx-agent.private.block-selection-probe664-trace/v1'
        and type(trace['case_index'])is int and trace['case_index']==1
        and trace['phase']=='create_bookmarks'and trace['error_code']==original.worker_code.EXPECTED_STOP
        and trace['probe_complete']is True and trace['input_leases_closed']is True
        and trace['cleanup_error']is None and trace['artifacts']=={}and trace['block_ranges']==[]
        and trace['block_content_support_qualified']is False and trace['P09_complete']is False,
        'RETAINED_OBSERVATIONS_NOT_CAPTURE')
    original.diagnostic_producer(trace,scope['retired_sessions'])
    profile=scope['retired_sessions'][0]['startup_profile']
    require(profile['forced_termination_invoked']is False and profile['kill_on_close']is False,
        'NO_FORCED_CLEANUP')
    rows=trace['selection_probe']
    require(type(rows)is list and len(rows)==8 and [v['label']for v in rows]==list(original.LABELS),'EIGHT_FIXED_OBSERVATIONS')
    for row in rows:
        require(set(row)=={'label','read_returned','value','error_kind','hresult'}
            and type(row['read_returned'])is bool,'OBSERVATION_SHAPE')
        if row['read_returned']:
            require(type(row['value'])is dict and row['error_kind']is None and row['hresult']is None,'RETURNED_VALUE')
        else:
            require(row['value']is None and row['error_kind']in('COMException','RuntimeException','InvalidOperationException',
                'ArgumentException','MissingMethodException','OtherException')and type(row['hresult'])is str
                and re.fullmatch(r'0x[0-9A-F]{8}',row['hresult']),'BOUNDED_FAILURE_ONLY')
    # Report observations as recorded, never reinterpret false selection APIs as PASS.
    return dict(observations_recorded=8,diagnostic_producer_bound=True,Native_replayed=False,
        original_failure_reclassified=False,historical_final_hashes_claimed=False,
        original_case_boundary_closed=False,original_capture_boundary_closed=False,
        source_capture_executed=False,selection_API_qualified=False,
        block_content_support_qualified=False,reference_semantics_qualified=False,P09_complete=False)

def original_pins(receipt):
    """Union identical inputs once; conflicting original pins abort recovery."""
    rows={k:{}for k in('source','native','shell','runtime')}
    for name in('qualification_boundary','capture_boundary','partial_case_source_boundary'):
        boundary=receipt[name]
        require(set(boundary['readers'])==set(rows),'EXACT_ORIGINAL_ROOTS')
        for label,reader in boundary['readers'].items():
            require(reader['fresh_inputs']==len(reader['pins'])>0,'COMPLETE_ORIGINAL_PIN_INVENTORY')
            for pin in reader['pins']:
                require(set(pin)=={'path','bytes','sha256'},'PIN_SHAPE')
                old=rows[label].get(pin['path'])
                require(old is None or old==pin,'CONFLICTING_ORIGINAL_PIN')
                rows[label][pin['path']]=pin
    return rows
