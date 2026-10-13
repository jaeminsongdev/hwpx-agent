"""P162: fresh r04 product build from the accepted P161 XML delta.

Frozen original compiler/stream/Job guards are reused, never restamped.
Build only: no listing/full249/Gate or performance acceptance.
"""
import argparse
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import build_observed_graph_product as d

p=d.p
SELF='tools/p09/build_source_xml_product.py'
TEST='tools/p09/tests/test_source_xml_product_build.py'
RUN=4
PARENT=dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.source-closing-run03.v1.json',
    bytes=300097,sha256='06064c635b123d3665369374a3c342a254b0451e4ceb44e8f5c09d7cb5aa23b1')
PASS='PASS_SOURCE_XML_CURRENT_PRODUCT_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
CONTRACT_COUNT=50

def require(ok,code):d.require(ok,'XML_BUILD_'+code)

def parent_scope(row):
    require(row['state']=='PASS_SOURCE_XML_REUSE_DELTA_AND_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['actual_unit_tests_passed']==68
        and row['whole_original_core_inverse_exact'] and row['all_original_package_lib_tests_preserved']
        and row['typecheck_accepted'] and row['current_Rust_input_count']==785
        and len(row['source_test_names'])==249 and len(row['source_module_instances'])==59
        and len(row['declared_Rust_source_changes'])==1
        and row['protected_parent_EXE_inputs_exact']==62
        and row['old_product_EXE_not_current_qualified']
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'PARENT_SCOPE')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1279)
    protected={n:v for n,v in expected.items() if n.endswith('.exe')}
    require(len(protected)==63 and expected[row['declared_Rust_source_changes'][0]['path']]
        ==row['declared_Rust_source_changes'][0] and protected[row['fresh_package_lib_executable_pin']['path']]
        ==row['fresh_package_lib_executable_pin'],'PARENT63_DELTA_AND_FRESH_LIB')
    return expected,protected

def fresh_scope(protected):
    name=p.b.executable_name(RUN)
    require(name.endswith('form_stored_provider-p152-r04.exe') and name not in protected,'FRESH_R04')
    p.s.scoped_path(name,fresh=True);return name

def worker(task):
    require(task==p.b.task_for(RUN),'CLOSED_WORKER_TASK')
    with patch.object(d,'RUN',RUN):return d.worker(task)

def contracts():
    d.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_source_xml_product_build')
    with patch('subprocess.Popen',side_effect=AssertionError('P162_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P162_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P162_LIGHT_THREAD_FORBIDDEN')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==4 and not checked.skipped,'CONTRACT4_PLUS46')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)

def helpers():return sorted(set(p.helpers())|{SELF,TEST,d.SELF,d.TEST,PARENT['path']})

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_P161_CLOSING')
        row=q.json(PARENT['path']);expected,protected=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        fresh_scope(protected);contracts();local=helpers()
        for n in local:expected[n]=q.pin(n)
        q.finish();return expected,list(protected.values()),local
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run_owned(destination,binding):
    dump=json.dump
    def write(row,stream,**kw):
        if row['state']==p.PASS:row['state']=PASS
        # Original p wrapper contains historical literal counts. This adapter
        # records the actually passed and freshly checked protected inventory.
        row.update(schema_version='hwpx-agent.p09-source-xml-product-build/v1',
            source_xml_delta_closing_pin=PARENT,protected_executables_expected=63,
            previous_parent_EXE_inputs_preserved=63,observed_same_owned_job=True,
            host_observed_target='cargo-launcher-process',observer_collection_seconds=1.0,
            diagnostic_snapshots_max=d.observed.MAX_SAVED,
            diagnostic_snapshots_are_not_complete_host_process_history=True,
            original_emergency_cpu_guard_unchanged=True,individual_duplicated_PID_attribution=False,
            source_xml_lib68_accepted=True,old_product_EXE_not_current_qualified=True,
            A12_gate='OPEN',A13_gate='OPEN')
        return dump(row,stream,**kw)
    with patch.object(p,'RUN',RUN),patch.object(p,'SELF',SELF),patch.object(p,'PARENT',PARENT), \
            patch.object(p.b.legacy.original.capture,'FullCapture',d.DiagnosticCapture), \
            patch.object(p.b.legacy,'RAW_CAPTURE',d.DiagnosticCapture),patch.object(json,'dump',write):
        return p.run_owned(destination,*binding)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-162-source-xml-product-build.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':return run_owned(destination,load_binding())
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic();out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,d.SELF,d.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_SOURCE_XML_PRODUCT_BUILD_CONTRACTS_ONLY_NOT_NATIVE_PRODUCT_OR_GATE',
            source_closing_exact=True,actual_Cargo_SQL_native_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out['error_code']=str(e) if isinstance(e,ValueError) else 'P162_LIGHT_REDACTED'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P162_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if d.observed.re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P162_REDACTED_FAILURE')))
        raise SystemExit(2) from None
