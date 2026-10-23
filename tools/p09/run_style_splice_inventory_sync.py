"""Selected final-splice model/product/doc closure; no50-case, Cargo or737-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_style_splice_inventory_recovery as target
base=target.base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-style-splice-inventory-sync211.v1.json'
DRIVER='tools/p09/run_style_splice_inventory_sync.py'
PROFILE='protocol/migrations/p09-style-splice-inventory-v1.md'
COMMON='protocol/migrations/p09-common-search-mutation-dispatch.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,COMMON,PROGRESS,'CURRENT_STATE.md'}
DOC_BASE='implementation/p09/evidence/p09-361-search-mutation-dispatch-sync208.v1.json'
RETAINED=base.NEW|base.CHANGED|{base.OLD_STYLE,base.OLD_TEXT}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_INVENTORY_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_SPLICE_INVENTORY_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        compiled_operation_route_full_transaction_or_gate_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);failed=q.json(target.FAILED);docbase=q.json(DOC_BASE)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='e2c57b62d8e165d39709e1aaa60bceeb40ad9dfa5884190b6f7f05c3db67a974'
            and passed['state']=='PASS_STYLE_SPLICE_INVENTORY12_AFFECTED38_NOT_COMPILED_OPERATION_NATIVE_TRANSACTION_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==737 and passed['total_executed_cases']==50,'EXACT210_NEW12_AFFECTED38_AND_FRESH_CLOSURE')
        c.require(q.snapshots[target.FAILED]['sha256']=='cb2d80233f4634c37407640ac84ccec6dd1862816b698db9841ce61ab9bdf38e'
            and failed['cleanup']and failed['steps'][0]['tests']==[]and failed['steps'][0]['exit_code']==101,'ORIGINAL209_COMPILER_FAILURE_AND_TEST0_PRESERVED')
        c.require(q.snapshots[DOC_BASE]['sha256']=='2e484f01e4cf8591c1de0d7dd460a16d1705ca2ee62fbd213fb22c76c61b12d2'
            and docbase['cleanup'],'EXACT208_PREVIOUS_DOCS_AND_HISTORY')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_SOURCE_AND_PRODUCT_INVENTORY_PATHS_DECLARED_BY210')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_LIVE_SPLICE_SOURCE_PRODUCT_AND_TESTS_MATCH210')
        cases=base.expected(q);tools.good_step(passed['steps'][0],cases)
        base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        text=q.text(base.TEST);restored=text.replace(target.NEW_SIGNATURE,target.OLD_SIGNATURE).replace(target.OLD_ZIP,'').replace(target.NEW_ACCESS,target.OLD_ACCESS).replace(target.NEW_END,target.OLD_END)
        audit.inverse(restored,{p['path']:p for p in failed['source_pins']}[base.TEST],'ENTIRE209_NEW_TEST_REQUIREMENTS_PRESERVED_EXCEPT_PUBLIC_READER_AND_GENERIC_REPOSITORY_HELPERS')
        for name in sorted(DOCS):q.pin(name)
        q.pin(DRIVER);previous={p['path']:p for p in docbase['source_pins']}
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 공통 후보 dispatcher 연결')
        audit.inverse(current[at:],previous['CURRENT_STATE.md'],'ENTIRE_OLD_CURRENT_STATE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 서식 후보의 실제 최종 splice 목록\n');end=progress.index('## 공통 후보준비 dispatcher 연결\n',start)
        restored=(progress[:start]+progress[end:]).replace(
            '| SEARCH-008 | 서식 치환 | 부분 run/text-style·문단/이름 스타일 core/저장/제품과 두 글자 축의 실제 최종 splice 목록 신규12·영향38 검증, operation compiler/유효 서식/전체 계약 미완료 |',
            '| SEARCH-008 | 서식 치환 | 부분 run/text-style·문단/이름 스타일 core·현재 저장/엄격한 v1 제품 통과, 유효 서식/전체 계약 미완료 |')
        audit.inverse(restored,previous[PROGRESS],'ALL_OTHER_SEARCH_ROWS_EXISTING_EVIDENCE_AND_FAILURE_HISTORY_PRESERVED')
        common=q.text(COMMON);audit.inverse(common[:common.index('\n## 서식 후보의 실제 splice 전달\n')],previous[COMMON],'ENTIRE_PREVIOUS_COMMON_DISPATCH_CONTRACT_AND_FAILURE_HISTORY_PRESERVED')
        rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(rows)==len(set(rows))==19,'EXACT19_P09_SEARCH_ROWS')
        for text in(current[:7500],progress[start:end],q.text(PROFILE)):
            for marker in('source-style-splice-inventory/v1','209','210','737fresh/final737','50pass','최종','fragment','최종 head'):
                c.require(norm(marker)in norm(text),'DOCS_ACTUAL_FINAL_SPLICE50_AND_CURRENT_CONSUMER_BOUNDARY')
        profile=norm(q.text(PROFILE))
        for marker in('source_start','source_end','replacement_sha256','replacement_bytes','legacy_receipt_sha256','canonical_sha256',
            '4096','8MiB','bounded streaming','with_verified_splice_inventory','CompiledOperationPlan','158/249','잔여91','next165',
            'P09/A12/A13 OPEN','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','임의 첫 문단'):
            c.require(norm(marker)in profile,'EXACT_CURRENT_INVENTORY_FIELDS_LIMITS_FRESH_ACCESS_NOT_OPERATION_OR_GATE')
        q.finish();guard.check(force=True);row.update(state='PASS_SELECTED_STYLE_SPLICE_INVENTORY_DOC_SYNC_NOT_COMPILED_OPERATION_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases_retained=12,affected_cases_retained=38,full737_inputs_replayed=False,
            original209_compile_failure_and_previous_doc_history_preserved=True,
            next_work='source_anchor_to_actual_operation_targets_compiler_then_real_route_manifest_durable_commit_CAS_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_INVENTORY_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
