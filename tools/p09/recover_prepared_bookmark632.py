"""Recover the already-completed631 metadata; NEVER start/retry a Native case.

Creates an explicitly new self-contained carrier and an independent recovery
audit. Original631 publication failure, source, claim, spool and630 remain intact.
"""
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace as NS

import run_prepared_bookmark_native631 as entry
import prepared_bookmark632_receipt as carrier
from verify_prepared_bookmark631 import command

r = entry.r
runtime = entry.runtime
SELF = 'tools/p09/recover_prepared_bookmark632.py'
MODULE = 'tools/p09/prepared_bookmark632_receipt.py'
TEST = 'tools/p09/tests/test_prepared_bookmark632_receipt.py'
RECOVERED = 'implementation/p09/evidence/p09-361-prepared-bookmark631-recovered632.v1.json'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark632-recovery001.v1.json'


def completed(value):
    carrier.require(value['state'] == 'CAPTURED631_REMAINING_SIX_AND_RETAINED_TWO_SEMANTICS_UNQUALIFIED'
                    and value['cleanup'] is True and value.get('error_code') is None
                    and value['fixed_eight_executed'] is True and value['batch_closed_for_final_audit'] is True
                    and value['fresh_inputs'] == value['final_fresh_hashes'] == 298
                    and value['section_timing']['completed'] is True
                    and runtime.sections.closed_boundary(value['final_audit_boundary'])
                    and len(value['case_source_boundaries']) == 6
                    and all(runtime.sections.closed_boundary(b) for b in value['case_source_boundaries'])
                    and value['qualification_worker']['cleanup'] is True and value['capture_worker']['cleanup'] is True,
                    'ORIGINAL_COMPLETE_CAPTURE_AND_FINAL_AUDIT')
    carrier.require(value['reference_semantics_qualified'] is False and value['P09_gate'] == 'OPEN'
                    and value['P10_started'] is False and value['accepted_count_delta'] == 0,
                    'NO_ACCEPTANCE_PROMOTION')


def main():
    carrier.require(sys.argv[1:] == ['--recover-metadata-only'], 'FIXED_METADATA_ONLY_MODE')
    for name in (RECOVERED, OUTPUT):
        runtime.prepared.require_absent(r.c.ROOT, name)
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    audit = dict(state='FAILED632_COMPLETED631_PUBLICATION_RECOVERY', steps=[],
                 actual_native_started=False, actual_cases_reexecuted=0, original631_dispatch_success_claimed=False,
                 original630_failure_reclassified=False, field_or_render_semantics_qualified=False,
                 P09_complete=False, P10_started=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        for name in (SELF, MODULE, TEST, 'tools/p09/receipt_xz_envelope_v1.py',
                     'tools/p09/crossref_lossless_receipt610.py', 'tools/p09/verify_prepared_bookmark631.py'):
            q.pin(name)
        value, raw = carrier.retained(q)
        completed(value)
        audit.update(original_raw_bytes=len(raw), original_raw_sha256=carrier.MANIFEST_SHA,
                     original_631_state=value['state'], original_631_cleanup=value['cleanup'],
                     original_631_final_inputs=value['final_fresh_hashes'],
                     original_631_elapsed_seconds=value['elapsed_seconds'])
        runtime.prepared.require_absent(r.c.ROOT, entry.OUTPUT)
        test = command(guard, [sys.executable, '-B', str(r.c.ROOT/TEST)], r.audit.environment(), audit, 'publication_contracts12')
        carrier.require({k: test[k] for k in ('run', 'errors', 'failures', 'skipped')} == dict(run=12, errors=0, failures=0, skipped=0),
                        'ALL_CHANGED_PUBLICATION_CONTRACTS')
        for pin in value['source_pins']:
            carrier.require(q.pin(pin['path']) == pin, 'CONSUMED631_SOURCE_UNCHANGED')
        retained = runtime.evidence.retained(q, entry.codec.unpack)
        carrier.require(retained == value['retained_cases'], 'UNCHANGED_OLD_TWO_CAPTURE_BINDING')
        scope = value['capture_worker']['handler_summary']['protocol']['scope']
        carrier.require(len(scope['retired_sessions']) == 12 and scope['closed'] is True, 'TWELVE_CLOSED_NATIVE_LIFETIMES')
        rows = [runtime.evidence.captured(q, runtime.directory(i), i, scope['retired_sessions'][(i-1)*2:i*2]) for i in range(1, 7)]
        carrier.require(rows == value['artifacts']['cases'], 'ALL_SIX_CURRENT_ARTIFACTS_AND_PRODUCERS')
        audit.update(new_cases_rebound=6, old_cases_rebound=2,
                     artifact_files_rebound=sum(len(v['artifacts']) for v in rows+retained['cases']))
        try:
            entry.codec.pack(value, guard.check)
        except ValueError as error:
            carrier.require(error.args == ('XREF_LOSSLESS610_COMPRESSED_LIMIT',), 'EXACT_ORIGINAL_ENCODING_FAILURE')
            audit['original_publication_error_reproduced_without_native'] = error.args[0]
        else:
            raise ValueError('P632_RECEIPT_ORIGINAL_FAILURE_NOT_REPRODUCED')
        packet = carrier.pack(value, guard.check)
        carrier.require(carrier.compact.raw(carrier.unpack(packet, guard.check)) == raw, 'SELF_CONTAINED_EXACT875415_BYTES')
        recovered = r.shared.publisher.publish(r.c.ROOT, RECOVERED, packet, NS(require=r.c.require, exact=r.a.exact))
        carrier.require(carrier.compact.raw(carrier.unpack(q.json(RECOVERED), guard.check)) == raw,
                        'PUBLISHED_READER_EXACT_RAW_ROUNDTRIP')
        audit.update(recovered_receipt=recovered, recovered_raw_sha256=carrier.MANIFEST_SHA,
                     publication_limit_bytes=262144, compressed_limit_bytes=180000,
                     original_failure_and_all_bytes_preserved=True)
        carrier.require(not runtime.base.session.startup.hwp_pids(guard.windows, guard.check), 'NO_HWP_AFTER_METADATA_RECOVERY')
        q.finish()
        guard.check(force=True)
        audit['state'] = 'RECOVERED632_COMPLETED631_ALL_EIGHT_CAPTURE_BOUND_NOT_FIELD_RENDER_OR_GATE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        audit.update(**runtime.io.safe_failure(error))
    finally:
        guard.close()
        audit.update(cleanup=guard.cleanup and all(s['cleanup'] for s in audit['steps']),
                     fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                     elapsed_seconds=round(time.monotonic()-start, 3),
                     system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
                     available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None),
                     source_pins=[] if q is None else list(q.snapshots.values()))
        pin = entry.publish(OUTPUT, audit)
        print(json.dumps({**{k: audit.get(k) for k in ('state', 'error_code', 'new_cases_rebound', 'old_cases_rebound',
            'artifact_files_rebound', 'fresh_inputs', 'final_fresh_hashes', 'cleanup', 'elapsed_seconds',
            'system_CPU_max', 'available_RAM_min_percent', 'recovered_receipt')},
            'failed_tests': [n for s in audit['steps'] for n in s.get('result', {}).get('failed_tests', [])], 'receipt': pin}), flush=True)
    return 0 if audit['state'].startswith('RECOVERED632_') and audit['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
