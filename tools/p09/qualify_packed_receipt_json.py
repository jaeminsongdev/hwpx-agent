"""P221 무손실 carrier 지원 검사. 제품/frame 실행·실제 연결·CPU 개선 증거가 아니다."""
import argparse
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_compact_pressure_runtime as h
import packed_receipt_json as packed

p = h.p
g = h.g
SELF = 'tools/p09/qualify_packed_receipt_json.py'
SCHEMA = 'hwpx-agent.p09-packed-receipt-qualification/v1'
PASS = 'PASS_PACKED_RECEIPT_CONTRACT16_AND_VALUE_SIZE_ONLY_NOT_ACTUAL_OR_GATE'
ROOT = dict(path=p.DIR + '/p220-case-032-run003.v1.json', bytes=1560624,
    sha256='885849bdd5aad4a136f43432a6342670db795324c66761c05559171836ac8e2b')
BODY = dict(path=p.DIR + '/cases/p220-case-032-run003.json', bytes=634572,
    sha256='c8b30d0554703b41f7077ccdb6da069a892f204d46d12d10b4fab8a8b69ee24a')


def require(ok, code):
    p.require(ok, 'PACKED_QUALIFY_' + code)


def contracts():
    sys.path.insert(0, str(p.c.ROOT / 'tools/p09/tests'))
    import test_packed_receipt_json as tests
    with patch('subprocess.Popen', side_effect=AssertionError('NO_PACKED_CONTRACT_CHILD')), \
            patch('subprocess.run', side_effect=AssertionError('NO_PACKED_CONTRACT_CHILD')), \
            patch('threading.Thread.start', side_effect=AssertionError('NO_PACKED_CONTRACT_THREAD')):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun == 16 and not result.skipped, 'CONTRACT16')
    return 16


def sample(doc, pin, checkpoint):
    checkpoint()
    original = copy.deepcopy(doc)
    checkpoint()
    stream = io.StringIO()
    stats = packed.dump(doc, stream, checkpoint=checkpoint, indent=2)
    carrier = json.loads(stream.getvalue())
    rebuilt = packed.unpack(carrier, checkpoint)
    require(doc == original and rebuilt == original and list(rebuilt) == list(original), 'ENTIRE_VALUE_AND_ORIGINAL_RETAINED')
    require(0 < stats['carrier_bytes'] < pin['bytes'], 'MEASURED_SMALLER_THAN_COMPACT_SAMPLE')
    return dict(source_pin=pin, carrier_bytes=stats['carrier_bytes'], raw_json_bytes=stats['raw_json_bytes'],
        gzip_bytes=stats['gzip_bytes'], saved_bytes=pin['bytes'] - stats['carrier_bytes'],
        reduction_percent=round(100 * (pin['bytes'] - stats['carrier_bytes']) / pin['bytes'], 4),
        entire_JSON_value_identical=True, original_value_unchanged=True,
        original_file_rewritten=False, writer_statistics=stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 99, 'CWD_RUN')
    destination = p.c.ROOT / f'{p.DIR}/p221-packed-receipt-light-run{args.run:02}.v1.json'
    require(not destination.exists(), 'FRESH_ONLY')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = candidate = None
    out = dict(schema_version=SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        actual_product_bridge_connected=False, actual_packed_product_receipt_executed=False,
        original_receipts_rewritten=False, measured_CPU_or_PC_freeze_improvement_claimed=False,
        maximum_raw_or_carrier_bytes=packed.MAX_BYTES, maximum_inflate_bytes=packed.INFLATE_BYTES,
        compression_level=packed.LEVEL, official_reference='https://docs.python.org/3/library/zlib.html')
    try:
        owner.admit()
        q = p.qualification.Reader(owner, context)
        with context.scope('contract_tests'):
            out['packed_receipt_contract_tests_passed'] = contracts()
        for name in (packed.SELF, packed.TEST, SELF, packed.compact.SELF, packed.compact.TEST):
            q.pin(name)
        for pin in (ROOT, BODY):
            require(q.pin(pin['path']) == pin, 'LITERAL_UNCHANGED_SAMPLE_PIN')
        root = q.json(ROOT['path'])
        body = q.json(BODY['path'])
        require(root['schema_version'] == h.SCHEMA and root['state'] == h.PASS
            and root.get('error_code') is None and root['resource_stop_reason'] is None
            and root['resource_watcher_cleanup_confirmed'] is True and root['case_receipt_pin'] == BODY
            and root['selected_test_index'] == 32 and body['schema_version'] == p.SCHEMA
            and body['state'] == 'PASS_SCOPED_NOT_GATE' and body['tests_passed'] == 1,
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
                and doc['IO']['bound_inputs'] == doc['IO']['final_fresh_hashes'] == 7, 'FINAL_ALL_FRESH')
            require(doc['packed_receipt_contract_tests_passed'] == 16
                and len(doc['lossless_size_samples']) == 2
                and all(row['entire_JSON_value_identical'] is True for row in doc['lossless_size_samples']), 'ALL_SUPPORT_RESULTS')
        g.complete(out, owner, candidate, validate)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'packed_receipt_contract_tests_passed',
            'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] == PASS else 2


if __name__ == '__main__':
    raise SystemExit(main())
