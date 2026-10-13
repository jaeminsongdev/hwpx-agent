"""P228: 원 입력·PASS·CPU 보호 유지, 검토된 이전 STOP 보존과 종료 실패 capture 연결.

수용된 P220/P222와 P226 STOP/빈 body 및 P227 지원 증거/소스는 수정하지 않는다. 원 P208 parent의
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
import resume_packed_pressure_runtime as original
import deferred_parent_failure as adapter
import qualify_deferred_parent_failure as qualified
h = original.h

p = h.p
g = h.g
packed = original.packed
compact = packed.compact
SELF = 'tools/p09/resume_deferred_failure_runtime.py'
TEST = 'tools/p09/tests/test_deferred_failure_runtime.py'
NEW = (adapter.SELF, adapter.TEST, adapter.failure.SELF, adapter.failure.TEST, qualified.SELF, SELF, TEST)
EXTRAS = (*original.EXTRAS, *NEW)
SCHEMA = 'hwpx-agent.p09-deferred-failure-runtime-pair/v1'
PASS = 'PASS_EXACT_R07_DEFERRED_FAILURE_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT = 'PASS_DEFERRED_FAILURE_SELECTION_NOT_ACTUAL_OR_GATE'
FILE = re.compile(r'p228-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
SEALED34 = dict(path=p.DIR + '/p220-case-034-run005.v1.json', bytes=1588449,
    sha256='49c1280ee39dac81d4140dba7ba0890b24375a87c659111bf561f8888889f6d8')
SUPPORT = dict(path=p.DIR + '/p221-packed-receipt-light-run01.v1.json', bytes=18137,
    sha256='c01529a6ade583042ef46fb5aef544f32a96cb7243a013bc73e23c1a3a3a554c')


def require(ok, code):
    p.require(ok, 'DEFERRED_RUNTIME_' + code)


class Reader(original.Reader):
    def json(self, path):
        carrier = super().json(path)
        name = self.name(path)
        if name.startswith(p.DIR + '/p228-') or name.startswith(p.DIR + '/cases/p228-'):
            # 원 실제 fresh 읽기는 superclass에 유지하고 해제 검사는 추가한다.
            h.canonical(carrier, self.reader.snapshots[name], self.checkpoint)
            return packed.unpack(carrier, self.checkpoint) if carrier.get('schema_version') == packed.SCHEMA else carrier
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


STOP_PIN = dict(path=p.DIR+'/p222-case-060-run020.v1.json', bytes=208007,
    sha256='78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0')
REVIEW_PIN = dict(path=p.DIR+'/p226-stop-review-run01.v1.json',bytes=14694,
    sha256='f1ee9b8c0250cecd2ec51852f5a8dcfc8c9ff5ca9499f39ddc57a75d4a3eb530')
CONNECTION_PIN = dict(path=p.DIR+'/p227-parent-stop-connection-run01.v1.json',bytes=6857,
    sha256='3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68')


def reviewed_stop(doc,pin,plan):
    require(pin==STOP_PIN and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P206_LOCK_P208_FRAME_LIVE_STATE'
        and doc['resource_stop_reason']==adapter.failure.STOP
        and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['selected_test_index']==plan['next_runtime_index']==60
        and doc['prior_runtime_plan']==plan,'LITERAL_REVIEWED_STOP_NOT_PASS')
    frame=doc['terminal_source_frame'];own=frame['handles'];dup=own['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1503 and frame['input_bytes']==118841107
        and own['input_lock_cleanup_confirmed'] is True
        and own['input_lock_handles_opened']==own['input_lock_handles_closed']==1809
        and own['input_lock_handles_remaining']==own['active_reader_bindings']==own['active_byte_streams']==0
        and own['handle_close_failed_attempts']==0
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==2210
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0,
        'REVIEWED_STOP_ALL_INPUT_HANDLES_CLOSED')


def anchor(q):
    legacy,base,names,expected,exe,old_required,old_extras=original.anchor(q)
    require(q.pin(REVIEW_PIN['path'])==REVIEW_PIN,'EXACT_COMPLETED_STOP_REVIEW')
    review=q.json(REVIEW_PIN['path'])
    require(review['state']=='PASS_BOUNDED_STOP_REVIEW_AND_FAILURE_WRITER_SUPPORT_NOT_RUNTIME_OR_GATE'
        and review['original_stop_pin']==STOP_PIN and review['runtime_resume_authorized'] is False
        and review['empty_body_semantic_or_job_result_established'] is False
        and review['IO']['finished'] is True and review['IO']['bound_inputs']==review['IO']['final_fresh_hashes']==12
        and review['resource_stop_reason'] is None and review['resource_watcher_cleanup_confirmed'] is True
        and all(q.pin(pin['path'])==pin for pin in review['bound_input_pins']),'REVIEW_ONLY_NO_OLD_BODY_ACCEPTANCE')
    early=sorted((* (p.c.ROOT/p.DIR).glob('p222-admission-run*.v1.json'),
                  * (p.c.ROOT/p.DIR).glob('p222-packed-light-run*.v1.json')))
    require(len(early)<=4096,'BOUNDED_ORIGINAL_EARLY')
    for path in early:original.closed_attempt(q.json(path.relative_to(p.c.ROOT).as_posix()))
    plan=base;stops=0
    for path in sorted((p.c.ROOT/p.DIR).glob('p222-case-*-run*.v1.json')):
        match=original.FILE.fullmatch(path.name);require(match is not None,'ORIGINAL_FILENAME')
        index,run=map(int,match.groups());require(1<=index<=249 and 1<=run<=999,'ORIGINAL_INDEX')
        name=path.relative_to(p.c.ROOT).as_posix();doc=q.json(name)
        if name==STOP_PIN['path']:
            reviewed_stop(doc,q.pin(name),plan);stops+=1
            require(doc['selected_test_name']==names[index-1]
                and q.pin(review['empty_body_pin']['path'])==review['empty_body_pin'],
                'KEEP_EXACT_ZERO_BODY_AND_NO_SEMANTIC_CLAIM')
            continue
        original.closed_attempt(doc)
        require(doc['selected_test_index']==index,'ORIGINAL_FILENAME_INDEX')
        pin=doc['case_receipt_pin']
        require(pin['path']==f'{p.DIR}/cases/p222-case-{index:03}-run{run:03}.json'
            and q.pin(pin['path'])==pin,'ORIGINAL_BODY_PIN')
        body=q.json(pin['path'])
        plan=original.record(doc,body,pin,old_required,p.v.identity(names,expected,exe),old_extras,names,legacy,plan)
    require(stops==1 and plan==review['runtime_plan'],'ONE_STOP_NO_SILENT_SKIP_OR_RECLASSIFICATION')
    require(q.pin(CONNECTION_PIN['path'])==CONNECTION_PIN,'EXACT_PARENT_CONNECTION_SUPPORT')
    proof=q.json(CONNECTION_PIN['path'])
    require(proof['state']==qualified.PASS and proof['connection_contract_tests_passed']==44
        and proof['original_parent_call_path_exercised'] is True
        and proof['real_filesystem_sidecar_written_after_original_owner_cleanup'] is True
        and proof['actual_product_worker_executed'] is False and proof['runtime_resume_authorized'] is False
        and proof['IO']['finished'] is True and proof['IO']['bound_inputs']==proof['IO']['final_fresh_hashes']==17
        and proof['resource_stop_reason'] is None and proof['resource_watcher_cleanup_confirmed'] is True
        and all(q.pin(pin['path'])==pin for pin in proof['bound_input_pins']),'UNCHANGED_SYNTHETIC_CONNECTION_NOT_PRODUCT')
    require(q.pin(proof['synthetic_sidecar_pin']['path'])==proof['synthetic_sidecar_pin'],'CONNECTION_OUTPUT_FRESH')
    example=q.json(proof['synthetic_sidecar_pin']['path'])
    require(example['state']=='STOPPED_NOT_ACCEPTED' and example['capture']['error_code']=='NO_CAPTURE'
        and example['passed_test_names']==[],'SYNTHETIC_OUTPUT_NEVER_RUNTIME_EVIDENCE')
    added={name:q.pin(name) for name in NEW};required={**old_required,**added};extras={**old_extras,**added}
    require(len(required)==1510 and len(extras)==43 and set(old_required)<set(required),'ORIGINAL1503_PLUS_NEW7')
    return legacy,plan,names,expected,exe,required,extras


def native_pair(component, body, pin, required, binding, extras):
    p.validate_closing(component, body, pin, required, binding, extras)
    frame = component['source_frame']
    own = frame['handles']
    dup = own['borrowed_byte_streams']
    count = len(required)
    require(count == 1510 and own['input_lock_handles_opened'] == own['input_lock_handles_closed'] == count + 306
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
        and doc['deferred_failure_runtime_contract_tests_passed'] == 144
        and doc['selected_test_index'] == index and doc['selected_test_name'] == name
        and doc['deferred_failure_capture_connected'] is True
        and doc['reviewed_original_stop_pin']==STOP_PIN
        and doc['completed_stop_review_pin']==REVIEW_PIN
        and doc['parent_connection_support_pin']==CONNECTION_PIN
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
    early = sorted((*folder.glob('p228-admission-run*.v1.json'), *folder.glob('p228-packed-light-run*.v1.json')))
    require(len(early) <= 4096, 'BOUNDED_EARLY_ATTEMPTS')
    for path in early:
        name = path.relative_to(p.c.ROOT).as_posix()
        doc = q.json(name)
        closed_attempt(doc)
    files = sorted(folder.glob('p228-case-*-run*.v1.json'))
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
        require(body_path == f'{p.DIR}/cases/p228-case-{index:03}-run{run:03}.json', 'OWN_BODY_PATH_BEFORE_READ')
        pin = q.pin(body_path)
        require(pin == doc['case_receipt_pin'], 'UNCHANGED_BODY_PIN')
        body = q.json(body_path)
        plan = record(doc, body, pin, required, binding, extras, names, legacy, plan)
    return plan


def contracts(fixtures):
    require(original.contracts(fixtures[:3])==88 and qualified.contracts()==44,'ORIGINAL132_CONTRACTS')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_deferred_failure_runtime as tests
    with patch.object(tests,'FIXTURES',fixtures), \
         patch('subprocess.Popen',side_effect=AssertionError('NO_DEFERRED_RUNTIME_CONTRACT_CHILD')), \
         patch('subprocess.run',side_effect=AssertionError('NO_DEFERRED_RUNTIME_CONTRACT_CHILD')), \
         patch('threading.Thread.start',side_effect=AssertionError('NO_DEFERRED_RUNTIME_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'DEFERRED_RUNTIME_CONTRACT12')
    return 144


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('light', 'actual'), default='light')
    ap.add_argument('--run', type=int, required=True)
    args = ap.parse_args()
    require(p.c.Path.cwd().resolve() == p.c.ROOT and 1 <= args.run <= 999, 'CWD_RUN')
    root = p.c.ROOT
    destination = root / f'{p.DIR}/p228-admission-run{args.run:03}.v1.json'
    if args.mode == 'light':
        destination = root / f'{p.DIR}/p228-packed-light-run{args.run:03}.v1.json'
    require(not destination.exists(), 'FRESH_RECEIPT')
    context = g.observation.Context()
    owner = g.observation.Resources(context)
    q = meta = frame = candidate = body = capture = None
    writes = []
    out = dict(schema_version=SCHEMA, state='FAILED_NOT_ACCEPTED', **p.r.flags(),
        reviewed_original_stop_pin=STOP_PIN,completed_stop_review_pin=REVIEW_PIN,
        parent_connection_support_pin=CONNECTION_PIN,
        native_pressure_bridge_connected=False, packed_parent_writer_connected=False, deferred_failure_capture_connected=False,
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
            out['deferred_failure_runtime_contract_tests_passed'] = contracts((legacy, plan, names, q.json(STOP_PIN['path'])))
        out.update(binding=binding, selected_test_index=index, selected_test_name=name,
            prior_runtime_plan=plan, immutable_original34_pin=SEALED34,
            extra_frame_controller_pins=list(extras.values()))
        if args.mode == 'light':
            q.finish()
            candidate = dict(state=LIGHT)
        else:
            destination = root / f'{p.DIR}/p228-case-{index:03}-run{args.run:03}.v1.json'
            require(not destination.exists(), 'FRESH_EXACT_CASE')
            require(not list((root / p.DIR / 'cases').glob(f'p228-case-{index:03}-run*.json')), 'NO_BODY_RETRY')
            body_path = root / f'{p.DIR}/cases/p228-case-{index:03}-run{args.run:03}.json'
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
                packed_parent_writer_connected=True, deferred_failure_capture_connected=True, case_receipt_path=body_path.relative_to(root).as_posix())
            capture = adapter.Capture(frame, writes, index, name, binding)
            with patch.object(p, 'RAW_DUMP', capture.writer):
                code = p.run_parent(frame, index, name, body_path, context, binding)
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted'] = True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
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
        if capture is not None and capture.pending:
            failure_path=root/f'{p.DIR}/cases/p228-failure-{index:03}-run{args.run:03}.json'
            try:
                digest=hashlib.sha256();written=0
                class Output:
                    def __init__(self,stream):self.stream=stream
                    def write(self,block):
                        nonlocal written
                        count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_WRITE_ONCE')
                        digest.update(block.encode('ascii'));written+=count;return count
                with failure_path.open('x',encoding='utf-8') as stream:
                    stats=capture.write_terminal(Output(stream),owner,out)
                out.update(terminal_parent_failure_sidecar_pin=dict(path=failure_path.relative_to(root).as_posix(),
                    bytes=written,sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,
                    original_failure_body_placeholder_preserved=True)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x', encoding='utf-8') as stream:
                if out['state'] in (PASS,LIGHT):
                    packed.dump(out,stream,checkpoint=lambda:terminal_checkpoint(out,owner),indent=2)
                else:
                    compact.dump(out,stream,checkpoint=lambda:terminal_checkpoint(out,owner),indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='DEFERRED_RUNTIME_TERMINAL_SERIALIZATION_FAILED')))
            return 2
        print(json.dumps({k: out.get(k) for k in ('state', 'deferred_failure_runtime_contract_tests_passed',
            'selected_test_index', 'error_code', 'resource_stop_reason')}))
    return 0 if out['state'] in (PASS, LIGHT) else 2


if __name__ == '__main__':
    raise SystemExit(main())
