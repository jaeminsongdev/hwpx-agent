"""Scoped search code/docs/result closure; no Cargo, old queue or Native replay."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness

shared, c, a = harness.shared, harness.c, harness.a
OUTPUT = 'implementation/p09/evidence/p09-361-source-search-sync044.v1.json'
ROOT = 'implementation/p09/evidence/p09-361-'
PASSED = ROOT + 'source-search-recovery043.v1.json'
PRIOR = ROOT + 'source-search-components042.v1.json'
BASELINE = ROOT + 'note-export-context-product-recovery038.v1.json'
TEST = 'crates/hwpx-package/tests/document_import_search.rs'
NEW = {'crates/hwpx-package/src/document_import/search.rs',
       'crates/hwpx-package/src/document_import/search/extract.rs',
       'crates/hwpx-package/src/document_import/search/normalization.rs', TEST}
CHANGED = {'crates/hwpx-package/src/document_import.rs', 'crates/hwpx-package/Cargo.toml', 'Cargo.lock'}
DOCS = ('CURRENT_STATE.md', 'implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
        'protocol/migrations/p09-source-search-index-v1.md')


def inverse(text, pin, label):
    normalized = text.replace('\r\n', '\n')
    c.require(pin['sha256'] in {hashlib.sha256(normalized.encode()).hexdigest(),
              hashlib.sha256(normalized.replace('\n', '\r\n').encode()).hexdigest()}, label)


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'SOURCE_SEARCH_SYNC_IMMUTABLE_RUN_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(
        shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_SOURCE_SEARCH_SCOPED_SYNC', actual_Cargo_or_tests=False,
               actual_Hangul_or_COM=False, Native011_executed=False, prior_Native_replayed=False,
               accepted_count_delta=0, P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        passed, prior, baseline = q.json(PASSED), q.json(PRIOR), q.json(BASELINE)
        for name, sha in ((PASSED, '134f32e394f7af30a70f8782ddcd496244f0e10f55090a8ce883c1cbc75c44f0'),
                          (PRIOR, '72d4c86b04e150dd5ea02af1409625659f354ebd1cf3c60600e6b710261c41f0'),
                          (BASELINE, 'e9b76870002e6475e5beb72f9d6023d6b9bd67aee9478c1982a3c0c3a84f5a90')):
            c.require(q.snapshots[name]['sha256'] == sha, 'EXACT_SEARCH_AND_PRE_SEARCH_RESULTS')
        c.require(passed['state'] == 'PASS_MAPPED_SOURCE_SEARCH_ONE_RECOVERY_TWENTY_THREE_PRIOR_PASSES_PRESERVED_NOT_FULL_SEARCH_OR_GATE'
                  and passed['fresh_inputs'] == passed['final_fresh_hashes'] == 439
                  and passed['prior_passes_preserved'] == 23 and passed['tests_executed_this_run'] == 1
                  and passed['exact_test_file_inverse_verified'] and not passed['prior_passed_tests_reexecuted'],
                  'EXACT_ONE_RECOVERY_AND_TWENTY_THREE_UNCHANGED_PRIOR_PASSES')
        tested = {p['path']: p for p in passed['source_pins']}
        old = {p['path']: p for p in baseline['source_pins']}
        source_names = {n for n in tested if n.startswith('crates/') or n in {'Cargo.toml', 'Cargo.lock', 'rust-toolchain.toml'}}
        c.require(source_names - set(old) == NEW, 'ONLY_DECLARED_NEW_SEARCH_SOURCE_AND_TEST_FILES')
        for name in sorted(source_names - NEW - CHANGED):
            c.require(tested[name] == old[name], 'RETAINED_PRE_SEARCH_INPUT_PINS_IN_VERIFIED_RECOVERY')
        for name in sorted(NEW | CHANGED):
            q.pin(name)
            c.require(q.snapshots[name] == tested[name], 'CURRENT_SEARCH_CODE_MATCHES_PASSED_RECOVERY')
        module = q.text('crates/hwpx-package/src/document_import.rs')
        c.require(module.count('pub mod search;\n') == 1, 'ONLY_ONE_SEARCH_MODULE_ADDITION')
        inverse(module.replace('pub mod search;\n', ''), old['crates/hwpx-package/src/document_import.rs'],
                'ORIGINAL_DOCUMENT_IMPORT_EXACT_MODULE_INVERSE')
        manifest = q.text('crates/hwpx-package/Cargo.toml')
        c.require(manifest.count('regex.workspace = true\n') == 1, 'ONE_EXISTING_WORKSPACE_REGEX_DEPENDENCY')
        inverse(manifest.replace('regex.workspace = true\n', ''), old['crates/hwpx-package/Cargo.toml'],
                'ORIGINAL_PACKAGE_MANIFEST_EXACT_DEPENDENCY_INVERSE')
        lock = q.text('Cargo.lock')
        begin = lock.index('[[package]]\nname = "hwpx-package"\n')
        end = lock.index('[[package]]', begin + 12)
        block = lock[begin:end]
        c.require(block.count(' "regex",\n') == 1, 'ONE_LOCKFILE_PACKAGE_DEPENDENCY_ADDITION')
        inverse(lock[:begin] + block.replace(' "regex",\n', '') + lock[end:], old['Cargo.lock'],
                'ORIGINAL_LOCKFILE_EXACT_PACKAGE_DEPENDENCY_INVERSE_NO_NEW_VERSION')
        expected = set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(', q.text(TEST)))
        before = dict(prior['steps'][0]['tests'])
        after = dict(passed['steps'][0]['tests'])
        failed = {n for n, status in before.items() if status == 'FAILED'}
        c.require(len(expected) == 24 and set(before) == expected and len(failed) == 1
                  and set(after) == failed and all(v == 'ok' for v in after.values())
                  and sum(v == 'ok' for v in before.values()) == 23, 'ALL_TWENTY_FOUR_DISTINCT_SEARCH_CASES_COVERED')
        for record in (prior, passed):
            c.require(record['cleanup'], 'SEARCH_RUN_CLEANUP')
            for step in record['steps']:
                job = step['owned_job']
                c.require(step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty']
                          and job['job_handle_closed'] and job['last_job_accounting']['active_processes'] == 0,
                          'SEARCH_OWNED_JOBS_TERMINAL_AND_CLOSED')
        for suffix, sha in (('040', 'a6b444a747a8fa51f1f0dd12d43e740442416f8e5ad93b5ee31fe539e05a3de2'),
                            ('041', '9d8c763a2d1678bc7a34a0b06c75473b2b4d262ecd73f4f13a1584556fc8c319')):
            name = ROOT + 'source-search-components' + suffix + '.v1.json'
            failure = q.json(name)
            c.require(q.snapshots[name]['sha256'] == sha and failure['state'] == 'FAILED_SOURCE_SEARCH_COMPONENTS'
                      and failure['cleanup'] and failure['steps'][0]['tests'] == [], 'ORIGINAL_SEARCH_COMPILE_FAILURE_PRESERVED')
        for name in DOCS:
            q.pin(name)
        progress = q.text(DOCS[1])
        ids = re.findall(r'^\| (SEARCH-[0-9]{3}) \|', progress, re.M)
        c.require(len(ids) == len(set(ids)) == 19 and sorted(ids) == passed['p09_search_catalog_ids'],
                  'ALL_NINETEEN_P09_SEARCH_CAPABILITIES_HAVE_EXPLICIT_COMPLETION_BOUNDARIES')
        for marker in ('전체 제품 계약의 완료는 아니다', '439 fresh/final439', '23개는 재실행하지',
                       '158/249', 'Native011 미승인', 'SearchScopeSelector', 'P11 소유'):
            c.require(marker in progress, 'PROGRESS_COVERAGE_AND_AUTHORITY_BOUNDARIES')
        profile = q.text(DOCS[2])
        for marker in ('whole_document_visibility_and_search_qualified=false', 'decoded scalar ranges',
                       'non-adjacent source pieces', 'whole-file inverse', 'P09/A12/A13 OPEN'):
            c.require(marker in profile, 'SOURCE_SEARCH_PROFILE_REQUIRED_SEMANTICS')
        state = q.text(DOCS[0]).split('> 2026-10-19 P09 이전 주석 XML 문맥', 1)[0]
        for marker in ('REF46+SEARCH19=65', '439fresh/final439', '23개를 반복하지', '잔여91',
                       '고정CROSSREF8종 NOT_RUN', 'Native011 미승인/미실행', 'P10미시작'):
            c.require(marker in state, 'CURRENT_SEARCH_PROGRESS_AND_UNCHANGED_GATE')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        q.pin('tools/p09/run_source_search_components.py')
        c.require(q.snapshots['tools/p09/run_source_search_components.py'] == tested['tools/p09/run_source_search_components.py'],
                  'RECOVERY_VERIFIER_UNCHANGED')
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_SOURCE_SEARCH_SCOPED_CODE_DOCUMENT_SYNC_TWENTY_FOUR_COMPONENTS_NOT_FULL_SEARCH_OR_GATE',
                   fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
                   distinct_component_passes=24, prior_passes_reexecuted=False,
                   source_inventory_compared_to_pre_search_baseline=True,
                   original_module_manifest_lockfile_inverse_verified=True,
                   entire_439_input_inventory_reaudited=False,
                   p09_search_catalog_ids=sorted(ids), whole_document_search_qualified=False,
                   full_product_or_native_or_gate_complete=False,
                   next_work='Search_scope_explicit_coverage_and_product_request_wiring')
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message)
                   else 'SOURCE_SEARCH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        samples = guard.samples
        row.update(cleanup=guard.cleanup, elapsed_seconds=round(time.monotonic() - started, 3),
                   source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=samples,
                   system_CPU_max=max((s['system_cpu_percent'] for s in samples), default=None),
                   available_RAM_min_percent=min((s['available_ram_percent'] for s in samples), default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys = list(samples[0])
            values = [[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_SEARCH_SYNC_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row,
            NS(require=c.require, exact=lambda x, y, label: c.require(x == y, label)))
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'fresh_inputs', 'final_fresh_hashes',
              'cleanup', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'pin': pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
