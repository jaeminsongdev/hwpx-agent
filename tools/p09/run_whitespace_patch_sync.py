"""Selected typed-whitespace foundation/source/docs closure; no43-case/Cargo/693-input replay."""
import json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_patch_strengthening as target
base=target.base
shared,c,a=target.shared,target.c,target.a
OUTPUT='implementation/p09/evidence/p09-361-whitespace-patch-sync183.v1.json'
PROFILE='protocol/migrations/p09-whitespace-atom-patch-v1.md'
DOCS={PROFILE,'CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md','protocol/migrations/p09-width-product-request-v1.md'}
RETAINED={'crates/hwpx-package/tests/patch_text_atom_ranges.rs','crates/hwpx-package/tests/patch_leaf_scalar_ranges.rs',
    'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
    'crates/hwpx-package/src/patch/leaf_scalar_ranges.rs','crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/preserving_xml.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/unicode/plan.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs',
    'crates/product-cli/src/reference_validation_product/source.rs','tools/p09/run_whitespace_patch_components.py',
    'tools/p09/run_whitespace_patch_strengthening.py','tools/p09/conservative_maintenance.py','tools/p09/owned_sql_job.py','Cargo.lock','Cargo.toml'}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_PATCH_SYNC_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_PATCH_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);previous=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='8303bfcd1b3456a0f019b939c718ff9967947b42ee099603b6285da0b60f6350'
            and passed['state']=='PASS_WHITESPACE2_STRENGTHENED41_RETAINED_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==693 and passed['current_cases']==2 and passed['retained_cases']==41
            and passed['total_distinct_cases']==43 and passed['production_unchanged_after181']and not passed['unchanged41_cases_reexecuted'],
            'EXACT_TWO_CURRENT41_RETAINED_AND693_INPUT_CLOSURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='25377b3cccff818059d57940c4f2badaa0470d81832857e3631c086fa51f374f'
            and previous['state']=='PASS_WHITESPACE_PATCH24_RANGE19_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE'and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==692 and previous['total_executed_cases']==43,'EXACT_ORIGINAL181_43_PASSES_AND_INPUT_CLOSURE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='37e2065b5df76f9ff8732911e647e1d563ef0b720fe827f298b5543c562ce41c','EXACT_PRIOR178_ORIGINAL_PATCH_ENGINE_BASELINE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']};earlier={p['path']:p for p in previous['source_pins']}
        for name in sorted(base.NEW|base.CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_CURRENT_PATCH_SOURCE_OLD_GUARDS_TESTS_AND_LIMITS_MATCH_PASS182')
        base.inverse(q,old);target.repair(q,earlier);cases=base.expected(q);base.good_step(previous['steps'][0],cases);base.good_step(passed['steps'][0],target.CASES)
        c.require(len(cases-target.CASES)==41 and passed['original_patch_engine_and_all_old_range_bodies_inverse_verified'],'EXACT43_IDENTITIES_AND_ORIGINAL_ENGINE_BODY_PRESERVATION')
        for name in sorted(DOCS):q.pin(name)
        profile=q.text(PROFILE);progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        latest=q.text('CURRENT_STATE.md').split('> 2026-10-20 P09 ACTIVE 최신 전각 반각 변환 저장과 제품 연결',1)[0]
        for marker in('ReplaceWhitespaceAtomRanges','WhitespaceAtomRangeReplacement','White_Space25개','19개','E0308',
            '수정2pass·693fresh/final693','고유43개','기존제품218·공식249','117.937','29.453','3.77','1713.75MiB',
            '92.063','3.188','0.14','575.36MiB','37.70%','P09/A12/A13 OPEN','Native011 미승인/미실행'):
            c.require(marker in profile,'PRECISE_TYPED_PATCH_ONLY_BOUNDARIES_COUNTS_RESOURCES_AND_OPEN_NATIVE_GATE')
        c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19 and
            '| SEARCH-023 | 공백·탭·줄바꿈 정규화 | 별도 typed whitespace/control patch 신규24+영향19=고유43개 확인, 원본 정책/선택/보호 compiler·저장/제품/전체 계약 미완료 |'in progress,
            'ALL19_ROWS_WITH_PATCH_FOUNDATION_NOT_A_COMPLETED_WHITESPACE_SOURCE_COMPILER')
        for marker in('693fresh/final693','고유43개','다음 접근허용 불필요 작업은 SEARCH-023 원본 정규화 정책','공식158/249',
            'P09/A12/A13 OPEN','목표ACTIVE','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in latest,'LATEST_STATE_PATCH_FOUNDATION_AND_UNCHANGED_PRODUCT_NATIVE_AND_PHASE_BOUNDARIES')
        c.require('p09-whitespace-atom-patch-v1.md'in q.text('protocol/migrations/p09-width-product-request-v1.md'),'PREVIOUS_WIDTH_PRODUCT_LINKS_DISTINCT_WHITESPACE_FOUNDATION')
        q.pin(Path(__file__).absolute().relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE_PATCH_SELECTED_DOCS_SYNC_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_patch_cases=24,affected_range_cases=19,total_distinct_cases=43,source693_or_Cargo_or_tests_reexecuted=False,
            next_work='SEARCH023_original_source_whitespace_policy_selection_protection_compiler_and_readback_then_current_store_product_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_PATCH_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WHITESPACE_PATCH_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
