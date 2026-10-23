"""364: current selected-body mask25/shared3 and preserved362 compile failure; source/docs only."""
import json,re,time
from types import SimpleNamespace as NS
import run_personal_info_mask_recovery as latest
base=latest.base
shared,c,a,tools,compact,harness,audit=base.shared,base.c,base.a,base.tools,base.compact,base.harness,base.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-mask-sync364.v1.json';DRIVER='tools/p09/run_personal_info_mask_sync.py'
STATE='CURRENT_STATE.md';PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_PERSONAL_INFO_MASK_PROGRESS.md'
PROFILE='protocol/migrations/p09-source-personal-info-selection-mask-v1.md'
OLD_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | 실제 치환·개인정보 정책·비노출 검증 필요 |'
NEW_ROW='| SEARCH-019 | 개인정보 바로 바꾸기 | 명시적 선택/두 별표 정책 source25+공유 경계3 검증, 현재 저장/제품·전체 개인정보 정책·문서 전체 익명화/실제 실행/저장/target 미완료 |'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_MASK_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_MASK_SYNC',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        document_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,
        whole_package_personal_data_removed=False,native_mask_semantics_or_service_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=compact.unpack(q.json(base.OUTPUT));docs=q.json(base.DOCS);before=compact.unpack(q.json(base.BASE))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='ffd4119fb913ff0bcdc8d67a142be08e646745db1310c1ae77c909d7c9814a8c'and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==850
            and run['state']=='PASS_SOURCE_SELECTION_PERSONAL_INFO_MASK25_SHARED_BOUNDARY3_NOT_NATIVE_PACKAGE_SANITIZATION_OR_GATE','EXACT363_NEW25_SHARED3_FULL_SOURCE_AND_TERMINAL_CLEANUP')
        c.require(q.snapshots[base.DOCS]['sha256']=='639b2e837e1f51d46124788c68fe7388ecefbf26dfe42cff990633a3bcda79f5'and docs['cleanup'],'EXACT361_PRIOR_CURRENT_DOC_BASELINE')
        old={p['path']:p for p in run['source_pins']};sources=base.NEW|{base.PARENT,base.OLD_TEST,
            'crates/hwpx-package/src/document_import/search/replacement/atoms/unicode/plan.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/unicode/transform.rs',
            'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs','crates/hwpx-package/src/document_import/search/replacement/atoms/styles/text/output.rs',
            'crates/hwpx-package/src/document_import/protection.rs','crates/hwpx-package/tests/support/document_import_review_assembly_fixture.rs',
            'crates/hwpx-package/tests/support/review_cell_output_fixture.rs','docs/04_feature_catalog/contracts/03_search_contracts.md'}
        for path in sorted(sources):
            q.pin(path)
            if path in old:c.require(q.snapshots[path]==old[path],'ALL_CURRENT_MASK_SOURCE_TEST_PLANNER_WRITER_AND_PROTECTION_MATCH363')
        base.inverse(q,{p['path']:p for p in before['source_pins']})
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST)));c.require(len(cases)==25 and '#[ignore]'not in q.text(base.TEST),'EXACT_CURRENT25_NO_IGNORES')
        tools.good_step(run['steps'][0],cases);tools.good_step(run['steps'][1],base.AFFECTED)
        c.require(run['elapsed_seconds']==121.765 and run['system_CPU_max']==24.25 and 39.4990<run['available_RAM_min_percent']<39.4991
            and max(s['owned_job']['last_job_accounting']['peak_job_private_mib']for s in run['steps'])==588.29,'EXACT363_RESOURCE_SCOPE_NOT_FREEZE_FIX')
        old_docs={p['path']:p for p in docs['source_pins']};state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 최신 스타일 선언의 현재 저장과 제품 요청'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 최신 개인정보 선택 본문 마스킹')and state.count(marker)==1,'ONE_CURRENT_PERSONAL_INFO_MASK_PREFIX')
        prefix=state[:state.index(marker)];audit.inverse(state[state.index(marker):],old_docs[STATE],'ALL_PRIOR_STYLE_FAILURE_AND_PHASE_HISTORY_PRESERVED')
        progress=q.text(PROGRESS);start=progress.index('## 선택한 원본 본문의 개인정보 마스킹\n');end=progress.index('## 스타일 선언의 현재 저장과 제품 요청\n',start);section=progress[start:end]
        c.require(progress.count(NEW_ROW)==1,'ONLY_SEARCH019_ROW_ADVANCED');audit.inverse((progress[:start]+progress[end:]).replace(NEW_ROW,OLD_ROW),old_docs[PROGRESS],'ALL_OTHER18_SEARCH_ROWS_AND_PRIOR_PROGRESS_PRESERVED')
        report=q.text(REPORT);profile=q.text(PROFILE);q.pin(DRIVER)
        for document in(prefix,section,report,profile):
            for marker in('362','363','850fresh/final850','28pass','공식158/249','P09/A12/A13 OPEN','Native011 미승인/미실행','SEARCH-020','마스킹'):
                c.require(marker in document,'SOURCE_ONLY_MASK_COUNTS_NO_PACKAGE_SANITIZATION_OR_NATIVE_GATE_PROMOTION')
        for marker in('PerOriginalScalarPreserveSlots','ThreeAsterisksPerTextGroup','whole_package_personal_data_removed','native_mask_semantics_or_service_execution_qualified',
            '2020','query/replacement','read_only','개인정보 값별 해시','4MiB','1byte','미리보기'):
            c.require(marker in profile,'EXPLICIT_POLICY_NATIVE_UNQUALIFIED_CATALOG_CONFLICT_AND_PRIVACY_BOUNDARIES')
        for path,document in((PROGRESS,section),(REPORT,report),(PROFILE,profile)):
            for target in re.findall(r'\]\(([^)]+)\)',document):
                if target.startswith('https://'):c.require(target.startswith('https://help.hancom.com/'),'ONLY_PRIMARY_OFFICIAL_HELP_REFERENCE');continue
                p=((c.ROOT/path).parent/target).resolve();c.require(p.is_relative_to(c.ROOT.resolve())and p.is_file(),'LOCAL_PERSONAL_INFO_CONTRACT_AND_EVIDENCE_LINK_EXISTS')
        q.finish();guard.check(force=True);row.update(state='PASS_SOURCE_MASK25_SHARED3_CURRENT_DOC_SYNC_NOT_STORED_PRODUCT_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_mask_cases=25,shared_boundary_cases=3,mutation_families=22,official_queue_accepted=158,official_queue_total=249,
            next_work='current_stored_service_and_strict_personal_info_mask_product_then_full_scope_policy_and_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_MASK_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
