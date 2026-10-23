"""Scoped code/document closure of72 retained plus17 focused regex cases; no Cargo/test replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_replacement_focused as base
shared,c,a=base.shared,base.c,base.a
recovery=base.prior;core=base.base
OUTPUT='implementation/p09/evidence/p09-361-regex-replacement-sync115.v1.json'
PROFILE='protocol/migrations/p09-source-selector-regex-replacement-v1.md'
DOCS={'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE,
    'protocol/migrations/p09-source-search-index-v1.md','protocol/migrations/p09-source-literal-text-atom-output-v2.md',
    'protocol/migrations/p09-source-review-literal-output-v3.md'}
RETAINED={'crates/hwpx-package/tests/'+n+'.rs'for n in('document_import_search','document_import_search_atom_replacement',
    'document_import_search_review_replacement','document_import_review_selector_replacement','document_import_review_selector','document_import_selector_styles')}
RETAINED|={'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs','crates/hwpx-package/src/document_import/search/replacement/output.rs',
    'crates/hwpx-package/src/text_flow/source_text_span.rs','crates/hwpx-package/src/patch/text_atom_ranges.rs',
    'crates/hwpx-package/tests/support/review_scope_fixture.rs','crates/hwpx-package/tests/support/search_definition_fixture.rs',
    'crates/hwpx-package/tests/support/document_import_field_fixture.rs','crates/hwpx-package/tests/support/review_cell_output_fixture.rs',
    'tools/p09/run_regex_replacement_components.py','tools/p09/run_regex_replacement_recovery.py','tools/p09/run_regex_replacement_focused.py',
    'tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','tools/p09/run_source_note_api_components.py'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_REPLACEMENT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);stopped=q.json(recovery.OUTPUT);failed=q.json(core.OUTPUT);previous=q.json(core.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='478e21869b593aeefd331fc7d115a6d214151e6fdac901a39bec968751ca86eb'
            and passed['state']=='PASS_REGEX_REPLACEMENT_SEVENTY_TWO_RETAINED_SEVENTEEN_FOCUSED_NOT_STORED_PRODUCT_ZERO_WIDTH_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==582 and passed['total_distinct_core_cases']==89
            and passed['new_core_cases']==17 and passed['retained_original_cases']==72,'EXACT_SEVENTEEN_FOCUSED_SEVENTY_TWO_RETAINED_INPUT_CLOSURE')
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='69de98f688e2dbf7caa21fecfdf6b7670658990b5da179d1c81c48364053e083'
            and stopped['error_code']=='STOP_SOURCE_NOTE_API_COMMAND_DEADLINE'and stopped['cleanup'],'COMPILE_DEADLINE_AND_UNCONFIRMED_EXECUTION_NOT_PROMOTED')
        c.require(q.snapshots[core.OUTPUT]['sha256']=='f53fd16a7e66e637f3bdfb9cf9c303ae757f118a1b86280bc6222207fc28459b'
            and failed['state']=='FAILED_REGEX_REPLACEMENT_COMPONENTS'and failed['cleanup'],'ORIGINAL_TWO_FAILURES_PRESERVED')
        c.require(q.snapshots[core.prior.OUTPUT]['sha256']=='4965fe2b5d8e247f4ab7849a7aee4e1e2fb7d2cb980747f85d72cd67a8d383f3','EXACT_PREVIOUS_PRODUCT_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};initial={p['path']:p for p in failed['source_pins']};old={p['path']:p for p in previous['source_pins']}
        for name in sorted(core.NEW|core.CHANGED|RETAINED|{base.FOCUSED}):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_REGEX_CODE_TEST_GUARD_WRITER_AND_FIXTURES_MATCH_FOCUSED_PASS')
        core.inverse(q,old);recovery.budget_inverse(q,initial);recovery.test_inverse(q,initial);expected=recovery.expected(q)
        first=failed['steps'][0];last=passed['steps'][0]
        c.require(len(first['tests'])==88 and {n for n,s in first['tests']if s!='ok'}==recovery.FAILED
            and len([n for n,s in first['tests']if s=='ok'and not n.startswith('regex_replacement::')])==72
            and last['exit_code']==0 and len(last['tests'])==17 and {n for n,s in last['tests']}==expected and all(s=='ok'for n,s in last['tests'])
            and last['diagnostics']==[]and last['panic_locations']==[]and last['safe_error_variants']==[],'ALL_EXPECTED_FOCUSED_CASES_PASS_WITH_RETAINED_OLD_CASES_AND_NO_DIAGNOSTICS')
        for step,mask in((first,1),(stopped['steps'][0],1),(last,4)):
            job=step['owned_job'];limits=job['limits_readback']
            c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']and job['last_job_accounting']['active_processes']==0
                and limits['verified']and limits['affinity_mask']==mask and mask.bit_count()==1 and limits['cpu_hard_cap_machine_percent']==6.25
                and limits['priority_class']==16384 and limits['kill_on_close'],'ALL_ORIGINAL_AND_FOCUSED_JOBS_TERMINAL_WITH_UNCHANGED_ONE_CPU_CAP_AND_PRIORITY')
        c.require(not passed['common_guard_or_other_process_settings_changed']and passed['own_cpu_selection']['selected_cpu_count']==1
            and passed['own_cpu_selection']['selected_mask']==4 and passed['own_cpu_selection']['only_current_verifier_changed'],
            'SEPARATE_SINGLE_CPU_WITHOUT_OTHER_PROCESS_OR_COMMON_GUARD_MUTATION')
        for name in sorted(DOCS):q.pin(name)
        progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md');profile=q.text(PROFILE)
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in('17pass·582fresh/final582','고유89개','NFC capture/템플릿·4종 범위/review 정책·원 atom 출력 core 통과',
            '빈 일치 삽입·전체 계약 미완료','다음은 정규식 캡처 후보의 현재 저장/엄격한 제품 JSON 연결'):
            c.require(marker in progress,'CURRENT_REGEX_CORE_COUNTS_AND_OPEN_PRODUCT_ZERO_WIDTH_BOUNDARY')
        for marker in('source-selector-regex-replacement-candidate/v1','each accepted occurrence','normally1,000,000','exact512-unit boundary',
            'Zero-width insertion is not qualified','captures_iter','No template, query, capture values','mask4','582 fresh/final582',
            'not a new89-case run','test execution unconfirmed','Current stored-service binding and strict product JSON are next'):
            c.require(marker in profile,'PRECISE_CAPTURE_TEMPLATE_WORK_PRESERVATION_REUSE_AND_CURRENT_CORE_BOUNDARY')
        for name in DOCS-{'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',PROFILE}:
            c.require('p09-source-selector-regex-replacement-v1.md'in q.text(name),'RELATED_MATCHER_AND_LITERAL_PROFILES_LINK_ADDITIVE_REGEX_CORE')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 컨트롤 범위 제품 v8',1)[0]
        for marker in('17pass·582fresh/final582','고유89개','100.703초','25.516초','1.44초','23.875초','29.49%','36.2434%','5.1452%',
            'affinity4 단일 bit','빈 일치 삽입','공식158/249','잔여91','P09/A12/A13 OPEN','P10미시작','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_REGEX_CORE_RESOURCES_AND_UNCHANGED_PHASE_GATE_BOUNDARY')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_REPLACEMENT_CODE_DOCUMENT_SYNC_NOT_STORED_PRODUCT_ZERO_WIDTH_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            total_distinct_core_cases=89,current_regex_cases=17,retained_original_cases=72,entire_582_input_set_reaudited=False,tests_reexecuted=False,
            next_work='Current_stored_and_strict_product_binding_of_regex_capture_candidates_then_remaining_full_contract_and_zero_width_insertions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
