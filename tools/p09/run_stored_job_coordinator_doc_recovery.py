"""Retain276 KeyError; use the actual269 document closure, not absent code-receipt doc pins."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_job_coordinator_sync as origin
latest,checker,prior_sync=origin.latest,origin.checker,origin.prior_sync
shared,c,a,audit,tools,compact=origin.shared,origin.c,origin.a,origin.audit,origin.tools,origin.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-coordinator-doc-recovery277.v1.json'
DRIVER='tools/p09/run_stored_job_coordinator_doc_recovery.py'
DOC_BASE=prior_sync.OUTPUT
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COORDINATOR_DOC_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_JOB_COORDINATOR_DOC_RECOVERY',own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        durable_idempotency_complete=False,P09_product_execution_or_commit=False,actual_cases_reexecuted=0,full919_inputs_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(checker.OUTPUT))
        c.require(q.snapshots[checker.OUTPUT]['sha256']=='f7f8d8d21f6b30665222d40672d2bb2ff129441b2210108dea542833377e87b7'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==919 and passed['total_executed_cases']==9
            and passed['unchanged_lifecycle_cases_reused']==15 and passed['test_scratch_empty'],'EXACT275_COORDINATOR9_LIFECYCLE15_AND919_SOURCE_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        selected=prior_sync.RETAINED|latest.CHANGED|latest.NEW|latest.predecessor.NEW|{
            checker.DRIVER,latest.recovery.DRIVER,latest.recovery.FAILED,latest.recovery.checker.DRIVER,latest.recovery.checker.FAILED,
            latest.predecessor.predecessor.ART,latest.predecessor.predecessor.ART_ROOT,latest.predecessor.predecessor.PREPARE,
            latest.predecessor.predecessor.MODEL,latest.predecessor.predecessor.LIB,latest.predecessor.predecessor.PARENT,latest.predecessor.predecessor.TEST}
        for name in sorted(selected|prior_sync.base.migration_inputs(guard.check)):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_PRODUCT_SQL_TEST_AND_SECURITY_SOURCES_MATCH275')
        cases={'job_v1::'+n for n in latest.predecessor.predecessor.names(q,latest.TEST)};c.require(len(cases)==9,'EXACT_COORDINATOR9_CASE_NAMES');tools.good_step(passed['steps'][0],cases)
        original=compact.unpack(q.json(latest.BASE))
        c.require(q.snapshots[latest.BASE]['sha256']=='78ffabd31f729f59016278be6acb8a2800d141860f0e0404ccb5cb38a287f23f'
            and original['cleanup']and original['total_executed_cases']==15 and original['fresh_inputs']==original['final_fresh_hashes']==914,'EXACT273_LIFECYCLE15_SOURCE_CLOSURE')
        modelcases={latest.predecessor.PREFIX+'tests::'+n for n in latest.predecessor.predecessor.names(q,latest.predecessor.TEST)}|{
            latest.predecessor.PREFIX+'sql::tests::'+n for n in latest.predecessor.predecessor.names(q,latest.predecessor.SQL)}
        c.require(len(modelcases)==15,'EXACT_LIFECYCLE15_CASE_NAMES');tools.good_step(original['steps'][0],modelcases)
        checker.inverse(q,{p['path']:p for p in original['source_pins']})
        for step in passed['steps']+original['steps']:
            j=step['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'273_275_JOBS_TERMINAL_EMPTY_CLOSED')
        plan=compact.unpack(q.json(latest.predecessor.predecessor.OUTPUT))
        c.require(q.snapshots[latest.predecessor.predecessor.OUTPUT]['sha256']=='32c22842f7f39818cc863cfdff99be65bac269ef51381bec7c48b75e65678221'
            and plan['cleanup']and plan['total_executed_cases']==41,'EXACT270_ARTIFACT6_EXPECTED_IDENTITY9_AFFECTED26')
        docs=q.json(DOC_BASE);c.require(q.snapshots[DOC_BASE]['sha256']=='28e2573ddba10bcd7ef4300537ec84cf621d1af36807fab5aac36e85021ca617'
            and docs['cleanup'],'ACTUAL269_PRIOR_DOCUMENT_CLOSURE')
        docpins={p['path']:p for p in docs['source_pins']}
        for name in(origin.PROFILE,origin.PROGRESS,'CURRENT_STATE.md',origin.DRIVER,DRIVER):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index(origin.OLD_CURRENT)
        audit.inverse(current[at:],docpins['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_UNCHANGED')
        blocks=[current[:at]]
        for name in(origin.PROGRESS,origin.PROFILE):
            text=q.text(name);start=text.index(origin.TITLE);end=text.index(origin.OLDTITLE,start);blocks.append(text[start:end]);restored=text[:start]+text[end:]
            if name==origin.PROFILE:
                c.require(restored.count(origin.INTRO_AFTER)==1,'ONE_CURRENT_PROFILE_STATUS_CORRECTED');restored=restored.replace(origin.INTRO_AFTER,origin.INTRO_BEFORE)
            audit.inverse(restored,docpins[name],'ALL_PREVIOUS_DOCUMENT_FEATURE_ROWS_FAILURES_AND_CONTRACTS_UNCHANGED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',q.text(origin.PROGRESS),re.M)))==19,'ALL19_SEARCH_ROWS_RETAINED_WITHOUT_PROMOTION')
        for block in blocks:
            for marker in('ArtifactService SQL23','41pass','StoredJobLifecycleRepository','PreparedStoredJob','run_once','replay','precommit',
                'E0425','lifecycle15pass','914fresh/final914','coordinator9pass','919fresh/final919','신규 고유24개','기존 lifecycle15',
                '119.406/132.782','1.828/14.328','1.641/12.328','375.15/876.22MiB','24.95/26.56%','45.1297/44.6472%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%','모델·합성',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','routing_allowed=false'):
                c.require(origin.tight(marker)in origin.tight(block),'ACCURATE_COORDINATOR_REUSE_FAILURES_METRICS_AND_OPEN_GATES')
        failed=q.json(origin.OUTPUT);c.require(q.snapshots[origin.OUTPUT]['sha256']=='95fe49c237548dd274ce223a63fbd87fed307979731d5453b3f4be9dd5600635'
            and failed['cleanup']and failed['error_type']=='KeyError','ORIGINAL276_DOC_KEYERROR_PRESERVED')
        for pin in failed['source_pins']:
            q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'NO_PRODUCT_TEST_OR_DOCUMENT_EDITS_SINCE276')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_COORDINATOR9_LIFECYCLE15_PRECOMMIT41_AND_DOC_SYNC_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_distinct_cases_this_turn=24,
            retained_precommit_scope_cases=41,all23_migrations_and_all19_search_rows_retained=True,failure271_272_274_276_preserved=True,
            next_work='owned_SQL23_catalog_privilege_runtime_worker_and_restart_campaign_then_qualified_product_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'COORDINATOR_DOC_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
