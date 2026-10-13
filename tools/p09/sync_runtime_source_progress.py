"""P196/P197 r66 evidence/document synchronization, not another runtime closing."""
import json
import runtime_source_closing_r07 as r
import process_cpu_attribution as attribution
from sync_pending_r07_review_docs import raw

c=r.c;b=r.b
SELF='tools/p09/sync_runtime_source_progress.py'
DEST='implementation/p09/evidence/p09-197-runtime-progress-doc-sync-run01.v1.json'
REPORT='implementation/p09/P09-196_RUNTIME_CLOSING_AND_CPU_ATTRIBUTION_REPORT.md'
PRIOR='implementation/p09/source-archive/p09-197-pre-runtime-progress/'
DOCS=(('CURRENT_STATE.md',PRIOR+'CURRENT_STATE.md'),
    ('implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',PRIOR+'P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'))
CLOSE=dict(path=r.destination('close',4,1,1),bytes=1160181,
    sha256='c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd')
PLAN=dict(path=r.destination('plan',4,1,1),bytes=48223,
    sha256='d1a5bdf9f0bf1ef46dfab08cc1a874726d5784bdfb949ad6fd01b45f51a85020')
LIGHT=dict(path=r.destination('light',4,1,2),bytes=44397,
    sha256='ddbf864d61054a1df58a41dce2ee928af4a8456cc0262a7b74d7e0426949d586')
BASELINE=dict(path='implementation/p09/evidence/p09-197-process-cpu-baseline-run01.v1.json',bytes=24219,
    sha256='2b7e6a6b9ce9f431a44279b42aa3e1d9240b64fefef96a16aa5ada45fb599ca2')


def main():
    r.require(c.Path.cwd().resolve()==c.ROOT,'DOC_CWD')
    destination=b.s.scoped_path(DEST,fresh=True);context=r.observation.Context()
    owner=r.observation.Resources(context);q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**r.flags(),additional_heavy_closing_executed=False,
        original_passed_product_bodies_not_reexecuted=True)
    try:
        owner.admit();q=r.Reader(owner,context);q.pin(SELF)
        proofs={}
        for pin in (CLOSE,PLAN,LIGHT,BASELINE):
            r.require(q.pin(pin['path'])==pin,'DOC_RECEIPT_PIN');proofs[pin['path']]=q.json(pin['path'])
        closing=proofs[CLOSE['path']];light=proofs[LIGHT['path']];stored_plan=proofs[PLAN['path']]
        bound=r.v.pins(closing['bound_input_pins'])
        for name in (r.SELF,r.TEST,r.observation.SELF,r.observation.TEST,
                attribution.SELF,attribution.TEST,'tools/p09/run_attributed_runtime_closing.py'):
            r.require(q.pin(name)==bound[name],'DOC_TESTED_SOURCE_PIN')
        r.require(light['state']=='PASS_RUNTIME_SOURCE_CLOSING_CONTRACTS_AND_PLAN_ONLY_NOT_WHOLE_OR_GATE'
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed']
            and light['IO']['finished'] and sum(light[k] for k in ('contract_tests_passed',
                'observation_contract_tests_passed','runtime_source_closing_contract_tests_passed',
                'process_cpu_attribution_contract_tests_passed'))==188,'DOC_CONTRACT_PROOF188')
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        controller=r.controllers(q);legacy,plan,_=r.progress(q,expected,names,exe,engine,controller)
        r.require(stored_plan['runtime_plan']==plan and stored_plan['legacy_plan']==legacy
            and legacy['accepted_individual_cases']==3
            and plan['runtime_source_qualified_individual_cases']==4
            and plan['runtime_remaining_individual_cases']==245
            and plan['runtime_remaining_regular_cases']==239 and plan['runtime_remaining_corpus_cases']==6
            and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['next_runtime_index']==5,'DOC_RECOMPUTED_CURRENT_PLAN')
        observed=closing['metadata_observation']['process_CPU_attribution']
        r.require(closing['state']==r.PASS and closing['IO']['finished']
            and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==1420
            and closing['IO']['bytes_read']==253734505 and observed['error_code'] is None
            and observed['completed_intervals']==67
            and observed['CPU_cause_or_PC_freeze_resolution_established'] is False,'DOC_ACTUAL_SCOPE_NOT_CAUSE')
        prefix=[]
        for name,prior in DOCS:
            before=raw(q,prior);after=raw(q,name)
            r.require(after.endswith(before) and len(after)>len(before),'DOC_EXACT_R65_PREIMAGE')
            prefix.append(after[:-len(before)])
        r.require(prefix[0]==prefix[1] and prefix[0].startswith(b'> 2026-10-08 P196/P197')
            and all(x in prefix[0].decode('utf-8') for x in ('r66','수용4/249','수용3/249',
                '잔여245','whole','253734505','프리즈 원인','compiled249=true/full249=false/signed16=false')),
            'DOC_PREFIX_SAME_SCOPE')
        report=q.text(REPORT)
        r.require(all(pin['sha256'] in report for pin in (CLOSE,PLAN,LIGHT,BASELINE))
            and all(x in report for x in ('수용4/249','수용3/249','기존 runner','원인 및 해결은 미확정')),
            'DOC_REPORT_SCOPE')
        q.finish();out.update(state='PASS_RUNTIME4_LEGACY3_R66_DOC_SYNC_NOT_NEW_CLOSING_OR_GATE',
            runtime_plan=plan,legacy_plan=legacy,reused_contract_test_proofs=188,
            exact_prior_document_bytes_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','reused_contract_test_proofs','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
