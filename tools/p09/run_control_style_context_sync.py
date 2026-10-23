"""Selected context-fix/doc closure:2 current+24 retained source+26 products, no replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_control_style_context_recovery as recovery
from run_style_replacement_sync import good_step
base=recovery.base
shared,c,a=recovery.shared,recovery.c,recovery.a
OUTPUT='implementation/p09/evidence/p09-361-control-style-context-sync156.v1.json'
PROFILE='protocol/migrations/p09-control-style-context-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-resolved-formatting-v1.md','protocol/migrations/p09-resolved-style-product-v9.md'}
RETAINED={'crates/hwpx-package/src/document_import/search/reviews/selector/resolved_styles.rs',
    'crates/hwpx-package/src/document_import/search/inspection/definitions.rs','crates/hwpx-package/src/text_flow.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/structure.rs',
    'crates/hwpx-package/src/document_import/search/selector.rs','crates/hwpx-package/src/document_import/search/reviews/selector.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search/resolved_styles.rs',
    'crates/product-cli/src/form_product_request/stored_source_search/selector/resolved_styles.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/reference_validation_product/source.rs',
    'tools/p09/run_control_style_context_components.py','tools/p09/run_control_style_context_recovery.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_CONTEXT_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_STYLE_CONTEXT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(recovery.OUTPUT);failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT);observed=q.json(base.OBSERVATION)
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='bc2c563a3074e79bd4d6f7630f99ca5491b2247fbe997ea26ac2cbd66c6fd622'
            and passed['state']=='PASS_CONTROL_CONTEXT_2_REPAIRED_24_RETAINED_26_PRODUCTS_NOT_CASCADE_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==645
            and passed['current_source_cases']==2 and passed['retained_source_cases']==24 and passed['current_product_cases']==26
            and passed['total_executed_cases']==28 and passed['total_distinct_cases']==52
            and not passed['passed24_source_cases_reexecuted']and not passed['unrelated104_products_reexecuted'],
            'EXACT_TWO_REPAIRED_24_RETAINED_AND26_CURRENT_PRODUCTS_WITH_COMPLETE_INPUT_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='3e7a183a9c09988b7d1633795992d6f5d583456692133b85cd2fa7dc478b6f95'
            and failed['state']=='FAILED_CONTROL_STYLE_CONTEXT_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['safe_error_variants']==['Body','Body'],
            'ORIGINAL154_REMAINS_FAILED_NOT_PROMOTED_TO_BATCH_PASS')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='5e421a1580b6b0b0830a685eb7cd0cdcf427d886762a6fe07964a6a4ec33a33d',
            'EXACT_V9_BASELINE_FOR_WHOLE_CORE_AND_TEST_INVERSES')
        c.require(q.snapshots[base.OBSERVATION]['sha256']=='4ff817dd8b25a75839018ca53e232a2a48e32ae16289fcbf6dfe3910a4b984b6'
            and observed['cleanup']and observed['fresh_inputs']==observed['final_fresh_hashes']==89
            and len(observed['observations'])==10 and observed['prepared_fixture_paths']==3 and observed['historical_saved_or_reopened_paths']==7
            and not observed['new_native_attestation']and not observed['precedence_or_hidden_visibility_qualified']
            and observed['totals']==dict(xml_parts=20,paragraphs=35,runs=59,text_elements=52,text_style_references=0,control_style_references=0,
                hidden_explanations=0,named_character_definitions=10,missing_direct_run_references=0,missing_direct_paragraph_references=0),
            'EXACT_TEN_PATH_OBSERVATIONS_NOT_NATIVE_STYLE_OR_VISIBILITY_PROOF')
        pins={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']};negative_pins={p['path']:p for p in failed['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|{base.MODEL}|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==pins[name],'SELECTED_CURRENT_CONTEXT_GUARD_READERS_PRODUCTS_TESTS_AND_RESOURCE_HELPERS_MATCH_PASS')
        recovery.repairs(q,negative_pins);base.inverse(q,old);source,product=base.expected(q)
        retained={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        c.require(len(retained)==24 and source==retained|recovery.SOURCE_CURRENT,'EXACT26_SOURCE_IDENTITIES_WITH24_RETAINED_NOT_RERUN')
        good_step(passed['steps'][0],recovery.SOURCE_CURRENT);good_step(passed['steps'][1],product)
        for step in passed['steps']:c.require(step['diagnostics']==[]and step['bounded_output_observation']['safe_warning_locations']==[],'NO_CURRENT_ERRORS_OR_WARNINGS')
        job=failed['steps'][0]['owned_job'];limits=job['limits_readback']
        c.require(failed['steps'][0]['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0 and limits['verified']and limits['affinity_mask']==4
            and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,'FAILED154_RETAINED_RESULTS_HAVE_TERMINAL_JOB_AND_ORIGINAL_LIMITS')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('not infer a Native inheritance rule','one parent-state map','without per-match XML parsing',
            'foreign attribute is not interpreted','using the existing coverage shape','10 existing paths:3 prepared fixtures and7 historical',
            'Text/control-style references and hidden explanations are all0','Components154 runs26 source cases and records24 passes/two failures',
            'exact original FormImportError::Body','all28 pass with645 fresh/final645','52 distinct cases','not one current52-case run',
            '127.250 seconds','2.984 seconds','0.29 seconds','41.266 seconds','7.64 seconds','1694.93 MiB','5.3198%',
            'CPU44.85%','RAM24.3244%','SEARCH-022 actual source Unicode normalization','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_CONTEXT_SCOPE_ORACLE_CORRECTION_RETAINED_COUNTS_OBSERVATIONS_AND_REMAINING_WORK')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_PRESERVED')
        for marker in('ctrl 문맥 guard 검증','현재28pass·645fresh/final645','고유52개','단일 현재52개가 아니다','SEARCH-022 실제 원본 Unicode 정규화'):
            c.require(marker in progress,'CONTEXT_AND_RETAINED_CURRENT_COUNTS_NOT_FULL_CASCADE_COMPLETION')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 직접 서식 해석 저장과 v9 제품 연결',1)[0]
        for marker in('수정원본2pass+제품26pass·645fresh/final645','고유52개','통과24·무관제품104·공식249',
            'SEARCH-022 실제 원본 Unicode 정규화','공식158/249','잔여91','next165','P09/A12/A13 OPEN',
            '목표ACTIVE','P10미시작','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_CONTEXT_CORRECTION_AND_UNCHANGED_QUEUE_PHASE_NATIVE_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-control-style-context-v1.md'in q.text(name),'RELATED_SOURCE_PRODUCT_PROFILES_LINK_CONTEXT_CORRECTION')
        ref=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        c.require('reference-source-assessment/v12'in ref and 'validation_report: None'in ref
            and all('UnresolvedReferenceStage::'+n in ref for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),'REFERENCE_API_REMAINS_INCOMPLETE')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_STYLE_CONTEXT_CODE_DOCUMENT_SYNC_NOT_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_source_cases=2,retained_source_cases=24,current_product_cases=26,total_distinct_cases=52,tests_reexecuted=False,entire_645_input_set_reaudited=False,
            next_work='SEARCH022_source_Unicode_normalization_while_native_style_semantics_and_styled_MEMO_admission_remain_unresolved')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_STYLE_CONTEXT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples)
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTROL_CONTEXT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
