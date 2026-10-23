"""Scoped closure of v2 mixed candidates and stored access; no tests, queue or Native replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_text_atom_components as core
import run_stored_literal_text_atom_components as stored
import run_stored_literal_text_atom_recovery as recovery
import run_search_review_text_components as original
shared,c,a=core.shared,core.c,core.a
OUTPUT='implementation/p09/evidence/p09-361-literal-text-atom-sync078.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-text-atom-patch-v1.md','protocol/migrations/p09-literal-replacement-product-request-v1.md',
    'protocol/migrations/p09-source-literal-text-atom-output-v2.md')
RETAINED={'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/fields.rs',
    'crates/hwpx-package/src/document_import/search/extract.rs','crates/hwpx-package/src/document_import/search/scope.rs',
    'crates/hwpx-package/src/patch/leaf_scalar_ranges.rs','crates/hwpx-package/src/patch/text_atom_ranges.rs',
    'crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/text_flow/source_text_span.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/product-cli/src/form_stored_provider.rs',
    'crates/product-cli/src/form_product_request/stored_literal_replacement.rs',core.prior.base.prior.prior.TEST,
    core.prior.base.prior.prior.base.HEADER,'crates/hwpx-package/tests/support/search_definition_fixture.rs'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_ATOM_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_TEXT_ATOM_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior,passed,failed,old_scalar=q.json(core.PRIOR),q.json(recovery.OUTPUT),q.json(stored.OUTPUT),q.json(core.OUTPUT)
        for name,sha in ((core.PRIOR,'46f5b0cbf46024e650f046370b6569e1b20bee686e3e12ad7299a24d89bdbb84'),
            (recovery.OUTPUT,'d824977e51989932c03e16d591f11bd90a40928a713c4cf69fab62b3f58f75c5'),
            (stored.OUTPUT,'aea8bdc4813d41bffb57bb5972b7c9687d08cfe7a40a21fc56aa5264c2c67bfd'),
            (core.OUTPUT,'feb3a50059ad8c85d2c29a1964e378d1e02d48d9749e9362ff5695e2bd24d29b')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_ORIGINAL_ATOM_PATCH_CORE_AND_STORED_FAILURE_RECOVERY_RESULTS')
        # old_scalar is the successfully completed current v2 core result, not the prior patch suite.
        c.require(old_scalar['state']=='PASS_LITERAL_TEXT_ATOM_V2_TWELVE_NEW_TEN_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'
            and old_scalar['cleanup']and old_scalar['fresh_inputs']==old_scalar['final_fresh_hashes']==484
            and old_scalar['total_executed_cases']==22,'EXACT_TWELVE_NEW_TEN_AFFECTED_CORE_CLOSURE')
        c.require(passed['state']=='PASS_STORED_LITERAL_TEXT_ATOM_SIX_NEW_TWENTY_TWO_CORE_RETAINED_NOT_JSON_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==489 and passed['total_executed_cases']==6
            and passed['retained_core_cases']==22 and passed['test_only_permission_name_repaired'],'EXACT_SIX_STORED_PASSES_AND_CORE_NOT_REEXECUTED')
        c.require(failed['state']=='FAILED_STORED_LITERAL_TEXT_ATOM_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['tests']==[] and any('E0433'in x for x in failed['steps'][0]['diagnostics']),'ZERO_TEST_PERMISSION_NAME_COMPILE_FAILURE_PRESERVED')
        tested={p['path']:p for p in passed['source_pins']};core_pins={p['path']:p for p in old_scalar['source_pins']};old={p['path']:p for p in prior['source_pins']}
        for name in sorted(core.NEW|core.CHANGED|stored.NEW|stored.CHANGED|RETAINED):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_V2_CORE_STORED_AND_RETAINED_SOURCE_INPUTS_MATCH_PASS')
        for name in core.NEW|core.CHANGED|RETAINED:c.require(tested[name]==core_pins[name],'CORE_PROOF_READER_SCALAR_AND_V1_PRODUCT_INPUTS_EXACTLY_RETAINED_FOR_STORAGE')
        core.inverse(q,old);stored.inverse(q,core_pins)
        initial={p['path']:p for p in failed['source_pins']};text=q.text(stored.TEST)
        c.require(text.count('artifact_service::ArtifactPermission::Read')==1,'ONLY_ONE_TEST_PERMISSION_TYPE_QUALIFICATION')
        original.inverse(text.replace('artifact_service::ArtifactPermission::Read','ArtifactPermission::Read'),initial[stored.TEST],
            'SIX_STORED_TESTS_UNCHANGED_EXCEPT_ORIGINAL_PERMISSION_NAME_REPAIR')
        new=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(core.TEST)))
        v1=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(core.prior.base.prior.prior.TEST)))
        current={'actual_import::literal_text_atom_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)}
        c.require((len(new),len(v1),len(current))==(12,10,6),'EXACT_TWENTY_EIGHT_CURRENT_TEST_IDENTITIES')
        for step,expected in zip(old_scalar['steps'],(new,v1),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['exit_code']==0 and step['diagnostics']==[] and step['panic_locations']==[],'ALL_TWENTY_TWO_CORE_CASES_PASS_WITHOUT_DIAGNOSTICS')
        step=passed['steps'][0];warning=['warning: function `package` is never used','warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning']
        c.require(len(passed['steps'])==1 and len(step['tests'])==6 and{n for n,s in step['tests']}==current and all(s=='ok'for n,s in step['tests'])
            and step['exit_code']==0 and step['diagnostics']==warning and step['panic_locations']==[],'SIX_STORED_PASSES_ONLY_ORIGINAL_FIXTURE_HELPER_WARNING')
        for step in (*old_scalar['steps'],*failed['steps'],*passed['steps']):
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_CORE_STORED_PASS_AND_FAILED_JOBS_TERMINAL_EMPTY_CLOSED')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'ALL_NINETEEN_P09_SEARCH_ROWS_RETAINED')
        for marker in ('core22+저장6=28개','484 fresh/final484','489 fresh/final489','선택 atom 밖','v2 저장 후보의 원본 소유권 전달',
            'v2 제품 JSON/확장 본문/전체 transaction 미완료'):
            c.require(marker in progress,'PROGRESS_COUNTS_PRECISE_READBACK_AND_PENDING_STRICT_V2_PRODUCT')
        profile=q.text(DOCS[4])
        for marker in ('outside_selected_text_atoms_exact','28 current cases','borrowed','Existing v1 JSON schema','ArtifactPermission',
            'Source API v12','Native011 unapproved/unexecuted','P09/A12/A13 OPEN','P10 not started'):
            c.require(marker in profile,'V2_PROFILE_PRECISE_PRESERVATION_SERVICE_NOT_JSON_OR_GATE')
        for name in DOCS[2:4]:c.require('p09-source-literal-text-atom-output-v2.md'in q.text(name),'PRIOR_PROFILES_LINK_SEPARATE_V2_WITHOUT_WIDENING_V1')
        state=q.text(DOCS[0]).split('> 2026-10-20 P09 이전 혼합 atom 편집 기반',1)[0]
        for marker in ('core22+저장6=28개','484fresh/final484','489fresh/final489','26.547초','121.234초','29.40%',
            '원 실패를 보존','엄격한 v2 제품 JSON','공식158/249','잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_V2_CORE_STORED_RESULTS_RESOURCES_AND_UNCHANGED_NATIVE_GATE')
        for name in ('tools/p09/run_literal_text_atom_components.py','tools/p09/run_stored_literal_text_atom_components.py','tools/p09/run_stored_literal_text_atom_recovery.py'):
            q.pin(name);c.require(q.snapshots[name]==tested[name],'COMPLETED_CORE_AND_STORED_RUNNER_SOURCES_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_LITERAL_TEXT_ATOM_V2_CORE_STORED_DOCUMENT_SYNC_TWENTY_EIGHT_CASES_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,core_cases=22,stored_cases=6,total_current_cases=28,
            original_v1_compiler_writer_and_stored_boundary_bodies_preserved=True,entire_489_input_set_reaudited=False,
            resource_policy_unchanged=True,strict_v2_product_json_or_owned_source_handoff_qualified=False,
            next_work='Explicit_strict_v2_literal_product_JSON_and_owned_source_handoff')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_ATOM_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_ATOM_SYNC_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
