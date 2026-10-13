"""r32 scope/doc sync only. Original cancel failure/final-hash false stay immutable."""
import base64
import hashlib
import json
import time
import run_durable_negative_sql_probe as s

SELF='tools/p09/verify_durable_negative_execution_progress_sync.py'
ARCHIVE='implementation/p09/source-archive/p09-151-pre-progress-r32/source-preimages.v1.json'
PINS=[{"path":"implementation/p09/evidence/p09-151-current-SQL-execution.pre-cancel-run01.v1.json","bytes":393751,"sha256":"5f21ec6f340dd4755f60b02db92dba2e1855f35dd6c2514770b93c7fec72a1b4"},{"path":"implementation/p09/evidence/p09-151-current-SQL-execution.preflight-run02.v1.json","bytes":43917,"sha256":"21a2904b286356451dde0f7d0fde3e597bcc8a25406b3229f583ba5a32e4bd6d"},{"path":"implementation/p09/evidence/p09-151-current-SQL-execution.terminal-audit-run01.v1.json","bytes":289924,"sha256":"d28e1223c3cfabebb673e64a6bfec51932671bd72d691cdc87dc4e4fd1165f59"}]


def main():
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'SYNC_REPOSITORY_CWD')
    destination=s.subject.scoped_path('implementation/p09/evidence/p09-151-current-execution.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-current39-owned-execution-progress-sync/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,actual_SQL_Docker_native_or_EXE_executed=False,goal_status='active',
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        raw_logs_included=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        for pin in PINS:s.require(q.pin(pin['path'])==pin,'SYNC_IMMUTABLE_EVIDENCE')
        actual=q.json(PINS[0]['path']);preflight=q.json(PINS[1]['path']);closing=q.json(PINS[2]['path'])
        s.require(actual['state']=='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_ONLY_NOT_SQL_OR_GATE'
            and actual['source_closing_exact'] and actual['actual_SQL_executed'] is False
            and actual['actual_owned_worker_executed'] is True,'SYNC_ACTUAL_HOST_SCOPE')
        original=actual['executions'][0]['supervisor']['worker_result']['accounted_call']
        s.require(original['state']=='ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS'
            and original['driver_error_code']==s.CANCEL_REASON and original['reader_count']==0
            and original['source_final_hash_completed'] is False,'SYNC_ORIGINAL_FAILURE_NOT_PROMOTED')
        s.require(preflight['state']=='PASS_CURRENT39_READ_ONLY_PREREQUISITE_CHECK_NOT_SQL_OR_GATE'
            and preflight['preflight']['diagnosis']=='FIXED_LOCAL_IMAGE_ABSENT'
            and preflight['preflight']['ready'] is False and preflight['actual_SQL_executed'] is False,'SYNC_READ_ONLY_PREREQUISITE_SCOPE')
        s.require(closing['state']=='PASS_CURRENT39_PRE_BACKEND_CANCEL_HOST_CLOSING_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and closing['source_closing_exact'] and closing['contract_tests_passed']==36
            and closing['required_check_count']==39 and closing['current_Rust_input_count']==785
            and closing['product_entrypoint_connected'] is True,'SYNC_CLOSING_SCOPE')
        prefixes=[];docs=[]
        for item in q.json(ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            s.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'SYNC_PREVIOUS_WHOLE_DOCUMENT')
            pin=q.pin(item['path']);current=q.text(item['path']).encode('utf-8')
            s.require(len(current)==pin['bytes'] and hashlib.sha256(current).hexdigest()==pin['sha256']
                and len(current)>len(raw) and current.endswith(raw),'SYNC_PREVIOUS_BODY_BYTE_EXACT')
            prefixes.append(current[:-len(raw)]);docs.append(pin)
        s.require(len(docs)==2 and prefixes[0]==prefixes[1]
            and prefixes[0].startswith('> 2026-10-07 P151 current39 owned-execution-r32:'.encode()),'SYNC_COMMON_CURRENT_PREFIX')
        header=prefixes[0].decode('utf-8')
        for literal in ('목표 active','잔여76','product=false','P10 새 구현 없음','product entrypoint가 연결됐지만','NOT_RUN',
                'source_final_hash_completed=false','FIXED_LOCAL_IMAGE_ABSENT','미완료'):
            s.require(literal in header,'SYNC_DECLARED_BOUNDARY')
        for pin in PINS:s.require(pin['sha256'] in header,'SYNC_CURRENT_EVIDENCE_LINK')
        q.finish();out.update(state='PASS_PROGRESS_SYNC_ONLY_NOT_SQL_NATIVE_OR_GATE',source_closing_exact=True,
            previous_document_whole_bodies_preserved=True,current_document_pins=docs,current_execution_pins=PINS,
            current_Rust_input_count=785,current_SQL_consumption_view=846,required_SQL_check_count=39,
            product_entrypoint_connected=True,actual_SQL_product_qualified=False,original_failure_and_final_hash_false_preserved=True,
            prefix_bytes=len(prefixes[0]),prefix_sha256=hashlib.sha256(prefixes[0]).hexdigest(),
            resource_stop_reason=resources.reason)
    finally:
        s.finish_watcher(resources,out)
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_document_whole_bodies_preserved','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and not resources.reason and out.get('resource_watcher_cleanup_confirmed') else 2


if __name__=='__main__':raise SystemExit(main())
