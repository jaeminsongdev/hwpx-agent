"""Prepared-file Native capture composition, never SDK insertion or acceptance.

Public steps describe actual prepared-file IO. The unchanged legacy16 schedule
is only an INTERNAL resource/owner state machine. In particular its sdk_insert
slot schedules a PDF export; it never attests to or invokes an insertion.
No new Native/startup/cleanup policy is implemented here.
"""
import json
import sys
from pathlib import Path

import bookmark_native_preparation629 as prepared
import crossref_external_batch_runtime as base
import crossref_fixed_worker as worker_base
import crossref_native_worker_io603 as io
import crossref_section010_policy as sections

r = base.r
require = base.require
SELF = 'tools/p09/prepared_bookmark_native630.py'
ENTRY = 'tools/p09/run_prepared_bookmark_native630.py'
TARGET = 'implementation/p09/tools/run-prepared-bookmark630-worker.ps1'
PORTS = 'implementation/p09/tools/prepared-bookmark630-ports.ps1'
CHANNEL = 'implementation/p09/tools/prepared-bookmark630-channel.ps1'
PREFIX = 'implementation/p09/evidence/private/p09-361-prepared-bookmark630-native001-c'
REQUEST = 'hwpx-agent.private.prepared-bookmark630-request/v1'
RESPONSE = 'hwpx-agent.private.prepared-bookmark630-response/v1'
STEPS = ('prepare_slot', 'create_save_session', 'candidate_open', 'candidate_bind',
         'initial_identity', 'initial_snapshot', 'initial_pdf', 'saved_save', 'saved_bind',
         'save_session_close', 'create_reopen_session', 'fresh_saved_open',
         'reopened_save', 'reopened_pdf', 'reopen_session_close', 'final_source_check')
LEGACY = dict(zip(STEPS, base.batch.original.original.STEPS))
SOURCES = set(base.candidate.SOURCES) | {TARGET, PORTS, CHANNEL,
    'implementation/p09/tools/crossref-save-reopen.ps1',
    'implementation/p09/tools/crossref-capture008-application-binding.ps1'}


def directory(index):
    require(type(index) is int and 1 <= index <= 8, 'PREPARED630_EXACT_CASE')
    return PREFIX + f'{index:02}'


def absent():
    for i in range(1, 9):
        prepared.require_absent(r.c.ROOT, directory(i))


def translate_request(raw):
    require(type(raw) is str and 0 < len(raw.encode()) <= 4096 and '\n' not in raw and '\r' not in raw,
            'PREPARED630_WIRE_BOUND')
    value = json.loads(raw, object_pairs_hook=base.batch.original.original.unique_pairs)
    require(type(value) is dict and value.get('schema_version') == REQUEST, 'PREPARED630_DISTINCT_PURPOSE_SCHEMA')
    result = dict(value, schema_version=base.batch.original.REQUEST)
    if value.get('operation') == 'checkpoint':
        require(type(value.get('step')) is str and value['step'] in LEGACY, 'PREPARED630_EXACT_STEP')
        result['step'] = LEGACY[value['step']]
    # Original exact keys/types/owner/sequence limits are not relaxed.
    base.batch.original.decode_request(json.dumps(result, separators=(',', ':')))
    return value, result


class Host(base.batch.FixedEightHost):
    def respond(self, raw):
        try:
            _, internal = translate_request(raw)
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            self.protocol.protocol.stopped = True
            self.scope.stopped = True
            raise
        result = json.loads(super().respond(json.dumps(internal, separators=(',', ':'))))
        result['schema_version'] = RESPONSE
        return json.dumps(result, separators=(',', ':'))

    def summary(self):
        return dict(super().summary(), purpose='prepared_candidate_open_save_reopen_pdf_only',
                    legacy_schedule_is_resource_bookkeeping_only=True, SDK_insertion_invoked=False,
                    reference_semantics_qualified=False)


class Worker(worker_base.FixedWorker):
    def _fixed_command(self, reader):
        require(reader.root.resolve() == r.c.ROOT.resolve(), 'PREPARED630_FIXED_ROOT')
        for path in sorted(SOURCES):
            reader.pin(path)
        require(reader.snapshots[base.candidate.original.BOOTSTRAP]['sha256'] == base.candidate.original.BOOTSTRAP_SHA,
                'PREPARED630_ORIGINAL_BOOTSTRAP')
        args = [base.candidate.original.SHELL, '-NoLogo', '-NoProfile', '-NonInteractive', '-STA',
                '-File', str(r.c.ROOT / TARGET), '-PreparedEightAfterCurrentSession']
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
                'PREPARED630_CLOSED_PREVIOUS_CASE_AND_OWNERS')
        require(all(v['startup_profile']['cleanup_confirmed'] is True for v in s.sessions)
                and self.handoff.consumed and self.qualification.closed, 'PREPARED630_SAME_CLOSED_LIFECYCLE')
        return True

    def begin(self, index):
        require(self.current is None and index == len(self.rows)+1, 'PREPARED630_NO_CASE_RETRY')
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
            and len(host.scope.sessions) == 16, 'PREPARED630_ALL_EIGHT_AND_SIXTEEN_CLOSED_SESSIONS')
    reader = r.a.AcceptanceReader(r.c.ROOT, guard.check)
    rows = []
    for index in range(1, 9):
        folder = directory(index)
        pins = {name: reader.pin(folder+'/'+name) for name in ('initial.hwpx', 'initial.pdf', 'saved.hwpx', 'reopened.hwpx', 'reopened.pdf', 'case-trace.json')}
        trace = reader.json(folder+'/case-trace.json')
        require(trace['schema_version'] == 'hwpx-agent.private.prepared-bookmark630-trace/v1'
                and type(trace['case_index']) is int and trace['case_index'] == index
                and trace['state'] == 'capture_returned_semantics_unqualified'
                and trace['SDK_insertion_invoked'] is False and trace['source_identity_preserved'] is True
                and trace['input_leases_closed'] is True and trace['cleanup_error'] is None
                and len(trace['sessions']) == len(trace['dual_identity_evidence']) == 2,
                'PREPARED630_EXACT_NEW_CAPTURE_TRACE')
        for offset, (native, session, admission) in enumerate(zip(host.scope.sessions[(index-1)*2:index*2], trace['sessions'], trace['dual_identity_evidence'])):
            profile = native['startup_profile']
            observed = admission['observation']
            require(session['label'] == ('save' if offset == 0 else 'reopen')
                    and session['quit_invoked'] is True and session['close_without_dirty_prompt_returned'] is True
                    and session['remaining_owned_process_count'] == 0 and session['cleanup_error'] is None
                    and admission['channel_message_returned'] is True
                    and observed['compatibility_identity'] == session['process']
                    and observed['kernel_identity']['process_id'] == profile['process_id']
                    and observed['kernel_creation_filetime_100ns'] == str(profile['process_birth_100ns'])
                    and profile['cleanup_confirmed'] is True and profile['owner_bound'] is True
                    and profile['assigned_before_initial_thread'] is True, 'PREPARED630_KERNEL_PRODUCER_AND_EXACT_CLEANUP')
        require(set(trace['artifacts']) == set(pins)-{'case-trace.json'}, 'PREPARED630_ALL_CAPTURE_ARTIFACTS')
        for name, artifact in trace['artifacts'].items():
            require(artifact['pin']['sha256'] == pins[name]['sha256'] and artifact['pin']['bytes'] == pins[name]['bytes']
                    and artifact['owner'] == trace['sessions'][0 if name in ('initial.hwpx', 'initial.pdf', 'saved.hwpx') else 1]['process'],
                    'PREPARED630_EXACT_ARTIFACT_PRODUCER')
        rows.append(dict(case_index=index, artifacts=pins, native_capture_bound=True, reference_semantics_qualified=False))
    reader.finish()
    return dict(cases=rows, fresh_inputs=len(reader.snapshots), final_fresh_hashes=reader.final_fresh_hashes,
                field_readback_semantics_qualified=False, PDF_render_diff_qualified=False, P09_complete=False)


def execute(guard, manifest, paths, shell_expected, env, notify, record):
    absent()
    before = base.installed.current_identity(guard.windows)
    q = base.Boundary(guard, manifest, paths, 'prepared630_current_session', shell_expected, current004=True)
    worker = base.candidate.SessionWorker(guard)
    qualifier = base.session.SessionQualifier(guard, worker, q.native_pin, q.shell_pin)
    attempt = {}
    record['qualification_worker'] = attempt
    result = io.run(guard, worker, q.source, worker.start_session_worker, base.SessionHandler(qualifier),
                    'hwpx-agent.private.crossref-session-worker-result/v1', env, lambda v: notify('qualification', v), attempt)
    require(attempt['exit_code'] == 0, 'PREPARED630_CURRENT_SESSION_FAILED_NO_BATCH')
    q.finish()
    record['qualification_boundary'] = q.summary()
    handoff = base.batch.issue_handoff(guard, qualifier, result, q.closed, before, base.installed.current_identity(guard.windows), q.fingerprint)
    absent()
    current = base.Boundary(guard, manifest, paths, 'prepared630_eight', shell_expected, current004=True)
    cases = Cases(guard, manifest, shell_expected, paths)
    full = Worker(guard)
    host = Host(guard, full, handoff, base.installed.current_identity(guard.windows), q.fingerprint,
                cases.native_pin, current.shell_pin, cases.begin, cases.end)
    cases.host, cases.handoff, cases.qualification = host, handoff, q
    attempt = {}
    record['capture_worker'] = attempt
    try:
        result = io.run(guard, full, current.source, full.start_fixed_worker, Handler(host, cases),
                        'hwpx-agent.private.crossref-fixed-worker-result/v1', env, lambda v: notify('prepared_eight', v), attempt)
        require(attempt['exit_code'] == 0 and result['state'] == 'fixed_eight_callbacks_returned_semantics_unqualified'
                and result['completed_callback_cases'] == 8 and result['SDK_insertion_invoked'] is False
                and result['retained_live_or_uncertain_owners'] == 0 and len(cases.rows) == 8 and cases.current is None,
                'PREPARED630_WHOLE_CAPTURE_AND_CASE_CLOSURE')
        current.finish()
        require(base.installed.current_identity(guard.windows) == before, 'PREPARED630_SAME_LIVE_CREATOR')
        record['artifacts'] = artifacts(guard, host)
        require(attempt['cleanup'] is True and full.closed and host.scope.closed and host.worker_lease.closed,
                'PREPARED630_ALL_OWNER_WORKER_IO_CLEANUP')
        record['batch_closed_for_final_audit'] = True
    finally:
        record.update(capture_boundary=current.summary(), case_source_boundaries=cases.rows,
                      partial_case_source_boundary=None if cases.current is None else cases.current.summary(),
                      same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']
