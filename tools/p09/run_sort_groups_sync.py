"""Selected source16 lineage and documentation closure, no Cargo/old tests/full818 replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_sort_groups_serialization_recovery as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-sync245.v1.json'
DRIVER='tools/p09/run_sort_groups_sync.py'
PROFILE='protocol/migrations/p09-paragraph-sort-groups-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,PROGRESS,'CURRENT_STATE.md',DRIVER}
RETAINED=base.NEW if hasattr(base,'NEW') else base.base.NEW
RETAINED=RETAINED|base.base.CHANGED|{base.DRIVER,base.previous.DRIVER,
    base.base.ROOT[:-3]+'/order.rs',base.base.ROOT[:-3]+'/verify.rs',
    'Cargo.toml','Cargo.lock','crates/hwpx-package/Cargo.toml',
    'crates/hwpx-package/src/patch.rs','crates/hwpx-package/src/patch/sibling_permutation.rs','crates/hwpx-package/src/writer.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/styles/text/output.rs',
    'crates/hwpx-package/tests/source_paragraph_sort.rs',
    'crates/hwpx-package/tests/support/paragraph_sort_splice_inventory.rs'}
OLD_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 원본19·제품20·이동목록/공통 compiler/manifest 신규18개 검증, 다중/중첩·구조적 키·실제 실행/전체 계약 미완료 |'
NEW_ROW='| SEARCH-021 | 텍스트·문단 정렬 | 단일 원본19·제품20·공통연결18과 다중 그룹 원본16개 검증, 새 다중 제품 연결·중첩·구조적 키·실제 실행/전체 계약 미완료 |'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,multigroup_current_stored_or_product_request_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='cbda1142d600e2054606f2d402412ab24521c89c34c725155492649a1376e779'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==818 and passed['total_executed_cases']==16,'EXACT244_SOURCE16_AND818_CLOSURE')
        tested={p['path']:p for p in passed['source_pins']}
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'ALL_SELECTED_SOURCE_MULTIGROUP_AND_ORIGINAL_GUARDS_AND_TESTS_UNCHANGED_SINCE244')
        cases=base.base.expected(q);tools.good_step(passed['steps'][0],cases)
        records=[passed]
        for path,sha in((base.previous.OUTPUT,'01a64bb8cf14acdbfed65f0b6ebbc026f43660ea369769dd61a894e539fd067f'),
                         (base.base.OUTPUT,'cb97054c0c0099657697e0a3c622a5d8c8ce2865b6b393830e5d2d45fcfafed7')):
            failed=q.json(path);c.require(q.snapshots[path]['sha256']==sha and failed['cleanup']and failed['steps'][0]['exit_code']==101
                and not failed['steps'][0]['tests'],'BOTH_ORIGINAL_E0277_COMPILER_FAILURES_RETAINED_NO_FALSE_TEST_PASSES');records.append(failed)
        for record in records:
            job=record['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'ALL_THREE_JOBS_TERMINAL_EMPTY_CLOSED')
        docs=q.json(base.base.DOC_BASE);c.require(q.snapshots[base.base.DOC_BASE]['sha256']=='021d3a52307cea1992b3a53476f38b1307a05c0fc97cf58f48dc6fca7379e113','EXACT239_PREVIOUS_DOC_BASELINE')
        old={p['path']:p for p in docs['source_pins']}
        for name in sorted(DOCS):q.pin(name)
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 문단 정렬의 실제 이동 목록과 공통 계획')
        audit.inverse(current[at:],old['CURRENT_STATE.md'],'ENTIRE_PREVIOUS_CURRENT_STATE_AND_FAILURE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 다중 부모와 다중 part 문단 정렬\n');end=progress.index('## 문단 정렬의 실제 이동 목록과 공통 계획\n',start)
        restored=progress[:start]+progress[end:];c.require(restored.count(NEW_ROW)==1,'ONE_ACCURATE_PARTIAL_SEARCH021_UPDATE')
        audit.inverse(restored.replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_FEATURE_HISTORY_PRESERVED')
        c.require(len(set(re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M)))==19,'ALL19_ORIGINAL_P09_SEARCH_FEATURES_RETAINED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('lower_selector_paragraph_sort_groups_candidate','PackagePath','Serialize','E0277','신규16pass','818fresh/final818',
                'source19/제품20/공통연결21·공식249','138.531','32.970','2.86','31.859','1798.73MiB/5.64557%','62.52%','44.7120%',
                'active0/empty/handle closed','CPU cap6.25%','private8%/stop7%','RAM/commit95%',
                '158/249','잔여91','next165','P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
                c.require(norm(marker)in norm(text),'ACCURATE16_SOURCE_SCOPE_LINEAGE_RESOURCE_AND_REMAINING_BOUNDARIES')
        observation=q.json('implementation/p09/evidence/p09-361-crossref-startup-prerequisites240.v1.json')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-crossref-startup-prerequisites240.v1.json']['sha256']=='1dbf8ae8f642e5628886afcee367a6313f8e9368251a6b9676f67e5ba06db0a7'
            and observation['actual_observation']['failed_prerequisites']==['caller_lifecycle_native_safe']
            and not observation['actual_Hangul_or_COM'],'EXACT240_READONLY_REJECTION_NOT_NATIVE_AUTHORITY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_MULTIGROUP_SOURCE16_DOC_SYNC_NOT_CURRENT_PRODUCT_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_cases_retained=16,actual_cases_reexecuted=0,
            full818_inputs_replayed=False,previous_docs_other_rows_and_original_failures_preserved=True,
            next_work='current_store_strict_multigroup_request_actual_splices_common_compiler_then_nested_structured_keys_and_actual_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
