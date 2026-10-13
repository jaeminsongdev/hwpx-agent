"""P198 r67 metadata/document verification. Never reexecutes a passed test."""
import argparse
import json
import run_runtime_resumable_r07_case as p
from sync_pending_r07_review_docs import raw

c=p.c;b=p.b;r=p.r
SELF='tools/p09/sync_single_runtime_resume_progress.py'
REPORT='implementation/p09/P09-198_SINGLE_RUNTIME_RESUME_REPORT.md'
PRIOR='implementation/p09/source-archive/p09-198-pre-single-runtime-progress/'
DOCS=(('CURRENT_STATE.md',PRIOR+'CURRENT_STATE.md'),
    ('implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',PRIOR+'P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'))
BASE='implementation/p09/evidence/runtime-r07/'
PINS=[dict(path=BASE+name,bytes=size,sha256=digest) for name,size,digest in (
    ('p198-runtime-resume-light-run02.v1.json',49066,'5c6db491340943f81cf01b4f28281817590de24f1e4adc76cb2fc06d6e17242f'),
    ('p198-runtime-resume-preparation-run01.v1.json',49141,'f149e0e90265def09eb8e92dc7ed12bde0317182c61af243d74d7eda975dbda8'),
    ('cases/p190-case-005-attempt-001.json',936745,'cc19fbe61c82168ba7970dbea001b3f1690ddf29d12a9ddd4d3fb26acae2231f'),
    ('p198-case-005-attempt-001-close-01.v1.json',1135501,'f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569'),
    ('p198-runtime-resume-plan-run01.v1.json',54301,'8f4ef7accf5f9ea0710bcb8bebe7ebbc427006a12af9777c372df3d36c09abf1'))]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    p.require(1<=args.run<=99,'DOC_RUN')
    p.require(c.Path.cwd().resolve()==c.ROOT,'DOC_CWD')
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-198-single-runtime-progress-doc-sync-run{args.run:02}.v1.json',fresh=True)
    context=r.observation.Context()
    owner=r.observation.Resources(context);q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**r.flags(),additional_heavy_closing_executed=False,
        original_passed_product_bodies_not_reexecuted=True)
    try:
        owner.admit();q=r.Reader(owner,context);q.pin(SELF);proofs=[]
        for pin in PINS:
            p.require(q.pin(pin['path'])==pin,'DOC_RECEIPT_PIN');proofs.append(q.json(pin['path']))
        light,prep,case,closing,stored_plan=proofs
        tested=p.v.pins(light['bound_input_pins'])
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        control=p.controllers(q)
        p.require(all(tested[n]==pin for n,pin in control.items()),'DOC_CURRENT_TESTED_CONTROLLERS')
        legacy,plan,_,_=p.progress(q,expected,names,exe,engine,control)
        p.require(plan==stored_plan['runtime_plan'] and legacy==stored_plan['legacy_plan']
            and plan['runtime_source_qualified_individual_cases']==5
            and plan['runtime_remaining_individual_cases']==244
            and plan['runtime_remaining_regular_cases']==238 and plan['runtime_remaining_corpus_cases']==6
            and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==2
            and plan['next_runtime_index']==6 and legacy['accepted_individual_cases']==3,'DOC_RECOMPUTED_QUEUE')
        p.require(light['state']==prep['state']=='PASS_RUNTIME_RESUME_PREPARATION_NOT_BODY_OR_WHOLE_OR_GATE'
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed']
            and light['IO']['finished'] and sum(light[k] for k in ('contract_tests_passed',
                'observation_contract_tests_passed','runtime_source_closing_contract_tests_passed',
                'process_cpu_attribution_contract_tests_passed','runtime_resume_contract_tests_passed'))==202,
            'DOC_CONTRACT_PROOF202')
        p.require(prep['selected_case_status']==dict(next_index=5,next_attempt=1)
            and prep['runtime_plan']['runtime_source_qualified_individual_cases']==4,'DOC_ONE_NEW_CASE_ONLY')
        r.validate(closing,case,PINS[2],expected,names,exe,engine,control)
        p.require(case['exit_code']==0 and case['job_final']['active_processes']==0
            and case['job_final']['job_cpu_seconds']==.188 and case['cleanup_confirmed']
            and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==1414
            and closing['IO']['bytes_read']==237768033,'DOC_REAL_SINGLE_CASE_AND_CLOSING')
        for receipt in (case,closing):
            p.require(receipt['process_CPU_attribution']['error_code'] is None
                and receipt['process_CPU_attribution']['CPU_cause_or_PC_freeze_resolution_established'] is False,
                'DOC_NO_FREEZE_CAUSE_PROMOTION')
        prefix=[]
        for name,prior in DOCS:
            before=raw(q,prior);after=raw(q,name)
            p.require(after.endswith(before) and len(after)>len(before),'DOC_EXACT_R66_PREIMAGE')
            prefix.append(after[:-len(before)])
        p.require(prefix[0]==prefix[1] and prefix[0].startswith(b'> 2026-10-08 P198')
            and all(text in prefix[0].decode('utf-8') for text in ('r67','수용5/249','수용3',
                '잔여244','다음index6','237768033','프리즈 원인','compiled249=true/full249=false/signed16=false')),
            'DOC_PREFIX_SCOPE')
        report=q.text(REPORT)
        p.require(all(pin['sha256'] in report for pin in PINS) and all(text in report for text in
            ('수용5/249','수용3','원runtime1413','Job CPU0.188','whole reconciliation','프리즈 해결을 주장하지 않는다')),
            'DOC_REPORT_SCOPE')
        q.finish();out.update(state='PASS_RUNTIME5_LEGACY3_R67_DOC_SYNC_NOT_NEW_RUNTIME_OR_GATE',
            runtime_plan=plan,legacy_plan=legacy,reused_contract_test_proofs=202,
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
