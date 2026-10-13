"""P194 r64 docs only: fresh metadata pins, exact prior-byte suffix, no child."""
import json
import review_pending_r07_closing as review

b=review.batch;c=b.c
SELF='tools/p09/sync_pending_r07_review_docs.py'
DEST='implementation/p09/evidence/p09-194-pending-case004-doc-sync-run01.v1.json'
REPORT='implementation/p09/P09-194_PENDING_CASE004_CLOSING_REPORT.md'
PRIOR='implementation/p09/source-archive/p09-194-pre-pending-progress/'
DOCS=(('CURRENT_STATE.md',PRIOR+'CURRENT_STATE.md'),
    ('implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md',PRIOR+'P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'))
REVIEW=dict(path=review.DEST,bytes=16265,
    sha256='a0789196efcba9e241ec77f2deff0227b427a17a3d601a462a732dfc8dcf5dd9')


def raw(q,name):
    # 원 chunk/rate/scope/parse cap 및 마지막 fresh pass를 그대로 유지한다.
    pin,buffer=q.reader._read(name,parse=True);q.reader._bind(name,pin);return bytes(buffer)


def main():
    review.require(c.Path.cwd().resolve()==c.ROOT,'DOC_CWD')
    destination=b.s.scoped_path(DEST,fresh=True);resources=b.run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**b.core.flags(),additional_product_child_executed=False,
        additional_heavy_closing_executed=False,prior_passed_contract_tests_not_reexecuted=True)
    try:
        resources.admit();q=b.run.pressure.PressureReader(resources);q.pin(SELF)
        review.require(q.pin(REVIEW['path'])==REVIEW,'DOC_REVIEW_PIN');doc=q.json(REVIEW['path'])
        review.require(doc['state']=='PASS_PENDING_CASE004_AND_PRESERVED_STOP_PLAN_ONLY_NOT_CLOSING_OR_GATE'
            and doc['contract_tests_passed']==154 and doc['pending_review_contract_tests_passed']==4
            and doc['IO']['finished'] and doc['resource_stop_reason'] is None
            and doc['resource_watcher_cleanup_confirmed'],'DOC_PRIOR158_METADATA_PASS')
        inputs=b.v.pins(doc['bound_input_pins'])
        for name in (review.SELF,review.TEST):review.require(q.pin(name)==inputs[name],'DOC_REVIEW_CODE_UNCHANGED')
        for pin in (review.CASE,review.STOP):review.require(q.pin(pin['path'])==pin,'DOC_PRESERVED_CASE_AND_STOP')
        review.validate_pending(q.json(review.CASE['path']),q.json(review.STOP['path']),doc['plan'])
        prefixes=[]
        for current,prior in DOCS:
            previous=raw(q,prior);latest=raw(q,current)
            review.require(latest.endswith(previous) and len(latest)>len(previous),'DOC_EXACT_PRIOR_BYTE_SUFFIX')
            prefixes.append(latest[:-len(previous)])
        review.require(prefixes[0]==prefixes[1] and prefixes[0].startswith(b'> 2026-10-08 P194')
            and all(word in prefixes[0].decode('utf-8') for word in
                ('r64','CASE004_PASSED_CLOSING_STOPPED','SKIP3_HOLD_CANDIDATE4','후보1',
                 '다음미실행index5','case004 자동재실행금지','246','245',
                 'compiled249=true/full249=false/signed16=false')),'DOC_IDENTICAL_CURRENT_BOUNDARY')
        report=q.text(REPORT)
        review.require(all(pin['sha256'] in report for pin in (review.CASE,review.STOP,REVIEW))
            and all(word in report for word in ('246','245','--max-cases 1','154','신규4','미수용')),'DOC_REPORT_PIN_SCOPE')
        q.finish();out.update(state='PASS_R64_PENDING_CASE004_DOC_PREFIX_AND_EXACT_PRIOR_SUFFIX_ONLY_NOT_CLOSING_OR_GATE',
            reused_contract_tests_passed=158,accepted_individual_cases=3,successful_candidates_requiring_separate_closing=1,
            whole_prior_document_bytes_preserved=True,original_failed_closing_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.run.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['resource_tail']=b.run.pressure.observation.parent_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','reused_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
