"""393: external001 complete and scope20 modeled -> docs, no replay of source tests/Native."""
import re
import time
import json
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-scope-sync393.v1.json'
DRIVER='tools/p09/sync_crossref_preassigned_scope.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-preassigned-scope392.v1.json'
EXTERNAL='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run001.v1.json'
BASE='implementation/p09/evidence/p09-361-external-crossref-host-sync391.v1.json'
STATE='CURRENT_STATE.md'
REPORT='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
GUIDE='implementation/p09/P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md'
NEW='implementation/p09/P09_CROSSREF_PREASSIGNED_SESSION_PROGRESS.md'
SOURCES={'tools/p09/crossref_preassigned_session_scope.py','tools/p09/tests/test_crossref_preassigned_session_scope.py',
    'tools/p09/run_crossref_preassigned_scope.py','tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
    'tools/p09/crossref_native_host_channel.py','implementation/p09/tools/sdk-baseline-owned-session.ps1',
    'implementation/p09/tools/crossref-native-case-ports.ps1'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_SCOPE_SYNC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_SCOPE_DOC_SYNC',own_cpu_selection=selection,
        external001_completed_and_independently_bound=True,actual_Hangul_COM_child_or_test_replayed=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);runtime=r.compact.unpack(q.json(RUNTIME));docs=r.compact.unpack(q.json(BASE));external=r.compact.unpack(q.json(EXTERNAL))
        c.require(q.snapshots[RUNTIME]['sha256']=='3387bf3b49a3e1cde216c668d961b5cab1130ced40502997dc358283637cfef8'
            and runtime['cleanup']and runtime['fresh_inputs']==runtime['final_fresh_hashes']==205
            and runtime['contracts']==dict(run=20,errors=0,failures=0,skipped=0)
            and runtime['actual_preparation_guard_denied_before_native_constructor']is True
            and not runtime['actual_Hangul_COM_or_child_started'],'EXACT392_NEW20_MODELED_SCOPE_AND_ACTUAL_GUARD_DENIAL_NOT_NATIVE')
        c.require(q.snapshots[BASE]['sha256']=='b7457499c24ec54b847ce42377769a9e994c7783ab7135dd44ce2d3032c8a4e5'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==38,'EXACT391_PREVIOUS_DOCUMENT_BASELINE')
        c.require(q.snapshots[EXTERNAL]['sha256']=='a9598c11a234b96a602ac9d075c8af151a518e7ab2ba40d53fcab6ea93c068c7'
            and external['state']=='OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION'
            and external['cleanup']and external['fresh_inputs']==external['final_fresh_hashes']==200
            and external['external_image_final_hashes']==external['external_runtime_final_hashes']==1
            and not external['native_startup_qualified']and not external['fixed_eight_executed'],
            'ORIGINAL_EXTERNAL001_USER_RECEIPT_PRESERVED_NOT_FUTURE_LIVE_NATIVE_AUTHORITY')
        pins={p['path']:p for p in runtime['source_pins']}
        for path in sorted(SOURCES):c.require(q.pin(path)==pins[path],'CURRENT_SCOPE_AND_ORIGINAL_NATIVE_FACTORY_LIMITS_PORTS_UNCHANGED')
        old={p['path']:p for p in docs['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 외부 CROSSREF 호스트 사전검사 준비'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 외부 검사001 통과와 사전배정 세션 연결'),'ONE_EXTERNAL_COMPLETE_AND_SCOPE_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PRIOR_EXTERNAL_FAILURES_CATALOG_PRODUCT_AND_USER_HISTORY_PRESERVED')
        report=q.text(REPORT);start=report.index('## 사전배정 세션 연결');end=report.index('## 현재 확인 결과',start)
        restored=(report[:start]+report[end:]).replace(
            '사용자는 외부 터미널에서 검사001을 실행했다. 원 영수증과200fresh/final200·외부 image/runtime 각각1final·\ncleanupTrue,원 전제5개·실제 jobless·kernel identity 앞뒤 동일성·빈 Job 정리를 확인했다.\n검사001을 다시 실행하지 않으며 [실행 안내](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)에 결과를 반영했다.',
            '사용자는 외부 터미널에서 직접 실행 가능하다고 답했다. 새 `inspect-only` 진입점과\n[실행 안내](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)를 준비했으며 사용자 실행001 결과는 아직 없다.').replace(
            '직접 실행 가능 답변에 따라 외부 사전검사001을 완료하고 독립 대조했다. 완료된 호출의 영수증을\n향후 실제 세션의 live 자격으로 재사용하지 않는다. 이 답변으로 작업 스케줄러·상위 Job/보안 설정을 변경하거나',
            '직접 실행 가능 답변은 외부 사전검사 준비 범위로 적용했다. 사용자에게 검사 명령을 전달했으며\n외부 실행001 결과를 기다린다. 이 답변으로 작업 스케줄러·상위 Job/보안 설정을 변경하거나')
        r.audit.inverse(restored,old[REPORT],'ONLY_USER_EXTERNAL_RESULT_AND_NEW_SCOPE_SECTION_ORIGINAL_NATIVE_CONDITIONS_PRESERVED')
        guide=q.text(GUIDE);start=guide.index('## 완료된 외부 검사');end=guide.index('## 실행 방법',start)
        restored=(guide[:start]+guide[end:]).replace(
            "& (Join-Path $env:USERPROFILE '.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe')",
            "& 'C:\\Users\\thdqu\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'")
        r.audit.inverse(restored,old[GUIDE],'ONLY_COMPLETED001_STATUS_AND_EQUIVALENT_COPY_SAFE_POWERSHELL_COMMAND_CHANGED')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('200fresh/final200','205fresh/final205','20','CROSSREF8종 NOT_RUN','Native011 미승인/미실행',
                '공식158/249','잔여91','P09/A12/A13 OPEN','목표ACTIVE','P10 미시작'):
                c.require(token in text,'EXTERNAL_OBSERVATION_MODEL_RESULT_AND_UNCHANGED_GATE_BOUNDARIES')
        for token in('ROT','worker1%','모의','실제 세션','재실행하지 않는다'):
            c.require(token in progress,'REMAINING_COM_WORKER_AND_LIVE_NATIVE_BOUNDARIES_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(REPORT,report),(GUIDE,guide)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_REVIEWED_PRIMARY_ROT_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_EXTERNAL001_CURRENT_AND_HISTORICAL_EVIDENCE_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_EXTERNAL001_COMPLETE_AND_PREASSIGNED_SCOPE20_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='exact_ROT_owner_attachment_worker_and_live_startup_qualification_before_conditional_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_SCOPE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
