"""Qualify only new bundle reader2; retain source-identical prior14/7/3 and worker denial evidence."""
import json
import subprocess
import sys
import time
import run_prepared_bookmark_native630 as entry
import prepared_bookmark_native630 as runtime
import crossref_lossless_receipt610 as codec

r = runtime.r
SELF = 'tools/p09/verify_prepared_bookmark630_history.py'
TEST = 'tools/p09/tests/test_prepared_bookmark630_history.py'
PRIOR = 'implementation/p09/evidence/p09-361-prepared-bookmark630-code005.v1.json'
ARCHIVE = 'implementation/p09/source-archive/p361-prepared-bookmark630/entry-code005.py'
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark630-code006-forensic'


def main():
    runtime.require(sys.argv[1:] == ['--bounded-bundle-history-reader'], 'PREPARED630_HISTORY_READER_ONLY')
    runtime.prepared.require_absent(r.c.ROOT, entry.CODE)
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = owned = capture = None;start = time.monotonic()
    row = dict(state='FAILED630_BUNDLE_HISTORY_READER', actual_native_started=False, steps=[],
               previous14_7_3_and_worker_denials_replayed=False, fixed_eight_executed=False, P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire();q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        prior = codec.unpack(q.json(PRIOR))
        runtime.require(q.snapshots[PRIOR]['sha256'] == '6a8dd66434a804bf748477431b31e2b43d1943d9b9cda4f56be42a4ed1827468'
                        and prior['state'] == entry.STATE and prior['cleanup'] is True
                        and prior['entry_failure_contracts'] == dict(run=3, errors=0, failures=0, skipped=0), 'PREPARED630_RETAINED_CODE005')
        pins = {p['path']: p for p in prior['source_pins']}
        runtime.require(q.pin(ARCHIVE)['sha256'] == pins[entry.SELF]['sha256'], 'PREPARED630_ARCHIVED_CODE005_ENTRY')
        current = q.text(entry.SELF)
        inverse = current.replace('code006.v1.json', 'code005.v1.json', 1)
        inverse = inverse.replace("                    and proof['bundle_history_contracts'] == dict(run=2, errors=0, failures=0, skipped=0)\n", '', 1)
        addition = "    # Full history is freshly bound ONCE by the enclosing bundle reader; its\n    # final audit rereads these same bytes. Do not carry history into case paths.\n    for path in sorted(set(pins) - paths):\n        runtime.require(reader.pin(path) == pins[path], 'PREPARED630_CHANGED_BUNDLE_HISTORY')\n"
        runtime.require(inverse.replace(addition, '', 1) == q.text(ARCHIVE), 'PREPARED630_ONLY_BUNDLE_HISTORY_BINDING_ADDED')
        paths = set(pins) | runtime.prepared.loaded_dependencies(r.c.ROOT) | {SELF, TEST, PRIOR, ARCHIVE}
        for path in sorted(paths):
            actual = q.pin(path)
            if path in pins and path != entry.SELF:
                runtime.require(actual == pins[path], 'PREPARED630_PRIOR24_AND_RUNTIME_UNCHANGED')
        for key in ('execution_dependency_paths', 'contracts', 'port_models', 'entry_failure_contracts', 'ready_denial',
                    'current_session_worker_check', 'shell_pin', 'current_session_worker_source_requalified_not_called_unchanged'):
            row[key] = prior[key]
        row.update(retained_code_receipt=PRIOR, ready_denial_retained_not_current_execution=True,
                   current_session_worker_check_retained_not_replayed=True,
                   history_proofs_checked_only_at_bundle_boundaries_not_per_case=True)
        runtime.require(not runtime.base.session.startup.hwp_pids(guard.windows, guard.check), 'PREPARED630_NO_HWP_BEFORE')
        step = dict(stage='bundle_history_reader2_not_native', cleanup=False);row['steps'].append(step)
        args = [str(runtime.prepared.inspection.fixed.PYTHON), '-B', str(r.c.ROOT/TEST)]
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[args[0]], cwd=r.c.ROOT, checkpoint=guard.check, env=r.audit.environment())
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check();runtime.require(time.monotonic()-start < 180, 'PREPARED630_NEW_READER_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:
                capture.progress();owned.observe()
        result = json.loads(out);row['bundle_history_contracts'] = {k: result[k] for k in ('run', 'errors', 'failures', 'skipped')}
        step.update(exit_code=owned.returncode, failed_tests=result['failed_tests'])
        runtime.require(owned.returncode == 0 and not err and row['bundle_history_contracts'] == dict(run=2, errors=0, failures=0, skipped=0), 'PREPARED630_NEW_READER_TWO')
        runtime.require(not runtime.base.session.startup.hwp_pids(guard.windows, guard.check), 'PREPARED630_NO_HWP_AFTER')
        q.finish();guard.check(force=True);row['state'] = entry.STATE
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(error_type=type(error).__name__, error_code=runtime.prepared.safe_code(error))
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();row['steps'][-1].update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
            source_pins=[] if q is None else list(q.snapshots.values()), fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=guard.samples, elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None), available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        normalized, retained = entry.retention.retain(r.c.ROOT, SPOOL, row);pin = entry.publish(entry.CODE, normalized)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'bundle_history_contracts', 'fresh_inputs', 'final_fresh_hashes', 'cleanup',
            'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'failed_tests': [n for s in row['steps'] for n in s.get('failed_tests', [])], 'receipt': pin}), flush=True)
    return 0 if row['state'] == entry.STATE and row['cleanup'] else 2


if __name__ == '__main__':raise SystemExit(main())
