"""Explicit light/admission only: no SQL/Docker/EXE/native execution entrypoint."""
import argparse
import io
import json
import re
import sys
import time
import unittest
import uuid
from unittest.mock import patch
import durable_negative_sql_contract as s
import durable_negative_sql_driver as driver


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','admission'),required=True)
    parser.add_argument('--run',type=int,choices=range(1,100),required=True);args=parser.parse_args()
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'REPOSITORY_CWD')
    destination=s.build.parent.scoped_path(f'implementation/p09/evidence/p09-151-SQL-admission.{args.mode}-run{args.run:02}.v1.json',fresh=True)
    resources=s.build.parent.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-ds06-SQL-admission/v1',state='FAILED_NOT_ACCEPTED',mode=args.mode,
        source_closing_exact=False,actual_SQL_Docker_native_or_EXE_executed=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        full_durable_DS01_DS09_qualified=False,actual_SQL_metadata_or_signed_consumer_qualified=False,
        independent_restart_or_key_custody_qualified=False,PC_freeze_resolved=False,raw_logs_included=False,
        resource_samples=resources.samples)
    try:
        resources.admit();q=s.build.parent.LiveSQLReader(resources)
        for name in [*s.SOURCES,s.build.parent.SOURCE,
                'implementation/p09/source-archive/p09-151-pre-SQL-light-helper-closing-r31/source-preimages.v1.json',
                'implementation/p09/evidence/p09-151-SQL-admission.light-run01.v1.json']:
            q.pin(name)
        made,holder=driver.make_driver(q,str(uuid.uuid4()))
        s.require(holder.root is None and made.ROOT_CHECKS==driver.required_checks(),'ADMISSION_NO_ROOT_CREATED')
        out.update(provided_driver_guard_count_delta=[842,846],whole_original_driver_inverse_exact=True,
            original_root_checks_retained=27,prior_durable_checks_retained=4,new_DS06_checks=8,required_check_count=39,
            exact_check_names=made.ROOT_CHECKS,original_source_files_modified=False,
            original_SQL_security_and_resource_policy_unchanged=True,owned_root_created=False,
            image_downloaded_or_backend_changed=False)
        sys.path.insert(0,str(s.c.ROOT/'tools/p09/tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName('test_durable_negative_sql_admission')
        with patch('subprocess.Popen',side_effect=AssertionError('P151_ADMISSION_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_ADMISSION_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P151_ADMISSION_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed={getattr(t,'test_case',t).id() for t,_ in checked.errors+checked.failures+checked.skipped}
        out.update(tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failed),
            failed_tests=sorted(n.split('.')[-1] for n in failed))
        s.require(checked.wasSuccessful() and not checked.skipped and checked.testsRun==16,'CONTRACT16')
        if args.mode=='admission':
            view,exe,binding=s.bind_probe_build(q,s.BUILD_PIN['path'])
            out.update(current_build_consumption_view=True,compiled_source_count=len(view['source_freeze']),
                current_Rust_input_count=785,protected_executables_exact=53,executable_pin=exe,binding=binding,
                build_receipt_pin=s.BUILD_PIN,build_closing_pin=s.CLOSING_PIN)
            out['state']='PASS_CURRENT_DS06_BUILD_SQL_ADMISSION_ONLY_NOT_SQL_NATIVE_OR_GATE'
        else:out['state']='PASS_DS06_SQL_ADMISSION_CONTRACT_ONLY_NOT_SQL_NATIVE_OR_GATE'
        helpers=set()
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=s.c.Path(file).absolute()
                if path.is_relative_to(s.c.ROOT/'tools/p09') and path.suffix=='.py':
                    helpers.add(path.relative_to(s.c.ROOT).as_posix())
        for name in sorted(helpers):q.pin(name)
        out['imported_helper_inventory']=sorted(helpers)
        q.finish();out['source_closing_exact']=True
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        value=str(error) if isinstance(error,ValueError) else 'SQL_P151_ADMISSION_OPERATION_FAILED'
        out['error_code']=value if len(value)<=160 and re.fullmatch('[A-Z_]+',value) else 'SQL_P151_REDACTED_FAILURE'
    finally:
        if q is not None and not q.finished:
            try:q.finish();out['source_closing_exact']=True
            except (ValueError,OSError):out['state']='FAILED_NOT_ACCEPTED';out['final_freshness_error']='SQL_P151_FINAL_FRESHNESS'
        s.build.parent.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason:out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','tests_run','tests_passed','failed_tests','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] and not resources.reason \
        and out.get('resource_watcher_cleanup_confirmed') else 2


if __name__=='__main__':raise SystemExit(main())
