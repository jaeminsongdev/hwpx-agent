"""P215: 원 큐 검증을 재사용한 r79 문서 delta. 제품 재실행/전체 source 읽기 없음."""
import argparse
import json
import resume_generic_locked_runtime as g

p=g.p
SELF='tools/p09/verify_generic_locked_progress.py'
REPORT='implementation/p09/P09-215_GENERIC_LOCKED_RUNTIME_CONTINUATION_REPORT.md'
HISTORY='implementation/p09/evidence/runtime-progress-r78/'
DOCS=(dict(path='CURRENT_STATE.md',bytes=411891,sha256='222ff500b0d550b66f166892c01203743c84a30c161894d382557596a49fdac5'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=505523,
        sha256='bfb8815510ffc2aef7f6b04ccfdd74f7a3d0bc4033aaeed9ac53af6266352d5d'))
PROOFS=(dict(path=p.DIR+'/p215-case-014-run001.v1.json',bytes=2036363,
        sha256='0adc30d144213c49b9aca37a878a8286e4bb4271bfcdd7daf31fd3ffe263c952'),
    dict(path=p.DIR+'/cases/p215-case-014-run001.json',bytes=792014,
        sha256='8beaf52d17fc1061cc43b400747993f1b3764014776ea666561f78f853c1b1da'),
    dict(path=p.DIR+'/p215-case-015-run002.v1.json',bytes=2052380,
        sha256='47282ac819b91c50a9c47a4171e8783610ddd682e078b2531e8d76bfcdf42ab7'),
    dict(path=p.DIR+'/cases/p215-case-015-run002.json',bytes=805843,
        sha256='52f6e875bda1c73ddc35498e8ba5cc67892f757e258b6c2b0d3ff77608113684'))


def require(ok,code):p.require(ok,'GENERIC_DOC_'+code)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p215-generic-doc-sync-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context);q=None;candidate=None
    out=dict(schema_version='hwpx-agent.p09-generic-locked-progress-doc/v1',state='FAILED_NOT_ACCEPTED',
        **p.r.flags(),new_product_or_full_source_frame_executed=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        legacy,base,names,expected,exe,required,extras=g.anchor(q)
        binding=p.v.identity(names,expected,exe)
        plan=g.progress(q,legacy,base,names,required,binding,extras)
        require(plan['runtime_source_qualified_individual_cases']==15 and plan['next_runtime_index']==16
            and plan['runtime_remaining_individual_cases']==234 and plan['runtime_remaining_regular_cases']==228
            and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
            and plan['all_successful_bodies_pending_whole_reconciliation']==12,'EXACT_RUNTIME15_NOT_WHOLE')
        for pin in PROOFS:require(q.pin(pin['path'])==pin,'EXACT_TWO_RUNTIME_PAIR_PINS')
        light=q.json(p.DIR+'/p215-generic-light-run004.v1.json')
        require(light['schema_version']==g.SCHEMA and light['state']==g.LIGHT and light.get('error_code') is None
            and light['selected_test_index']==16 and light['prior_runtime_plan']==plan
            and light['generic_contract_tests_passed']==18 and light['product_worker_invocation_requested'] is False
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'] is True
            and light['preparation_IO']['finished'] is True
            and light['preparation_IO']['bound_inputs']==light['preparation_IO']['final_fresh_hashes']
            and light['extra_frame_controller_pins']==list(extras.values()),'NEXT16_WITHOUT_REEXECUTION')
        require(g.contracts((legacy,plan,names))==18,'CONTRACT18')
        prefixes=[]
        for pin in DOCS:
            archived=HISTORY+pin['path'].split('/')[-1]
            require(q.pin(archived)==dict(pin,path=archived),'EXACT_OLD_R78_DOCUMENT_PIN')
            before=q.text(archived);after=q.text(pin['path'])
            require(after.endswith(before) and len(after)>len(before),'PRESERVED_OLD_DOCUMENT')
            prefixes.append(after[:-len(before)])
            old_raw=q.reader._read(archived,parse=True)[1];new_raw=q.reader._read(pin['path'],parse=True)[1]
            require(new_raw.endswith(old_raw),'EXACT_OLD_BYTE_SUFFIX')
        require(prefixes[0]==prefixes[1]
            and prefixes[0].startswith('> 2026-10-08 P215 generic-locked-runtime-r79 '),'IDENTICAL_R79_PREFIX')
        require(all(s in prefixes[0] for s in ('runtime 수용15/249','잔여234(일반228+corpus6)',
            '미closing후보0','다음index16','whole재조정대기12','보호 중단null','P09·A12·A13 OPEN')),
            'EXACT_DOCUMENT_BOUNDARIES')
        report=q.text(REPORT)
        require(all(s in report for s in ('PC 프리즈 원인·해결은 미확정','원 STOP/FAILED 보존',
            '전체 성공 본문 중 whole 재조정 대기12','CPU 보호 중단 시 자동 재시도 금지')),'NO_GATE_OR_CAUSE_PROMOTION')
        for pin in PROOFS:require(pin['sha256'] in report,'REPORTED_EVIDENCE_HASH')
        for name in (SELF,g.SELF,g.TEST):q.pin(name)
        q.finish()
        candidate=dict(state='PASS_GENERIC_RUNTIME15_DOC_SYNC_NOT_WHOLE_OR_GATE',document_revision=79,
            runtime_plan=plan,generic_contract_tests_passed=18,exact_prior_document_bytes_preserved=True,
            actual_runtime_pair_pins=list(PROOFS),original_failure_receipts_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=p.b.run.original.closed_error(error));candidate=None
    finally:
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes'],
                'FINAL_FRESH_ALL_BOUND_INPUTS')
        g.complete(out,owner,candidate,validate)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','document_revision','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
