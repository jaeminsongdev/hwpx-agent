"""Selected whitespace-source/docs closure, no24-case/Cargo/700-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_source_recovery as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-whitespace-source-sync186.v1.json'
PROFILE='protocol/migrations/p09-source-whitespace-normalization-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-whitespace-atom-patch-v1.md'}
RETAINED={'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/replacement.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/text/output.rs','crates/hwpx-package/src/patch/whitespace_atom_ranges.rs',
    'crates/hwpx-package/src/patch/text_atom_ranges.rs','crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/preserving_xml.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_whitespace_source_components.py',
    'tools/p09/run_whitespace_source_recovery.py','tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_SOURCE_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_SOURCE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='a322d2a1c5247e928bfed53083b41965c4b0caf720cc3960e898e792f6599042'
            and passed['state']=='PASS_WHITESPACE24_SOURCE_NOT_CURRENT_STORE_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==700 and passed['new_source_cases']==24,'EXACT185_TWENTY_FOUR_SOURCE_PASSES_AND_FRESH_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='98c2d3e7b4e74ae2819beff17c79d3654b26069cbc3be6b8f6a0322c318e61f3'
            and failed['state']=='FAILED_WHITESPACE_SOURCE_COMPONENTS'and failed['cleanup']and not failed['steps'][0]['tests'],'ORIGINAL184_ZERO_TEST_FAILURE_PRESERVED')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='8303bfcd1b3456a0f019b939c718ff9967947b42ee099603b6285da0b60f6350'
            and baseline['cleanup']and baseline['total_distinct_cases']==43,'ORIGINAL_PATCH43_NOT_REPLAYED_OR_PROMOTED')
        pins={p['path']:p for p in passed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_SOURCE_DEPENDENCIES_TESTS_GUARDS_WRITER_AND_READBACK_MATCH185')
        base.inverse(q,{p['path']:p for p in baseline['source_pins']});target.repair(q,{p['path']:p for p in failed['source_pins']})
        cases=base.expected(q);base.prior.base.good_step(passed['steps'][0],cases)
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)
        c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11_OWNED_OPERATIONS')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12000]):
            c.require('source-match-whitespace-normalization/v1'in text and '700fresh/'in text and '24'in text
                and '158/249'in text and '91'in text and 'P10'in text and 'Native011'in text,'DOCUMENTS_SOURCE_PROFILE_INPUTS_PASSES_AND_UNCHANGED_GATE_BOUNDARIES')
        profile=q.text(PROFILE)
        for marker in('Unicode17Breaking','EachOriginalScalar','1~1024','U+00A0','U+2007','U+202F','할당 전에','700fresh/final700','185','184','현재 저장 서비스·엄격한 제품 JSON'):
            c.require(marker in profile,'EXPLICIT_POLICY_GUARD_READBACK_LIMIT_FAILURE_AND_NEXT_PRODUCT_BOUNDARIES')
        c.require('현재 저장 서비스·엄격한 제품 JSON 연결'in progress and '제어 변경 readback 신규24개 검증'in progress,'LATEST_SEARCH023_ROW_AND_NEXT_WORK')
        c.require(not passed['old_patch43_products218_and_unrelated_source_reexecuted']and passed['shared_guard_body_and_old_readback_unchanged']
            and passed['namespace_and_numeric_output_bytes_bounded_before_allocation'],'TEST_SCOPE_AND_PREALLOCATION_PROTECTION_PRESERVED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE_SOURCE_SELECTED_DOCS_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            source_cases=24,retained_patch_cases=43,old218_products_reexecuted=False,full700_inputs_replayed=False,
            next_work='SEARCH023_current_store_and_strict_product_binding_then_remaining_full_P09_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_SOURCE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
