"""Selected style source/document closure:19 current +40 retained, no test or604-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_replacement_target as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-style-replacement-sync128.v1.json'
PROFILE='protocol/migrations/p09-source-character-style-replacement-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-review-selector-style-core-v1.md','protocol/migrations/p09-source-definition-style-search-v3.md',
    'protocol/migrations/p09-regex-insertion-product-request-v2.md'}
RETAINED={'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/replacement.rs',
    'crates/hwpx-package/src/document_import/search/replacement/output.rs','crates/hwpx-package/src/document_import/search/reviews/selector.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/catalog.rs','crates/hwpx-package/src/patch/leaf_scalar_ranges.rs',
    'crates/hwpx-package/tests/document_import_search_definitions.rs','crates/hwpx-package/tests/document_import_selector_styles.rs',
    'crates/hwpx-package/tests/document_import_search_review_replacement.rs','crates/hwpx-package/tests/patch_text_atom_ranges.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_style_replacement_components.py','tools/p09/run_style_replacement_target.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py','tools/p09/bounded_process_progress.py'}


def good_step(step,names):
    c.require(step['exit_code']==0 and {n for n,s in step['tests']}==names and len(step['tests'])==len(names)and all(s=='ok'for n,s in step['tests'])
        and step['panic_locations']==[]and step['safe_error_variants']==[]and all(d.startswith('warning:')for d in step['diagnostics']),
        'EXACT_COMPLETED_TEST_IDENTITIES_NO_FAILURES_IGNORES_OR_ERROR_DIAGNOSTICS')
    job=step['owned_job'];limits=job['limits_readback']
    c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
        and limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384 and limits['kill_on_close'],
        'ORIGINAL_ONE_CPU2_HARD_CAP_PRIORITY_AND_TERMINAL_OWNED_JOB')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_REPLACEMENT_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_REPLACEMENT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);initial=q.json(base.OUTPUT);passed=q.json(target.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='9e8ca0a778f97c7aa43118ae9b897616dc7cdb650414a51ee4f8d01d9737192c'
            and initial['state'].startswith('PASS_')and initial['cleanup']and initial['fresh_inputs']==initial['final_fresh_hashes']==603 and initial['total_executed_cases']==58,
            'EXACT_INITIAL_EIGHTEEN_NEW_FORTY_ORIGINAL_STYLE_PASSES_AND_COMPLETE_INPUT_CLOSURE')
        c.require(q.snapshots[target.OUTPUT]['sha256']=='d2eec58ff9c8fbd2c73d929c4fd8889c842e406434d23916dbf3e72cd17bd75c'
            and passed['state'].startswith('PASS_')and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==604
            and passed['actual_current_cases']==19 and passed['retained_original_cases']==40 and passed['total_distinct_cases']==59,
            'EXACT_NINETEEN_CURRENT_FORTY_RETAINED_NOT_SINGLE_CURRENT_FIFTY_NINE_CASE_RUN')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in initial['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_SOURCE_PROOF_MATCHER_RENDER_READBACK_GUARDS_FIXTURES_AND_TESTS_MATCH_PASS')
        target.inverse(q,old)
        c.require(initial['original_common_code_and_test_bodies_inverse_verified']and passed['original_matcher_inverse_outside_private_typed_anchor_index']
            and passed['target_anchor_from_same_original_typed_catalog_not_extra_header_scan']and not passed['previous_original_cases_reexecuted'],
            'ORIGINAL_MATCHER_REVIEW_PATCH_AND_TYPED_TARGET_PROVENANCE_CHECKS_PRESERVED')
        current={'style_replacement::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))}
        retained={n for n,s in initial['steps'][0]['tests']if not n.startswith('style_replacement::')and s=='ok'}
        c.require(len(current)==19 and len(retained)==40,'EXACT_CURRENT_AND_RETAINED_TEST_IDENTITIES');good_step(passed['steps'][0],current)
        good_step(initial['steps'][0],retained|{n for n,s in initial['steps'][0]['tests']if n.startswith('style_replacement::')})
        warnings=passed['steps'][0]['bounded_output_observation']['safe_warning_locations']
        c.require(len(warnings)==2 and {(w['path'],w['line'],w['kind'],tuple(w['symbols']))for w in warnings}=={
            ('crates/hwpx-package/tests/support/review_scope_fixture.rs',5,'dead_code',('package',)),
            ('crates/hwpx-package/tests/support/review_scope_fixture.rs',6,'dead_code',('with_body',))},'ONLY_TWO_UNCHANGED_ORIGINAL_FIXTURE_DEAD_CODE_WARNINGS_RECORDED')
        for name in sorted(DOCS):q.pin(name)
        flat=' '.join(q.text(PROFILE).split())
        for marker in('source-selector-character-style-replacement/v1','not completion','partial runs','one definition import',
            'same typed catalog','not widened','run shells','original in-scope namespaces','charTcId','including noops',
            'Nested selected hidden/MEMO/table/note runs','no overlapping byte edits','every original point',
            'cumulative compiled-byte limits','58 total,603 fresh/final603','only19 affected style cases','604 fresh/final604',
            '59 distinct component cases','two compiler warnings','107.500 seconds','30.359 seconds','5.42 seconds','28.844 seconds',
            '1659.40 MiB','5.2083%','54.53%','35.5320%','current stored-service and strict product-request binding',
            'Paragraph/named/text-style replacement','unapproved/unexecuted'):
            c.require(marker.lower()in flat.lower(),'PRECISE_PARTIAL_STYLE_TARGET_PRESERVATION_COUNTS_WARNINGS_RESOURCES_AND_REMAINING_CONTRACT')
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_SEARCH_ROWS_RETAINED')
        for marker in('부분 run 글자 모양 참조·4범위/review core 통과','19pass·604fresh/final604','고유59개',
            '저장/제품·문단/이름/text-style·유효 서식/전체 계약 미완료','다음은 부분 글자 모양 후보의 현재 저장/엄격한 제품 연결'):
            c.require(marker in progress,'PRECISE_SOURCE_ONLY_STYLE_ROW_AND_NEXT_PRODUCT_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-character-style-replacement-v1.md'in q.text(name),'RELATED_SEARCH_AND_PREVIOUS_PRODUCT_PROFILES_LINK_PARTIAL_STYLE_SOURCE')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 빈 일치 정규식 저장과 제품 연결',1)[0]
        for marker in('19pass·604fresh/final604','고유59개','다음은 이 부분 글자 모양 후보의 현재 저장 서비스와 엄격한 제품 요청 연결',
            '공식158/249','잔여91','next165','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_SOURCE_STYLE_STATUS_AND_UNCHANGED_QUEUE_PHASE_GATE')
        source=q.text('crates/product-cli/src/reference_validation_product/source.rs');c.require('reference-source-assessment/v12'in source and 'validation_report: None'in source
            and all('UnresolvedReferenceStage::'+n in source for n in('OtherTargetFamilies','ReferenceEdgeSemantics','CompleteAuxiliaryState','DocumentFlow')),
            'REFERENCE_SOURCE_API_REMAINS_INCOMPLETE_WITH_FOUR_UNRESOLVED_STAGES')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_REPLACEMENT_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_style_cases=19,retained_original_cases=40,total_distinct_cases=59,known_fixture_dead_code_warnings=2,
            entire_604_input_set_reaudited=False,tests_reexecuted=False,
            next_work='Current_stored_and_strict_product_binding_of_partial_character_style_candidates_then_paragraph_named_effective_style_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
