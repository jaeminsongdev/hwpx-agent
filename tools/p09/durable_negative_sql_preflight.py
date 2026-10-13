"""Bounded read-only exact local endpoint/image prerequisite; no pull or backend change."""
import re
import shutil
import subprocess
import time
import durable_negative_sql_contract as c
from sql_runtime_supervision import LocalDockerJobFactory,LOCAL_DOCKER_HOST
from bounded_process_progress import bounded_observation_run

SELF='tools/p09/durable_negative_sql_preflight.py'
DOCKER=c.c.Path('C:/Program Files/Docker/Docker/resources/bin/docker.exe')
# Only the reviewed ownership module defines the image.
import sql_container_ownership as ownership
IMAGE=ownership.IMAGE
IMAGE_ID=IMAGE.split('@',1)[1]


def commands(docker):
    c.require(c.c.Path(docker)==DOCKER,'PREFLIGHT_EXACT_LOCAL_DOCKER')
    return (('server_version',[docker,'version','--format','{{.Server.Version}}']),
        ('fixed_image_identity',[docker,'image','inspect','--format','{{.Id}}',IMAGE]))


def classify(result,kind):
    c.require(kind in {'server_version','fixed_image_identity'} and isinstance(result.stdout,str)
        and isinstance(result.stderr,str) and type(result.returncode) is int,'PREFLIGHT_RESULT_SCOPE')
    errors=result.stderr.lower();text=result.stdout.strip()
    connection=any(word in errors for word in ('cannot find the file','cannot connect','failed to connect',
        'error during connect','is the docker daemon running','pipe/dockerdesktoplinuxengine',
        'pipe\\dockerdesktoplinuxengine','the system cannot find','cannot open','connection refused'))
    exact=bool(result.returncode==0 and not result.stderr and
        (re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9._-]{1,64})?',text) if kind=='server_version' else text==IMAGE_ID))
    return dict(command_kind=kind,exit_code=result.returncode,stdout_bytes=len(result.stdout.encode()),
        stderr_bytes=len(result.stderr.encode()),backend_connection_error=connection,
        pinned_image_not_found_error=bool(re.search(r'no such (?:image|object)',errors)),
        exact_identity_accepted=exact,raw_stdout_or_stderr_included=False)


def diagnosis(rows):
    c.require(isinstance(rows,list) and len(rows)==2
        and [r['command_kind'] for r in rows]==['server_version','fixed_image_identity'],'PREFLIGHT_TWO_EXACT_READS')
    server,image=rows
    if server['exact_identity_accepted'] and image['exact_identity_accepted']:return 'READY_FIXED_LOCAL_IMAGE_ONLY_NOT_SQL_OR_GATE'
    if server['backend_connection_error'] and image['backend_connection_error']:return 'LOCAL_BACKEND_ENDPOINT_UNAVAILABLE'
    if server['exact_identity_accepted'] and image['pinned_image_not_found_error']:return 'FIXED_LOCAL_IMAGE_ABSENT'
    return 'FURTHER_BACKEND_DIAGNOSIS_REQUIRED'


def check(resources,reader):
    started=time.monotonic()
    out=dict(exact_local_endpoint=LOCAL_DOCKER_HOST,pinned_image=IMAGE,commands=[],owned_host_job_profiles=[],
        backend_started_or_stopped=False,image_pulled_or_removed=False,container_created=False,
        SQL_or_native_executed=False,Docker_daemon_or_WSL_contained_in_host_Job=False,
        backend_container_cleanup_qualified=False,raw_logs_included=False)
    reader.pin(SELF)
    docker=shutil.which('docker');c.require(docker is not None and c.c.Path(docker)==DOCKER,'PREFLIGHT_DOCKER_LOCATION')
    for ancestor in (DOCKER,*DOCKER.parents):
        c.require(not ancestor.is_symlink() and not ancestor.is_junction(),'PREFLIGHT_DOCKER_LINK')
    old=reader.json('implementation/p09/evidence/p09-146-corpus-consumer-run07.v1.json')
    allowed=[docker,str(c.c.ROOT/old['executable_pin']['path']),str(c.c.ROOT/c.build.executable_name(1))]
    for pin in (old['executable_pin'],):c.require(reader.pin(pin['path'])==pin,'PREFLIGHT_ORIGINAL_METADATA_EXE')
    runtime=reader.json(c.BUILD_PIN['path'])['executable_pin']
    c.require(runtime['path']==c.build.executable_name(1) and reader.pin(runtime['path'])==runtime,'PREFLIGHT_CURRENT_EXE_PIN')
    for kind,args in commands(docker):
        factory=LocalDockerJobFactory(windows=resources.windows,allowed_executables=allowed,
            checkpoint=resources.checkpoint_io,record=lambda p:out['owned_host_job_profiles'].extend(p))
        try:
            result=bounded_observation_run(args,cwd=c.c.ROOT,timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,process_factory=factory)
            out['commands'].append(classify(result,kind))
        finally:factory.close()
    c.require(out['owned_host_job_profiles'] and all(p['cleanup_confirmed'] and p['owned_tree_empty']
        and p['job_handle_closed'] and p['last_job_accounting']['active_processes']==0
        for p in out['owned_host_job_profiles']),'PREFLIGHT_OWNED_HOST_CLEANUP')
    out.update(diagnosis=diagnosis(out['commands']),ready=all(r['exact_identity_accepted'] for r in out['commands']),
        wall_seconds=round(time.monotonic()-started,4))
    return out
