"""Bind partial630 closed captures; never rewrite630 or qualify field/render semantics."""
import re
from pathlib import Path
import prepared_bookmark_native630 as old

r = old.r
FAILED = 'implementation/p09/evidence/p09-361-prepared-bookmark630-native001.v1.json'
FAILED_SHA = 'c50e6898cda51fa711f3bc0d82829200da68754cf211f382e8552dd122560a78'
CODE = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code006.v1.json'
CODE_SHA = '8284f00e45a52e49633398581029ba7f873a2fc6355dbc4aa5b2d06aa30654e3'


def require(ok, code):
    if not ok:
        raise ValueError('XREF_PREPARED631_EVIDENCE_'+code)


def producer(trace, profiles):
    require(len(profiles) == len(trace['sessions']) == len(trace['dual_identity_evidence']) == 2,
            'TWO_INDEPENDENT_CLOSED_SESSIONS')
    for offset, (native, session, admission) in enumerate(zip(profiles, trace['sessions'], trace['dual_identity_evidence'])):
        profile = native['startup_profile']
        observed = admission['observation']
        require(session['label'] == ('save' if offset == 0 else 'reopen')
                and session['quit_invoked'] is True and session['close_without_dirty_prompt_returned'] is True
                and type(session['remaining_owned_process_count']) is int and session['remaining_owned_process_count'] == 0
                and session['cleanup_error'] is None and admission['channel_message_returned'] is True
                and observed['compatibility_identity'] == session['process']
                and observed['kernel_identity']['process_id'] == profile['process_id']
                and observed['kernel_creation_filetime_100ns'] == str(profile['process_birth_100ns'])
                and profile['cleanup_confirmed'] is True and profile['owner_bound'] is True
                and profile['assigned_before_initial_thread'] is True, 'EXACT_KERNEL_PRODUCER_CLEANUP')


def captured(reader, folder, index, profiles, *, retained=False):
    trace = reader.json(folder+'/case-trace.json')
    version = '630' if retained else '631'
    require(trace['schema_version'] == 'hwpx-agent.private.prepared-bookmark'+version+'-trace/v1'
            and type(trace['case_index']) is int and trace['case_index'] == index
            and trace['state'] == 'capture_returned_semantics_unqualified'
            and trace['error_code'] is None and trace['cleanup_error'] is None
            and trace['source_identity_preserved'] is True and trace['input_leases_closed'] is True
            and trace['SDK_insertion_invoked'] is False, 'CLOSED_CAPTURE_NOT_ACCEPTANCE')
    producer(trace, profiles)
    names = {'initial.hwpx', 'saved.hwpx', 'reopened.hwpx'}
    if retained:
        names |= {'initial.pdf', 'reopened.pdf'}
    else:
        require(type(trace['source_case_index']) is int and trace['source_case_index'] == index+2,
                'ORDINAL_TO_SOURCE_CASE_MAPPING')
        for label in ('initial', 'reopened'):
            images = {name: value for name, value in trace['artifacts'].items() if name.startswith(label+'-page-')}
            require(1 <= len(images) <= 8, 'ALL_RENDERED_PAGES_BOUND')
            expected = {label+f'-page-{i+1:03}.bmp' for i in range(len(images))}
            require(set(images) == expected, 'EXACT_IMAGE_FILENAMES')
            for i in range(len(images)):
                artifact = images[label+f'-page-{i+1:03}.bmp']
                require(type(artifact['page_number']) is int and artifact['page_number'] == i
                        and type(artifact['page_count']) is int and artifact['page_count'] == len(images)
                        and artifact['bitmap']['format'] == 'BMP' and artifact['bitmap']['depth'] == 24
                        and artifact['bitmap']['resolution'] == 96
                        and artifact['bitmap']['visual_semantics_qualified'] is False,
                        'EXACT_PAGE_CAPTURE_METADATA')
            names |= expected
    require(set(trace['artifacts']) == names, 'EXACT_CAPTURE_ARTIFACT_SET')
    pins = {name: reader.pin(folder+'/'+name) for name in sorted(names | {'case-trace.json'})}
    for name, artifact in trace['artifacts'].items():
        require(artifact['pin']['bytes'] == pins[name]['bytes'] and artifact['pin']['sha256'] == pins[name]['sha256']
                and artifact['owner'] == trace['sessions'][0 if name.startswith('initial') or name == 'saved.hwpx' else 1]['process']
                and artifact['effect_semantics_qualified'] is False, 'IMMUTABLE_ARTIFACT_AND_PRODUCER')
    return dict(source_case_index=index if retained else index+2, artifacts=pins,
                native_capture_bound=True, reference_semantics_qualified=False, render_semantics_qualified=False)


def retained(reader, unpack):
    code = unpack(reader.json(CODE))
    require(reader.snapshots[CODE]['sha256'] == CODE_SHA and code['cleanup'] is True
            and code['state'] == 'PASS630_PREPARED_NATIVE_CAPTURE_CODE_AND_ACTUAL_READY_DENIAL_NOT_NATIVE_OR_GATE',
            'UNCHANGED_OLD_CODE_QUALIFICATION')
    codepins = {p['path']: p for p in code['source_pins']}
    # Bundle start/final only. None of these historical inputs is carried into
    # every new tail case merely for being part of an old receipt.
    for path, pin in codepins.items():
        require(reader.pin(path) == pin, 'RETAINED_CODE_CHANGED')
    value = unpack(reader.json(FAILED))
    require(reader.snapshots[FAILED]['sha256'] == FAILED_SHA
            and value['state'] == 'FAILED630_PREPARED_NATIVE_CAPTURE' and value['cleanup'] is False
            and value['fixed_eight_executed'] is False, 'FAILURE_REMAINS_FAILURE')
    summary = value['capture_worker']['handler_summary']['protocol']
    scope, protocol = summary['scope'], summary['protocol']
    require(protocol['completed_callback_cases'] == [dict(case_index=i, case_status='returned') for i in (1, 2)]
            and len(value['case_source_boundaries']) == 2 and len(scope['retired_sessions']) == 4,
            'ONLY_TWO_CLOSED_CASES')
    roots = dict(source=r.c.ROOT,
                 native=Path(old.base.installed.native.EXECUTABLE).parent,
                 shell=Path(old.base.candidate.original.SHELL).parent,
                 runtime=old.prepared.inspection.fixed.PYTHON.parent)
    external = {k: r.a.AcceptanceReader(v, reader.checkpoint) for k, v in roots.items() if k != 'source'}
    rows = []
    for i, boundary in enumerate(value['case_source_boundaries'], 1):
        require(old.sections.closed_boundary(boundary), 'OLD_CASE_FULL_FRESH_CLOSURE')
        for label, detail in boundary['readers'].items():
            q = reader if label == 'source' else external[label]
            for pin in detail['pins']:
                require(q.pin(pin['path']) == pin, 'OLD_CASE_INPUT_CHANGED')
        profiles = scope['retired_sessions'][(i-1)*2:i*2]
        require(all(p['case_index'] == i for p in profiles), 'OLD_CASE_SESSION_MAPPING')
        rows.append(captured(reader, old.directory(i), i, profiles, retained=True))
    for q in external.values():
        q.finish()
    return dict(cases=rows, original_failed_receipt=reader.snapshots[FAILED],
                failed630_cleanup_reclassified=False, failed630_replayed=False,
                external_current_images_freshly_closed=True, field_or_render_acceptance=False)


def current_artifacts(guard, host, directory):
    reader = r.a.AcceptanceReader(r.c.ROOT, guard.check)
    rows = [captured(reader, directory(i), i, host.scope.sessions[(i-1)*2:i*2]) for i in range(1, 7)]
    reader.finish()
    return dict(cases=rows, fresh_inputs=len(reader.snapshots), final_fresh_hashes=reader.final_fresh_hashes,
                field_readback_semantics_qualified=False, render_diff_qualified=False, P09_complete=False)
