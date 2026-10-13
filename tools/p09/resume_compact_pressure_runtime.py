"""P220: 원 Native pressure/전후 byte 검사를 유지하고 새 receipt만 compact 저장.

수용된 P218 29개·P219 지원 증거/소스는 수정하지 않는다. 원 P208 parent의
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
import resume_native_pressure_runtime as h
import qualify_receipt_compact_json as qualified

p = h.p
g = h.g
compact = qualified.compact
SELF = 'tools/p09/resume_compact_pressure_runtime.py'
TEST = 'tools/p09/tests/test_compact_pressure_runtime.py'
NEW = (compact.SELF, compact.TEST, qualified.SELF, SELF, TEST)
EXTRAS = (*h.EXTRAS, *NEW)
SCHEMA = 'hwpx-agent.p09-compact-pressure-runtime-pair/v1'
PASS = 'PASS_EXACT_R07_COMPACT_PRESSURE_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT = 'PASS_COMPACT_PRESSURE_SELECTION_NOT_ACTUAL_OR_GATE'
FILE = re.compile(r'p220-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
SEALED29 = dict(path=p.DIR + '/p218-case-029-run008.v1.json', bytes=2222962,
    sha256='6cc90037a0fe969aae7467cab32ea667bf2e08a88c148ccd7da717424b7652d1')
SUPPORT = dict(path=p.DIR + '/p219-compact-receipt-light-run01.v1.json', bytes=18123,
    sha256='fedd3863a799814fa883f5bf1a57a159d4781aaf9466cc120edce5a6c9b901bf')


def require(ok, code):
    p.require(ok, 'COMPACT_RUNTIME_' + code)


def policy():
    return dict(writer_source=compact.SELF, ensure_ascii=True, separators=[',', ':'], indent=None,
        original_parent_keywords=dict(ensure_ascii=False, indent=2), semantic_fields_removed=0,
        parent_original_frame_guard_connected=True, root_written_after_original_resource_cleanup=True,
        root_terminal_lifecycle_checkpoint_only=True, new_sampler_started=False,
        original_receipts_rewritten=False, CPU_or_PC_freeze_improvement_claimed=False)


def canonical(doc, pin, checkpoint):
    digest = hashlib.sha256()
    class Sink:
        def write(self, text):
            digest.update(text.encode('ascii'))
            return len(text)
    stats = compact.dump(doc, Sink(), checkpoint=checkpoint, indent=2)
    require(stats['characters_written'] == pin['bytes'] and digest.hexdigest() == pin['sha256'],
        'EXACT_CANONICAL_BYTES_NOT_ONLY_DECLARED_STYLE')


def stats_contract(row, pin):
    require(row['characters_written'] == pin['bytes'] and row['write_batches'] >= 1
        and 0 < row['maximum_write_batch_chars'] <= compact.WRITE_CHARS
        and row['maximum_allowed_write_batch_chars'] == compact.WRITE_CHARS
        and row['guard_token_interval'] == compact.GUARD_TOKEN_INTERVAL
        and row['semantic_fields_intentionally_removed'] == 0
        and row['extra_sampler_or_native_query_started'] is False
        and row['original_files_rewritten'] is False, 'ORIGINAL_PARENT_COMPLETE_COMPACT_WRITE')


def parent_writer(frame, completed):
    def write(doc, stream, **keywords):
        require(keywords == dict(ensure_ascii=False, indent=2), 'EXACT_ORIGINAL_PARENT_DUMP_OPTIONS')
        # ASCII escape representation alone changes; JSON values are unchanged.
        # The original parent already validated doc before invoking this writer.
        stats = compact.dump(doc, stream, checkpoint=frame.check, indent=2)
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
    require(base['runtime_source_qualified_individual_cases'] == 29 and base['next_runtime_index'] == 30
        and q.pin(SEALED29['path']) == SEALED29, 'SEALED29_NOT_REEXECUTED')
    require(q.pin(SUPPORT['path']) == SUPPORT, 'LITERAL_COMPACT_SUPPORT_PIN')
    support = q.json(SUPPORT['path'])
    require(support['schema_version'] == qualified.SCHEMA and support['state'] == qualified.PASS
        and support.get('error_code') is None and support['resource_stop_reason'] is None
        and support['resource_watcher_cleanup_confirmed'] is True
        and support['compact_receipt_contract_tests_passed'] == 12
        and support['IO']['finished'] is True
        and support['IO']['bound_inputs'] == support['IO']['final_fresh_hashes'] == 5
        and support['actual_product_bridge_connected'] is False
        and support['actual_compact_product_receipt_executed'] is False
        and support['original_receipts_rewritten'] is False
        and len(support['bound_input_pins']) == 5
        and all(q.pin(pin['path']) == pin for pin in support['bound_input_pins']),
        'UNCHANGED_SUPPORT_ONLY_NOT_ACTUAL')
    added = {name: q.pin(name) for name in NEW}
    required = {**old_required, **added}
    extras = {**old_extras, **added}
    require(len(required) == 1498 and len(extras) == 31 and set(old_required) < set(required),
        'ALL_ORIGINAL1493_PLUS_NEW5')
    return legacy, base, names, expected, exe, required, extras


def native_pair(component, body, pin, required, binding, extras):
    p.validate_closing(component, body, pin, required, binding, extras)
    frame = component['source_frame']
    own = frame['handles']
    dup = own['borrowed_byte_streams']
    count = len(required)
    require(count == 1498 and own['input_lock_handles_opened'] == own['input_lock_handles_closed'] == count + 306
        and own['maximum_lock_seconds'] == 600 and own['ancestor_walk_steps'] == 305
        and own['native_open_pacing']['maximum_opens_per_second'] == 32
        and own['native_open_pacing']['open_reservations'] == 3 * count + 306
        and dup['duplicate_handles_opened'] == dup['duplicate_handles_closed'] == dup['shared_offset_resets'] == 2 * count
        and dup['duplicate_handles_remaining'] == dup['duplicate_close_failed_attempts'] == dup['byte_stream_pathname_reopens'] == 0
        and frame['held_identity_after_owned_cleanup'] == dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0, regular_file_count=count, directory_count=306),
        'ALL_NATIVE_ORIGINAL_STREAMS_AND_IDENTITIES')
    h.pressure_contract(own['native_open_backpressure'])


def record(doc, body, pin, required, binding, extras, names, legacy, base):
    index, name = g.old.select(base, names)
    require(doc['schema_version'] == SCHEMA and doc['state'] == PASS and doc.get('error_code') is None
        and doc['compact_pressure_runtime_contract_tests_passed'] == 62
        and doc['selected_test_index'] == index and doc['selected_test_name'] == name
        and doc['binding'] == binding and doc['prior_runtime_plan'] == base and doc['case_receipt_pin'] == pin
        and all(doc[k] is True for k in ('native_pressure_bridge_connected', 'compact_parent_writer_connected',
            'compact_root_writer_selected', 'frame_acquisition_requested', 'frame_acquisition_complete',
            'product_worker_invocation_requested', 'actual_product_child_executed', 'resource_watcher_cleanup_confirmed'))
        and doc['receipt_serialization_policy'] == policy() and doc['resource_stop_reason'] is None
        and doc['P09_gate'] == doc['A12_gate'] == doc['A13_gate'] == 'OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified', 'historical67_current_fresh_qualified',
            'full249_current_qualified', 'signed16_current_qualified', 'product_complete', 'PC_freeze_resolved'))
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs'] == doc['preparation_IO']['final_fresh_hashes'],
        'COMPLETE_OVERALL_WITH_ORIGINAL_GATES')
    native_pair(doc['closing_component'], body, pin, required, binding, extras)
    stats_contract(doc['compact_parent_write_statistics'], pin)
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
    early = sorted((*folder.glob('p220-admission-run*.v1.json'), *folder.glob('p220-compact-light-run*.v1.json')))
    require(len(early) <= 4096, 'BOUNDED_EARLY_ATTEMPTS')
    for path in early:
        name = path.relative_to(p.c.ROOT).as_posix()
        doc = q.json(name)
        closed_attempt(doc)
        canonical(doc, q.reader.snapshots[name], q.checkpoint)
    files = sorted(folder.glob('p220-case-*-run*.v1.json'))
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
        canonical(doc, q.reader.snapshots[name], q.checkpoint)
        require(doc['selected_test_index'] == index, 'EXACT_FILENAME_INDEX')
        body_path = doc['case_receipt_pin']['path']
        require(body_path == f'{p.DIR}/cases/p220-case-{index:03}-run{run:03}.json', 'OWN_BODY_PATH_BEFORE_READ')
        pin = q.pin(body_path)
        require(pin == doc['case_receipt_pin'], 'UNCHANGED_BODY_PIN')
        body = q.json(body_path)
        canonical(body, pin, q.checkpoint)
        plan = record(doc, body, pin, required, binding, extras, names, legacy, plan)
    return plan


def contracts(fixtures):
    require(h.contracts(fixtures) == 40 and qualified.contracts() == 12, 'ORIGINAL52_SUPPORT_CONTRACTS')
    sys.path.insert(0, str(p.c.ROOT / 'tools/p09/tests'))
    import test_compact_pressure_runtime as tests
    with patch.object(tests, 'FIXTURES', fixtures), \
            patch('subprocess.Popen', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_CHILD')), \
            patch('subprocess.run', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_CHILD')), \
            patch('threading.Thread.start', side_effect=AssertionError('NO_COMPACT_BRIDGE_CONTRACT_THREAD')):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun == 10 and not result.skipped, 'BRIDGE_CONTRACT10')
    return 62


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('light', 'actual'), default='light')
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 999, 'CWD_RUN')
    root = p.c.ROOT
    destination = root / f'{p.DIR}/p220-admission-run{args.run:03}.v1.json'
    if args.mode == 'light':
        destination = root / f'{p.DIR}/p220-compact-light-run{args.run:03}.v1.json'
    require(not destination.exists(), 'FRESH_RECEIPT')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = meta = frame = candidate = body = None
    writes = []
    out = dict(schema_version=SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        native_pressure_bridge_connected=False, compact_parent_writer_connected=False,
        compact_root_writer_selected=True, frame_acquisition_requested=False,
        frame_acquisition_complete=False, product_worker_invocation_requested=False,
        accepted_exact_product_body_count=0, original_successful_bodies_not_reexecuted=True,
        receipt_serialization_policy=policy())
    try:
        owner.admit()
        q = p.qualification.Reader(owner, context)
        legacy, base, names, expected, exe, required, extras = anchor(q)
        binding = p.v.identity(names, expected, exe)
        plan = progress(q, legacy, base, names, required, binding, extras)
        index, name = g.old.select(plan, names)
        with context.scope('contract_tests'):
            out['compact_pressure_runtime_contract_tests_passed'] = contracts((legacy, plan, names))
        out.update(binding=binding, selected_test_index=index, selected_test_name=name,
            prior_runtime_plan=plan, immutable_original29_pin=SEALED29,
            extra_frame_controller_pins=list(extras.values()))
        if args.mode == 'light':
            q.finish()
            candidate = dict(state=LIGHT)
        else:
            destination = root / f'{p.DIR}/p220-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(), 'FRESH_EXACT_CASE')
            require(not list((root / p.DIR / 'cases').glob(f'p220-case-{index:03}-run*.json')), 'NO_BODY_RETRY')
            body_path = root / f'{p.DIR}/cases/p220-case-{index:03}-run{args.run:03}.json'
            body_path.parent.mkdir(parents=True, exist_ok=True)
            q.finish()
            held = h.native.PressureInputLocks(root, owner.checkpoint_io, owner)
            require(held.api.pacer.checkpoint is held.open_pressure and held.open_pressure.resources is owner,
                'ORIGINAL_OWNER_NATIVE_PRESSURE_CONNECTION')
            frame = p.frames.Frame(p.frames.Registry(), required, owner.checkpoint_io, held=held)
            counter = p.frames.Counters(q.reader, frame.readers)
            context.reader = counter
            out.update(native_pressure_bridge_connected=True, frame_acquisition_requested=True)
            with context.scope('metadata_hash'):
                frame.acquire()
            out.update(frame_acquisition_complete=True, product_worker_invocation_requested=True,
                compact_parent_writer_connected=True, case_receipt_path=body_path.relative_to(root).as_posix())
            with patch.object(p, 'RAW_DUMP', parent_writer(frame, writes)):
                code = p.run_parent(frame, index, name, body_path, context, binding)
            meta = p.qualification.Reader(owner, context)
            counter.metadata.append(meta.reader)
            context.reader = counter
            body = meta.json(body_path.relative_to(root).as_posix())
            pin = meta.reader.snapshots[body_path.relative_to(root).as_posix()]
            out['actual_product_child_executed'] = True if body.get('actual_product_child_executed') is True else None
            require(code == 0 and len(writes) == 1, 'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body, name, binding, required)
            stats_contract(writes[0], pin)
            canonical(body, pin, meta.checkpoint)
            meta.finish()
            component = dict(schema_version=p.CLOSING_SCHEMA, state=p.PASS, **p.r.flags(),
                selected_test_name=name, binding=binding, case_receipt_pin=pin,
                metadata_IO=meta.summary(), source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()), sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin, closing_component=component,
                compact_parent_write_statistics=writes[0])
            candidate = dict(state=PASS, runtime_plan=g.advance(legacy, plan, names, index),
                accepted_exact_product_body_count=1)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt, p.c.subprocess.SubprocessError) as error:
        out.update(state='FAILED_NOT_ACCEPTED', error_code=p.b.run.original.closed_error(error))
        candidate = None
    finally:
        if frame is not None:
            try:
                if not frame.close():
                    out.update(error_code='COMPACT_RUNTIME_FRAME_CLEANUP_FAILED')
                    candidate = None
            except (ValueError, OSError):
                out.update(error_code='COMPACT_RUNTIME_FRAME_CLEANUP_FAILED')
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
                compact.dump(out, stream, checkpoint=lambda: terminal_checkpoint(out, owner), indent=2)
        except (ValueError, OSError, TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED', error_code='COMPACT_RUNTIME_TERMINAL_SERIALIZATION_FAILED')))
            return 2
        print(json.dumps({k: out.get(k) for k in ('state', 'compact_pressure_runtime_contract_tests_passed',
            'selected_test_index', 'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] in (PASS, LIGHT) else 2


if __name__ == '__main__':
    raise SystemExit(main())
