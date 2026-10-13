"""Reusable streamed progress/doc verification, never another product execution.

현재 큐를 실제 원 receipt로 다시 검증하며 문서의 동일 prefix와 이전 byte 보존을 확인한다.
검증된212 계약의 입력 동일성을 확인해 재사용한다. EXE 재해시/새 child/Gate 승격은 없다.
"""
import argparse
import json
import re
from unittest.mock import patch
import stream_runtime_resume_progress as s
from sync_pending_r07_review_docs import raw

p=s.p;r=s.r;c=s.c;b=s.b
SELF='tools/p09/verify_streamed_runtime_progress_docs.py'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--revision',type=int,required=True);ap.add_argument('--report',required=True)
    ap.add_argument('--proof-run',type=int,required=True);args=ap.parse_args()
    s.require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=999 and 68<=args.revision<=9999
        and 1<=args.proof_run<=99,'DOC_ARGUMENTS')
    s.require(re.fullmatch(r'implementation/p09/P09-[0-9]{3}_[A-Z0-9_]+_REPORT\.md',args.report),'DOC_REPORT_PATH')
    destination=b.s.scoped_path(f'implementation/p09/evidence/runtime-r07/streamed-doc-sync-run{args.run:03}.v1.json',fresh=True)
    prior=f'implementation/p09/source-archive/runtime-progress-r{args.revision-1}/'
    context=r.observation.Context();owner=r.observation.Resources(context);q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**r.flags(),additional_product_child_executed=False,
        additional_heavy_closing_executed=False,original_passed_product_bodies_not_reexecuted=True)
    try:
        owner.admit();q=r.Reader(owner,context);q.pin(SELF);q.pin('tools/p09/sync_pending_r07_review_docs.py')
        proof_path=p.target('light',args.proof_run);proof=q.json(proof_path)
        s.require(proof['state']=='PASS_RUNTIME_RESUME_PREPARATION_NOT_BODY_OR_WHOLE_OR_GATE'
            and proof['resource_stop_reason'] is None and proof['resource_watcher_cleanup_confirmed']
            and proof['IO']['finished'] and proof['IO']['bound_inputs']==proof['IO']['final_fresh_hashes']
            and sum(proof[k] for k in ('contract_tests_passed','observation_contract_tests_passed',
                'runtime_source_closing_contract_tests_passed','process_cpu_attribution_contract_tests_passed',
                'runtime_resume_contract_tests_passed','streaming_progress_contract_tests_passed'))==212,
            'DOC_CONTRACT_PROOF212')
        tested=s.v.pins(proof['bound_input_pins'])
        with patch.object(p,'CONTROLLERS',s.CONTROLLERS):controller=p.controllers(q)
        s.require(all(tested[n]==pin for n,pin in controller.items()),'DOC_TESTED_CONTROLLERS_UNCHANGED')
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        legacy,plan,closing_pins,_=s.progress(q,expected,names,exe,engine,controller)
        s.require(plan['legacy_whole_accepted_individual_cases']==legacy['accepted_individual_cases']
            and plan['historical_whole_gate_reconciliation_required'] is True
            and all(plan[k] is False for k in ('whole1470_current_fresh_qualified','full249_current_qualified',
                'signed16_current_qualified','product_complete')) and plan['P09_gate']=='OPEN','DOC_NO_GATE_PROMOTION')
        prefixes=[]
        for name in DOCS:
            before=raw(q,prior+c.Path(name).name);after=raw(q,name)
            s.require(after.endswith(before) and len(after)>len(before),'DOC_EXACT_PREVIOUS_BYTES')
            prefixes.append(after[:-len(before)])
        count=plan['runtime_source_qualified_individual_cases'];remaining=plan['runtime_remaining_individual_cases']
        required=(f'r{args.revision}',f'수용{count}/249',f'잔여{remaining}',
            f"일반{plan['runtime_remaining_regular_cases']}+corpus{plan['runtime_remaining_corpus_cases']}",
            f"미closing후보{plan['runtime_successful_candidates_requiring_closing']}",
            f"다음index{plan['next_runtime_index']}",
            f"whole 수용{legacy['accepted_individual_cases']}",
            f"whole미확인성공{plan['all_successful_bodies_pending_whole_reconciliation']}",
            args.report,'compiled249=true/full249=false/signed16=false','프리즈 원인·해결은 미확정')
        s.require(prefixes[0]==prefixes[1] and all(text in prefixes[0].decode('utf-8') for text in required),
            'DOC_CURRENT_PREFIX_SCOPE')
        report=q.text(args.report)
        s.require(all(text in report for text in (f'수용{count}/249',f'잔여{remaining}','212',
            'whole/Gate','프리즈 원인·해결은 미확정')),'DOC_REPORT_CURRENT_SCOPE')
        # 본문에 적힌 각 run의 실제 body/closing을 원 validator와 함께 확인한다.
        for pin in closing_pins:
            s.require(pin['sha256'] in report,'DOC_CLOSING_RECEIPT_HASH')
        q.finish();out.update(state='PASS_STREAMED_RUNTIME_PROGRESS_DOC_SYNC_NOT_NEW_RUNTIME_OR_GATE',
            runtime_plan=plan,legacy_plan=legacy,reused_contract_test_proofs=212,
            contract_proof_pin=q.reader.snapshots[proof_path],verified_runtime_closing_receipt_pins=closing_pins,
            exact_prior_document_bytes_preserved=True,document_revision=args.revision)
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
