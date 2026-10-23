"""Selected paragraph source/doc closure:37 retained +1 repaired, no tests or628-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_paragraph_style_fixture_recovery as target
from run_style_replacement_sync import good_step
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-sync143.v1.json'
PROFILE='protocol/migrations/p09-source-paragraph-style-replacement-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-text-style-product-request-v1.md','protocol/migrations/p09-character-style-product-request-v1.md',
    'protocol/migrations/p09-source-definition-style-search-v3.md'}
RETAINED={'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/styles/verify.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/render.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs','crates/hwpx-package/src/id_index.rs',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/document_import/structure/caption_text_batch.rs',
    'crates/hwpx-package/tests/document_import_search_definitions.rs','crates/hwpx-package/tests/document_import_selector_styles.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_paragraph_style_components.py',
    'tools/p09/run_paragraph_style_recovery.py','tools/p09/run_paragraph_style_fixture_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PARAGRAPH_STYLE_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_STYLE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(target.FAILED);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='8d96f12627a043474a009552c0c51ee29f73f9b41c6eb5b62c66afc2cbb9eb91'
            and passed['state']=='PASS_PARAGRAPH_STYLE_ONE_REPAIRED_THIRTY_SEVEN_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==628
            and passed['actual_current_cases']==1 and passed['retained_cases']==37 and passed['total_distinct_cases']==38
            and passed['new_paragraph_style_cases']==20 and passed['affected_original_cases']==18
            and not passed['previous_passed_cases_reexecuted'],'EXACT_ONE_REPAIRED_AND_THIRTY_SEVEN_RETAINED_QUALIFICATION')
        c.require(q.snapshots[target.FAILED]['sha256']=='e1e216f549d24c71c873be0692aa7ca6969c9a003b2f21389aa557ddb1c2d40b'
            and failed['state']=='FAILED_PARAGRAPH_STYLE_COMPONENTS'and failed['cleanup']and failed['steps'][0]['exit_code']==101
            and failed['steps'][0]['safe_error_variants']==['Body'],'ORIGINAL_FAILED_BODY_ADMISSION_RESULT_NOT_PROMOTED_TO_PASS')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='29718112cc55901e2d8e694f918cc20ba9aad78def2137f9d4eb7226bddf089a','EXACT_ORIGINAL_TEXT_PRODUCT_SOURCE_BASELINE')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']};prior_pins={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_PROOF_SCOPE_PROTECTION_TYPED_TARGET_WRITER_AND_TEST_PINS_MATCH_PASS')
        target.previous.original_inverse(q,old)
        text=q.text(base.TEST);c.require(text.count(target.NEW)==1,'ONE_ADMITTED_LOCKED_DESCENDANT_FIXTURE_REPAIR')
        target.audit.inverse(text.replace(target.NEW,target.OLD),prior_pins[base.TEST],'WHOLE_TEST_BODIES_UNCHANGED_EXCEPT_ONE_FAILED_FIXTURE_LINE')
        cases=base.expected(q);retained={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        c.require(len(retained)==37 and cases==retained|{target.CASE}and {n for n,s in failed['steps'][0]['tests']if s!='ok'}=={target.CASE},'EXACT_38_DISTINCT_COMPONENTS_NOT_SINGLE_CURRENT_RUN')
        good_step(passed['steps'][0],{target.CASE})
        job=failed['steps'][0]['owned_job'];limits=job['limits_readback']
        c.require(failed['steps'][0]['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
            and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_FAILED_RUN_RETAINED_TESTS_HAVE_TERMINAL_OWNED_JOB_AND_UNCHANGED_LIMITS')
        for step in(failed['steps'][0],passed['steps'][0]):
            warnings=step['bounded_output_observation']['safe_warning_locations']
            c.require(len(warnings)==2 and {(w['path'],w['line'],w['kind'],tuple(w['symbols']))for w in warnings}=={
                ('crates/hwpx-package/tests/support/review_scope_fixture.rs',5,'dead_code',('package',)),
                ('crates/hwpx-package/tests/support/review_scope_fixture.rs',6,'dead_code',('with_body',))},'ONLY_TWO_UNCHANGED_ORIGINAL_FIXTURE_WARNINGS_PRESERVED')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('source-selector-paragraph-style-replacement/v1','WholeMatchedParagraphWithinScope','not current stored/product execution',
            'exactly PARA','CHAR, unknown/missing type','same owned catalog pass','without cloning/re-resolving',
            "whole indexed extent",'nextStyle is not inheritance','unqueried locked descendant','Protection precedes no-op elimination',
            '3N element visits','outside selected attribute edits remain exact','Components140 fails compilation','passes37 of38',
            '1 pass,628 fresh/final628','38 distinct cases, not a single current38-case run','two unchanged fixture dead-code warnings',
            '85.218 seconds','4.578 seconds','0.12 seconds','2.125 seconds','574.51 MiB','1.8032%','47.16%','28.4418%',
            'Next is current stored and strict product binding','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_PARAGRAPH_EXTENT_AXIS_PRESERVATION_FAILURES_COUNTS_WARNINGS_AND_REMAINING_BOUNDARY')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_SEARCH_ROWS_PRESERVED')
        for marker in('문단/이름 스타일 source core 통과','문단 축 저장/제품·유효 서식/전체 계약 미완료','고유38개',
            '1pass·628fresh/final628','다음은 두 문단 축의 현재 저장/엄격한 제품 요청 연결'):
            c.require(marker in progress,'PARAGRAPH_SOURCE_COMPLETION_NOT_CURRENT_PRODUCT_OR_FULL_STYLE')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 text-style 치환 저장과 제품 연결',1)[0]
        for marker in('1pass·628fresh/final628','고유38개','다음은 이 두 문단 축의 현재 저장/엄격한 제품 요청 연결',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_PARAGRAPH_SOURCE_AND_UNCHANGED_QUEUE_PHASE_NATIVE_STATUS')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-paragraph-style-replacement-v1.md'in q.text(name),'RELATED_SOURCE_AND_PRODUCT_PROFILES_LINK_PARAGRAPH_BOUNDARY')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),'REFERENCE_SOURCE_API_REMAINS_INCOMPLETE')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_PARAGRAPH_STYLE_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=1,retained_cases=37,total_distinct_cases=38,known_fixture_dead_code_warnings=2,tests_reexecuted=False,entire_628_input_set_reaudited=False,
            next_work='Current_stored_and_strict_product_binding_for_paragraph_axes_then_effective_style_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PARAGRAPH_STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PARAGRAPH_STYLE_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
