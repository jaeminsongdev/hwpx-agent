"""318: natural-language report marker reconciliation; retain317 and do not replay tests."""
import json,re,time
from types import SimpleNamespace as NS
import run_stored_font_sync as previous
shared,c,a,tools,compact,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-stored-font-sync-recovery318.v1.json';DRIVER='tools/p09/run_stored_font_sync_recovery.py'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_FONT_DOC_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_FONT_SYNC_RECOVERY',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_and_changed_source_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(previous.OUTPUT)
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='559a147a2ca065f52cf93b9ee17cbce4a7deb6b03b0ec63750c01b248080822c'and failed['cleanup']
            and failed['state']=='FAILED_STORED_FONT_SYNC'and failed['error_code']=='REPORT_EXACT_PRODUCT_COMPONENT_AND_RESOURCE_SCOPE','EXACT317_REPORT_MARKER_FAILURE_RETAINED')
        for pin in failed['source_pins']:
            q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'ALL317_CURRENT_PRODUCT_PROOF_AND_SOURCE_INPUTS_UNCHANGED')
        # 317 reached this report after exact316 receipt, actual identities, source and Job checks.
        # Independently check those closed facts again without running the product or old tests.
        latest=previous.latest;code=latest.previous;r=compact.unpack(q.json(latest.OUTPUT));step=r['steps'][0];j=step['owned_job']
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(code.TEST)))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='69244dce380116a69c7429d2a6bdc40e983a33545a151b3c6ce9ccf2e52a7182'and r['cleanup']
            and r['fresh_inputs']==r['final_fresh_hashes']==739 and len(cases)==24 and len(step['tests'])==24 and {n for n,s in step['tests']if s=='ok'}==cases
            and step['diagnostics']==[]and step['exit_code']==0,'EXACT316_PRODUCT24_SUCCESS_AND_FRESHNESS')
        c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'EXACT316_TERMINAL_JOB')
        docs=q.json(previous.BASE);old={p['path']:p for p in docs['source_pins']}
        text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 폰트 이름과 선택 범위 치환'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 현재 저장과 제품 요청')and text.count(marker)==1,'ONE_CURRENT_STORED_FONT_PREFIX')
        audit.inverse(text[text.index(marker):],old['CURRENT_STATE.md'],'ALL_PRIOR_STATE_HISTORY_PRESERVED')
        sections=[]
        for path,end,pass_marker in ((previous.REPORT,'## 폰트 이름과 선택 범위 치환\n','신규24개는 모두pass'),(previous.PROGRESS,'## 원본 폰트 참조 치환\n','24pass')):
            text=q.text(path);start=text.index('## 현재 저장 서비스와 폰트 제품 요청\n');finish=text.index(end,start);section=text[start:finish];sections.append((path,section))
            restored=text[:start]+text[finish:]
            if path==previous.PROGRESS:c.require(text.count(previous.NEW_ROW)==1,'ONLY_SEARCH024_ADVANCED');restored=restored.replace(previous.NEW_ROW,previous.OLD_ROW)
            audit.inverse(restored,old[path],'ALL_OTHER_PROGRESS_AND_FAILURE_HISTORY_PRESERVED')
            for marker in (pass_marker,'739fresh/final739','107.782초','12.969초','8.39초','736.46MiB','16.93%','41.2961%','P09/A12/A13 OPEN'):
                c.require(marker in section,'REPORT_EXACT_PRODUCT_COUNT_AND_RESOURCE_SCOPE')
        text=q.text(previous.PROFILE);c.require(text.count(previous.NEW_BOUNDARY)==1,'ONE_SOURCE_CONTRACT_BOUNDARY_UPDATE')
        audit.inverse(text.replace(previous.NEW_BOUNDARY,previous.OLD_BOUNDARY),old[previous.PROFILE],'ALL_PRIOR_SOURCE_CONTRACTS_PRESERVED')
        text=q.text(previous.PRODUCT);sections.extend(((previous.PROFILE,previous.NEW_BOUNDARY),(previous.PRODUCT,text)))
        for marker in ('product-scoped-font-replacement-request/v1','1~10000','16KiB','RouteUnqualified','공통 operation compiler/dispatcher','739fresh/final739'):
            c.require(marker in text,'STRICT_PRODUCT_SCHEMA_BUDGETS_AND_DENIED_AUTHORITY')
        for path,section in sections:
            for target in re.findall(r'\]\(([^)]+)\)',section):
                p=(c.ROOT/path).parent/target;c.require(p.resolve().is_relative_to(c.ROOT.resolve())and p.is_file(),'CURRENT_LOCAL_PROTOCOL_AND_EVIDENCE_LINK_EXISTS')
        q.pin(previous.DRIVER);q.pin(DRIVER);q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_FONT_PRODUCT24_CURRENT_DOC_SYNC_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            distinct_new_product_cases=24,official_queue_accepted=158,official_queue_total=249,next_work='source_edit_inventory_and_common_operation_compiler_and_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'STORED_FONT_DOC_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','distinct_new_product_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
