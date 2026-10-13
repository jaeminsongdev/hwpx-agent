"""P167 partial timing + P168 Writer delta, whole prior documents retained."""
import base64
import hashlib
import json
from unittest.mock import patch
import audit_writer_xml_reuse as a

b=a.b
SELF='tools/p09/sync_writer_xml_reuse_progress.py'
PINS=[
    {
        "path": "implementation/p09/evidence/p09-167-current-signed-stage-cost.light-run01.v1.json",
        "bytes": 2184,
        "sha256": "61b4c91503878fd0fb6c4e06ee6d7240c5782f656b96644ae38e1bfa05b984a9"
    },
    {
        "path": "implementation/p09/evidence/p09-167-current-signed-stage-cost.actual-run01.v1.json",
        "bytes": 638579,
        "sha256": "4deee8d8eec3c57e4b63331ce8d5b27885e225a833eae24b23a0c6de3513a2ed"
    },
    {
        "path": "implementation/p09/evidence/p09-167-current-signed-stage-cost.terminal-audit-run01.v1.json",
        "bytes": 274673,
        "sha256": "84fc2be417a14ffe817fa57b81d9a5bb2bc5a7e4bd8151a1720f30adb1d5085e"
    },
    {
        "path": "implementation/p09/evidence/p09-168-writer-xml-reuse.light-run02.v1.json",
        "bytes": 1138,
        "sha256": "069b24859f9ddcaab26dfd083948b7d8c5b515192359baccb6ef44d08679ae46"
    },
    {
        "path": "implementation/p09/evidence/p09-168-writer-xml-reuse.units-run01.v1.json",
        "bytes": 1452883,
        "sha256": "858dc1e52548a55174cd025a8cd05a66d47195d6ae58046ccf01bbc067d3da24"
    },
    {
        "path": "implementation/p09/evidence/p09-168-writer-xml-reuse.source-closing-run01.v1.json",
        "bytes": 310132,
        "sha256": "c6a675eda17ce1450721ce31f4c6b702191138cbd0eb53ffc5fcef90ce3e3709"
    },
    {
        "path": "implementation/p09/source-archive/p09-168-initial-contract-failure-r48/preimages.v1.json",
        "bytes": 24065,
        "sha256": "7bd59704c3c390633f9b8c0c657c81590cb281b16ee41690e886cf33fc73d6de"
    }
]
FAILED_ARCHIVE='implementation/p09/source-archive/p09-168-initial-contract-failure-r48/preimages.v1.json'

def main():
    b.require(b.c.Path.cwd().resolve()==b.c.ROOT,'SYNC_CWD')
    destination=b.s.scoped_path('implementation/p09/evidence/p09-168-writer-xml-reuse.progress-sync-run01.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_child_or_new_thread_started=False)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('P168_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P168_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P168_SYNC_THREAD_FORBIDDEN')):
            q.pin(SELF);b.require(len(PINS)==7,'SYNC_PINS')
            for pin in PINS:b.require(q.pin(pin['path'])==pin,'SYNC_IMMUTABLE_RECEIPTS')
            stage_light,stage,stage_audit,units_light,units,closing,failed=(q.json(pin['path']) for pin in PINS)
            b.require(stage_light['contract_tests_passed']==130 and stage_light['state'].startswith('PASS_'),
                'SYNC_STAGE_LIGHT_ONLY')
            b.parent_scope(stage_audit)
            b.require(stage['state']=='STOPPED_NOT_ACCEPTED' and stage['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and stage['maximum_seconds']==180 and stage['original_full_qualification_seconds']==1200
                and stage['policy']==b.c.POLICY and stage['cleanup_confirmed'] and stage['owned_tree_empty']
                and stage['job_final']['active_processes']==0 and stage['job_final']['owned_processes']==[]
                and stage_audit['actual_stage_receipt_pin']==PINS[1]
                and stage['capture_diagnostics']['signed_stage_cost']==stage_audit['signed_stage_cost'],
                'SYNC_STAGE_STOP_PARTIAL_CLEANUP')
            b.require(units_light['state']=='PASS_WRITER_XML_REUSE_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
                and units_light['contract_tests_passed']==136 and not units_light['actual_child_or_new_thread_started'],
                'SYNC_UNITS_LIGHT_ONLY')
            accepted=units['state']==a.units.PASS
            b.require(units['state'] in (a.units.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
                and units['maximum_seconds']==600 and units['policy']==b.c.POLICY and units['cleanup_confirmed']
                and units['owned_tree_empty'] and units['original_package_lib_cases']==68
                and units['new_writer_xml_regression_cases']==3 and units['fresh_target_no_old_EXE_overwrite']
                and units['baseline_closing_pin']==b.PARENT and units['baseline_archive']==b.ARCHIVE
                and units['test_package_profile_config']==list(b.p.b.CONFIG),'SYNC_UNIT_SCOPE')
            b.require(closing['state']==('PASS_WRITER_XML_REUSE_DELTA_AND_ALL71_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
                if accepted else 'PASS_WRITER_XML_REUSE_DELTA_AND_UNIT_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE')
                and closing['source_closing_exact'] and closing['contract_tests_passed']==136
                and closing['actual_unit_receipt_pin']==PINS[4] and closing['current_Rust_input_count']==785
                and closing['protected_parent_EXE_inputs_exact']==64 and closing['whole_original_core_inverse_exact']
                and closing['test_oracle_whole_original_body_exact_after_declared_formatting']
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed'],
                'SYNC_INDEPENDENT_CURRENT_CLOSING')
            if accepted:
                b.require(units['exit_code']==0 and units['stop_reason'] is None and units['tests_passed']==71
                    and closing['actual_unit_tests_passed']==71 and closing['typecheck_accepted'],'SYNC_ACTUAL_ALL71')
                exe=closing['fresh_package_lib_executable_pin'];b.require(q.pin(exe['path'])==exe,'SYNC_FRESH_LIB_EXE')
            for row in (units,closing):
                b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                    and not row['signed16_current_qualified'] and not row['product_complete']
                    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
                    and not row['PC_freeze_resolved'] and not row['full_product_performance_improvement_measured'],
                    'SYNC_NO_RUNTIME_FREEZE_GATE_PROMOTION')
            b.require(failed['state']=='PRESERVED_INITIAL_CONTRACT_FAILURE_NOT_RUNTIME_OR_GATE'
                and failed['failure_code']=='CONTRACT6_PLUS130' and failed['actual_Rust_compile_or_test_not_started'],
                'SYNC_INITIAL_FAILURE_RETAINED')
            old_light,raw=b.preimage(failed,'implementation/p09/evidence/p09-168-writer-xml-reuse.light-run01.v1.json')
            b.require(q.pin(old_light['path'])=={k:old_light[k] for k in ('path','bytes','sha256')},'SYNC_FAILED_LIGHT_UNCHANGED')
            archive=q.json(b.ARCHIVE);b.require(archive['baseline_closing_pin']==b.PARENT,'SYNC_PREIMAGES')
            _,original=b.preimage(archive,b.SOURCE)
            current=q.text(b.SOURCE);b.inverse(current,original.decode());a.verify_original_oracle(current,original.decode())
            b.require(len(closing['declared_Rust_source_changes'])==1
                and q.pin(b.SOURCE)==closing['declared_Rust_source_changes'][0],'SYNC_ONLY_WRITER_DELTA')
            prefix=None
            for n in b.DOCS:
                item,old=b.preimage(archive,n);current=q.text(n).encode()
                b.require(current.endswith(old) and len(current)>len(old),'SYNC_WHOLE_PRIOR_DOCUMENT')
                added=current[:-len(old)];b.require(prefix is None or prefix==added,'SYNC_IDENTICAL_PREFIX');prefix=added
            header=prefix.decode()
            for token in ('P167/P168 writer-call-local-XML-reuse-r48:','목표 active','잔여76',
                    'P10 새 구현 없음','compiled249=false/full249=false/signed16=false','STOP_SUSTAINED_SYSTEM_CPU',
                    '59개 단계 기록','3개 완결','프리즈 해결·전체 성능 개선 미입증','SQL fixed image 부재',
                    '접근허용 없음','Git 명령 없음'):
                b.require(token in header,'SYNC_DOC_BOUNDARIES')
            for pin in PINS[:6]:b.require(pin['sha256'] in header,'SYNC_DOC_RECEIPTS')
            for n in (b.SELF,a.SELF,a.units.SELF,a.units.TEST):q.pin(n)
            q.finish();out.update(state='PASS_WRITER_XML_REUSE_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                previous_whole_document_bytes_preserved=True,current_evidence_pins=PINS,
                actual_unit_tests_passed=71 if accepted else None,initial_failed_contract_evidence_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=b.prior.d.original.closed_error(e)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','previous_whole_document_bytes_preserved',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
