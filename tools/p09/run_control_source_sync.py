"""Selected control-source/docs closure; no36-case/Cargo/712-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_control_source_components as target
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-control-source-sync193.v1.json'
PROFILE='protocol/migrations/p09-source-text-control-replacement-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-text-control-atom-patch-v1.md','protocol/migrations/p09-review-selector-control-core-v1.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED={target.OLD_TEST,SOURCE+'forms.rs',SOURCE+'fields.rs',SOURCE+'search.rs',SOURCE+'search/reviews/selector.rs',
    SOURCE+'search/selector.rs',SOURCE+'search/selector/control_geometry.rs',SOURCE+'search/inspection.rs',
    SOURCE+'search/replacement.rs',SOURCE+'search/replacement/atoms/review.rs',SOURCE+'search/replacement/atoms/readback.rs',
    SOURCE+'search/replacement/atoms/unicode/plan.rs',SOURCE+'search/replacement/atoms/whitespace/lexical.rs',
    SOURCE+'search/replacement/atoms/styles/text/output.rs','crates/hwpx-package/src/patch/text_control_atoms.rs',
    'crates/hwpx-package/src/patch/whitespace_atom_ranges.rs','crates/hwpx-package/src/text_flow.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_control_source_components.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_SOURCE_SYNC_IMMUTABLE_RUN_EXISTS');selection=target.prior.base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_SOURCE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);baseline=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='2c5c3182775ea96039baade96a89bf232420296c1cc2cbaab6757e5fa0aca604'
            and passed['state']=='PASS_CONTROL_SOURCE24_SELECTOR12_NOT_OTHER_KINDS_STORE_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==712 and passed['new_source_cases']==24
            and passed['affected_selector_cases']==12 and passed['total_executed_cases']==36,'EXACT192_TWENTY_FOUR_SOURCE_TWELVE_SELECTOR_AND_FRESH_CLOSURE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='db43378fce7e924fed7bac34a0b1f9f4e5822cac8911ecf91d4462676c2ac68f'
            and baseline['state']=='PASS_TEXT_CONTROL_PATCH18_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['new_patch_cases']==18,'ORIGINAL190_PATCH18_RETAINED_NOT_REPLAYED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_ORIGINAL_SOURCE_GUARDS_READBACK_WINDOWS_WRITER_FIXTURES_AND_TESTS_MATCH192')
        target.inverse(q,old);cases=target.expected(q);target.prior.base.prior.prior.base.prior.base.good_step(passed['steps'][0],cases)
        c.require(passed['original_selector_body_and_shared_readback_guard_bodies_inverse_verified']and passed['one_scope_resolution_and_preclone_output_budget']
            and passed['complete_atomic_original_control_selection_not_just_discovery_start']and not passed['old18_patch_whitespace24_products242_or_official249_reexecuted'],
            'SHARED_BODIES_COMPLETE_ATOMIC_PROOF_AND_TEST_SCOPE_NOT_WEAKENED')
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_control_source_sync.py')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)
        c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('source-selector-text-control-replacement/v1'in text and '712fresh/'in text and '36'in text
                and '158/249'in text and '91'in text and 'Native011'in text and 'P10'in text,'DOCS_SOURCE_PROFILE_INPUTS_PASSES_AND_UNCHANGED_GATE_BOUNDARIES')
        profile=q.text(PROFILE)
        for marker in('Tab/LineBreak','UnsupportedKind'):
            c.require(marker in profile,'QUALIFIED_TEXT_CONTROL_KINDS_AND_OTHER_KINDS_UNAVAILABLE')
        for marker in('단일 control unit','한 원본 기여자','scalar0','no-op','MEMO','3N','복제 전에','712fresh/final712',
            '192','신규 원본24+영향 선택 범위12=36pass','현재 저장 서비스·엄격한 제품 JSON','다른 제어 종류'):
            c.require(marker in profile,'EXPLICIT_ATOMIC_SCOPE_PROTECTION_BOUNDS_TEST_SCOPE_AND_REMAINING_PRODUCT_BOUNDARIES')
        c.require('원본 선택/보호/치환/readback 신규24+영향12개 검증'in progress
            and 'SEARCH-009 현재 저장 서비스·엄격한 제품 JSON 연결'in progress,'LATEST_SEARCH009_ROW_AND_NEXT_CURRENT_STORE_PRODUCT_WORK')
        q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_SOURCE_SELECTED_DOCS_SYNC_NOT_OTHER_KINDS_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            source_cases=24,affected_selector_cases=12,old18_patch_whitespace24_products242_reexecuted=False,full712_inputs_replayed=False,
            next_work='SEARCH009_current_store_strict_product_and_other_control_families_then_remaining_full_P09_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_SOURCE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
