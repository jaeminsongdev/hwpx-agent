"""Selected typed-control foundation/source/docs closure; no18-case/Cargo/708-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_text_control_patch_recovery as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-text-control-patch-sync191.v1.json'
PROFILE='protocol/migrations/p09-text-control-atom-patch-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-whitespace-atom-patch-v1.md'}
RETAINED={'crates/hwpx-package/src/patch/text_atom_ranges.rs','crates/hwpx-package/src/patch/leaf_scalar_ranges.rs',
    'crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/text_flow/source_text_span.rs','crates/hwpx-package/src/preserving_xml.rs',
    'crates/hwpx-package/tests/patch_whitespace_atom_ranges.rs','crates/hwpx-package/tests/patch_text_atom_ranges.rs','crates/hwpx-package/tests/patch_leaf_scalar_ranges.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/whitespace.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/whitespace/plan.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_text_control_patch_components.py','tools/p09/run_text_control_patch_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_CONTROL_PATCH_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_CONTROL_PATCH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='db43378fce7e924fed7bac34a0b1f9f4e5822cac8911ecf91d4462676c2ac68f'
            and passed['state']=='PASS_TEXT_CONTROL_PATCH18_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==708 and passed['new_patch_cases']==18,'EXACT190_EIGHTEEN_PATCH_PASSES_AND_FRESH_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='8f722fdc7a45aa209c505740fd421fcc10ae59f3cf81417cb572d0ac89f899fc'
            and failed['state']=='FAILED_TEXT_CONTROL_PATCH_COMPONENTS'and failed['cleanup']and not failed['steps'][0]['tests'],'ORIGINAL189_ZERO_TEST_GRAPH_API_FAILURE_PRESERVED')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='a5a5da0058370b59835fc4e5d5e00539d11a3119e25bcf64c703a5917ef3ed75'
            and baseline['cleanup']and baseline['new_product_cases']==24,'ORIGINAL187_PRODUCT_BOUNDARY_RETAINED')
        pins={p['path']:p for p in passed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_SOURCE_OLD_BODIES_FIXTURES_GUARDS_AND_TESTS_MATCH190')
        base.inverse(q,{p['path']:p for p in baseline['source_pins']});target.repair(q,{p['path']:p for p in failed['source_pins']})
        cases=base.expected(q);base.prior.prior.base.prior.base.good_step(passed['steps'][0],cases)
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_text_control_patch_sync.py')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)
        c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('ReplaceTextControlAtoms'in text and '708fresh/'in text and '18'in text and '158/249'in text
                and '91'in text and 'Native011'in text and 'P10'in text,'DOCS_PATCH_PROFILE_INPUTS_PASSES_AND_UNCHANGED_GATE_BOUNDARY')
        profile=q.text(PROFILE)
        for marker in('TextControlAtomReplacement::new','원본 qualified','일반 Text','control subtree','네 편집 계열','5배',
            '708fresh/final708','189','190','2천 control','20만 ampersand','실제 control_anchor','보호 compiler','현재 저장/엄격한 제품 요청'):
            c.require(marker in profile,'EXPLICIT_TYPED_INPUTS_CONTROL_SELECTION_LIMIT_OPTIMIZATION_FAILURE_AND_NEXT_SOURCE_BOUNDARIES')
        c.require('제어 편집 기반 신규18개 검증'in progress and 'SEARCH-009 실제 control_anchor의 검색/선택·보호 compiler'in progress,'LATEST_SEARCH009_FOUNDATION_AND_NEXT_SOURCE_COMPILER')
        c.require(passed['production_unchanged_after189']and passed['all_old_patch_and_whitespace_bodies_inverse_verified']
            and passed['old_intents_early_zero_budget_and_original_control_rejection_preserved'],'ORIGINAL_PRODUCTION_GUARDS_AND_ERROR_NOT_WEAKENED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_CONTROL_PATCH_SELECTED_DOCS_SYNC_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            patch_cases=18,old_products242_reexecuted=False,full708_inputs_replayed=False,
            next_work='SEARCH009_exact_original_control_search_selection_protection_compiler_and_readback_then_other_control_families_and_full_product_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_CONTROL_PATCH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
