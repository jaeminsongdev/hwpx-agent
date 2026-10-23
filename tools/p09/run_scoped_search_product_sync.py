"""Scoped search product source/result/doc closure; no Cargo, Native or queue replay."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared, c, a = harness.shared, harness.c, harness.a
ROOT = 'implementation/p09/evidence/p09-361-'
OUTPUT = ROOT + 'scoped-search-product-sync046.v1.json'
PASSED = ROOT + 'scoped-search-product-components045.v1.json'
BASELINE = ROOT + 'source-search-recovery043.v1.json'
NEW = {'crates/hwpx-package/src/document_import/search/scope.rs',
       'crates/hwpx-package/tests/document_import_search_scope.rs',
       'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
       'crates/product-cli/src/form_product_request/stored_source_search.rs',
       'crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'}
CHANGED = {'crates/hwpx-package/src/document_import/search.rs',
           'crates/product-cli/src/form_product_request.rs',
           'crates/product-cli/src/form_stored_provider/actual_import.rs',
           'crates/product-cli/tests/form_stored_provider/actual_import.rs'}
RETAINED = {'crates/hwpx-package/tests/document_import_search.rs',
            'crates/hwpx-package/src/document_import/search/extract.rs',
            'crates/hwpx-package/src/document_import/search/normalization.rs',
            'crates/hwpx-package/src/document_import/forms.rs',
            'crates/product-cli/src/form_stored_provider.rs',
            'crates/product-cli/src/form_product_request/stored_note_file.rs'}
DOCS = ('CURRENT_STATE.md', 'implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
        'protocol/migrations/p09-source-search-index-v1.md',
        'protocol/migrations/p09-source-search-product-request-v1.md')


def inverse(text, pin, label):
    normalized = text.replace('\r\n', '\n')
    c.require(pin['sha256'] in {hashlib.sha256(normalized.encode()).hexdigest(),
              hashlib.sha256(normalized.replace('\n', '\r\n').encode()).hexdigest()}, label)


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'SCOPED_SEARCH_SYNC_IMMUTABLE_RUN_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(
        shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_SCOPED_SEARCH_PRODUCT_SYNC', actual_Cargo_or_tests=False,
               actual_Hangul_or_COM=False, Native011_executed=False, prior_Native_replayed=False,
               accepted_count_delta=0, P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        passed, baseline = q.json(PASSED), q.json(BASELINE)
        c.require(q.snapshots[PASSED]['sha256'] == 'f0070c1d7bacd15c37e596b516b6b44b31472de03e388239ba650f676ee9e83c'
                  and q.snapshots[BASELINE]['sha256'] == '134f32e394f7af30a70f8782ddcd496244f0e10f55090a8ce883c1cbc75c44f0',
                  'EXACT_SCOPED_SEARCH_RESULT_AND_PREVIOUS_SOURCE_BASELINE')
        c.require(passed['state'] == 'PASS_SCOPED_SOURCE_SEARCH_SIX_NEW_TWENTY_FOUR_AFFECTED_NINE_PRODUCT_NOT_FULL_SEARCH_OR_GATE'
                  and passed['fresh_inputs'] == passed['final_fresh_hashes'] == 444 and passed['cleanup']
                  and passed['original_twenty_four_test_bodies_unchanged']
                  and not passed['unrelated_stored_suites_reexecuted'], 'SCOPED_SEARCH_VERIFIED_RESULT')
        tested = {p['path']: p for p in passed['source_pins']}
        old = {p['path']: p for p in baseline['source_pins']}
        source_names = {n for n in tested if n.startswith('crates/') or n in {'Cargo.toml', 'Cargo.lock', 'rust-toolchain.toml'}}
        c.require(source_names - set(old) == NEW, 'ONLY_FIVE_DECLARED_NEW_SCOPE_AND_PRODUCT_FILES')
        for name in source_names - NEW - CHANGED:
            c.require(tested[name] == old[name], 'ORIGINAL_OTHER_SOURCE_INPUTS_RETAINED_IN_VERIFIED_RUN')
        for name in sorted(NEW | CHANGED | RETAINED):
            q.pin(name)
            c.require(q.snapshots[name] == tested[name], 'CURRENT_SCOPED_SEARCH_CODE_MATCHES_PASS')
        search = q.text('crates/hwpx-package/src/document_import/search.rs')
        wrapper = ('        self.find_selected(query,None)\n    }\n'
                   '    fn find_selected(&self,query:SourceSearchQuery<\'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>)->Result<SourceSearchResult,E> {\n')
        for fragment in ('pub mod scope;\n', '    #[error("SEARCH_SCOPE_INVALID")] Scope,\n', wrapper,
                         '            if selected.is_some_and(|set|!set.contains(&block.paragraph.opaque_handle)){continue;}\n'):
            c.require(search.count(fragment) == 1, 'EXACT_DECLARED_SEARCH_SCOPE_DISPATCH_ADDITION')
            search = search.replace(fragment, '')
        inverse(search, old['crates/hwpx-package/src/document_import/search.rs'], 'ORIGINAL_FIND_BODY_EXACT_SCOPE_DISPATCH_INVERSE')
        for name, fragment in (
            ('crates/product-cli/src/form_product_request.rs', 'pub mod stored_source_search;\n'),
            ('crates/product-cli/src/form_stored_provider/actual_import.rs', 'pub mod source_search;\n'),
            ('crates/product-cli/tests/form_stored_provider/actual_import.rs', '#[path = "actual_import/source_search.rs"]\nmod source_search;\n')):
            value = q.text(name)
            c.require(value.count(fragment) == 1, 'ONE_ADDITIVE_SEARCH_MODULE_INCLUDE')
            inverse(value.replace(fragment, ''), old[name], 'ORIGINAL_REQUEST_PROVIDER_AND_TEST_MODULE_EXACT_INVERSE')
        expected_core = set()
        for name in ('document_import_search', 'document_import_search_scope'):
            expected_core |= set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',
                                            q.text('crates/hwpx-package/tests/' + name + '.rs')))
        expected_product = {'actual_import::source_search::' + n for n in
            re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',
                       q.text('crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'))}
        c.require(len(expected_core) == 30 and len(expected_product) == 9 and len(passed['steps']) == 2,
                  'EXACT_THIRTY_CORE_NINE_PRODUCT_CASE_INVENTORY')
        for step, expected in zip(passed['steps'], (expected_core, expected_product), strict=True):
            c.require(len(step['tests']) == len(expected) and {n for n, s in step['tests']} == expected
                      and all(s == 'ok' for n, s in step['tests']) and step['diagnostics'] == [], 'ALL_THIRTY_NINE_CASES_PASS_WITHOUT_DIAGNOSTICS')
            job = step['owned_job']
            c.require(step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty']
                      and job['job_handle_closed'] and job['last_job_accounting']['active_processes'] == 0,
                      'BOTH_SCOPED_SEARCH_JOBS_TERMINAL_AND_CLOSED')
        for name in DOCS:
            q.pin(name)
        progress = q.text(DOCS[1])
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|', progress, re.M)) == 19, 'RETAINED_NINETEEN_P09_SEARCH_COMPLETION_ROWS')
        for marker in ('총 39개', '444 fresh/final444', '286개', '검색 질의 자체는 반복하지', '16 KiB',
                       '전체 제품 계약의 완료는 아니다', 'source API v12', 'Native011 미승인', 'P11 소유'):
            c.require(marker in progress, 'SCOPED_SEARCH_PROGRESS_RESULT_AND_LIMIT_BOUNDARIES')
        profile = q.text(DOCS[3])
        for marker in ('document.write', 'Duplicate keys', 'mapped_document', 'paragraphs', '16 KiB',
                       'do not rerun the query', 'final head read precedes the consumer', '444 fresh/final444',
                       'Native011 unapproved/unexecuted', 'P09/A12/A13 OPEN'):
            c.require(marker in profile, 'SCOPED_SEARCH_PRODUCT_PROFILE_REQUIRED_CONTRACTS')
        state = q.text(DOCS[0]).split('> 2026-10-19 P09 이전 원본 검색 인덱스', 1)[0]
        for marker in ('39pass', '444fresh/final444', '54.05%', '20.8380%', '잔여91', '고정CROSSREF8종 NOT_RUN',
                       'Native011 미승인/미실행', 'P10미시작', '부분 원본 검색 경로'):
            c.require(marker in state, 'CURRENT_SCOPED_SEARCH_RESULT_AND_GATE_BOUNDARIES')
        c.require('p09-source-search-product-request-v1.md' in q.text(DOCS[2]), 'PURE_INDEX_AND_PRODUCT_PROFILE_LINKED')
        q.pin('tools/p09/run_scoped_search_product_components.py')
        c.require(q.snapshots['tools/p09/run_scoped_search_product_components.py'] ==
                  tested['tools/p09/run_scoped_search_product_components.py'], 'TESTED_SCOPED_SEARCH_VERIFIER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_SCOPED_SEARCH_PRODUCT_CODE_DOCUMENT_SYNC_THIRTY_NINE_CASES_NOT_FULL_SEARCH_OR_GATE',
                   fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
                   distinct_component_tests=39, original_other_source_and_test_bodies_preserved=True,
                   original_find_body_inverse_verified=True, original_request_provider_module_inverse_verified=True,
                   whole_444_input_inventory_reaudited=False, full_search_or_native_or_gate_qualified=False,
                   next_work='Source_style_control_observations_and_visibility_effective_style_search_coverage')
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__, error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}', message)
                   else 'SCOPED_SEARCH_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
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
            c.require([dict(zip(keys, v)) for v in values] == samples, 'LOSSLESS_SCOPED_SEARCH_SYNC_SAMPLES')
            row['resource_samples'] = dict(encoding='lossless_columns_v1', columns=keys, rows=values)
        pin = shared.publisher.publish(c.ROOT, OUTPUT, row,
            NS(require=c.require, exact=lambda x, y, label: c.require(x == y, label)))
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'fresh_inputs', 'final_fresh_hashes',
              'cleanup', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'pin': pin}), flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
