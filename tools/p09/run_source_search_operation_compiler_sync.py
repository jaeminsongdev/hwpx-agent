"""Selected tested compiler and current docs closure; no Cargo or750-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_source_search_operation_compiler_components as base
shared,c,a,audit,tools=base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-search-operation-compiler-sync217.v1.json'
DRIVER='tools/p09/run_source_search_operation_compiler_sync.py'
PASSED='implementation/p09/evidence/p09-361-source-search-review-compiler-recovery216.v1.json'
OWNER='implementation/p09/evidence/p09-361-source-search-owner-admission-recovery215.v1.json'
FAILED214='implementation/p09/evidence/p09-361-source-search-operation-compiler-recovery214.v1.json'
DOC_BASE='implementation/p09/evidence/p09-361-style-splice-inventory-sync-recovery212.v1.json'
PROFILE='protocol/migrations/p09-source-search-operation-compiler-v1.md'
COMMON='protocol/migrations/p09-common-search-mutation-dispatch.md'
STYLE='protocol/migrations/p09-style-splice-inventory-v1.md'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md'
DOCS={PROFILE,COMMON,STYLE,PROGRESS,'CURRENT_STATE.md'}
RETAINED=base.NEW|base.CHANGED|{
    'tools/p09/run_source_search_operation_compiler_recovery.py',
    'tools/p09/run_source_search_owner_admission_recovery.py',
    'tools/p09/run_source_search_review_compiler_recovery.py'}
OLD_ROW='| SEARCH-008 | 서식 치환 | 부분 run/text-style·문단/이름 스타일 core/저장/제품과 두 글자 축의 실제 최종 splice 목록 신규12·영향38 검증, operation compiler/유효 서식/전체 계약 미완료 |'
NEW_ROW='| SEARCH-008 | 서식 치환 | 부분 run/text-style·문단/이름 스타일 core/저장/제품·실제 최종 splice와16계열 공통 operation compiler 검증, 유효 서식/실제 실행/전체 계약 미완료 |'


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_COMPILER_SYNC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_COMPILER_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        trusted_route_full_transaction_or_gate_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed=q.json(PASSED);owner=q.json(OWNER);original=q.json(base.OUTPUT);failed214=q.json(FAILED214);docbase=q.json(DOC_BASE)
        for name,digest in((PASSED,'1061ad23466f2c7d57bd056439620384f82eb36dfbecd3f3b17b87610092e89c'),
            (OWNER,'6dde02878a95f427df70e171358086e77fed33200c9da560e87ba90f3b158684'),
            (base.OUTPUT,'30d6a01aa8e88be436d9ec8a468a1929ffb8f5b99ac4786d355ccac28d7fe694'),
            (FAILED214,'2e3d2b168ebc257418f978361e1cdad76a0a7856f2b4cfd407d66c32bdbf0d4a'),
            (DOC_BASE,'7d3e771729eea77b2ceab84380067787ad3024ae6d90cf460f1cd33d36ad8fe9')):
            c.require(q.snapshots[name]['sha256']==digest,'EXACT_COMPILER_TEST_AND_PREVIOUS_DOC_EVIDENCE')
        c.require(passed['state']=='PASS_SIXTEEN_FAMILY_SOURCE_OPERATION_COMPILER30_OWNER6_RETAINED35_NOT_TRUSTED_ROUTE_NATIVE_TRANSACTION_OR_GATE'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==750
            and passed['total_executed_cases']==1 and not passed['passed35_cases_reexecuted'],'EXACT216_ONE_RECOVERY_AND_CURRENT750_CLOSURE')
        c.require(all(e['cleanup']and e['state'].startswith('FAILED_')for e in(original,failed214,owner))and docbase['cleanup'],
            'ORIGINAL213_214_215_FAILURES_AND212_DOC_HISTORY_PRESERVED')
        tested={p['path']:p for p in passed['source_pins']}
        selected=RETAINED|{name for name in tested if name.startswith('crates/domain-ir/src/')and name.rsplit('/',1)[-1]in{'operation_plan.rs','selector.rs','document_graph.rs'}}
        c.require(selected<=tested.keys(),'ALL_SELECTED_COMPILER_SOURCE_TESTS_DECLARED_BY216')
        for name in sorted(selected):q.pin(name);c.require(q.snapshots[name]==tested[name],'LIVE_SELECTED_COMPILER_AND_SOURCE_SECURITY_INPUTS_MATCH216')
        units,products=base.expected(q)
        owner5={n for n,s in original['steps'][0]['tests']if s=='ok'};owner1={n for n,s in owner['steps'][0]['tests']if s=='ok'}
        product29={n for n,s in owner['steps'][1]['tests']if s=='ok'};recovered={n for n,s in passed['steps'][0]['tests']if s=='ok'}
        c.require(len(owner5)==5 and len(owner1)==1 and owner5.isdisjoint(owner1)and owner5|owner1==units
            and len(product29)==29 and len(recovered)==1 and product29.isdisjoint(recovered)and product29|recovered==products,
            'EXACT_DISTINCT36_COVERAGE_NOT_CURRENT36_SINGLE_RUN')
        tools.good_step(passed['steps'][0],recovered)
        base.inverse(q,{p['path']:p for p in q.json(base.BASELINE)['source_pins']})
        for name in sorted(DOCS|{DRIVER}):q.pin(name)
        previous={p['path']:p for p in docbase['source_pins']}
        current=q.text('CURRENT_STATE.md');at=current.index('> 2026-10-20 P09 ACTIVE 최신 서식 후보의 실제 최종 splice 목록')
        audit.inverse(current[at:],previous['CURRENT_STATE.md'],'ENTIRE_OLD_CURRENT_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 실제 원본에 결속한 공통 operation compiler\n');end=progress.index('## 서식 후보의 실제 최종 splice 목록\n',start)
        c.require(progress.count(NEW_ROW)==1,'ONE_UPDATED_SEARCH008_COMPILER_BOUNDARY')
        audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),previous[PROGRESS],'ALL_OTHER_SEARCH_ROWS_AND_HISTORY_PRESERVED')
        for name,heading in((COMMON,'\n## 실제 원본 operation compiler 연결\n'),(STYLE,'\n## 검증한 원본 operation compiler 소비자\n')):
            text=q.text(name);c.require(text.count(heading)==1,'ONE_ADDITIVE_COMPILER_CONTRACT_LINK')
            audit.inverse(text[:text.index(heading)],previous[name],'ENTIRE_PREVIOUS_CONTRACT_AND_FAILURE_HISTORY_PRESERVED')
        ids=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(ids)==len(set(ids))==19,'EXACT19_P09_SEARCH_ROWS_NO_P11_SCOPE_ADDED')
        for text in(current[:at],progress[start:end],q.text(PROFILE)):
            for marker in('product-source-search-operation-compiler/v1','SelectorSnapshot','OperationPlanCompiler','12개','4096','8MiB','16MiB',
                '213','214','215','216','750fresh/final750','고유36개','단일 실행이 아니다','FieldContent','RouteUnqualified','최종 head'):
                c.require(norm(marker)in norm(text),'EXACT_DOCUMENTED_ACTUAL_COMPILER36_CURRENT_ACCESS_AND_FAILURE_BOUNDARIES')
        profile=norm(q.text(PROFILE))
        for marker in('source_anchor_json','source_edit_index','source_edit_domain','owner_binding_profile','actual_structural_owner_with_exact_source_edit/v1',
            'execution_authority','false','ingest/commit/CAS','영속 멱등','158/249','잔여91','next165','P09/A12/A13 OPEN',
            'CROSSREF8종 NOT_RUN','Native011 미승인/미실행','임의 첫 문단','가상 document node'):
            c.require(norm(marker)in profile,'EXACT_FIELDS_AND_REMAINING_PRODUCT_NATIVE_GATE_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_SOURCE_OPERATION_COMPILER36_DOC_SYNC_NOT_TRUSTED_ROUTE_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,distinct_product_cases_retained=30,distinct_owner_units_retained=6,
            actual_cases_reexecuted=0,full750_inputs_replayed=False,original213_214_215_failures_and_previous_doc_history_preserved=True,
            next_work='real_target_registry_route_manifest_and_durable_transaction_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_COMPILER_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
