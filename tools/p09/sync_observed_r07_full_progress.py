"""P187/P188/P189 r59 documents; preserve whole r58 and running-stop evidence.

This sync checks only declared receipts/helpers/docs, not all runtime inputs.
Inherited P181/P186 build/list standing is not a new runtime qualification.
"""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import run_observed_r07_full as candidate

run=candidate.run;stopped=candidate.stopped;c=run.c;s=run.s
SELF='tools/p09/sync_observed_r07_full_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-187-pre-progress-r59/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-187-current-r07-full.progress-sync-run01.v1.json'
LIGHT=dict(path=candidate.LIGHT,bytes=6325,sha256='8e0d8138a6ac0688c2dc6a420ae4be731a5b5c2fda3208920da5d031cdb04dd9')

def require(ok,code):run.require(ok,'R59_DOC_'+code)

def actual_role_dry_contracts():
    def no_runtime_main():
        require(run.SELF==candidate.SELF and run.TEST==candidate.TEST and run.PREP==candidate.PREP
            and run.ACTUAL==candidate.ACTUAL and run.PASS==candidate.PASS
            and run.run_owned is candidate.run_owned and run.pressure.PressureReader is candidate.BoundReader,
            'NEXT_ACTUAL_ADAPTER_ROLES')
        checked=candidate.contracts();require(checked['contract_tests_passed']==109,'NEXT_ACTUAL_ROLE_CONTRACT109')
        helpers=candidate.helpers()
        require(all(p['path'] in helpers for p in candidate.HISTORY)
            and candidate.observer.SELF in helpers and candidate.observer.TEST in helpers,
            'NEXT_ACTUAL_FAILURE_AND_IO_INPUTS')
        return 109
    with patch.object(candidate.sys,'argv',[candidate.SELF,'--mode','actual']), \
            patch.object(run,'main',no_runtime_main),patch('subprocess.Popen',side_effect=AssertionError('R59_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('R59_NO_CHILD')):
        result=candidate.main()
    require(result==109 and run.SELF=='tools/p09/run_current_r07_full.py'
        and run.run_owned is candidate.OLD_OWNED and run.pressure.PressureReader is candidate.BASE_READER,
        'NEXT_ACTUAL_ROLE_RESTORE')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True);mode=ap.parse_args().mode
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');destination=s.scoped_path(ARCHIVE if mode=='archive' else DEST,fresh=True)
    resources=run.pressure.observation.OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_build_accepted=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        whole_current_runtime_inputs_reaudited_by_doc_sync=False,actual_full_test_or_Cargo_SQL_Hangul_child_executed=False,
        artifact_EXE_scan_started=False,new_actual_full249_or_signed16_qualification_granted=False)
    try:
        resources.admit();q=run.pressure.PressureReader(resources);q.pin(SELF)
        if mode=='archive':
            files=[]
            for name in run.b.parser.DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_P187_R59_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            for pin in (*candidate.HISTORY,LIGHT,run.PARENT):require(q.pin(pin['path'])==pin,'IMMUTABLE_CURRENT_RECEIPTS')
            actual=q.json(stopped.ACTUAL['path']);prep=q.json(stopped.PREP['path']);parent=q.json(run.PARENT['path'])
            stopped.actual_scope(actual,prep,parent)
            probe=q.json(candidate.STOP_PROBE['path']);light=q.json(LIGHT['path'])
            require(probe['state']==stopped.PASS and probe['contract_tests_passed']==100
                and probe['first_P188_failure_preserved'] and probe['empty_owned_job_IO_API_verified']
                and probe['empty_owned_job_cleanup_confirmed'] and probe['resource_watcher_cleanup_confirmed']
                and probe['resource_stop_reason'] is None and not probe['source_closing_exact']
                and not probe['current_whole_runtime_inputs_reaudited'] and not probe['full249_current_qualified']
                and not probe['signed16_current_qualified'] and not probe['product_complete']
                and not probe['new_runtime_IO_observer_connected_to_product'],'EMPTY_JOB_PROBE_NOT_RUNTIME')
            require(light['state']=='PASS_OBSERVED_R07_FULL_CONTRACT109_ONLY_NOT_RUNTIME_OR_GATE'
                and light['contract_tests_passed']==109 and light['original_P187_stop_preserved']
                and light['original_1200_seconds_and_resource_policy_retained']
                and light['resource_watcher_cleanup_confirmed'] and light['resource_stop_reason'] is None
                and light['nominal_success_output_bytes']==31325 and light['original_per_stream_output_cap']==32768
                and light['nominal_size_is_not_worst_case_or_overflow_waiver']
                and light['IO']['finished'] and light['IO']['bound_inputs']==light['IO']['final_fresh_hashes']==19
                and not light['actual_Cargo_SQL_Hangul_child_or_test_body_executed']
                and not light['actual_runtime_IO_observation_executed'] and not light['runtime_preparation_executed']
                and not light['full249_current_qualified'] and not light['signed16_current_qualified'],'NEXT_CANDIDATE_ONLY')
            require(not (c.ROOT/candidate.PREP).exists() and not (c.ROOT/candidate.ACTUAL).exists(),'NEXT_ACTUAL_NOT_RUN')
            for row in (probe,light):require(row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
                and not row['PC_freeze_resolved'],'NO_GATE_OR_CAUSE_PROMOTION')
            prepared=s.inputs.inventory(prep['bound_input_pins'],1447)
            for name in (run.SELF,run.TEST,run.owned.SELF,run.owned.TEST,run.pressure.SELF,run.pressure.TEST,
                    run.original.SELF,run.original.TEST):require(q.pin(name)==prepared[name],'P187_FROZEN_HELPERS')
            frozen=s.inputs.inventory(light['bound_input_pins'],19)
            for name in (candidate.SELF,candidate.TEST,candidate.observer.SELF,candidate.observer.TEST,
                    stopped.SELF,stopped.TEST,stopped.ARCHIVE):require(q.pin(name)==frozen[name],'P189_FROZEN_HELPERS')
            out['P189_actual_role_contract_tests_passed']=actual_role_dry_contracts()
            old=q.json(ARCHIVE);prefixes=[]
            require(old['state']=='WHOLE_P187_R59_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','WHOLE_PRIOR_ARCHIVE')
            for name in run.b.parser.DOCS:
                _,raw=run.b.parser.preimage(old,name);current=q.text(name).encode()
                require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
                prefixes.append(current[:-len(raw)])
            prefix=prefixes[0]
            require(prefixes[0]==prefixes[1] and all(word in prefix for word in
                (b'P187',b'P188',b'P189',b'r59',b'TERMINAL',b'compiled249=true/full249=false/signed16=false',
                b'RUNNING_CPU_STOP',b'P189_ACTUAL_NOT_RUN')),'SAME_ACCURATE_NEW_PREFIX')
            q.finish();out.update(state='PASS_R07_RUNNING_STOP_AND_IO_DIAGNOSTIC_CANDIDATE_DOCUMENT_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                current_build_accepted=True,current_compiled249_qualified=True,
                inherited_P181_P186_standing_only_not_new_qualification=True,whole_prior_documents_preserved=True,
                actual_full_receipt_pin=stopped.ACTUAL,preparation_receipt_pin=stopped.PREP,
                current_compiled249_parent_pin=run.PARENT,empty_owned_IO_probe_pin=candidate.STOP_PROBE,
                candidate_light_pin=LIGHT,original_P187_runtime_stop_preserved=True,
                original_P188_initial_failure_preserved=True,P189_actual_NOT_RUN=True,
                actual_role_contract_check_did_not_start_preparation_or_worker=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','current_compiled249_qualified',
            'P189_actual_role_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2

if __name__=='__main__':raise SystemExit(main())
