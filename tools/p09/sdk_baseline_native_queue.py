"""One entire 17 SDK baseline + unchanged P56 17 automation queue; no subsets."""
import json
import subprocess
from pypdf.errors import PdfReadError
from tools.p09 import sdk_baseline_capture as capture

q, r, ROOT = capture.q, capture.r, capture.ROOT
require, sha, canonical = capture.require, capture.sha, capture.canonical


def validate_dispatch(value, rows, predecessor, pins, bundle_sha):
    expected = {'schema_version': 'hwpx-agent.sdk-baseline-and-automation-complete34-dispatch/v1',
        'state': 'all_thirty_four_actual_attempts_terminal_non_green', 'source_sha256': pins,
        'capture_input_bundle_sha256': bundle_sha, 'predecessor_context_sha256': sha(canonical(predecessor)),
        'p56_actual_dispatch_sha256': sha(r.bounded(ROOT / q.DISPATCH)),
        'human_authored_direct_oracle': False, 'permission_click_attestation': 'not_attested',
        'native_render_direct_differential_or_product_qualified': False, 'p09_complete': False}
    require(type(value) is dict and value.keys() == expected.keys() | {'baseline_cases', 'baseline_evidence_sha256'},
            'p58_full34_dispatch_schema')
    for key, item in expected.items():
        require(type(value[key]) is type(item) and canonical(value[key]) == canonical(item), 'p58_full34_dispatch_identity')
    records = value['baseline_cases']
    require(type(records) is list and len(records) == 17 and
        tuple(row.get('case_id') for row in records) == q.EXPECTED_IDS, 'p58_full34_case_inventory')
    require(type(value['baseline_evidence_sha256']) is dict and 17 <= len(value['baseline_evidence_sha256']) <= 85,
            'p58_full34_evidence_inventory')
    require(rows == capture.inputs(), 'p58_full34_current_input_inventory')


def rebind(value, rows, predecessor, pins, bundle_sha):
    validate_dispatch(value, rows, predecessor, pins, bundle_sha)
    cases = []; evidence = {}
    for row, recorded in zip(rows, value['baseline_cases'], strict=True):
        require(type(recorded) is dict and type(recorded.get('harness_exit')) is int, 'p58_full34_actual_child_exit')
        actual, files = capture.read_case(row, recorded['harness_exit'], pins, bundle_sha)
        require(canonical(actual) == canonical(recorded), 'p58_full34_baseline_trace_unbound')
        cases.append(actual); evidence.update(files)
    require(evidence == value['baseline_evidence_sha256'], 'p58_full34_baseline_inventory_unbound')
    p56_raw = r.bounded(ROOT / q.DISPATCH)
    p56_dispatch = json.loads(p56_raw, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    automation = q.rebind_current(p56_dispatch, predecessor['p56_queue_context'], capture.c.prior.pins())
    require(predecessor == capture.predecessor() and rows == capture.inputs() and
        sha(p56_raw) == value['p56_actual_dispatch_sha256'] and p56_raw == r.bounded(ROOT / q.DISPATCH),
        'p58_full34_sources_or_automation_changed')
    return cases, automation[0]['cases'] + automation[1]


def execute(admitted, pins_callback):
    # NEVER reached by offline source tests. The caller must explicitly select --execute-native.
    pins = pins_callback(); predecessor = capture.predecessor(); rows = capture.inputs()
    require(admitted['source_sha256'] == pins and admitted['predecessor'] == predecessor and
        admitted['complete_current_sdk_inputs'] == rows, 'p58_full34_source_admission_changed')
    bundle_sha = capture.inspect_bundle(rows)['sha256']
    capture.unused(rows, predecessor['p56_queue_context'])
    capture.actual_preflights(rows, pins, bundle_sha)
    q.preflight_all(predecessor['p56_queue_context'])  # All34 before the first new activation.
    require(pins == pins_callback() and predecessor == capture.predecessor(), 'p58_sources_changed_before_activation')
    print(json.dumps({'event': 'complete_queue_start', 'case_count': 34, 'permission_clicks': 'user_owned'}), flush=True)
    cases = []; evidence = {}
    for row in rows:
        require(pins == pins_callback() and predecessor == capture.predecessor() and rows == capture.inputs(),
                'p58_sources_changed_before_baseline_case')
        q.forms.hwp_zero()
        command = capture.command(row, pins, bundle_sha)
        require(command[-1] == '-PreflightOnly', 'p58_exact_child_command')
        command[-1] = '-ExecuteNative'
        print(json.dumps({'event': 'sdk_baseline_start', 'case_id': row['case_id'], 'of': 34}), flush=True)
        child = subprocess.Popen(command, cwd=ROOT, env=q.forms.environment.child_environment(),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        count = 0
        for chunk in iter(lambda: child.stdout.read(4096), b''): count += len(chunk)
        code = child.wait()  # No access-prompt timeout/retry/force kill/child restart.
        require(count <= 262144, 'p58_actual_native_child_output_bound')
        actual, files = capture.read_case(row, code, pins, bundle_sha)
        cases.append(actual); evidence.update(files)
        require(actual['cleanup_safe_to_continue'], 'p58_owned_cleanup_or_original_stop_preserve_partial_batch')
        q.forms.hwp_zero()
        require(pins == pins_callback() and predecessor == capture.predecessor(), 'p58_sources_changed_after_baseline_case')
    require(pins == pins_callback(), 'p58_sources_changed_before_automation_lane')
    q.execute_full_queue(capture.c.predecessor(), capture.c.prior.pins())  # EXACT original full15+2 dispatcher.
    require(pins == pins_callback(), 'p58_sources_changed_after_automation_lane')
    value = {'schema_version': 'hwpx-agent.sdk-baseline-and-automation-complete34-dispatch/v1',
        'state': 'all_thirty_four_actual_attempts_terminal_non_green', 'source_sha256': pins,
        'capture_input_bundle_sha256': bundle_sha, 'predecessor_context_sha256': sha(canonical(predecessor)),
        'p56_actual_dispatch_sha256': sha(r.bounded(ROOT / q.DISPATCH)), 'baseline_cases': cases,
        'baseline_evidence_sha256': evidence, 'human_authored_direct_oracle': False,
        'permission_click_attestation': 'not_attested', 'native_render_direct_differential_or_product_qualified': False,
        'p09_complete': False}
    rebind(value, rows, predecessor, pins, bundle_sha)
    path = r.unlinked(ROOT / capture.DISPATCH)
    with path.open('xb') as stream: stream.write(canonical(value))
    print(json.dumps({'state': 'complete_thirty_four_diagnostic_attempts_terminal', 'p09_complete': False}), flush=True)


def current(predecessor, rows, pins, engine, bundle_sha):
    base = {'scope': 'actual_current_sdk_native_baseline_vs_automation_not_human_or_product_oracle',
        'native_session_started': False, 'human_authored_direct_oracle': False,
        'native_semantics_or_product_or_p09_qualified': False, 'p09_complete': False}
    if not (ROOT / capture.DISPATCH).exists():
        return {**base, 'state': 'NOT_RUN', 'case_count': 0, 'cases': [],
            'reason': 'actual_complete34_dispatch_absent_partial_baselines_not_promoted'}
    raw = r.bounded(ROOT / capture.DISPATCH)
    value = json.loads(raw, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    bound = rebind(value, rows, predecessor, pins, bundle_sha)
    results = []
    for plan, direct, auto, automation_plan in zip(rows, *bound,
            predecessor['p56_queue_context']['complete_ordered_queue'], strict=True):
        item = {'case_id': plan['case_id'], 'sdk_target_input_sha256': plan['source_sha256'],
            'automation_input_sha256': plan['automation_input_sha256'], 'human_authored_direct_oracle': False}
        require(plan['case_id'] == auto['case_id'] and plan['automation_input_sha256'] == automation_plan['package_sha256'],
                'p58_render_exact_pair_input_binding')
        if not capture.c.stage_eligible(direct) or not capture.c.stage_eligible(auto):
            results.append({**item, 'state': 'NOT_RUN', 'reason': 'both_actual_successful_lifecycles_required'})
            continue
        paths = [ROOT / directory / name for directory in (plan['run_directory'], automation_plan['run_directory'])
                 for name in ('saved.pdf', 'reopened.pdf')]
        hashes = [record['artifacts'][name]['sha256'] for record in (direct, auto)
                  for name in ('saved.pdf', 'reopened.pdf')]
        snapshots = [r.bounded(path, identity) for path, identity in zip(paths, hashes, strict=True)]
        try:
            comparisons = {name: engine.compare(snapshots[a], snapshots[b]) for name, a, b in (
                ('sdk_baseline_stability', 0, 1), ('automation_stability', 2, 3),
                ('saved_sdk_vs_automation', 0, 2), ('reopened_sdk_vs_automation', 1, 3))}
            results.append({**item, 'state': 'exact_raster_diagnostics_not_semantic_acceptance' if all(
                row['state'] == 'exact_full_document' for row in comparisons.values()) else 'mismatch',
                'comparisons': comparisons})
        except (ValueError, PdfReadError, subprocess.TimeoutExpired):
            results.append({**item, 'state': 'rejected', 'reason': 'bounded_raster_comparison_failed'})
    require(bound == rebind(value, rows, predecessor, pins, bundle_sha) and raw == r.bounded(ROOT / capture.DISPATCH),
            'p58_render_actual_pairs_changed')
    return {**base, 'state': 'complete_seventeen_current_pair_diagnostics_not_semantic_acceptance',
            'case_count': 17, 'cases': results, 'actual_complete34_dispatch_sha256': sha(raw)}
