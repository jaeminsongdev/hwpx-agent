"""P168 fresh isolated all71 LIB tests; original profile81 and owned caps."""
import argparse
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch
import writer_xml_reuse_binding as b

c=b.c
s=b.s
SELF='tools/p09/run_writer_xml_reuse_units.py'
TEST='tools/p09/tests/test_writer_xml_reuse_units.py'
TARGET=c.ROOT/'target/p09-168-writer-xml-reuse'
TASK='p168-writer-xml-reuse-tests'
ARGS=['test','-p','hwpx-package','--lib',*[v for entry in b.p.b.CONFIG for v in ('--config',entry)]]
PASS='PASS_WRITER_XML_REUSE_ALL71_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'

def fresh_target():
    b.require(TARGET.parent==c.ROOT/'target' and TARGET.name=='p09-168-writer-xml-reuse'
        and TARGET.resolve()==TARGET,'TARGET_SCOPE')
    b.require(not TARGET.exists() and not TARGET.is_symlink() and not TARGET.is_junction(),'FRESH_TARGET')
    b.require(TARGET.parent.is_dir() and not TARGET.parent.is_symlink() and not TARGET.parent.is_junction(),
        'TARGET_PARENT')

def worker(task):
    b.require(task==TASK,'WORKER_TASK')
    fresh_target()
    with patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{TASK:ARGS}):return c.worker(task)

def contracts():
    b.prior.d.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_writer_xml_reuse_units')
    with patch('subprocess.Popen',side_effect=AssertionError('P168_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P168_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P168_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    b.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT6_PLUS130')
    return dict(contract_tests_run=136,contract_tests_passed=136)

def load_binding():
    resources=s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=s.LiveSQLReader(resources);expected,names,modules=b.bind(q,resources)
        contracts()
        for n in (SELF,TEST):expected[n]=q.pin(n)
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).resolve()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                    n=path.relative_to(c.ROOT).as_posix();expected[n]=q.pin(n)
        q.finish();return expected,names,modules
    finally:b.require(s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run(destination,binding):
    expected,names,modules=binding
    raw_pins=c.pins;raw_admitted=c.admitted_count;dump=json.dump;accepted=False;post_hash=False
    def admitted(row,count):return raw_admitted(row,count) if row['available_ram_percent']>=15 else 0
    def pins(checkpoint=None):
        nonlocal post_hash
        actual=raw_pins(checkpoint);seen={pin['path']:pin for pin in actual}
        b.require(all(seen.get(n)==pin for n,pin in expected.items()),'WHOLE_FRESH_INPUT')
        if not post_hash:
            stable=0;windows=c.Windows()
            for _ in range(6):
                c.time.sleep(.5);row=windows.sample();stable=admitted(row,stable)
                b.require(row['system_cpu_percent']<98,'DEFERRED_ALREADY_SATURATED_SYSTEM')
                if stable>=2:post_hash=True;break
            b.require(post_hash,'DEFERRED_COMPILER_HEADROOM15')
        return actual
    def write(row,stream,**kw):
        nonlocal accepted
        if row.get('state')=='PASS_SCOPED_NOT_GATE':
            accepted=row.get('tests_passed')==71
            row['state']=PASS if accepted else 'STOPPED_NOT_ACCEPTED'
            if not accepted:row['stop_reason']='P168_EXACT_LIB71_REQUIRED'
        row.update(current_Rust_input_count=785,original_package_lib_cases=68,new_writer_xml_regression_cases=3,
            isolated_target=TARGET.relative_to(c.ROOT).as_posix(),fresh_target_no_old_EXE_overwrite=True,
            baseline_closing_pin=b.PARENT,baseline_archive=b.ARCHIVE,whole_original_core_inverse_exact=True,
            source_test_names=names,source_module_instances=modules,test_package_profile_config=list(b.p.b.CONFIG),
            compiler_admission_RAM_percent=15,post_hash_compiler_admission_revalidated=post_hash,
            current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',goal_status='active',
            PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
            remaining_non_permission_work_units=76,actual_Hangul_COM_SQL_or_Process_query_run=False)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'TARGET',TARGET), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(c,'admitted_count',admitted),patch.object(json,'dump',write):code=c.run(TASK,destination,600)
    return 0 if accepted else (code or 2)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    parser.add_argument('--run',type=int,default=1,choices=range(1,100))
    args=parser.parse_args();mode=args.mode;b.require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-168-writer-xml-reuse.{"light" if mode=="light" else "units"}-run{args.run:02}.v1.json',fresh=True)
    if mode=='actual':fresh_target();return run(destination,load_binding())
    resources=s.SQLRuntimeResources();out={};q=None
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        for n in (SELF,TEST,b.SELF):q.pin(n)
        result=contracts();q.finish()
        out.update(result,state='PASS_WRITER_XML_REUSE_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_child_or_new_thread_started=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=b.prior.d.original.closed_error(e))
    finally:
        b.require(s.finish_watcher(resources,out),'LIGHT_CLEANUP')
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
    print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code')}))
    return 0 if out.get('state','').startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=b.prior.d.original.closed_error(e))))
        raise SystemExit(2) from None
