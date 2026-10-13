"""Fixed current17 SDK baselines and actual child binding; no default activation."""
from datetime import timedelta
import json
import re
import subprocess
import zipfile
from tools.p09 import verify_reference_pdf_render as previous

c, r, q = previous.c, previous.r, previous.q
ROOT, canonical, sha, require = q.ROOT, q.canonical, q.sha, q.require
HARNESS = 'implementation/p09/tools/run-hancom-2020-sdk-baseline-capture.ps1'
LIBRARY = 'implementation/p09/tools/sdk-baseline-owned-session.ps1'
BUNDLE = 'implementation/p09/evidence/private/p09-58-sdk-baseline-plans-20261003-r01/capture-manifest.json'
CAPSULE = 'implementation/p09/evidence/p09-58-sdk-baseline-capture.source.v1.json'
DISPATCH = 'implementation/p09/evidence/p09-58-sdk-baseline-complete34.dispatch-r01.v1.json'
P57_SHA = 'c001c5f34fcbc4310c5d531954712ca911a471301a24d29bd35ec44f3d18335d'
COMPLETE = 'sdk_baseline_lifecycle_completed_not_semantic_or_render_acceptance'
FALSE_FIELDS = ('managed_document_setter_invoked', 'human_authored_direct_oracle',
    'computer_use_click_or_type_invoked', 'raw_document_values_present', 'registry_or_system_setting_changed',
    'external_network_invoked', 'native_package_render_differential_or_product_qualified', 'p09_complete')
TRACE_KEYS = set(('schema_version case_id capture_index state started_at_utc completed_at_utc target '
    'source_sha256 source_bytes bundle_sha256 harness_sha256 owned_library_sha256 security_module_sha256 sessions '
    'artifacts failed_phase error_code source_identity_preserved remaining_hwp_process_count').split()) | set(FALSE_FIELDS)
PHASES = {'first_session_create': ((0,), (0, 1)), 'source_open': ((0,), (1,)),
    'first_save': ((0, 1), (1,)), 'first_pdf': ((1, 2), (1,)), 'first_owner_cleanup': ((2,), (1,)),
    'fresh_session_create': ((2,), (1, 2)), 'fresh_saved_open': ((2,), (2,)),
    'fresh_reopened_save': ((2, 3), (2,)), 'fresh_pdf': ((3, 4), (2,)),
    'source_identity_check': ((0, 1, 2, 3, 4), (0, 1, 2))}


def predecessor():
    raw = r.bounded(ROOT / previous.CAPSULE, P57_SHA)
    value = previous.admitted()
    require(value['source_sha256'] == previous.pins() and raw == r.bounded(ROOT / previous.CAPSULE, P57_SHA),
            'p58_original_source_admission_changed')
    # P57 admitted checks the exact frozen P56 transitive source/context without old workflow replay.
    return {'p57_source_receipt_sha256': P57_SHA, 'p57_source_sha256': previous.pins(),
            'p56_queue_context': c.predecessor()['queue_context']}


def inputs():
    form = q.forms.candidate
    rows = form.validate_manifest(q.forms.read_json(form.MANIFEST, 524288))
    cases = []
    for row in rows:
        path = form.MANIFEST.parent / row['file']
        raw = r.bounded(path, row['package_sha256'], 4194304)
        cases.append({'case_id': row['case_id'], 'kind': 'native_form',
            'source_file': path.relative_to(ROOT).as_posix(), 'source_sha256': row['package_sha256'],
            'source_bytes': len(raw), 'automation_input_sha256': row['package_sha256'],
            'expected_semantic_state_sha256': row['target_state_sha256']})
    for row in q.field.p.original_inputs()[0]:
        raw = r.bounded(ROOT / row['sdk_expected_file'], row['sdk_expected_package_sha256'], 4194304)
        cases.append({'case_id': row['case_id'], 'kind': 'click_here', 'source_file': row['sdk_expected_file'],
            'source_sha256': row['sdk_expected_package_sha256'], 'source_bytes': len(raw),
            'automation_input_sha256': row['source_package_sha256'],
            'expected_semantic_state_sha256': row['sdk_expected_section_sha256']})
    for i, row in enumerate(cases, 1):
        row.update(capture_index=i, run_directory='implementation/p09/evidence/private/'
            f'p09-58-sdk-baseline-20261003-r01-c{i:02}-attempt01')
    require(tuple(row['case_id'] for row in cases) == q.EXPECTED_IDS, 'p58_complete_input_inventory')
    return cases


def bundle(rows=None):
    return {'schema_version': 'hwpx-agent.sdk-baseline-capture-inputs/v1',
            'cases': inputs() if rows is None else rows, 'human_authored_direct_oracle': False, 'p09_complete': False}


def inspect_bundle(rows=None):
    raw = r.bounded(ROOT / BUNDLE, limit=262144)
    require(raw == canonical(bundle(rows)), 'p58_exact_input_bundle')
    return {'sha256': sha(raw), 'bytes': len(raw), 'cases': 17, 'native_evidence': False}


def prepare_bundle():
    path = ROOT / BUNDLE
    r.unlinked(path.parent)
    require(not path.parent.exists(), 'p58_exclusive_bundle_exists')
    value = bundle()
    path.parent.mkdir()
    with path.open('xb') as stream: stream.write(canonical(value))
    return inspect_bundle(value['cases'])


def command(row, source_pins, bundle_sha):
    require(type(row) is dict and any(canonical(row) == canonical(item) for item in inputs()), 'p58_exact_command_case')
    return [str(q.forms.environment.SHELL), '-NoLogo', '-NoProfile', '-NonInteractive', '-STA', '-File',
        str(ROOT / HARNESS), '-CaseIndex', str(row['capture_index']), '-ExpectedBundleSha256', bundle_sha,
        '-ExpectedLibrarySha256', source_pins[LIBRARY], '-ExpectedHarnessSha256', source_pins[HARNESS], '-PreflightOnly']


def unused(rows, ctx):
    require(canonical(rows) == canonical(inputs()), 'p58_unused_exact_inputs')
    for row in rows:
        r.unlinked(ROOT / row['run_directory'])
        require(not (ROOT / row['run_directory']).exists(), 'p58_native_attempt_already_exists')
    q.unused(ctx)
    require(not (ROOT / DISPATCH).exists(), 'p58_full34_dispatch_already_exists')


def actual_preflights(rows, source_pins, bundle_sha):
    require(canonical(rows) == canonical(inputs()), 'p58_actual_complete_prefix_inventory')
    result = []
    for row in rows:
        child = subprocess.run(command(row, source_pins, bundle_sha), cwd=ROOT, capture_output=True,
            env=q.forms.environment.child_environment(), timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        require(child.returncode == 0 and not child.stderr, 'p58_actual_no_com_prefix_failed')
        value = json.loads(child.stdout, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
        expected = {'state': 'preflight_pass_no_com_no_run_directory', 'case_id': row['case_id'],
            'capture_index': row['capture_index'], 'source_sha256': row['source_sha256'], 'bundle_sha256': bundle_sha,
            'harness_sha256': source_pins[HARNESS], 'owned_library_sha256': source_pins[LIBRARY], 'x86_sta': True,
            'native_session_started': False, 'native_run_directory_created': False,
            'registry_or_system_setting_changed': False, 'p09_complete': False}
        q.field.exact_dict(value, expected, 'p58_actual_prefix_response')
        require(not (ROOT / row['run_directory']).exists(), 'p58_prefix_created_native_directory')
        result.append({'case_id': row['case_id'], 'capture_index': row['capture_index'], 'exit_code': 0,
                       'actual_no_com_prefix_pass': True, 'native_session_started': False})
    return result


def bind_trace(trace, row, code, source_pins, bundle_sha):
    f = q.field
    require(type(trace) is dict and trace.keys() == TRACE_KEYS, 'p58_trace_schema')
    expected = {'schema_version': 'hwpx-agent.p09-58-sdk-baseline-target-trace/v1', 'case_id': row['case_id'],
        'capture_index': row['capture_index'], 'source_sha256': row['source_sha256'], 'source_bytes': row['source_bytes'],
        'bundle_sha256': bundle_sha, 'harness_sha256': source_pins[HARNESS], 'owned_library_sha256': source_pins[LIBRARY],
        'security_module_sha256': '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'}
    require(all(type(trace[k]) is type(v) and trace[k] == v for k, v in expected.items()), 'p58_trace_input_identity')
    f.exact_dict(trace['target'], f.TARGET, 'p58_trace_target')
    require(all(trace[k] is False for k in FALSE_FIELDS) and type(code) is int and code in (0, 2)
        and type(trace['source_identity_preserved']) is bool and f.integer(trace['remaining_hwp_process_count']),
        'p58_trace_false_claims_and_exit')
    start, end = f.utc(trace['started_at_utc']), f.utc(trace['completed_at_utc'])
    require(start <= end, 'p58_trace_time_order')
    sessions = trace['sessions']; require(type(sessions) is list and len(sessions) <= 2, 'p58_trace_session_count')
    seen = set(); births = []; session_ids = set(); clean = True
    for i, session in enumerate(sessions):
        require(type(session) is dict and session.keys() == f.SESSION_KEYS and session['label'] == ('save', 'reopen')[i]
            and type(session['label']) is str and session['version'] in (None, f.TARGET['build'])
            and (session['register_module_return'] is None or type(session['register_module_return']) is bool)
            and type(session['quit_invoked']) is bool and type(session['close_without_dirty_prompt_returned']) is bool
            and f.integer(session['remaining_owned_process_count'], -1)
            and session['cleanup_error'] in (None, 'P58_OWNER_UNVERIFIED_NO_BLANKET_QUIT',
                'P58_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL'), 'p58_trace_owner_schema')
        owner = session['process']
        if owner is None:
            require(session['version'] is None and session['register_module_return'] is None
                and session['quit_invoked'] is False and session['close_without_dirty_prompt_returned'] is False
                and session['remaining_owned_process_count'] == -1 and session['cleanup_error'] is not None,
                'p58_trace_unverified_owner')
            clean = False
        else:
            require(type(owner) is dict and owner.keys() == f.PROCESS_KEYS and f.integer(owner['process_id'], 1)
                and f.integer(owner['session_id']) and owner['executable_sha256'] == f.TARGET['executable_sha256']
                and owner['window_handle_binds_exact_process'] is True and owner['process_id'] not in seen,
                'p58_trace_owned_process')
            birth = f.utc(owner['created_at_utc'])
            require(start - timedelta(seconds=2) <= birth <= end and (not births or birth >= births[-1]),
                    'p58_trace_owner_birth')
            births.append(birth); seen.add(owner['process_id']); session_ids.add(owner['session_id'])
            clean = clean and session['cleanup_error'] is None and session['quit_invoked'] is True and \
                session['close_without_dirty_prompt_returned'] is True and session['remaining_owned_process_count'] == 0
    require(len(session_ids) <= 1, 'p58_trace_owner_session_changed')
    artifacts = trace['artifacts']
    names = tuple(f.OUTPUTS)
    require(type(artifacts) is dict and set(artifacts) == set(names[:len(artifacts)]), 'p58_trace_artifact_prefix')
    for name, artifact in artifacts.items():
        require(type(artifact) is dict and artifact.keys() == {'sha256', 'bytes'} and f.digest(artifact['sha256'])
            and f.integer(artifact['bytes'], 1, f.OUTPUTS[name]), 'p58_trace_artifact_identity')
    completed = trace['state'] == COMPLETE
    if completed:
        require(trace['failed_phase'] is None and trace['error_code'] is None and len(sessions) == 2
            and len(artifacts) == 4 and trace['source_identity_preserved'] is True
            and all(s['version'] == f.TARGET['build'] and type(s['register_module_return']) is bool for s in sessions),
            'p58_trace_completed_reachability')
    else:
        require(trace['state'] == 'effect_unknown' and trace['failed_phase'] in PHASES
            and type(trace['error_code']) is str and re.fullmatch('P58_[A-Z_]+', trace['error_code']),
            'p58_trace_failure_scope')
        amounts, counts = PHASES[trace['failed_phase']]
        require(len(artifacts) in amounts and len(sessions) in counts, 'p58_trace_failed_reachability')
    successful = completed and clean and trace['remaining_hwp_process_count'] == 0
    require(code == (0 if successful else 2), 'p58_trace_real_child_exit')
    return {'case_id': row['case_id'], 'capture_index': row['capture_index'], 'harness_exit': code,
        'lifecycle': 'pass' if successful else 'fail', 'source_identity_preserved': trace['source_identity_preserved'],
        'cleanup_safe_to_continue': trace['remaining_hwp_process_count'] == 0 and trace['source_identity_preserved'],
        'failed_phase': trace['failed_phase'] if not completed else (None if successful else 'owner_cleanup'),
        'human_authored_direct_oracle': False, 'native_package_render_differential_or_product_qualified': False}


def bind_artifacts(trace, row, outputs):
    require(type(outputs) is dict and outputs.keys() <= q.field.OUTPUTS.keys(), 'p58_actual_output_inventory')
    expected = q.field.p.parts(r.bounded(ROOT / row['source_file'], row['source_sha256'], 4194304))
    result = {}
    for name, maximum in q.field.OUTPUTS.items():
        claim = trace['artifacts'].get(name); raw = outputs.get(name)
        require(claim is None or raw is not None, 'p58_actual_claimed_output_missing')
        if raw is None: continue
        require(type(raw) is bytes and len(raw) <= maximum, 'p58_actual_output_bound')
        if claim is not None:
            require(sha(raw) == claim['sha256'] and len(raw) == claim['bytes'] and
                (not name.endswith('.pdf') or raw.startswith(b'%PDF-')), 'p58_actual_output_identity')
        else: require(trace['state'] != COMPLETE, 'p58_completed_unclaimed_output')
        item = {'sha256': sha(raw), 'bytes': len(raw), 'lifecycle_claim_bound': claim is not None,
                'partial_unqualified_preserved': claim is None}
        if claim is not None and name.endswith('.hwpx'):
            try:
                actual = q.field.p.parts(raw)
                changed = sum(expected[n] != actual[n] for n in expected.keys() & actual.keys())
                missing, added = len(expected.keys() - actual.keys()), len(actual.keys() - expected.keys())
                item['whole_sdk_expanded_comparison'] = {'state': 'exact' if not changed + missing + added else 'changed',
                    'changed_parts': changed, 'missing_parts': missing, 'added_parts': added,
                    'all_expanded_part_bytes_checked': True, 'metadata_or_xml_normalized': False}
            except (ValueError, zipfile.BadZipFile):
                item['whole_sdk_expanded_comparison'] = {'state': 'rejected', 'all_expanded_part_bytes_checked': False}
        result[name] = item
    return result


def read_case(row, code, pins, bundle_sha):
    require(type(row) is dict and any(canonical(row) == canonical(item) for item in inputs()), 'p58_exact_actual_case')
    directory = r.unlinked(ROOT / row['run_directory'])
    require(directory.exists() and set(p.name for p in directory.iterdir()) <= q.field.OUTPUTS.keys() | {'target-trace.json'},
            'p58_actual_native_file_inventory')
    raw = r.bounded(directory / 'target-trace.json', limit=262144)
    trace = json.loads(raw, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    result = bind_trace(trace, row, code, pins, bundle_sha)
    outputs = {}
    for name, bound in q.field.OUTPUTS.items():
        path = directory / name
        if not path.exists(): continue
        r.unlinked(path); before = path.stat()
        require(path.is_file() and 0 <= before.st_size <= bound, 'p58_actual_partial_boundary')
        with path.open('rb') as stream: content = stream.read(bound + 1)
        after = path.stat()
        require(before.st_size == after.st_size == len(content) and before.st_mtime_ns == after.st_mtime_ns,
                'p58_actual_output_changed')
        outputs[name] = content
    result['artifacts'] = bind_artifacts(trace, row, outputs)
    files = {row['run_directory'] + '/target-trace.json': sha(raw)}
    files.update({row['run_directory'] + '/' + name: sha(content) for name, content in outputs.items()})
    return result, files
