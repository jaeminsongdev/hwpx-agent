"""Audit historical run290's actual evidence and local documentation; no runtime requalification.

Run290 already pins675 compile inputs before/after. This document-only audit checks the
immutable receipts, scoped new probe/worker sources and exact document inverse; it does
not repeat a third full compile-input scan or relabel a document check as runtime proof.
"""
import json,re,time
from types import SimpleNamespace as NS
import run_sql23_storage as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-real-storage-sync291.v1.json'
DRIVER='tools/p09/run_sql23_storage_sync.py'
DOC_BASE='implementation/p09/evidence/p09-361-sql23-job-lifecycle-sync287.v1.json'
PROFILE='protocol/migrations/p09-stored-revision-jobs-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md'}
TITLE='## 디스크 AEAD와 SQL23 등록 CAS 완료\n'
OLDTITLE='## SQL23 작업의 실제 claim과 lease\n'
OLD_CURRENT='> 2026-10-21 P09 ACTIVE 최신 SQL23 작업의 실제 claim과 lease'
BEFORE='실제 blob/AEAD/scanner/issuer·SQL23 intent 등록/결과 CAS/성공 완료/확인 유실 복구와 제품 실행 자격은 미완료다.\n'
AFTER='''별도 시험에서 실제 디스크 AEAD·SQL23 의도 등록/결과 CAS/성공 완료와 DB/Rust 재시작 후 커밋 관찰도 확인했다.
입력/route/scanner/validator는 합성이며 확인 유실/unknown 복구·전체 거부 경계·scanner/issuer와 실제 P09 제품 실행 자격은 미완료다.
'''
def tight(text):return ''.join(text.split())
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORAGE_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SQL23_STORAGE_SYNC',own_cpu_selection=selection,current_run_Rust_or_DB_replayed=False,
        current_run_full_compile_input_requalification=False,document_audit_not_runtime_evidence=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_P09_product_or_Native_execution=False,Native011_executed=False,prior_Native_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='d5d44414d97a1cd24158839bcf367d616eabc03ab417abb392d796688cc8a8b8'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==675 and passed['actual_disk_AEAD_artifacts']==6
            and passed['actual_SQL23_registered_CAS_and_success_completion']and passed['actual_wrong_key_denial']
            and passed['actual_DB_restart_replay_and_readonly_commit_recovery'],'EXACT290_REAL_STORAGE_TERMINAL_RUNTIME_PROOF')
        old={p['path']:p for p in passed['source_pins']}
        for name in latest.NEW|{latest.MANIFEST}:
            q.pin(name);c.require(q.snapshots[name]==old[name],'SCOPED_NEW_PROBE_WORKER_AND_PRESERVED_FAILURES_UNCHANGED')
        observation='target/p09-sql23-storage-observations-288.json';observations=q.json(observation)
        c.require(q.snapshots[observation]['sha256']=='4ecdece41e60ddfe95c2981f98651d33171b3f4300a17d1ec54cb0665306c91d'
            and len(observations['probes'])==5 and len(observations['postmasters'])==2 and observations['all_owned_postmasters_normal_stop']
            and all(p['normal_stop']for p in observations['postmasters']),'EXACT290_FIVE_PROBES_AND_TWO_NORMAL_STOPS')
        expected=dict(artifacts=6,available=6,jobs=2,succeeded_jobs=2,successful_records=2,attempts=2,authorizations=0,intents=1,revisions=2,seals=2,head=2)
        c.require(observations['snapshots']==[expected,expected]and observations['blob_snapshots'][0]==observations['blob_snapshots'][1]
            and len(observations['blob_snapshots'][0])==6,'REAL_CIPHERTEXT_AND_DB_COUNTS_PRESERVED_WITHOUT_REEXECUTION')
        c.require(observations['probes'][0]['metadata_artifacts_seeded']==0 and observations['probes'][2]['registered_intent']
            and observations['probes'][2]['success_completion']and observations['probes'][3]['state']=='PASS_REAL_DISK_AES_GCM_WRONG_KEY_REJECTED'
            and observations['probes'][4]['execution_retried']is False and observations['parent_retained_ephemeral_test_keys']
            and observations['synthetic_route_scanner_validator_and_bytes'],'ACTUAL_CRYPTO_CAS_NOT_NATIVE_SCANNER_VALIDATOR_OR_KEY_CUSTODY_QUALIFICATION')
        for step in passed['steps']:
            j=step['owned_job'];limits=j['limits_readback'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']
                and j['last_job_accounting']['active_processes']==0 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==4
                and limits['breakaway_disabled']and limits['kill_on_close'],'BOTH_RUNTIME_JOBS_TERMINAL_WITH_UNCHANGED_PROTECTION')
        docs=q.json(DOC_BASE);c.require(q.snapshots[DOC_BASE]['sha256']=='f092b17424a8f1a1516fdc414ecd54b4dff9cf0b79f8b9b6f9d462c60cbf902d'
            and docs['cleanup'],'EXACT287_PREVIOUS_DOC_CLOSURE');old_docs={p['path']:p for p in docs['source_pins']}
        for name in DOCS|{DRIVER}:q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index(OLD_CURRENT);audit.inverse(current[at:],old_docs['CURRENT_STATE.md'],'ALL_PREVIOUS_STATE_AND_FAILURE_HISTORY_RETAINED');blocks=[current[:at]]
        for name in(PROGRESS,PROFILE):
            text=q.text(name);start=text.index(TITLE);end=text.index(OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if name==PROFILE:c.require(restored.count(AFTER)==1,'ONE_STORAGE_INTRO_UPDATE');restored=restored.replace(AFTER,BEFORE)
            audit.inverse(restored,old_docs[name],'ALL_PREVIOUS_SEARCH_ROWS_AND_CONTRACT_HISTORY_RETAINED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_UNCHANGED')
        for block in blocks:
            for marker in('sql23_storage','LocalEncryptedBlobStore','PreparedStoredJob','합성 artifact 행은0개','E0107','675fresh/final675','5회 probe',
                'SQL23 작업 실행은1회','CryptoFailure','artifact6/available6','job2/성공2','attempt2','authorization0','intent1','revision2/seal2','head2',
                '임시 시험 키','114.422','2.422','1.922','704.79MiB','5.938','3.609','73.33MiB','27.81%','43.2051%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%','입력 bytes/route/scanner/validator는 합성',
                '확인 유실/unknown 복구','공식158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(tight(marker)in tight(block),'ACCURATE_HISTORICAL_STORAGE_SCOPE_RESOURCE_VALUES_AND_OPEN_GATES')
        q.finish();guard.check(force=True);row.update(state='PASS_REAL_SQL23_STORAGE_EVIDENCE_AND_DOC_SYNC_NOT_RUNTIME_REQUALIFICATION_OR_P09_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,prior_runtime_source_inputs_verified_before_after=675,
            prior_real_AEAD_artifacts=6,prior_SQL23_execution_count=1,prior_total_bootstrap_and_SQL23_CAS=2,
            next_work='actual_ack_loss_unknown_recovery_and_negative_boundaries_then_qualified_P09_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'STORAGE_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
