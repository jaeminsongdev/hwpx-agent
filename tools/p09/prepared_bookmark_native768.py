"""Renamed eight product candidates, three image roles and original guarded tree drain.
Consumed runs remain immutable. Captures never attest semantics.
"""
import json
import prepared_bookmark768_evidence as evidence
import prepared_bookmark689_drain as drain
import sys
from pathlib import Path

import bookmark_cursor_preparation768 as prepared
import crossref_external_batch_runtime as base
import crossref_fixed_worker as worker_base
import prepared_bookmark690_io as io
import prepared_bookmark768_sections as sections

r = base.r
require = base.require
SELF = 'tools/p09/prepared_bookmark_native768.py'
ENTRY = 'tools/p09/run_prepared_bookmark_native768.py'
TARGET = 'implementation/p09/tools/run-prepared-bookmark768-worker.ps1'
PORTS = 'implementation/p09/tools/prepared-bookmark768-ports.ps1'
CHANNEL = 'implementation/p09/tools/prepared-bookmark768-channel.ps1'
PREFIX = 'implementation/p09/evidence/private/p09-361-prepared-bookmark768-native001-c'
REQUEST = 'hwpx-agent.private.prepared-bookmark768-request/v1'
RESPONSE = 'hwpx-agent.private.prepared-bookmark768-response/v1'
STEPS = ('prepare_slot', 'create_save_session', 'candidate_open', 'candidate_bind',
         'initial_identity', 'initial_snapshot', 'initial_image', 'saved_save', 'saved_bind',
         'save_session_close', 'create_reopen_session', 'fresh_saved_open',
         'reopened_save', 'reopened_image', 'reopen_session_close', 'final_source_check')
LEGACY = dict(zip(STEPS, base.batch.original.original.STEPS))
SOURCES = set(base.candidate.SOURCES) | {SELF, ENTRY, TARGET, PORTS, CHANNEL,
    
    'tools/p09/bookmark_cursor_preparation768.py','tools/p09/prepared_bookmark690_io.py','tools/p09/prepared_bookmark690_notice.py',
    'tools/p09/prepared_bookmark768_sections.py', 'tools/p09/prepared_bookmark689_drain.py',
    'tools/p09/prepared_bookmark768_evidence.py',
    'implementation/p09/tools/crossref-save-reopen.ps1','implementation/p09/tools/bookmark-target-cursor768.ps1',
    'implementation/p09/tools/crossref-capture008-application-binding.ps1'}


def directory(index):
    require(type(index) is int and 1 <= index <= 8, 'PREPARED768_EXACT_CASE')
    return PREFIX + f'{index:02}'


def absent():
    for i in range(1, 9):
        prepared.require_absent(r.c.ROOT, directory(i))


def translate_request(raw):
    require(type(raw) is str and 0 < len(raw.encode()) <= 4096 and '\n' not in raw and '\r' not in raw,
            'PREPARED768_WIRE_BOUND')
    value = json.loads(raw, object_pairs_hook=base.batch.original.original.unique_pairs)
    require(type(value) is dict and value.get('schema_version') == REQUEST, 'PREPARED768_DISTINCT_PURPOSE_SCHEMA')
    result = dict(value, schema_version=base.batch.original.REQUEST)
    if value.get('operation') == 'checkpoint':
        require(type(value.get('step')) is str and value['step'] in LEGACY, 'PREPARED768_EXACT_STEP')
        result['step'] = LEGACY[value['step']]
    # Original exact keys/types/owner/sequence limits are not relaxed.
    base.batch.original.decode_request(json.dumps(result, separators=(',', ':')))
    require(1 <= result['case_index'] <= 8, 'PREPARED768_TAIL_TWO_ONLY')
    return value, result


class Host(base.batch.FixedEightHost):
    def respond(self, raw):
        try:
            _, internal = translate_request(raw)
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            self.protocol.protocol.stopped = True
            self.scope.stopped = True
            raise
        exact = (internal['sequence'] == self.protocol.protocol.sequence+1
                 and internal['case_index'] == self.scope.case_index)
        if exact and internal['operation'] == 'checkpoint' and not self.protocol.protocol.stopped:
            expected = base.batch.original.original.STEPS
            if self.scope.cursor >= len(expected) or internal['step'] != expected[self.scope.cursor]:
                self.protocol.protocol.stopped = self.scope.stopped = True
                raise ValueError('XREF_PREPARED768_EXACT_NEXT_CHECKPOINT')
            if internal['step'] in ('create_reopen_session', 'final_source_check'):
                try:
                    require(self.ready and self.worker_lease is not None, 'PREPARED768_CURRENT_EXACT_WORKER')
                    self.worker_lease.observe(refresh_image=False)
                    drain.wait(self.scope.current, self.guard, self.worker, self.drain_notify, self.drain_records)
                except BaseException:
                    self.protocol.protocol.stopped = True
                    self.scope.stopped = True
                    raise
        result = json.loads(super().respond(json.dumps(internal, separators=(',', ':'))))
        result['schema_version'] = RESPONSE
        return json.dumps(result, separators=(',', ':'))

    def close(self):
        # Transport first waits for the exact native tree. No unguarded work loop.
        self.scope.close()
        if self.worker_lease is not None:
            self.worker_lease.close()

    def summary(self):
        return dict(super().summary(), drain_records=getattr(self, 'drain_records', []), purpose='prepared_candidate_open_save_reopen_direct_BMP_only',
                    legacy_schedule_is_resource_bookkeeping_only=True, SDK_insertion_invoked=False,
                    reference_semantics_qualified=False)


class Worker(worker_base.FixedWorker):
    def _fixed_command(self, reader):
        require(reader.root.resolve() == r.c.ROOT.resolve(), 'PREPARED768_FIXED_ROOT')
        for path in sorted(SOURCES):
            reader.pin(path)
        require(reader.snapshots[base.candidate.original.BOOTSTRAP]['sha256'] == base.candidate.original.BOOTSTRAP_SHA,
                'PREPARED768_ORIGINAL_BOOTSTRAP')
        args = [base.candidate.original.SHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-STA',
                '-File', str(r.c.ROOT / TARGET), '-PreparedBookmarkCursorEightAfterCurrentSession']
        return [sys.executable, '-B', str(r.c.ROOT / base.candidate.original.BOOTSTRAP), '--worker', json.dumps(args, ensure_ascii=False)]


class Cases(base.CaseInputs):
    def __init__(self, guard, manifest, shell_expected, paths):
        super().__init__(guard, manifest, shell_expected, fixed_capture004=True)
        self.paths = paths

    def between(self, index):
        h = self.host
        s = h.scope
        p = h.protocol.protocol
        require(self.current is None and len(self.rows) == index - 1
                and all(sections.closed_boundary(v) for v in self.rows)
                and h.ready and h.source_case is None and s.current is None
                and not s.pending_admission and not s.stopped and not p.stopped
                and s.case_index == p.case_index == index and s.cursor == 0
                and len(s.sessions) == 2*(index-1) and len(s.finished) == index-1,
                'PREPARED768_CLOSED_PREVIOUS_CASE_AND_OWNERS')
        require(all(v['startup_profile']['cleanup_confirmed'] is True for v in s.sessions)
                and self.handoff.consumed and self.qualification.closed, 'PREPARED768_SAME_CLOSED_LIFECYCLE')
        return True

    def begin(self, index):
        require(self.current is None and index == len(self.rows)+1, 'PREPARED768_NO_CASE_RETRY')
        self.guard.advance('case'+str(index), lambda: self.between(index))
        self.current = base.Boundary(self.guard, self.manifest, self.paths, 'case'+str(index), self.shell_expected, current004=True)


class Handler(base.BatchHandler):
    def __init__(self, host, cases):
        super().__init__(host)
        self.cases = cases

    def handle(self, line):
        reply = super().handle(line)
        request, response = json.loads(line), json.loads(reply)
        if request.get('operation') == 'finish' and request.get('case_index') == 8 and request.get('case_status') == 'returned' and response.get('acknowledged') is True:
            self.host.guard.advance('batch_close', lambda: self.cases.between(9))
        return reply


def artifacts(guard, host):
    require(host.protocol.protocol.case_index == 9 and not host.protocol.protocol.stopped
            and len(host.scope.sessions) == 16, 'PREPARED768_TWO_CASES_FOUR_CLOSED_SESSIONS')
    return evidence.current_artifacts(guard, host, directory)


def execute(guard, manifest, paths, shell_expected, env, notify, record):
    absent()
    before = base.installed.current_identity(guard.windows)
    q = base.Boundary(guard, manifest, paths, 'prepared768_current_session', shell_expected, current004=True)
    worker = base.candidate.SessionWorker(guard)
    qualifier = base.session.SessionQualifier(guard, worker, q.native_pin, q.shell_pin)
    attempt = {}
    record['qualification_worker'] = attempt
    result = io.run(guard, worker, q.source, worker.start_session_worker, base.SessionHandler(qualifier),
                    'hwpx-agent.private.crossref-session-worker-result/v1', env, lambda v: notify('qualification', v), attempt)
    require(attempt['exit_code'] == 0, 'PREPARED768_CURRENT_SESSION_FAILED_NO_BATCH')
    q.finish()
    record['qualification_boundary'] = q.summary()
    handoff = base.batch.issue_handoff(guard, qualifier, result, q.closed, before, base.installed.current_identity(guard.windows), q.fingerprint)
    absent()
    current = base.Boundary(guard, manifest, paths, 'prepared768_eight', shell_expected, current004=True)
    cases = Cases(guard, manifest, shell_expected, paths)
    full = Worker(guard)
    host = Host(guard, full, handoff, base.installed.current_identity(guard.windows), q.fingerprint,
                cases.native_pin, current.shell_pin, cases.begin, cases.end)
    host.drain_notify = lambda value: notify('prepared_eight', value)
    host.drain_records = drain.SessionRecords(8)
    cases.host, cases.handoff, cases.qualification = host, handoff, q
    attempt = {}
    record['capture_worker'] = attempt
    try:
        result = io.run(guard, full, current.source, full.start_fixed_worker, Handler(host, cases),
                        'hwpx-agent.private.crossref-fixed-worker-result/v1', env, lambda v: notify('prepared_eight', v), attempt)
        require(attempt['exit_code'] == 0 and result['state'] == 'block_eight_callbacks_returned_semantics_unqualified'
                and result['completed_callback_cases'] == 8 and result['SDK_insertion_invoked'] is False
                and result['retained_live_or_uncertain_owners'] == 0 and len(cases.rows) == 8 and cases.current is None,
                'PREPARED768_WHOLE_CAPTURE_AND_CASE_CLOSURE')
        current.finish()
        require(base.installed.current_identity(guard.windows) == before, 'PREPARED768_SAME_LIVE_CREATOR')
        record['artifacts'] = artifacts(guard, host)
        require(attempt['cleanup'] is True and full.closed and host.scope.closed and host.worker_lease.closed,
                'PREPARED768_ALL_OWNER_WORKER_IO_CLEANUP')
        record['batch_closed_for_final_audit'] = True
    finally:
        record.update(capture_boundary=current.summary(), case_source_boundaries=cases.rows,
                      partial_case_source_boundary=None if cases.current is None else cases.current.summary(),
                      same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']
