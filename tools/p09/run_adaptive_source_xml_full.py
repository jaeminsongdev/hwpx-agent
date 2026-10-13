"""P165 original current r04 full249 with qualified adaptive diagnostics.

P164 only qualifies the diagnostic component. This runner keeps original1200,
all249/zero failed ignored filtered, guards and additional footer validation.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_source_xml_product_full as previous
import probe_adaptive_host_cpu_sampler_r2 as qualified
import adaptive_host_cpu_sampler as adaptive

p=previous.p
s=previous.s
SELF='tools/p09/run_adaptive_source_xml_full.py'
TEST='tools/p09/tests/test_adaptive_source_xml_full.py'
PARENT=dict(path='implementation/p09/evidence/p09-164-adaptive-native-query.terminal-audit-run01.v1.json',
    bytes=305888,sha256='467e21f0128fc95ea4b42ed026954b3071e362e2f5685a02f439207c6c0b5fd4')
PASS='PASS_CURRENT_ADAPTIVE_SOURCE_XML_UNFILTERED_FULL249_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
RUN=4

def require(ok,code):previous.require(ok,'ADAPTIVE_FULL_'+code)

def worker(task):
    require(task==s.task_for(RUN),'CLOSED_R04_TASK')
    with patch.object(s,'observed_call',adaptive.observed_call):return previous.worker(task)

def contracts():
    qualified.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_adaptive_source_xml_full')
    with patch('subprocess.Popen',side_effect=AssertionError('P165_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P165_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P165_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'CONTRACT4_PLUS81')
    return dict(contract_tests_run=85,contract_tests_passed=85)

def parent_scope(row):
    require(row['state']=='PASS_ADAPTIVE_NATIVE_QUERY_CURRENT_SOURCE_CLOSING_ONLY_NOT_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['current_compiled249_qualified']
        and row['contract_tests_passed']==81 and row['current_Rust_input_count']==785
        and row['protected_EXE_inputs_exact']==64 and row['one_native_query_closed_explicitly']
        and row['actual_native_probe_helper_count']==67 and row['cold_native_queries_avoided']==2
        and row['production_callback_actual_full249_executed'] is False
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'QUALIFIED_COMPONENT_NOT_PRODUCT_PASS')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1304);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R04_IDENTITY')
    return expected,exe

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_COMPONENT_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        contracts()
        for n in (*p.helpers(),SELF,TEST,PARENT['path']):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);mode=parser.parse_args().mode
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD');s.original.require_scope(1200)
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-165-adaptive-source-xml-full.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':
        binding=load_binding();dump=json.dump
        def write(row,stream,**kw):
            row.update(schema_version='hwpx-agent.p09-adaptive-source-xml-current-full249/v1',
                current_graph_inventory_closing_pin=PARENT,adaptive_native_closing_pin=PARENT,
                host_observed_target='stored-product-test-process',legacy_total_samples_counts_host_polls=True,
                native_cold_periods_explicitly_not_observed=True,adaptive_footer_required_for_success=True,
                cold_gap_average_never_promoted_to_fresh_hot_sample=True,
                full_product_performance_improvement_measured=False,actual_Hangul_COM_or_SQL_run=False,
                previous_failed_full_or_CPU_stop_evidence_modified=False)
            return dump(row,stream,**kw)
        with patch.object(s,'SELF',SELF),patch.object(s,'TEST',TEST),patch.object(s,'PASS',PASS), \
                patch.object(s,'Capture',adaptive.Capture),patch.object(s.original,'PARENT',PARENT),patch.object(json,'dump',write):
            return s.run_owned(RUN,destination,*binding)
    resources=p.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,adaptive.SELF,qualified.SELF,qualified.TEST):q.pin(n)
        require(q.pin(PARENT['path'])==PARENT,'LIGHT_QUALIFIED_PARENT')
        out.update(contracts());q.finish()
        out.update(state='PASS_ADAPTIVE_SOURCE_XML_FULL_CONNECTION_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            source_closing_exact=True,actual_product_test_body_executed=False,actual_native_counter_run=False,
            full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
            P09_gate='OPEN',PC_freeze_resolved=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:out['error_code']=s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=s.original.closed_error(e))));raise SystemExit(2) from None
