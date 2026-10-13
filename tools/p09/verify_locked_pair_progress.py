"""P214 수용/실제case13/원error 보존 및 r78 문서 delta 확인. 새 제품 실행 없음."""
import argparse
import json
import close_borrowed_runtime_pair as pair

p=pair.p;a=pair.a;runner=pair.runner;observation=pair.observation
SELF='tools/p09/verify_locked_pair_progress.py'
PAIR=dict(path='implementation/p09/evidence/locked-r07/p214-case-013-pair-closing-run01.v1.json',
    bytes=34085,sha256='a05a85a61a7caffe91c8c3bf7fa8b5934c9d67c4c6d6d296fbeff56dd67edfaa')
REPORT='implementation/p09/P09-214_LOCKED_COMPOUND_AND_NEXT_RUNTIME_REPORT.md'
HISTORY='implementation/p09/evidence/runtime-progress-r77/'
DOCS=(dict(path='CURRENT_STATE.md',bytes=410269,sha256='33d4cbee54d7bfb5cc089c6c1b49ed6ebe4a550910f9c5a36cae2a7458b4ea8f'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=503901,
        sha256='9c0c9ab2f5c4eebbbc58005a33d2579655f4713639bc33476ac14766dea1d93c'))


def require(ok,code):p.require(ok,'PAIR_DOC_'+code)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p214-pair-doc-sync-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=None
    out=dict(schema_version='hwpx-agent.p09-locked-pair-doc-delta/v1',state='FAILED_NOT_ACCEPTED',**p.r.flags(),
        new_product_or_full_source_frame_executed=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        for pin in (PAIR,pair.SOURCE,pair.BODY,runner.PRIOR,a.documents.CLOSED,p.b.BASE_PREP,p.m.PARENT):
            require(q.pin(pin['path'])==pin,'EXACT_LINKED_EVIDENCE_PINS')
        current=q.json(PAIR['path']);source=q.json(pair.SOURCE['path']);body=q.json(pair.BODY['path'])
        prior=q.json(runner.PRIOR['path']);old_source=q.json(a.documents.CLOSED['path'])
        prep=q.json(p.b.BASE_PREP['path']);compiled=q.json(p.m.PARENT['path'])
        expected=p.v.pins(prep['whole_inputs']);names=compiled['source_test_names'];exe=compiled['compiled_test_executable_pin']
        required=p.v.pins(old_source['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        required.update({name:q.pin(name) for name in (a.SELF,a.TEST,runner.SELF,runner.TEST)})
        extras={name:q.pin(name) for name in runner.EXTRAS}
        plan=pair.qualify(source,body,prior,names,expected,exe,required,extras)
        require(current['schema_version']==pair.SCHEMA and current['state']==pair.PASS
            and current['runtime_plan']==plan and current['pair_closing_contract_tests_passed']==14
            and current['original_source_frame_receipt_pin']==pair.SOURCE and current['original_parent_receipt_pin']==pair.BODY
            and current['prior_compound_pin']==runner.PRIOR and current['resource_stop_reason'] is None
            and current['resource_watcher_cleanup_confirmed'] is True
            and current['IO']['bound_inputs']==current['IO']['final_fresh_hashes']==25 and current['IO']['finished'] is True
            and current['original_runner_overall_accepted'] is False and current['original_runner_error_preserved'] is True,
            'NEW_PAIR13_NOT_ORIGINAL_OVERALL_PASS')
        require(current['pair_consumer_pins']==[q.pin(name) for name in (pair.SELF,pair.TEST)]
            and current['original_executed_controller_pins']==list(extras.values()),'UNCHANGED_TESTED_PAIR_AND_RUNNER_CODE')
        require(prior['compound_consumer_pins']==[q.pin(name) for name in (a.SELF,a.TEST)],'UNCHANGED_COMPOUND_CONSUMER_CODE')
        report=q.text(REPORT);prefixes=[]
        for pin in DOCS:
            archived=HISTORY+pin['path'].split('/')[-1]
            require(q.pin(archived)==dict(pin,path=archived),'SEALED_OLD_DOCUMENT_BYTES')
            before=q.text(archived);after=q.text(pin['path'])
            require(after.endswith(before) and len(after)>len(before),'OLD_HISTORY_PRESERVED')
            prefixes.append(after[:-len(before)])
            old_raw=q.reader._read(archived,parse=True)[1];new_raw=q.reader._read(pin['path'],parse=True)[1]
            require(new_raw.endswith(old_raw),'EXACT_OLD_BYTE_SUFFIX')
        require(prefixes[0]==prefixes[1] and prefixes[0].startswith('> 2026-10-08 P212~P214 locked-compound-runtime-r78 '),
            'IDENTICAL_R78_PREFIX')
        require(all(text in prefixes[0] for text in ('runtime 수용13/249','잔여236(일반230+corpus6)','미closing후보0',
            '다음index14','whole재조정대기10','hostCPUmax34.67%','overall 수용에 사용하지 않았다','P09·A12·A13 OPEN')),
            'EXACT_PROGRESS_AND_ERROR_BOUNDARIES')
        require(all(text in report for text in ('원 STOP/FAILED','원 root의 exit0/PASS','runtime13','전체 성공 본문 중 whole 재조정 대기10',
            'PC 프리즈 원인·해결은 미확정')),'NO_ERROR_OR_GATE_PROMOTION')
        for pin in (PAIR,pair.SOURCE,pair.BODY,runner.PRIOR):require(pin['sha256'] in report,'REPORT_EVIDENCE_HASHES')
        for archived in ('p212-missing-terminal-counter-preimage/accept_locked_runtime_candidate.py',
                'p212-missing-terminal-counter-preimage/test_locked_runtime_compound.py',
                'p213-premature-finalization-preimage/run_borrowed_runtime_r07_case.py',
                'p213-premature-finalization-preimage/test_borrowed_runtime_case.py'):
            q.pin('implementation/p09/evidence/'+archived)
        q.pin(SELF);q.finish()
        out.update(state='PASS_LOCKED_RUNTIME13_PAIR_DOC_SYNC_NOT_WHOLE_OR_GATE',document_revision=78,runtime_plan=plan,
            compound_receipt_pin=runner.PRIOR,pair_receipt_pin=PAIR,actual_body_receipt_pin=pair.BODY,
            original_source_frame_error_preserved=True,exact_prior_document_bytes_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error))
    finally:
        p.b.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=observation.summary(owner)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','document_revision','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
