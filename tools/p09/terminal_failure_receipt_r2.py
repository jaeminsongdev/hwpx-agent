"""P227 r2: 보호 중단 후 정리된 실패 증거만 낮은 비용으로 보존.

아직 실제 parent에 연결하지 않는다. PASS writer/guard를 대체하지 않는다.
caller는 새 sidecar를 exclusive-create로 열고 기존 0-byte/STOP 파일을 보존해야 한다.
gzip·frame 재검사·새 sampler·Native query·원본 읽기·재시도 없이 전체 JSON 값을 쓴다.
"""
import receipt_compact_json as compact

SELF = 'tools/p09/terminal_failure_receipt_r2.py'
TEST = 'tools/p09/tests/test_terminal_failure_receipt_r2.py'
MAX_BYTES = 16 * 1024 * 1024
STOP = 'STOP_SUSTAINED_SYSTEM_CPU'


def require(ok, code):
    if not ok:
        raise ValueError('TERMINAL_FAILURE_' + code)


def validate_parent(document):
    require(isinstance(document, dict), 'PARENT_OBJECT')
    require(document.get('state') in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
        and document.get('stop_reason') == STOP
        and document.get('resource_stop_reason') == STOP, 'EXACT_STOP_NOT_PASS')
    require(document.get('cleanup_confirmed') is True
        and document.get('owned_tree_empty') is True, 'PARENT_CLEANUP')
    if document['state'] == 'DEFERRED_NOT_STARTED':
        require(document.get('heavy_work_started') is False
            and document.get('actual_product_child_executed') is False, 'DEFERRED_NOT_EXECUTED')
    job = document.get('job_final')
    if job is None:
        require(document['state'] == 'DEFERRED_NOT_STARTED'
            and all(document.get(key) is False for key in
                ('worker_created','job_assigned','writer_authorized')), 'NO_JOB_ONLY_BEFORE_SETUP')
    else:
        require(isinstance(job, dict) and type(job.get('active_processes')) is int
            and job['active_processes'] == 0 and job.get('owned_processes') == [], 'EMPTY_JOB')


def validate(document, lifecycle):
    require(isinstance(lifecycle, dict), 'LIFECYCLE_OBJECT')
    validate_parent(document)
    require(all(document.get(key) is False for key in
        ('product_complete', 'full249_current_qualified', 'signed16_current_qualified',
         'whole1470_current_fresh_qualified', 'PC_freeze_resolved'))
        and all(document.get(key) == 'OPEN' for key in ('P09_gate', 'A12_gate', 'A13_gate')),
        'NO_GATE_PROMOTION')
    require(lifecycle.get('owner_done') is True and lifecycle.get('owner_cleanup_confirmed') is True
        and lifecycle.get('frame_state') == 'CLOSED'
        and lifecycle.get('input_lock_cleanup_confirmed') is True
        and lifecycle.get('original_stop_reason') == STOP, 'TERMINAL_CLEANUP_ONLY')
    require(all(type(lifecycle.get(key)) is int and lifecycle[key] == 0 for key in
        ('input_lock_handles_remaining', 'duplicate_handles_remaining', 'active_byte_streams')),
        'ZERO_HANDLES_NOT_BOOLEAN')


def dump(document, stream, *, lifecycle):
    # 종료 snapshot만 받고 CPU guard/frame을 재시작하지 않는다.
    # snapshot을 생성하는 caller의 구현·실제 연결은 별도 검증이 필요하다.
    validate(document, lifecycle)
    require(callable(getattr(stream, 'write', None)), 'STREAM')
    original_state = document['state']
    original_reason = document['stop_reason']
    written = 0

    def checkpoint():
        validate(document, lifecycle)
        require(document['state'] == original_state and document['stop_reason'] == original_reason,
            'STATE_UNCHANGED')

    class BoundedStream:
        def write(self, block):
            nonlocal written
            require(isinstance(block, str) and block.isascii()
                and 0 < len(block) <= compact.WRITE_CHARS, 'BOUNDED_ASCII_BLOCK')
            require(written + len(block) <= MAX_BYTES, 'MAX_BYTES')
            count = stream.write(block)
            require(type(count) is int and count == len(block), 'SHORT_WRITE_NO_RETRY')
            written += count
            return count

    statistics = compact.dump(document, BoundedStream(), checkpoint=checkpoint, indent=2)
    require(statistics['characters_written'] == written, 'ACCOUNTING')
    return dict(**statistics, terminal_failed_evidence_only=True, gzip_used=False,
        original_live_frame_guard_restarted=False, maximum_bytes=MAX_BYTES,
        product_body_executed=False, runtime_accepted=False, CPU_improvement_established=False)
