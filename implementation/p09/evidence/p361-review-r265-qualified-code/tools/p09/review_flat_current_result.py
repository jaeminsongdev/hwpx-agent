"""Bounded real-result review; no runtime replay, queue write or new profiler.

The immutable case DATA and observed raw root pin select one completed result.
Keep the qualified complete oracle and negative checks under the original Guard.
This inspection helper is not part of the product's Python import closure.
"""
import argparse
import copy
from datetime import datetime
import json
import re
import time

import flat_current_queue_acceptance as m

r = m.r
a = m.a
SELF = 'tools/p09/review_flat_current_result.py'


def maxima(rows, key):
    return max((x[key] for x in rows if x.get(key) is not None), default=None)


def metrics(rows):
    a.resource_history(rows)
    return dict(samples=len(rows), CPU_max=maxima(rows, 'system_cpu_percent'),
        RAM_min=min(x['available_ram_percent'] for x in rows),
        commit_max=maxima(rows, 'commit_used_percent'),
        parent_CPU_max=maxima(rows, 'parent_cpu_machine_percent'),
        private_max_MiB=maxima(rows, 'parent_private_mib'),
        CPU_at_least90_samples=sum(x['system_cpu_percent'] >= 90 for x in rows))


def review(index, root_pin):
    step = r.configure(index)
    g = a.Guard()
    q = None
    out = {}
    stage = 'admission'
    error = None
    checks = []
    try:
        g.acquire()
        q = a.AcceptanceReader(r.c.ROOT, g.check)
        q.pin(SELF)
        stage = 'actual_complete_candidate_oracle'
        row, listing, evidence, proof = m.prepare(q, root_pin)
        checks.append('REAL_CURRENT_COMPLETE_NATIVE_PRODUCT_ORACLE')
        entry, ep = r.entry()
        engine, eg = r.template()
        a.require(ep['original115_wrapper_AST_restored_exactly'] and eg['original_engine_AST_restored_exactly'], 'FIXED_ENTRY_ENGINE_AST')
        checks.append('UNCHANGED_FIXED_ENTRY_ENGINE_AST')
        raw = m.candidate.read_source(q, m.candidate.ACCEPTOR_PIN)
        execute, ap = m.run_projection(raw, root_pin)
        a.require(ap['original_acceptor_AST_restored_exactly'] and ap['queue_metadata_fields'] == 10
            and f'case{index}-current-epoch-accept001' in execute.__globals__['OUTPUT'], 'EXACT_CURRENT_ACCEPTOR_AST')
        checks.append('EXACT_ACCEPTOR_AST_AND_UNIQUE_CURRENT_METADATA')
        stage = 'negative_complete_oracle_contracts'
        try:
            m.prepare(q, dict(root_pin, path=f'implementation/p09/evidence/p09-361-case{index-1}-current-runtime-run001.v1.json'))
        except ValueError:
            checks.append('WRONG_ROOT_PATH_REJECTED')
        else:
            raise ValueError('WRONG_ROOT_ACCEPTED')
        body = a.read_exact(q, a.BODY_PIN)
        fresh = a.packed.unpack(a.read_exact(q, a.FRESH_PIN), g.check)
        negatives = (
            ('MISSING_SOURCE_REJECTED', lambda x: x['source_freeze'].pop()),
            ('MISSING_POST_SAMPLE_REJECTED', lambda x: x.update(post_Job_cleanup_resource_samples=[])),
            ('GATE_PROMOTION_REJECTED', lambda x: x.update(P09_gate='PASS')),
            ('FAILED_CLEANUP_REJECTED', lambda x: x.update(cleanup_confirmed=False)),
            ('TAGGED_SYNTHETIC_REJECTED', lambda x: x.update(synthetic_fixture_only_not_evidence=True)),
        )
        for label, mutate in negatives:
            g.check()
            changed = copy.deepcopy(row)
            mutate(changed)
            try:
                m.validate_candidate(q, changed, listing, body, fresh, r.context(step))
            except (ValueError, KeyError, TypeError):
                checks.append(label)
            else:
                raise ValueError('NEGATIVE_CANDIDATE_ACCEPTED')
        a.exact(len(checks), 9, 'NINE_COMPLETE_ORACLE_CONTRACTS')
        stage = 'actual_distinct_acceptance_and_preserved_code'
        name = f'implementation/p09/evidence/p09-361-case{index}-current-epoch-accept001.v1.json'
        accepted = q.json(name)
        a.fields(accepted, dict(state=m.PASS, accepted_count_before=step.before,
            accepted_count_delta=1, accepted_count_after=step.before+1,
            runtime_remaining_individual_cases=249-step.before-1, next_runtime_index=index+1,
            accepted_current_generation_case_count=step.before+1-105,
            resource_cleanup_confirmed=True, P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN',
            full249_current_qualified=False, signed16_current_qualified=False), 'EXACT_DISTINCT_CURRENT_QUEUE')
        a.exact(accepted['runtime_candidate_pin'], root_pin, 'EXACT_ACTUAL_ROOT_AUTHORITY')
        qualified = r.scope.pins(row['source_freeze'])
        current_fresh = r.scope.pins(accepted['fresh_input_pins'])
        code_pins = []
        for code in (r.SELF, r.TEST, m.SELF):
            pin = qualified[code]
            a.exact(q.pin(code), pin, 'CURRENT_QUALIFIED_FIXED_CODE')
            a.exact(current_fresh[code], pin, 'FRESH_QUALIFIED_FIXED_CODE')
            archive = 'implementation/p09/evidence/p361-flat116-qualified-code/' + code
            a.exact(q.pin(archive), dict(pin, path=archive), 'PRESERVED_FIXED_CODE_ARCHIVE')
            code_pins.append(pin)
        a.exact(qualified[step.path], step.pin, 'ACTUAL_CURRENT_STEP_DATA')
        a.exact(current_fresh[step.path], step.pin, 'FRESH_CURRENT_STEP_DATA')
        stage = 'closing_fresh_reads_and_original_guard'
        q.finish()
        time.sleep(.5)
        g.check(force=True)
        s = row['samples']
        post = row['post_Job_cleanup_resource_samples']
        frame = row['source_frame']
        handles = frame['handles']
        actual = metrics(s)
        actual.update(inputs=frame['input_count'], directories=frame['held_identity_after_owned_cleanup']['directory_count'],
            each_boundary_bytes=[x['reader_diagnostics']['bytes_read'] for x in frame['actual_byte_boundaries']],
            elapsed_seconds=row['elapsed_seconds'], frame=frame['frame_state'],
            held_opened=handles['input_lock_handles_opened'], held_closed=handles['input_lock_handles_closed'],
            duplicates_opened=handles['borrowed_byte_streams']['duplicate_handles_opened'],
            duplicates_closed=handles['borrowed_byte_streams']['duplicate_handles_closed'],
            remaining=handles['input_lock_handles_remaining']+handles['borrowed_byte_streams']['duplicate_handles_remaining'],
            metadata_checks=handles['handle_metadata_checks'], streams=handles['byte_stream_identity_checks'],
            peak_physical=handles['borrowed_byte_streams']['physical_handle_peak'],
            imported_paths=len(row['imported_worker_source_paths']),
            predicted_seconds=row['complete_runtime_budget']['predicted_runtime_combined_seconds'],
            post_samples=len(post), post_CPU=post[-1]['system_cpu_percent'],
            last_to_post_seconds=(datetime.fromisoformat(post[-1]['time_utc'])-datetime.fromisoformat(s[-1]['time_utc'])).total_seconds(),
            closing_error=row.get('closing_error'), cleanup=row['cleanup_confirmed'], tree_empty=row['owned_tree_empty'],
            capture=row['capture_diagnostics']['buffered_bytes'], PDH=row['serial_CPU_attribution']['probes'][0])
        acceptance = metrics(accepted['resource_samples'])
        acceptance.update(elapsed_seconds=accepted['elapsed_seconds'],
            fresh_inputs=len(accepted['fresh_input_pins']), fresh_reads=accepted['fresh_read_passes'],
            fresh_bytes=accepted['fresh_bytes_read'], final_hashes=accepted['final_fresh_hashes'],
            cleanup=accepted['resource_cleanup_confirmed'])
        out.update(state='PASS_NINE_REAL_CURRENT_FLAT_RESULT_CONTRACTS_NOT_PRODUCT_REPLAY',
            index=index, contracts=checks, contract_count=len(checks),
            actual_pin=root_pin, acceptance_pin=q.snapshots[name], step_pin=step.pin,
            reused_fixed_code_pins=code_pins, inspection_source_fresh_pin=q.snapshots[SELF],
            inspection_helper_is_product_import_closure=False,
            queue=dict(before=step.before, delta=1, after=step.before+1,
                remaining=249-step.before-1, next=index+1, current_generation_count=step.before+1-105),
            next_name=listing['source_test_names'][index], actual=actual, acceptance=acceptance)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        candidate = str(exc) if isinstance(exc, ValueError) else type(exc).__name__.upper()
        error = candidate if re.fullmatch('[A-Z0-9_]{1,256}', candidate) else 'REDACTED_RESULT_REVIEW_FAILURE'
        out['state'] = 'STOPPED_RESULT_REVIEW_NOT_ACCEPTANCE'
    finally:
        try:
            g.close()
        except (ValueError, OSError):
            error = 'ORIGINAL_GUARD_CLEANUP_FAILED'
            out['state'] = 'STOPPED_RESULT_REVIEW_NOT_ACCEPTANCE'
    out.update(stage=stage, error_code=error, review_resource_samples=len(g.samples),
        review_CPU_max=maxima(g.samples, 'system_cpu_percent'), review_cleanup_confirmed=g.cleanup,
        product_or_Native_replayed=False, review_queue_delta=0, PC_freeze_resolved=False)
    print(json.dumps(out))
    return 0 if error is None and g.cleanup else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', type=int, required=True)
    parser.add_argument('--root-bytes', type=int, required=True)
    parser.add_argument('--root-sha256', required=True)
    args = parser.parse_args()
    pin = dict(path=f'implementation/p09/evidence/p09-361-case{args.case}-current-runtime-run001.v1.json',
               bytes=args.root_bytes, sha256=args.root_sha256)
    a.scope.pins([pin])
    raise SystemExit(review(args.case, pin))
