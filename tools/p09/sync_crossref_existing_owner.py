"""397: current compiled adapter/model+self/capture evidence -> docs only; no worker/ROT/Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-existing-owner-sync397.v1.json'
DRIVER='tools/p09/sync_crossref_existing_owner.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-existing-owner-capture396.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-scope-sync393.v1.json'
STATE='CURRENT_STATE.md';REPORT='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
SCOPE='implementation/p09/P09_CROSSREF_PREASSIGNED_SESSION_PROGRESS.md'
NEW='implementation/p09/P09_CROSSREF_EXISTING_OWNER_PROGRESS.md'
SOURCES={'implementation/p09/tools/crossref-existing-owner.cs','implementation/p09/tools/test-crossref-existing-owner.cs',
    'implementation/p09/tools/test-crossref-existing-owner.ps1','tools/p09/crossref_existing_owner_test_runtime.py',
    'tools/p09/run_crossref_existing_owner_capture.py','tools/p09/crossref_preassigned_session_scope.py',
    'tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
    'implementation/p09/tools/sdk-baseline-owned-session.ps1','implementation/p09/tools/crossref-native-case-ports.ps1'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'ROT_OWNER_SYNC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_ROT_OWNER_DOC_SYNC',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);runtime=r.compact.unpack(q.json(RUNTIME));docs=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[RUNTIME]['sha256']=='cb433c26468811ef62d02d1420ed7d5bdbc8b735057dca37fb3686f1ed589b06'
            and runtime['cleanup']and runtime['fresh_inputs']==runtime['final_fresh_hashes']==193
            and runtime['external_shell_final_hashes']==1 and runtime['pure_capture_contracts_passed']==3
            and not runtime['actual_Hangul_or_ROT_or_COM_queried'],'EXACT396_CURRENT_COMPILED_MODELS_KERNEL_SELF_AND_CAPTURE_NOT_ACTUAL_ROT')
        c.require(len(runtime['steps'])==1,'ONE_FIXED_READONLY_COMPILE_WORKER');step=runtime['steps'][0]
        c.require(step['exit_code']==0 and len(step['tests'])==21 and all(status=='ok'for _,status in step['tests'])
            and len({name for name,_ in step['tests']})==21 and not step['safe_error_codes']
            and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed']and step['cleanup']
            and runtime['retained_compiler_scratch_entries']==0,'ACTUAL_ALL21_MARKERS_AND_COMPLETE_WORKER_CLEANUP_NO_SKIPS')
        c.require(q.snapshots[BASE]['sha256']=='7845bd371cbea3c46929195a0e90966b9ffabb285a10d7a1b282cd40be0f27c9'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==16,'EXACT393_PREVIOUS_DOC_BASELINE')
        pins={p['path']:p for p in runtime['source_pins']}
        for path in sorted(SOURCES):c.require(q.pin(path)==pins[path],'ALL_VERIFIED_CSHARP_MODELS_CAPTURE_SCOPE_AND_ORIGINAL_NATIVE_INPUTS_UNCHANGED')
        old={p['path']:p for p in docs['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 외부 검사001 통과와 사전배정 세션 연결'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 기존 ROT 객체 연결부 컴파일 검증'),'ONE_CURRENT_COMPILED_ROT_ADAPTER_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_EXTERNAL001_SCOPE20_PRIVATE_FAILURES_AND_USER_HISTORY_PRESERVED')
        report=q.text(REPORT);start=report.index('## 기존 객체 연결부');end=report.index('## 현재 확인 결과',start)
        r.audit.inverse(report[:start]+report[end:],old[REPORT],'ONLY_EXISTING_OWNER_COMPILED_STATUS_ADDED_ORIGINAL_READINESS_CONDITIONS_PRESERVED')
        scope=q.text(SCOPE);new='후속 [기존 객체 연결부](P09_CROSSREF_EXISTING_OWNER_PROGRESS.md)는 x86 C# 컴파일·모의20·현재 worker kernel1과\nparser3을 검증했지만 실제 ROT/한글 COM은 조회하지 않았다. 다음은 이 연결부와 worker1% 자원 Job·새 private host protocol/owner factory의'
        before='다음은 정확한 기존 ROT/COM 객체 연결·worker1% 자원 Job·새 private host protocol/owner factory의'
        c.require(scope.count(new)==1,'ONE_SCOPE_FOLLOWUP_STATUS');r.audit.inverse(scope.replace(new,before),old[SCOPE],'ALL_SCOPE20_RESULT_AND_ORIGINAL_EXTERNAL001_CONDITIONS_PRESERVED')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('193fresh/final193','20','21','parser3','CROSSREF8종 NOT_RUN','Native011 미승인/미실행',
                '공식158/249','잔여91','P09/A12/A13 OPEN','목표ACTIVE','P10 미시작'):
                c.require(token in text,'MODELS_SELF_CAPTURE_SEPARATED_FROM_NATIVE_AND_UNCHANGED_GATE_BOUNDARIES')
        for token in('worker1%','实际'.replace('实际','실제'),'256','1024','100ns','394','395','CRLF','67.20MiB'):
            c.require(token in progress,'LIMITS_FAILURE_LINEAGE_RESOURCE_AND_REMAINING_WORKER_SCOPE_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(REPORT,report),(SCOPE,scope)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_REVIEWED_PRIMARY_ROT_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_SOURCE_CURRENT_AND_ORIGINAL_FAILURE_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_EXISTING_ROT_ADAPTER_COMPILED_MODELS_SELF_CAPTURE_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='descriptor_protocol_resource_bound_worker_successor_owner_factory_integration_then_actual_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'ROT_OWNER_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
