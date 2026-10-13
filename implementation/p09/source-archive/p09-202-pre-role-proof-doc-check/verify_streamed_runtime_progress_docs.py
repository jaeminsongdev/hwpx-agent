"""Reusable streamed progress/doc verification, never another product execution.

현재 큐를 실제 원 receipt로 다시 검증하며 문서의 동일 prefix와 이전 byte 보존을 확인한다.
검증된212/224 계약의 입력 동일성을 확인해 재사용한다. EXE 재해시/새 child/Gate 승격은 없다.
"""
import argparse
import json
import re
from unittest.mock import patch
import stream_runtime_resume_progress as s
import joined_runtime_resume_progress as joined
from sync_pending_r07_review_docs import raw

p=s.p;r=s.r;c=s.c;b=s.b
SELF='tools/p09/verify_streamed_runtime_progress_docs.py'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--revision',type=int,required=True);ap.add_argument('--report',required=True)
    ap.add_argument('--proof-run',type=int,required=True)
    ap.add_argument('--cpu-inspection');args=ap.parse_args()
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
        common_contracts=sum(proof[k] for k in ('contract_tests_passed','observation_contract_tests_passed',
            'runtime_source_closing_contract_tests_passed','process_cpu_attribution_contract_tests_passed',
            'runtime_resume_contract_tests_passed','streaming_progress_contract_tests_passed'))
        joined_contracts=proof.get('joined_progress_contract_tests_passed',0)
        s.require(common_contracts==212 and joined_contracts in (0,12),'DOC_CLOSED_CONTRACT_GENERATIONS')
        proof_count=common_contracts+joined_contracts
        producer=joined if joined_contracts==12 else s
        s.require(proof['state']=='PASS_RUNTIME_RESUME_PREPARATION_NOT_BODY_OR_WHOLE_OR_GATE'
            and proof['resource_stop_reason'] is None and proof['resource_watcher_cleanup_confirmed']
            and proof['IO']['finished'] and proof['IO']['bound_inputs']==proof['IO']['final_fresh_hashes']
            and len(proof['closing_controller_pins'])==len(producer.CONTROLLERS),
            'DOC_COMPLETE_CONTRACT_PROOF')
        tested=s.v.pins(proof['bound_input_pins'])
        with patch.object(p,'CONTROLLERS',producer.CONTROLLERS):controller=p.controllers(q)
        s.require(all(tested[n]==pin for n,pin in controller.items())
            and s.v.pins(proof['closing_controller_pins'])==controller,'DOC_TESTED_CONTROLLERS_UNCHANGED')
        expected,names,exe=b.baseline(q);engine={n:q.pin(n) for n in (b.SELF,b.TEST)}
        legacy,plan,closing_pins,_=producer.progress(q,expected,names,exe,engine,controller)
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
        s.require(all(text in report for text in (f'수용{count}/249',f'잔여{remaining}',str(proof_count),
            'whole/Gate','프리즈 원인·해결은 미확정')),'DOC_REPORT_CURRENT_SCOPE')
        # 본문에 적힌 각 run의 실제 body/closing을 원 validator와 함께 확인한다.
        for pin in closing_pins:
            s.require(pin['sha256'] in report,'DOC_CLOSING_RECEIPT_HASH')
        if args.cpu_inspection:
            s.require(re.fullmatch(r'implementation/p09/evidence/runtime-r07/p09-[0-9]{3}-case[0-9]{3}-cpu-spike-inspection\.v1\.json',
                args.cpu_inspection),'DOC_INSPECTION_PATH')
            inspected=q.json(args.cpu_inspection);source=inspected['source_receipt_pin']
            s.require(q.pin(source['path'])==source,'DOC_INSPECTION_SOURCE_PIN')
            original=q.json(source['path'])
            s.require(original['state']==s.v.CASE_PASS and inspected['schema_version']=='hwpx-agent.p09-cpu-spike-inspection/v1'
                and inspected['state']=='OBSERVED_CPU_SPIKE_FROM_SAVED_RECEIPT_NOT_CAUSE_OR_GATE',
                'DOC_INSPECTION_SCOPE')
            indices=[i for i,row in enumerate(original['samples']) if row['system_cpu_percent']>=95]
            s.require(indices==inspected['warning_sample_indices'],'DOC_ALL_WARNING_SAMPLES')
            s.require(len(indices)==len(inspected['warning_samples']),'DOC_WARNING_COUNT')
            for selected,index in zip(inspected['warning_samples'],indices):
                s.require(selected['sample_index']==index and all(original['samples'][index][k]==value
                    for k,value in selected.items() if k!='sample_index'),'DOC_WARNING_VALUES')
            pressure=original['owned_source_reader_passes'][1]['near_saturation_read_backpressure']
            s.require(all(pressure[k]==value for k,value in inspected['second_source_read_backpressure'].items()),
                'DOC_ACTUAL_READ_BACKPRESSURE')
            s.require(inspected['CPU_cause_or_PC_freeze_resolution_established'] is False
                and inspected['new_stress_or_product_test_executed_by_inspection'] is False
                and inspected['foreign_processes_requeried_by_inspection'] is False
                and inspected['original_receipt_not_modified'] is True
                and inspected['P09_gate']=='OPEN' and inspected['product_complete'] is False
                and args.cpu_inspection in report,'DOC_NO_SPIKE_CAUSE_PROMOTION')
            out['cpu_spike_inspection_pin']=q.reader.snapshots[args.cpu_inspection]
        q.finish();out.update(state='PASS_STREAMED_RUNTIME_PROGRESS_DOC_SYNC_NOT_NEW_RUNTIME_OR_GATE',
            runtime_plan=plan,legacy_plan=legacy,reused_contract_test_proofs=proof_count,
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
