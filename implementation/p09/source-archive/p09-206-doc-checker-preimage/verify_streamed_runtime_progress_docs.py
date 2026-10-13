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
import audit_runtime_input_roles as roles
import runtime_fixture_inputs as fixtures
import minimal_r07_worker as minimal_worker
import audit_minimal_worker_inputs as worker_audit
import run_minimal_runtime_r07_case as minimal_runtime
from sync_pending_r07_review_docs import raw

p=s.p;r=s.r;c=s.c;b=s.b
SELF='tools/p09/verify_streamed_runtime_progress_docs.py'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--revision',type=int,required=True);ap.add_argument('--report',required=True)
    ap.add_argument('--proof-run',type=int,required=True)
    ap.add_argument('--cpu-inspection');ap.add_argument('--input-role-audit');ap.add_argument('--fixture-inspection')
    ap.add_argument('--fixture-closure')
    ap.add_argument('--worker-input-probe')
    args=ap.parse_args()
    s.require(bool(args.input_role_audit)==bool(args.fixture_inspection),'DOC_PAIRED_ROLE_AND_FIXTURE_INSPECTIONS')
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
        worker_contracts=proof.get('minimal_worker_contract_tests_passed',0)
        bridge_contracts=proof.get('minimal_runtime_bridge_contract_tests_passed',0)
        s.require(common_contracts==212 and joined_contracts in (0,12)
            and (worker_contracts,bridge_contracts) in ((0,0),(12,10))
            and (bridge_contracts==0 or joined_contracts==12),'DOC_CLOSED_CONTRACT_GENERATIONS')
        proof_count=common_contracts+joined_contracts+worker_contracts+bridge_contracts
        producer=minimal_runtime if bridge_contracts else joined if joined_contracts==12 else s
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
        if bridge_contracts:
            s.require(proof['minimal_runtime_bridge_generation']=='P205_CONTROLLER16','DOC_ACTUAL_BRIDGE_GENERATION')
            with patch.object(joined,'case_controller',minimal_runtime.case_controller):
                legacy,plan,closing_pins,_=producer.progress(q,expected,names,exe,engine,controller)
        else:legacy,plan,closing_pins,_=producer.progress(q,expected,names,exe,engine,controller)
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
        if args.input_role_audit:
            s.require(re.fullmatch(r'implementation/p09/evidence/runtime-r07/p09-202-input-role-audit-run[0-9]{2}\.v1\.json',
                args.input_role_audit),'DOC_INPUT_ROLE_AUDIT_PATH')
            audit=q.json(args.input_role_audit);role= audit['input_roles'];audited=s.v.pins(audit['bound_input_pins'])
            s.require(audit['state']=='PASS_SOURCE_REFERENCE_AUDIT_NOT_REDUCED_RUNTIME_OR_GATE'
                and audit['input_role_contract_tests_passed']==12 and audit['resource_stop_reason'] is None
                and audit['resource_watcher_cleanup_confirmed'] and audit['IO']['finished']
                and audit['IO']['bound_inputs']==audit['IO']['final_fresh_hashes']==len(audited)
                and audit['all785_source_text_fresh_read_and_final_hash_confirmed'] is True
                and audit['binding']==s.v.identity(names,expected,exe),'DOC_ACTUAL_ROLE_AUDIT_PROOF')
            for name in (roles.SELF,roles.TEST):s.require(q.pin(name)==audited[name],'DOC_ROLE_HELPERS_UNCHANGED')
            rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
                and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
            s.require(len(rust)==role['scanned_source_count']==785 and all(audited.get(n)==expected[n] for n in rust)
                and s.v.pins([row['pin'] for row in role['manifest_roles']])==expected,'DOC_ROLE_FULL_BASELINE')
            counts={};sizes={}
            for row in role['manifest_roles']:
                key=row['role'];counts[key]=counts.get(key,0)+1;sizes[key]=sizes.get(key,0)+row['pin']['bytes']
            s.require(counts==role['role_counts'] and sizes==role['role_bytes'] and sum(counts.values())==1470
                and counts['HISTORICAL_EXECUTABLE_WHOLE_RECONCILIATION_REQUIRED']==67
                and role['safe_runtime_exclusions']==[] and role['runtime_input_exclusions_authorized'] is False
                and role['reduced_scope_runtime_qualified'] is False and role['dynamic_fixture_dependency_closure_complete'] is False
                and role['P09_gate']=='OPEN' and role['product_complete'] is False
                and audit['runtime_scope_changed'] is False and audit['actual_product_child_executed'] is False
                and args.input_role_audit in report,'DOC_ROLE_NO_SCOPE_REDUCTION')
            out.update(input_role_audit_pin=q.reader.snapshots[args.input_role_audit],reused_input_role_contract_proofs=12,
                role_audit785_source_freshness_proof_reused_not_reexecuted=True)
        if args.fixture_inspection:
            s.require(args.fixture_inspection=='implementation/p09/evidence/runtime-r07/p09-202-dynamic-fixture-boundary-inspection.v1.json',
                'DOC_FIXTURE_INSPECTION_PATH')
            fixture=q.json(args.fixture_inspection);parent=fixture['parent_case_pin']
            s.require(q.pin(parent['path'])==parent,'DOC_FIXTURE_PARENT_PIN');original=q.json(parent['path'])
            frozen=s.v.pins(original['source_freeze'])
            s.require(original['state']==s.v.CASE_PASS and fixture['state']=='OBSERVED_DECLARED_FIXTURE_BOUNDARIES_NOT_NEW_RUNTIME_OR_GATE'
                and len(fixture['families'])==2,'DOC_FIXTURE_OBSERVATION_SCOPE')
            for family in fixture['families']:
                pin=family['manifest_pin'];s.require(q.pin(pin['path'])==pin,'DOC_FIXTURE_MANIFEST_PIN')
                source=family['Rust_source'];s.require(q.pin(source)==expected[source],'DOC_FIXTURE_SOURCE_CODE_PIN')
                s.require(pin['sha256'] in q.text(source),'DOC_FIXTURE_HASH_PRESENT_IN_RUST')
                manifest=q.json(pin['path'])
                if family['family']=='P77_source_corpus':
                    inputs=[{k:row[k] for k in ('path','bytes','sha256')} for row in manifest['actual_inputs']]
                else:
                    s.require(family['family']=='P09_42_source_and_output_matrix'
                        and family['declared_cases']==len(manifest['cases']),'DOC_MATRIX_CASES')
                    inputs=[];prefix='fixtures/target-build/p09-42-product-form-values-01/output/'
                    for row in manifest['cases']:
                        for kind in ('source','output'):
                            item=row[kind];name=item['path']
                            s.require(isinstance(name,str) and name not in ('.','..') and not any(x in name for x in '/\\:'),
                                'DOC_MATRIX_BASENAME')
                            inputs.append(dict(path=prefix+name,bytes=item['bytes'],sha256=item['sha256']))
                s.v.pins(inputs)
                s.require(family['declared_packages']==len(inputs)
                    and family['declared_package_bytes']==sum(item['bytes'] for item in inputs)
                    and family['packages_present_in_old_Python_freeze']==sum(item['path'] in frozen for item in inputs)
                    and family['manifest_present_in_old_Python_freeze']==(pin['path'] in frozen),
                    'DOC_DECLARED_FIXTURE_BOUNDARY_VALUES')
            s.require(fixture['actual_package_contents_read_by_inspection'] is False
                and fixture['fixture_dependency_closure_complete'] is False and fixture['runtime_scope_changed'] is False
                and fixture['existing_runtime_results_reclassified_as_failure'] is False
                and fixture['new_product_test_executed'] is False and fixture['product_complete'] is False
                and fixture['P09_gate']=='OPEN' and args.fixture_inspection in report,'DOC_NO_FIXTURE_RUNTIME_PROMOTION')
            out['fixture_boundary_inspection_pin']=q.reader.snapshots[args.fixture_inspection]
        if args.fixture_closure:
            s.require(re.fullmatch(r'implementation/p09/evidence/runtime-r07/p09-203-fixture-input-closure-run[0-9]{2}\.v1\.json',
                args.fixture_closure),'DOC_FIXTURE_CLOSURE_PATH')
            closure=q.json(args.fixture_closure);bound=s.v.pins(closure['bound_input_pins'])
            s.require(closure['schema_version']==fixtures.SCHEMA and closure['state']==fixtures.PASS
                and closure['fixture_input_contract_tests_passed']==16 and closure['resource_stop_reason'] is None
                and closure['resource_watcher_cleanup_confirmed'] and closure['IO']['finished']
                and closure['IO']['bound_inputs']==closure['IO']['final_fresh_hashes']==len(bound)
                and closure['binding']==s.v.identity(names,expected,exe),'DOC_COMPLETE_FIXTURE_CLOSURE_PROOF')
            for name in (fixtures.SELF,fixtures.TEST):
                s.require(q.pin(name)==bound[name],'DOC_FIXTURE_CLOSURE_HELPERS_UNCHANGED')
            parent=q.json(b.run.PARENT['path']);modules=parent['source_module_instances']
            s.require(len(modules)==closure['compiled_test_module_instances']==59
                and set(closure['qualified_known_fixture_IO_sources'])==fixtures.IO_SOURCES
                and all(bound.get(row['path'])==expected[row['path']] for row in modules),
                'DOC_FIXTURE_FROZEN_MODULE_SCOPE')
            s.require(s.v.pins(closure['manifest_pins'])==fixtures.MANIFEST_PINS,'DOC_FIXTURE_FOUR_MANIFESTS')
            metadata={}
            for name,pin in fixtures.MANIFEST_PINS.items():
                fixtures.direct_file(c.ROOT,pin);s.require(q.pin(name)==pin,'DOC_CURRENT_FIXTURE_MANIFEST_PIN')
                metadata[name]=q.json(name)
            groups,inputs=fixtures.families(metadata[fixtures.P77],metadata[fixtures.FORM],metadata[fixtures.NOTE],
                metadata[fixtures.NATIVE],expected[fixtures.HEADER])
            s.require(s.v.pins(closure['fixture_input_pins'])==inputs
                and closure['family_reference_counts']=={name:len(rows) for name,rows in groups.items()}
                and closure['unique_fixture_inputs']==len(inputs)
                and closure['unique_fixture_input_bytes']==sum(pin['bytes'] for pin in inputs.values())
                and closure['old_manifest_overlap']==sum(name in expected for name in inputs)
                and closure['dynamic_fixture_inputs_newly_explicit']==sum(name not in expected for name in inputs),
                'DOC_FIXTURE_EXACT_DECLARED_INPUTS')
            fixtures.verify_bytes(q,inputs)
            s.require(closure['runtime_scope_changed'] is False
                and closure['native_note_original_failed_semantic_state_preserved'] is True
                and closure['every_known_fixture_byte_fresh_before_and_at_finish'] is True
                and closure['new_product_test_or_all_runtime_dependency_closure_proved'] is False
                and closure['runtime_input_exclusions_authorized'] is False and closure['safe_runtime_exclusions']==[]
                and closure['actual_Hangul_SQL_or_product_body_executed'] is False
                and closure['product_complete'] is False and closure['P09_gate']=='OPEN'
                and args.fixture_closure in report,'DOC_FIXTURE_NO_RUNTIME_OR_GATE_PROMOTION')
            out.update(fixture_input_closure_pin=q.reader.snapshots[args.fixture_closure],
                reused_fixture_input_contract_proofs=16,freshly_reverified_known_fixture_inputs=len(inputs))
        if args.worker_input_probe:
            s.require(re.fullmatch(r'implementation/p09/evidence/runtime-r07/p09-204-minimal-worker-input-probe-run[0-9]{2}\.v1\.json',
                args.worker_input_probe),'DOC_WORKER_INPUT_PROBE_PATH')
            probe=q.json(args.worker_input_probe);bound=s.v.pins(probe['bound_input_pins'])
            s.require(probe['schema_version']==worker_audit.SCHEMA and probe['state']==worker_audit.PASS
                and probe['worker_input_contract_tests_passed']==20 and probe['failed_contract_ids']==[]
                and probe['resource_stop_reason'] is None and probe['resource_watcher_cleanup_confirmed']
                and probe['IO']['finished'] and probe['IO']['bound_inputs']==probe['IO']['final_fresh_hashes']==len(bound),
                'DOC_WORKER_INPUT_PROBE_COMPLETE')
            executed=s.v.pins(probe['executed_repository_source_pins'])
            required={minimal_worker.SELF,*minimal_worker.CORE_PINS}
            s.require(set(executed)==required and set(probe['observed_repository_code_reads'])==required
                and probe['observed_repository_data_reads']==[minimal_worker.PARENT['path']]
                and probe['known_worker_direct_inventory_pin']==b.run.PARENT==minimal_worker.PARENT,
                'DOC_WORKER_EXACT_MINIMAL_DEPENDENCIES')
            for name in (worker_audit.SELF,worker_audit.TEST,minimal_worker.SELF,minimal_worker.TEST):
                s.require(q.pin(name)==bound[name],'DOC_WORKER_TESTED_HELPERS_UNCHANGED')
            for name,pin in executed.items():s.require(q.pin(name)==pin,'DOC_WORKER_EXECUTED_SOURCES_UNCHANGED')
            s.require(all(executed[name]==dict(path=name,**pin) for name,pin in minimal_worker.CORE_PINS.items())
                and minimal_worker.EXE==exe and minimal_worker.TASK_ARGS==b.core.run.original.TASK_ARGS
                and minimal_worker.TARGET==b.core.run.b.TARGET,'DOC_WORKER_ORIGINAL_INPUT_PARITY')
            selected=names[plan['next_runtime_index']-1]
            s.require(probe['selected_public_test_name']==selected and probe['selected_test_arguments']==s.v.arguments(selected)
                and probe['blocked_child_creation_test_events']==1 and probe['blocked_write_events']==0
                and probe['repository_bytecode_read_or_write_used'] is False
                and probe['audit_hook_not_security_sandbox'] is True
                and probe['runtime_import_probe_not_all_native_or_product_IO'] is True
                and all(probe[k] is False for k in ('actual_Job_GO_or_product_child_executed',
                    'actual_Cargo_SQL_Hangul_executed','runtime_scope_changed','PC_freeze_resolved','product_complete'))
                and probe['P09_gate']=='OPEN' and args.worker_input_probe in report,
                'DOC_WORKER_NO_RUNTIME_OR_GATE_PROMOTION')
            out.update(worker_input_probe_pin=q.reader.snapshots[args.worker_input_probe],reused_worker_input_contract_proofs=20)
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
