"""Selected casing/source/docs closure; no64-case/Cargo/673-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_case_conversion_recovery as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-case-conversion-sync172.v1.json'
PROFILE='protocol/migrations/p09-source-case-conversion-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-unicode-match-normalization-v1.md'}
SOURCE='crates/hwpx-package/src/document_import/'
RETAINED={SOURCE+'search/replacement/atoms/unicode/matches.rs',SOURCE+'search/replacement/atoms/readback.rs',
    SOURCE+'search/replacement/atoms/review.rs',SOURCE+'search/replacement/atoms/styles/text/output.rs',
    SOURCE+'search/reviews/selector.rs',SOURCE+'search/reviews/selector/styles.rs',SOURCE+'search/inspection/definitions.rs',
    SOURCE+'forms.rs',SOURCE+'fields.rs','crates/product-cli/src/reference_validation_product/source.rs',
    'crates/hwpx-package/tests/document_import_unicode_normalization.rs',
    'crates/hwpx-package/tests/document_import_unicode_match_normalization.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/review_scope_fixture.rs',
    'crates/hwpx-package/tests/support/review_cell_output_fixture.rs','crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
    'tools/p09/run_case_conversion_components.py','tools/p09/run_case_conversion_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CASE_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;stdlib=None;started=time.monotonic();row=dict(state='FAILED_CASE_CONVERSION_SYNC',actual_Cargo_or_tests=False,
        actual_Hangul_or_COM=False,own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='9052f0f34c12c073122b4ed0cf1f13c111a0baef83720e151675db6ef6b738b5'
            and passed['state']=='PASS_CASE1_REPAIRED63_RETAINED_NOT_CASE_STORED_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==673 and passed['stdlib_reference_inputs']==passed['stdlib_final_fresh_hashes']==3
            and passed['current_source_cases']==1 and passed['retained_source_cases']==63 and passed['total_distinct_cases']==64
            and not passed['passed63_cases_reexecuted']and passed['production_unchanged_after169'],'EXACT_ONE_CURRENT63_RETAINED_AND673_INPUT_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='c1d2709f369357e27a20ae65d99fcbc540852aa6c8a6675b5a00d0a065a0493c'
            and failed['state']=='FAILED_CASE_CONVERSION_COMPONENTS'and failed['cleanup'],'ORIGINAL169_FAILED_ORACLE_RETAINED')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='e2a13d4286f7890d0b6eed330b1b1c0c33ecbb3505eef2fb85724f6c18199133',
            'EXACT_PRIOR166_UNICODE_PRODUCT_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']};failed_pins={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_CASE_NORMALIZATION_GUARDS_TESTS_MATCH_PASS170')
        base.inverse(q,old);target.repair(q,failed_pins);cases=base.expected(q);retained={n for n,status in failed['steps'][0]['tests']if status=='ok'}
        c.require(len(retained)==63 and {n for n,status in failed['steps'][0]['tests']if status!='ok'}=={target.CASE}
            and cases==retained|{target.CASE},'EXACT64_DISTINCT_CASES_AND_NO_SYNTHETIC_SINGLE_RUN_CREDIT')
        base.good_step(passed['steps'][0],{target.CASE})
        c.require(passed['original_unicode_and_guard_patch_bodies_inverse_verified']and passed['whole_string_default_mapping_not_older_casefold_or_regex_properties']
            and passed['adjacent_changes_coalesced_only_within_original_text_atom'],'COMMON_ORIGINAL_PLAN_AND_SINGLE_GROUP_MAPPING_AND_BOUNDED_PATCHES')
        stdlib=a.AcceptanceReader(base.STD_ROOT,guard.check);stdpins={p['path']:p for p in passed['stdlib_reference_pins']}
        for name in sorted(base.STD_FILES):stdlib.pin(name);c.require(stdlib.snapshots[name]==stdpins[name],'SAME_THREE_UNICODE17_STD_REFERENCE_FILES_NOT_BINARY_REPRODUCIBILITY')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 검색 일치 Unicode 정규화 저장과 제품 v2',1)[0]
        for marker in('source-match-case-conversion/v1','UnicodeDefaultEachMatchedTextGroup','FinalSigma','Point import 누락 E0425',
            '신규22+영향기존42=고유64개','673fresh/final673','stdlib참고3/final3','통과63개','기존제품172·공식249',
            '91.188','4.250','0.84','577.45MiB','75.59%','P09/A12/A13 OPEN','Native011 미승인/미실행'):
            c.require(marker in profile,'PRECISE_CASE_POLICY_ORIGINAL_FAILURES_COUNTS_RESOURCES_AND_OPEN_NATIVE_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-013 | 대소문자 변환 | 명시적 Unicode17 기본 upper/lower source 신규22+영향42=고유64개 확인, 현재 저장/엄격한 제품 JSON·전체 계약/Native 미완료 |'in progress,
            'ALL19_FEATURE_ROWS_WITH_EXACT_CASE_SOURCE_ONLY_COMPLETION_BOUNDARY')
        for marker in('673fresh/final673','stdlib참고3/final3','신규22+영향기존42=고유64개','다음 접근허용 불필요 작업은 SEARCH-013 현재 저장 서비스',
            '공식158/249','P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_STATE_CASE_SOURCE_PROGRESS_AND_REMAINING_PRODUCT_AND_NATIVE_BOUNDARIES')
        c.require('p09-source-case-conversion-v1.md'in q.text('protocol/migrations/p09-source-unicode-match-normalization-v1.md'),
            'SHARED_ORIGINAL_UNICODE_PLAN_LINKS_CASE_PROFILE_WITHOUT_WIDENING_UNICODE_SEMANTICS')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();stdlib.finish();guard.check(force=True)
        row.update(state='PASS_CASE_SOURCE_SELECTED_DOCS_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            stdlib_reference_inputs=len(stdlib.snapshots),stdlib_final_fresh_hashes=stdlib.final_fresh_hashes,new_source_cases=22,affected_source_cases=42,
            total_distinct_cases=64,source673_or_Cargo_or_tests_reexecuted=False,
            next_work='Current_stored_and_strict_product_binding_of_explicit_default_case_conversion_then_remaining_P09_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CASE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),stdlib_reference_root=str(base.STD_ROOT),stdlib_reference_pins=[]if stdlib is None else list(stdlib.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CASE_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','stdlib_reference_inputs','stdlib_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
