"""P176 whole-old-document suffix and actual closing evidence, never Gate promotion."""
import json
import math
import xml_initial_capacity_binding as b
import weighted_audit_io as w
import audit_xml_initial_capacity_weighted as audit
import archive_weighted_audit_documents as archive
SELF='tools/p09/verify_weighted_audit_progress.py'
LIGHT='implementation/p09/evidence/p09-176-weighted-audit-io.light-r2-run01.v1.json'
CLOSING='implementation/p09/evidence/p09-176-weighted-xml-capacity.source-closing-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-175-xml-initial-capacity.units-run01.v1.json'

def main():
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False)
    destination=b.s.scoped_path('implementation/p09/evidence/p09-176-weighted-audit.progress-sync-run01.v1.json',fresh=True)
    try:
        resources.admit();q=w.WeightedLiveReader(resources);q.pin(SELF)
        actual=q.json(ACTUAL);light=q.json(LIGHT);closing=q.json(CLOSING)
        accepted=closing['state']==audit.PASS
        b.require(actual['state']=='PASS_XML_INITIAL_CAPACITY_ALL74_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
            and actual['tests_passed']==74 and actual['exit_code']==0 and actual['cleanup_confirmed']
            and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'P175_ACTUAL74')
        b.require(light['contract_tests_passed']==37 and light['state']=='PASS_WEIGHTED_AUDIT_READER_AND_CURRENT_CONTEXT_FIXTURES_ONLY_NOT_SOURCE_CLOSING_OR_GATE'
            and light['all_original_reader_oracles_retained'] and light['current_r4_whole_declared_extension_inverse_exact'],'LIGHT37')
        if accepted:
            b.require(closing['source_closing_exact'] and closing['actual_unit_tests_passed']==74
                and closing['actual_unit_receipt_pin']==q.pin(ACTUAL) and closing['contract_tests_passed']==64
                and closing['reader_contract_tests_passed']==37 and closing['total_contract_tests_passed']==101
                and closing['current_Rust_input_count']==785 and closing['protected_parent_EXE_inputs_exact']==66
                and len(closing['source_test_names'])==249 and len(closing['source_module_instances'])==59
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed'],'WHOLE_CLOSING')
            io=closing['IO'];pins=b.s.inputs.inventory(closing['bound_input_pins'])
            b.require(io['finished'] and io['bound_inputs']==io['final_fresh_hashes']==len(pins)
                and sum(n.endswith('.exe') for n in pins)==67,'FULL_FRESH_67')
            for name in (b.SOURCE,w.SELF,audit.SELF):b.require(q.pin(name)==pins[name],'EXACT_CURRENT_SOURCE_AND_HELPERS')
            exe=closing['fresh_package_lib_executable_pin'];b.require(q.pin(exe['path'])==exe,'LIB_NOT_PRODUCT')
        else:
            b.require(closing['state']=='FAILED_NOT_ACCEPTED' and not closing['source_closing_exact']
                and closing['resource_watcher_cleanup_confirmed'],'STOP_NOT_CLOSING')
        for row in (actual,closing):
            b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete']
                and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NOT_PRODUCT_OR_GATE')
        io=closing['IO']
        b.require(io['read_bytes_per_second'] is None and io['read_rates_by_kind']=={'binary':2621440,'other':4194304}
            and io['bytes_read']==io['pacer_bytes_read']==sum(io['bytes_read_by_kind'].values())
            and io['maximum_scope_seconds']==600 and io['burst_bytes']==65536
            and io['all_original_read_operations_preserved'],'ACTUAL_RATE_NOT_STALE_GLOBAL')
        tail=closing['resource_tail']
        b.require(tail['tail_limit']==8 and len(tail['samples'])<=8 and tail['existing_samples_only']
            and not tail['additional_native_queries_started'],'EXISTING_NUMERIC_TAIL')
        for row in tail['samples']:
            for key in ('system_cpu_percent','available_ram_percent','commit_used_percent'):
                b.require(type(row[key]) in (int,float) and math.isfinite(row[key]) and 0<=row[key]<=100,'TAIL_FINITE')
        old=q.json(archive.ARCHIVE);prefixes=[]
        b.require(old['state']=='WHOLE_P176_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','DOC_ARCHIVE')
        for name in b.DOCS:
            _,raw=b.preimage(old,name);current=q.text(name).encode()
            b.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_OLD_SUFFIX');prefixes.append(current[:-len(raw)])
        b.require(prefixes[0]==prefixes[1] and b'P176' in prefixes[0] and b'TERMINAL' in prefixes[0]
            and b'compiled249=false/full249=false/signed16=false' in prefixes[0],'SAME_PREFIX_NOT_PRODUCT_PASS')
        q.finish();out.update(state='PASS_WEIGHTED_AUDIT_TERMINAL_DOCUMENT_SYNC_ONLY_NOT_PRODUCT_OR_GATE',
            independent_whole_source_closing_qualified=accepted,actual_unit_tests_passed=74,
            whole_prior_documents_preserved=True,evidence_pins=[q.reader.snapshots[n] for n in (ACTUAL,LIGHT,CLOSING)])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','independent_whole_source_closing_qualified','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
