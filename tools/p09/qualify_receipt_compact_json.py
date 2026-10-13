"""P219 writer 지원 계약과 고정 sample의 값 보존/크기만 자격 확인한다.

제품 실행/frame/새 writer 연결/CPU 개선/프리즈 해결/Gate 증거가 아니다.
원 sample 파일은 읽기 전용이고 원 fresh IO/guard/final hash를 유지한다.
"""
import argparse
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_native_pressure_runtime as h
import receipt_compact_json as compact

p = h.p
g = h.g
SELF = 'tools/p09/qualify_receipt_compact_json.py'
SCHEMA = 'hwpx-agent.p09-compact-receipt-qualification/v1'
PASS = 'PASS_COMPACT_RECEIPT_CONTRACT12_AND_VALUE_SIZE_ONLY_NOT_ACTUAL_OR_GATE'
ROOT = dict(path=p.DIR + '/p218-case-028-run007.v1.json', bytes=2166291,
    sha256='1bf735447eeb2b7fafbd14baf6df5fb8b62204402df2d05504601b3ab7d5f590')
BODY = dict(path=p.DIR + '/cases/p218-case-028-run007.json', bytes=803125,
    sha256='7deb9983e4ccc7c76435a449627c27ff990d3de11d2e53b00944259180570e7d')


def require(ok, code):
    p.require(ok, 'COMPACT_QUALIFY_' + code)


def contracts():
    sys.path.insert(0, str(p.c.ROOT / 'tools/p09/tests'))
    import test_receipt_compact_json as tests
    with patch('subprocess.Popen', side_effect=AssertionError('NO_COMPACT_CONTRACT_CHILD')), \
            patch('subprocess.run', side_effect=AssertionError('NO_COMPACT_CONTRACT_CHILD')), \
            patch('threading.Thread.start', side_effect=AssertionError('NO_COMPACT_CONTRACT_THREAD')):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun == 12 and not result.skipped, 'CONTRACT12')
    return 12


def sample(doc, pin, checkpoint):
    checkpoint()
    original = copy.deepcopy(doc)
    checkpoint()
    stream = io.StringIO()
    stats = compact.dump(doc, stream, checkpoint=checkpoint, indent=2)
    text = stream.getvalue()
    checkpoint()
    rebuilt = json.loads(text)
    checkpoint()
    require(doc == original and rebuilt == original and list(rebuilt) == list(original), 'ALL_VALUES_AND_ORIGINAL_RETAINED')
    size = len(text.encode('utf-8'))
    require(0 < size < pin['bytes'] and size == stats['characters_written'], 'MEASURED_SMALLER_ASCII_BYTES')
    return dict(source_pin=pin, compact_bytes=size, saved_bytes=pin['bytes'] - size,
        reduction_percent=round(100 * (pin['bytes'] - size) / pin['bytes'], 4),
        entire_JSON_value_identical=True, original_in_memory_value_unchanged=True,
        in_memory_only_no_original_file_rewrite=True, writer_statistics=stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 99, 'CWD_RUN')
    destination = p.c.ROOT / f'{p.DIR}/p219-compact-receipt-light-run{args.run:02}.v1.json'
    require(not destination.exists(), 'FRESH_ONLY')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = candidate = None
    out = dict(schema_version=SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        actual_product_bridge_connected=False, actual_compact_product_receipt_executed=False,
        original_receipts_rewritten=False, measured_CPU_or_PC_freeze_improvement_claimed=False)
    try:
        owner.admit()
        q = p.qualification.Reader(owner, context)
        with context.scope('contract_tests'):
            out['compact_receipt_contract_tests_passed'] = contracts()
        for name in (compact.SELF, compact.TEST, SELF):
            q.pin(name)
        for pin in (ROOT, BODY):
            require(q.pin(pin['path']) == pin, 'LITERAL_UNCHANGED_SAMPLE_PIN')
        root = q.json(ROOT['path'])
        body = q.json(BODY['path'])
        require(root['schema_version'] == h.SCHEMA and root['state'] == h.PASS
            and root.get('error_code') is None and root['resource_stop_reason'] is None
            and root['resource_watcher_cleanup_confirmed'] is True
            and root['case_receipt_pin'] == BODY and root['selected_test_index'] == 28
            and body['schema_version'] == p.SCHEMA and body['state'] == 'PASS_SCOPED_NOT_GATE'
            and body['tests_passed'] == 1 and body['terminal_summary']['filtered_out'] == 248
            and root['product_complete'] is False and body['product_complete'] is False,
            'FIXED_SOURCE_BOUND_SAMPLE_ONLY')
        with context.scope('metadata_read_parse'):
            out['lossless_size_samples'] = [sample(doc, pin, q.checkpoint)
                for doc, pin in ((root, ROOT), (body, BODY))]
        q.finish()
        candidate = dict(state=PASS)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED', error_code=p.b.run.original.closed_error(error))
        candidate = None
    finally:
        if q is not None:
            out.update(IO=q.summary(), bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation'] = g.observation.summary(owner)
        def validate(doc):
            require(doc['IO']['finished'] is True
                and doc['IO']['bound_inputs'] == doc['IO']['final_fresh_hashes'] == 5, 'FINAL_ALL_FRESH')
            require(doc['compact_receipt_contract_tests_passed'] == 12
                and len(doc['lossless_size_samples']) == 2
                and all(row['entire_JSON_value_identical'] is True for row in doc['lossless_size_samples']),
                'ALL_SUPPORT_RESULTS')
        g.complete(out, owner, candidate, validate)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'compact_receipt_contract_tests_passed',
            'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] == PASS else 2


if __name__ == '__main__':
    raise SystemExit(main())
