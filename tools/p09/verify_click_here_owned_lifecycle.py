"""P55 scoped source progress with real no-COM preflight; no native dispatch."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import click_here_format_lifecycle as p

ROOT, sha, canonical, require = p.ROOT, p.sha, p.canonical, p.require
CAPSULE = 'implementation/p09/evidence/p09-55-click-owned-lifecycle.source-progress.v1.json'
SOURCES = (p.HARNESS, p.LIBRARY, p.INSPECTOR, 'tools/p09/click_here_format_lifecycle.py',
    'tools/p09/tests/test_click_here_format_lifecycle.py', 'tools/p09/verify_click_here_owned_lifecycle.py',
    'implementation/p09/P09-55_CLICK_HERE_OWNED_LIFECYCLE_POLICY.md')


def pins():
    return {n: sha(p.m.prior.candidate.bounded(ROOT/n)) for n in SOURCES}


def no_native_runs():
    rows, _ = p.original_inputs()
    require(all(not (ROOT/r['run_directory']).exists() for r in rows), 'p55_native_run_directory_exists')
    p.m.prior.hwp_zero()


def actual_tests():
    command = [sys.executable,'-m','unittest','tools.p09.tests.test_click_here_format_lifecycle','-v']
    result = subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60)
    require(result.returncode == 0,'p55_actual_suite_failed')
    lines = (result.stdout+result.stderr).decode('utf-8',errors='replace').splitlines()
    names = []
    for line in lines:
        match = re.fullmatch(r'(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_click_here_format_lifecycle\.[^)]+\) \.\.\. ok',line)
        if match: names.append(match[1])
    require(len(names) == len(set(names)) == 11 and 'OK' in lines and
        any(re.fullmatch(r'Ran 11 tests in [0-9.]+s',line) for line in lines),'p55_actual_suite_inventory')
    return {'exit_code':0,'passed':11,'test_names':sorted(names),'command_sha256':sha(canonical(command)),
        'actual_x86_sta_no_com_preflight_cases':2,'actual_wrong_hash_child_rejections':3,
        'native_execute_switch_passed':False,'pure_style_fixture_is_native_evidence':False}


def record():
    no_native_runs()
    before, old, bundle = pins(), p.preserved(), p.inspect_bundle()
    rows, _ = p.original_inputs()
    positive = [p.compare_saved_package(r['case_id'],p.m.prior.candidate.bounded(ROOT/r['sdk_expected_file'])) for r in rows]
    require(all(r['whole_expanded_bytes_exact'] for r in positive),'p55_sdk_source_comparison')
    tests = actual_tests()
    no_native_runs()
    require(before == pins() and old == p.preserved() and bundle == p.inspect_bundle(), 'p55_sources_changed_during_verification')
    return {'schema_version':'hwpx-agent.click-here-owned-lifecycle-source-progress/v1',
        'state':'implemented_scoped_source_progress_not_native_admission','source_sha256':before,
        'complete_two_case_original_inputs':rows,'private_source_plan_bundle_inventory':bundle,
        'preservation':old,'actual_tests':tests,'actual_existing_sdk_package_comparisons':positive,
        'claims':{'native_run_directories_created':False,'no_com_server_activation':True,
            'native_owned_session_or_cleanup_or_rollback_qualified':False,'native_save_reopen_or_render_differential_qualified':False,
            'current_native_result':'NOT_RUN','batch_dispatch_or_native_admission_implemented':False,
            'raw_document_values_present':False,'whole_ordinary_suites_qualified':False,'p09_complete':False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare',action='store_true');modes.add_argument('--publish',action='store_true');modes.add_argument('--verify',action='store_true')
    args = parser.parse_args()
    try:
        if args.prepare:
            no_native_runs();p.preserved();bundle=p.prepare_bundle()
            print(json.dumps({'state':'source_plan_bundle_prepared_not_native_admission','case_count':bundle['case_count'],
                'files':len(bundle['files']),'native_runtime_qualified':False}));return 0
        target = ROOT/CAPSULE
        p.m.prior.environment.q.shared.within(target.parent,ROOT/'implementation/p09/evidence')
        require(args.verify or not target.exists(),'p55_exclusive_receipt_exists')
        if target.exists():p.m.prior.candidate.bounded(target)
        value = record()
        if args.verify:
            existing=json.loads(p.m.prior.candidate.bounded(target),object_pairs_hook=p.m.prior.candidate.prior.io.duplicate_guard)
            require(value == existing,'p55_whole_source_progress_changed')
        else:
            with target.open('xb') as stream:stream.write(canonical(value))
        print(json.dumps({'state':'scoped_source_progress_pass_not_native_admission','passed':11,
            'actual_no_com_preflight_cases':2,'native_executed':False,'receipt_sha256':sha(p.m.prior.candidate.bounded(target)),
            'p09_complete':False},sort_keys=True));return 0
    except Exception as error:
        message=str(error);code=message if re.fullmatch('p55_[a-z_]+',message) else type(error).__name__
        print(json.dumps({'state':'fail','error_code':code,'native_executed':False,'p09_complete':False}));return 2


if __name__ == '__main__':
    raise SystemExit(main())
