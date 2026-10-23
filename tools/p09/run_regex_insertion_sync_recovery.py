"""Preserve failed121; normalize prose whitespace, check the actual product-boundary wording, no tests."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_sync as prior
shared,c,a=prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-sync122.v1.json'


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_SYNC_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=prior.base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_SYNC_RECOVERY',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='20bcc1ed55a32c9364aa1898860d138d3b9c58267fdc1c40d03f51b30de375b3'
            and failed['state']=='FAILED_REGEX_INSERTION_SYNC'and failed['error_code']=='SOURCE_PROFILE_COORDINATES_POLICY_LIMITS_RESOURCES_AND_PENDING_PRODUCT_NATIVE_QUALIFICATION'
            and failed['cleanup']and not failed['actual_Cargo_or_tests'],'EXACT_FAILED_PROSE_MARKER_AUDIT_PRESERVED_NO_TEST_REPLAY')
        for pin in failed['source_pins']:
            q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'ALL_CURRENT_CODE_DOCUMENTS_TESTS_RESULTS_AND_GUARDS_MATCH_FAILED_SYNC_EXACTLY')
        recovered=q.json(prior.linear.prior.OUTPUT);passed=q.json(prior.linear.OUTPUT);original=q.json(prior.base.OUTPUT)
        c.require(q.snapshots[prior.linear.OUTPUT]['sha256']=='9488aacb48a5217973ab47b17411e5b6fbac23d92c49f17df21172880d4322ea'
            and passed['state'].startswith('PASS_')and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==592
            and passed['total_distinct_cases']==116 and passed['retained_original_cases']==97,'CURRENT_LINEAR_COMPONENT_RESULTS_AND_FULL_INPUT_CLOSURE')
        prior.linear.inverse(q,{p['path']:p for p in recovered['source_pins']});prior.linear.prior.test_inverse(q,{p['path']:p for p in original['source_pins']});prior.base.boundaries(q)
        cases={'regex_insertions::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(prior.base.TEST))}
        prior.good_step(passed['steps'][0],cases);prior.good_step(recovered['steps'][1],prior.base.prior.expected(q))
        c.require(len(cases)==19,'EXACT_NINETEEN_CURRENT_V2_CASES')
        profile=' '.join(q.text(prior.PROFILE).split()).lower()
        for marker in('RightOriginalPointElseLeftFirstEmptyText','One suffix minimum','One protected output transaction','empty query remains invalid',
            'One direct-child edge inventory','does not repeatedly insert','116 distinct cases','original97 results are retained','592 fresh/final592',
            '102.328 seconds','26.500 seconds','1.77 seconds','24.891 seconds','29.31%','35.9864%','1647.82 MiB',
            'current stored access and a strict product request','unapproved/unexecuted'):
            c.require(marker.lower()in profile,'PRECISE_SOURCE_PROFILE_PROSE_WITH_FORMATTING_WHITESPACE_NORMALIZED')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19
            and '별도 빈 일치 source v2 통과'in progress and 'v2 저장/제품 연결·전체 계약 미완료'in progress
            and '19pass·592fresh/final592'in progress and '다음은 빈 일치 source v2의 현재 저장/엄격한 제품 연결'in progress,
            'ALL_SEARCH_ROWS_AND_SOURCE_ONLY_CURRENT_PRODUCT_BOUNDARY')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 정규식 치환 저장과 제품 요청',1)[0]
        for marker in('19pass·592fresh/final592','고유116개','다음은 이 명시적 v2 빈 일치 후보의 현재 저장 서비스와 엄격한 제품 요청 연결',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'CURRENT_SOURCE_PROGRESS_AND_UNCHANGED_QUEUE_PHASE_GATE')
        for name in prior.DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',prior.PROFILE}:
            c.require('p09-source-selector-regex-insertion-v2.md'in q.text(name),'OLD_V1_SOURCE_AND_PRODUCT_PROFILES_LINK_SEPARATE_V2')
        source=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('hwpx-agent.product.reference-source-assessment/v12'in source and 'validation_report: None'in source
            and all('UnresolvedReferenceStage::'+n in source for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_API_STILL_INCOMPLETE_WITH_FOUR_UNRESOLVED_STAGES')
        q.pin('tools/p09/run_regex_insertion_sync.py');q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_CODE_DOCUMENT_SYNC_NOT_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_v2_cases=19,retained_original_cases=97,total_distinct_cases=116,entire_592_input_set_reaudited=False,tests_reexecuted=False,
            failed_sync_preserved=True,only_prose_whitespace_and_actual_boundary_predicate_changed=True,
            next_work='Explicit_v2_zero_width_current_stored_and_strict_product_binding_then_remaining_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_SYNC_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_SYNC_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
