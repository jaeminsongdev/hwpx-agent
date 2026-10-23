"""Compare actual prepared captures to the independent old Native insertion oracle.
Read-only hypothesis triage. No old/current Native or passed test replay.
"""
import json
import sys
import time
import inspect_prepared_bookmark633 as observation

entry = observation.entry
r = entry.r
runtime = entry.runtime
SELF = 'tools/p09/compare_prepared_bookmark634.py'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark634-oracle-triage001.v1.json'
PRIOR = observation.OUTPUT
CORPUS = 'implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'


def main():
    observation.require(sys.argv[1:] == ['--compare-existing-captures-only'], 'READONLY_ORACLE_MODE')
    runtime.prepared.require_absent(r.c.ROOT, OUTPUT)
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    row = dict(state='FAILED634_EXISTING_CAPTURE_ORACLE_TRIAGE', cases=[], actual_native_started=False,
               field_or_target_or_render_acceptance=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        q.pin(SELF)
        q.pin(observation.SELF)
        prior = entry.codec.unpack(q.json(PRIOR), guard.check)
        observation.require(q.snapshots[PRIOR]['sha256'] == '5b6b15d7288734478c696806dd4ae38344b1d6c1937e9e8e53e6a8aced3617df'
                            and prior['state'].startswith('OBSERVED633_') and prior['cleanup'] is True
                            and prior['fresh_inputs'] == prior['final_fresh_hashes'] == 38, 'EXACT633_OBSERVATION_ONLY')
        for pin in prior['source_pins']:
            observation.require(q.pin(pin['path']) == pin, 'OBSERVATION_INPUTS_UNCHANGED')
        corpus = q.json(CORPUS)
        observation.require(q.snapshots[CORPUS]['sha256'] == '9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f'
                            and corpus['source'] == runtime.prepared.SOURCE_PIN
                            and len(corpus['cases']) == len(prior['cases']) == 8, 'INDEPENDENT_NATIVE_SAME_SOURCE_EIGHT')
        for current, oracle in zip(prior['cases'], corpus['cases']):
            observation.require(current['case_index'] == oracle['case_index']
                and current['display'] == oracle['display'] and current['hyperlink'] == oracle['hyperlink'], 'MATCHED_TYPED_COMBINATIONS')
            candidate = current['stages']['candidate']
            observation.require(candidate['crossref_count'] == 1, 'EXACTLY_ONE_GENERATED_FIELD')
            comparisons = {}
            for label in ('saved', 'reopened'):
                pin = oracle['artifacts'][label]
                observation.require(q.pin(pin['path']) == pin, 'EXACT_OLD_NATIVE_ORACLE_BYTES')
                target = observation.observe(observation.section(q, pin['path']))
                observation.require(target['crossref_count'] == 1, 'ONE_ORACLE_FIELD')
                original = target['crossrefs'][0]
                actual = current['stages'][label]['crossrefs']
                observation.require(len(actual) == 1, 'ONE_CURRENT_FIELD')
                actual = actual[0]
                comparisons[label] = dict(display_equal=actual['display_sha256'] == original['display_sha256'],
                    command_equal=actual['command_sha256'] == original['command_sha256'] == oracle['command_sha256'],
                    all_parameter_values_equal=actual['parameter_hashes'] == original['parameter_hashes'],
                    current_dirty=actual['dirty'], oracle_dirty=original['dirty'],
                    current_display_characters=actual['display_characters'], oracle_display_characters=original['display_characters'])
            a, b = current['stages']['saved']['crossrefs'][0], current['stages']['reopened']['crossrefs'][0]
            row['cases'].append(dict(case_index=current['case_index'], display=current['display'], hyperlink=current['hyperlink'],
                saved_vs_reopened_display_equal=a['display_sha256'] == b['display_sha256'],
                saved_vs_reopened_parameters_equal=a['parameter_hashes'] == b['parameter_hashes'], comparisons=comparisons))
        q.finish()
        guard.check(force=True)
        row['state'] = 'OBSERVED634_GENERATED_NATIVE_VS_INDEPENDENT_INSERTION_ORACLE_NOT_FULL_ACCEPTANCE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        row.update(**runtime.io.safe_failure(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup, fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                   source_pins=[] if q is None else list(q.snapshots.values()), elapsed_seconds=round(time.monotonic()-start, 3))
        pin = entry.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'fresh_inputs', 'final_fresh_hashes', 'elapsed_seconds')},
                         'cases': row['cases'], 'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('OBSERVED634_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
