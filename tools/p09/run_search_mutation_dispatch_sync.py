"""Selected current common-dispatch/doc closure; no Cargo,26-case or733-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_search_mutation_budget_strengthening as target
recovery,base=target.recovery,target.base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-search-mutation-dispatch-sync208.v1.json'
DRIVER='tools/p09/run_search_mutation_dispatch_sync.py'
PROFILE='protocol/migrations/p09-common-search-mutation-dispatch.md'
NUMBER_PROFILE='protocol/migrations/p09-number-control-product-request-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,NUMBER_PROFILE,PROGRESS,'CURRENT_STATE.md'}
LITERAL='crates/product-cli/src/form_product_request/stored_literal_replacement'
FAMILIES={LITERAL+'.rs'}|{LITERAL+'/'+n+'.rs'for n in('atoms','review','selector','regex','regex/insertions','styles','text_styles','paragraph_styles',
    'unicode','unicode/matches','case','width','whitespace','controls','number_controls')}
RETAINED=base.NEW|base.CHANGED|FAMILIES|{recovery.DRIVER,target.DRIVER}
DOC_BASE='implementation/p09/evidence/p09-361-number-control-product-sync204.v1.json'
INTRO='기존 치환·변환16개 스키마는 아래 공통 후보준비 dispatcher에도 연결했다. 실제 저장 트랜잭션과 실행 자격은 별도다.\n'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_DISPATCH_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_DISPATCH_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        full_search_transaction_or_gate_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed=q.json(target.OUTPUT);retried=q.json(recovery.OUTPUT);failed=q.json(base.OUTPUT);docbase=q.json(DOC_BASE)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='ad44c36f7a5fc14c10e3156f584dba9f7be120a3be0ca04eab1dd6485a003f57'
            and passed['state']=='PASS_COMMON_DISPATCH_BUDGET_POSITIVE_AND_TIGHT_CONTROLS_NOT_TRANSACTION_NATIVE_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==733,'EXACT207_ONE_AFFECTED_BUDGET_PASS_AND_FRESH_CLOSURE')
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='ec970564f5398b801555833e58c0b20e6ec7dd573fe559b064de2100a4115c94'
            and retried['state']=='PASS_COMMON_DISPATCH_RETAINED16_RECOVERED10_NOT_TRANSACTION_NATIVE_OR_GATE'
            and retried['cleanup']and retried['fresh_inputs']==retried['final_fresh_hashes']==732,'EXACT206_TEN_RECOVERED_AND_SIXTEEN_RETAINED')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='38c9ea9baa45d7a83eee1b6088a7991796cbae071e05cb241fec62ee2cd6aebf'
            and failed['state']=='FAILED_SEARCH_MUTATION_DISPATCH_COMPONENTS'and failed['cleanup'],'ORIGINAL205_FAILURE_NOT_PROMOTED_OR_OVERWRITTEN')
        c.require(q.snapshots[DOC_BASE]['sha256']=='7d707eebb8ec711c6a9c824e68e2ed4928ba00080f418e25ee97b086ce63b09a'
            and docbase['cleanup'],'EXACT204_PREVIOUS_DOCS_AND_HISTORY')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_COMMON_AND_ALL16_FAMILY_FILES_DECLARED_BY207')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_LIVE_DISPATCH_FAMILIES_BUDGETS_GUARDS_AND_TESTS_MATCH207')
        cases=base.expected(q);initial=failed['steps'][0]['tests'];oldpass={n for n,s in initial if s=='ok'};oldfail={n for n,s in initial if s!='ok'}
        c.require(len(oldpass)==16 and len(oldfail)==10 and oldpass|oldfail==cases and target.CASE in oldpass,'COMPLETE_DISTINCT26_CASE_IDENTITIES_WITH_ONE_AFFECTED_PASS_RECHECKED')
        tools.good_step(retried['steps'][0],oldfail);tools.good_step(passed['steps'][0],{target.CASE})
        base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        old={p['path']:p for p in failed['source_pins']};text=q.text(base.TEST)
        c.require(text.count(target.ADDITION)==1,'ONE_BUDGET_POSITIVE_CONTROL_ADDITION')
        audit.inverse(text.replace(target.ADDITION,'').replace(recovery.SOURCE_ADDITION,'').replace(recovery.NEW_END,recovery.OLD_END),old[base.TEST],
            'ALL_INITIAL26_TESTS_RESTORED_BY_ONLY_DECLARED_FIXTURE_DEBUG_AND_POSITIVE_BUDGET_ADDITIONS')
        audit.inverse(q.text(base.MODEL).replace(recovery.DEBUG_ADDITION,''),old[base.MODEL],'ALL_DISPATCH_EXECUTION_BODIES_MATCH205_EXCEPT_REDACTED_DEBUG')
        for name in sorted(DOCS):q.pin(name)
        q.pin(DRIVER);previous={p['path']:p for p in docbase['source_pins']}
        current=q.text('CURRENT_STATE.md');original=current.index('> 2026-10-20 P09 ACTIVE 최신 자동번호 재시작 치환 저장과 제품 연결')
        audit.inverse(current[original:],previous['CURRENT_STATE.md'],'ENTIRE_OLD_CURRENT_STATE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 공통 후보준비 dispatcher 연결\n');end=progress.index('## P09 검색 기능의 완료 경계\n',start)
        restored=(progress[:start]+progress[end:]).replace(INTRO,'').replace(
            '공통 후보준비 이후 실제 실행 dispatcher와 저장·CAS·영속 멱등 실행·게시 및 요구되는 Native 증거가 남는다.',
            '전체 operation dispatcher와 저장·CAS·멱등 실행·게시 및 요구되는 Native 증거가 남는다.').replace(
            '실제 저장/commit/CAS/영속 멱등/실행 dispatcher/게시','실제 저장/commit/CAS/영속 멱등/dispatcher/게시')
        audit.inverse(restored,previous[PROGRESS],'ALL_OLD_SEARCH_ROWS_FUNCTIONAL_EVIDENCE_AND_FAILURE_HISTORY_PRESERVED')
        number=q.text(NUMBER_PROFILE);audit.inverse(number[:number.index('\n## 공통 준비 진입점 연결\n')],previous[NUMBER_PROFILE],'ENTIRE_ORIGINAL203_NUMBER_PRODUCT_CONTRACT_AND_HISTORY_PRESERVED')
        rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(rows)==len(set(rows))==19,'ORIGINAL19_P09_SEARCH_FAMILIES_UNCHANGED')
        for text in (current[:7500],progress[start:end],q.text(PROFILE)):
            for marker in ('16','26','205','206','207','733fresh/final733','RouteUnqualified','실제','dispatcher'):
                c.require(norm(marker)in norm(text),'DOCS_COMMON_PREPARATION26_AND_UNFINISHED_EXECUTION_BOUNDARY')
        profile=norm(q.text(PROFILE))
        for marker in ('SearchMutationReceiptRef','prepare_json_with_search_limits','ReferenceAuxiliaryLimits','16KiB','2MiB','다른25개',
            '실제 저장 트랜잭션','158/249','잔여91','next165','P09/A12/A13 OPEN','Native011 미승인/미실행','CROSSREF8종 NOT_RUN'):
            c.require(norm(marker)in profile,'EXACT_CURRENT_PREPARATION_CONTRACT_TEST_SCOPE_AND_UNCHANGED_GATE_STATUS')
        q.finish();guard.check(force=True);row.update(state='PASS_SELECTED_COMMON_SEARCH_DISPATCH_DOC_SYNC_NOT_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,distinct_dispatch_cases_retained=26,dispatched_mutation_families=16,
            full733_inputs_replayed=False,old292_products_reexecuted=False,original205_failure_and_all_previous_doc_history_preserved=True,
            next_work='actual_product_transaction_route_manifest_and_durable_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_DISPATCH_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
