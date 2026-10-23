"""Selected whitespace-product/source/docs closure; no24-product/24-source/703-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_whitespace_product_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-whitespace-product-sync188.v1.json'
PROFILE='protocol/migrations/p09-whitespace-product-request-v1.md'
DOCS={PROFILE,'protocol/migrations/p09-source-whitespace-normalization-v1.md','protocol/migrations/p09-whitespace-atom-patch-v1.md',
    'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED=target.prior.base.NEW|target.prior.base.CHANGED|{
    SOURCE+'search/replacement/atoms/readback.rs',SOURCE+'search/replacement/atoms/review.rs',SOURCE+'search/replacement/atoms/styles/text/output.rs',
    SOURCE+'search/reviews/selector.rs',SOURCE+'search/reviews/selector/styles.rs',SOURCE+'search/inspection/definitions.rs',SOURCE+'forms.rs',SOURCE+'fields.rs',
    'crates/hwpx-package/src/patch/whitespace_atom_ranges.rs','crates/hwpx-package/src/patch/text_atom_ranges.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/product.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','crates/product-cli/tests/support/stored_source_fixture.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs',
    'tools/p09/run_whitespace_product_components.py','tools/p09/run_whitespace_source_components.py','tools/p09/run_whitespace_source_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_PRODUCT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);source=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='a5a5da0058370b59835fc4e5d5e00539d11a3119e25bcf64c703a5917ef3ed75'
            and passed['state']=='PASS_WHITESPACE_TWENTY_FOUR_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==703 and passed['new_product_cases']==24,'EXACT187_TWENTY_FOUR_PRODUCTS_AND_FRESH_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='a322d2a1c5247e928bfed53083b41965c4b0caf720cc3960e898e792f6599042'
            and source['state']=='PASS_WHITESPACE24_SOURCE_NOT_CURRENT_STORE_PRODUCT_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==700 and source['new_source_cases']==24,'EXACT185_ORIGINAL_SOURCE24_RETAINED_NOT_REPLAYED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in source['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_SOURCE_WRITER_ACCESS_PARSER_HEAD_BOUNDARIES_AND_TESTS_MATCH187')
        target.inverse(q,old);cases=target.expected(q);target.prior.base.prior.base.good_step(passed['steps'][0],cases)
        c.require(not passed['source24_reexecuted']and not passed['old218_products_reexecuted']and passed['original_product_and_source_test_bodies_inverse_verified']
            and passed['one_current_source_proof_whitespace_compiler_and_no_query_replay_on_delivery'],'OLD_COMPONENT_TESTS_RETAINED_AND_ONE_COMPILER_BOUNDARY')
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_whitespace_product_sync.py')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)
        c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11_OWNED_WORK')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:13000]):
            c.require('product-whitespace-normalization-request/v1'in text and '703fresh/'in text and '24'in text
                and '158/249'in text and '91'in text and 'P10'in text and 'Native011'in text,'DOCS_PRODUCT_REQUEST_INPUTS_PASSES_AND_UNCHANGED_PHASE_BOUNDARIES')
        profile=q.text(PROFILE)
        for marker in('normalize_whitespace_matches','whitespace_policy','tabs','line_breaks','sequence','output','16KiB','4096bytes','1~10000',
            'source v1','703fresh/final703','187','원본24·기존제품218·공식249는','RouteUnqualified','SEARCH-009','revision 저장 완료가 아니다'):
            c.require(marker in profile,'PRODUCT_EXPLICIT_POLICY_LIMIT_BINDING_TEST_SCOPE_NEXT_TASK_AND_NONAUTHORITY_BOUNDARY')
        c.require('현재 저장/엄격한 제품 JSON 신규24개 검증'in progress and 'SEARCH-009 지원 제어별 원본 치환과 참조/ID 보존'in progress,
            'LATEST_SEARCH023_COMPLETION_BOUNDARY_AND_NEXT_SEARCH009')
        q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE_PRODUCT_SELECTED_DOCS_SYNC_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            product_cases=24,retained_source_cases=24,old218_products_reexecuted=False,full703_inputs_replayed=False,
            next_work='SEARCH009_supported_control_source_replacement_and_reference_ID_preservation_then_remaining_P09_contract_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_PRODUCT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
