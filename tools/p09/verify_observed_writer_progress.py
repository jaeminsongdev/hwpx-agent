"""P171/P172 exact evidence and whole prior-document preservation, sync only."""
import base64
import hashlib
import json
import build_observed_writer_product_r2 as build
import run_observed_writer_inventory as listing
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
ARCHIVE='implementation/p09/source-archive/p09-171-initial-fixture-and-documents-r50/preimages.v1.json'
EVIDENCE=('implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run01.v1.json',
 'implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run01.v1.json',
 'implementation/p09/evidence/p09-171-observed-writer-product-build.light-run05.v1.json',
 'implementation/p09/evidence/p09-171-observed-writer-product-build.actual-run02.v1.json',
 'implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run02.v1.json',
 'implementation/p09/evidence/p09-172-observed-writer-inventory.light-run01.v1.json',
 'implementation/p09/evidence/p09-172-observed-writer-inventory.actual-run01.v1.json',
 'implementation/p09/evidence/p09-172-observed-writer-inventory.terminal-audit-run01.v1.json')
def main():
 s=build.s;require=build.prior.require;resources=s.SQLRuntimeResources();q=None
 out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',
  A13_gate='OPEN',full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False)
 destination=s.scoped_path('implementation/p09/evidence/p09-172-observed-writer.progress-sync-run01.v1.json',fresh=True)
 try:
  resources.admit();q=s.LiveSQLReader(resources)
  rows=[q.json(n) for n in EVIDENCE]
  failed,failed_audit,light,actual,closing,list_light,list_actual,list_closing=rows
  require(failed['state']=='STOPPED_NOT_ACCEPTED' and failed['stop_reason']=='OWNED_COMMAND_FAILED'
   and failed['cleanup_confirmed'] and failed['owned_tree_empty'] and not failed['current_build_binding_accepted']
   and failed_audit['source_closing_exact'] and not failed_audit['current_build_accepted'],'FAILURE_PRESERVED')
  require(light['contract_tests_passed']==205 and list_light['contract_tests_passed']==15,'CONTRACTS')
  require(actual['state']==build.prior.PASS and actual['current_build_binding_accepted']
   and actual['cleanup_confirmed'] and actual['owned_tree_empty'] and actual['source_freeze_exact_after']
   and closing['source_closing_exact'] and closing['current_build_accepted'] and closing['contract_tests_passed']==205
   and closing['resource_watcher_cleanup_confirmed'] and closing['resource_stop_reason'] is None,'CURRENT_BUILD')
  require(list_actual['state']==listing.PASS and list_actual['compiled_inventory_exact']
   and list_actual['current_compiled249_qualified'] and list_actual['cleanup_confirmed'] and list_actual['owned_tree_empty']
   and list_closing['state']=='PASS_OBSERVED_WRITER_COMPILED249_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
   and list_closing['source_closing_exact'] and list_closing['current_compiled249_qualified']
   and list_closing['compiled_test_count']==249 and list_closing['contract_tests_passed']==193
   and list_closing['resource_watcher_cleanup_confirmed'] and list_closing['resource_stop_reason'] is None,'COMPILED249_ONLY')
  exe=actual['executable_pin']
  require(exe==closing['compiled_test_executable_pin']==list_actual['compiled_test_executable_pin']
   ==list_closing['compiled_test_executable_pin'] and q.pin(exe['path'])==exe,'ONE_CURRENT_EXE')
  for row in (actual,closing,list_actual,list_closing):
   require(not row['full249_current_qualified'] and not row['signed16_current_qualified']
    and not row['product_complete'] and not row['PC_freeze_resolved']
    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NO_GATE_PROMOTION')
  archive=q.json(ARCHIVE);old={r['path']:r for r in archive['files'] if r['path'] in DOCS};prefixes=[]
  require(set(old)==set(DOCS),'OLD_DOCUMENTS')
  for n in DOCS:
   raw=base64.b64decode(old[n]['base64'],validate=True)
   require(len(raw)==old[n]['bytes'] and hashlib.sha256(raw).hexdigest()==old[n]['sha256'],'WHOLE_PREIMAGE')
   current=q.text(n).encode()
   require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
   prefixes.append(current[:-len(raw)])
  require(prefixes[0]==prefixes[1] and b'P171/P172' in prefixes[0] and b'compiled249=true' in prefixes[0],'IDENTICAL_PREFIX')
  frozen=s.inputs.inventory(list_closing['bound_input_pins'])
  for n in ('tools/p09/build_observed_writer_product.py',build.SELF,build.TEST,listing.SELF,listing.TEST,
   'tools/p09/audit_observed_writer_product_r2.py','tools/p09/audit_observed_writer_inventory.py'):
   require(q.pin(n)==frozen[n],'FROZEN_HELPERS')
  q.finish();out.update(state='PASS_OBSERVED_WRITER_BUILD_AND_COMPILED249_DOCUMENT_SYNC_ONLY_NOT_FULL249_OR_GATE',
   current_compiled249_qualified=True,whole_prior_documents_preserved=True,
   evidence_pins=[q.reader.snapshots[n] for n in EVIDENCE],compiled_test_executable_pin=exe)
 except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
  out['error_code']=build.d.writer.b.prior.d.original.closed_error(e)
 finally:
  s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
  if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
  if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
  with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
  print(json.dumps({k:out.get(k) for k in ('state','current_compiled249_qualified','error_code','resource_stop_reason')}))
 return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
