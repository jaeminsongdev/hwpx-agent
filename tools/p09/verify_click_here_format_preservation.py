"""Fixed, exclusive P54 source progress; never runs the native candidate worker."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import click_here_format_plan as m
from tools.p09 import verify_native_form_saved_package_contract as saved

ROOT, require, sha, canonical = m.ROOT, m.require, m.sha, m.prior.canonical
CAPSULE = 'implementation/p09/evidence/p09-54-click-format.source-progress.v1.json'
P53_SHA = '72ef8e2deedaa5ac483185a30d5aeb2b289cd231f9dd2cb34439d2f786ed5e85'
SOURCES = ('tools/p09/click_here_format_plan.py', m.LIBRARY, m.INSPECTOR,
    'tools/p09/tests/test_click_here_format_preservation.py',
    'tools/p09/verify_click_here_format_preservation.py',
    'implementation/p09/P09-54_CLICK_HERE_FORMAT_PRESERVATION_POLICY.md')


def preservation():
    record = json.loads(saved.checked(ROOT/saved.SOURCE_CAPSULE, P53_SHA),
        object_pairs_hook=m.prior.candidate.prior.io.duplicate_guard)
    old = saved.preservation()
    require(saved.own_pins() == record['source_sha256']
        and old == record['preserved_original_sources_and_native_files'], 'click_format_predecessor_drift')
    require(sha(m.prior.candidate.bounded(ROOT/m.PDF, 16777216)) == m.PDF_SHA, 'click_format_official_pdf_drift')
    require(len(old['all_seventy_five_original_native_sha256']) == 75, 'click_format_native_inventory')
    return {'p53_source_receipt_sha256': P53_SHA, 'p53_four_source_sha256': saved.own_pins(),
        'complete_p48_through_p52_and_seventy_five_native_identity_graph_sha256': sha(canonical(old)),
        'historical_native_files_checked': 75, 'original_pdf_sha256': m.PDF_SHA,
        'predecessor_workflows_reexecuted_here': False}


def pins():
    return {name: sha(m.prior.candidate.bounded(ROOT/name)) for name in SOURCES}


def suite(command, kind):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=60)
    raw = result.stdout+result.stderr
    require(result.returncode == 0, 'click_format_actual_'+kind+'_suite_failed')
    text = raw.decode('utf-8', errors='replace')
    if kind == 'python':
        names = re.findall(r'^(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_click_here_format_preservation\.[^)]+\) \.\.\. ok$',
            '\n'.join(text.splitlines()), re.M)
        require(len(names) == len(set(names)) == 14 and 'Ran 14 tests' in text and '\nOK' in text,
            'click_format_actual_python_inventory')
    else:
        names = re.findall(r'^test ([a-z_]+) \.\.\. ok\r?$', text, re.M)
        require(len(names) == len(set(names)) == 8 and
            '8 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out' in text,
            'click_format_actual_rust_inventory')
    return {'exit_code': 0, 'passed': len(names), 'test_names': sorted(names),
        'actual_command_sha256': sha(canonical(command)), 'native_worker_invoked': False}


def record():
    m.prior.hwp_zero()
    before, old, inventory = pins(), preservation(), m.public_inventory(m.original_plans())
    python = suite([sys.executable, '-m', 'unittest', 'tools.p09.tests.test_click_here_format_preservation', '-v'], 'python')
    rust = suite(['cargo', 'test', '--locked', '--offline', '-p', 'hwpx-package', '--test', 'click_here_hwpx'], 'rust')
    require(before == pins() and old == preservation() and inventory == m.public_inventory(m.original_plans()),
        'click_format_inputs_changed_during_checks')
    m.prior.hwp_zero()
    return {'schema_version': 'hwpx-agent.click-here-format-source-progress/v1',
        'state': 'private_worker_implemented_scoped_source_checks_pass_not_native_admission',
        'source_sha256': before, 'original_complete_two_case_public_inventory': inventory,
        'preservation': old, 'actual_suites': {'python': python, 'rust': rust},
        'claims': {'no_com_server_activation': True, 'native_worker_invoked': False,
            'private_plan_or_native_evidence_written': False, 'native_harness_or_batch_admitted': False,
            'raw_document_values_present': False, 'native_runtime_or_rollback_qualified': False,
            'native_save_reopen_render_differential_qualified': False, 'signed_product_route_enabled': False,
            'whole_ordinary_suites_qualified': False, 'p09_complete': False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--publish', action='store_true')
    mode.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    try:
        target = ROOT/CAPSULE
        m.prior.environment.q.shared.within(target.parent, ROOT/'implementation/p09/evidence')
        if target.exists():
            m.prior.candidate.bounded(target)
        # Refuse overwrite BEFORE running tests. No arbitrary output path is accepted.
        require(args.verify or not target.exists(), 'click_format_exclusive_receipt_exists')
        value = record()
        if args.verify:
            existing = json.loads(m.prior.candidate.bounded(target),
                object_pairs_hook=m.prior.candidate.prior.io.duplicate_guard)
            require(value == existing, 'click_format_whole_source_progress_changed')
        else:
            with target.open('xb') as stream:
                stream.write(canonical(value))
        print(json.dumps({'state': 'source_progress_pass_not_native_admission',
            'python_passed': 14, 'rust_passed': 8, 'native_worker_invoked': False,
            'receipt_sha256': sha(m.prior.candidate.bounded(target)), 'p09_complete': False}, sort_keys=True))
        return 0
    except Exception as error:
        code = str(error) if re.fullmatch('click_format_[a-z_]+', str(error)) else type(error).__name__
        print(json.dumps({'state': 'fail', 'error_code': code, 'native_worker_invoked': False, 'p09_complete': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
