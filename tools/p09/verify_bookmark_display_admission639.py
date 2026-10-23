"""Only changed point-bookmark authoring admission and one affected AEAD test.

No Native, previous specimen regeneration, old test suite or queued249 replay.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import time

import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dependencies
import metadata_forensic_retention615 as retention
import run_prepared_bookmark_native631 as publisher

SELF = 'tools/p09/verify_bookmark_display_admission639.py'
TEST = 'crates/product-cli/tests/support/bookmark_display_admission639.rs'
PARENT = 'crates/product-cli/tests/stored_bookmark_insertion628.rs'
OUTPUT = 'implementation/p09/evidence/p09-361-bookmark-display-admission639-audit003.v1.json'
SPOOL = 'implementation/p09/evidence/private/p09-361-bookmark-display-admission639-audit003-forensic'
PRIOR = 'implementation/p09/evidence/p09-361-bookmark-display-admission639-audit002.v1.json'
PRIOR_SHA = 'b10fb11317c1a51f92a84ff739b3dddf060bc33cdf1d1defd5ad3af5d891423f'
PRIOR_TEST = 'implementation/p09/source-archive/p361-bookmark-display-admission639-audit002/bookmark_display_admission639.rs'
PRIOR_COMPILED = 'implementation/p09/evidence/p09-361-bookmark-display-admission639-compiled002.v1.json'
ARCHIVE = 'implementation/p09/source-archive/p361-bookmark-display-admission639/'
EXPECTED = 'implementation/p09/evidence/p09-361-bookmark-creation627-output-digests.v1.json'
CHANGED = (
    'crates/hwpx-package/src/document_import/reference_targets/sdk.rs',
    'crates/hwpx-package/src/document_import/fields/bookmark_insertion.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/source_index/bookmark_updates.rs',
    'crates/product-cli/src/reference_validation_product/source_crossref/bookmark_insertion.rs',
    'crates/product-cli/src/reference_validation_product/source_crossref/bookmark_updates.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/bookmark_insertion_output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output.rs', PARENT)


def require(ok, code):
    r.c.require(ok, 'P639_' + code)


def main():
    require(sys.argv[1:] == ['--changed-authoring-only-no-native'], 'FIXED_CHANGED_MODE')
    require(not (r.c.ROOT/OUTPUT).exists(), 'NEW_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = binary = None
    start = time.monotonic()
    row = dict(state='FAILED639_POINT_BOOKMARK_AUTHORING_ADMISSION', steps=[], Native_or_COM_started=False,
        historical_discovery8_or_passed_suite_replayed=False, block_bookmark_positive_qualified=False,
        admitted_point_displays=['page', 'bookmark_name', 'relative_position'],
        rejected_point_content_not_silently_coerced=True, full_REF035_or_P09_qualified=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        names = inventory.inputs(guard.check) | includes.test_inputs((PARENT, TEST), guard) | {SELF, TEST, PARENT, EXPECTED}
        names |= {ARCHIVE+name for name in CHANGED}
        for name in sorted(names):
            q.pin(name)
        manifest = q.json(EXPECTED)
        source = manifest['source']
        require(q.pin(source['path']) == source, 'ORIGINAL_CURRENT_NATIVE_SOURCE_UNCHANGED')
        tests = {'admission639::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)', q.text(TEST))}
        require(len(tests) == 10 and '#[ignore]' not in q.text(TEST), 'EXACT_NEW_TEN_TESTS')
        affected = 'aead_failure_and_restoration_never_revive_denied_candidate'
        tests.add(affected)
        old = q.text(ARCHIVE+PARENT)
        current = q.text(PARENT)
        def body(text, name):
            hit = re.search(r'#\[test\]\s*fn\s+'+re.escape(name)+r'\(', text)
            require(hit is not None, 'TEST_BODY_EXISTS')
            # These rustfmt-owned top-level tests end at the first column-zero
            # closing brace, not at the next test (which swallowed later helpers).
            end = re.search(r'(?m)^}\r?$', text[hit.end():])
            require(end is not None, 'TOP_LEVEL_TEST_END')
            return text[hit.start():hit.end()+end.end()]
        require(body(old, affected).replace('Display::Content', 'Display::BookmarkName', 1) == body(current, affected),
            'AEAD_TEST_ONLY_INVALID_INPUT_CORRECTED')
        for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)', old):
            if name != affected:
                require(body(old, name) == body(current, name), 'OTHER_OLD_TEST_BODIES_UNCHANGED')
        prior = publisher.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256'] == PRIOR_SHA and prior['cleanup'] is True
            and len(prior['steps']) == 1 and prior['steps'][0]['cleanup'] is True
            and prior['steps'][0]['exit_code'] == 101, 'EXACT_PRIOR_PARTIAL_TEST_RESULT')
        failed = 'admission639::write_permission_and_source_drift_still_precede_display_denial'
        statuses = dict(prior['steps'][0]['tests'])
        require(set(statuses) == tests and statuses[failed] == 'FAILED'
            and all(state == 'ok' for name, state in statuses.items() if name != failed), 'EXACT_RETAINED_TEN_PASSES_ONE_FAILURE')
        priorpins = {p['path']: p for p in prior['source_pins']}
        require(q.pin(PRIOR_TEST)['sha256'] == priorpins[TEST]['sha256'], 'ORIGINAL_FAILED_TEST_SOURCE')
        before, after = q.text(PRIOR_TEST), q.text(TEST)
        name = failed.split('::')[-1]
        require(before.replace(body(before, name), body(after, name), 1) == after, 'ONLY_FAILED_FIXTURE_BODY_CHANGED')
        for name, pin in priorpins.items():
            if name not in (SELF, TEST):
                require(q.pin(name) == pin, 'RETAINED_PRODUCT_AND_TEST_HELPER_BYTES_UNCHANGED')
        compiled_prior = q.json(PRIOR_COMPILED)
        require(compiled_prior['prior_receipt_sha256'] == PRIOR_SHA and len(compiled_prior['files']) == 2, 'RETAINED_COMPILED_PAIR')
        for pin in compiled_prior['files']:
            require(q.pin(pin['path']) == pin, 'ORIGINAL_COMPILED_BYTES_RETAINED')
        tests = {failed}
        row.update(executed_new_tests=1, total_new_conditions=10, retained_pass_conditions=10,
            retained_pass_tests=sorted(name for name in statuses if name != failed), retained_source_receipt=q.snapshots[PRIOR],
            original_test_binary_and_dep_info=compiled_prior['files'], affected_AEAD_tests=1, unrelated_existing_tests_not_replayed=7,
            point_content_positive_8_fixture_retired_before_directory_creation=True)
        env = r.audit.environment()
        args = [r.harness.CARGO, 'test', '--offline', '--locked', '-j', '1', '-p', 'hwpx-agent-cli',
            '--features', 'p09-installed-format-fixture', '--message-format=short',
            '--config', 'profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config', 'profile.test.package.hwpx-agent-cli.codegen-units=2',
            '--test', 'stored_bookmark_insertion628', '--', *sorted(tests), '--exact', '--test-threads=1']
        begin = time.time_ns()
        r.harness.run_one('corrected_fixture_only1_retained10_not_replayed', args, tests, guard, env, row, observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code'] == 0 and not row['steps'][-1]['diagnostics'], 'CLEAN_CHANGED_TESTS')
        binary = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        compiled = []
        for path in (r.c.ROOT/'target/debug/deps').glob('stored_bookmark_insertion628-*.d'):
            if path.stat().st_mtime_ns < begin:
                continue
            actual = dependencies.dependencies(path)
            require({PARENT, TEST, EXPECTED} <= actual and actual <= set(q.snapshots), 'COMPILED_TEST_INPUTS_PREBOUND')
            compiled.append(dict(dep_info=binary.pin(path.relative_to(q.root).as_posix()),
                binary=binary.pin(path.with_suffix('.exe').relative_to(q.root).as_posix()), dependency_count=len(actual)))
        require(len(compiled) == 1, 'ONE_CURRENT_TEST_EXECUTABLE')
        row['compiled_inputs'] = compiled
        binary.finish()
        q.finish()
        guard.check(force=True)
        row.update(state='QUALIFIED639_FOUR_PRODUCT_POINT_AUTHORING_BOUNDARIES_DENY_CONTENT_NOT_BLOCK_SUPPORT_OR_FULL_F11',
            current_source_valid_six_output_digests_unchanged=True, current_source_point_content_cases_denied=2)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error, ValueError) and re.fullmatch(r'P639_[A-Z0-9_]{1,100}', str(error)):
            row['error_code'] = str(error)
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_fresh_inputs=0 if binary is None else len(binary.snapshots),
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            source_pins=[] if q is None else list(q.snapshots.values()), elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        row, retained = retention.retain(r.c.ROOT, SPOOL, row)
        pin = publisher.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'executed_new_tests', 'fresh_inputs',
            'final_fresh_hashes', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')},
            'steps': [{k:s.get(k) for k in ('stage','exit_code','diagnostics','panic_locations','safe_error_variants','tests')} for s in row['steps']],
            'receipt':pin}), flush=True)
    return 0 if row['state'].startswith('QUALIFIED639_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
