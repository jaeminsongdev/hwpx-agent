"""Independent observer closing and document sync; never executes test EXEs."""
import argparse
import base64
import hashlib
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import prepare_current_stored_generation as s
import probe_host_cpu_groups as groups

SELF='tools/p09/audit_host_cpu_groups.py'
DOC_ARCHIVE='implementation/p09/source-archive/p09-153-pre-progress-r35/document-pins.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-152-current-stored-full.actual-run01.v1.json',bytes=563181,
        sha256='a0cef0377ecb033be34a7138e87ae7273b9055d6922c926be8e0171583088577'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-full.terminal-audit-run01.v1.json',bytes=334564,
        sha256='f61aaad697c1dd63547de2f8eed6a308bc716cdd9e4e213375553c1057005618'),
    dict(path='implementation/p09/evidence/p09-153-host-cpu-groups.light-run01.v1.json',bytes=2062,
        sha256='3acfb5acda467c1aed1c5f04d23d7c4a62f4aad02e8b3529229105af7a92e8e5'),
    dict(path='implementation/p09/evidence/p09-153-host-cpu-groups.actual-run01.v1.json',bytes=19298,
        sha256='3780ceebd4a4115314cd6a32f60cbdd56a7866811795afe781755e07ddcc65aa'))


def require(ok,code):groups.require(ok,'AUDIT_'+code)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('closing','doc-sync'),required=True)
    parser.add_argument('--run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'REPOSITORY_CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-153-host-cpu-groups.{args.mode}-run{args.run:02}.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',goal_status='active',
        full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False,
        remaining_non_permission_work_units=76,source_closing_exact=False,
        actual_test_EXE_SQL_native_or_compiler_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('GROUP_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('GROUP_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('GROUP_AUDIT_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            full,closed,light,actual=(q.json(pin['path']) for pin in PINS)
            require(full['state']=='STOPPED_NOT_ACCEPTED' and full['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and full['tests_passed'] is None and full['full249_current_qualified'] is False
                and full['signed16_current_qualified'] is False and full['cleanup_confirmed'] and full['owned_tree_empty']
                and full['job_final']['active_processes']==0 and full['job_final']['owned_processes']==[],'ORIGINAL_FULL_STOP')
            require(closed['state']=='PASS_CURRENT_FULL249_STOP_TERMINAL_ACCOUNTED_NOT_RUNTIME_SQL_NATIVE_OR_GATE'
                and closed['source_closing_exact'] and closed['contract_tests_passed']==25
                and closed['full249_current_qualified'] is False
                and closed['original_source_final_hash_not_retroactively_promoted'] is True,'ORIGINAL_FULL_CLOSING')
            require(light['state']=='PASS_HOST_CPU_GROUP_CONTRACTS_ONLY_NOT_NATIVE_OR_GATE'
                and light['tests_run']==light['tests_passed']==40 and light['source_closing_exact'],'LIGHT40')
            require(actual['state']==groups.PASS and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['observer_query_cleanup_confirmed'] is True and actual['stop_reason'] is None
                and actual['observer_failure_code'] is None and actual['job_final']['active_processes']==0
                and actual['job_final']['owned_processes']==[] and actual['job_assigned'] and actual['writer_authorized']
                and actual['maximum_seconds']==30 and actual['Rust_or_test_body_executed'] is False
                and actual['full249_current_qualified'] is False and actual['PC_freeze_resolved'] is False,'ACTUAL_OBSERVER_ONLY')
            groups.validate_payload(actual['observer_probe'])
            require(all(sample['observation']['processor_count']==actual['resolved_owned_limits']['machine_logical_processors']
                for sample in actual['observer_probe']['samples']),'NORMALIZATION_MACHINE')
            require(actual['policy']==s.c.POLICY and actual['resolved_owned_limits']['job_cpu_hard_cap_machine_percent']==6.25
                and actual['job_final']['peak_job_private_percent']<7,'UNCHANGED_CAPS')
            frozen=s.inputs.inventory(actual['source_freeze'],10);require(set(frozen)==set(groups.FILES),'OBSERVER_INPUT_SCOPE')
            for name,pin in frozen.items():require(q.pin(name)==pin,'CURRENT_OBSERVER_INPUT')
            require(s.inputs.inventory(light['bound_input_pins'],10)==frozen,'LIGHT_ACTUAL_INPUTS')
            failed=[]
            for run in range(1,4):
                name=f'implementation/p09/evidence/p09-153-host-cpu-observer.actual-run{run:02}.v1.json'
                old=q.json(name);require(old['state']=='STOPPED_NOT_ACCEPTED' and old['stop_reason']=='OWNED_COMMAND_FAILED'
                    and old['cleanup_confirmed'] and old['owned_tree_empty'] and old['job_final']['active_processes']==0,'FAILED_PROBE_PRESERVED')
                failed.append(q.pin(name))
                if run==3:
                    require(old['observer_failure_code']=='P153_COUNTER_ADD','V2_UNAVAILABLE')
                    for name,pin in s.inputs.inventory(old['source_freeze'],7).items():require(q.pin(name)==pin,'V2_FAILED_SOURCE_PRESERVED')
            for archive in ('p09-153-pre-closed-error-r35','p09-153-pre-process-v2-r35'):
                row=q.json(f'implementation/p09/source-archive/{archive}/source-preimages.v1.json')
                require(len(row['files'])==7 and len(row['evidence_pins'])==2,'FAILED_PREIMAGE_SCOPE')
                for pin in row['evidence_pins']:require(q.pin(pin['path'])==pin,'FAILED_PREIMAGE_RECEIPT')
                prior=q.json(row['evidence_pins'][1]['path']);priorpins=s.inputs.inventory(prior['source_freeze'],7)
                for item in row['files']:
                    data=base64.b64decode(item['base64'],validate=True)
                    pin={k:item[k] for k in ('path','bytes','sha256')}
                    require(priorpins.get(item['path'])==pin and len(data)==item['bytes']
                        and hashlib.sha256(data).hexdigest()==item['sha256'],'WHOLE_FAILED_PREIMAGE_EXACT')
            if args.mode=='closing':
                sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
                # Observe contracts only: do NOT execute 249 Rust test bodies.
                suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)
                    for name in ('test_host_cpu_observer','test_probe_host_cpu_observer','test_host_cpu_groups',
                        'test_current_stored_full','test_compression_full_stored'))
                checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
                require(checked.wasSuccessful() and checked.testsRun==65 and not checked.skipped,'CONTRACT65')
                for name in ('tools/p09/run_current_stored_full.py','tools/p09/tests/test_current_stored_full.py','tools/p09/tests/test_compression_full_stored.py'):
                    pin=next(p for p in closed['bound_input_pins'] if p['path']==name);require(q.pin(name)==pin,'FULL_HELPER_IMMUTABLE')
                out['contract_tests_passed']=65
            else:
                closing=q.json('implementation/p09/evidence/p09-153-host-cpu-groups.closing-run02.v1.json')
                require(closing['state']=='PASS_NATIVE_GROUP_OBSERVER_CLOSING_ONLY_NOT_FULL249_OR_GATE'
                    and closing['source_closing_exact'] and closing['contract_tests_passed']==65,'OBSERVER_CLOSING')
                prior=s.inputs.inventory(q.json(DOC_ARCHIVE)['files'],2);prefix=None
                for name,pin in prior.items():
                    data=q.text(name).encode();now=q.reader.snapshots[name]
                    require(len(data)==now['bytes'] and hashlib.sha256(data).hexdigest()==now['sha256'],'DOC_BYTES')
                    require(len(data)>pin['bytes'] and hashlib.sha256(data[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOCUMENT')
                    this=data[:-pin['bytes']];require(prefix is None or prefix==this,'IDENTICAL_PREFIX');prefix=this
                require(prefix.startswith('> 2026-10-07 P152 full249-stop/P153 observer-r35:'.encode()),'CURRENT_PREFIX')
                header=prefix.decode()
                for text in ('목표 active','잔여76','product=false','P10 새 구현 없음','STOP_SUSTAINED_SYSTEM_CPU',
                    'full249=false','프리즈 해결은 미입증','그룹','원래1200초','SQL fixed image 부재'):
                    require(text in header,'DOC_BOUNDARY')
                for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE_PIN')
                out['previous_whole_document_bytes_preserved']=True
            q.finish();out.update(state='PASS_NATIVE_GROUP_OBSERVER_CLOSING_ONLY_NOT_FULL249_OR_GATE' if args.mode=='closing'
                else 'PASS_FULL_STOP_AND_OBSERVER_PROGRESS_SYNC_ONLY_NOT_GATE',source_closing_exact=True,
                original_full_stop_preserved=True,failed_probes_preserved=failed,accepted_observer_only=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P153_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P153_AUDIT_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','previous_whole_document_bytes_preserved','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
