"""Read-only exact local endpoint/image diagnosis; never starts/pulls a backend."""
import argparse
import json
import re
import shutil
import subprocess
import time
import run_signed_durable_sql_probe as s
from sql_runtime_supervision import LocalDockerJobFactory,LOCAL_DOCKER_HOST
from bounded_process_progress import bounded_observation_run

SELF='tools/p09/diagnose_signed_durable_sql_backend.py'


def classify(result,kind):
    errors=result.stderr.lower()
    connection=any(word in errors for word in ('cannot find the file','cannot connect','failed to connect',
        'error during connect','is the docker daemon running','pipe/dockerdesktoplinuxengine','pipe\\dockerdesktoplinuxengine',
        'the system cannot find','cannot open','connection refused'))
    return dict(command_kind=kind,exit_code=result.returncode,stdout_bytes=len(result.stdout.encode()),
        stderr_bytes=len(result.stderr.encode()),backend_connection_error=connection,
        pinned_image_not_found_error=bool(re.search(r'no such (?:image|object)',errors)),
        raw_stdout_or_stderr_included=False)


def main(run):
    destination=s.subject.scoped_path(
        f'implementation/p09/evidence/p09-150-durable-SQL-backend.read-only-run{run:02}.v1.json',fresh=True)
    resources,q,started=s.SQLRuntimeResources(),None,time.monotonic()
    row=dict(schema_version='hwpx-agent.p09-current-durable-SQL-backend-read-only/v1',state='FAILED_NOT_ACCEPTED',
        exact_local_endpoint=LOCAL_DOCKER_HOST,commands=[],owned_host_job_profiles=[],backend_started_or_stopped=False,
        image_pulled_or_removed=False,container_created=False,SQL_or_native_executed=False,
        source_closing_exact=False,resource_samples=resources.samples,P09_gate='OPEN',product_complete=False,
        raw_logs_included=False,system_or_Defender_or_WSL_settings_changed=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        q.pin(SELF);q.pin('tools/p09/sql_runtime_supervision.py');q.pin('tools/p09/bounded_process_progress.py')
        original=q.json('implementation/p09/evidence/p09-146-corpus-consumer-run07.v1.json')
        s.require(original['failed_stage']=='cached_image_identity' and original['error_code']=='pinned_local_image_missing',
            'DIAGNOSTIC_FAILURE_BINDING')
        docker=shutil.which('docker');s.require(docker is not None,'DIAGNOSTIC_DOCKER_MISSING')
        allowed=[docker,str(s.c.ROOT/original['executable_pin']['path']),str(s.c.ROOT/original['product_executable_pin']['path'])]
        for kind,arguments in (('server_version',[docker,'version','--format','{{.Server.Version}}']),
                               ('fixed_image_inspect',[docker,'image','inspect',s.subject.ownership.IMAGE])):
            factory=LocalDockerJobFactory(windows=resources.windows,allowed_executables=allowed,
                checkpoint=resources.checkpoint_io,record=lambda p:row['owned_host_job_profiles'].extend(p))
            try:
                result=bounded_observation_run(arguments,cwd=s.c.ROOT,timeout=3,
                    creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,process_factory=factory)
                row['commands'].append(classify(result,kind))
            finally:factory.close()
        server,image=row['commands']
        row['diagnosis']='LOCAL_BACKEND_ENDPOINT_UNAVAILABLE' if server['backend_connection_error'] and image['backend_connection_error'] \
            else 'FIXED_LOCAL_IMAGE_ABSENT' if server['exit_code']==0 and image['pinned_image_not_found_error'] \
            else 'FURTHER_BACKEND_DIAGNOSIS_REQUIRED'
        s.require(row['owned_host_job_profiles'] and all(p['cleanup_confirmed'] and p['owned_tree_empty']
            and p['job_handle_closed'] and p['last_job_accounting']['active_processes']==0
            for p in row['owned_host_job_profiles']),'DIAGNOSTIC_OWNED_CLEANUP')
        q.finish();row['source_closing_exact']=True;row['state']='PASS_READ_ONLY_DIAGNOSIS_ONLY_NOT_SQL_OR_GATE'
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        row['error_code']=s.closed_error(error)
    finally:
        s.finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
        if resources.reason:row['state']='FAILED_NOT_ACCEPTED'
        if q is not None:row['IO']=q.summary();row['bound_input_pins']=list(q.reader.snapshots.values())
        row['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
        print(json.dumps({k:row.get(k) for k in ('state','diagnosis','commands','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if row['state'].startswith('PASS_') and row['source_closing_exact'] \
        and row.get('resource_watcher_cleanup_confirmed') is True and resources.reason is None else 2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=int,choices=range(1,100),required=True);args=p.parse_args()
    raise SystemExit(main(args.run))
