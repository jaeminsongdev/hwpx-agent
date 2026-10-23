"""381: current native-startup blockers and immutable factory lineage; source/docs only, no process replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import inspect_current_crossref_prerequisites as current
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-current-crossref-prerequisites-sync381.v1.json';DRIVER='tools/p09/sync_current_crossref_prerequisites.py'
STATE='CURRENT_STATE.md';REPORT='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
ROOT='implementation/p09/evidence/p09-361-crossref-root-anchor062.v1.json';SESSION='implementation/p09/evidence/p09-361-crossref-session-readiness070.v1.json'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CURRENT_XREF_PREREQUISITE_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CURRENT_XREF_PREREQUISITE_SYNC',own_cpu_selection=selection,
        document_and_changed_source_audit_not_native_or_fresh_runtime_qualification=True,Cargo_Hangul_COM_or_child_process_replayed=False,
        native_startup_qualified=False,fixed_eight_executed=False,Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        external_execution_arrangement_requested_but_no_answer_recorded=True,OS_parent_job_or_security_settings_changed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);observed=q.json(current.OUTPUT);docs=q.json(current.CURRENT);root=q.json(ROOT);session=q.json(SESSION)
        c.require(q.snapshots[current.OUTPUT]['sha256']=='2cc887cfbc1991084ca944c28815dfeb9bfec09fcd8b7be49829d0ea4e4107ca'
            and observed['cleanup']and observed['fresh_inputs']==observed['final_fresh_hashes']==14 and observed['external_final_fresh_hashes']==1,'EXACT380_CURRENT_READONLY_FRESH_OBSERVATION_NO_NATIVE_QUALIFICATION')
        c.require(q.snapshots[current.CURRENT]['sha256']=='2ddadac05cde72decbe2845cc1e984061b4820f170c93e857e3e672d43598047'and docs['cleanup'],'EXACT379_PREVIOUS_CURRENT_STATE_DOC_BASELINE')
        observation=observed['actual_observation'];parent=observed['immediate_parent_job_observation']
        c.require(observation['failed_prerequisites']==['caller_lifecycle_native_safe']and observation['preexisting_hwp_processes']==0 and parent['job_present']
            and parent['flags']==0x2800 and observed['OS_permitted_external_breakaway_eligibility_only']and not observed['native_startup_qualified']
            and not observation['process_created']and not observation['COM_activated']and not observation['permission_dialog_requested'],'NATIVE_LIFECYCLE_FAILED_NOT_PERMISSION_OR_IMAGE_FAILURE')
        c.require(root['error_code']=='XREF_ROOT_ANCHOR_MEASURED_ALL_ANCESTOR_JOBS_REMOVED'and root['cleanup']and not root['actual_Hangul_or_COM']
            and not session['root062_replayed']and not session['fixed_eight_ready_to_execute']and not session['parent_lifecycle_qualified'],'ORIGINAL_ROOT_JOBLESS_FAILURE_AND_UNQUALIFIED_SESSION_PRESERVED_NO_REPLAY')
        pins={p['path']:p for p in observed['source_pins']}
        for path in sorted(current.NATIVE|{current.DRIVER,'tools/p09/named_style_verification_runtime.py'}):q.pin(path);c.require(q.snapshots[path]==pins[path],'ALL_ORIGINAL_NATIVE_FACTORY_GUARDS_AND_CLOSED_BATCH_CODE_UNCHANGED')
        owner=q.text('implementation/p09/tools/sdk-baseline-owned-session.ps1');start=owner.index('function New-P58Owner');end=owner.index('function Open-P58Document',start);body=owner[start:end]
        c.require(body.index("New-Object -ComObject 'HWPFrame.HwpObject.2'")<body.index('$owner.identity=')<body.index('return $owner'),'ORIGINAL_COM_FACTORY_IDENTITY_IS_POST_CREATION_NOT_PREASSIGNED_STARTUP')
        ports=q.text('implementation/p09/tools/crossref-native-case-ports.ps1');start=ports.index("'create_save_session' {");end=ports.index("'source_open'",start);body=ports[start:end]
        c.require(body.index("New-P58Owner 'save'")<body.index('& $State.admit_owned_process'),'PORTS_POST_FACTORY_ADMISSION_NOT_NATIVE_PRE_CREATION_LIMITS')
        old={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 개인정보 탐지의 현재 저장과 읽기 전용 제품'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 실제 CROSSREF 실행 경계 재확인')and state.count(marker)==1,'ONE_CURRENT_NATIVE_READINESS_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_PRODUCT35_SOURCE_FAILURES_QUEUE_AND_PHASE_HISTORY_RETAINED')
        report=q.text(REPORT);q.pin(DRIVER)
        for text in(prefix,report):
            for marker in('380','14fresh/final14','0x2800','kill-on-close','062','070','240','Native011 미승인/미실행','공식158/249','P09/A12/A13 OPEN','목표ACTIVE','CROSSREF8종 NOT_RUN'):
                c.require(marker in text,'READONLY_OBSERVATION_SEPARATED_FROM_NATIVE_AUTHORITY_AND_UNCHANGED_PHASE_BOUNDARIES')
        for marker in('단순한 별도 터미널','사후 관측','preassigned startup','접근 허용은 사용자만','답변은 아직 없으며','실제 실행 전에'):
            c.require(marker in report,'NO_EXTERNAL_TERMINAL_OR_USER_ANSWER_PROMOTED_TO_NATIVE_QUALIFICATION')
        for link in re.findall(r'\]\(([^)]+)\)',report):
            c.require(not link.startswith('http'),'ONLY_LOCAL_CURRENT_READINESS_AND_ORIGINAL_FAILURE_EVIDENCE')
            target=((c.ROOT/REPORT).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_CURRENT_AND_HISTORICAL_EVIDENCE_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_CURRENT_NATIVE_LIFECYCLE_BLOCKERS_DOC_SYNC_NOT_NATIVE_EXECUTION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='qualified_external_native_safe_host_and_preassigned_factory_before_conditional_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'CURRENT_XREF_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
