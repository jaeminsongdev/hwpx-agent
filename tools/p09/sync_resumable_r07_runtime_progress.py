"""P191 accepted exact-one/runtime resume documents; no further test launcher."""
import argparse
import base64
import hashlib
import json

import run_resumable_r07_case as case

c=case.c;v=case.v;run=case.run;s=case.s
SELF='tools/p09/sync_resumable_r07_runtime_progress.py'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
REPORT='implementation/p09/P09-191_CURRENT_R07_EXACT_ONE_RUNTIME_REPORT.md'
ARCHIVE='implementation/p09/source-archive/p09-191-pre-runtime-progress/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-191-exact-one-runtime-progress-sync.v1.json'
PREP=dict(path=case.paths(1)['preparation'],bytes=601637,
    sha256='076afa535640a5afad9f50ed3fd932ab29238cc8f6ed0a20b2ca526ff11cc5f1')
CASE=dict(path=case.DIR+'/p190-case-001-attempt-001.json',bytes=617840,
    sha256='7dfdede3acbe6a1f900a3775beb4512ac173ad4c0599c420b4670bfa608bad64')
CLOSING=dict(path=case.paths(1)['closing'],bytes=895299,
    sha256='8e220071e5126f80fe9a31ca140c46edf20ae1304bf0233a975990b1ce096f7a')
PLAN=dict(path=case.paths(4)['plan'],bytes=333034,
    sha256='c4810f15da2f6135985c0bd97e6fba7cede828eb1acd90766132749cf9af37fd')


def require(ok,code):case.require(ok,'DOC_'+code)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True)
    args=ap.parse_args();require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(ARCHIVE if args.mode=='archive' else DEST,fresh=True)
    resources=run.pressure.observation.ObservedResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',**case.flags(),further_test_Cargo_SQL_Hangul_child_executed=False,
        whole_current_source_or_EXE_reaudit_executed=False,single_process_full249_qualified=False)
    try:
        resources.admit();q=run.pressure.PressureReader(resources);q.pin(SELF)
        if args.mode=='archive':
            files=[]
            for name in DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'WHOLE_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_PRIOR_R61_DOC_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            for pin in (PREP,CASE,CLOSING,PLAN,run.PARENT):require(q.pin(pin['path'])==pin,'IMMUTABLE_RUNTIME_RECORDS')
            prep=q.json(PREP['path']);actual=q.json(CASE['path']);closing=q.json(CLOSING['path']);plan=q.json(PLAN['path'])
            expected=v.pins(prep['whole_inputs']);names=q.json(run.PARENT['path'])['source_test_names']
            exe=prep['binding']['compiled_test_executable_pin'];identity=v.identity(names,expected,exe)
            require(prep['state']==case.PREP_PASS and prep['contract_tests_passed']==142
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
                and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1470,
                'WHOLE_PREPARATION')
            v.accept_case(actual,names[0],identity,closing,expected,CASE)
            require(closing['IO']['finished'] and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==1472
                and closing['whole_original68_EXE_and_Rust785_closed'],'WHOLE_CLOSING')
            recomputed=v.plan(names,expected,exe,[(c.Path(CASE['path']).name,actual,CASE)],{CLOSING['path']:closing})
            require(plan['plan']==recomputed and recomputed['accepted_individual_cases']==1
                and recomputed['remaining_individual_cases']==248 and recomputed['remaining_regular_cases']==242
                and recomputed['remaining_corpus_cases']==6 and recomputed['next_index']==2
                and plan['resource_stop_reason'] is None and plan['resource_watcher_cleanup_confirmed'],'ACTUAL_SKIP_PROVEN')
            runtime,historical=case.runtime_scope(expected,exe)
            require(len(runtime)==1403 and len(historical)==67
                and len(actual['owned_source_reader_passes'])==2
                and all(row['read_passes']==1403 and row['bytes_read']==117816004 for row in actual['owned_source_reader_passes']),
                'PER_CASE_FRESH_SCOPE')
            for name in (case.SELF,case.TEST,v.SELF,v.TEST):require(q.pin(name)==expected[name],'ACTUAL_HELPERS_UNCHANGED')
            out.update(case.contracts())
            old=q.json(ARCHIVE);prefixes=[]
            require(old['state']=='WHOLE_PRIOR_R61_DOC_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','PRIOR_ARCHIVE')
            for name in DOCS:
                _,raw=run.b.parser.preimage(old,name);current=q.text(name).encode()
                require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
                prefixes.append(current[:-len(raw)])
            require(prefixes[0]==prefixes[1] and all(word in prefixes[0] for word in
                (b'r62',b'P191',b'EXACT_ONE_ACCEPTED',b'RESUME_SKIP_PROVEN',b'242',b'248',b'6',
                 b'compiled249=true/full249=false/signed16=false')),'SAME_ACCURATE_PREFIX')
            report=q.text(REPORT)
            require(all(word in report for word in ('142','1/249','242','6','132.71','NOT_RUN','P09')),'REPORT_SCOPE')
            q.finish();out.update(state='PASS_R07_EXACT_ONE_RUNTIME_AND_RESUME_SKIP_DOC_SYNC_ONLY_NOT_FULL_OR_GATE',
                accepted_individual_runtime_cases=1,remaining_individual_runtime_cases=248,
                whole_prior_documents_preserved=True,reusable_case_receipt_pin=CASE,whole_batch_closing_pin=CLOSING,
                plan_skip_receipt_pin=PLAN,original_P189_stop_preserved=True)
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
