"""Recover only the selected-doc baseline inventory; preserve195 and all product/source code."""
import json,re,time
from types import SimpleNamespace as NS
import run_control_product_sync as prior
target,source,shared,c,a,tools=prior.target,prior.source,prior.shared,prior.c,prior.a,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-control-product-sync-recovery196.v1.json'
PROFILE,DOCS=prior.PROFILE,prior.DOCS
#193's docs-only driver was not a194 product input; do not invent a194 pin for it.
RETAINED=prior.RETAINED-{'tools/p09/run_control_source_sync.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_PRODUCT_SYNC_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_PRODUCT_SYNC_RECOVERY',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);baseline=q.json(source.OUTPUT);failure=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='24246868ce16f02ba4cb4e73329bd57a32f63646d8da2cba24fe0c10acd12331'
            and failure['state']=='FAILED_CONTROL_PRODUCT_SYNC'and failure['error_type']=='KeyError'and failure['cleanup']
            and not failure['actual_Cargo_or_tests'],'ORIGINAL195_DOCS_BASELINE_KEYERROR_TERMINAL_PRESERVED_NO_TEST_REPLAY')
        c.require(q.snapshots[target.OUTPUT]['sha256']=='f12fe3c49d3dc91f50d65ad106954cdd7ba648817ecf57a43ac01ef4c7fbad81'
            and passed['state']=='PASS_CONTROL_TWENTY_FOUR_PRODUCTS_NOT_OTHER_KINDS_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==716 and passed['new_product_cases']==24,'EXACT194_NEW24_PRODUCT_AND_FRESH_CLOSURE')
        c.require(q.snapshots[source.OUTPUT]['sha256']=='2c5c3182775ea96039baade96a89bf232420296c1cc2cbaab6757e5fa0aca604'
            and baseline['state']=='PASS_CONTROL_SOURCE24_SELECTOR12_NOT_OTHER_KINDS_STORE_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['new_source_cases']==24 and baseline['affected_selector_cases']==12,'EXACT192_SOURCE36_RETAINED_NOT_REPLAYED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        names=target.NEW|target.CHANGED|source.NEW|source.CHANGED|RETAINED
        c.require(names<=tested.keys(),'SELECTED_SOURCE_PRODUCT_INPUTS_ALL_DECLARED_BY194')
        for name in sorted(names):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_PRODUCT_SOURCE_GUARDS_READBACK_PATCHES_FIXTURES_AND_TESTS_MATCH194')
        target.inverse(q,old);cases=target.expected(q);tools.good_step(passed['steps'][0],cases)
        c.require(not passed['source36_reexecuted']and not passed['old242_products_reexecuted']and not passed['accepted_count_delta']
            and passed['original_product_and_control_source_bodies_inverse_verified']
            and passed['one_borrowed_validated_output_current_source_proof_compiler_and_no_search_replay']
            and passed['linear_forward_anchor_subset_no_quadratic_revalidation']
            and passed['moved_wire_payload_borrowed_canonical_serialization_no_native_output_vector_clone'],
            'ORIGINAL_PROOF_LIMITS_OWNER_MOVE_LINEAR_SUBSET_AND_RETAINED_TEST_SCOPE')
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_control_product_sync.py');q.pin('tools/p09/run_control_product_sync_recovery.py')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)
        c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('product-text-control-replacement-request/v1'in text and '716fresh/final716'in text and '24pass'in text
                and '158/249'in text and '91'in text and 'Native011'in text and 'P10'in text,'DOCS_CURRENT_PRODUCT_PROFILE_PASSES_AND_UNCHANGED_GATE_BOUNDARIES')
        profile=q.text(PROFILE)
        for marker in('Tab/LineBreak','UnsupportedKind','replace_text_controls','max_replacements','1~4096','16KiB',
            'include_hidden_explanations/include_memo_bodies','ValidatedTextControlOutput','fresh reconstruction proof',
            'forward iterator','String','RouteUnqualified','266개','기존 원본36·이전 제품242·공식249는 재실행하지 않았다',
            'target match_set/semantic_diff/reopen','다른 제어 종류의 지원 조건과 참조/ID 보존'):
            c.require(marker in profile,'EXACT_PREPARATION_CONTRACT_PROOF_COST_AND_REMAINING_FULL_PRODUCT_BOUNDARIES')
        c.require('pub include_hidden_explanations:bool,pub include_memo_bodies:bool'in q.text('crates/hwpx-package/src/document_import/search/reviews.rs'),
            'DOCUMENTED_REVIEW_POLICY_FIELDS_MATCH_ACTUAL_REQUIRED_BOOL_KEYS')
        c.require('현재 저장/엄격한 제품24개 검증, 다른 제어·전체 계약/실행 미완료'in progress
            and 'SEARCH-009 다른 제어 종류의 지원 조건과 참조/ID 보존'in progress,'LATEST_SEARCH009_ROW_AND_NEXT_OTHER_CONTROL_WORK')
        q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_PRODUCT_SELECTED_DOCS_SYNC_NOT_OTHER_KINDS_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases_retained=24,source36_and_old242_products_reexecuted=False,full716_inputs_replayed=False,
            original195_failure_preserved=True,only_docs_baseline_inventory_corrected=True,
            next_work='SEARCH009_other_control_families_reference_ID_preservation_and_remaining_full_P09_contract_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_PRODUCT_SYNC_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
