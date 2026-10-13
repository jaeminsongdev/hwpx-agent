"""P151 r31 scope/doc sync only; never restamps runtime/SQL/Gate evidence."""
import base64
import hashlib
import json
import time
import durable_negative_sql_contract as s

SELF='tools/p09/verify_durable_negative_progress_sync.py'
ARCHIVE='implementation/p09/source-archive/p09-151-pre-progress-r31/source-preimages.v1.json'
PINS=[{"path":"implementation/p09/evidence/p09-151-runtime-build.actual-run01.v1.json","bytes":894137,"sha256":"a34b54014db8df958b2a39590b2374941df708ff591c26f49c938e44fc9f8ecc"},{"path":"implementation/p09/evidence/p09-151-runtime-build.terminal-audit-run01.v1.json","bytes":308783,"sha256":"422703400cb68e322643557157f9cdc09d4c557df32b031c59d8540e5f735f8d"},{"path":"implementation/p09/evidence/p09-151-SQL-admission.admission-run01.v1.json","bytes":366275,"sha256":"0bb627fda554717ea625bb5be05bd22b794eb45988fc0dc3d9b385d161b602ac"},{"path":"implementation/p09/evidence/p09-151-SQL-admission.terminal-audit-run01.v1.json","bytes":283975,"sha256":"d5bdda244d37851c51afa14cdaa85487e267fc5d30579c12be14ab44bb17b1cb"}]


def main():
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'SYNC_REPOSITORY_CWD')
    destination=s.build.parent.scoped_path('implementation/p09/evidence/p09-151-runtime-and-SQL-admission.progress-sync-run01.v1.json',fresh=True)
    resources=s.build.parent.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-ds06-runtime-and-SQL-admission-progress-sync/v1',
        state='FAILED_NOT_ACCEPTED',source_closing_exact=False,actual_SQL_native_or_EXE_executed=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        remaining_non_permission_work_units=76,goal_status='active',raw_logs_included=False)
    try:
        resources.admit();q=s.build.parent.LiveSQLReader(resources);q.pin(SELF)
        for pin in PINS:s.require(q.pin(pin['path'])==pin,'SYNC_IMMUTABLE_EVIDENCE')
        runtime=q.json(PINS[1]['path']);admission=q.json(PINS[3]['path'])
        s.require(runtime['state']=='PASS_CURRENT_DS06_RUNTIME_BUILD_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and runtime['source_closing_exact'] and runtime['current_Rust_input_count']==785
            and runtime['protected_executables_exact']==53 and runtime['contract_tests_passed']==22,'SYNC_RUNTIME_SCOPE')
        s.require(admission['state']=='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and admission['source_closing_exact'] and admission['compiled_source_count']==846
            and admission['required_check_count']==39 and admission['contract_tests_passed']==16
            and admission['actual_SQL_Docker_native_or_EXE_executed'] is False,'SYNC_ADMISSION_SCOPE')
        archive=q.json(ARCHIVE);prefixes=[];docs=[]
        for item in archive['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            s.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'SYNC_WHOLE_PREIMAGE')
            pin=q.pin(item['path']);current=q.text(item['path']).encode('utf-8')
            s.require(len(current)==pin['bytes'] and hashlib.sha256(current).hexdigest()==pin['sha256']
                and len(current)>len(raw) and current.endswith(raw),'SYNC_PRIOR_BODY_BYTE_EXACT')
            prefix=current[:-len(raw)];prefixes.append(prefix);docs.append(pin)
        s.require(len(docs)==2 and prefixes[0]==prefixes[1]
            and prefixes[0].startswith('> 2026-10-07 P151 current-DS06 non-test runtime/SQL admission-r31:'.encode()),'SYNC_COMMON_PREFIX')
        header=prefixes[0].decode('utf-8')
        for literal in ('목표 active','잔여76','product=false','P10 새 구현 없음','846','39','미완료','product 실행 entrypoint는 아직 연결하지 않았다'):
            s.require(literal in header,'SYNC_SCOPE_LITERAL')
        for pin in PINS:s.require(pin['sha256'] in header or pin==PINS[2],'SYNC_EVIDENCE_LINK')
        q.finish();out.update(state='PASS_PROGRESS_SYNC_ONLY_NOT_SQL_NATIVE_OR_GATE',source_closing_exact=True,
            previous_document_whole_bodies_preserved=True,previous_documents_count=2,current_document_pins=docs,
            prefix_bytes=len(prefixes[0]),prefix_sha256=hashlib.sha256(prefixes[0]).hexdigest(),
            runtime_build_and_closing_pins=PINS[:2],SQL_admission_and_closing_pins=PINS[2:],
            current_Rust_input_count=785,current_SQL_consumption_view=846,required_SQL_check_count=39,
            product_SQL_entrypoint_connected=False,resource_stop_reason=resources.reason)
    finally:
        s.build.parent.finish_watcher(resources,out)
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_document_whole_bodies_preserved','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and not resources.reason and out.get('resource_watcher_cleanup_confirmed') else 2


if __name__=='__main__':raise SystemExit(main())
