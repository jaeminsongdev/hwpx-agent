"""Exact frozen P55 trace/child/artifact binding. No sessions, writes or UI."""
from datetime import datetime, timedelta
import json
import re
import zipfile
from tools.p09 import verify_click_here_owned_lifecycle as frozen

p, ROOT = frozen.p, frozen.ROOT
require, sha, canonical = p.require, p.sha, p.canonical
P55_SHA = 'cb0a921596d1427d921063c8f0cd5bcc339749c5ff085e90d9a5a94810ce4b3b'
COMPLETE = 'owned_lifecycle_checks_completed_not_package_or_render_acceptance'
TARGET = {'build':'11.0.0.9136','architecture':'x86','prog_id':'HWPFrame.HwpObject.2',
    'executable_sha256':'7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce'}
TRACE_KEYS = set(('schema_version case_id worker_plan_case_id state started_at_utc target source_sha256 plan_sha256 '
    'harness_sha256 lifecycle_library_sha256 p54_worker_sha256 p50_copy_library_sha256 security_module_sha256 '
    'sessions artifacts checks failed_phase error_code binding_failure remaining_hwp_process_count completed_at_utc '
    'raw_document_values_present computer_use_click_or_type_invoked registry_or_system_setting_changed '
    'external_network_invoked saved_package_render_differential_or_product_qualified p09_complete').split())
FALSE_FIELDS = ('raw_document_values_present','computer_use_click_or_type_invoked','registry_or_system_setting_changed',
    'external_network_invoked','saved_package_render_differential_or_product_qualified','p09_complete')
SESSION_KEYS = set(('label version register_module_return process close_without_dirty_prompt_returned quit_invoked '
    'remaining_owned_process_count cleanup_error').split())
PROCESS_KEYS = {'process_id','session_id','created_at_utc','executable_sha256','window_handle_binds_exact_process'}
OUTPUTS = {'saved.hwpx':4194304,'saved.pdf':33554432,'reopened.hwpx':4194304,'reopened.pdf':33554432}
CHECKS = ('first_application','after_application','after_first_save','fresh_reopen','after_reopened_save')
APPLICATION = {'state':'runtime_text_and_complete_selected_style_check_not_saved_package_acceptance',
    'source_and_result_text_sha256_checked':True,'entire_selected_parameter_set_equivalent':True,
    'source_style_rgb_italic_bold_height_and_seven_fonts_checked':True,'selection_is_exact_unique_named_field':True,
    'native_ids_are_source_observations_not_runtime_binding':True,'raw_document_values_present':False,
    'native_save_reopen_render_or_differential_qualified':False,'p09_complete':False}
VERIFICATION = {'state':'runtime_result_matches_entire_original_selected_style','text_sha256_checked':True,
    'complete_selected_parameter_set_equivalent':True,'source_style_and_seven_fonts_checked':True,
    'document_style_or_text_write_invoked':False,'saved_package_or_render_or_native_rollback_qualified':False,
    'raw_document_values_present':False,'p09_complete':False}
PHASES = ('first_session_create','first_source_open','first_complete_original_style_capture',
    'native_text_and_complete_style_application','first_save','after_first_save_check','first_pdf',
    'fresh_session_create','fresh_original_source_open','fresh_complete_original_style_capture','fresh_saved_open',
    'fresh_read_only_entire_style_check','fresh_reopened_save','after_reopened_save_check','fresh_pdf')
INNER_PHASES = ('source_inventory','complete_source_style_clone','native_text_replacement','complete_source_style_application')
ROLLBACK = ('not_needed','attempted_text_style_restore_not_original_empty_field_or_package_proof',
    'text_style_restored_original_empty_field_dirty_state_and_package_unverified',
    'failed_preserve_trace_and_close_owned_session_without_save')
CLEANUP_ERRORS = ('P55_OWNER_UNVERIFIED_NO_BLANKET_QUIT','P55_OWNED_CLOSE_FAILED_NO_IMPLICIT_SAVE_OR_FORCE_KILL')


def integer(value, minimum=0, maximum=2147483647):
    return type(value) is int and minimum <= value <= maximum


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def utc(value):
    require(type(value) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{1,7}Z',value), 'p56_trace_timestamp')
    return datetime.fromisoformat(value.replace('Z','+00:00'))


def exact_dict(actual, expected, code):
    require(type(actual) is dict and actual.keys() == expected.keys() and
        all(type(actual[k]) is type(v) and canonical(actual[k]) == canonical(v) for k,v in expected.items()),code)


def predecessor():
    raw = p.m.prior.candidate.bounded(ROOT/frozen.CAPSULE)
    require(sha(raw) == P55_SHA,'p56_p55_receipt_identity')
    record = json.loads(raw,object_pairs_hook=p.m.prior.candidate.prior.io.duplicate_guard)
    require(record['source_sha256'] == frozen.pins() and record['preservation'] == p.preserved()
        and record['private_source_plan_bundle_inventory'] == p.inspect_bundle(),'p56_p55_source_or_input_drift')
    return record


def bind_trace(trace, row, code, *, source_pins=None):
    require(type(row) is dict and row in p.original_inputs()[0],'p56_exact_field_case')
    pins = predecessor()['source_sha256'] if source_pins is None else source_pins
    require(type(trace) is dict and trace.keys() == TRACE_KEYS,'p56_trace_schema')
    expected = {'schema_version':'hwpx-agent.p09-55-click-format-owned-target-trace/v1',
        'case_id':row['case_id'],'worker_plan_case_id':row['worker_plan_case_id'],'source_sha256':row['source_package_sha256'],
        'plan_sha256':row['plan_sha256'],'harness_sha256':pins[p.HARNESS],'lifecycle_library_sha256':pins[p.LIBRARY],
        'p54_worker_sha256':'6ccda3e4c42979e99be67f1033c4ff10866a97a822effee5c2ea1746e70cca89',
        'p50_copy_library_sha256':'c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183',
        'security_module_sha256':'9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6'}
    require(all(type(trace[k]) is type(v) and trace[k] == v for k,v in expected.items()),'p56_trace_identity')
    exact_dict(trace['target'],TARGET,'p56_trace_target')
    require(all(trace[k] is False for k in FALSE_FIELDS) and integer(trace['remaining_hwp_process_count'])
        and type(code) is int and code in (0,2),'p56_trace_claim_or_child_exit')
    start, end = utc(trace['started_at_utc']), utc(trace['completed_at_utc'])
    require(end >= start,'p56_trace_time_order')
    sessions = trace['sessions']
    require(type(sessions) is list and len(sessions) <= 2,'p56_trace_sessions')
    seen = set(); previous_birth = None; clean = True
    for index, session in enumerate(sessions):
        require(type(session) is dict and session.keys() == SESSION_KEYS and session['label'] == ('save','reopen')[index]
            and type(session['label']) is str and (session['version'] is None or session['version'] == TARGET['build'])
            and (session['register_module_return'] is None or type(session['register_module_return']) is bool)
            and type(session['close_without_dirty_prompt_returned']) is bool and type(session['quit_invoked']) is bool
            and (session['cleanup_error'] is None or session['cleanup_error'] in CLEANUP_ERRORS)
            and integer(session['remaining_owned_process_count'],-1),'p56_trace_session_scope')
        identity = session['process']
        if identity is None:
            require(session['version'] is None and session['register_module_return'] is None
                and session['remaining_owned_process_count'] == -1 and session['quit_invoked'] is False
                and session['close_without_dirty_prompt_returned'] is False and session['cleanup_error'] is not None,
                'p56_trace_unresolved_owner')
        else:
            require(type(identity) is dict and identity.keys() == PROCESS_KEYS and integer(identity['process_id'],1)
                and integer(identity['session_id']) and identity['executable_sha256'] == TARGET['executable_sha256']
                and identity['window_handle_binds_exact_process'] is True and identity['process_id'] not in seen,
                'p56_trace_owner_identity')
            birth = utc(identity['created_at_utc'])
            require(start-timedelta(seconds=2) <= birth <= end and (previous_birth is None or birth >= previous_birth),
                'p56_trace_owner_time')
            seen.add(identity['process_id']);previous_birth=birth
        clean = clean and identity is not None and session['version'] == TARGET['build'] and \
            type(session['register_module_return']) is bool and session['close_without_dirty_prompt_returned'] is True and \
            session['quit_invoked'] is True and session['remaining_owned_process_count'] == 0 and session['cleanup_error'] is None
    checks, artifacts = trace['checks'], trace['artifacts']
    require(type(checks) is dict and checks.keys() <= set(CHECKS) and type(artifacts) is dict
        and artifacts.keys() <= OUTPUTS.keys(),'p56_trace_check_artifact_inventory')
    require(set(checks) == set(CHECKS[:len(checks)]) and set(artifacts) == set(tuple(OUTPUTS)[:len(artifacts)]),
        'p56_trace_stage_gap')
    for index, name in enumerate(CHECKS):
        if name in checks:
            exact_dict(checks[name],APPLICATION if index == 0 else VERIFICATION,'p56_trace_style_check_scope')
            require(len(sessions) >= (2 if index >= 3 else 1),'p56_trace_check_session_order')
    requirements = {'saved.hwpx':'after_application','saved.pdf':'after_first_save',
        'reopened.hwpx':'fresh_reopen','reopened.pdf':'after_reopened_save'}
    for name, item in artifacts.items():
        require(type(item) is dict and item.keys() == {'sha256','bytes'} and digest(item['sha256'])
            and integer(item['bytes'],1,OUTPUTS[name]) and requirements[name] in checks,'p56_trace_artifact_claim')
    for check, prior_artifact in (('after_first_save','saved.hwpx'),('fresh_reopen','saved.pdf'),
        ('after_reopened_save','reopened.hwpx')):
        require(check not in checks or prior_artifact in artifacts,'p56_trace_check_before_artifact')
    completed = trace['state'] == COMPLETE
    require(type(trace['state']) is str and trace['state'] in ('effect_unknown',COMPLETE),'p56_trace_state')
    successful = completed and clean and len(sessions) == 2 and trace['remaining_hwp_process_count'] == 0
    if completed:
        require(len(checks) == 5 and len(artifacts) == 4 and len(sessions) == 2
            and trace['failed_phase'] is None and trace['error_code'] is None and trace['binding_failure'] is None,
            'p56_trace_completed_incomplete')
        require(code == (0 if successful else 2),'p56_trace_completed_exit_cleanup')
    else:
        require(code == 2 and trace['failed_phase'] in PHASES and type(trace['error_code']) is str
            and re.fullmatch(r'(P55|P09_CLICK_FORMAT)_[A-Z_]{1,128}',trace['error_code']),'p56_trace_failed_terminal')
        # Exact reachable prefixes of the frozen worker; no late results after an early failure.
        prefixes = {'first_session_create':((0,0),),'first_source_open':((0,0),),
            'first_complete_original_style_capture':((0,0),),'native_text_and_complete_style_application':((0,0),(1,0)),
            'first_save':((2,0),),'after_first_save_check':((2,1),),'first_pdf':((3,1),(3,2)),
            'fresh_session_create':((3,2),),'fresh_original_source_open':((3,2),),
            'fresh_complete_original_style_capture':((3,2),),'fresh_saved_open':((3,2),),
            'fresh_read_only_entire_style_check':((3,2),),'fresh_reopened_save':((4,2),),
            'after_reopened_save_check':((4,3),),'fresh_pdf':((5,3),(5,4))}
        require((len(checks),len(artifacts)) in prefixes[trace['failed_phase']],'p56_trace_failure_prefix')
        phase = PHASES.index(trace['failed_phase'])
        require(len(sessions) <= (1 if phase < PHASES.index('fresh_session_create') else 2)
            and (phase == 0 or len(sessions) >= (1 if phase <= PHASES.index('fresh_session_create') else 2)),
            'p56_trace_failure_session_order')
    failure = trace['binding_failure']
    if failure is not None:
        require(type(failure) is dict and failure.keys() == {'failed_phase','error_code','rollback_state','raw_document_values_present'}
            and failure['failed_phase'] in INNER_PHASES and failure['rollback_state'] in ROLLBACK
            and failure['raw_document_values_present'] is False and type(failure['error_code']) is str
            and re.fullmatch(r'P09_CLICK_FORMAT_[A-Z_]{1,128}',failure['error_code'])
            and trace['failed_phase'] == 'native_text_and_complete_style_application','p56_trace_rollback_scope')
    return {'case_id':row['case_id'],'harness_exit':code,'lifecycle':'pass' if successful else 'fail',
        'sessions':len(sessions),'complete_style_checks_passed':len(checks),
        'cleanup_safe_to_continue':trace['remaining_hwp_process_count'] == 0,
        'failed_phase':trace['failed_phase'] if not completed else (None if successful else 'owner_cleanup'),
        'error_code':trace['error_code'] if not completed else (None if successful else 'P56_OWNED_CLEANUP_UNVERIFIED'),
        'native_package_render_differential_or_product_qualified':False}


def bind_artifacts(trace, row, artifacts):
    require(type(artifacts) is dict and artifacts.keys() <= OUTPUTS.keys(),'p56_artifact_inventory')
    result = {}
    for name,bound in OUTPUTS.items():
        claimed = trace['artifacts'].get(name);raw=artifacts.get(name)
        require(claimed is None or raw is not None,'p56_claimed_artifact_missing')
        if raw is None:continue
        require(type(raw) is bytes and len(raw) <= bound,'p56_artifact_boundary')
        if claimed is not None:
            require(len(raw) == claimed['bytes'] and sha(raw) == claimed['sha256']
                and (not name.endswith('.pdf') or raw.startswith(b'%PDF-')),'p56_artifact_identity')
        else:
            require(trace['state'] != COMPLETE,'p56_unclaimed_completed_artifact')
        summary={'sha256':sha(raw),'bytes':len(raw),'lifecycle_claim_bound':claimed is not None,
            'partial_unqualified_preserved':claimed is None,'native_render_or_product_qualified':False}
        if name.endswith('.hwpx') and claimed is not None:
            try:summary['whole_sdk_package_comparison']=p.compare_saved_package(row['case_id'],raw)
            except (ValueError,zipfile.BadZipFile):
                summary['whole_sdk_package_comparison']={'state':'invalid_or_unsupported_package_rejected',
                    'whole_expanded_bytes_exact':False,'native_runtime_rollback_or_render_differential_qualified':False,
                    'p09_complete':False}
        result[name]=summary
    return result


def read_case(row, code, *, source_pins=None):
    require(row in p.original_inputs()[0],'p56_actual_case_scope')
    directory=ROOT/row['run_directory']
    p.m.prior.environment.q.shared.within(directory,ROOT/'implementation/p09/evidence/private')
    require({n.name for n in directory.iterdir()} <= OUTPUTS.keys()|{'target-trace.json'},'p56_actual_file_inventory')
    trace_raw=p.m.prior.candidate.bounded(directory/'target-trace.json',262144)
    trace=json.loads(trace_raw,object_pairs_hook=p.m.prior.candidate.prior.io.duplicate_guard)
    record=bind_trace(trace,row,code,source_pins=source_pins)
    raw={}
    for name, bound in OUTPUTS.items():
        path=directory/name
        if path.exists():
            # Zero-byte partial files are retained and hashed, never upgraded to claims.
            p.m.prior.environment.q.shared.within(path,ROOT/'implementation/p09/evidence/private')
            before=path.stat()
            require(path.is_file() and 0 <= before.st_size <= bound,'p56_actual_partial_file_boundary')
            with path.open('rb') as stream:content=stream.read(bound+1)
            after=path.stat()
            require(before.st_size == after.st_size == len(content) and before.st_mtime_ns == after.st_mtime_ns,
                'p56_actual_partial_file_changed')
            raw[name]=content
    record['artifacts']=bind_artifacts(trace,row,raw)
    files={row['run_directory']+'/target-trace.json':sha(trace_raw)}
    files.update({row['run_directory']+'/'+name:sha(content) for name,content in raw.items()})
    return record,files
