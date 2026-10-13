"""P175 terminal-only evidence/document sync with whole prior suffix retained."""
import json
import xml_initial_capacity_binding as b
import run_xml_initial_capacity_units as units
import audit_xml_initial_capacity_r3 as audit

SELF='tools/p09/verify_xml_initial_capacity_progress.py'
LIGHT='implementation/p09/evidence/p09-175-xml-initial-capacity.light-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-175-xml-initial-capacity.units-run01.v1.json'
CLOSING='implementation/p09/evidence/p09-175-xml-initial-capacity.source-closing-r3-run01.v1.json'

def main():
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False)
    destination=b.s.scoped_path('implementation/p09/evidence/p09-175-xml-initial-capacity.progress-sync-run01.v1.json',fresh=True)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);q.pin(SELF)
        light=q.json(LIGHT);actual=q.json(ACTUAL);closing=q.json(CLOSING)
        passed=actual['state']==units.PASS
        b.require(light['state']=='PASS_XML_INITIAL_CAPACITY_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
            and light['contract_tests_passed']==64 and not light['actual_child_or_new_thread_started'],'LIGHT')
        b.require(passed and closing['state']=='FAILED_NOT_ACCEPTED' and not closing['source_closing_exact']
            and closing['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and closing['resource_watcher_cleanup_confirmed'],'INDEPENDENT_CLOSING_PENDING_CPU_STOP')
        b.require(actual['maximum_seconds']==600 and actual['cleanup_confirmed'] and actual['owned_tree_empty']
            and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[]
            and actual['changed_allocation_hint_not_admission_limits'] and not actual['authorization_or_signature_cache_added'],'TERMINAL')
        if passed:b.require(actual['tests_passed']==74 and closing['actual_unit_tests_passed'] is None
            and actual['exit_code']==0 and actual['stop_reason'] is None,'ALL74_NOT_CLOSING')
        for row in (actual,closing):
            b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete'] and not row['PC_freeze_resolved']
                and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NOT_GATE')
        frozen=b.s.inputs.inventory(actual['source_freeze'])
        for name in (b.SOURCE,b.SELF,units.SELF,units.TEST,b.ARCHIVE,b.PARENT['path']):
            b.require(q.pin(name)==frozen[name],'EXACT_ACTUAL_HELPERS_NOT_WHOLE_CLOSING')
        q.pin(audit.SELF)
        for name,reason in (
            ('implementation/p09/evidence/p09-175-xml-initial-capacity.source-closing-run01.v1.json',
             'P152_PREP_P157_BUILD_WRITER_BUILD_WRITER_FULL_CASE_COST_XML_CAPACITY_UNCHANGED_PARSER_RESERVATION_ORACLE'),
            ('implementation/p09/evidence/p09-175-xml-initial-capacity.source-closing-r2-run01.v1.json',
             'STOP_SUSTAINED_SYSTEM_CPU')):
            failed=q.json(name)
            b.require(failed['state']=='FAILED_NOT_ACCEPTED' and not failed['source_closing_exact']
                and failed['error_code']==reason,'FAILED_RECEIPT_RETAINED')
        archive=q.json(b.ARCHIVE);prefixes=[]
        for name in b.DOCS:
            _,raw=b.preimage(archive,name);current=q.text(name).encode()
            b.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX')
            prefixes.append(current[:-len(raw)])
        b.require(prefixes[0]==prefixes[1] and b'P175' in prefixes[0] and b'TERMINAL' in prefixes[0]
            and b'compiled249=false/full249=false/signed16=false' in prefixes[0],'IDENTICAL_CLOSED_PREFIX')
        q.finish();out.update(state='PASS_XML_INITIAL_CAPACITY_UNITS_AND_PENDING_AUDIT_DOCUMENT_SYNC_ONLY_NOT_CLOSING_OR_GATE',
            whole_prior_documents_preserved=True,actual_unit_tests_passed=74 if passed else None,
            independent_whole_source_closing_qualified=False,independent_closing_stop_reason=closing['resource_stop_reason'],
            original_stop_reason=actual['stop_reason'],evidence_pins=[q.reader.snapshots[name] for name in (LIGHT,ACTUAL,CLOSING)])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
