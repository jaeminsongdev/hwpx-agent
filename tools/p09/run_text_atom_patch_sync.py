"""Scoped atom-patch result/source/document closure, no Cargo or queue replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_atom_patch_recovery as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-text-atom-patch-sync074.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-source-text-atom-patch-v1.md')
RETAINED={base.base.prior.LOWER,base.base.prior.prior.TEST,base.base.prior.prior.PRODUCT,
    base.base.prior.STORED,'crates/product-cli/src/form_product_request/stored_literal_replacement.rs',
    base.base.prior.prior.scalar.TEST,base.base.prior.prior.base.HEADER,'crates/hwpx-package/tests/support/search_definition_fixture.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_ATOM_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_ATOM_PATCH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed,failed,prior=q.json(base.OUTPUT),q.json(base.FAILED),q.json(base.base.PRIOR)
        for name,sha in ((base.OUTPUT,'46f5b0cbf46024e650f046370b6569e1b20bee686e3e12ad7299a24d89bdbb84'),
            (base.FAILED,'da4d29646be723868f2a93feef7ed068875cccd22f1dce8d01e9c1b8828e66ac'),
            (base.base.PRIOR,'cacd9b8ef647792299c661d3a5f107fa9b5e516b081e8485c653f4e6900449df')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_ATOM_RECOVERY_FAILURE_AND_PREVIOUS_PRODUCT_RESULTS')
        c.require(passed['state']=='PASS_TEXT_ATOM_PATCH_TWO_RECOVERED_NINE_AFFECTED_EIGHT_RETAINED_NOT_SEARCH_COMPILER_PRODUCT_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==481 and passed['total_executed_cases']==11
            and passed['prior_new_passes_preserved']==8 and passed['distinct_validated_cases']==19,'EXACT_ELEVEN_CURRENT_EIGHT_RETAINED_NINETEEN_DISTINCT_ATOM_RESULTS')
        c.require(failed['state']=='FAILED_TEXT_ATOM_PATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_TWO_FIXTURE_FAILURES_REMAIN_FAILED')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in prior['source_pins']}
        for name in sorted(base.base.NEW|base.base.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_ATOM_PATCH_AND_RETAINED_COMPILER_PRODUCT_INPUTS_MATCH_PASS')
        base.base.inverse(q,old)
        for name in RETAINED:c.require(tested[name]==old[name],'V1_LITERAL_COMPILER_PRODUCT_AND_OLD_SCALAR_TESTS_RETAINED_EXACT')
        new=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.base.TEST)))
        scalar=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.base.prior.prior.scalar.TEST)))
        before=dict(failed['steps'][0]['tests'])
        c.require(len(new)==10 and len(scalar)==9 and set(before)==new and {n for n,s in before.items()if s=='FAILED'}==base.RECOVERED
            and sum(s=='ok'for s in before.values())==8,'EXACT_NEW_AND_RETAINED_ATOM_CASE_IDENTITIES')
        for step,expected in zip(passed['steps'],(base.RECOVERED,scalar),strict=True):
            c.require(len(step['tests'])==len(expected)and {n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['exit_code']==0 and step['diagnostics']==[] and step['panic_locations']==[],'ELEVEN_CURRENT_CASES_PASS_WITHOUT_DIAGNOSTICS')
        for step in (*failed['steps'],*passed['steps']):
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_ATOM_PASS_AND_FAILED_JOBS_TERMINAL_EMPTY_CLOSED')
        for marker in ('other_eight_case_and_shared_fixture_bodies_unchanged','original_reader_value_policy_and_patch_bodies_inverse_verified',
            'combined_scalar_intent_budgets_enforced','failed_source_result_preserved'):
            c.require(passed[marker]is True,'RECOVERY_PRESERVES_EIGHT_TESTS_READER_BUDGET_AND_FAILURE_BOUNDARIES')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_SEARCH_ROWS_RETAINED')
        for marker in ('고유19개','481 fresh/final481','수정2개+미실행 영향 scalar9개','기존 문자열 치환 compiler/저장/제품 v1의 혼합 leaf 거부는 유지',
            '별도 v2 문자열 치환 후보 compiler'):
            c.require(marker in progress,'ATOM_PROGRESS_SUCCESS_COUNTS_AND_PENDING_COMPILER_JOIN')
        profile=q.text(DOCS[2])
        for marker in ('19 distinct validated cases,481 fresh/final481','ReplaceLeafScalarRanges retains','charStyleIDRef',
            'Existing compiler/stored/product v1 still rejects mixed leaves','P09/A12/A13 OPEN','P10 not started','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'ATOM_PROFILE_ADDITIVE_COORDINATES_COMPATIBILITY_AND_GATE_BOUNDARIES')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 엄격한 문자열 치환 제품 요청',1)[0]
        for marker in ('고유19개','481fresh/final481','26.89%','26.6786%','5.0086%','원 실패는 보존','별도 v2 치환 후보',
            '공식158/249','잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_ATOM_EVIDENCE_RESOURCES_AND_UNCHANGED_GATE_BOUNDARY')
        for name in ('tools/p09/run_text_atom_patch_components.py','tools/p09/run_text_atom_patch_recovery.py'):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'ACTUAL_ATOM_COMPONENT_RUNNERS_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_ATOM_PATCH_CODE_DOCUMENT_SYNC_NINETEEN_DISTINCT_NOT_SEARCH_COMPILER_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_executed_cases=11,retained_cases=8,distinct_validated_cases=19,
            original_reader_scalar_decoder_and_v1_literal_paths_preserved=True,entire_481_input_set_reaudited=False,
            resource_policy_unchanged=True,full_mixed_literal_compiler_or_product_qualified=False,
            next_work='Explicit_v2_literal_candidate_compiler_preserving_controls_and_output_atom_readback')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_ATOM_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_ATOM_SYNC_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
