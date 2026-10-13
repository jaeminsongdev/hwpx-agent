"""P222: 원 단일 owner/Native pressure/전후 byte 검사를 유지하고 새 receipt만 무손실 압축 저장.

수용된 P220 34개·P221 지원 증거/소스는 수정하지 않는다. 원 P208 parent의
최종 writer에만 연결한다. 실패/CPU STOP/부분 JSON은 자동 재시도하지 않는다.
"""
import argparse
import hashlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_compact_pressure_runtime as h
import qualify_packed_receipt_json as qualified

p = h.p
g = h.g
packed = qualified.packed
compact = packed.compact
SELF = 'tools/p09/resume_packed_pressure_runtime.py'
TEST = 'tools/p09/tests/test_packed_pressure_runtime.py'
NEW = (packed.SELF, packed.TEST, qualified.SELF, SELF, TEST)
EXTRAS = (*h.EXTRAS, *NEW)
SCHEMA = 'hwpx-agent.p09-packed-pressure-runtime-pair/v1'
PASS = 'PASS_EXACT_R07_PACKED_PRESSURE_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT = 'PASS_PACKED_PRESSURE_SELECTION_NOT_ACTUAL_OR_GATE'
FILE = re.compile(r'p222-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
SEALED34 = dict(path=p.DIR + '/p220-case-034-run005.v1.json', bytes=1588449,
    sha256='49c1280ee39dac81d4140dba7ba0890b24375a87c659111bf561f8888889f6d8')
SUPPORT = dict(path=p.DIR + '/p221-packed-receipt-light-run01.v1.json', bytes=18137,
    sha256='c01529a6ade583042ef46fb5aef544f32a96cb7243a013bc73e23c1a3a3a554c')


def require(ok, code):
    p.require(ok, 'PACKED_RUNTIME_' + code)


class Reader(p.qualification.Reader):
    def json(self, path):
        carrier = super().json(path)
        name = self.name(path)
        if name.startswith(p.DIR + '/p222-') or name.startswith(p.DIR + '/cases/p222-'):
            # 원 실제 fresh 읽기는 superclass에 유지하고 해제 검사는 추가한다.
            h.canonical(carrier, self.reader.snapshots[name], self.checkpoint)
            return packed.unpack(carrier, self.checkpoint)
        return carrier


def policy():
    return dict(writer_source=packed.SELF, codec='gzip-base64-canonical-ascii-json',
        compression_level=packed.LEVEL, maximum_raw_or_carrier_bytes=packed.MAX_BYTES,
        maximum_inflate_bytes=packed.INFLATE_BYTES, ensure_ascii=True, separators=[',', ':'], indent=None,
        original_parent_keywords=dict(ensure_ascii=False, indent=2), semantic_fields_removed=0,
        parent_original_frame_guard_connected=True, root_written_after_original_resource_cleanup=True,
        root_terminal_lifecycle_checkpoint_only=True, new_sampler_started=False,
        original_receipts_rewritten=False, CPU_or_PC_freeze_improvement_claimed=False)


def stats_contract(row, pin):
    h.stats_contract(row['carrier_write_statistics'], pin)
    require(row['carrier_bytes'] == pin['bytes'] and 0 < row['raw_json_bytes'] <= packed.MAX_BYTES
        and 0 < row['gzip_bytes'] <= packed.MAX_BYTES
        and row['raw_encode_statistics']['characters_written'] == row['raw_json_bytes']
        and row['semantic_fields_removed'] == 0 and row['original_files_rewritten'] is False
        and row['new_sampler_or_native_query_started'] is False
        and row['CPU_or_PC_freeze_improvement_claimed'] is False, 'COMPLETE_LOSSLESS_CARRIER_WRITE')


def parent_writer(frame, completed):
    def write(doc, stream, **keywords):
        require(keywords == dict(ensure_ascii=False, indent=2), 'EXACT_ORIGINAL_PARENT_DUMP_OPTIONS')
        # ASCII escape representation alone changes; JSON values are unchanged.
        # The original parent already validated doc before invoking this writer.
        stats = packed.dump(doc, stream, checkpoint=frame.check, indent=2)
        completed.append(stats)
        return None
    return write


def terminal_checkpoint(doc, owner):
    # 원 overall writer도 원 resource cleanup 뒤에 실행된다. 종료된 owner로
    # 새 admission/표본을 만들지 않는다. 실패 receipt도 항상 보존해야 한다.
    require(owner.done.is_set() and doc.get('state') in (PASS, LIGHT, 'FAILED_NOT_ACCEPTED'),
        'TERMINAL_LIFECYCLE_ONLY_NO_RESOURCE_RESTART')


def anchor(q):
    legacy, base, names, expected, exe, old_required, old_extras = h.anchor(q)
    binding = p.v.identity(names, expected, exe)
    base = h.progress(q, legacy, base, names, old_required, binding, old_extras)
    require(base['runtime_source_qualified_individual_cases'] == 34 and base['next_runtime_index'] == 35
        and q.pin(SEALED34['path']) == SEALED34, 'SEALED34_NOT_REEXECUTED')
    require(q.pin(SUPPORT['path']) == SUPPORT, 'LITERAL_COMPACT_SUPPORT_PIN')
    support = q.json(SUPPORT['path'])
    require(support['schema_version'] == qualified.SCHEMA and support['state'] == qualified.PASS
        and support.get('error_code') is None and support['resource_stop_reason'] is None
        and support['resource_watcher_cleanup_confirmed'] is True
        and support['packed_receipt_contract_tests_passed'] == 16
        and support['IO']['finished'] is True
        and support['IO']['bound_inputs'] == support['IO']['final_fresh_hashes'] == 7
        and support['actual_product_bridge_connected'] is False
        and support['actual_packed_product_receipt_executed'] is False
        and support['original_receipts_rewritten'] is False
        and len(support['bound_input_pins']) == 7
        and all(q.pin(pin['path']) == pin for pin in support['bound_input_pins']),
        'UNCHANGED_SUPPORT_ONLY_NOT_ACTUAL')
    added = {name: q.pin(name) for name in NEW}
    required = {**old_required, **added}
    extras = {**old_extras, **added}
    require(len(required) == 1503 and len(extras) == 36 and set(old_required) < set(required),
        'ALL_ORIGINAL1498_PLUS_NEW5')
    return legacy, base, names, expected, exe, required, extras


def native_pair(component, body, pin, required, binding, extras):
    p.validate_closing(component, body, pin, required, binding, extras)
    frame = component['source_frame']
    own = frame['handles']
    dup = own['borrowed_byte_streams']
    count = len(required)
    require(count == 1503 and own['input_lock_handles_opened'] == own['input_lock_handles_closed'] == count + 306
        and own['maximum_lock_seconds'] == 600 and own['ancestor_walk_steps'] == 305
        and own['native_open_pacing']['maximum_opens_per_second'] == 32
        and own['native_open_pacing']['open_reservations'] == 3 * count + 306
        and dup['duplicate_handles_opened'] == dup['duplicate_handles_closed'] == dup['shared_offset_resets'] == 2 * count
        and dup['duplicate_handles_remaining'] == dup['duplicate_close_failed_attempts'] == dup['byte_stream_pathname_reopens'] == 0
        and frame['held_identity_after_owned_cleanup'] == dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0, regular_file_count=count, directory_count=306),
        'ALL_NATIVE_ORIGINAL_STREAMS_AND_IDENTITIES')
    h.h.pressure_contract(own['native_open_backpressure'])


def record(doc, body, pin, required, binding, extras, names, legacy, base):
    index, name = g.old.select(base, names)
    require(doc['schema_version'] == SCHEMA and doc['state'] == PASS and doc.get('error_code') is None
        and doc['packed_pressure_runtime_contract_tests_passed'] == 88
        and doc['selected_test_index'] == index and doc['selected_test_name'] == name
        and doc['binding'] == binding and doc['prior_runtime_plan'] == base and doc['case_receipt_pin'] == pin
        and all(doc[k] is True for k in ('native_pressure_bridge_connected', 'packed_parent_writer_connected',
            'packed_root_writer_selected', 'frame_acquisition_requested', 'frame_acquisition_complete',
            'product_worker_invocation_requested', 'actual_product_child_executed', 'resource_watcher_cleanup_confirmed'))
        and doc['receipt_serialization_policy'] == policy() and doc['resource_stop_reason'] is None
        and doc['P09_gate'] == doc['A12_gate'] == doc['A13_gate'] == 'OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified', 'historical67_current_fresh_qualified',
            'full249_current_qualified', 'signed16_current_qualified', 'product_complete', 'PC_freeze_resolved'))
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs'] == doc['preparation_IO']['final_fresh_hashes'],
        'COMPLETE_OVERALL_WITH_ORIGINAL_GATES')
    native_pair(doc['closing_component'], body, pin, required, binding, extras)
    stats_contract(doc['packed_parent_write_statistics'], pin)
    require(body['task'] == f'p204-r07-case-{index:03}-tests'
        and doc['runtime_plan'] == g.advance(legacy, base, names, index)
        and doc['accepted_exact_product_body_count'] == 1, 'EXACT_BODY_AND_NEXT_QUEUE')
    return doc['runtime_plan']


def closed_attempt(doc):
    require(doc.get('state') in (PASS, LIGHT) and doc.get('error_code') is None
        and doc.get('resource_stop_reason') is None and doc.get('resource_watcher_cleanup_confirmed') is True,
        'INSPECT_ANY_FAILED_ATTEMPT_BEFORE_RESUME')


def progress(q, legacy, base, names, required, binding, extras):
    folder = p.c.ROOT / p.DIR
    early = sorted((*folder.glob('p222-admission-run*.v1.json'), *folder.glob('p222-packed-light-run*.v1.json')))
    require(len(early) <= 4096, 'BOUNDED_EARLY_ATTEMPTS')
    for path in early:
        name = path.relative_to(p.c.ROOT).as_posix()
        doc = q.json(name)
        closed_attempt(doc)
    files = sorted(folder.glob('p222-case-*-run*.v1.json'))
    require(len(files) <= 4096, 'BOUNDED_CASES')
    plan = base
    for path in files:
        match = FILE.fullmatch(path.name)
        require(match is not None, 'EXACT_CASE_FILENAME')
        index, run = map(int, match.groups())
        require(1 <= index <= 249 and 1 <= run <= 999, 'CASE_INDEX_RUN')
        name = path.relative_to(p.c.ROOT).as_posix()
        doc = q.json(name)
        closed_attempt(doc)
        require(doc['selected_test_index'] == index, 'EXACT_FILENAME_INDEX')
        body_path = doc['case_receipt_pin']['path']
        require(body_path == f'{p.DIR}/cases/p222-case-{index:03}-run{run:03}.json', 'OWN_BODY_PATH_BEFORE_READ')
        pin = q.pin(body_path)
        require(pin == doc['case_receipt_pin'], 'UNCHANGED_BODY_PIN')
        body = q.json(body_path)
        plan = record(doc, body, pin, required, binding, extras, names, legacy, plan)
    return plan


def contracts(fixtures):
    require(h.contracts(fixtures) == 62 and qualified.contracts() == 16, 'ORIGINAL78_SUPPORT_CONTRACTS')
    sys.path.insert(0, str(p.c.ROOT / 'tools/p09/tests'))
    import test_packed_pressure_runtime as tests
    with patch.object(tests, 'FIXTURES', fixtures), \
            patch('subprocess.Popen', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_CHILD')), \
            patch('subprocess.run', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_CHILD')), \
            patch('threading.Thread.start', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_THREAD')):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun == 10 and not result.skipped, 'BRIDGE_CONTRACT10')
    return 88


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('light', 'actual'), default='light')
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 999, 'CWD_RUN')
    root = p.c.ROOT
    destination = root / f'{p.DIR}/p222-admission-run{args.run:03}.v1.json'
    if args.mode == 'light':
        destination = root / f'{p.DIR}/p222-packed-light-run{args.run:03}.v1.json'
    require(not destination.exists(), 'FRESH_RECEIPT')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = meta = frame = candidate = body = None
    writes = []
    out = dict(schema_version=SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        native_pressure_bridge_connected=False, packed_parent_writer_connected=False,
        packed_root_writer_selected=True, frame_acquisition_requested=False,
        frame_acquisition_complete=False, product_worker_invocation_requested=False,
        accepted_exact_product_body_count=0, original_successful_bodies_not_reexecuted=True,
        receipt_serialization_policy=policy())
    try:
        owner.admit()
        q = Reader(owner, context)
        legacy, base, names, expected, exe, required, extras = anchor(q)
        binding = p.v.identity(names, expected, exe)
        plan = progress(q, legacy, base, names, required, binding, extras)
        index, name = g.old.select(plan, names)
        with context.scope('contract_tests'):
            out['packed_pressure_runtime_contract_tests_passed'] = contracts((legacy, plan, names))
        out.update(binding=binding, selected_test_index=index, selected_test_name=name,
            prior_runtime_plan=plan, immutable_original34_pin=SEALED34,
            extra_frame_controller_pins=list(extras.values()))
        if args.mode == 'light':
            q.finish()
            candidate = dict(state=LIGHT)
        else:
            destination = root / f'{p.DIR}/p222-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(), 'FRESH_EXACT_CASE')
            require(not list((root / p.DIR / 'cases').glob(f'p222-case-{index:03}-run*.json')), 'NO_BODY_RETRY')
            body_path = root / f'{p.DIR}/cases/p222-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True, exist_ok=True)
            q.finish()
            held = h.h.native.PressureInputLocks(root, owner.checkpoint_io, owner)
            require(held.api.pacer.checkpoint is held.open_pressure and held.open_pressure.resources is owner,
                'ORIGINAL_OWNER_NATIVE_PRESSURE_CONNECTION')
            frame = p.frames.Frame(p.frames.Registry(), required, owner.checkpoint_io, held=held)
            counter = p.frames.Counters(q.reader, frame.readers)
            context.reader = counter
            out.update(native_pressure_bridge_connected=True, frame_acquisition_requested=True)
            with context.scope('metadata_hash'):
                frame.acquire()
            out.update(frame_acquisition_complete=True, product_worker_invocation_requested=True,
                packed_parent_writer_connected=True, case_receipt_path=body_path.relative_to(root).as_posix())
            with patch.object(p, 'RAW_DUMP', parent_writer(frame, writes)):
                code = p.run_parent(frame, index, name, body_path, context, binding)
            meta = Reader(owner, context)
            counter.metadata.append(meta.reader)
            context.reader = counter
            body = meta.json(body_path.relative_to(root).as_posix())
            pin = meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_product_child_executed'] = True if body.get('actual_product_child_executed') is True else None
            require(code == 0 and len(writes) == 1, 'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body, name, binding, required)
            stats_contract(writes[0], pin)
            meta.finish()
            component = dict(schema_version=p.CLOSING_SCHEMA, state=p.PASS, **p.r.flags(),
                selected_test_name=name, binding=binding, case_receipt_pin=pin,
                metadata_IO=meta.summary(), source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()), sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin, closing_component=component,
                packed_parent_write_statistics=writes[0])
            candidate = dict(state=PASS, runtime_plan=g.advance(legacy, plan, names, index),
                accepted_exact_product_body_count=1)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt, p.c.subprocess.SubprocessError) as error:
        out.update(state='FAILED_NOT_ACCEPTED', error_code=p.b.run.original.closed_error(error))
        candidate = None
    finally:
        if frame is not None:
            try:
                if not frame.close():
                    out.update(error_code='PACKED_RUNTIME_FRAME_CLEANUP_FAILED')
                    candidate = None
            except (ValueError, OSError):
                out.update(error_code='PACKED_RUNTIME_FRAME_CLEANUP_FAILED')
                candidate = None
            out['terminal_source_frame'] = frame.summary()
        if q is not None:
            out['preparation_IO'] = q.summary()
        out['metadata_observation'] = g.observation.summary(owner)
        def validate(doc):
            if doc['state'] == PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],
                    resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc, body, pin, required, binding, extras, names, legacy, plan)
            else:
                require(doc['state'] == LIGHT and doc['preparation_IO']['finished'] is True, 'LIGHT_ALL_FRESH')
        g.complete(out, owner, candidate, validate)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open('x', encoding='utf-8') as stream:
                packed.dump(out, stream, checkpoint=lambda: terminal_checkpoint(out, owner), indent=2)
        except (ValueError, OSError, TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED', error_code='PACKED_RUNTIME_TERMINAL_SERIALIZATION_FAILED')))
            return 2
        print(json.dumps({k: out.get(k) for k in ('state', 'packed_pressure_runtime_contract_tests_passed',
            'selected_test_index', 'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] in (PASS, LIGHT) else 2


if __name__ == '__main__':
    raise SystemExit(main())
