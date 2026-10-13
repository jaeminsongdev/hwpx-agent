"""P195 r65 document-only consistency; preserve original failed receipts."""
import json
import audit_r07_closing_workload as audit
from sync_pending_r07_review_docs import raw

b=audit.b;c=audit.c
SELF='tools/p09/sync_r07_recovery_progress.py'
RAW='tools/p09/sync_pending_r07_review_docs.py'
DEST='implementation/p09/evidence/p09-195-recovery-progress-doc-sync-run01.v1.json'
REPORT='implementation/p09/P09-195_INDEPENDENT_CLOSING_RECOVERY_REPORT.md'
PRIOR='implementation/p09/source-archive/p09-195-pre-recovery-progress/'
DOCS=(('CURRENT_STATE.md',PRIOR+'CURRENT_STATE.md'),
    ('implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',PRIOR+'P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'))
PROFILE=dict(path=audit.DEST,bytes=18179,
    sha256='ca8d0fa757a27069ba96ce5f4b416adcd387705f9b0cd071c81276e8a3af30a5')


def main():
    audit.require(c.Path.cwd().resolve()==c.ROOT,'DOC_CWD')
    destination=b.s.scoped_path(DEST,fresh=True);owner=b.run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**b.core.flags(),additional_product_child_executed=False,
        additional_heavy_closing_executed=False,original_passed_contract_tests_not_reexecuted=True)
    try:
        owner.admit();q=b.run.pressure.PressureReader(owner)
        for n in (SELF,RAW):q.pin(n)
        audit.require(q.pin(PROFILE['path'])==PROFILE,'DOC_PROFILE_PIN');profile=q.json(PROFILE['path'])
        audit.require(profile['state']=='PASS_RUNTIME_AND_HISTORICAL_SCOPE_COST_INVENTORY_ONLY_NOT_CLOSING_OR_GATE'
            and profile['resource_stop_reason'] is None and profile['resource_watcher_cleanup_confirmed']
            and profile['IO']['finished'] and profile['reused_prior_contract_tests_passed']==176
            and profile['scope_inventory_contract_tests_passed']==4,'DOC_PROFILE_NOT_GATE')
        expected=b.v.pins(profile['bound_input_pins'])
        for n in (audit.SELF,audit.TEST,*audit.recovery.SOURCES):
            audit.require(q.pin(n)==expected[n],'DOC_TESTED_SOURCE_UNCHANGED')
        for pin in (audit.LIGHT,audit.STOP,audit.recovery.STOP,audit.recovery.CASE):
            audit.require(q.pin(pin['path'])==pin,'DOC_FAILURE_AND_SUCCESS_PRESERVED')
        audit.recovery.pending.validate_pending(q.json(audit.recovery.CASE['path']),
            q.json(audit.recovery.STOP['path']),profile['plan'])
        stopped=q.json(audit.STOP['path'])
        audit.require(stopped['state']=='FAILED_NOT_ACCEPTED' and stopped['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and stopped['IO']['finished'] is False,'DOC_NO_RECOVERY_PROMOTION')
        prefixes=[]
        for name,prior in DOCS:
            before=raw(q,prior);after=raw(q,name)
            audit.require(after.endswith(before) and len(after)>len(before),'DOC_EXACT_PRIOR_BYTES')
            prefixes.append(after[:-len(before)])
        audit.require(prefixes[0]==prefixes[1] and prefixes[0].startswith(b'> 2026-10-08 P195')
            and all(x in prefixes[0].decode('utf-8') for x in ('r65','RECOVERY_STOPPED_NOT_ACCEPTED',
                'HOLD_CANDIDATE4','723121152','수용완료3/249','잔여246','미실행245',
                'compiled249=true/full249=false/signed16=false')),'DOC_CURRENT_BOUNDARY')
        text=q.text(REPORT)
        audit.require(all(pin['sha256'] in text for pin in (audit.LIGHT,audit.STOP,PROFILE))
            and all(x in text for x in ('FAILED_NOT_ACCEPTED','176','1271','723121152','600초','214.5276')),'DOC_REPORT')
        q.finish();out.update(state='PASS_P195_RECOVERY_STOP_AND_SCOPE_COST_R65_DOC_SYNC_ONLY_NOT_CLOSING_OR_GATE',
            accepted_individual_cases=3,successful_candidates_requiring_separate_closing=1,
            reused_contract_test_proofs=180,exact_prior_document_bytes_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=b.run.pressure.observation.parent_tail(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','reused_contract_test_proofs','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
