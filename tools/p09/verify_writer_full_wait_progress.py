"""P173 wait-doc sync ONLY; file existence is not proof of a live process."""
import base64
import hashlib
import json
import run_writer_current_full as d
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
ARCHIVE='implementation/p09/source-archive/p09-173-pre-progress-r51/document-preimages.v1.json'
LIGHT='implementation/p09/evidence/p09-173-writer-current-full.light-run01.v1.json'
def main():
    resources=d.s.SQLRuntimeResources();q=None
    destination=d.s.scoped_path('implementation/p09/evidence/p09-173-writer-current-full.wait-progress-run01.v1.json',fresh=True)
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',
        A13_gate='OPEN',full249_current_qualified=False,signed16_current_qualified=False,
        tool_handle_reference=42277,live_handle_verified_by_this_script=False,
        terminal_runtime_result_not_inferred_from_files=True)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources)
        q.pin('tools/p09/verify_writer_full_wait_progress.py');row=q.json(LIGHT)
        d.require(row['state']=='PASS_CURRENT_WRITER_FULL_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
            and row['contract_tests_passed']==32 and not row['actual_Cargo_SQL_native_or_test_EXE_executed'],'LIGHT_ONLY')
        frozen=d.s.inputs.inventory(row['bound_input_pins'])
        for n in (d.SELF,d.TEST,d.original.SELF,d.original.TEST,d.original.full.SELF,d.original.full.TEST):
            d.require(q.pin(n)==frozen[n],'FROZEN_DRIVER_AND_ORIGINAL_CAPTURE')
        d.contracts();q.pin('tools/p09/audit_writer_current_full.py')
        d.require(q.pin(d.PARENT['path'])==d.PARENT,'COMPILED_CLOSING_PIN')
        parent=q.json(d.PARENT['path']);_,exe=d.parent_scope(parent)
        d.require(q.pin(exe['path'])==exe,'EXE_IMMUTABLE')
        old={x['path']:x for x in q.json(ARCHIVE)['files']};prefixes=[]
        d.require(set(old)==set(DOCS),'OLD_DOC_SCOPE')
        for n in DOCS:
            raw=base64.b64decode(old[n]['base64'],validate=True)
            d.require(len(raw)==old[n]['bytes'] and hashlib.sha256(raw).hexdigest()==old[n]['sha256'],'WHOLE_PREIMAGE')
            current=q.text(n).encode();d.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
            prefixes.append(current[:-len(raw)])
        d.require(prefixes[0]==prefixes[1] and b'P173' in prefixes[0] and b'WAITING' in prefixes[0],'IDENTICAL_WAIT_PREFIX')
        q.finish();out.update(state='PASS_CURRENT_WRITER_WAIT_DOCUMENT_SYNC_ONLY_NOT_RUNTIME_OR_LIVENESS_OR_GATE',
            contract_tests_passed=32,whole_prior_documents_preserved=True,compiled_test_executable_pin=exe)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
