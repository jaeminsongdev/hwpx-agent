"""Selected source/document closure for17 current +4 retained text-style cases, no test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_style_id_recovery as target
from run_style_replacement_sync import good_step
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-text-style-sync136.v1.json'
PROFILE='protocol/migrations/p09-source-text-style-replacement-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-character-style-product-request-v1.md','protocol/migrations/p09-source-definition-style-search-v3.md'}
RETAINED={'crates/hwpx-package/src/document_import/search/replacement/output.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions.rs',
    'crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/text_atom_ranges.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/styles.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement/styles.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/style_replacement_product.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_text_style_components.py',
    'tools/p09/run_text_style_recovery.py','tools/p09/run_text_style_id_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_STYLE_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=target.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_STYLE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='f6e09fcba44c43862eb35bd41592d8fb8d1975a60a528c3161cb69ece48a7c30'
            and passed['state']=='PASS_TEXT_STYLE_SEVENTEEN_CURRENT_FOUR_RETAINED_NOT_STORED_PRODUCT_EFFECTIVE_STYLE_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==616
            and passed['current_cases']==17 and passed['retained_unaffected_cases']==4 and passed['total_distinct_cases']==21
            and not passed['retained_cases_reexecuted'],'EXACT_CURRENT_TEXT_STYLE_QUALIFICATION_AND_RETAINED_BOUNDARY')
        baseline=q.json(target.base.prior.OUTPUT);failed=q.json('implementation/p09/evidence/p09-361-text-style-recovery132.v1.json')
        c.require(q.snapshots[target.base.prior.OUTPUT]['sha256']=='bfcece3d80b9a8cf588ca019744537554c51328f401d165c95f30bb8ce8d5c56'
            and q.snapshots['implementation/p09/evidence/p09-361-text-style-recovery132.v1.json']['sha256']=='30bf84adfdb437c1c4f7f00cda02813332106f23b9d4a90748c1b1c684f4e08f',
            'EXACT_PRIOR_RUN_PRODUCT_AND_ORIGINAL_TEXT_FAILURE_RECORDS')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        for name in sorted(target.NEW|target.CHANGED|RETAINED|{target.OFFICIAL}):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_SOURCE_MATCHER_WRITER_PROTECTION_PRODUCT_AND_TEST_PINS_MATCH_PASS')
        target.inverse(q,old,failed)
        all_cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(target.base.TEST)))
        c.require(len(all_cases)==21 and target.RETAINED<={n for n,s in failed['steps'][0]['tests']if s=='ok'},'EXACT_FOUR_UNCHANGED_NEGATIVE_CASES_RETAINED')
        good_step(passed['steps'][0],all_cases-target.RETAINED)
        c.require(len(passed['steps'])==1 and passed['steps'][0]['diagnostics']==[]
            and passed['steps'][0]['bounded_output_observation']['safe_warning_locations']==[],'NO_ERROR_DIAGNOSTICS_OR_COMPILER_WARNINGS')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('source-selector-text-style-replacement/v1','source stage','current stored/product binding',
            'same typed catalog','existing typed character reader','not guessed named-style inheritance',
            'original run and paragraph shells','One edge scan per requested Text atom','every unchanged run reference',
            'hwpml-2011-text-style-static/v9','original v1 through v8 engine and rules','attribute vocabulary, not target behavior',
            'Components131 fails compilation','5 pass and11 fail','no specific code','17 current cases with 616 fresh/final616',
            'Four unchanged negative cases','21 distinct cases','exact Writer rejection','108.485 seconds','28.797 seconds',
            '4.79 seconds','27.219 seconds','1662.26 MiB','5.2172%','29.44%','29.5011%','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_TEXT_AXIS_SOURCE_BOUNDARY_FAILURES_COUNTS_LIMITS_AND_REMAINING_PRODUCT_WORK')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_PRESERVED')
        for marker in('부분 run 글자 모양 core/저장/v1 제품 및 text-style source core 통과',
            'text-style 저장/제품·문단/이름·유효 서식/전체 계약 미완료','고유21개','17pass·616fresh/final616',
            '다음은 이 text-style 후보의 현재 저장/엄격한 제품 요청 연결'):
            c.require(marker in progress,'SOURCE_VERSUS_CURRENT_PRODUCT_AND_REMAINING_STYLE_AXES_EXPLICIT')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 부분 글자 모양 치환 저장과 제품 연결',1)[0]
        for marker in('17pass·616fresh/final616','고유21개','다음은 text-style 후보의 현재 저장/엄격한 제품 요청 연결',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_TEXT_SOURCE_AND_UNCHANGED_PHASE_QUEUE_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-text-style-replacement-v1.md'in q.text(name),'RELATED_STYLE_SOURCE_PRODUCT_PROFILES_LINK_EXACT_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_SOURCE_API_STAYS_INCOMPLETE_WITH_FOUR_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_STYLE_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=17,retained_cases=4,total_distinct_cases=21,tests_reexecuted=False,entire_616_input_set_reaudited=False,
            next_work='Current_stored_and_strict_product_binding_for_text_style_then_paragraph_named_effective_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_STYLE_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
