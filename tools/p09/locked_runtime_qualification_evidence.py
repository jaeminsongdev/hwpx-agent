"""P207: 실제 전체 잠금 결과의 범위·byte·수명 검증. 제품/Gate 수용은 아니다."""
import io
import sys
import unittest
from unittest.mock import patch
import locked_runtime_inputs as locks

SELF='tools/p09/locked_runtime_qualification_evidence.py'
TEST='tools/p09/tests/test_locked_runtime_qualification_evidence.py'
PASS='PASS_FULL_RUNTIME_AND_KNOWN_FIXTURE_READ_LOCKS_NOT_SHARED_FRAME_PRODUCT_OR_GATE'


def require(ok,code):locks.require(ok,'EVIDENCE_'+code)


def pins(rows):
    require(isinstance(rows,list) and 0<len(rows)<=locks.MAX_INPUTS,'PIN_LIST_BOUND')
    require(all(isinstance(row,dict) and isinstance(row.get('path'),str) for row in rows),'PIN_ROWS')
    by_path={row['path']:row for row in rows}
    require(len(by_path)==len(rows),'NO_DUPLICATE_INPUT_PATHS')
    return locks.input_pins(by_path)


def validate(doc,required,binding,helpers,runtime_count,fixture_count):
    required=locks.input_pins(required);files=len(required);directories={locks.ROOT}
    for name in required:
        parent=(locks.ROOT/name).parent
        while parent not in directories:directories.add(parent);parent=parent.parent
    directory_count=len(directories);held=files+directory_count
    require(doc['schema_version']=='hwpx-agent.p09-locked-runtime-input-qualification/v1'
        and doc['state']==PASS and doc['qualification_scope']=='full-runtime'
        and doc['input_lock_contract_tests_passed']==43 and doc['binding']==binding,'FULL_QUALIFICATION_BINDING')
    require(pins(doc['qualified_input_pins'])==required and doc['qualified_inputs']==files
        and doc['qualified_input_bytes']==sum(p['bytes'] for p in required.values())
        and doc['prior_runtime_inputs']==runtime_count and doc['known_fixture_input_count']==fixture_count
        and doc['all_prior_runtime_inputs_retained'] is True
        and pins(doc['qualification_helper_pins'])==helpers,'EVERY_DECLARED_INPUT_EXACT')
    require(doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['goal_status']=='active' and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and doc['new_input_exclusions']==[] and all(doc[k] is False for k in (
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved',
            'whole1470_current_fresh_qualified','historical67_current_fresh_qualified','actual_product_child_executed',
            'actual_product_test_body_or_shared_frame_executed','existing_actual_runner_input_scope_changed',
            'content_or_attributes_written_or_deleted','verification_IO_reduction_already_applied')),'NO_PRODUCT_GATE_OR_REDUCTION')
    require(doc['actual_file_and_ancestor_handles_noninheritable'] is True
        and doc['file_and_path_identities_checked_before_and_after_fresh_reads'] is True,'ACTUAL_IDENTITY_BOUNDARY')
    before=doc['locked_identity_before'];after=doc['locked_identity_after'];stream=doc['byte_stream_identity_passes']
    require(all(row['held_identity_checks_complete'] is True and row['regular_file_count']==files
        and row['directory_count']==directory_count for row in (before,after))
        and before['path_identities_confirmed_on_acquisition'] is True and after['separate_pathname_reopens']==0
        and stream==dict(verified_byte_streams=2*files,locked_inputs=files,
            each_input_hashed_twice_with_same_open_stream_identity=True,separate_pathname_reopens=0),'TWO_FULL_STREAM_IDENTITY_PASSES')
    own=doc['input_locks']
    require(own['input_lock_handles_opened']==own['input_lock_handles_closed']==held
        and own['input_lock_handles_remaining']==own['probe_handles_remaining']==0
        and own['probe_handles_opened']==own['probe_handles_closed']==3
        and own['input_lock_cleanup_confirmed'] is True
        and own['handle_close_failed_attempts']==own['probe_handle_close_failed_attempts']==0
        and own['active_reader_bindings']==own['active_byte_streams']==0
        and own['release_started'] is True and own['ancestor_walk_steps']==directory_count-1
        and own['maximum_lock_seconds']==600 and own['byte_stream_identity_checks']==2*files
        and own['handle_metadata_checks']==2*held+2*files and own['separate_pathname_reopens']==0
        and all(own[k] is False for k in ('file_write_or_delete_operation_executed','input_scope_reduced',
            'kernel_or_malicious_bypass_protection_claimed')),'ALL_HELD_PROBE_AND_STREAM_LIFETIMES_CLOSED')
    pacing=own['native_open_pacing'];budget=locks.open_budget(files,directory_count)
    require(pacing['maximum_opens_per_second']==32 and pacing['idle_time_cannot_accumulate_multiple_open_credits'] is True
        and pacing['open_reservations']==budget['optimized_source_scope_open_requests']+6,'SHARED_OPEN_PACING_ACCOUNTING')
    io_row=doc['IO'];bound=pins(doc['bound_input_pins'])
    require(io_row['finished'] is True and io_row['bound_inputs']==io_row['final_fresh_hashes']==len(bound)
        and all(bound.get(name)==pin for name,pin in required.items())
        and io_row['read_passes']>=2*files and io_row['bytes_read']>=2*sum(p['bytes'] for p in required.values())
        and io_row['bytes_read']==io_row['pacer_bytes_read']==sum(io_row['bytes_read_by_kind'].values())
        and io_row['bytes_read_by_kind']['binary']==2*sum(p['bytes'] for n,p in required.items() if n.lower().endswith('.exe'))
        and io_row['maximum_scope_seconds']==600 and io_row['chunk_bytes']==io_row['burst_bytes']==65536
        and io_row['parse_budget_bytes']==16777216 and io_row['all_original_read_operations_preserved'] is True
        and io_row['read_rates_by_kind']==dict(binary=1048576,other=2097152),'ALL_FINAL_BYTE_PINS_FRESH')
    pressure=io_row['near_saturation_read_backpressure']
    require(pressure['warning_system_CPU_percent']==95 and pressure['cool_distinct_sample_windows']==2
        and pressure['maximum_pause_windows_per_entry']==8
        and all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified',
            'original_IO_deadline_unmodified','original_sampler_windows_reused'))
        and pressure['new_native_query_or_sampler_thread_started'] is False
        and pressure['original_read_checks_skipped'] is False,'ORIGINAL_PRESSURE_GUARDS_RETAINED')
    during=doc['access_during_held_locks'];released=doc['access_after_release']
    require(during==dict(read=dict(opened=True,win32_error=0),write=dict(opened=False,win32_error=32),
            delete=dict(opened=False,win32_error=32))
        and released==dict(write=dict(opened=True,win32_error=0),delete=dict(opened=True,win32_error=0))
        and doc['probe_access_open_only_no_write_truncate_delete_or_rename'] is True
        and doc['sharing_probe_file_pin']==required[doc['sharing_probe_file_pin']['path']]
        and doc['own_probe_after_release_read_bytes']==doc['sharing_probe_file_pin']['bytes'],'ACCESS_PROBE_NO_MUTATION')
    return dict(qualified_input_count=files,qualified_input_bytes=sum(p['bytes'] for p in required.values()),
        directory_count=directory_count,actual_byte_stream_checks=2*files,actual_scope_open_reservations=pacing['open_reservations'],
        shared_runtime_frame_or_product_acceptance=False)


def contracts():
    sys.path.insert(0,str(locks.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_locked_runtime_qualification_evidence')
    with patch('subprocess.Popen',side_effect=AssertionError('P207_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P207_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P207_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==8 and not checked.skipped,'CONTRACT8')
    return 8
