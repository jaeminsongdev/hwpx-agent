"""Reconcile35 total/32 profile calls and sync actual admission scope; no Rust/DB replay."""
import collections,json,re,time
from types import SimpleNamespace as NS
import run_sql23_service_admission as latest
shared,c,a,tools,compact=latest.shared,latest.c,latest.a,latest.tools,latest.compact
audit=latest.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-service-admission-sync285.v1.json'
DRIVER='tools/p09/run_sql23_service_admission_sync.py'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
TITLE='## SQL23 서비스 계정의 실제 접속과 거부\n'
OLDTITLE='## 네이티브 PostgreSQL의 SQL 적용과 재시작\n'
OLD_CURRENT='> 2026-10-21 P09 ACTIVE 최신 네이티브 PostgreSQL의 SQL 적용과 재시작'
BEFORE='''coordinator의 모델/서비스 component는 통과했다. 실제 애플리케이션 계정 admission·RLS/권한 거부·
worker·job 함수/trigger·등록/CAS·완료/확인 유실 복구와 제품 실행 자격은 미완료다.
'''
AFTER='''coordinator의 모델/서비스 component는 통과했다. 두 서비스 계정의 실제 admission·Artifact 행 RLS와
고정 tenant/subject의6개 검사·권한/메타데이터 변조15개의 거부/복구도 확인했다.
실제 blob/AEAD/scanner/issuer·worker 등록/lease·job 함수/trigger의 실제 실행·등록/CAS·
완료/확인 유실/재시작 복구와 제품 실행 자격은 미완료다.
'''
def tight(text):return ''.join(text.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SQL23_ADMISSION_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SQL23_ADMISSION_SYNC',own_cpu_selection=selection,
        current_run_actual_Rust_or_DB_replayed=False,actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_worker_or_registered_CAS=False,actual_product_execution=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='9aa1b8178204f93d533e4166b57bd67c779379aff011e5209895d6fbb93cf5e8'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==224 and passed['actual_fault_cases']==15
            and passed['actual_metadata_scope_checks']==6,'EXACT284_REAL_SERVICE_ADMISSION_SCOPE6_FAULT15_SOURCE_CLOSURE')
        for pin in passed['source_pins']:
            q.pin(pin['path'])
            if pin['path']not in DOCS:c.require(q.snapshots[pin['path']]==pin,'ALL_COMPILED_THREE_PACKAGE_SOURCES23_MIGRATIONS_PROBE_FIXTURES_AND_NATIVE_GUARDS_UNCHANGED')
        observation_path='target/p09-sql23-role-observations-284.json';observations=q.json(observation_path)
        c.require(q.snapshots[observation_path]['sha256']=='58f5e9d0ddf490ba3f8e348120c8034ad7b0e36df29a782685e5f364b34f51e4'
            and observations['all_owned_postmasters_normal_stop']and len(observations['postmasters'])==1 and observations['postmasters'][0]['normal_stop'],
            'EXACT284_CLOSED_OBSERVATION_AND_NORMAL_POSTMASTER_STOP')
        expected_modes={'--baseline':(True,True),'--behavior':(True,True),'--artifact-denied':(False,True),'--revision-denied':(True,False),'--both-denied':(False,False)}
        profiles=[p for p in observations['probes']if p.get('mode')in expected_modes]
        admins=[p for p in observations['probes']if'mode'not in p]
        c.require(len(observations['probes'])==35 and len(profiles)==32 and len(admins)==3 and passed['actual_profile_probe_calls']==35,'ORIGINAL284_35_LABEL_IS_TOTAL_NOT32_PROFILE_CALLS')
        c.require(collections.Counter(p['mode']for p in profiles)==collections.Counter({'--baseline':16,'--behavior':1,'--artifact-denied':4,'--revision-denied':8,'--both-denied':3}),
            'EXACT32_POSITIVE_NEGATIVE_AND_RESTORED_PROFILE_CALLS')
        for p in profiles:c.require(p['state']=='PASS_SQL23_PROFILE_EXPECTATION'and(p['artifact_admitted'],p['revision_admitted'])==expected_modes[p['mode']]
            and p['actual_product_worker_or_CAS']is False,'ACTUAL_EACH_PROFILE_OUTCOME_MATCHES_ITS_SPECIFIC_FAULT')
        c.require([p['actual_metadata_scope_checks']for p in profiles if p['mode']=='--behavior']==[6],'SIX_ACTUAL_METADATA_SCOPE_AND_ARTIFACT_ROW_RLS_CHECKS')
        faults=set(observations['faults_verified']);c.require(len(faults)==15 and {'deny_'+n for n in faults}=={p['label']for p in profiles if p['label'].startswith('deny_')}
            and {'restored_'+n for n in faults}=={p['label']for p in profiles if p['label'].startswith('restored_')},'ALL15_FAULTS_HAVE_ACTUAL_DENIAL_AND_RESTORED_BASELINE')
        for step in passed['steps']:
            job=step['owned_job'];limits=job['limits_readback'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==4
                and limits['breakaway_disabled']and limits['kill_on_close'],'BUILD_AND_ACTUAL_SERVICE_JOBS_TERMINAL_WITH_UNCHANGED_LIMITS')
        docs=q.json(latest.DOC_BASE);c.require(q.snapshots[latest.DOC_BASE]['sha256']=='c8a8c7e3e39091f3ea396edacdc3536d307e47962a6dcebc5af7c1f8166f8420'
            and docs['cleanup'],'EXACT283_PREVIOUS_DOCUMENT_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for name in DOCS|{DRIVER}:q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index(OLD_CURRENT)
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURE_EVIDENCE_UNCHANGED');blocks=[current[:at]]
        for name in(PROGRESS,PROFILE):
            text=q.text(name);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if name==PROFILE:
                c.require(restored.count(AFTER)==1,'ONE_CURRENT_ADMISSION_SCOPE_RECONCILED');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old[name],'ALL_PREVIOUS_SEARCH_FEATURES_NATIVE_HISTORY_AND_CONTRACTS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_UNCHANGED_NO_ACCEPTANCE_PROMOTION')
        for block in blocks:
            for marker in('p09_sql23_admission','LocalPostgresMetadataRepository::connect_schema23_diagnosed','LocalPostgresStoredRevisionJobsRepository::connect',
                '합성 SQL 메타데이터','prosrc 해시','35회','실제 접속 판정은32회','15개 변조','actual_profile_probe_calls=35','224fresh/final224',
                '55.313','1.813','0.984','311.95MiB','11.406','8.906','62.76MiB','25.05%','46.1495%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
                '실제 blob/AEAD/scanner/issuer','worker 등록/lease','공식158/249','잔여91','next165','P09/A12/A13 OPEN',
                'CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(block),'ACCURATE_REAL_ADMISSION_SCOPE_COUNT_RECONCILIATION_RESOURCES_AND_OPEN_GATES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_SQL23_ADMISSION_SCOPE6_FAULT15_COUNT_RECONCILIATION_AND_DOC_SYNC_NOT_JOB_OR_P09_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,actual_prior_probe_calls=35,actual_prior_profile_calls=32,
            actual_prior_admin_fixture_body_calls=3,original284_count_label_preserved_and_classified=True,
            actual_prior_fault_denials_and_restorations=15,actual_prior_metadata_scope_checks=6,
            next_work='genuine_worker_and_SQL23_job_claim_lease_registered_CAS_completion_unknown_restart_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SQL23_ADMISSION_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
