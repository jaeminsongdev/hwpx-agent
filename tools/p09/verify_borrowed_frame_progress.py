"""P211 source-only proof 및 r77 새 문서 delta 검증. 제품/전체 hash 재실행 없음."""
import argparse
import json
import close_borrowed_source_frame as closing
import probe_borrowed_locked_streams as probe

p=closing.p;review=closing.review;observation=closing.observation
SELF='tools/p09/verify_borrowed_frame_progress.py'
NATIVE=dict(path='implementation/p09/evidence/locked-r07/p209-borrowed-stream-probe-run03.v1.json',
    bytes=9211,sha256='408e1a943fab183ee22aae4654fda223d492b213f3830ea86467a93682b2dd6a')
REVIEW=dict(path='implementation/p09/evidence/locked-r07/p210-post-stop-review-run01.v1.json',
    bytes=11713,sha256='d41d0734897a616fa97f0497a8cf04a03f99b8fb6f6381785e02c8a314a9620d')
CLOSED=dict(path='implementation/p09/evidence/locked-r07/p211-borrowed-source-frame-run01.v1.json',
    bytes=1281951,sha256='1f5d45554d2d6c288b5dc602761ffcebc7d15ee1b8be33784e7df0b5e54d8c51')
REPORT='implementation/p09/P09-211_POST_STOP_INPUT_IO_OPTIMIZATION_REPORT.md'
HISTORY='implementation/p09/evidence/runtime-progress-r76/'
DOCS=(dict(path='CURRENT_STATE.md',bytes=408696,sha256='74edf969b10f4cfd0688c58713c667427eeef5f5719cd82534673e0824cf3d99'),
    dict(path='implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',bytes=502328,
        sha256='4f267f60b576915172db7b288fe3fff81fe908b246db54bda7ec376e070884e0'))


def require(ok,code):closing.require(ok,'DOC_DELTA_'+code)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    root=p.c.ROOT;require(p.c.Path.cwd().resolve()==root and 1<=args.run<=99,'CWD_RUN')
    destination=root/f'{p.DIR}/p211-borrowed-frame-doc-sync-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT_ONLY')
    context=observation.Context();owner=observation.Resources(context);q=None
    out=dict(schema_version='hwpx-agent.p09-borrowed-frame-progress-doc-delta/v1',state='FAILED_NOT_ACCEPTED',
        **p.r.flags(),additional_product_body_or_full_source_executed=False)
    try:
        owner.admit();q=p.qualification.Reader(owner,context)
        for pin in (review.FRAME,review.BODY,NATIVE,REVIEW,CLOSED):require(q.pin(pin['path'])==pin,'EXACT_RECEIPT_PIN')
        original=q.json(review.FRAME['path']);body=q.json(review.BODY['path']);result=review.review(original,body)
        reviewed=q.json(REVIEW['path']);require(reviewed['review']==result
            and reviewed['review_contract_tests_passed']==12 and reviewed['resource_stop_reason'] is None
            and reviewed['metadata_IO']['bound_inputs']==reviewed['metadata_IO']['final_fresh_hashes']==4,
            'REVIEW_NOT_RUNTIME_ACCEPTANCE')
        full=q.json(CLOSED['path']);required=p.v.pins(original['source_frame']['actual_byte_boundaries'][0]['actual_byte_pins'])
        extras={name:q.pin(name) for name in closing.EXTRAS}
        require(full['extra_controller_pins']==list(extras.values()),'CURRENT_CONTROLLER_PINS_EQUAL_FULL_FRAME')
        required.update(extras);closing.validate(full,required)
        native=q.json(NATIVE['path']);require(native['borrow_contract_tests_passed']==24
            and native['state']=='PASS_SMALL_NATIVE_BORROWED_STREAMS_NOT_FULL_RUNTIME_PRODUCT_OR_GATE'
            and native['resource_stop_reason'] is None,'SMALL_NATIVE_PROOF')
        require(p.v.pins(native['source_pins'])=={name:q.pin(name) for name in probe.SOURCES},'LATEST_NATIVE_HELPERS')
        report=q.text(REPORT)
        prefixes=[]
        for pin in DOCS:
            archived=HISTORY+pin['path'].split('/')[-1]
            require(q.pin(archived)==dict(pin,path=archived),'EXACT_PRIOR_DOCUMENT_PIN')
            before=q.text(archived);after=q.text(pin['path'])
            require(after.endswith(before) and len(after)>len(before),'PRIOR_DOCUMENT_TEXT_PRESERVED')
            prefixes.append(after[:-len(before)])
            # text의 개행 정규화만으로 원 byte 보존을 대신하지 않는다.
            reader=q.reader;old_bytes=reader._read(archived,parse=True)[1];new_bytes=reader._read(pin['path'],parse=True)[1]
            require(new_bytes.endswith(old_bytes),'EXACT_PRIOR_DOCUMENT_BYTES_PRESERVED')
        require(prefixes[0]==prefixes[1] and prefixes[0].startswith('> 2026-10-08 P208~P211 borrowed-input-frame-r77 '),
            'IDENTICAL_R77_PREFIX')
        require(all(text in prefixes[0] for text in ('runtime 수용11/249','잔여238(일반232+corpus6)','semantic 후보1개',
            '1480입력/306디렉터리','hostCPUmax51.33%','ownmax0.587084%','P09·A12·A13 OPEN')),
            'EXACT_PROGRESS_WITH_PENDING_CANDIDATE')
        require(all(text in report for text in ('runtime 수용 11/249','프리즈 원인 및 해결은 미확정',
            '성공한 본문 1~12 재실행 금지','P211 actual run01','source frame','NOT_RUN')),'REPORT_NO_PROMOTION')
        for pin in (review.FRAME,review.BODY,NATIVE,REVIEW,CLOSED):require(pin['sha256'] in report,'RECEIPT_PIN_IN_REPORT')
        q.pin(SELF);q.finish()
        out.update(state='PASS_BORROWED_SOURCE_FRAME_DOC_DELTA_NOT_RUNTIME_WHOLE_OR_GATE',document_revision=77,
            exact_prior_document_bytes_preserved=True,semantic_pending_candidates=1,runtime_accepted_count=11,
            runtime_acceptance_changed=False,current_controller_pins=list(extras.values()),
            original_failed_frame_pin=review.FRAME,original_stopped_parent_pin=review.BODY,
            borrowed_full_source_frame_pin=CLOSED,report_pin=q.reader.snapshots[REPORT])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=p.b.run.original.closed_error(error)
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
