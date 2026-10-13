"""Protected P51-to-P50 complete source admission, without native activation."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import verify_native_form_control_candidates as candidate
from tools.p09 import qualify_native_owned_exit_wait_environment as environment

ROOT = candidate.ROOT
PREFIX = 'p09-52-20261003-r01'
ADMISSION = 'implementation/p09/evidence/p09-52-native-form-binding-admission.v1.json'
DISPATCH = 'implementation/p09/evidence/p09-52-native-form-binding-dispatch.r01.json'
HARNESS = 'implementation/p09/tools/run-hancom-2020-native-form-control-binding.ps1'
LIBRARY = 'implementation/p09/tools/native-form-control-binding.ps1'
PROBE = 'implementation/p09/tools/probe-hancom-native-form-binding-preflight-no-com.ps1'
INSPECTOR = 'tools/p09/inspect_native_form_binding_typelib.ps1'
HARNESS_SHA = '2777a290bc6b8442d125c6920a9ce68b851ef0500e8f86121fc9459e7204035f'
LIBRARY_SHA = 'c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183'
PROGRESS_SHA = '925ce0c7d134752f37cf3913d78e3f809c8e9bc3364e55849d5e3d0efddad2a8'
SOURCES = ('tools/p09/qualify_native_form_binding_batch.py',
    'tools/p09/run_native_form_binding_batch.py', 'tools/p09/tests/test_native_form_binding_batch.py',
    'implementation/p09/P09-52_NATIVE_FORM_BINDING_BATCH_POLICY.md', PROBE,
    'tools/p09/qualify_native_owned_exit_wait_environment.py')
GUARDS = {
    'test_complete_candidate_and_progress_graph_is_exact',
    'test_all_fifteen_fixed_cases_and_unused_paths_are_required',
    'test_case_subset_reordering_substitution_or_prior_prefix_is_rejected',
    'test_probe_is_exact_line_normalized_pre_native_prefix_and_stops_before_run',
    'test_child_environment_changes_only_module_path_not_parent_or_policy',
    'test_fixed_receipt_boundaries_reject_alias_relative_or_traversal',
    'test_trace_rejects_foreign_target_input_plan_library_and_cleanup',
    'test_synthetic_failed_trace_stays_failed_without_inventing_saved_outputs',
    'test_synthetic_pass_trace_requires_all_lifecycle_and_managed_stages',
    'test_trace_rejects_coercion_native_promotions_missing_sessions_and_duplicate_pid',
    'test_artifact_hashes_sizes_claims_and_partial_files_are_bound',
    'test_unknown_artifact_names_and_unclaimed_pass_outputs_are_rejected',
    'test_native_failure_inventory_is_bounded_and_never_contains_names_or_text',
    'test_no_com_prefix_rejects_substituted_input_plan_and_library_hashes',
    'test_dispatcher_has_only_complete_run_no_selection_retry_kill_or_public_action'}

require, sha, canonical = candidate.require, candidate.plan.sha, candidate.prior.io.canonical


def read_json(path, maximum=4194304):
    return json.loads(candidate.bounded(path, maximum), object_pairs_hook=candidate.prior.io.duplicate_guard)


def own_pins():
    return {name: sha(candidate.bounded(ROOT/name)) for name in SOURCES}


def fixed_path(path, kind):
    expected = ROOT/{'admission': ADMISSION, 'dispatch': DISPATCH}[kind]
    require(path.is_absolute() and '..' not in path.parts and path == expected,
            'binding_batch_receipt_boundary')
    # The existing regular manifest check establishes unlinked ROOT; the evidence
    # parent is separately checked, including all ancestors, before publication.
    environment.q.shared.within(path.parent, ROOT/'implementation/p09/evidence')
    if path.exists():
        candidate.bounded(path)
    return path


def inherited():
    raw = candidate.bounded(ROOT/candidate.CAPSULE)
    require(len(raw) == 8860 and sha(raw) == PROGRESS_SHA, 'binding_batch_progress_identity')
    value = json.loads(raw, object_pairs_hook=candidate.prior.io.duplicate_guard)
    require(value['source_sha256'] == candidate.pins(), 'binding_batch_original_source_changed')
    inspected = candidate.inspect_files()
    require(inspected == value['complete_persisted_candidate_and_plan_inventory'],
            'binding_batch_candidate_graph_changed')
    preserved = candidate.preservation()
    require(preserved == value['preserved_original_source_and_native_evidence'],
            'binding_batch_original_evidence_changed')
    require(sha(candidate.bounded(ROOT/HARNESS)) == HARNESS_SHA
            and sha(candidate.bounded(ROOT/LIBRARY)) == LIBRARY_SHA, 'binding_batch_native_worker_identity')
    return {'p51_progress_sha256': PROGRESS_SHA, 'p51_source_sha256': value['source_sha256'],
        'complete_candidate_inventory': inspected, 'preserved_original_evidence': preserved,
        'predecessor_full_workflows_reexecuted_here': False}


def run_directory(index):
    require(type(index) is int and 1 <= index <= 15, 'binding_batch_case_index')
    return ROOT/'implementation/p09/evidence/private'/(
        f'p09-17-field-auto-number-target-{PREFIX}-c{index:02}-attempt01')


def case_plan(rows, prefix=PREFIX, *, require_unused=True):
    require(prefix == PREFIX and type(rows) is list and len(rows) == 15,
            'binding_batch_complete_inventory')
    # Full original manifest validation rejects reordered/aliased/coerced rows.
    expected = candidate.validate_manifest(read_json(candidate.MANIFEST, 524288))
    require(canonical(rows) == canonical(expected), 'binding_batch_case_substitution')
    result = []
    for index, row in enumerate(rows, 1):
        path = run_directory(index)
        environment.q.shared.within(path.parent, ROOT/'implementation/p09/evidence/private')
        require(not require_unused or not path.exists(), 'binding_batch_attempt_exists')
        source, plan = candidate.MANIFEST.parent/row['file'], candidate.MANIFEST.parent/row['plan_file']
        require(sha(candidate.bounded(source)) == row['package_sha256']
                and sha(candidate.bounded(plan)) == row['plan_sha256'], 'binding_batch_case_input_changed')
        result.append((row, source, plan, path))
    return result


def hwp_zero():
    command = "if (@(Get-CimInstance Win32_Process -Filter \"Name='Hwp.exe'\" -ErrorAction Stop).Count -ne 0) {exit 2};[Console]::Write('P09_52_HWP_ZERO')"
    result = subprocess.run([str(environment.SHELL), '-NoProfile', '-Command', command],
        cwd=ROOT, env=environment.child_environment(), capture_output=True, timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW)
    require(result.returncode == 0 and result.stdout == b'P09_52_HWP_ZERO' and not result.stderr,
            'binding_batch_preexisting_hwp')


def prefix_inverse():
    original = candidate.bounded(ROOT/HARNESS).replace(b'\r\n', b'\n')
    marker = b'[void][IO.Directory]::CreateDirectory($run)'
    suffix = b"[Console]::Write('P09_52_EXACT_PRE_NATIVE_PREFIX_PASS')\nexit 0\n"
    probe = candidate.bounded(ROOT/PROBE).replace(b'\r\n', b'\n')
    require(sha(candidate.bounded(ROOT/HARNESS)) == HARNESS_SHA and original.count(marker) == 1
            and probe == original[:original.index(marker)]+suffix, 'binding_batch_probe_inverse')
    return {'entire_pre_native_prefix_exact_except_crlf_to_lf': True,
            'new_run_directory_and_native_body_excluded': True}


def command_for(row, source, plan, directory, *, probe=False):
    return [str(environment.SHELL), '-NoProfile', '-STA', '-File', str(ROOT/(PROBE if probe else HARNESS)),
        '-InputPath', str(source), '-ExpectedInputSha256', row['package_sha256'],
        '-RunDirectory', str(directory), '-PlanPath', str(plan), '-ExpectedPlanSha256', row['plan_sha256'],
        '-ExpectedBindingLibrarySha256', LIBRARY_SHA]


def actual_prefixes(cases):
    proof = []
    for row, source, plan, directory in cases:
        result = subprocess.run(command_for(row, source, plan, directory, probe=True), cwd=ROOT,
            env=environment.child_environment(), capture_output=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW)
        require(result.returncode == 0 and result.stdout == b'P09_52_EXACT_PRE_NATIVE_PREFIX_PASS'
                and not result.stderr and not directory.exists(), 'binding_batch_actual_prefix_failed')
        proof.append({'case_id': row['case_id'], 'exit_code': 0, 'exact_prefix_pass': True,
                      'new_run_directory_created': False, 'native_session_started': False})
    return proof


def actual_metadata():
    # Preserve P50's actual qualified static-reader host. Its explicit Registry32
    # and SYS_WIN32 TLB declarations identify x86, without native activation.
    # Legacy x86 Windows PowerShell is ONLY the native/prefix host, not this C# reader.
    result = subprocess.run(['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(ROOT/INSPECTOR)],
        cwd=ROOT, capture_output=True, timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW)
    require(result.returncode == 0 and not result.stderr and 0 < len(result.stdout) <= 262144,
            'binding_batch_installed_metadata_failed')
    value = json.loads(result.stdout, object_pairs_hook=candidate.prior.io.duplicate_guard)
    require(value['state'] == 'read_only_inspection_complete_not_native_qualification'
            and value['exact_build'] == '11.0.0.9136'
            and value['executable_sha256'] == '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'
            and value['registered_typelib_sha256'] == 'abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9'
            and value['registered_typelib_bytes'] == 473120
            and value['no_com_server_activation'] is True and value['registry_read_only'] is True
            and value['hwp_process_set_unchanged'] is True and value['p09_complete'] is False,
            'binding_batch_installed_metadata_identity')
    tlb = [b for b in value['binaries'] if b['binary_name'] == 'HwpObject.tlb']
    require(len(tlb) == 1 and tlb[0]['state'] == 'type_library_read', 'binding_batch_typelib_not_read')
    types = {t['name']: t for t in tlb[0]['surface']['selected_types']}
    declarations = []
    for interface, field, kind, member, returned, args in (
        ('IDHwpCtrlCode', 'GetAnchorPos', 'INVOKE_FUNC', 15000, 9, [(3, 0)]),
        ('IDHwpCtrlCode', 'Properties', 'INVOKE_PROPERTYPUT', 6, 24, [(9, 1)]),
        ('IDHwpParameterSet', 'Clone', 'INVOKE_FUNC', 15000, 9, []),
        ('IDHwpParameterSet', 'IsEquivalent', 'INVOKE_FUNC', 15004, 11, [(9, 1)]),
        ('IDHwpParameterSet', 'ItemExist', 'INVOKE_FUNC', 15006, 11, [(8, 1)]),
        ('IDHwpParameterSet', 'SetItem', 'INVOKE_FUNC', 15010, 24, [(8, 1), (12, 1)]),
        ('HShapeObject', 'ShapeFormCommonAttr', 'INVOKE_PROPERTYGET', 744, 9, []),
        ('HFormCommonAttr', 'name', 'INVOKE_PROPERTYPUT', 16416, 24, [(8, 1)]),
        ('HFormCommonAttr', 'TabOrder', 'INVOKE_PROPERTYPUT', 16421, 24, [(3, 1)]),
        ('HFormCommonAttr', 'Color', 'INVOKE_PROPERTYPUT', 16417, 24, [(19, 1)]),
        ('IHwpObject', 'RGBColor', 'INVOKE_FUNC', 30007, 3, [(17, 1), (17, 1), (17, 1)])):
        expected = {'name': field, 'member_id': member, 'invoke_kind': kind,
            'return_variant_type': returned, 'parameters': [{'variant_type': v, 'flags': f} for v, f in args]}
        actual = [m for m in types[interface]['members'] if m['name'] == field and m['invoke_kind'] == kind]
        require(actual == [expected], 'binding_batch_installed_member_changed')
        declarations.append({'interface': interface, **expected})
    return {'actual_read_only_inspector_invoked': True, 'complete_metadata_sha256': sha(canonical(value)),
        'registered_typelib_sha256': value['registered_typelib_sha256'], 'exact_runtime_member_declarations': declarations,
        'no_com_server_activation': True, 'declarations_are_not_runtime_binding': True}


def actual_prefix_rejections():
    row, source, plan, directory = case_plan(candidate.validate_manifest(read_json(candidate.MANIFEST, 524288)))[0]
    results = []
    for parameter, code in (
        ('-ExpectedInputSha256', 'INPUT_IDENTITY_MISMATCH'),
        ('-ExpectedPlanSha256', 'PLAN_IDENTITY_MISMATCH'),
        ('-ExpectedBindingLibrarySha256', 'LIBRARY_IDENTITY_MISMATCH')):
        command = command_for(row, source, plan, directory, probe=True)
        command[command.index(parameter)+1] = '0'*64
        actual = subprocess.run(command, cwd=ROOT, env=environment.child_environment(),
            capture_output=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        error = ('P09_NATIVE_FORM_CONTROL_BINDING_TARGET_'+code).encode('ascii')
        require(actual.returncode == 1 and not actual.stdout and error in actual.stderr
                and len(actual.stderr) <= 131072 and not directory.exists(),
                'binding_batch_actual_substitution_not_rejected')
        results.append({'parameter': parameter, 'exit_code': 1, 'error_code': error.decode('ascii'),
                        'new_run_directory_created': False, 'native_session_started': False})
    hwp_zero()
    return results


def actual_guards():
    result = subprocess.run([sys.executable, '-E', '-B', '-X', 'utf8', '-m', 'unittest', '-v',
        'tools.p09.tests.test_native_form_binding_batch'], cwd=ROOT, capture_output=True, timeout=180)
    require(result.returncode == 0 and not result.stdout.strip()
            and len(result.stderr) <= 262144, 'binding_batch_actual_guard_suite_failed')
    text = result.stderr.decode('utf-8', errors='strict')
    observed = []
    for line in text.splitlines():
        match = re.fullmatch(r'(test_[a-z0-9_]+) \([^\r\n]+\.([a-z0-9_]+)\) \.\.\. ok', line)
        if match:
            require(match[1] == match[2], 'binding_batch_guard_method_identity')
            observed.append(match[1])
    require(len(observed) == len(GUARDS) and set(observed) == GUARDS
            and text.count(' ... ') == len(GUARDS) and 'skipped' not in text
            and re.search(rf'\nRan {len(GUARDS)} tests in [0-9.]+s\s+OK\s*$', text),
            'binding_batch_guard_inventory')
    return {'actually_invoked': True, 'passed': len(GUARDS), 'failed': 0, 'errors': 0,
            'skipped': 0, 'method_names': sorted(observed), 'native_execution': False}


def qualify():
    before, parent = own_pins(), dict(os.environ)
    preserved = inherited()
    rows = candidate.validate_manifest(read_json(candidate.MANIFEST, 524288))
    cases = case_plan(rows)
    hwp_zero()
    inverse = prefix_inverse()
    module = environment.module_proof()  # Only this read-only helper; not old qualify/replay.
    metadata = actual_metadata()
    prefixes = actual_prefixes(cases)
    rejections = actual_prefix_rejections()
    guards = actual_guards()
    hwp_zero()
    require(before == own_pins() and preserved == inherited() and parent == dict(os.environ)
            and all(not c[3].exists() for c in cases), 'binding_batch_inputs_changed_during_admission')
    return {'schema_version': 'hwpx-agent.p09-52-native-form-binding-admission/v1',
        'state': 'complete_source_preflight_admitted_not_native_qualification', 'prefix': PREFIX,
        'source_sha256': before, 'inherited_exact_identity_graph': preserved,
        'harness_sha256': HARNESS_SHA, 'binding_library_sha256': LIBRARY_SHA,
        'prefix_inverse': inverse, 'actual_child_builtin_module_proof': module,
        'actual_installed_metadata': metadata, 'actual_all_fifteen_pre_native_prefixes': prefixes,
        'actual_no_com_hash_substitution_rejections': rejections,
        'actual_source_guards': guards, 'parent_environment_unchanged': True,
        'claims': {'all_fifteen_native_inputs_admitted': True, 'native_session_started': False,
            'native_identity_setter_rollback_save_reopen_render_or_product_qualified': False,
            'security_trust_registry_or_permission_settings_changed': False, 'green_rows': 0, 'p09_complete': False}}


def admitted():
    value = read_json(ROOT/ADMISSION)
    require(value['schema_version'] == 'hwpx-agent.p09-52-native-form-binding-admission/v1'
            and value['state'] == 'complete_source_preflight_admitted_not_native_qualification'
            and value['prefix'] == PREFIX and value['source_sha256'] == own_pins()
            and value['inherited_exact_identity_graph'] == inherited()
            and value['harness_sha256'] == HARNESS_SHA and value['binding_library_sha256'] == LIBRARY_SHA
            and value['actual_source_guards']['passed'] == len(GUARDS)
            and value['claims'] == {'all_fifteen_native_inputs_admitted': True, 'native_session_started': False,
                'native_identity_setter_rollback_save_reopen_render_or_product_qualified': False,
                'security_trust_registry_or_permission_settings_changed': False, 'green_rows': 0, 'p09_complete': False},
            'binding_batch_admission_unbound')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--output', type=Path); modes.add_argument('--verify', type=Path)
    args = parser.parse_args()
    try:
        path = fixed_path(args.output or args.verify, 'admission')
        require(not args.output or not path.exists(), 'binding_batch_admission_exists')
        raw = canonical(qualify())
        if args.output:
            with path.open('xb') as stream:
                stream.write(raw)
        else:
            require(candidate.bounded(path) == raw, 'binding_batch_fresh_admission_changed')
        result = {'state': 'pass', 'scope': 'actual_complete_source_admission_not_native',
            'sha256': sha(raw), 'bytes': len(raw), 'prefix_cases': 15, 'source_guard_tests': len(GUARDS),
            'native_session_started': False, 'green_rows': 0}
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch('[a-z_]+', str(error)) else type(error).__name__
        result = {'state': 'fail', 'error_code': code, 'partial_and_original_evidence_preserved': True}
    print(json.dumps(result))
    return 0 if result['state'] == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
