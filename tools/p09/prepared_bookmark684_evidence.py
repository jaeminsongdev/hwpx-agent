"""Eight fresh block candidates: exact producer/file binding, no semantic acceptance."""
import re
from pathlib import Path
import named_style_verification_runtime as r


def require(ok, code):
    if not ok:
        raise ValueError('XREF_PREPARED684_EVIDENCE_'+code)


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


def captured(reader, folder, index, profiles):
    trace = reader.json(folder+'/case-trace.json')
    version = '684'
    require(trace['schema_version'] == 'hwpx-agent.private.prepared-bookmark'+version+'-trace/v1'
            and type(trace['case_index']) is int and trace['case_index'] == index
            and trace['state'] == 'capture_returned_semantics_unqualified'
            and trace['error_code'] is None and trace['cleanup_error'] is None
            and trace['source_identity_preserved'] is True and trace['input_leases_closed'] is True
            and trace['SDK_insertion_invoked'] is False, 'CLOSED_CAPTURE_NOT_ACCEPTANCE')
    producer(trace, profiles)
    names = {'initial.hwpx', 'saved.hwpx', 'reopened.hwpx'}
    if True:
        require(type(trace['source_case_index']) is int and trace['source_case_index'] == index,
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
    return dict(source_case_index=index, artifacts=pins,
                native_capture_bound=True, reference_semantics_qualified=False, render_semantics_qualified=False)


def current_artifacts(guard, host, directory):
    reader = r.a.AcceptanceReader(r.c.ROOT, guard.check)
    rows = [captured(reader, directory(i), i, host.scope.sessions[(i-1)*2:i*2]) for i in range(1, 9)]
    reader.finish()
    return dict(cases=rows, fresh_inputs=len(reader.snapshots), final_fresh_hashes=reader.final_fresh_hashes,
                field_readback_semantics_qualified=False, render_diff_qualified=False, P09_complete=False)
