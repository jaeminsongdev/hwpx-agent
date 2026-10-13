"""P192 serial runtime / shared closing docs; no additional product test."""
import argparse
import base64
import hashlib
import json

import run_shared_resumable_r07_batch as batch

c=batch.c;v=batch.v;run=batch.run;s=batch.s;core=batch.core
SELF='tools/p09/sync_shared_resumable_r07_progress.py'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
ARCHIVE='implementation/p09/source-archive/p09-192-pre-shared-progress/document-preimages.v1.json'
REPORT='implementation/p09/P09-192_SHARED_RESUMABLE_R07_BATCH_REPORT.md'
DEST='implementation/p09/evidence/p09-192-shared-resumable-progress-sync.v1.json'
PREP=dict(path=batch.paths(2)['preparation'],bytes=305109,
    sha256='ad683791ad475ad001f94b26d5d9911bda95d9a2cb3f9bfdf6a896f1aa4f5c91')
CASES=(dict(path=core.DIR+'/p190-case-002-attempt-001.json',bytes=659057,
    sha256='b1b4447f28219bd47afa7f665185c1cd2a5752ef2dd165a401846ca119a8163a'),
    dict(path=core.DIR+'/p190-case-003-attempt-001.json',bytes=701199,
    sha256='eb37b8dc27f5c5646afa5eac627be5a73ae72a26f8c4ee78c5c724a3436830df'))
CLOSING=dict(path=batch.paths(2)['closing'],bytes=898623,
    sha256='4c2b452cd1acfbadfbe46a6e2b5154f6b889a97106a1510e79b4d5b9b2408422')
PLAN=dict(path=batch.paths(4)['plan'],bytes=305929,
    sha256='d6040c0c798e50b3707bf6933379d76e232f22826beb5e6ee384a8a55e4660e3')


def require(ok,code):batch.require(ok,'DOC_'+code)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True)
    args=ap.parse_args();require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(ARCHIVE if args.mode=='archive' else DEST,fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**core.flags(),further_product_test_or_Cargo_SQL_Hangul_child_executed=False,
        new_whole_source_or_EXE_reaudit_executed=False,inherited_whole_before_not_relabelled_fresh=True)
    try:
        resources.admit();q=run.pressure.PressureReader(resources);q.pin(SELF)
        if args.mode=='archive':
            files=[]
            for name in DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'WHOLE_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_PRIOR_R62_DOC_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            for pin in (PREP,*CASES,CLOSING,PLAN):require(q.pin(pin['path'])==pin,'IMMUTABLE_BATCH_RECORDS')
            expected,names,exe=batch.baseline(q)
            prep=q.json(PREP['path']);closing=q.json(CLOSING['path']);plan=q.json(PLAN['path'])
            engine=v.pins(prep['supplemental_scheduler_input_pins'])
            require(prep['state']==batch.PREP_PASS and prep['contract_tests_passed']==154
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
                and prep['current_whole_baseline_inputs_reaudited'] is False
                and prep['inherited_before_is_historical_not_fresh'] is True
                and prep['maximum_cases']==2 and prep['new_case_start_budget_seconds']==300,
                'SHARED_PREP_NOT_NEW_WHOLE_AUDIT')
            require(closing['publisher']=='P192_shared_batch' and closing['accepted_new_case_count']==2
                and closing['sealed_whole_before_anchor']==batch.BASE_CLOSE
                and closing['supplemental_scheduler_before']==closing['supplemental_scheduler_after']==list(engine.values())
                and closing['inherited_before_is_historical_not_new_fresh_audit'] is True
                and closing['IO']['finished'] and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==1480,
                'SUPPLEMENTAL_AND_WHOLE_END_CLOSING')
            rows=[]
            for index,pin in enumerate(CASES,1):
                doc=q.json(pin['path']);v.accept_case(doc,names[index],prep['binding'],closing,expected,pin)
                batch.validate_supplement(doc,expected,engine)
                require(doc['selected_test_names']==[names[index]] and doc['closing_id']==CLOSING['path'],'NEXT_TWO_ONLY')
                rows.append((c.Path(pin['path']).name,doc,pin))
            old=q.json(batch.BASE_CASE['path']);prior=q.json(batch.BASE_CLOSE['path'])
            rows.insert(0,(c.Path(batch.BASE_CASE['path']).name,old,batch.BASE_CASE))
            reconstructed=v.plan(names,expected,exe,rows,{batch.BASE_CLOSE['path']:prior,CLOSING['path']:closing})
            require(plan['plan']==reconstructed and reconstructed['accepted_individual_cases']==3
                and reconstructed['remaining_individual_cases']==246 and reconstructed['remaining_regular_cases']==240
                and reconstructed['remaining_corpus_cases']==6 and reconstructed['next_index']==4
                and plan['resource_stop_reason'] is None and plan['resource_watcher_cleanup_confirmed'],'SKIP3_NEXT4')
            for n,p in engine.items():require(q.pin(n)==p,'EXECUTED_SCHEDULER_UNCHANGED')
            out.update(batch.contracts())
            old_docs=q.json(ARCHIVE);prefixes=[]
            require(old_docs['state']=='WHOLE_PRIOR_R62_DOC_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','ARCHIVE_STATE')
            for name in DOCS:
                _,raw=run.b.parser.preimage(old_docs,name);current=q.text(name).encode()
                require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_DOC_SUFFIX')
                prefixes.append(current[:-len(raw)])
            require(prefixes[0]==prefixes[1] and all(word in prefixes[0] for word in
                (b'r63',b'P192',b'SHARED_BATCH_ACCEPTED',b'SKIP3_NEXT4',b'246',b'240',b'6',
                 b'compiled249=true/full249=false/signed16=false')),'SAME_ACCURATE_PREFIX')
            report=q.text(REPORT);require(all(word in report for word in ('154','3/249','246','240','6','NOT_RUN')),'REPORT_SCOPE')
            q.finish();out.update(state='PASS_SHARED_R07_TWO_RUNTIME_CASES_AND_SKIP3_DOC_SYNC_ONLY_NOT_FULL_OR_GATE',
                accepted_individual_runtime_cases=3,remaining_individual_runtime_cases=246,
                accepted_new_cases=2,reusable_case_receipt_pins=list(CASES),shared_closing_pin=CLOSING,
                resume_plan_pin=PLAN,whole_prior_documents_preserved=True,original_P189_stop_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','accepted_individual_runtime_cases',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2


if __name__=='__main__':raise SystemExit(main())
