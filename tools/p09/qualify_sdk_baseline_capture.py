"""Full current17 SDK capture source admission / one full34 native queue, explicit modes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import sdk_baseline_native_queue as queue

c, r, q = queue.capture, queue.r, queue.q
ROOT, sha, canonical, require = c.ROOT, c.sha, c.canonical, c.require
FAILURE = 'implementation/p09/evidence/p09-58-sdk-baseline-capture.initial-prefix-failure.v1.json'
SOURCES = (c.HARNESS, c.LIBRARY, 'tools/p09/sdk_baseline_capture.py', 'tools/p09/sdk_baseline_native_queue.py',
    'tools/p09/tests/test_sdk_baseline_capture.py', 'tools/p09/qualify_sdk_baseline_capture.py',
    'implementation/p09/P09-58_SDK_BASELINE_CAPTURE_POLICY.md', FAILURE)
CLAIMS = {'new_seventeen_sdk_baseline_collection_source_implemented': True,
    'entire_thirty_four_native_queue_connected': True, 'human_authored_direct_oracle': False,
    'native_session_started': False, 'native_dispatch_invoked': False,
    'actual_current_direct_baseline_or_differential_qualified': False, 'signed_product_qualified': False,
    'permission_clicks_automated': False, 'raw_document_values_present': False,
    'whole_ordinary_suites_qualified': False, 'green_rows': 0, 'p09_complete': False}


def pins(): return {name: sha(r.bounded(ROOT / name)) for name in SOURCES}


def actual_tests():
    command = [sys.executable, '-m', 'unittest', 'tools.p09.tests.test_sdk_baseline_capture', '-v']
    child = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60)
    lines = (child.stdout + child.stderr).decode('utf-8', errors='replace').splitlines()
    names = []
    for line in lines:
        match = re.fullmatch(r'(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_sdk_baseline_capture\.[^)]+\) \.\.\. ok', line)
        if match: names.append(match[1])
    require(child.returncode == 0 and len(names) == len(set(names)) == 20 and 'OK' in lines and
        any(re.fullmatch(r'Ran 20 tests in [0-9.]+s', line) for line in lines), 'p58_actual_unit_inventory')
    return {'passed': 20, 'exit_code': 0, 'test_names': sorted(names), 'command_sha256': sha(canonical(command)),
            'synthetic_traces_published_as_native': False}


def actual_ast():
    # Parse AST only, including native code. Never dot-source/invoke the native body.
    command = r"""
$ErrorActionPreference='Stop';$paths=@('implementation/p09/tools/run-hancom-2020-sdk-baseline-capture.ps1','implementation/p09/tools/sdk-baseline-owned-session.ps1');
foreach ($path in $paths) {$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PWD $path),[ref]$tokens,[ref]$errors);if($errors.Count){exit 2};if($path.EndsWith('sdk-baseline-owned-session.ps1')){foreach($statement in $ast.EndBlock.Statements){if($statement -is [Management.Automation.Language.FunctionDefinitionAst]){continue};if($statement -is [Management.Automation.Language.PipelineAst] -and $statement.Extent.Text -ceq 'Set-StrictMode -Version Latest'){continue};exit 2}}};[Console]::Write('P58_AST_FUNCTIONS_ONLY_PASS')
"""
    result = subprocess.run([str(q.forms.environment.SHELL), '-NoProfile', '-Command', command], cwd=ROOT,
        capture_output=True, timeout=30, env=q.forms.environment.child_environment(), creationflags=subprocess.CREATE_NO_WINDOW)
    require(result.returncode == 0 and result.stdout == b'P58_AST_FUNCTIONS_ONLY_PASS' and not result.stderr,
            'p58_actual_ast_no_top_level_activation')
    return {'files': 2, 'exit_code': 0, 'library_top_level_is_functions_and_strict_mode_only': True,
            'native_body_invoked': False}


def wrong_hash_controls(rows, source_pins, bundle_sha):
    original = c.command(rows[0], source_pins, bundle_sha)
    controls = []
    for argument in ('-ExpectedBundleSha256', '-ExpectedLibrarySha256', '-ExpectedHarnessSha256'):
        command = list(original); command[command.index(argument) + 1] = '0' * 64
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30,
            env=q.forms.environment.child_environment(), creationflags=subprocess.CREATE_NO_WINDOW)
        require(result.returncode == 1 and not result.stdout and b'P58_FILE_IDENTITY' in result.stderr
            and len(result.stderr) <= 262144, 'p58_actual_hash_substitution_not_rejected')
        controls.append({'argument': argument, 'exit_code': 1, 'rejected_before_native': True})
    return controls


def record():
    before = pins(); predecessor = c.predecessor(); rows = c.inputs(); bundle = c.inspect_bundle(rows)
    c.unused(rows, predecessor['p56_queue_context'])
    tests = actual_tests(); ast = actual_ast()
    prefixes = c.actual_preflights(rows, before, bundle['sha256'])
    wrong = wrong_hash_controls(rows, before, bundle['sha256'])
    engine = r.Renderer()
    current = queue.current(predecessor, rows, before, engine, bundle['sha256'])
    require(current['state'] == 'NOT_RUN' and current['case_count'] == 0, 'p58_source_current_scope')
    require(before == pins() and predecessor == c.predecessor() and rows == c.inputs()
        and bundle == c.inspect_bundle(rows) and engine.identity == engine.runtime_identity(), 'p58_source_context_changed')
    c.unused(rows, predecessor['p56_queue_context'])
    return {'schema_version': 'hwpx-agent.sdk-baseline-and-complete34-source/v1',
        'state': 'complete_current_sdk_baseline_source_not_native_qualification', 'source_sha256': before,
        'predecessor': predecessor, 'complete_current_sdk_inputs': rows, 'private_source_capture_bundle': bundle,
        'actual_unit_tests': tests, 'actual_ast': ast, 'actual_new_seventeen_no_com_prefixes': prefixes,
        'actual_three_hash_rejections': wrong, 'actual_current': current, 'claims': CLAIMS}


def admitted():
    value = json.loads(r.bounded(ROOT / c.CAPSULE), object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    expected = {'schema_version': 'hwpx-agent.sdk-baseline-and-complete34-source/v1',
        'state': 'complete_current_sdk_baseline_source_not_native_qualification', 'source_sha256': pins(),
        'predecessor': c.predecessor(), 'complete_current_sdk_inputs': c.inputs(),
        'private_source_capture_bundle': c.inspect_bundle(), 'claims': CLAIMS}
    require(type(value) is dict and value.keys() == expected.keys() | {'actual_unit_tests', 'actual_ast',
        'actual_new_seventeen_no_com_prefixes', 'actual_three_hash_rejections', 'actual_current'}, 'p58_admission_schema')
    for key, item in expected.items():
        require(type(value[key]) is type(item) and canonical(value[key]) == canonical(item), 'p58_admission_identity')
    prefixes = [{'case_id': row['case_id'], 'capture_index': row['capture_index'], 'exit_code': 0,
        'actual_no_com_prefix_pass': True, 'native_session_started': False} for row in expected['complete_current_sdk_inputs']]
    require(canonical(value['actual_new_seventeen_no_com_prefixes']) == canonical(prefixes)
        and value['actual_unit_tests']['passed'] == 20 and value['actual_unit_tests']['exit_code'] == 0
        and value['actual_unit_tests']['synthetic_traces_published_as_native'] is False
        and value['actual_ast'] == {'files': 2, 'exit_code': 0,
            'library_top_level_is_functions_and_strict_mode_only': True, 'native_body_invoked': False}
        and value['actual_current']['state'] == 'NOT_RUN' and value['actual_current']['case_count'] == 0,
        'p58_admission_actual_offline_scope')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ('publish', 'verify', 'current', 'execute-native'): mode.add_argument('--' + name, action='store_true')
    args = parser.parse_args()
    try:
        if args.execute_native:
            queue.execute(admitted(), pins); return 0
        if args.current:
            value = admitted(); before = pins(); engine = r.Renderer()
            result = queue.current(value['predecessor'], value['complete_current_sdk_inputs'], before, engine,
                                   value['private_source_capture_bundle']['sha256'])
            require(before == pins() and value == admitted() and engine.identity == engine.runtime_identity(),
                    'p58_current_context_changed')
            print(json.dumps(result, sort_keys=True)); return 0  # No native/current evidence writes.
        target = r.unlinked(ROOT / c.CAPSULE)
        require(args.verify or not target.exists(), 'p58_exclusive_source_receipt_exists')
        value = record()
        if args.verify: require(canonical(value) == r.bounded(target), 'p58_independent_fresh_source_changed')
        else:
            with target.open('xb') as stream: stream.write(canonical(value))
        print(json.dumps({'state': 'sdk_baseline_source_pass_not_native', 'new_no_com_prefixes': 17,
            'unit_tests': 20, 'wrong_hash_rejections': 3, 'complete_queued_native_attempts': 34,
            'native_executed': False, 'source_receipt_bytes': target.stat().st_size,
            'source_receipt_sha256': sha(r.bounded(target)), 'p09_complete': False}, sort_keys=True)); return 0
    except Exception as error:
        message = str(error); code = message if re.fullmatch('p58_[a-z0-9_]+', message) else type(error).__name__
        print(json.dumps({'state': 'fail', 'error_code': code, 'partial_evidence_preserved': True,
                         'native_executed': False, 'p09_complete': False})); return 2


if __name__ == '__main__': raise SystemExit(main())
