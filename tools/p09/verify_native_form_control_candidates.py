"""Independent complete candidate/worker-plan verifier; never activates native COM."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import native_form_control_plan as plan

ROOT, prior = plan.ROOT, plan.prior
EXAMPLE = 'p09_51_native_form_color_candidates'
GENERATOR = f'crates/hwpx-package/examples/{EXAMPLE}.rs'
DIRECTORY = ROOT/'fixtures/target-build/p09-51-native-form-candidates-20261003-r01'
MANIFEST = DIRECTORY/'output/fixture-manifest.json'
CAPSULE = 'implementation/p09/evidence/p09-51-native-form-control-candidates.progress.v1.json'
CASE_KEYS = set('case_id file plan_file plan_sha256 plan_bytes source_file original_package_sha256 original_package_bytes '
    'package_sha256 package_bytes complete_map controls policy_sha256 original_state_sha256 target_state_sha256 '
    'document_flow_sha256 actual_sdk_color_receipt whole_original_control_intent_except_declared_style_reference_exact '
    'actual_sdk_external_output_verification deterministic_preparation_retry native_runtime_qualified anchor_mapping_qualified'.split())
SOURCES = (GENERATOR, 'tools/p09/verify_native_form_control_candidates.py',
    'tools/p09/tests/test_native_form_control_candidates.py', 'implementation/p09/P09-51_NATIVE_FORM_CANDIDATES_POLICY.md',
    'tools/p09/inspect_native_form_binding_typelib.ps1', 'tools/p09/native_form_control_plan.py',
    'tools/p09/tests/test_native_form_control_plan.py', 'implementation/p09/tools/native-form-control-binding.ps1',
    'implementation/p09/tools/run-hancom-2020-native-form-control-binding.ps1')


def require(value, code):
    plan.require(value, code)


def bounded(path, maximum=4194304):
    return prior.color.history.progress.original.public.bounded_bytes(path, maximum)


def pins():
    return {name:plan.sha(bounded(ROOT/name)) for name in SOURCES}


def preservation():
    previous=json.loads(prior.io.checked(ROOT/prior.CAPSULE,
        'ebd8e94b8826525752f4ce7b0d57ff7a289fa8772bc02e43534b1f3e3d385262'),object_pairs_hook=prior.io.duplicate_guard)
    require(prior.pins()==previous['source_sha256'] and prior.preserved_color()==previous['preserved_color_source_successor'],
            'candidate_original_source_or_native_evidence_changed')
    prior.io.checked(ROOT/'implementation/p09/tools/run-hancom-2020-field-auto-number-target-owned-exit-wait.ps1',
                     '7463b70fce52407f5173da8ccff75344ce740ab88f664620796d591edd3ec1a3')
    return {'p48_all_23_sources_and_1551_inputs_exact':True, 'p49_all_nine_sources_exact':True,
            'original_native_files_receipts_archives_and_harness_exact':True,
            'predecessor_full_workflows_reexecuted_here':False}


def originals():
    raw=prior.io.checked(ROOT/plan.MANIFEST,plan.MANIFEST_SHA)
    value=json.loads(raw,object_pairs_hook=prior.io.duplicate_guard)
    require(type(value['cases']) is list and len(value['cases'])==15,'candidate_original_fifteen_required')
    return value['cases']


def validate_manifest(value):
    expected={'schema_version':'hwpx-agent.p09-51-complete-coupled-native-candidates/v1',
        'original_manifest_sha256':plan.MANIFEST_SHA,'actual_hangul':False,'native_runtime_qualified':False,
        'render':'not_run','green_rows':0,'source_policy':'original_hash_checked_caller_declarations_not_native_defaults',
        'raw_document_values_present':False,'absolute_private_paths_present':False,'signed_form_publication_or_p09_gate':False}
    require(type(value) is dict and value.keys()==expected.keys()|{'cases'}
            and all(type(value[k]) is type(v) and value[k]==v for k,v in expected.items()),'candidate_manifest_scope_changed')
    rows=value['cases']; old=originals()
    require(type(rows) is list and len(rows)==15,'candidate_complete_fifteen_inventory')
    for index,(row,source) in enumerate(zip(rows,old,strict=True)):
        require(type(row) is dict and row.keys()==CASE_KEYS,'candidate_case_keys')
        required={'case_id':f'P09-35-C{index+1:02}','file':f'p09-51-c{index+1:02}-coupled-native-form.hwpx',
            'plan_file':f'p09-50-c{index+1:02}-native-form-plan.json','source_file':source['file'],
            'original_package_sha256':source['package_sha256'],'original_package_bytes':source['package_bytes'],
            'controls':source['controls'],'policy_sha256':source['policy_sha256'],
            'original_state_sha256':source['target_state_sha256'],
            'whole_original_control_intent_except_declared_style_reference_exact':True,
            'actual_sdk_external_output_verification':True,'deterministic_preparation_retry':True,
            'native_runtime_qualified':False,'anchor_mapping_qualified':False}
        require(all(type(row[k]) is type(v) and row[k]==v for k,v in required.items())
                and prior.io.canonical(row['complete_map'])==prior.io.canonical(source['complete_map']),
                'candidate_case_identity_or_claim_changed')
        for key in ('package_sha256','plan_sha256','target_state_sha256','document_flow_sha256'):
            require(type(row[key]) is str and re.fullmatch('[0-9a-f]{64}',row[key]),'candidate_hash_type')
        for key,maximum in (('package_bytes',4194304),('plan_bytes',262144)):
            require(type(row[key]) is int and 0<row[key]<=maximum,'candidate_artifact_bound')
        receipt=row['actual_sdk_color_receipt']
        require(type(receipt) is dict and receipt['profile']=='hwpx-agent.native-form-package.coupled-foreground/v1'
                and receipt['source_package_sha256']==source['package_sha256']
                and receipt['output_package_sha256']==row['package_sha256']
                and receipt['target_state_sha256']==row['target_state_sha256']
                and receipt['document_flow_sha256']==row['document_flow_sha256']
                and type(receipt['requested_controls']) is int and receipt['requested_controls']==source['controls']
                and receipt['actual_native_validation']=='not_run','candidate_sdk_receipt_binding')
        for key in ('existing_styles_and_fonts_preserved','undeclared_expanded_parts_byte_exact','outside_declared_xml_edits_byte_exact'):
            require(receipt['preservation'][key] is True,'candidate_sdk_preservation_claim')
    return rows


def verify_plan(source, row, raw, actual):
    require(plan.sha(raw)==row['package_sha256'] and len(raw)==row['package_bytes'],'candidate_output_identity')
    derived=copy.deepcopy(source)
    derived.update(package_sha256=row['package_sha256'],package_bytes=row['package_bytes'])
    expected=plan.compile_case(derived,raw)
    require(prior.io.canonical(actual)==prior.io.canonical(expected),'candidate_sdk_python_plan_disagreement')
    original_raw=prior.color.history.progress.original.public.checked((ROOT/plan.MANIFEST).parent/source['file'],
        source['package_sha256'],4194304)
    old=plan.compile_case(source,original_raw)
    # Package/section identities change for the explicit coupled style transition.
    # EVERY remaining worker intent and physical source coordinate must remain exact.
    for previous,current in zip(old['controls'],expected['controls'],strict=True):
        previous=copy.deepcopy(previous);previous['section_sha256']=current['section_sha256']
        require(prior.io.canonical(previous)==prior.io.canonical(current),'candidate_original_worker_intent_changed')
    return expected


def inspect_files():
    raw=bounded(MANIFEST,512*1024)
    value=json.loads(raw,object_pairs_hook=prior.io.duplicate_guard); rows=validate_manifest(value)
    expected_names={'fixture-manifest.json'}|{r[k] for r in rows for k in ('file','plan_file')}
    require({p.name for p in MANIFEST.parent.iterdir()}==expected_names,'candidate_persisted_inventory')
    files={'fixture-manifest.json':{'sha256':plan.sha(raw),'bytes':len(raw)}}
    old=originals()
    for source,row in zip(old,rows,strict=True):
        artifacts={}
        for filename, digest, length in ((row['file'],row['package_sha256'],row['package_bytes']),
                                         (row['plan_file'],row['plan_sha256'],row['plan_bytes'])):
            content=prior.color.history.progress.original.public.checked(MANIFEST.parent/filename,digest,4194304)
            require(len(content)==length,'candidate_persisted_bytes')
            files[filename]={'sha256':digest,'bytes':length};artifacts[filename]=content
        actual=json.loads(artifacts[row['plan_file']],object_pairs_hook=prior.io.duplicate_guard)
        verify_plan(source,row,artifacts[row['file']],actual)
    require(len(files)==31,'candidate_complete_file_inventory')
    return {'manifest_sha256':plan.sha(raw),'manifest_bytes':len(raw),'cases':15,'controls':17,'files':files,
            'candidate_and_plan_total_bytes':sum(v['bytes'] for v in files.values()),
            'sdk_and_independent_python_full_worker_plans_exact':True,'original_worker_intents_exact':True,
            'native_runtime_or_anchor_mapping_or_render_qualified':False}


def verify_sdk_result(value, inspected):
    expected={'state':'pass','scope':'fresh_complete_sdk_candidates_and_plans','cases':15,'controls':17,'files':31,
              'manifest_sha256':inspected['manifest_sha256'],'native_session_started':False,'green_rows':0}
    require(type(value) is dict and prior.io.canonical(value)==prior.io.canonical(expected),'candidate_actual_sdk_cli_result_changed')
    return expected


def fresh_sdk(inspected):
    actual=subprocess.run(['cargo','run','--locked','--offline','--quiet','-p','hwpx-package','--example',EXAMPLE,
                          '--','--verify',str(DIRECTORY)],cwd=ROOT,capture_output=True,timeout=180,check=False)
    require(actual.returncode==0 and not actual.stderr.strip() and 0<len(actual.stdout)<=4096,
            'candidate_actual_fresh_sdk_cli_failed')
    return verify_sdk_result(json.loads(actual.stdout,object_pairs_hook=prior.io.duplicate_guard),inspected)


def verify():
    before=pins(); old=preservation(); inspected=inspect_files(); sdk=fresh_sdk(inspected)
    require(before==pins() and old==preservation() and inspected==inspect_files(),'candidate_inputs_changed_during_verification')
    return {'state':'pass','scope':'complete_actual_sdk_candidates_and_independent_worker_plans_not_native',
            'source_pins':len(before),'cases':15,'controls':17,'files':31,
            'manifest_sha256':inspected['manifest_sha256'],'bytes':inspected['candidate_and_plan_total_bytes'],
            'fresh_actual_sdk_cli_executed':sdk['state']=='pass','native_session_started':False,'green_rows':0}


def actual_suites():
    suites = [
        ('rust_candidate_tests', ['cargo','test','--locked','--offline','-p','hwpx-package','--example',EXAMPLE],
            {'tests::complete_fifteen_candidates_use_actual_sdk_and_external_verifier_and_preserve_intents',
             'tests::worker_plan_keeps_native_ids_missing_and_all_unicode_metachar_names_exact',
             'tests::public_manifest_is_hash_only_and_exclusive_output_boundaries_reject_aliases'}, 'rust'),
        ('python_candidate_tests', [sys.executable,'-E','-B','-X','utf8','-m','unittest','-v',
            'tools.p09.tests.test_native_form_control_candidates'],
            {'test_all_fifteen_persisted_actual_sdk_candidates_and_seventeen_python_plans_are_exact',
             'test_actual_fresh_rust_cli_reconstructs_all_candidates_and_checks_all_persisted_files',
             'test_manifest_rejects_inventory_substitution_coercion_extra_keys_and_native_promotions',
             'test_sdk_worker_plan_rejects_any_name_tab_color_identity_coordinate_or_type_drift',
             'test_fake_fresh_sdk_results_cannot_promote_native_partial_or_unbound_output',
             'test_original_frozen_sources_native_evidence_and_worker_library_remain_preserved'}, 'python'),
        ('python_worker_pure_metadata_tests', [sys.executable,'-E','-B','-X','utf8','-m','unittest','-v',
            'tools.p09.tests.test_native_form_control_plan'],
            {'test_all_original_fifteen_complete_intents_have_missing_native_ids_and_no_runtime_claim',
             'test_pure_worker_matches_all_original_cases_even_with_reversed_collection',
             'test_actual_x86_windows_powershell_pure_binding_preserves_all_fifteen_unicode_plans',
             'test_worker_rejects_missing_extra_ambiguous_wrong_type_or_anchor_scopes_before_writes',
             'test_worker_rejects_coerced_intents_and_false_runtime_promotions',
             'test_original_unicode_metachar_names_and_all_colors_are_exact_not_normalized',
             'test_source_substitution_protection_and_invented_native_id_are_rejected',
             'test_global_duplicate_tab_names_and_nested_paragraphs_are_rejected',
             'test_installed_property_metadata_and_frozen_source_inputs_remain_exact'}, 'python')]
    evidence = {}
    for label,command,names,kind in suites:
        actual=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180,check=False)
        require(actual.returncode==0 and len(actual.stdout)+len(actual.stderr)<=262144,'candidate_actual_suite_failed')
        text=(actual.stdout if kind=='rust' else actual.stderr).decode('utf-8',errors='strict')
        observed=[]
        for line in text.splitlines():
            if kind=='rust':
                match=re.fullmatch(r'test ([a-z0-9_:]+) \.\.\. ok',line)
            else:
                match=re.fullmatch(r'(test_[a-z0-9_]+) \([^\r\n]+\.([a-z0-9_]+)\) \.\.\. ok',line)
                if match:require(match[1]==match[2],'candidate_suite_method_identity')
            if match:observed.append(match[1])
        require(len(observed)==len(names) and set(observed)==names and text.count(' ... ')==len(names),
                'candidate_actual_suite_inventory')
        if kind=='rust':
            require(f'test result: ok. {len(names)} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' in text,
                    'candidate_actual_rust_suite_summary')
        else:
            require(not actual.stdout.strip() and 'skipped' not in text
                    and re.search(rf'\nRan {len(names)} tests in [0-9.]+s\s+OK\s*$',text),
                    'candidate_actual_python_suite_summary')
        evidence[label]={'passed':len(names),'failed':0,'errors':0,'skipped_or_ignored':0,
                         'method_names':sorted(names),'actually_invoked':True,'native_execution':False}
    clippy=subprocess.run(['cargo','clippy','--locked','--offline','-p','hwpx-package','--example',EXAMPLE,'--','-D','warnings'],
        cwd=ROOT,capture_output=True,timeout=180,check=False)
    require(clippy.returncode==0 and len(clippy.stdout)+len(clippy.stderr)<=262144,'candidate_actual_clippy_failed')
    evidence['actual_candidate_clippy_warnings_denied']={'state':'pass','actually_invoked':True}
    return evidence


def record():
    before=pins(); old=preservation(); inspected=inspect_files()
    sdk=fresh_sdk(inspected); suites=actual_suites()
    require(before==pins() and old==preservation() and inspected==inspect_files(),'candidate_record_inputs_changed')
    return {'schema_version':'hwpx-agent.p09-51-complete-coupled-native-candidate-progress/v1',
        'state':'actual_complete_sdk_candidates_and_worker_source_checks_pass_not_native_admission',
        'source_sha256':before,'preserved_original_source_and_native_evidence':old,
        'complete_persisted_candidate_and_plan_inventory':inspected,'actual_fresh_sdk_cli_verification':sdk,
        'actual_suites':suites,'claims':{'all_fifteen_original_cases_and_seventeen_controls_prepared':True,
            'complete_sdk_outputs_and_independent_worker_plans_exact':True,
            'native_worker_pure_metadata_tests_not_live_bindings':True,'native_source_admission_or_dispatcher_complete':False,
            'actual_native_control_identity_or_setter_or_rollback_qualified':False,
            'actual_native_save_reopen_render_differential_qualified':False,'new_native_session_started':False,
            'signed_form_route_publication_cas_idempotency_cli_full_import_or_p09_gate':False,'green_rows':0},
        'privacy':{'raw_document_values_or_absolute_private_paths_present':False,
            'original_inputs_failed_runs_or_security_settings_changed':False}}


def evidence_path(path):
    require(path.is_absolute() and '..' not in path.parts and path==ROOT/CAPSULE,'candidate_evidence_output_boundary')
    bounded(MANIFEST)
    if path.exists():bounded(path)
    return path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--verify',action='store_true');modes.add_argument('--output',type=Path)
    modes.add_argument('--verify-evidence',type=Path);args=parser.parse_args()
    try:
        if args.verify:result=verify()
        else:
            path=evidence_path(args.output or args.verify_evidence)
            require(not args.output or not path.exists(),'candidate_progress_receipt_already_exists')
            raw=prior.io.canonical(record())
            if args.output:
                with path.open('xb') as stream:stream.write(raw)
            else:require(bounded(path)==raw,'candidate_progress_fresh_complete_result_changed')
            result={'state':'pass','scope':'complete_sdk_candidates_and_worker_source_progress_not_native_admission',
                    'source_pins':9,'cases':15,'controls':17,'files':31,'bytes':len(raw),'sha256':plan.sha(raw),
                    'rust_tests':3,'python_candidate_tests':6,'python_pure_worker_tests':9,
                    'native_session_started':False,'green_rows':0}
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,subprocess.SubprocessError) as error:
        code=str(error) if type(error) is ValueError and re.fullmatch('[a-z_]+',str(error)) else type(error).__name__
        print(json.dumps({'state':'fail','error_code':code,'original_and_failed_evidence_not_removed':True}));return 2
    print(json.dumps(result));return 0


if __name__=='__main__':raise SystemExit(main())
