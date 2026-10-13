"""One complete protected fifteen-case native batch; user owns all permissions."""
from __future__ import annotations
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import qualify_native_form_binding_batch as a

LIFECYCLE = ('first_open', 'first_save', 'pdf_export', 'fresh_reopen', 'fresh_reopen_save', 'fresh_reopen_pdf_export')
MANAGED = ('native_form_first_application', 'native_form_after_first_save',
           'native_form_fresh_reopen', 'native_form_after_reopened_save')
OUTPUTS = {'saved.hwpx': ('output', 'first_save', 4194304), 'saved.pdf': ('pdf', 'pdf_export', 33554432),
    'reopened.hwpx': ('reopened', 'fresh_reopen_save', 4194304),
    'reopened.pdf': ('reopened_pdf', 'fresh_reopen_pdf_export', 33554432)}
TRACE_KEYS = set(('schema_version state started_at_utc completed_at_utc target input_sha256 input_bytes security_module '
    'sessions quit_invoked remaining_hwp_process_count failed_phase error_code raw_document_text_present '
    'native_form_plan_sha256 native_form_binding_library_sha256 native_form_binding_failure '
    'native_semantics_render_or_p09_gate_qualified user_document_scanned external_network_invoked '
    'registry_or_system_setting_changed computer_use_click_or_type_invoked').split()) | set(LIFECYCLE) | set(MANAGED) | {
    f'{stem}_{suffix}' for stem, _, _ in OUTPUTS.values() for suffix in ('sha256', 'bytes')}
TARGET = {'product': 'Hancom Hangul 2020', 'build': '11.0.0.9136', 'architecture': 'x86',
    'locale': 'ko-KR', 'prog_id': 'HWPFrame.HwpObject.2',
    'executable_sha256': '7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'}
FALSE_FIELDS = ('raw_document_text_present', 'native_semantics_render_or_p09_gate_qualified',
    'user_document_scanned', 'external_network_invoked', 'registry_or_system_setting_changed',
    'computer_use_click_or_type_invoked')


def integer(value, minimum=0, maximum=2147483647):
    return type(value) is int and minimum <= value <= maximum


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def observed_inventory(counts, anchors):
    a.require(type(counts) is dict and 1 <= len(counts) <= 4096
        and all(type(k) is str and re.fullmatch(r'[A-Za-z0-9$%+ ]{1,4}', k) and integer(v, 1, 4096)
                for k, v in counts.items()) and sum(counts.values()) <= 4096,
        'binding_batch_observed_type_inventory')
    a.require(type(anchors) is list and len(anchors) <= 4096, 'binding_batch_observed_anchor_inventory')
    for row in anchors:
        a.require(type(row) is dict and row.keys() == {'ctrl_type', 'local_anchor', 'top_anchor', 'root_anchor'}
                  and row['ctrl_type'] in ('+edt', '+rbt'), 'binding_batch_observed_anchor_type')
        for key in ('local_anchor', 'top_anchor', 'root_anchor'):
            value = row[key]
            a.require(type(value) is dict and value.keys() == {'List', 'Para', 'Pos'}
                      and all(integer(v) for v in value.values()), 'binding_batch_observed_anchor_scope')


def managed_result(value, row, plan, *, verify_only):
    required = {'state': 'managed_property_check_pass_not_saved_package_qualification',
        'matched_controls': row['controls'], 'verify_only': verify_only,
        'binding_uses_collection_index_or_reservation_id': False, 'pos_inferred_from_xml': False,
        'unmanaged_runtime_parameters_checked': not verify_only,
        'native_save_reopen_render_qualified': False, 'p09_complete': False}
    a.require(type(value) is dict and value.keys() == required.keys() | {
        'walked_controls', 'observed_control_type_counts', 'observed_anchor_inventory'}
        and all(type(value[k]) is type(v) and value[k] == v for k, v in required.items())
        and integer(value['walked_controls'], row['controls'], 4096), 'binding_batch_managed_result_scope')
    counts, anchors = value['observed_control_type_counts'], value['observed_anchor_inventory']
    observed_inventory(counts, anchors)
    a.require(sum(counts.values()) == value['walked_controls'] and len(anchors) == row['controls'],
              'binding_batch_managed_inventory_count')
    expected = {(c['native_ctrl_type'], c['runtime_anchor_candidate']['List'],
                 c['runtime_anchor_candidate']['Para']) for c in plan['controls']}
    observed = set()
    for anchor in anchors:
        root = anchor['root_anchor']
        a.require(anchor['local_anchor'] == root and anchor['top_anchor'] == root,
                  'binding_batch_managed_anchor_scopes_differ')
        key = (anchor['ctrl_type'], root['List'], root['Para'])
        a.require(key not in observed, 'binding_batch_managed_anchor_ambiguous')
        observed.add(key)
    a.require(observed == expected, 'binding_batch_managed_anchor_plan_unbound')


def bind_case(trace, row, plan, code):
    a.require(type(trace) is dict and trace.keys() == TRACE_KEYS, 'binding_batch_trace_schema')
    a.require(trace['schema_version'] == 'hwpx-agent.p09-50-native-form-control-binding-target-trace/v1'
        and trace['target'] == TARGET and trace['input_sha256'] == row['package_sha256']
        and integer(trace['input_bytes'], 1, 4194304) and trace['input_bytes'] == row['package_bytes']
        and trace['native_form_plan_sha256'] == row['plan_sha256']
        and trace['native_form_binding_library_sha256'] == a.LIBRARY_SHA
        and trace['security_module'] == {'name': 'FilePathCheckerModuleExample',
            'sha256': '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6', 'preflight_state': 'pass'},
        'binding_batch_trace_identity')
    a.require(all(trace[k] is False for k in FALSE_FIELDS)
        and type(trace['quit_invoked']) is bool and type(trace['remaining_hwp_process_count']) is int
        and trace['remaining_hwp_process_count'] == 0, 'binding_batch_trace_cleanup_or_claim')
    for key in ('started_at_utc', 'completed_at_utc'):
        a.require(type(trace[key]) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{1,7}Z', trace[key]),
                  'binding_batch_trace_timestamp')
    a.require(datetime.fromisoformat(trace['completed_at_utc'].replace('Z', '+00:00')) >=
              datetime.fromisoformat(trace['started_at_utc'].replace('Z', '+00:00')), 'binding_batch_trace_time_order')
    sessions = trace['sessions']
    a.require(type(sessions) is list and len(sessions) <= 2, 'binding_batch_trace_session_inventory')
    seen = set()
    for index, session in enumerate(sessions):
        a.require(type(session) is dict and session.keys() == {'label', 'version', 'register_module_return', 'process'}
            and session['label'] == ('save', 'reopen')[index] and session['version'] == '11.0.0.9136'
            and type(session['register_module_return']) is bool, 'binding_batch_trace_session_identity')
        process = session['process']
        a.require(type(process) is dict and process.keys() == {
            'process_id', 'session_id', 'executable_sha256', 'command_line_sha256'}
            and integer(process['process_id'], 1) and integer(process['session_id'])
            and process['executable_sha256'] == TARGET['executable_sha256'] and digest(process['command_line_sha256'])
            and process['process_id'] not in seen, 'binding_batch_trace_owned_process')
        seen.add(process['process_id'])
    passed = trace['state'] == 'pass'
    a.require(trace['state'] in ('pass', 'effect_unknown') and type(code) is int and code == (0 if passed else 2),
              'binding_batch_trace_terminal_exit')
    gap = False
    for key in LIFECYCLE:
        a.require(trace[key] in ('pass', 'not_run'), 'binding_batch_trace_lifecycle_state')
        if trace[key] == 'not_run':
            gap = True
        else:
            a.require(not gap and len(sessions) >= (2 if key.startswith('fresh') else 1),
                      'binding_batch_trace_lifecycle_order')
    for index, key in enumerate(MANAGED):
        if trace[key] is not None:
            managed_result(trace[key], row, plan, verify_only=index != 0)
            required = ('first_open', 'first_save', 'fresh_reopen', 'fresh_reopen_save')[index]
            a.require(trace[required] == 'pass' and all(trace[k] is not None for k in MANAGED[:index]),
                      'binding_batch_trace_managed_stage_order')
    for lifecycle, managed in (('first_save', MANAGED[0]), ('pdf_export', MANAGED[1]),
                               ('fresh_reopen_save', MANAGED[2]), ('fresh_reopen_pdf_export', MANAGED[3])):
        a.require(trace[lifecycle] != 'pass' or trace[managed] is not None,
                  'binding_batch_trace_missing_prior_managed_stage')
    for _, (stem, stage, bound) in OUTPUTS.items():
        hash_value, size = trace[f'{stem}_sha256'], trace[f'{stem}_bytes']
        a.require((hash_value is None and size is None and trace[stage] == 'not_run')
            or (digest(hash_value) and integer(size, 1, bound) and trace[stage] == 'pass'),
            'binding_batch_trace_output_claim')
    failure = trace['native_form_binding_failure']
    if passed:
        a.require(len(sessions) == 2 and trace['quit_invoked'] is True
            and all(trace[k] == 'pass' for k in LIFECYCLE) and all(trace[k] is not None for k in MANAGED)
            and trace['failed_phase'] is None and trace['error_code'] is None and failure is None,
            'binding_batch_trace_pass_incomplete')
    else:
        a.require(type(trace['failed_phase']) is str and re.fullmatch('[a-z_]{1,80}', trace['failed_phase'])
            and type(trace['error_code']) is str and re.fullmatch('[A-Z0-9_]{1,256}', trace['error_code']),
            'binding_batch_trace_failed_terminal')
        if failure is not None:
            a.require(type(failure) is dict and failure.keys() == {'error_code', 'rollback_state',
                'observed_control_type_counts', 'observed_anchor_inventory', 'raw_names_text_or_payload_present'}
                and failure['raw_names_text_or_payload_present'] is False
                and type(failure['error_code']) is str and re.fullmatch('P09_FORM_[A-Z_]{1,128}', failure['error_code'])
                and failure['rollback_state'] in ('not_needed', 'attempted_not_yet_verified',
                    'runtime_parameters_restored_not_saved_package_proof', 'failed_preserve_evidence_and_close_without_save'),
                'binding_batch_trace_failure_scope')
            # Counts may be empty if the native walk failed before reading its first control.
            if failure['observed_control_type_counts']:
                observed_inventory(failure['observed_control_type_counts'], failure['observed_anchor_inventory'])
            else:
                a.require(failure['observed_control_type_counts'] == {} and failure['observed_anchor_inventory'] == [],
                          'binding_batch_trace_empty_failure_inventory')
    return {'case_id': row['case_id'], 'harness_exit': code, 'lifecycle': 'pass' if passed else 'fail',
        'sessions': len(sessions), 'managed_stages_passed': sum(trace[k] is not None for k in MANAGED),
        'failed_phase': trace['failed_phase'], 'error_code': trace['error_code'],
        'native_package_semantics_render_or_product_qualified': False}


def bind_artifacts(trace, artifacts):
    a.require(type(artifacts) is dict and artifacts.keys() <= OUTPUTS.keys(), 'binding_batch_unknown_artifact')
    result = {}
    for name, (stem, stage, bound) in OUTPUTS.items():
        claimed = trace[f'{stem}_sha256'] is not None
        raw = artifacts.get(name)
        a.require(not claimed or raw is not None, 'binding_batch_claimed_artifact_missing')
        if raw is None:
            continue
        a.require(type(raw) is bytes and len(raw) <= bound, 'binding_batch_artifact_bound')
        if claimed:
            a.require(a.sha(raw) == trace[f'{stem}_sha256'] and len(raw) == trace[f'{stem}_bytes']
                and (not name.endswith('.pdf') or raw.startswith(b'%PDF-')), 'binding_batch_artifact_identity')
        else:
            a.require(trace['state'] != 'pass', 'binding_batch_unclaimed_pass_artifact')
        result[name] = {'sha256': a.sha(raw), 'bytes': len(raw),
            'lifecycle_claim_bound': claimed, 'partial_unqualified_preserved': not claimed}
    return result


def actual_artifacts(directory, trace):
    a.require(directory.exists() and {p.name for p in directory.iterdir()} <= OUTPUTS.keys() | {'target-trace.json'},
              'binding_batch_private_file_inventory')
    raw = {name: a.candidate.bounded(directory/name, bound) for name, (_, _, bound) in OUTPUTS.items()
           if (directory/name).exists()}
    return bind_artifacts(trace, raw)


def run():
    output = a.fixed_path(a.ROOT/a.DISPATCH, 'dispatch')
    a.require(not output.exists(), 'binding_batch_dispatch_exists')
    admission = a.admitted()
    admission_raw = a.candidate.bounded(a.ROOT/a.ADMISSION)
    rows = a.candidate.validate_manifest(a.read_json(a.candidate.MANIFEST, 524288))
    cases = a.case_plan(rows)
    a.hwp_zero()
    # Actual current metadata/module/preflight again immediately before activation.
    a.require(a.actual_metadata() == admission['actual_installed_metadata']
        and a.environment.module_proof() == admission['actual_child_builtin_module_proof'],
        'binding_batch_environment_changed_since_admission')
    a.actual_prefixes(cases)
    records, native_pins = [], {}
    for row, source, plan_path, directory in cases:
        a.require(a.admitted() == admission and a.candidate.bounded(a.ROOT/a.ADMISSION) == admission_raw,
                  'binding_batch_admitted_inputs_changed')
        a.hwp_zero()
        print(json.dumps({'event': 'case_start', 'case_id': row['case_id'], 'of': 15}), flush=True)
        # No permission timeout, relaunch, UI click, forced kill or automatic retry.
        process = subprocess.Popen(a.command_for(row, source, plan_path, directory), cwd=a.ROOT,
            env=a.environment.child_environment(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW)
        size = 0
        for line in process.stdout:
            size += len(line)
            if line.strip() in (b'P09_NATIVE_FORM_BINDING_READY_FOR_INPUT_OPEN',
                                 b'P09_NATIVE_FORM_BINDING_READY_FOR_FRESH_REOPEN'):
                print(json.dumps({'event': line.strip().decode('ascii'), 'case_id': row['case_id']}), flush=True)
        code = process.wait()
        a.require(size <= 262144, 'binding_batch_child_output_limit')
        a.hwp_zero()
        trace_raw = a.candidate.bounded(directory/'target-trace.json', 262144)
        trace = json.loads(trace_raw, object_pairs_hook=a.candidate.prior.io.duplicate_guard)
        record = bind_case(trace, row, a.read_json(plan_path, 262144), code)
        artifacts = actual_artifacts(directory, trace)
        record['artifacts'] = artifacts
        records.append(record)
        native_pins[(directory/'target-trace.json').relative_to(a.ROOT).as_posix()] = a.sha(trace_raw)
        native_pins.update({(directory/name).relative_to(a.ROOT).as_posix(): item['sha256']
                            for name, item in artifacts.items()})
        a.require(a.admitted() == admission, 'binding_batch_original_sources_changed_after_case')
        print(json.dumps({k: v for k, v in record.items() if k != 'artifacts'}), flush=True)
    # Rebind every actual trace/output at completion, not only accumulated status.
    for row, _, plan_path, directory in cases:
        index = rows.index(row)
        trace = a.read_json(directory/'target-trace.json', 262144)
        rebound = bind_case(trace, row, a.read_json(plan_path, 262144), records[index]['harness_exit'])
        rebound['artifacts'] = actual_artifacts(directory, trace)
        a.require(rebound == records[index], 'binding_batch_actual_trace_changed')
    for name, expected in native_pins.items():
        a.require(a.sha(a.candidate.bounded(a.ROOT/name, 33554432)) == expected, 'binding_batch_native_files_changed')
    a.require(a.admitted() == admission, 'binding_batch_final_source_changed')
    value = {'schema_version': 'hwpx-agent.p09-52-native-form-binding-dispatch/v1',
        'state': 'all_fifteen_actual_attempts_terminal_non_green', 'prefix': a.PREFIX,
        'admission_sha256': a.sha(admission_raw), 'source_sha256': admission['source_sha256'],
        'harness_sha256': a.HARNESS_SHA, 'binding_library_sha256': a.LIBRARY_SHA,
        'cases': records, 'native_evidence_sha256': native_pins,
        'permission_click_attestation': 'not_attested', 'computer_use_click_or_type_invoked': False,
        'claims': {'complete_fifteen_actual_diagnostic_attempts': True,
            'native_package_semantics_render_differential_or_product_qualified': False,
            'green_rows': 0, 'p09_complete': False}}
    with output.open('xb') as stream:
        stream.write(a.canonical(value))
    print(json.dumps({'state': 'pass', 'actual_attempts': 15,
        'lifecycle_pass': sum(r['lifecycle'] == 'pass' for r in records),
        'managed_stages_passed': sum(r['managed_stages_passed'] for r in records),
        'native_package_semantics_qualified': False, 'green_rows': 0}), flush=True)


if __name__ == '__main__':
    try:
        # No selectable command-line cases or paths. Reject unexpected options.
        a.require(len(sys.argv) == 1, 'binding_batch_arguments_rejected')
        run()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, subprocess.SubprocessError) as error:
        code = str(error) if type(error) is ValueError and re.fullmatch('[a-z_]+', str(error)) else type(error).__name__
        print(json.dumps({'state': 'fail', 'error_code': code, 'partial_evidence_preserved': True}), flush=True)
        raise SystemExit(2)
