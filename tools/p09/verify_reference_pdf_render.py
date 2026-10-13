"""Offline SOURCE regression/current raster consumer; no native execution option."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09 import reference_render_consumer as c

r, q = c.render, c.q
SOURCES = ('tools/p09/reference_pdf_render.py', 'tools/p09/reference_render_consumer.py',
           'tools/p09/tests/test_reference_pdf_render.py', 'tools/p09/verify_reference_pdf_render.py',
           'implementation/p09/P09-57_REFERENCE_PDF_RENDER_POLICY.md')
CAPSULE = 'implementation/p09/evidence/p09-57-reference-pdf-render.source.v1.json'


def canonical(value):
    return q.canonical(value)


def pins():
    return {name: r.sha(r.bounded(q.ROOT / name)) for name in SOURCES}


def tests():
    command = [sys.executable, '-m', 'unittest', 'tools.p09.tests.test_reference_pdf_render', '-v']
    result = subprocess.run(command, cwd=q.ROOT, capture_output=True, timeout=60)
    lines = (result.stdout + result.stderr).decode('utf-8', errors='replace').splitlines()
    names = []
    for line in lines:
        match = re.fullmatch(r'(test_[a-z0-9_]+) \(tools\.p09\.tests\.test_reference_pdf_render\.[^)]+\) \.\.\. ok', line)
        if match: names.append(match[1])
    r.require(result.returncode == 0 and len(names) == len(set(names)) == 18 and 'OK' in lines and
        any(re.fullmatch(r'Ran 18 tests in [0-9.]+s', line) for line in lines), 'p57_actual_test_inventory')
    return {'passed': 18, 'exit_code': 0, 'test_names': sorted(names),
            'command_sha256': r.sha(canonical(command)), 'pure_controls_are_native_evidence': False}


def record():
    before = pins(); predecessor = c.predecessor()
    q.forms.hwp_zero()
    engine = r.Renderer()
    controls = tests()
    regression = c.historical(engine)
    current = c.observe_current(engine)
    r.require(current['state'] == 'NOT_RUN' and current['case_count'] == 0, 'p57_source_scope_current_must_not_run')
    r.require(before == pins() and predecessor == c.predecessor() and engine.identity == engine.runtime_identity(),
              'p57_source_or_runtime_changed')
    q.forms.hwp_zero()
    return {'schema_version': 'hwpx-agent.reference-full-pdf-raster-source/v1',
            'state': 'offline_raster_regression_source_not_current_native_qualification',
            'source_sha256': before, 'p56_source_admission_sha256': c.P56_SHA,
            'queue_context_sha256': r.sha(canonical(predecessor['queue_context'])),
            'renderer_runtime': engine.identity, 'actual_tests': controls,
            'actual_original_pdf_regression': regression, 'actual_current_observation': current,
            'claims': {'native_session_started': False, 'access_prompt_triggered': False,
                'historical_originals_rewritten': False, 'new_direct_baseline_or_capture_lane_implemented': False,
                'current_native_render_direct_differential_or_product_qualified': False,
                'original_920_pixel_mismatch_repaired': False, 'green_rows': 0, 'p09_complete': False}}


def admitted():
    raw = r.bounded(q.ROOT / CAPSULE)
    value = json.loads(raw, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    r.require(value['schema_version'] == 'hwpx-agent.reference-full-pdf-raster-source/v1'
        and value['state'] == 'offline_raster_regression_source_not_current_native_qualification'
        and value['source_sha256'] == pins() and value['p56_source_admission_sha256'] == c.P56_SHA,
        'p57_source_admission_changed')
    before = c.predecessor()
    r.require(value['queue_context_sha256'] == r.sha(canonical(before['queue_context'])), 'p57_queue_context_changed')
    r.require(value['claims'] == {'native_session_started': False, 'access_prompt_triggered': False,
        'historical_originals_rewritten': False, 'new_direct_baseline_or_capture_lane_implemented': False,
        'current_native_render_direct_differential_or_product_qualified': False,
        'original_920_pixel_mismatch_repaired': False, 'green_rows': 0, 'p09_complete': False},
        'p57_source_claim_changed')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ('publish', 'verify', 'current'): mode.add_argument('--' + name, action='store_true')
    args = parser.parse_args()
    try:
        if args.current:
            admitted_value = admitted(); before = pins(); engine = r.Renderer()
            r.require(engine.identity == admitted_value['renderer_runtime'], 'p57_renderer_admission_changed')
            current = c.observe_current(engine)
            r.require(before == pins() and admitted_value == admitted() and engine.identity == engine.runtime_identity(),
                      'p57_current_source_or_runtime_changed')
            # Read-only status: NEVER write a native/current evidence capsule from inspection.
            print(json.dumps(current, sort_keys=True)); return 0
        target = q.ROOT / CAPSULE
        r.unlinked(target)
        r.require(args.verify or not target.exists(), 'p57_exclusive_source_capsule_exists')
        value = record()
        if args.verify: r.require(canonical(value) == r.bounded(target), 'p57_independent_fresh_source_changed')
        else:
            with target.open('xb') as stream: stream.write(canonical(value))
        print(json.dumps({'state': 'offline_raster_source_pass_not_current_native', 'actual_unit_tests': 18,
            'dpi_profiles': list(r.DPIS), 'original_mismatch_pixels_96dpi': 920,
            'current_case_count': 0, 'source_capsule_sha256': r.sha(r.bounded(target)),
            'source_capsule_bytes': target.stat().st_size, 'native_executed': False, 'p09_complete': False}, sort_keys=True))
        return 0
    except Exception as error:
        code = str(error)
        print(json.dumps({'state': 'fail', 'error_code': code if re.fullmatch(r'p57_[a-z0-9_]+', code)
            else type(error).__name__, 'native_executed': False, 'p09_complete': False})); return 2


if __name__ == '__main__': raise SystemExit(main())
