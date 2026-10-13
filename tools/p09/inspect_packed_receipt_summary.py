"""P222 원장은 원 보호 Reader로 읽고 허용된 요약만 출력한다. 본문 실행 없음."""
import argparse
import json
import re
import resume_packed_pressure_runtime as r


def fields(doc, names):
    return {key: doc[key] for key in names if key in doc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--path', required=True)
    args = ap.parse_args()
    r.require(r.p.c.Path.cwd().resolve() == r.p.c.ROOT, 'INSPECT_CWD')
    r.require(re.fullmatch(re.escape(r.p.DIR) +
        r'/p222-(?:packed-light-run[0-9]{3}|case-[0-9]{3}-run[0-9]{3})\.v1\.json', args.path),
        'INSPECT_OWN_PATH')
    context = r.g.observation.Context()
    owner = r.g.observation.Resources(context)
    q = candidate = result = None
    out = dict(state='FAILED_NOT_ACCEPTED', **r.p.r.flags())
    try:
        owner.admit()
        q = r.Reader(owner, context)
        doc = q.json(args.path)
        r.closed_attempt(doc)
        result = fields(doc, ('state', 'selected_test_index', 'selected_test_name',
            'packed_pressure_runtime_contract_tests_passed', 'error_code', 'resource_stop_reason',
            'resource_watcher_cleanup_confirmed', 'accepted_exact_product_body_count'))
        result['root_pin'] = q.reader.snapshots[args.path]
        # 두 번째 실제 읽기도 기존 Reader의 동일성/자원 검사를 거친다.
        result['root_size_comparison'] = fields(super(r.Reader, q).json(args.path),
            ('raw_json_bytes', 'gzip_bytes'))
        result['preparation_IO'] = fields(doc.get('preparation_IO', {}),
            ('bound_inputs', 'final_fresh_hashes', 'finished', 'bytes_read'))
        result['observation'] = fields(doc.get('metadata_observation', {}),
            ('completed_sample_count', 'system_cpu_max_percent', 'own_cpu_max_machine_percent',
             'own_private_max_bytes', 'available_ram_min_percent', 'new_sampler_thread_started'))
        result['plan'] = fields(doc.get('runtime_plan', {}),
            ('runtime_source_qualified_individual_cases', 'runtime_remaining_individual_cases',
             'runtime_remaining_regular_cases', 'runtime_remaining_corpus_cases',
             'runtime_successful_candidates_requiring_closing', 'next_runtime_index',
             'all_successful_bodies_pending_whole_reconciliation'))
        if doc['state'] == r.PASS:
            pin = doc['case_receipt_pin']
            index = doc['selected_test_index']
            r.require(re.fullmatch(re.escape(r.p.DIR) + rf'/cases/p222-case-{index:03}-run[0-9]{{3}}\.json', pin['path']),
                'INSPECT_EXACT_BODY_PATH')
            body = q.json(pin['path'])
            r.require(q.reader.snapshots[pin['path']] == pin, 'INSPECT_UNCHANGED_BODY_PIN')
            result['body_pin'] = pin
            result['body'] = fields(body, ('state', 'tests_passed', 'exit_code', 'elapsed_seconds',
                'resource_stop_reason', 'resource_watcher_cleanup_confirmed'))
            result['job_final'] = fields(body.get('job_final', {}),
                ('job_cpu_seconds', 'peak_job_private_mib', 'active_processes'))
            result['body_write'] = fields(doc['packed_parent_write_statistics'],
                ('raw_json_bytes', 'gzip_bytes', 'carrier_bytes', 'semantic_fields_removed',
                 'original_files_rewritten', 'CPU_or_PC_freeze_improvement_claimed'))
            result['frame'] = fields(doc['closing_component']['source_frame'],
                ('frame_state', 'input_count', 'input_bytes', 'original_owned_cleanup_confirmed_before_release',
                 'original_two_actual_per_case_byte_reads_retained', 'input_exclusions_added'))
            frame = doc['closing_component']['source_frame']
            own = frame['handles']
            result['handles'] = fields(own, ('input_lock_handles_opened', 'input_lock_handles_closed',
                'input_lock_cleanup_confirmed', 'ancestor_walk_steps'))
            result['borrowed'] = fields(own['borrowed_byte_streams'],
                ('duplicate_handles_opened', 'duplicate_handles_closed', 'duplicate_handles_remaining',
                 'shared_offset_resets', 'duplicate_close_failed_attempts'))
            result['native_pressure'] = fields(own['native_open_backpressure'],
                ('warning_entries', 'completed_pause_windows', 'requested_pause_seconds',
                 'maximum_pause_windows_per_entry', 'original_hard_resource_decisions_unmodified'))
        q.finish()
        candidate = dict(state='PASS_READONLY_PACKED_SUMMARY_NOT_GATE')
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        out['error_code'] = r.p.b.run.original.closed_error(error)
    finally:
        if q is not None:
            out['IO'] = q.summary()
        r.g.complete(out, owner, candidate, lambda row: r.require(
            row['IO']['finished'] is True and row['IO']['bound_inputs'] == row['IO']['final_fresh_hashes'],
            'INSPECT_ALL_FRESH'))
        safe = fields(out, ('state', 'error_code', 'resource_stop_reason', 'resource_watcher_cleanup_confirmed'))
        if out['state'] == 'PASS_READONLY_PACKED_SUMMARY_NOT_GATE':
            safe['summary'] = result
        print(json.dumps(safe, ensure_ascii=True))
    return 0 if out['state'] == 'PASS_READONLY_PACKED_SUMMARY_NOT_GATE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
