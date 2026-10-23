"""Qualify only the current8 post-save field readback vs same-source Native oracle.
Not general target resolution, DocumentGraph reopening, render or REF-035 closure.
"""
import sys
import time
import json
import compare_prepared_bookmark634 as prior
from verify_prepared_bookmark631 import command

entry = prior.entry
runtime = prior.runtime
r = prior.r
SELF = 'tools/p09/qualify_prepared_bookmark635.py'
TEST = 'tools/p09/tests/test_prepared_bookmark635_readback.py'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark635-field-readback001.v1.json'


def main():
    prior.observation.require(sys.argv[1:] == ['--qualify-existing-field-readback-only'], 'EXISTING_READBACK_ONLY')
    runtime.prepared.require_absent(r.c.ROOT, OUTPUT)
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    row = dict(state='FAILED635_CURRENT_BOOKMARK_FIELD_READBACK', steps=[], actual_native_started=False,
               previous_Native_or_product_trials_replayed=False, render_qualified=False,
               target_motion_or_rename_qualified=False, complete_DocumentGraph_semantic_reopen_qualified=False,
               full_REF035_or_P09_qualified=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        q.pin(SELF)
        q.pin(TEST)
        value = entry.codec.unpack(q.json(prior.OUTPUT), guard.check)
        prior.observation.require(q.snapshots[prior.OUTPUT]['sha256'] == 'b33c30bfd74bd9e745c9a367a6f5ce60a33da5bdbee52ca4a4697104cff1b0eb'
            and value['state'].startswith('OBSERVED634_') and value['cleanup'] is True
            and value['fresh_inputs'] == value['final_fresh_hashes'] == 57, 'EXACT_EXISTING634_CLOSED_INPUTS')
        for pin in value['source_pins']:
            prior.observation.require(q.pin(pin['path']) == pin, 'UNCHANGED_ACTUAL_HWPX_AND_OBSERVERS')
        proof = entry.codec.unpack(q.json(prior.PRIOR), guard.check)
        prior.observation.require(len(value['cases']) == len(proof['cases']) == 8, 'ALL_EIGHT_TYPED_COMBINATIONS')
        for index, (case, observed) in enumerate(zip(value['cases'], proof['cases']), 1):
            prior.observation.require(case['case_index'] == observed['case_index'] == index
                and case['display'] == observed['display'] == ('page', 'bookmark_name', 'content', 'relative_position')[(index-1)//2]
                and case['hyperlink'] == observed['hyperlink'] == bool((index-1)%2)
                and case['saved_vs_reopened_display_equal'] is True and case['saved_vs_reopened_parameters_equal'] is True,
                'EXACT_PROFILE_AND_REOPEN_INVARIANCE')
            candidate = observed['stages']['candidate']['crossrefs']
            prior.observation.require(len(candidate) == 1 and candidate[0]['dirty'] == '1', 'UNEVALUATED_GENERATED_CANDIDATE')
            for label in ('initial', 'saved', 'reopened'):
                fields = observed['stages'][label]['crossrefs']
                prior.observation.require(len(fields) == 1 and fields[0]['dirty'] == '0'
                    and fields[0]['display_sha256'] != candidate[0]['display_sha256']
                    and fields[0]['display_sha256'] == observed['stages']['saved']['crossrefs'][0]['display_sha256'],
                    'POST_NATIVE_CALCULATED_RESULT_PRESERVED')
            for match in case['comparisons'].values():
                prior.observation.require(all(match[k] is True for k in ('display_equal', 'command_equal', 'all_parameter_values_equal'))
                    and match['current_dirty'] == match['oracle_dirty'] == '0', 'INDEPENDENT_NATIVE_ORACLE_READBACK')
        test = command(guard, [sys.executable, '-B', str(r.c.ROOT/TEST)], r.audit.environment(), row, 'field_span_reader_contracts12')
        prior.observation.require({k: test[k] for k in ('run', 'errors', 'failures', 'skipped')} == dict(run=12, errors=0, failures=0, skipped=0),
                                  'STRICT_READER_CONTRACTS')
        q.finish()
        guard.check(force=True)
        row.update(state='QUALIFIED635_CURRENT_BOOKMARK8_POST_SAVE_FIELD_READBACK_NOT_RENDER_TARGET_RENAME_OR_F11',
                   profile_cases=8, initial_saved_reopened_documents=24, independent_native_oracle_documents=16,
                   case_results=value['cases'], field_readback_profile_qualified=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        row.update(**runtime.io.safe_failure(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(v['cleanup'] for v in row['steps']),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            source_pins=[] if q is None else list(q.snapshots.values()), elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        pin = entry.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'profile_cases', 'fresh_inputs', 'final_fresh_hashes',
            'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
            'failed_tests': [n for s in row['steps'] for n in s.get('result', {}).get('failed_tests', [])], 'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('QUALIFIED635_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
