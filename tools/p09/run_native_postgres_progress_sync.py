"""Fresh source/evidence/document closure for native PG catalogue/restart, no DB/Cargo replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_native_postgres_ascii_campaign as latest
import run_stored_job_coordinator_doc_recovery as previous_docs
shared,c,a,tools,compact=latest.shared,latest.c,latest.a,latest.tools,latest.compact
audit=latest.origin.runner.core.audit
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-progress-sync283.v1.json'
DRIVER='tools/p09/run_native_postgres_progress_sync.py'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
TITLE='## 네이티브 PostgreSQL의 SQL 적용과 재시작\n'
OLDTITLE='## SQL23 작업 처리와 1회성 coordinator\n'
CURRENT_OLD='> 2026-10-21 P09 ACTIVE 최신 SQL23 작업 처리와 1회성 coordinator'
BEFORE='''Rust는 이 precommit Receipt를 실제 저장하며, SQL23은 Result 원본과 영속 job 결속을 위한 미적용 구현이다.
SQL23은 여전히 구문/실행 미검증·미적용이다. ArtifactService SQL23 profile·전용 RevisionService
connector·CAS 전 등록 callback·1회성 typed job coordinator를 구현하고 모델/서비스 component를 검증했다.
실제 DB의 catalog/권한·worker·함수·trigger·claim/lease/완료·중단/재시작과 제품 실행 자격은 미완료다.
'''
AFTER='''Rust는 이 precommit Receipt를 실제 저장하며, SQL23은 Result 원본과 영속 job 결속을 위한 별도 구현이다.
PostgreSQL18.6 전용 시험 DB에서 migration1..23을 실제 적용하고 버전/SHA와 정상 재시작 보존을 확인했다.
ArtifactService SQL23 profile·전용 RevisionService connector·CAS 전 등록 callback·1회성 typed job
coordinator의 모델/서비스 component는 통과했다. 실제 애플리케이션 계정 admission·RLS/권한 거부·
worker·job 함수/trigger·등록/CAS·완료/확인 유실 복구와 제품 실행 자격은 미완료다.
'''
def tight(value):return ''.join(value.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NATIVE_PG_DOC_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NATIVE_POSTGRES_PROGRESS_SYNC',own_cpu_selection=selection,
        current_run_actual_database_or_Cargo_replayed=False,actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_application_role_admission_or_job_functions=False,
        previous_SQL23_applied_only_in_owned_test_database=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='73a13f51e784232e0d2b9920d3c647f578063b3655a3b4d730b30641a4ae7669'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==181 and passed['clean_restart_verified']
            and passed['actual_SQL23_applied_in_owned_test_database']and passed['previous_Rust249_or_model10_reexecuted']==0,'EXACT282_ASCII_SQL23_RESTART_SOURCE_CLOSURE')
        for pin in passed['source_pins']:
            q.pin(pin['path'])
            if pin['path']not in DOCS:c.require(q.snapshots[pin['path']]==pin,'ALL_NATIVE_RUNTIME_SQL23_CLUSTER_AUTH_DIAGNOSTIC_AND_GUARD_INPUTS_UNCHANGED')
        result=passed['steps'][0]['result'];c.require(result['migrations_applied']==list(range(1,24))and result['normal_restart_verified']and result['initdb_ascii_succeeded']
            and result['runtime_files_copied']==1583 and result['runtime_bytes_copied']==147885345 and len(result['postmasters'])==2
            and all(p['normal_stop']for p in result['postmasters'])and len(result['cluster_attestations'])==2
            and result['actual_application_role_admission_or_job_functions']is False,'EXACT_OWNED_SQL_AND_RESTART_NOT_APPLICATION_JOB_AUTHORITY')
        for pin in result['migration_inputs']:c.require(q.snapshots[pin['path']]==pin,'ALL23_MIGRATIONS_UNCHANGED_SINCE_ACTUAL_APPLICATION')
        for attestation in result['cluster_attestations']:
            c.require(attestation['listen']=='127.0.0.1'and attestation['version']==180006 and attestation['hba_clean']and attestation['scram_local']and attestation['no_trust']
                and attestation['fsync']==attestation['sync_commit']=='on','TWO_EXACT_SCRAM_LOOPBACK_DURABLE_STARTS')
        runtime=compact.unpack(q.json(latest.origin.RUNTIME));c.require(q.snapshots[latest.origin.RUNTIME]['sha256']=='cf772540317b4521d565ea3f9662e7a213f7b1e2e8d82b47194a396e3bd86682'
            and runtime['cleanup']and runtime['model_cases']==12 and runtime['versions_checked']==3 and runtime['fresh_inputs']==runtime['final_fresh_hashes']==156,'EXACT279_ARCHIVE_MODELS12_VERSION3')
        fail=compact.unpack(q.json(latest.origin.OUTPUT));c.require(q.snapshots[latest.origin.OUTPUT]['sha256']=='359ca1846f619fddb19ff9a4960899d4dbdd504ede8d53daca985534b5d78d05'
            and fail['cleanup']and fail['steps'][0]['result']['tests_run']==10 and fail['steps'][0]['result']['failures']==[]
            and fail['steps'][1]['result']['stage']=='initialize_new_reject_auth_cluster','ORIGINAL280_FAILURE_AND_REUSED10_MODELS')
        diagnostic=compact.unpack(q.json(latest.DIAGNOSTIC));c.require(q.snapshots[latest.DIAGNOSTIC]['sha256']=='b83019bfbcd0a6ae4bdaabb866f7455bb6a968c45af1c335effa150ea999f314'
            and diagnostic['cleanup']and 'invalid byte sequence'in diagnostic['diagnostic_result']['diagnostics']['first_error_sanitized'],'EXACT281_UTF8_PATH_DIAGNOSTIC')
        for proof in(runtime,fail,diagnostic,passed):
            for step in proof['steps']:
                job=step['owned_job'];limits=job['limits_readback'];c.require(job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                    and job['last_job_accounting']['active_processes']==0 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==4
                    and limits['active_process_limit']==16 and limits['breakaway_disabled']and limits['kill_on_close'],'ALL_OWNED_NATIVE_TREES_CLOSED_UNDER_UNCHANGED_LIMITS')
        docs=q.json(previous_docs.OUTPUT);c.require(q.snapshots[previous_docs.OUTPUT]['sha256']=='797dffe3d8535703536d5d99e976976d885693d2f0ceb5b4cc5e7ac04ce3db6d'
            and docs['cleanup'],'EXACT277_PREVIOUS_DOCUMENT_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        for path in DOCS|{DRIVER}:q.pin(path)
        current=q.text('CURRENT_STATE.md');at=current.index(CURRENT_OLD);audit.inverse(current[at:],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED');blocks=[current[:at]]
        for path in(PROGRESS,PROFILE):
            text=q.text(path);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if path==PROFILE:
                c.require(restored.count(AFTER)==1,'ONE_CURRENT_TEST_DATABASE_STATUS_UPDATE');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old[path],'ALL_PREVIOUS_SEARCH_CONTRACTS_SERVICE_BOUNDARIES_AND_FAILURES_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_RETAINED_NO_ACCEPTANCE_PROMOTION')
        for block in blocks:
            for marker in('PostgreSQL18.6','1583','147885345bytes','384620317bytes','e2246ba91d22345bc3d017586c09ede52d9df180b1eeb480f050445f1cad84e2',
                'vendor 서명/checksum 자격은 아니다','모델12pass','156fresh/final156','모델10pass','0xb0','D:/devdata/hwpx-agent-p09-pg18-ascii-282',
                'migration1..23 실제 적용','전후 버전/SHA23개','정상 종료/재시작 뒤 표식 보존','실제 함수 내부 SQL/권한/제품 실행의 완료 판정은 아니다',
                '32.625','8.500','5.953','54.45MiB','14.07%','45.7678%','181fresh/final181','active0/empty/handle closed',
                'CPU cap6.25%','private8%/stop7%','RAM/commit95%','계정 admission','공식158/249','잔여91','next165','P09/A12/A13 OPEN',
                'CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(block),'ACCURATE_ACTUAL_SQL_RESTART_SCOPE_RESOURCE_AND_OPEN_GATE_STATUS')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE_POSTGRES_SQL23_RESTART_EVIDENCE_AND_DOC_SYNC_NOT_APP_JOB_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_model_cases12_and10=22,actual_prior_version_commands=3,actual_prior_migrations=23,actual_prior_normal_restarts=1,
            next_work='actual_SQL23_service_role_admission_worker_registered_job_CAS_and_failure_recovery_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NATIVE_PG_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
