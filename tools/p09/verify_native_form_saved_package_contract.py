"""Independent exact saved-package contract and bound current P52 consumer; no COM."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_binding_batch as admission
from tools.p09 import run_native_form_binding_batch as dispatch_binder
from tools.p09 import diagnose_native_form_readback as historical

ROOT, require, sha, canonical = admission.ROOT, admission.require, admission.sha, admission.canonical
EXAMPLE = 'p09_53_native_form_saved_package_contract'
SOURCE_CAPSULE = 'implementation/p09/evidence/p09-53-saved-package-contract.source.v1.json'
CURRENT_CAPSULE = 'implementation/p09/evidence/p09-53-saved-package-contract.current-r01.v1.json'
ADMISSION_SHA = 'f33948527c1208019d3dc87693cf71c8a7e2cadbc9326feff66a6f9bae354752'
SOURCES = (f'crates/hwpx-package/examples/{EXAMPLE}.rs',
    'tools/p09/verify_native_form_saved_package_contract.py', 'tools/p09/tests/test_native_form_saved_package_contract.py',
    'implementation/p09/P09-53_NATIVE_FORM_SAVED_PACKAGE_CONTRACT_POLICY.md')
RUST_TESTS = {'all_fifteen_complete_sdk_outputs_pass_only_source_contract',
    'all_thirty_original_native_outputs_retain_full_package_failures',
    'unmanaged_parts_inventory_content_and_names_cannot_be_discarded',
    'invalid_archive_fails_closed_without_raw_exception_or_native_claims',
    'current_dispatch_absence_is_not_run_not_success',
    'actual_candidate_managed_name_change_rejects_without_replacing_expectation',
    'actual_unmanaged_header_bytes_change_cannot_be_normalized_away',
    'archive_recompression_is_not_document_mutation_or_native_acceptance'}
PYTHON_TESTS = {'test_real_complete_candidate_and_historical_stage_results_are_separate',
    'test_source_protocol_rejects_inventory_substitution_native_claims_or_changed_hash',
    'test_historical_original_source_bindings_and_native_failures_cannot_be_promoted',
    'test_current_dispatch_missing_is_not_run_without_fabricated_cases',
    'test_current_dispatch_envelope_rejects_subset_foreign_sources_or_native_promotions',
    'test_synthetic_current_results_bind_every_saved_stage_without_native_promotion',
    'test_fixed_exclusive_evidence_paths_and_preserved_source_graph'}
STAGE_BASE_KEYS = set(('state package_sha256 package_bytes expanded_parts public_package_reader complete_policy_binding '
    'complete_state_exact observed_state_sha256 complete_controls_exact full_package_bindings_exact document_flow_exact '
    'reference_overlay_exact expected_state_sha256 native_identity_or_setter_or_rollback_qualified '
    'render_or_differential_or_product_or_p09_gate_qualified').split())


def checked(path, digest, maximum=4194304):
    raw = admission.candidate.bounded(path, maximum)
    require(sha(raw) == digest, 'saved_contract_file_identity')
    return raw


def own_pins():
    return {name: sha(admission.candidate.bounded(ROOT/name)) for name in SOURCES}


def preservation():
    value = admission.admitted()
    checked(ROOT/admission.ADMISSION, ADMISSION_SHA)
    recovery = json.loads(checked(ROOT/historical.RECOVERY, historical.RECOVERY_SHA),
                          object_pairs_hook=admission.candidate.prior.io.duplicate_guard)
    pins = historical.native_pins(recovery)
    return {'p52_admission_sha256': ADMISSION_SHA, 'p52_source_sha256': value['source_sha256'],
        'inherited_exact_identity_graph': value['inherited_exact_identity_graph'],
        'all_seventy_five_original_native_sha256': pins, 'predecessor_workflows_reexecuted_here': False}


def fresh_cli(mode):
    require(mode in ('--source-self-check', '--historical', '--current-status', '--current'), 'saved_contract_cli_mode')
    result = subprocess.run(['cargo', 'run', '--locked', '--offline', '--quiet', '-p', 'hwpx-package',
        '--example', EXAMPLE, '--', mode], cwd=ROOT, capture_output=True, timeout=180)
    require(result.returncode == 0 and not result.stderr.strip() and 0 < len(result.stdout) <= 1048576,
            'saved_contract_actual_sdk_cli_failed')
    return json.loads(result.stdout, object_pairs_hook=admission.candidate.prior.io.duplicate_guard)


def validate_stage(value, expected_sha, package_sha, package_bytes, *, exact):
    require(type(value) is dict and STAGE_BASE_KEYS <= value.keys()
        and value.keys() <= STAGE_BASE_KEYS | {'policy_error_code', 'reader_error_code'}
        and value['state'] == ('exact_package_contract_not_native_acceptance' if exact else 'rejected')
        and value['package_sha256'] == package_sha and type(value['package_bytes']) is int
        and value['package_bytes'] == package_bytes and value['expected_state_sha256'] == expected_sha
        and value['public_package_reader'] == 'pass'
        and value['native_identity_or_setter_or_rollback_qualified'] is False
        and value['render_or_differential_or_product_or_p09_gate_qualified'] is False,
        'saved_contract_stage_identity_or_claim')
    parts = value['expanded_parts']
    require(type(parts) is dict and parts.keys() == {'state', 'expected_parts', 'observed_parts',
        'changed_parts', 'added_parts', 'removed_parts', 'all_expanded_part_bytes_checked',
        'xml_or_document_metadata_normalized', 'entry_names_or_raw_values_present'}
        and parts['all_expanded_part_bytes_checked'] is True
        and parts['xml_or_document_metadata_normalized'] is False and parts['entry_names_or_raw_values_present'] is False,
        'saved_contract_expanded_parts_scope')
    for key in ('expected_parts', 'observed_parts', 'changed_parts', 'added_parts', 'removed_parts'):
        require(type(parts[key]) is int and 0 <= parts[key] <= 512, 'saved_contract_part_counter')
    require(parts['expected_parts'] > 0 and parts['observed_parts'] > 0
        and parts['observed_parts'] == parts['expected_parts']+parts['added_parts']-parts['removed_parts']
        and parts['changed_parts'] <= min(parts['expected_parts']-parts['removed_parts'],
                                         parts['observed_parts']-parts['added_parts']), 'saved_contract_part_inventory')
    require(parts['state'] == ('exact' if exact else 'changed')
        and (parts['changed_parts']+parts['added_parts']+parts['removed_parts'] == 0) is exact,
        'saved_contract_part_failure_lost')
    for key in ('complete_state_exact', 'complete_controls_exact', 'full_package_bindings_exact',
                'document_flow_exact', 'reference_overlay_exact'):
        require(type(value[key]) is bool and (not exact or value[key] is True), 'saved_contract_full_state_check')
    if value['complete_policy_binding'] == 'pass':
        require(dispatch_binder.digest(value['observed_state_sha256'])
            and value['complete_state_exact'] is (value['observed_state_sha256'] == expected_sha)
            and 'policy_error_code' not in value, 'saved_contract_domain_state_binding')
    else:
        require(value['complete_policy_binding'] == 'fail' and value['observed_state_sha256'] is None
            and value['complete_state_exact'] is False
            and value.get('policy_error_code') == 'NATIVE_FORM_PACKAGE_POLICY_REJECTED', 'saved_contract_policy_failure_lost')


def validate_source(value):
    required = {'schema_version': 'hwpx-agent.p09-53-saved-package-contract-source/v1',
        'scope': 'all_fifteen_actual_sdk_candidates_positive_source_contract_not_native', 'state': 'pass',
        'manifest_sha256': 'c18e5d8b3c9af28367137735572b6842c56aca43b0676f40e48836fc4f7a51cd',
        'native_session_started': False, 'native_acceptance_qualified': False,
        'raw_document_values_or_private_paths_present': False, 'green_rows': 0, 'p09_complete': False}
    require(type(value) is dict and value.keys() == required.keys() | {'cases'}
        and all(type(value[k]) is type(v) and value[k] == v for k, v in required.items()), 'saved_contract_source_scope')
    rows = admission.candidate.validate_manifest(admission.read_json(admission.candidate.MANIFEST, 524288))
    require(type(value['cases']) is list and len(value['cases']) == 15, 'saved_contract_source_complete_inventory')
    for original, row in zip(rows, value['cases'], strict=True):
        require(type(row) is dict and row.keys() == {'case_id', 'source_self_contract'}
                and row['case_id'] == original['case_id'], 'saved_contract_source_case_identity')
        validate_stage(row['source_self_contract'], original['target_state_sha256'],
                       original['package_sha256'], original['package_bytes'], exact=True)
    return value


def validate_historical(value):
    required = {'schema_version': 'hwpx-agent.p09-53-saved-package-contract-historical/v1', 'state': 'pass',
        'scope': 'complete_historical_fifteen_case_thirty_saved_stages_failure_oracle',
        'original_manifest_sha256': historical.MANIFEST_SHA, 'recovery_sha256': historical.RECOVERY_SHA,
        'all_seventy_five_original_native_files_unchanged': True, 'native_session_started': False,
        'new_native_repair_or_p52_current_batch_qualified': False, 'raw_document_values_or_private_paths_present': False,
        'render_or_differential_or_product_qualified': False, 'green_rows': 0, 'p09_complete': False}
    require(type(value) is dict and value.keys() == required.keys() | {'cases'}
        and all(type(value[k]) is type(v) and value[k] == v for k, v in required.items()), 'saved_contract_historical_scope')
    rows = admission.read_json(ROOT/historical.MANIFEST)['cases']
    require(type(value['cases']) is list and len(value['cases']) == 15, 'saved_contract_historical_complete_inventory')
    for index, (original, row) in enumerate(zip(rows, value['cases'], strict=True), 1):
        require(type(row) is dict and row.keys() == {'case_id', 'actual_original_input_sha256', 'saved', 'reopened'}
            and row['case_id'] == original['case_id'] and row['actual_original_input_sha256'] == original['package_sha256'],
            'saved_contract_historical_original_source')
        directory = ROOT/'implementation/p09/evidence/private'/(
            f'p09-17-field-auto-number-target-p09-35-20261003-r05-c{index:02}-attempt01')
        trace = admission.read_json(directory/'target-trace.json', 262144)
        require(trace['input_sha256'] == original['package_sha256'], 'saved_contract_historical_trace_source')
        for stage, stem in (('saved', 'output'), ('reopened', 'reopened')):
            raw = checked(directory/f'{stage}.hwpx', trace[f'{stem}_sha256'])
            validate_stage(row[stage], original['target_state_sha256'], sha(raw), len(raw), exact=False)
    return value


def validate_not_run(value):
    expected = {'state': 'not_run', 'scope': 'p52_current_native_saved_package_contract',
        'reason': 'no_actual_p52_dispatch_receipt', 'actual_current_cases': 0,
        'native_session_started': False, 'green_rows': 0, 'p09_complete': False}
    require(type(value) is dict and canonical(value) == canonical(expected), 'saved_contract_missing_dispatch_promoted')
    return value


def validate_dispatch_envelope(value, admitted):
    required = {'schema_version': 'hwpx-agent.p09-52-native-form-binding-dispatch/v1',
        'state': 'all_fifteen_actual_attempts_terminal_non_green', 'prefix': admission.PREFIX,
        'admission_sha256': ADMISSION_SHA, 'source_sha256': admitted['source_sha256'],
        'harness_sha256': admission.HARNESS_SHA, 'binding_library_sha256': admission.LIBRARY_SHA,
        'permission_click_attestation': 'not_attested', 'computer_use_click_or_type_invoked': False,
        'claims': {'complete_fifteen_actual_diagnostic_attempts': True,
            'native_package_semantics_render_differential_or_product_qualified': False, 'green_rows': 0, 'p09_complete': False}}
    require(type(value) is dict and value.keys() == required.keys() | {'cases', 'native_evidence_sha256'}
        and all(type(value[k]) is type(v) and canonical(value[k]) == canonical(v) for k, v in required.items()),
        'saved_contract_current_dispatch_envelope')
    rows = value['cases']
    require(type(rows) is list and len(rows) == 15
        and all(type(row) is dict and row.get('case_id') == f'P09-35-C{index:02}'
                for index, row in enumerate(rows, 1)), 'saved_contract_current_complete_inventory')
    require(type(value['native_evidence_sha256']) is dict and 15 <= len(value['native_evidence_sha256']) <= 75,
            'saved_contract_current_native_inventory')


def bind_actual_current():
    admitted = admission.admitted()
    checked(ROOT/admission.ADMISSION, ADMISSION_SHA)
    value = admission.read_json(ROOT/admission.DISPATCH)
    validate_dispatch_envelope(value, admitted)
    rows = admission.candidate.validate_manifest(admission.read_json(admission.candidate.MANIFEST, 524288))
    pins = {}
    for (row, _, plan, directory), record in zip(admission.case_plan(rows, require_unused=False), value['cases'], strict=True):
        trace_raw = admission.candidate.bounded(directory/'target-trace.json', 262144)
        trace = json.loads(trace_raw, object_pairs_hook=admission.candidate.prior.io.duplicate_guard)
        bound = dispatch_binder.bind_case(trace, row, admission.read_json(plan, 262144), record['harness_exit'])
        bound['artifacts'] = dispatch_binder.actual_artifacts(directory, trace)
        require(bound == record, 'saved_contract_current_case_trace_unbound')
        pins[(directory/'target-trace.json').relative_to(ROOT).as_posix()] = sha(trace_raw)
        pins.update({(directory/name).relative_to(ROOT).as_posix(): item['sha256'] for name, item in bound['artifacts'].items()})
    require(pins == value['native_evidence_sha256'] and admission.admitted() == admitted,
            'saved_contract_current_evidence_changed')
    return value


def current_observation():
    if not (ROOT/admission.DISPATCH).exists():
        return validate_not_run(fresh_cli('--current'))
    before = bind_actual_current()
    observed = fresh_cli('--current')
    validate_current(observed, before, sha(admission.candidate.bounded(ROOT/admission.DISPATCH)))
    require(bind_actual_current() == before, 'saved_contract_actual_current_binding')
    return observed


def validate_current(observed, dispatch, dispatch_sha):
    required = {'schema_version': 'hwpx-agent.p09-53-saved-package-contract-current/v1', 'state': 'pass',
        'scope': 'actual_current_fifteen_bound_saved_package_checks_not_render_or_product',
        'actual_dispatch_sha256': dispatch_sha,
        'candidate_manifest_sha256': 'c18e5d8b3c9af28367137735572b6842c56aca43b0676f40e48836fc4f7a51cd',
        'native_session_started': False, 'raw_document_values_or_private_paths_present': False,
        'native_identity_or_setter_or_rollback_qualified': False, 'render_or_differential_or_product_qualified': False,
        'green_rows': 0, 'p09_complete': False}
    require(type(observed) is dict and observed.keys() == required.keys() | {'cases'}
        and all(type(observed[k]) is type(v) and observed[k] == v for k, v in required.items())
        and type(observed['cases']) is list and len(observed['cases']) == 15, 'saved_contract_current_result_scope')
    rows = admission.candidate.validate_manifest(admission.read_json(admission.candidate.MANIFEST, 524288))
    for source, result, record in zip(rows, observed['cases'], dispatch['cases'], strict=True):
        require(type(result) is dict and result.keys() == {'case_id', 'actual_candidate_input_sha256', 'saved', 'reopened'}
            and result['case_id'] == source['case_id'] == record['case_id']
            and result['actual_candidate_input_sha256'] == source['package_sha256'], 'saved_contract_current_source_binding')
        for stage in ('saved', 'reopened'):
            actual = result[stage]
            artifact = record['artifacts'].get(f'{stage}.hwpx')
            if not artifact or artifact['lifecycle_claim_bound'] is False:
                require(actual == {'state': 'not_run', 'reason': 'actual_native_stage_not_saved',
                    'native_package_semantics_or_render_or_product_qualified': False}, 'saved_contract_unsaved_stage_promoted')
            elif actual.get('public_package_reader') == 'pass':
                validate_stage(actual, source['target_state_sha256'], artifact['sha256'], artifact['bytes'],
                               exact=actual.get('state') == 'exact_package_contract_not_native_acceptance')
            else:
                require(type(actual) is dict and actual.keys() == STAGE_BASE_KEYS | {'reader_error_code'}
                    and actual['state'] == 'rejected' and actual['public_package_reader'] == 'fail'
                    and actual['complete_policy_binding'] == 'not_run'
                    and actual['package_sha256'] == artifact['sha256'] and type(actual['package_bytes']) is int
                    and actual['package_bytes'] == artifact['bytes']
                    and actual['expected_state_sha256'] == source['target_state_sha256']
                    and type(actual['reader_error_code']) is str and re.fullmatch('NATIVE_FORM_PACKAGE_[A-Z_]+', actual['reader_error_code'])
                    and all(actual[k] is None for k in ('complete_state_exact', 'observed_state_sha256',
                        'complete_controls_exact', 'full_package_bindings_exact', 'document_flow_exact', 'reference_overlay_exact'))
                    and actual['native_identity_or_setter_or_rollback_qualified'] is False
                    and actual['render_or_differential_or_product_or_p09_gate_qualified'] is False,
                    'saved_contract_current_reader_failure_lost')
                parts = actual['expanded_parts']
                if parts.get('state') == 'rejected':
                    require(parts == {'state': 'rejected', 'error_code': 'P09_SAVED_PACKAGE_ZIP_REJECTED'},
                            'saved_contract_current_zip_failure_scope')
                else:
                    require(parts.keys() == {'state', 'expected_parts', 'observed_parts', 'changed_parts',
                        'added_parts', 'removed_parts', 'all_expanded_part_bytes_checked',
                        'xml_or_document_metadata_normalized', 'entry_names_or_raw_values_present'}
                        and parts['state'] in ('exact', 'changed') and parts['all_expanded_part_bytes_checked'] is True
                        and parts['xml_or_document_metadata_normalized'] is False
                        and parts['entry_names_or_raw_values_present'] is False
                        and all(type(parts[k]) is int and 0 <= parts[k] <= 512 for k in (
                            'expected_parts', 'observed_parts', 'changed_parts', 'added_parts', 'removed_parts')),
                        'saved_contract_current_reader_part_scope')


def actual_suites():
    result = {}
    suites = [('rust', ['cargo', 'test', '--locked', '--offline', '-p', 'hwpx-package', '--example', EXAMPLE], RUST_TESTS),
        ('python', [sys.executable, '-E', '-B', '-X', 'utf8', '-m', 'unittest', '-v',
                    'tools.p09.tests.test_native_form_saved_package_contract'], PYTHON_TESTS)]
    for kind, command, names in suites:
        actual = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
        require(actual.returncode == 0 and len(actual.stdout)+len(actual.stderr) <= 262144,
                'saved_contract_actual_suite_failed')
        text = (actual.stdout if kind == 'rust' else actual.stderr).decode('utf-8', errors='strict')
        observed = []
        for line in text.splitlines():
            pattern = r'test tests::([a-z0-9_]+) \.\.\. ok' if kind == 'rust' else r'(test_[a-z0-9_]+) \([^\r\n]+\.([a-z0-9_]+)\) \.\.\. ok'
            match = re.fullmatch(pattern, line)
            if match:
                require(kind == 'rust' or match[1] == match[2], 'saved_contract_suite_method_identity')
                observed.append(match[1])
        require(len(observed) == len(names) and set(observed) == names and text.count(' ... ') == len(names),
                'saved_contract_actual_suite_inventory')
        if kind == 'rust':
            require(f'test result: ok. {len(names)} passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' in text,
                    'saved_contract_rust_suite_summary')
        else:
            require(not actual.stdout.strip() and 'skipped' not in text
                and re.search(rf'\nRan {len(names)} tests in [0-9.]+s\s+OK\s*$', text), 'saved_contract_python_suite_summary')
        result[kind] = {'actually_invoked': True, 'passed': len(names), 'failed': 0, 'errors': 0,
            'skipped_or_ignored': 0, 'method_names': sorted(observed), 'native_execution': False}
    clippy = subprocess.run(['cargo', 'clippy', '--locked', '--offline', '-p', 'hwpx-package', '--example', EXAMPLE,
                            '--', '-D', 'warnings'], cwd=ROOT, capture_output=True, timeout=180)
    require(clippy.returncode == 0 and len(clippy.stdout)+len(clippy.stderr) <= 262144, 'saved_contract_clippy_failed')
    result['actual_clippy_warnings_denied'] = True
    return result


def source_record():
    before, preserved = own_pins(), preservation()
    source = validate_source(fresh_cli('--source-self-check'))
    old = validate_historical(fresh_cli('--historical'))
    status = current_observation()
    require(status['state'] == 'not_run', 'saved_contract_source_receipt_not_native_successor')
    suites = actual_suites()
    require(before == own_pins() and preserved == preservation(), 'saved_contract_sources_or_originals_changed')
    return {'schema_version': 'hwpx-agent.p09-53-saved-package-contract-source-receipt/v1',
        'state': 'actual_complete_package_contract_source_and_historical_failure_oracle_not_current_native',
        'source_sha256': before, 'preserved_original_sources_and_native_files': preserved,
        'actual_all_fifteen_candidate_source_contracts': source, 'actual_all_thirty_historical_saved_contracts': old,
        'actual_current_native_status': status, 'actual_suites': suites,
        'claims': {'new_native_session_started': False, 'actual_p52_native_package_contract_tested': False,
            'native_setters_rollback_render_differential_signed_route_or_product_qualified': False,
            'predecessor_full_workflows_or_whole_ordinary_suites_reexecuted_here': False, 'green_rows': 0, 'p09_complete': False}}


def evidence_path(path, current=False):
    expected = ROOT/(CURRENT_CAPSULE if current else SOURCE_CAPSULE)
    require(path.is_absolute() and '..' not in path.parts and path == expected, 'saved_contract_evidence_boundary')
    admission.environment.q.shared.within(path.parent, ROOT/'implementation/p09/evidence')
    if path.exists(): admission.candidate.bounded(path)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', action='store_true')
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--output', type=Path); modes.add_argument('--verify', type=Path)
    args = parser.parse_args()
    try:
        path = evidence_path(args.output or args.verify, args.current)
        require(not args.output or not path.exists(), 'saved_contract_evidence_exists')
        if args.current:
            preserved, before = preservation(), own_pins()
            observed = current_observation()
            if observed['state'] == 'not_run':
                print(json.dumps(observed)); return 0  # No invented current evidence file.
            require(preserved == preservation() and before == own_pins(), 'saved_contract_current_sources_changed')
            value = {'schema_version': 'hwpx-agent.p09-53-bound-current-package-contract-receipt/v1',
                     'source_sha256': before, 'preserved_original_sources_and_native_files': preserved,
                     'actual_bound_current_observation': observed, 'p09_complete': False}
        else:
            value = source_record()
        raw = canonical(value)
        if args.output:
            with path.open('xb') as stream: stream.write(raw)
        else:
            require(admission.candidate.bounded(path) == raw, 'saved_contract_fresh_complete_result_changed')
        result = {'state': 'pass', 'scope': 'bound_current_package_contract_only' if args.current else 'complete_saved_package_source_contract_not_native',
            'bytes': len(raw), 'sha256': sha(raw), 'rust_tests': len(RUST_TESTS), 'python_tests': len(PYTHON_TESTS),
            'new_native_session_started': False, 'green_rows': 0}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch('[a-z_]+', str(error)) else type(error).__name__
        result = {'state': 'fail', 'error_code': code, 'partial_and_original_evidence_preserved': True}
    print(json.dumps(result)); return 0 if result['state'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
