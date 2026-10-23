"""Mapped-source NFC/literal/regex components; no Native, product execution or queue replay."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness

shared, c, a = harness.shared, harness.c, harness.a
OUTPUT = 'implementation/p09/evidence/p09-361-source-search-recovery043.v1.json'
PRIOR = 'implementation/p09/evidence/p09-361-source-search-components042.v1.json'
FAILED_TEST = 'query_result_and_compiled_pattern_limits_return_errors_not_partial_sets'
TEST = 'crates/hwpx-package/tests/document_import_search.rs'
CONTRACTS = {'docs/04_feature_catalog/03_search.md',
             'docs/04_feature_catalog/contracts/03_search_contracts.md'}


def inventory(check):
    return shared.source_inventory(check) | {TEST} | CONTRACTS


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'SOURCE_SEARCH_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(
        shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_SOURCE_SEARCH_COMPONENTS', steps=[], actual_Hangul_or_COM=False,
               Native011_executed=False, prior_Native_replayed=False, accepted_count_delta=0,
               P09_gate='OPEN', P10_started=False, output_ingest_commit_or_publication=False,
               compiled_queue_reexecuted=False, whole_search_catalog_qualified=False,
               whole_document_visibility_and_search_qualified=False,
               edit_or_service_access_authority=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        names = inventory(guard.check)
        for name in sorted(names):
            q.pin(name)
        for module in tuple(sys.modules.values()):
            value = getattr(module, '__file__', None)
            if value:
                path = Path(value).absolute()
                if path.is_relative_to(c.ROOT / 'tools/p09') and path.suffix == '.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        expected = set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(', q.text(TEST)))
        c.require(len(expected) == 24, 'EXACT_TWENTY_FOUR_SOURCE_SEARCH_TESTS')
        prior = q.json(PRIOR)
        prior_tests = dict(prior['steps'][0]['tests'])
        c.require(prior['cleanup'] and prior['state'] == 'FAILED_SOURCE_SEARCH_COMPONENTS'
                  and set(prior_tests) == expected and prior_tests[FAILED_TEST] == 'FAILED'
                  and sum(v == 'ok' for v in prior_tests.values()) == 23,
                  'EXACT_PRESERVED_TWENTY_THREE_PASSES_AND_ONE_FAILURE')
        prior_pins = {p['path']: p for p in prior['source_pins']}
        c.require(names <= set(prior_pins), 'PRIOR_COMPLETE_SOURCE_SEARCH_INPUT_INVENTORY')
        for name in sorted(names - {TEST}):
            c.require(q.snapshots[name] == prior_pins[name], 'UNCHANGED_SOURCE_SEARCH_PRODUCTION_AND_OTHER_INPUTS')
        new = b'    assert!(matches!(i.find(Query {query:r"\\p{L}{100}",mode:Mode::Regex,..query("x")}),Err(E::Pattern)));Ok(())'
        old = b'    assert!(matches!(i.find(query("a")),Err(E::Pattern)));Ok(())'
        actual, test_bytes = q._read(TEST, parse=True)
        q._bind(TEST, actual)
        # Keep original bytes/newlines; q.text intentionally normalizes line endings.
        c.require(test_bytes.count(new) == 1, 'EXACT_ONE_FAILED_PATTERN_EXPECTATION_EDIT')
        restored = test_bytes.replace(new, old)
        c.require(len(restored) == prior_pins[TEST]['bytes']
                  and hashlib.sha256(restored).hexdigest() == prior_pins[TEST]['sha256'],
                  'EXACT_WHOLE_TEST_FILE_INVERSE_PRESERVES_OTHER_TWENTY_THREE_TESTS')
        catalog = q.text('docs/04_feature_catalog/03_search.md')
        catalog_ids = re.findall(r'^\| (SEARCH-[0-9]{3}) \|[^\n]*\| P09 \|', catalog, re.M)
        c.require(set(catalog_ids) == {f'SEARCH-{i:03}' for i in
                    (*range(1, 11), 13, 14, *range(19, 26))}, 'EXACT_NINETEEN_P09_SEARCH_CAPABILITIES')
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT / 'target'),
                   CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
                   CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
                   CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='SOURCE_SEARCH_PREFLIGHT_COMPLETE', inputs=len(q.snapshots))), flush=True)
        harness.run_one('only_previously_failed_compiled_pattern_limit_case',
                        [harness.CARGO, 'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-package',
                         '--test', 'document_import_search', '--', FAILED_TEST, '--exact', '--test-threads=1'],
                        {FAILED_TEST}, guard, env, row)
        c.require(inventory(guard.check) == names, 'FINAL_SOURCE_SEARCH_INPUT_INVENTORY_DRIFT')
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_MAPPED_SOURCE_SEARCH_ONE_RECOVERY_TWENTY_THREE_PRIOR_PASSES_PRESERVED_NOT_FULL_SEARCH_OR_GATE',
                   fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
                   component_tests=24, tests_executed_this_run=1, prior_passes_preserved=23,
                   prior_failure_pin=q.snapshots[PRIOR], exact_test_file_inverse_verified=True,
                   p09_search_catalog_ids=sorted(catalog_ids),
                   profile='hwpx-agent.source-text-search/nfc-map-v1',
                   full_search_001_and_002_contract_qualified=False,
                   prior_passed_tests_reexecuted=False, source_api_reexecuted=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__,
                   error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message)
                   else 'SOURCE_SEARCH_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        samples = guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
                   elapsed_seconds=round(time.monotonic() - started, 3),
                   source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=samples,
                   system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
                   available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys = list(samples[0])
            values = [[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_SOURCE_SEARCH_RESOURCE_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row,
            NS(require=c.require, exact=lambda x, y, label: c.require(x == y, label)))
        print(json.dumps({**{k: row.get(k) for k in
            ('state', 'error_code', 'fresh_inputs', 'final_fresh_hashes', 'cleanup',
             'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
            'steps': [{k: s.get(k) for k in ('stage', 'exit_code', 'diagnostics', 'locations',
                       'summaries', 'tests', 'panic_locations', 'safe_error_variants')} for s in row['steps']],
            'pin': pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
