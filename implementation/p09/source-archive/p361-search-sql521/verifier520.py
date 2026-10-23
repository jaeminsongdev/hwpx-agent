"""520: one fresh owned PostgreSQL24 common-search vertical path, actual AEAD/registered recovery."""
import ast,importlib.util,json,os,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as inputs
import character_detail_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_search_request_recovery as worker
from paced_postgres_hash import PacedPostgresHasher
SELF='tools/p09/verify_search_request_sql.py'
OUTPUT='implementation/p09/evidence/p09-361-search-sql520.v1.json'
SCRATCH='target/p09-search-sql-scratch520'
BASE='implementation/p09/evidence/p09-361-search-lookup515.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-search-sql516/'
COMMON='crates/product-cli/examples/sql23_storage.rs'
PROBE='crates/product-cli/examples/sql24_search_request_recovery.rs'
LEAF='crates/product-cli/examples/sql23_storage/search_request_recovery.rs'
WORKER='tools/p09/native_postgres_search_request_recovery.py'
PACER='tools/p09/paced_postgres_hash.py'
TEST='tools/p09/tests/test_paced_postgres_hash.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'

def dependency_path(value):
    root=r.c.ROOT.resolve();path=Path(value);path=path if path.is_absolute()else root/path
    try:name=path.resolve().relative_to(root).as_posix()
    except ValueError:raise ValueError('SEARCHSQL518_DEPENDENCY_OUTSIDE_REPO')from None
    r.c.require(name.startswith(('crates/','migrations/postgres/','tools/p09/fixtures/')),'SEARCHSQL518_CLOSED_DEPENDENCY_ROOT')
    return name

def probe_dependencies(path):
    raw=path.read_bytes();r.c.require(0<len(raw)<=131072,'SEARCHSQL518_BOUNDED_DEP_INFO')
    line=raw.decode('utf-8').splitlines()[0];r.c.require(': 'in line,'SEARCHSQL518_DEP_INFO_TARGET')
    names={dependency_path(value)for value in line.split(': ',1)[1].split()}
    r.c.require(bool(names),'SEARCHSQL518_NONEMPTY_ACTUAL_DEPENDENCIES');return names

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/SCRATCH).exists()and not worker.OWNED.exists()
        and not(c.ROOT/worker.OBSERVATION).exists(),'SEARCHSQL516_FRESH_OWNED_RUN_ONLY_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;observation=None
    row=dict(state='FAILED_COMMON_SEARCH_SQL24',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,official249_replayed=False,external003_replayed_or_cleanup_changed=False,
        operational_database_accessed=False,production_registry_scanner_key_custody_or_native_product_route_qualified=False,
        previous30_lookup_and31_storage_tests_replayed=False,real_SQL_common_search_case_scope=1)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='07d8b90bd946b5c90aaaa58cbf9ad23ac6e886af79d708acb4cbe85a127a2ed6'
            and old['cleanup']is True and old['fresh_inputs']==old['final_fresh_hashes']==1017 and old['qualified_test_cases']==30,'SEARCHSQL516_EXACT515_RESULT_PRESERVED')
        names=inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,BASE,COMMON,PROBE,LEAF,WORKER,PACER,TEST,MANIFEST,ARCHIVE+'sql-main.rs',
            'tools/p09/native_postgres_storage.py','tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py',
            'tools/p09/native_postgres_ascii_campaign.py','tools/p09/fixtures/native_postgres_hba.conf',
            'tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}
        names|=inputs.test_inputs((PROBE,),guard)
        failed='implementation/p09/evidence/p09-361-search-sql516.v1.json'
        names.add(failed)
        names|={'implementation/p09/source-archive/p361-search-sql517/'+name for name in
            ('failed-model516.py','verifier516.py','worker516.py','case516.rs','common516.rs')}
        previous='implementation/p09/evidence/p09-361-search-sql517.v1.json'
        names|={previous,'implementation/p09/source-archive/p361-search-sql518/verifier517.py'}
        precision_failure='implementation/p09/evidence/p09-361-search-sql518.v1.json'
        names|={precision_failure,'target/p09-common-search-sql24-observation-517.json'}
        names|={'implementation/p09/source-archive/p361-search-sql519/'+name for name in
            ('verify_search_request_sql.py','paced_postgres_hash.py','test_paced_postgres_hash.py','native_postgres_search_request_recovery.py')}
        coarse_failure='implementation/p09/evidence/p09-361-search-sql519.v1.json'
        names|={coarse_failure,'target/p09-common-search-sql24-observation-519.json'}
        names|={'implementation/p09/source-archive/p361-search-sql520/'+name for name in
            ('verify_search_request_sql.py','paced_postgres_hash.py','test_paced_postgres_hash.py','native_postgres_search_request_recovery.py')}
        for path in sorted(names):q.pin(path)
        c.require(q.snapshots[failed]['sha256']=='f29833d15f1d1112f432f4e400549b3e9c791a2346af8264c833fabeaf86e2e0','SEARCHSQL517_ORIGINAL_FAILED_PREFLIGHT_PRESERVED')
        c.require(q.snapshots[previous]['sha256']=='659d7c29ee917ca83e66f2dac2d4d3f5cd361295e77653cb1870d5979f6d6c5e','SEARCHSQL518_ORIGINAL_DEP_INFO_FAILURE_PRESERVED')
        c.require(q.snapshots[precision_failure]['sha256']=='857720712cf15d68fc7b8ac309084bd647918af3083a527287260c30e837c108','SEARCHSQL519_ORIGINAL_CLOCK_FAILURE_PRESERVED')
        c.require(q.snapshots[coarse_failure]['sha256']=='63f13213f9e797fb8bc95b3bb5ec56d80346a62c478c07ffab71de51715ab0e2','SEARCHSQL520_ORIGINAL_COARSE_CLOCK_FAILURE_PRESERVED')
        c.require(dependency_path(PROBE)==PROBE and dependency_path(str(c.ROOT/PROBE))==PROBE,'SEARCHSQL518_RELATIVE_ABSOLUTE_IDENTICAL')
        try:dependency_path(str(c.ROOT.parent/'outside.sql'))
        except ValueError:pass
        else:raise ValueError('SEARCHSQL518_OUTSIDE_PATH_MUST_DENY')
        row['dependency_path_models']=3
        for pin in old['source_pins']:
            if pin['path']==COMMON:
                saved=q.snapshots[ARCHIVE+'sql-main.rs'];c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'SEARCHSQL516_ORIGINAL_COMMON_PROBE_ARCHIVED')
            else:c.require(q.snapshots[pin['path']]==pin,'SEARCHSQL516_ALL_PRODUCT_LIBRARY_GUARDS_AND_PREVIOUS_BODIES_UNCHANGED')
        text=q.text(COMMON)
        additions=['#[path="sql23_storage/search_request_recovery.rs"]mod search_request_recovery;\n',
            'const SEARCH_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-search-recovery-519";\nstatic SEARCH_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n',
            'pub fn search_request_recovery_main(){SEARCH_MODE.store(true,std::sync::atomic::Ordering::Relaxed);LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);\n    let mode=env::args().nth(1).unwrap_or_default();finish(search_request_recovery::run(&mode),&mode)}\n']
        for addition in additions:c.require(text.count(addition)==1,'SEARCHSQL516_ONE_CLOSED_NEW_FIXTURE_MODE');text=text.replace(addition,'')
        text=text.replace('if SEARCH_MODE.load(std::sync::atomic::Ordering::Relaxed){SEARCH_ROOT}else if CUSTODY_MODE','if CUSTODY_MODE')
        r.audit.inverse(text,q.snapshots[ARCHIVE+'sql-main.rs'],'SEARCHSQL516_OLD_SQL_ROOTS_CREDENTIALS_REPOSITORIES_AND_ALL_OLD_BODIES_RESTORED')
        c.require(q.snapshots[MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','SEARCHSQL516_ORIGINAL_RUNTIME_MANIFEST_PIN')
        for path in(SELF,WORKER,PACER,TEST):ast.parse(q.text(path))
        spec=importlib.util.spec_from_file_location('search_sql_hash_models',str(c.ROOT/TEST));models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(models.Models).run(result)
        row['hash_pacing_models']=dict(tests=result.testsRun,errors=len(result.errors),failures=len(result.failures))
        c.require(result.testsRun==7 and not result.errors and not result.failures,'SEARCHSQL520_SEVEN_FRESH_HASH_PACING_AND_CLOCK_MODELS')
        hasher=PacedPostgresHasher()
        for _ in range(32):
            guard.check();c.require(hasher.sha_file(c.ROOT/PACER)==q.snapshots[PACER]['sha256'],'SEARCHSQL520_REAL_CLOCK_FULL_FRESH_READ_MATCH')
        row['real_clock_preflight']=dict(profile=hasher.profile(),monotonic_clock=vars(time.get_clock_info('monotonic')),
            selected_clock=vars(time.get_clock_info('perf_counter')))
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.301693333880961,'SEARCHSQL516_RAM95_COMPILE_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists(),'SEARCHSQL516_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(c.ROOT/'tools/p09'))
        artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='SEARCH_SQL_PREFLIGHT',inputs=len(q.snapshots),models=7,SQL_cases=1,CPU_cap_percent=6.25)),flush=True)
        name='sql24_search_request_recovery'
        r.harness.run_one('compile_fresh_common_search_SQL24_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--example',name,'--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'SEARCHSQL516_PROBE_COMPILES_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d'
        artifact.pin(dep_path);declared=probe_dependencies(c.ROOT/dep_path)
        c.require(declared<=set(q.snapshots),'SEARCHSQL516_ALL_ACTUAL_EXAMPLE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:
            reply=postgres_runner.run_owned('one_fresh_SQL24_search_job_and_public_recovery',[sys.executable,str(c.ROOT/WORKER),'--owned-schema24-common-search'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'SEARCHSQL516_EXACT_OWNED_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_COMMON_SEARCH_SQL24_REAL_JOB_CAS_AND_PUBLIC_EFFECT_RECOVERY_BEFORE_AFTER_RESTART_NOT_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['common_search_SQL_cases']==1,'SEARCHSQL516_REAL_JOB_EFFECT_RESTART_NO_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['read_passes']>=3166 and io['full_fresh_hash_preserved']is True
            and io['raw_or_parsed_content_cached']is False and io['max_file_opens_per_second']==20,'SEARCHSQL516_TWO_FULL_RUNTIME_READS_NOT_CACHE')
        c.require(not any(scratch.iterdir()),'SEARCHSQL516_COMPILER_TEMP_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_SEARCH_REAL_SQL24_ONE_CASE_PUBLIC_RECOVERY_BEFORE_AFTER_RESTART_NOT_NATIVE_OR_GATE',
            actual_owned_SQL24_started=True,actual_job_claim_lease_registered_CAS_completion=True,actual_public_request_registered_effect_recovery=True,
            actual_SQL_counts=observation['snapshots'][0],compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SEARCHSQL516_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        if observation is not None:row.update(database_stage=observation.get('stage'),database_error=observation.get('error_code'),
            last_probe=None if not observation['probes']else observation['probes'][-1],fresh_runtime_hash_io=observation.get('fresh_runtime_hash_io'),
            all_owned_postmasters_normal_stop=observation.get('all_owned_postmasters_normal_stop',False))
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','database_stage','database_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
