"""Read actual P56 complete17 results, never fabricate a current direct baseline."""
import json
import subprocess
from pypdf.errors import PdfReadError
from tools.p09 import reference_pdf_render as render
from tools.p09 import verify_reference_native_queue as prior

q = prior.q
P56_SHA = '3869c502ed4b7e1ba08f85e181f9dada3622a72a45e63a222fe8d6a267dd0de7'
HISTORICAL = (
    ('implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-22-20261002-c01-attempt01/saved.pdf',
     '8e8e567f0b7a47ecd91c3e3763791c1bbdd3c05f9b3f4282184415833f0f5afd'),
    ('implementation/p09/evidence/private/p09-22-click-here-discovery-20261002-01/filled.pdf',
     '97a271a0c93fdae2b3753065b22fb8caabec147f09e8964d5bcfc971604eb067'),
    ('implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-22-20261002-c01-attempt01/reopened.pdf',
     '0528f2a8508dc18db0dffafa45506a5057195037275b0bda30331af12cf5ff81'),
)


def predecessor():
    raw = render.bounded(q.ROOT / q.ADMISSION, P56_SHA)
    value = prior.admitted()  # Exact frozen source/context admission; no preflight/COM/replay.
    render.require(raw == render.bounded(q.ROOT / q.ADMISSION, P56_SHA), 'p57_predecessor_changed')
    return value


def historical(engine):
    inputs = [render.bounded(q.ROOT / path, identity) for path, identity in HISTORICAL]
    differential = engine.compare(inputs[0], inputs[1])
    first, second = differential['pages'][0]['profiles']
    render.require(differential['state'] == 'mismatch' and
        (first['changed_pixels'], first['rgb_delta_sum'], first['difference_bbox']) ==
        (920, 215567, [113, 132, 273, 145]), 'p57_original_mismatch_not_reproduced')
    render.require((second['changed_pixels'], second['rgb_delta_sum'], second['difference_bbox']) ==
        (2822, 930553, [227, 266, 546, 291]), 'p57_high_dpi_mismatch_changed')
    stability = engine.compare(inputs[0], inputs[2])
    render.require(stability['state'] == 'exact_full_document', 'p57_historical_stability_changed')
    for (path, identity), raw in zip(HISTORICAL, inputs, strict=True):
        render.require(raw == render.bounded(q.ROOT / path, identity), 'p57_historical_source_changed')
    return {'scope': 'historical_regression_not_current_native_or_baseline',
            'source_pdf_sha256': [identity for _, identity in HISTORICAL],
            'original_direct_automation_mismatch': differential, 'old_saved_reopened_stability': stability,
            'original_920_pixel_mismatch_repaired': False, 'current_native_qualified': False}


def direct_baselines():
    # There is NO current exact-candidate direct capture lane/admission. Old PDFs are never substitutes.
    return [{'case_id': case, 'state': 'NOT_RUN', 'reason': 'current_exact_candidate_direct_capture_absent',
             'historical_baseline_reused': False} for case in q.EXPECTED_IDS]


def stage_eligible(record):
    if record['harness_exit'] != 0 or record['lifecycle'] != 'pass':
        return False
    return all(record.get('artifacts', {}).get(name, {}).get('lifecycle_claim_bound') is True
               for name in ('saved.pdf', 'reopened.pdf'))


def observe_current(engine):
    before = predecessor()
    base = {'scope': 'actual_complete17_saved_reopened_raster_not_direct_differential',
            'native_session_started': False, 'direct_baselines': direct_baselines(),
            'direct_automation_differential_qualified': False, 'p09_complete': False}
    if not (q.ROOT / q.DISPATCH).exists():
        render.require(before == predecessor(), 'p57_current_predecessor_changed')
        return {**base, 'state': 'NOT_RUN', 'case_count': 0, 'cases': [],
                'reason': 'actual_complete17_dispatch_absent'}
    raw = render.bounded(q.ROOT / q.DISPATCH)
    dispatch = json.loads(raw, object_pairs_hook=q.forms.candidate.prior.io.duplicate_guard)
    actual = q.rebind_current(dispatch, before['queue_context'], prior.pins())
    records = actual[0]['cases'] + actual[1]
    render.require(tuple(row['case_id'] for row in records) == q.EXPECTED_IDS, 'p57_complete_case_inventory')
    rows = []
    for plan, record in zip(before['queue_context']['complete_ordered_queue'], records, strict=True):
        if not stage_eligible(record):
            rows.append({'case_id': record['case_id'], 'state': 'NOT_RUN',
                         'reason': 'actual_successful_lifecycle_and_two_claimed_pdfs_required'})
            continue
        snapshots = [render.bounded(q.ROOT / plan['run_directory'] / name,
                       record['artifacts'][name]['sha256']) for name in ('saved.pdf', 'reopened.pdf')]
        try:
            comparison = engine.compare(*snapshots)
            rows.append({'case_id': record['case_id'], 'state': comparison['state'], 'comparison': comparison})
        except (ValueError, PdfReadError, subprocess.TimeoutExpired) as error:
            # Failure is retained per case, never silently excluded from full17 coverage.
            code = str(error)
            rows.append({'case_id': record['case_id'], 'state': 'rejected',
                         'reason': code if code.startswith('p57_') and code.isascii() and
                         all(c.islower() or c.isdigit() or c == '_' for c in code) else 'p57_pdf_parse_rejected'})
    render.require(actual == q.rebind_current(dispatch, before['queue_context'], prior.pins()) and
                   raw == render.bounded(q.ROOT / q.DISPATCH) and before == predecessor(),
                   'p57_actual_native_artifacts_changed')
    return {**base, 'state': 'all_seventeen_raster_diagnostics_not_direct_acceptance', 'case_count': 17,
            'cases': rows, 'actual_dispatch_sha256': render.sha(raw),
            'exact_saved_reopened_rasters': sum(r['state'] == 'exact_full_document' for r in rows)}
