"""One current lifecycle and one fixed source document, never an authority issuer."""
import json
from pathlib import Path
import prepared_bookmark_native631 as prior
import block_bookmark_source647_host as host_code
import block_bookmark_source648_worker as worker_code
import block_bookmark_source650_sections as sections
from block_bookmark_source_plan643 import cases as planned_cases

r=prior.r
base=prior.base
SELF='tools/p09/block_bookmark_source650.py'
ENTRY='tools/p09/run_block_bookmark_source650.py'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-bookmark643-source-document001'
NAMES={'created.hwpx','reopened.hwpx','created-page-001.bmp','reopened-page-001.bmp'}
SOURCES=set(prior.base.candidate.SOURCES)|worker_code.SOURCES|{SELF,ENTRY,
    'tools/p09/block_bookmark_source650_sections.py','tools/p09/block_bookmark_source647_host.py',
    'tools/p09/block_bookmark_source648_worker.py','tools/p09/prepared_bookmark631_evidence.py',
    'tools/p09/block_bookmark_source_plan643.py'}

def require(ok,code):
    if not ok:raise ValueError('XREF_BLOCK650_'+code)

def absent():prior.prepared.require_absent(r.c.ROOT,DIRECTORY)

def capture_metadata(reader,host):
    require(host.schedule.done and not host.schedule.stopped and host.scope.closed and host.scope.current is None
        and not host.scope.pending_admission and host.source_case is None and len(host.scope.sessions)==2
        and host.scope.finished==[dict(case_index=1,case_status='returned')],'ONE_CLOSED_CASE_TWO_RETIRED_OWNERS')
    trace=reader.json(DIRECTORY+'/case-trace.json')
    require(trace['schema_version']=='hwpx-agent.private.block-bookmark-source648-trace/v1'
        and type(trace['case_index'])is int and trace['case_index']==1
        and trace['state']=='source_capture_returned_semantics_unqualified'
        and trace['error_code']is None and trace['cleanup_error']is None
        and trace['source_identity_preserved']is True and trace['input_leases_closed']is True
        and trace['block_content_support_qualified']is False and trace['P09_complete']is False,'SOURCE_TRACE_NOT_SEMANTICS')
    prior.evidence.producer(trace,host.scope.sessions)
    require(set(trace['artifacts'])==NAMES,'EXACT_FOUR_ARTIFACTS')
    require(type(trace['block_ranges'])is list and len(trace['block_ranges'])==8,'ALL_EIGHT_SOURCE_RANGES')
    for row,expected in zip(trace['block_ranges'],planned_cases()):
        require(json.dumps(row,sort_keys=True)==json.dumps(dict(case_index=expected['case_index'],selection=expected['selection'],
            action_returned=True,native_source_or_block_content_qualified=False),sort_keys=True),'EXACT_TYPED_RANGE_TRACE')
    pins={name:reader.pin(DIRECTORY+'/'+name)for name in sorted(NAMES|{'case-trace.json'})}
    for name,artifact in trace['artifacts'].items():
        p=pins[name];expected=trace['sessions'][0 if name.startswith('created')else 1]['process']
        require(artifact['pin']['bytes']==p['bytes']and artifact['pin']['sha256']==p['sha256']and artifact['owner']==expected
            and artifact['effect_semantics_qualified']is False,'EXACT_BYTES_PRODUCER_AND_NO_SEMANTIC_PROMOTION')
        require(0<p['bytes']<=(16777216 if name.endswith('.bmp')else 4194304),'FIXED_ARTIFACT_SIZE')
        if name.endswith('.bmp'):
            require(artifact['bitmap']['depth']==24 and artifact['bitmap']['resolution']==96
                and artifact['bitmap']['format']=='BMP'and artifact['bitmap']['visual_semantics_qualified']is False,'FIXED_IMAGE_PROFILE')
    reader.finish()
    return dict(artifacts=pins,native_capture_producer_bound=True,actual_block_XML_mapping_qualified=False,
        block_content_support_qualified=False,reference_semantics_qualified=False,P09_complete=False)

class OneCase(base.CaseInputs):
    def __init__(self,guard,manifest,shell_expected,paths):
        super().__init__(guard,manifest,shell_expected,fixed_capture004=True)
        self.paths=paths
    def begin(self,index):
        require(type(index)is int and index==1 and not self.rows,'ONE_SOURCE_NO_CASE_REPLAY')
        super().begin(index)

def execute(guard,manifest,paths,shell_expected,env,notify,record):
    absent();before=base.installed.current_identity(guard.windows)
    q=base.Boundary(guard,manifest,paths,'block650_current_session',shell_expected,current004=True)
    worker=base.candidate.SessionWorker(guard)
    qualifier=base.session.SessionQualifier(guard,worker,q.native_pin,q.shell_pin)
    attempt={};record['qualification_worker']=attempt
    result=prior.io.run(guard,worker,q.source,worker.start_session_worker,base.SessionHandler(qualifier),
        'hwpx-agent.private.crossref-session-worker-result/v1',env,lambda v:notify('qualification',v),attempt)
    require(attempt['exit_code']==0 and attempt['cleanup']is True,'CURRENT_SESSION_RETURN_AND_CLEANUP_NO_BATCH_ON_FAILURE')
    q.finish();record['qualification_boundary']=q.summary()
    handoff=base.batch.issue_handoff(guard,qualifier,result,q.closed,before,base.installed.current_identity(guard.windows),q.fingerprint)
    guard.advance('capture',lambda:sections.closed_boundary(record['qualification_boundary']))
    absent();current=base.Boundary(guard,manifest,paths,'block650_capture',shell_expected,current004=True)
    cases=OneCase(guard,manifest,shell_expected,paths);full=worker_code.Worker(guard)
    host=host_code.Host(guard,full,handoff,base.installed.current_identity(guard.windows),q.fingerprint,
        cases.native_pin,current.shell_pin,cases.begin,cases.end,notify=lambda v:notify('capture',v))
    attempt={};record['capture_worker']=attempt
    def notice(value):
        # io603 records the original result before calling legacy result_notice.
        # Replace that notice for THIS new profile, not by weakening old io.
        if value.get('state')=='NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP'and isinstance(attempt.get('result'),dict):
            value=worker_code.source_result_notice(attempt['result'])
        notify('capture',value)
    try:
        result=prior.io.run(guard,full,current.source,full.start_fixed_worker,base.BatchHandler(host),worker_code.RESULT,env,notice,attempt)
        require(attempt['exit_code']==0 and attempt['requests']==55 and attempt['cleanup']is True
            and result['state']=='block_source_callbacks_returned_semantics_unqualified'
            and type(result['completed_callback_cases'])is int and result['completed_callback_cases']==1
            and result['planned_cases']==1 and result['planned_block_ranges']==8 and result['retained_live_or_uncertain_owners']==0
            and result['block_content_support_qualified']is False and len(cases.rows)==1 and cases.current is None,'ONE_WHOLE_SOURCE_NO_PARTIAL_PROMOTION')
        require(full.closed and host.scope.closed and host.worker_lease.closed and handoff.consumed,'ALL_OWNER_WORKER_HANDOFF_CLOSED')
        current.finish();require(base.installed.current_identity(guard.windows)==before,'SAME_KERNEL_CREATOR')
        guard.advance('batch_close',lambda:sections.closed_boundary(current.summary())and all(sections.closed_boundary(v)for v in cases.rows))
        artifacts=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        record['artifacts']=capture_metadata(artifacts,host)
        record['artifact_boundary']=dict(fresh_inputs=len(artifacts.snapshots),final_fresh_hashes=artifacts.final_fresh_hashes)
        record['batch_closed_for_final_audit']=True
    finally:
        record.update(capture_boundary=current.summary(),case_source_boundaries=cases.rows,
            partial_case_source_boundary=None if cases.current is None else cases.current.summary(),same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']
