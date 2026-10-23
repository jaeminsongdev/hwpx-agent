"""One fresh common late-revocation SQL case, only AFTER external005 is terminal.

Missing/incomplete005 result defers before the shared lock, compilation or DB.
Current process exclusion remains mandatory even when a final file exists.
"""
import ast,hashlib,json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_common_late584 as worker
import common_late585_publication as publication
import crossref_inline_receipt567 as layout
SELF='tools/p09/verify_common_late585.py'
HOST='tools/p09/inspect_common_sql_exclusion585.ps1'
WORKER='tools/p09/native_postgres_common_late584.py'
CASE='crates/product-cli/examples/sql23_storage/https_common_late584.rs'
EXAMPLE='crates/product-cli/examples/sql26_https_common_late584.rs'
MODELS='implementation/p09/evidence/p09-361-common-late584-models.v1.json'
EXTERNAL='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run005.v1.json'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
SHELL=Path(r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe')


def terminal_value(value):
    return type(value)is dict and type(value.get('generation'))is int and value['generation']==5 \
        and type(value.get('state'))is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value['state'])is not None \
        and type(value.get('cleanup'))is bool and type(value.get('native_claim_created'))is bool \
        and type(value.get('fixed_eight_executed'))is bool and value.get('native_startup_qualified')is False \
        and type(value.get('accepted_count_delta'))is int and value['accepted_count_delta']==0 \
        and value.get('P09_gate')=='OPEN'and value.get('P10_started')is False


def external_terminal(root):
    path=root/EXTERNAL
    if not path.is_file()or path.is_symlink()or path.is_junction():return None
    try:
        if not 0<path.stat().st_size<=262144:return None
        raw=path.read_bytes();value=layout.unpack(json.loads(raw))
        if terminal_value(value):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),original_cleanup=value['cleanup'])
    except(ValueError,OSError,KeyError,TypeError,RecursionError):pass
    return None


def exclusion(guard,env,row):
    shared=r.shared;owned=capture=None;start=time.monotonic();step=dict(stage='readonly_current_crossref_exclusion',cleanup=False);row['steps'].append(step)
    try:
        owned=shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/HOST),'-ReadOnlyOwnedCrossrefExclusion'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=shared.BoundedProcessCapture(owned,output_limit=8192,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-start<15,'SQL585_READONLY_QUERY_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        value=json.loads(out);step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),result=value)
        r.c.require(owned.returncode==0 and not err.strip()and type(value)is dict and value.get('state')=='OBSERVED_READONLY_CROSSREF_SQL_EXCLUSION'
            and type(value.get('native_processes'))is int and value['native_processes']>=0
            and type(value.get('crossref_hosts'))is int and value['crossref_hosts']>=0
            and value.get('process_created_or_stopped')is False and value.get('COM_activated')is False,'SQL585_EXACT_READONLY_EXCLUSION_RESPONSE')
        return value['native_processes']==value['crossref_hosts']==0
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-start,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--after-external005-terminal-only'],'SQL585_CLOSED_POST005_MODE')
    terminal=external_terminal(c.ROOT)
    if terminal is None:
        print(json.dumps(dict(state='DEFERRED_EXTERNAL005_NOT_TERMINAL_NO_LOCK_BUILD_OR_DATABASE',shared_lock_acquired=False,
            actual_Cargo_SQL_or_Native_started=False,SQL_case_consumed=False,P09_complete=False)),flush=True);return 3
    c.require(not(c.ROOT/publication.OUTPUT).exists()and not(c.ROOT/publication.SPOOL).exists(),'SQL585_IMMUTABLE_ONE_FRESH_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=observation=None;started=time.monotonic();deferred=False;published=None
    row=dict(state='FAILED_COMMON_LATE_SQL585',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Hancom_COM_Native_or_249_started=False,external005_replayed=False,old545_571_product_or_databases_replayed=False,
        operational_database_registry_worker_custody_or_admission_qualified=False,actual_owned_SQL26_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in(SELF,HOST,WORKER,'tools/p09/common_late585_publication.py',EXTERNAL):q.pin(name)
        c.require(q.snapshots[EXTERNAL]['bytes']==terminal['bytes']and q.snapshots[EXTERNAL]['sha256']==terminal['sha256'],
            'SQL585_SAME_COMPLETED_EXTERNAL005_PACKET')
        env=r.audit.environment()
        if not exclusion(guard,env,row):
            deferred=True;row['state']='DEFERRED_LIVE_CROSSREF_OR_HANCOM_NO_BUILD_OR_DATABASE';return 3
        names=inventory.inventory(guard)|includes.test_inputs((EXAMPLE,),guard)|{SELF,HOST,WORKER,CASE,EXAMPLE,MODELS,MANIFEST,EXTERNAL,deps.CAPTURE,
            'tools/p09/common_late585_publication.py','tools/p09/crossref_generation005_publication.py',
            'tools/p09/native_postgres_storage.py','tools/p09/paced_postgres_hash.py','tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py',
            'tools/p09/native_postgres_ascii_campaign.py','tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql',
            'tools/p09/fixtures/sql23_service_roles.sql'}
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        c.require(len(names)<=2048,'SQL585_CURRENT_DEPENDENCY_COUNT_BOUND')
        for name in sorted(names):q.pin(name)
        models=layout.unpack(q.json(MODELS))
        c.require(q.snapshots[MODELS]['sha256']=='f9c00292e645b9abf1bf7a129d05c2c0ee11c68dfaa30f723c301b03b0950603'
            and models['models']==dict(run=8,errors=0,failures=0,skipped=0)and models['cleanup']is True
            and models['fresh_inputs']==models['final_fresh_hashes']==11 and models['SQL_case_state']=='NOT_RUN','SQL585_EXACT_PURE_PREPARATION_NOT_SQL_AUTHORITY')
        for pin in models['source_pins']:
            c.require(q.pin(pin['path'])==pin,'SQL585_ALL_PREPARED_CASE_AND_WORKER_INPUTS_UNCHANGED')
        for name in(SELF,WORKER):ast.parse(q.text(name))
        c.require(not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'SQL585_FRESH_OWNED_DATABASE_AND_OBSERVATION_ONLY')
        scratch=c.ROOT/'target/p09-common-late585-scratch'
        c.require(not scratch.exists()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'SQL585_FRESH_COMPILER_TEMP');scratch.mkdir()
        env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql26_https_common_late584'
        row['external005_terminal_prerequisite']=dict(receipt=q.snapshots[EXTERNAL],original_native_cleanup=terminal['original_cleanup'],
            current_Hancom_and_crossref_hosts_absent=True,not_a_Native_or_P09_qualification=True)
        print(json.dumps(dict(state='COMMON_LATE585_CURRENT_PREFLIGHT',inputs=len(q.snapshots),fresh_SQL_cases=1,
            original545_571_replayed=False,Native_started=False,CPU_hard_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_common_late584_once',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'SQL585_NO_COMPILER_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep='target/debug/examples/'+name+'.d';artifact.pin(dep)
        declared=deps.dependencies(c.ROOT/dep);c.require(declared<=set(q.snapshots),'SQL585_ALL_ACTUAL_COMPILE_INPUTS_PREPINNED')
        row['actual_probe_dependencies']=sorted(declared);env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_common_late584_SQL_CAS_denial_and_restart',[sys.executable,str(c.ROOT/WORKER),'--owned-schema26-common-late-584'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'SQL585_EXACT_CURRENT_WORKER_OBSERVATION')
        c.require(observation['state']=='PASS_COMMON_SQL26_LATE_REVOCATION_DENIED_AND_RESTART_OBSERVATION_NOT_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['actual_common_dispatch_atomic_policy_CAS_denial']is True
            and observation['common_existing_after_restart_without_reexecution']is True and observation['duplicate_equivalent_recovery_executed']is False,
            'SQL585_ACTUAL_COMMON_LATE_CAS_DENIAL_RESTART_AND_CLEANUP')
        projection=dict(artifacts=7,available=7,jobs=2,succeeded_jobs=1,successful_records=1,attempts=2,authorizations=1,intents=1,revisions=1,seals=1,head=1)
        c.require(observation['snapshots']==[projection,projection]and observation['policy_snapshots']==[dict(versions=1,revocations=1,latest=1)]*2,
            'SQL585_ORIGINAL_DENIED_AUTHORIZATION_RETAINED_HEAD_UNCHANGED_BEFORE_AFTER')
        io=observation['fresh_runtime_hash_io'];c.require(io['full_fresh_hash_preserved']is True and io['raw_or_parsed_content_cached']is False
            and io['max_file_opens_per_second']==20,'SQL585_ORIGINAL_FULL_FRESH_RUNTIME_HASH_PACING_NO_CACHE')
        c.require(not any(scratch.iterdir()),'SQL585_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_LATE_SQL585_CURRENT_CAS_DENIAL_RESTART_NOT_NATIVE_OR_GATE',actual_owned_SQL26_started=True,
            actual_common_request_atomic_policy_CAS_denial=True,actual_same_attempt_restart_observation=True,
            SQL_counts=projection,SQL_policy_counts=observation['policy_snapshots'][0],compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'SQL585_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        if observation is not None:row.update(database_stage=observation.get('stage'),database_error=observation.get('error_code'),
            last_probe=None if not observation['probes']else observation['probes'][-1],fresh_runtime_hash_io=observation.get('fresh_runtime_hash_io'),
            all_owned_postmasters_normal_stop=observation.get('all_owned_postmasters_normal_stop',False),
            actual_owned_SQL26_started=observation.get('actual_owned_postmaster_started',False))
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        if deferred:print(json.dumps(dict(state=row['state'],shared_lock_released=guard.cleanup,actual_Cargo_SQL_or_Native_started=False,SQL_case_consumed=False)),flush=True)
        else:
            try:published=publication.publish_final(c.ROOT,row)
            except(ValueError,OSError,KeyError,TypeError):
                retained=False
                try:retained=publication.retained_row(c.ROOT)==row
                except(ValueError,OSError,KeyError,TypeError):pass
                print(json.dumps(dict(state='FAILED_SQL585_FORMAL_PUBLICATION',exact_private_row_retained=retained,P09_complete=False)),flush=True)
            if published is not None:print(json.dumps({**{k:row.get(k)for k in('state','error_code','database_stage','database_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':published}),flush=True)
    return 0 if published is not None and row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
