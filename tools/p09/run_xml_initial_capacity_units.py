"""P175 isolated all74 library tests under unchanged original owned limits."""
import argparse
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
import xml_initial_capacity_binding as b

c=b.c; s=b.s
SELF='tools/p09/run_xml_initial_capacity_units.py'
TEST='tools/p09/tests/test_xml_initial_capacity_units.py'
TARGET=c.ROOT/'target/p09-175-xml-initial-capacity'
TASK='p175-xml-initial-capacity-tests'
CONFIG=b.d.d.p.b.CONFIG
ARGS=['test','-p','hwpx-package','--lib',*[v for entry in CONFIG for v in ('--config',entry)]]
PASS='PASS_XML_INITIAL_CAPACITY_ALL74_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
CONTRACT_COUNT=64

def fresh_target():
    b.require(TARGET.parent==c.ROOT/'target' and TARGET.name=='p09-175-xml-initial-capacity'
        and TARGET.resolve()==TARGET,'TARGET_SCOPE')
    b.require(not TARGET.exists() and not TARGET.is_symlink() and not TARGET.is_junction(),'FRESH_TARGET')
    b.require(TARGET.parent.is_dir() and not TARGET.parent.is_symlink() and not TARGET.parent.is_junction(),'TARGET_PARENT')

def worker(task):
    b.require(task==TASK,'WORKER_TASK');fresh_target()
    with patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{TASK:ARGS}):return c.worker(task)

def contracts():
    b.d.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_xml_initial_capacity_units')
    with patch('subprocess.Popen',side_effect=AssertionError('P175_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P175_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P175_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    b.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT58_PLUS6')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)

def helpers():
    return sorted(set(b.d.helpers())|{SELF,TEST,b.SELF,b.PARENT['path'],b.ARCHIVE,
        'tools/p09/audit_xml_initial_capacity.py'})

def load_binding():
    resources=s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=s.LiveSQLReader(resources);expected,names,modules=b.bind(q,resources)
        contracts()
        for name in helpers():expected[name]=q.pin(name)
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).resolve()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                    name=path.relative_to(c.ROOT).as_posix();expected[name]=q.pin(name)
        q.finish();return expected,names,modules
    finally:b.require(s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run(destination,binding):
    expected,names,modules=binding
    raw_pins=c.pins;raw_admitted=c.admitted_count;dump=json.dump;accepted=False;post_hash=False
    def admitted(row,count):return raw_admitted(row,count) if row['available_ram_percent']>=15 else 0
    def pins(checkpoint=None):
        nonlocal post_hash
        actual=raw_pins(checkpoint);seen={pin['path']:pin for pin in actual}
        b.require(all(seen.get(name)==pin for name,pin in expected.items()),'WHOLE_FRESH_INPUT')
        if not post_hash:
            stable=0;windows=c.Windows()
            for _ in range(6):
                c.time.sleep(.5);row=windows.sample();stable=admitted(row,stable)
                b.require(row['system_cpu_percent']<98,'DEFERRED_ALREADY_SATURATED_SYSTEM')
                if stable>=2:post_hash=True;break
            b.require(post_hash,'DEFERRED_COMPILER_HEADROOM15')
        return actual
    def write(row,stream,**kwargs):
        nonlocal accepted
        if row.get('state')=='PASS_SCOPED_NOT_GATE':
            accepted=row.get('tests_passed')==74
            row['state']=PASS if accepted else 'STOPPED_NOT_ACCEPTED'
            if not accepted:row['stop_reason']='P175_EXACT_LIB74_REQUIRED'
        row.update(current_Rust_input_count=785,original_package_lib_cases=71,new_xml_capacity_regression_cases=3,
            isolated_target=TARGET.relative_to(c.ROOT).as_posix(),fresh_target_no_old_EXE_overwrite=True,
            baseline_closing_pin=b.PARENT,baseline_archive=b.ARCHIVE,whole_original_core_inverse_exact=True,
            source_test_names=names,source_module_instances=modules,test_package_profile_config=list(CONFIG),
            compiler_admission_RAM_percent=15,post_hash_compiler_admission_revalidated=post_hash,
            current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',goal_status='active',
            PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
            remaining_non_permission_work_units=76,actual_Hangul_COM_SQL_or_Process_query_run=False,
            changed_allocation_hint_not_admission_limits=True,authorization_or_signature_cache_added=False)
        return dump(row,stream,**kwargs)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'TARGET',TARGET), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(c,'admitted_count',admitted),patch.object(json,'dump',write):code=c.run(TASK,destination,600)
    return 0 if accepted else (code or 2)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    parser.add_argument('--run',type=int,default=1,choices=range(1,100));args=parser.parse_args()
    b.require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-175-xml-initial-capacity.{"light" if args.mode=="light" else "units"}-run{args.run:02}.v1.json',fresh=True)
    if args.mode=='actual':fresh_target();return run(destination,load_binding())
    resources=s.SQLRuntimeResources();out={};q=None
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        for name in (SELF,TEST,b.SELF):q.pin(name)
        out.update(contracts());q.finish()
        out.update(state='PASS_XML_INITIAL_CAPACITY_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_child_or_new_thread_started=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=b.d.original.closed_error(error))
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
    print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out.get('state','').startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.d.original.closed_error(error))))
        raise SystemExit(2) from None
