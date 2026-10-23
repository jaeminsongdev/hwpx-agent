"""Scoped source search + strict authenticated product joins, serial and non-Native."""
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
OUTPUT = 'implementation/p09/evidence/p09-361-scoped-search-product-components045.v1.json'
CORE = ('document_import_search', 'document_import_search_scope')
PRODUCT = 'crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
PREFIX = 'actual_import::source_search::'
DOCS = ('docs/04_feature_catalog/03_search.md', 'docs/04_feature_catalog/contracts/03_search_contracts.md')


def inventory(check):
    return shared.source_inventory(check) | {PRODUCT} | set(DOCS) | {
        'crates/hwpx-package/tests/' + name + '.rs' for name in CORE}


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'SCOPED_SEARCH_PRODUCT_IMMUTABLE_RUN_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(
        shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    started = time.monotonic()
    q = None
    row = dict(state='FAILED_SCOPED_SEARCH_PRODUCT_COMPONENTS', steps=[], actual_Hangul_or_COM=False,
               Native011_executed=False, prior_Native_replayed=False, accepted_count_delta=0,
               P09_gate='OPEN', P10_started=False, output_ingest_commit_or_publication=False,
               compiled_queue_reexecuted=False, full_search_contract_or_native_qualified=False)
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
        expected = set()
        counts = []
        for name in CORE:
            found = set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',
                                  q.text('crates/hwpx-package/tests/' + name + '.rs')))
            c.require(not expected & found, 'DISTINCT_SCOPED_SEARCH_CORE_TEST_NAMES')
            expected |= found
            counts.append(len(found))
        c.require(counts == [24, 6], 'EXACT_SIX_NEW_TWENTY_FOUR_AFFECTED_SEARCH_CASES')
        product_tests = {PREFIX + n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(', q.text(PRODUCT))}
        c.require(len(product_tests) == 9, 'EXACT_NINE_NEW_SCOPED_SEARCH_PRODUCT_CASES')
        previous = q.json('implementation/p09/evidence/p09-361-source-search-recovery043.v1.json')
        previous_pins = {p['path']: p for p in previous['source_pins']}
        c.require(q.snapshots['crates/hwpx-package/tests/document_import_search.rs'] ==
                  previous_pins['crates/hwpx-package/tests/document_import_search.rs'], 'PRIOR_TWENTY_FOUR_TEST_BODIES_UNCHANGED')
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT / 'target'),
                   CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
                   CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
                   CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
                   CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='SCOPED_SEARCH_PRODUCT_PREFLIGHT_COMPLETE', inputs=len(q.snapshots))), flush=True)
        harness.run_one('six_new_scope_and_twenty_four_affected_search_cases',
            [harness.CARGO, 'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-package',
             '--test', CORE[0], '--test', CORE[1], '--', '--test-threads=1'], expected, guard, env, row)
        harness.run_one('nine_exact_authenticated_search_product_cases',
            [harness.CARGO, 'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-agent-cli',
             '--test', 'form_stored_provider', '--', *sorted(product_tests), '--exact', '--test-threads=1'],
            product_tests, guard, env, row)
        c.require(inventory(guard.check) == names, 'FINAL_SCOPED_SEARCH_PRODUCT_INPUT_INVENTORY_DRIFT')
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_SCOPED_SOURCE_SEARCH_SIX_NEW_TWENTY_FOUR_AFFECTED_NINE_PRODUCT_NOT_FULL_SEARCH_OR_GATE',
                   fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
                   new_scope_tests=6, affected_search_tests=24, new_product_tests=9,
                   original_twenty_four_test_bodies_unchanged=True, unrelated_stored_suites_reexecuted=False,
                   caller_source_or_form_import_required=False, service_write_acl_aead_head_rechecked=True,
                   retained_search_queries_reexecuted_on_verify=False,
                   complete_search_scope_hidden_style_or_native_qualified=False,
                   idempotency_key_claimed=False, command_line_or_server_route_added=False)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message)
                   else 'SCOPED_SEARCH_PRODUCT_FAILURE_NO_RAW_VALUES')
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
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_SCOPED_SEARCH_PRODUCT_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row,
            NS(require=c.require, exact=lambda x, y, label: c.require(x == y, label)))
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'fresh_inputs', 'final_fresh_hashes',
              'cleanup', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
              'steps': [{k: s.get(k) for k in ('stage', 'exit_code', 'diagnostics', 'locations', 'summaries',
                         'tests', 'panic_locations', 'safe_error_variants')} for s in row['steps']], 'pin': pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
