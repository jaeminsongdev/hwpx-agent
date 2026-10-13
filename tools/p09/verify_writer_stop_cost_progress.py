"""P173 CPU stop/P174 cost evidence sync only; whole prior docs preserved."""
import base64
import hashlib
import json
import run_writer_case_cost as d
import audit_writer_case_cost as audit
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
ARCHIVE='implementation/p09/source-archive/p09-174-pre-progress-r52/document-preimages.v1.json'
NAMES=('implementation/p09/evidence/p09-173-writer-current-full.actual-run01.v1.json',d.PARENT['path'],
 'implementation/p09/evidence/p09-174-writer-case-cost.light-run01.v1.json',audit.ACTUAL,
 'implementation/p09/evidence/p09-174-writer-case-cost.terminal-audit-run01.v1.json')
def main():
 resources=d.s.SQLRuntimeResources();q=None
 out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=True,
  full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
  P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False)
 destination=d.s.scoped_path('implementation/p09/evidence/p09-174-writer-stop-cost.progress-sync-run01.v1.json',fresh=True)
 try:
  resources.admit();q=d.s.LiveSQLReader(resources);q.pin('tools/p09/verify_writer_stop_cost_progress.py')
  full,closing,light,actual,cost_closing=(q.json(n) for n in NAMES)
  d.require(full['state']=='STOPPED_NOT_ACCEPTED' and full['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
   and full['maximum_seconds']==1200 and not full['full249_current_qualified']
   and full['tests_passed'] is None and full['cleanup_confirmed'] and full['owned_tree_empty'],'FULL_STOP')
  d.require(q.pin(d.PARENT['path'])==d.PARENT,'FULL_CLOSING_PIN');_,exe=d.parent_scope(closing)
  d.require(light['state']=='PASS_CURRENT_WRITER_PIPE_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
   and light['contract_tests_passed']==58 and not light['actual_EXE_or_native_query_started'],'LIGHT_ONLY')
  d.require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
   and actual['maximum_seconds']==360 and actual['original_full_qualification_seconds']==1200
   and actual['cleanup_confirmed'] and actual['owned_tree_empty'] and actual['tests_passed'] is None
   and not actual['native_Process_query_executed'],'COST_ONLY')
  d.require(cost_closing['state']==audit.PASS and cost_closing['source_closing_exact']
   and cost_closing['contract_tests_passed']==58 and cost_closing['completed_case_observations']==50
   and cost_closing['resource_stop_reason'] is None and cost_closing['resource_watcher_cleanup_confirmed'],'COST_CLOSING')
  names=cost_closing['source_test_names'];trace=cost_closing['case_progress'];audit.validate_trace(trace,names,False)
  d.require(trace==actual['capture_diagnostics']['case_progress'] and trace['started_case_count']==51
   and all(x['result']=='ok' for x in trace['completed']) and trace['active'] is not None,'EXACT_PARTIAL50_PLUS1')
  for row in (full,closing,actual,cost_closing):
   d.require(not row['full249_current_qualified'] and not row['signed16_current_qualified']
    and not row['product_complete'] and not row['PC_freeze_resolved']
    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NO_PROMOTION')
   job=row.get('job_final',row.get('owned_job_final'))
   d.require(job['active_processes']==0 and job['owned_processes']==[],'ALL_OWNED_TERMINAL')
  d.require(exe==actual['compiled_test_executable_pin']==cost_closing['compiled_test_executable_pin']
   and q.pin(exe['path'])==exe,'SAME_CURRENT_EXE')
  frozen=d.s.inputs.inventory(cost_closing['bound_input_pins'])
  for n in (d.SELF,d.TEST,audit.SELF,d.full.SELF,d.full.TEST,d.original.SELF,d.original.full.SELF):
   d.require(q.pin(n)==frozen[n],'FROZEN_HELPERS')
  old={x['path']:x for x in q.json(ARCHIVE)['files']};prefixes=[]
  d.require(set(old)==set(DOCS),'OLD_DOC_SCOPE')
  for n in DOCS:
   raw=base64.b64decode(old[n]['base64'],validate=True)
   d.require(len(raw)==old[n]['bytes'] and hashlib.sha256(raw).hexdigest()==old[n]['sha256'],'WHOLE_PREIMAGE')
   current=q.text(n).encode();d.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
   prefixes.append(current[:-len(raw)])
  d.require(prefixes[0]==prefixes[1] and b'P173/P174' in prefixes[0] and b'TERMINAL' in prefixes[0],'IDENTICAL_PREFIX')
  q.finish();out.update(state='PASS_CURRENT_WRITER_FULL_STOP_AND_COST_DOCUMENT_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
   whole_prior_documents_preserved=True,evidence_pins=[q.reader.snapshots[n] for n in NAMES],
   completed_case_observations=50,full_stop_reason=full['stop_reason'],diagnostic_stop_reason=actual['stop_reason'])
 except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.original.closed_error(e)
 finally:
  d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
  if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
  if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
  with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
  print(json.dumps({k:out.get(k) for k in ('state','completed_case_observations','error_code','resource_stop_reason')}))
 return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
