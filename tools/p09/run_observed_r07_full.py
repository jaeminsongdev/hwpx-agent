"""P189 next ALL249 adapter: same checks/1200s, owned IO and public test progress.

Only output formatting changes from terse to pretty/color-never. Capture and
zero-failed/ignored/filtered conditions are retained and public-name checks
are added. No original body/source/EXE changes or immediate test retry.
"""
import argparse
import contextlib
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import run_current_r07_full as run
import inspect_current_r07_stop_r2 as stopped
import owned_job_io_observer as observer

c=run.c;s=run.s
SELF='tools/p09/run_observed_r07_full.py'
TEST='tools/p09/tests/test_observed_r07_full.py'
LIGHT='implementation/p09/evidence/p09-189-observed-r07-full.light-run01.v1.json'
PREP='implementation/p09/evidence/p09-189-observed-r07-full.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-189-observed-r07-full.actual-run01.v1.json'
PASS='PASS_CURRENT_R07_OBSERVED_UNFILTERED_ALL249_ONLY_NOT_SQL_HANGUL_PRODUCT_OR_GATE'
STOP_PROBE=dict(path=stopped.DEST,bytes=12904,sha256='a0ad259557f0e56f6dd9a2f405b1a34d3cc0b6a230718de9cdbe43c17ec21dda')
HISTORY=(stopped.ACTUAL,stopped.PREP,stopped.LIGHT,STOP_PROBE,*stopped.PRIOR_PINS)
OLD_CONTRACTS=run.contracts
OLD_HELPERS=run.helpers
OLD_OWNED=run.run_owned
OLD_WORKER=run.worker
BASE_READER=run.pressure.PressureReader
BASE_CAPTURE=run.original.full.FullCapture
LINE=re.compile(r'^test ([A-Za-z_][A-Za-z0-9_:]*) \.\.\. (?:(ok|FAILED|ignored))?$')

def require(ok,code):run.require(ok,'OBSERVED_'+code)

def progress(data,names):
    require(isinstance(data,bytes) and len(data)<=32768,'ORIGINAL_OUTPUT_BUDGET')
    known=frozenset(names);require(len(known)==len(names) and bool(known),'PUBLIC_NAMES')
    finished={};active=None;duplicate=False
    # Raw unknown/panic/private lines never become persisted progress values.
    for line in data.decode('utf-8',errors='replace').split('\n'):
        match=LINE.fullmatch(line.removesuffix('\r'))
        if not match or match[1] not in known:continue
        name,status=match.groups()
        if status is None:active=name;continue
        duplicate=duplicate or name in finished;finished[name]=status
        if active==name:active=None
    return dict(public_active_test_name=active,public_completed_test_count=len(finished),
        public_passed_test_count=sum(x=='ok' for x in finished.values()),
        public_failed_test_count=sum(x=='FAILED' for x in finished.values()),
        public_ignored_test_count=sum(x=='ignored' for x in finished.values()),
        public_duplicate_result_seen=duplicate,public_all_expected_results_seen=set(finished)==known,
        raw_logs_or_unknown_names_saved=False,active_name_inferred_from_terse_dots=False)

def nominal_output_bytes(names):
    return len(b'\nrunning 249 tests\n')+sum(len(f'test {n} ... ok\n'.encode()) for n in names)+len(
        b'\ntest result: ok. 249 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1200.00s\n\n')

def worker(task):
    original_call=run.original.subprocess.call
    def selected(args,**kw):
        require(args==[str(c.ROOT/run.b.executable_name()),'--test-threads=1','--format=terse'],
            'ORIGINAL_UNFILTERED_CALL_ONLY')
        require(kw['env']['RUST_TEST_NOCAPTURE']=='0' and kw['env']['RUST_TEST_THREADS']=='1',
            'NO_CAPTURE_OR_THREAD_OVERRIDE')
        return original_call([args[0],'--test-threads=1','--format=pretty','--color=never'],**kw)
    with patch.object(run.original.subprocess,'call',selected):return OLD_WORKER(task)

class BoundReader(BASE_READER):
    def pin(self,name):
        pin=super().pin(name)
        for fixed in HISTORY:
            if name==fixed['path']:require(pin==fixed,'ORIGINAL_STOP_HISTORY_IMMUTABLE')
        return pin

def contracts():
    # Actual adapter role patches must not recursively replace the old oracle.
    with patch.object(run,'contracts',OLD_CONTRACTS):stopped.contracts()
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_r07_full')
    with patch('subprocess.Popen',side_effect=AssertionError('P189_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P189_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P189_NO_NEW_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==9 and not checked.skipped,'CONTRACT100_PLUS9')
    return dict(contract_tests_passed=109,contract_tests_run=109)

def helpers():
    return sorted(set(OLD_HELPERS())|{n['path'] for n in HISTORY}|{stopped.ARCHIVE,stopped.SELF,stopped.TEST,
        observer.SELF,observer.TEST,run.SELF,run.TEST,SELF,TEST})

def run_owned(destination,binding):
    names=binding[1];require(len(names)==249 and nominal_output_bytes(names)<=32768,'NOMINAL_PRETTY_FITS_ORIGINAL_CAP')
    old_windows=run.owned.windows_type;dump=json.dump
    class Capture(BASE_CAPTURE):
        def public_progress(self):
            with self.lock:data=bytes(self.buffers['stdout'])
            return progress(data,names)
        def diagnostics(self):
            row=super().diagnostics();row.update(self.public_progress());return row
        def communicate(self,timeout):
            result=super().communicate(timeout)
            if self.process.returncode==0:
                seen=self.public_progress()
                require(seen['public_all_expected_results_seen'] and seen['public_completed_test_count']==249
                    and seen['public_passed_test_count']==249 and seen['public_failed_test_count']==0
                    and seen['public_ignored_test_count']==0 and not seen['public_duplicate_result_seen']
                    and seen['public_active_test_name'] is None,'ALL249_PUBLIC_RESULTS_PLUS_ORIGINAL_SUMMARY')
            return result
    def windows_type(box):return observer.windows_type(old_windows(box))
    def write(row,stream,**kw):
        row.update(actual_test_output_format='pretty',actual_test_color='never',original_bounded_output_limit_retained=True,
            public_test_progress_from_actual_named_lines_only=True,owned_job_IO_observer_connected=True,
            additional_owned_job_IO_query_per_original_accounting=1,additional_foreign_PID_query=False,
            extra_sampler_or_test_body_thread_started=False,original_full249_summary_validator_retained=True,
            all249_public_result_validation_added=True,original_P187_running_stop_pin=stopped.ACTUAL,
            empty_job_IO_probe_pin=STOP_PROBE,nominal_success_output_bytes=nominal_output_bytes(names),
            nominal_size_is_not_worst_case_or_overflow_waiver=True)
        return dump(row,stream,**kw)
    with patch.object(run.owned,'windows_type',windows_type),patch.object(run.original.full,'FullCapture',Capture), \
            patch.object(json,'dump',write):return OLD_OWNED(destination,binding)

def light():
    destination=s.scoped_path(LIGHT,fresh=True);resources=run.pressure.observation.OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        actual_Cargo_SQL_Hangul_child_or_test_body_executed=False,actual_runtime_IO_observation_executed=False,
        runtime_preparation_executed=False,artifact_EXE_scan_started=False,foreign_Process_query_executed=False)
    try:
        resources.admit();q=BoundReader(resources);require(q.pin(run.PARENT['path'])==run.PARENT,'CURRENT_COMPILED_PARENT')
        parent=q.json(run.PARENT['path']);run.parent_scope(parent);names=parent['source_test_names']
        require(len(names)==249 and all(re.fullmatch('[A-Za-z_][A-Za-z0-9_:]*',n) for n in names)
            and nominal_output_bytes(names)<=32768,'PUBLIC_NAMES_NOMINAL_BUDGET_ONLY')
        out.update(contracts())
        for pin in HISTORY:require(q.pin(pin['path'])==pin,'STOP_AND_API_PROBE_PRESERVED')
        for name in (SELF,TEST,observer.SELF,observer.TEST,stopped.SELF,stopped.TEST,stopped.ARCHIVE,
                run.SELF,run.TEST,run.owned.SELF,run.owned.TEST):q.pin(name)
        q.finish();out.update(state='PASS_OBSERVED_R07_FULL_CONTRACT109_ONLY_NOT_RUNTIME_OR_GATE',
            nominal_success_output_bytes=nominal_output_bytes(names),original_per_stream_output_cap=32768,
            nominal_size_is_not_worst_case_or_overflow_waiver=True,original_P187_stop_preserved=True,
            original_1200_seconds_and_resource_policy_retained=True,empty_job_probe_not_product_IO_observation=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=run.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason',
            'nominal_success_output_bytes')}))
    return 0 if out['state'].startswith('PASS_') else 2

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');run.original.require_scope(1200)
    if args.mode=='light':return light()
    with contextlib.ExitStack() as stack:
        for name,value in (('SELF',SELF),('TEST',TEST),('PREP',PREP),('ACTUAL',ACTUAL),('PASS',PASS),
                ('contracts',contracts),('helpers',helpers),('run_owned',run_owned)):
            stack.enter_context(patch.object(run,name,value))
        stack.enter_context(patch.object(run.pressure,'PressureReader',BoundReader))
        return run.main()

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,run.original.subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=run.original.closed_error(error))));raise SystemExit(2) from None
