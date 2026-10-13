"""P223: 고정 case043의 CPU peak를 원 보호 Reader로 요약. 재실행/원인 확정 없음."""
import argparse
import collections
import json
import math
import resume_packed_pressure_runtime as r

SELF = 'tools/p09/review_packed_cpu_peak.py'
ROOT_PIN = dict(path=r.p.DIR + '/p222-case-043-run009.v1.json', bytes=585368,
    sha256='36139bea1c5a9c7e128485d9350b3c9eeaa439392498be9b0ffe9c5869c59c06')
PASS = 'PASS_BOUNDED_CPU_PEAK_REVIEW_NOT_CAUSE_OR_GATE'


def summarize(rows):
    r.require(isinstance(rows, list) and 0 < len(rows) <= 1440, 'PEAK_BOUNDED_ROWS')
    peak = hot = max_hot = high95 = high98 = 0
    phases = collections.Counter()
    high_own = high_job = 0.0
    neighbors = []
    hot_indices = []
    for index, row in enumerate(rows):
        value = row['system_cpu_percent']
        r.require(type(value) in (float, int) and math.isfinite(value) and 0 <= value <= 100,
            'PEAK_FINITE_CPU')
        peak = max(peak, value)
        hot = hot + 1 if value >= 98 else 0
        max_hot = max(max_hot, hot)
        if value >= 95:
            high95 += 1
            phases[str(row.get('phase_at_sample', 'not_tagged_original_parent'))] += 1
            hot_indices.append(index)
        if value >= 98:
            high98 += 1
        if value >= 95:
            for key, label in (('parent_cpu_machine_percent', 'own'),
                    ('owned_job_cpu_machine_percent', 'job')):
                number = row.get(key)
                if type(number) in (int, float) and math.isfinite(number):
                    if label == 'own':
                        high_own = max(high_own, number)
                    else:
                        high_job = max(high_job, number)
    # 전체 로그/표본을 복제하지 않고 첫 경고 표본 주변 최대3개의 수치만 제공한다.
    if hot_indices:
        index = hot_indices[0]
        for j in range(max(0, index - 1), min(len(rows), index + 2)):
            neighbors.append({key: rows[j][key] for key in
                ('system_cpu_percent', 'phase_at_sample', 'parent_cpu_machine_percent',
                 'owned_job_cpu_machine_percent', 'audited_logical_read_bytes_delta') if key in rows[j]})
    return dict(sample_count=len(rows), system_peak_percent=peak,
        samples_at_or_above95=high95, samples_at_or_above98=high98,
        maximum_consecutive98_samples=max_hot, warning_phase_counts=dict(phases),
        own_CPU_max_at_warning=high_own, job_CPU_max_at_warning=high_job,
        first_warning_numeric_neighbors=neighbors,
        all_samples_or_raw_logs_output=False, external_PID_or_cause_identified=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True, type=int)
    args = ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve() == r.p.c.ROOT and 1 <= args.run <= 99, 'PEAK_CWD_RUN')
    path = r.p.c.ROOT / f'{r.p.DIR}/p223-cpu-peak-review-run{args.run:02}.v1.json'
    r.require(not path.exists(), 'PEAK_FRESH_ONLY')
    context = r.g.observation.Context()
    owner = r.g.observation.Resources(context)
    q = candidate = None
    out = dict(schema_version='hwpx-agent.p09-packed-cpu-peak-review/v1',
        state='FAILED_NOT_ACCEPTED', **r.p.r.flags(),
        product_body_reexecuted=False, original_files_rewritten=False,
        CPU_cause_or_PC_freeze_resolution_established=False)
    try:
        owner.admit()
        q = r.Reader(owner, context)
        q.pin(SELF)
        r.require(q.pin(ROOT_PIN['path']) == ROOT_PIN, 'PEAK_LITERAL_COMPLETED_ROOT')
        root = q.json(ROOT_PIN['path'])
        r.closed_attempt(root)
        r.require(root['state'] == r.PASS and root['selected_test_index'] == 43,
            'PEAK_EXACT_COMPLETED_CASE43')
        pin = root['case_receipt_pin']
        r.require(pin['path'] == r.p.DIR + '/cases/p222-case-043-run009.json', 'PEAK_EXACT_BODY_PATH')
        body = q.json(pin['path'])
        r.require(q.reader.snapshots[pin['path']] == pin and body['state'] == 'PASS_SCOPED_NOT_GATE'
            and body['tests_passed'] == 1 and body['stop_reason'] is None, 'PEAK_UNCHANGED_COMPLETED_BODY')
        out['metadata_peak_review'] = summarize(root['metadata_observation']['samples'])
        out['original_parent_peak_review'] = summarize(body['samples'])
        out['native_pressure'] = root['closing_component']['source_frame']['handles']['native_open_backpressure']
        out['owned_read_pressure'] = [{key: value for key, value in row.items()
            if 'pressure' in key} for row in body['owned_source_reader_passes']]
        out['phase_counter_interpretation'] = 'phase_at_sample is a caller scope tag, not external CPU cause'
        q.finish()
        candidate = dict(state=PASS)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out['error_code'] = r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:
            out['IO'] = q.summary()
            out['bound_input_pins'] = list(q.reader.snapshots.values())
        r.g.complete(out, owner, candidate, lambda doc: r.require(doc['IO']['finished'] is True
            and doc['IO']['bound_inputs'] == doc['IO']['final_fresh_hashes'] == 3, 'PEAK_ALL_FRESH'))
        with path.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({key: out.get(key) for key in ('state', 'error_code', 'resource_stop_reason',
            'resource_watcher_cleanup_confirmed', 'metadata_peak_review', 'original_parent_peak_review',
            'owned_read_pressure')}))
    return 0 if out['state'] == PASS else 2


if __name__ == '__main__':
    raise SystemExit(main())
