"""Selected match/scope source and docs closure;1 current+41 retained, no full663/test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_match_recovery as target
base=target.base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-unicode-match-sync165.v1.json'
PROFILE='protocol/migrations/p09-source-unicode-match-normalization-v1.md'
DOCS={PROFILE,'protocol/migrations/p09-source-unicode-normalization-v1.md','protocol/migrations/p09-unicode-product-request-v1.md',
    'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'}
RETAINED={base.base.TEST,base.base.ROOT+'normalization.rs',base.base.ROOT+'extract.rs',base.base.ROOT+'replacement.rs',
    base.base.ROOT+'replacement/atoms/unicode/transform.rs',base.base.ROOT+'replacement/atoms/readback.rs',base.base.ROOT+'replacement/atoms/review.rs',
    base.base.ROOT+'replacement/atoms/styles/text/output.rs',base.base.ROOT+'reviews.rs',base.base.ROOT+'reviews/selector/styles.rs',
    base.base.ROOT+'inspection.rs',base.base.ROOT+'inspection/definitions.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/unicode.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/unicode.rs',
    'crates/product-cli/src/reference_validation_product/source.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs','crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
    'tools/p09/run_unicode_match_components.py','tools/p09/run_unicode_match_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_MATCH_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_MATCH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(base.OUTPUT);original=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='f4e9af5273787ab26e600dcc5e7c9c9302a076f4b264813325b6ba5d10bdf86d'
            and passed['state']=='PASS_UNICODE_MATCH1_REPAIRED_41_RETAINED_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==663 and passed['total_distinct_cases']==42
            and passed['production_unchanged_after163']and not passed['passed41_cases_reexecuted'],'EXACT_CURRENT1_RETAINED41_MATCH_SOURCE_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='7cd0d7c55159120bd313949f3bffa04657f0b390a6b6e49f4acd84a80b9e6485'
            and failed['state']=='FAILED_UNICODE_MATCH_COMPONENTS'and failed['cleanup']and failed['steps'][0]['exit_code']==101
            and failed['steps'][0]['safe_error_variants']==['NoMatches'],'EXACT_ORIGINAL163_FAILURE_NOT_PROMOTED')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='1e3606982c37b493d59756f55daca0e7b029439fcaa3f4734881a43525b537af','EXACT_PRIOR_SCOPE_PRODUCT_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};pins={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_CORE_SCOPE_GUARD_MATCHER_PRODUCTS_AND_TESTS_MATCH_164')
        target.repair(q,pins);base.inverse(q,{p['path']:p for p in original['source_pins']});cases=base.expected(q)
        retained={n for n,s in failed['steps'][0]['tests']if s=='ok'};c.require(len(retained)==41 and retained|{target.CASE}==cases and len(cases)==42,'EXACT18_NEW_24_SCOPE_IDENTITIES')
        base.base.good_step(passed['steps'][0],{target.CASE});job=failed['steps'][0]['owned_job'];limits=job['limits_readback']
        c.require(failed['steps'][0]['cleanup']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'RETAINED41_RESULTS_HAVE_ORIGINAL_LIMITS_AND_TERMINAL_JOB')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 Unicode 정규화 저장과 제품 연결',1)[0]
        for marker in('source-match-unicode-normalization/v1','source-selector-unicode-normalization/v2','인접한 일치도 합치지 않는다',
            '663fresh/final663','신규18+영향기존24=고유42개','41pass/1fail','86.672','1.875','575.61MiB','65.23%','24.62%',
            '다음은 이 match 후보의 현재 저장 서비스·엄격한 제품 JSON 연결','P09/A12/A13 OPEN','Native011'):
            c.require(marker in profile,'PRECISE_MATCH_SOURCE_SEMANTICS_ORIGINAL_FAILURE_COUNTS_RESOURCES_AND_NEXT_PRODUCT_BOUNDARY')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-022 | Unicode 정규화 | 선택 범위 v1 제품20개·검색어/명시적 서식 일치 source 고유42개 검증, 일치 저장/제품·전체 계약 미완료 |'in progress,
            'ALL19_ROWS_AND_SOURCE_ONLY_MATCH_QUALIFICATION_NOT_CURRENT_PRODUCT')
        for marker in('663fresh/final663','고유42개','다음은 이 match 후보의 현재 저장 서비스·엄격한 제품 JSON 연결',
            '공식158/249','P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_STATE_EXACT_PROGRESS_NEXT_TASK_AND_ORIGINAL_PHASE_BOUNDARIES')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-unicode-match-normalization-v1.md'in q.text(name),'PRIOR_SCOPE_PROFILES_LINK_DISTINCT_MATCH_SOURCE_WITHOUT_WIDENING_OLD_REQUEST')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_MATCH_SELECTED_SOURCE_DOCS_SYNC_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=1,retained_cases=41,new_source_cases=18,affected_scope_cases=24,total_distinct_cases=42,
            source663_or_Cargo_or_tests_reexecuted=False,next_work='Current_stored_service_and_strict_match_normalization_product_request_then_remaining_full_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_MATCH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_MATCH_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
