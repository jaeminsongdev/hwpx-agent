"""537: actual owned SQL24 HTTPS storage + public recovery, not policy issuer/worker admission/Native/Gate."""
import ast,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_target_recovery as worker
SELF='tools/p09/verify_https_target_sql.py'
OUTPUT='implementation/p09/evidence/p09-361-https-target-sql537.v1.json'
BASE='implementation/p09/evidence/p09-361-https-target-job536.v1.json'
PRODUCT='crates/product-cli/src/form_product_request/stored_operations/https_targets.rs'
COMMON='crates/product-cli/examples/sql23_storage.rs'
PROBE='crates/product-cli/examples/sql24_https_target_recovery.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
WORKER='tools/p09/native_postgres_https_target_recovery.py'
CAMPAIGN='tools/p09/native_postgres_storage.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
ARCHIVE='implementation/p09/source-archive/p361-https-sql537/'

def inverse(q):
    old=q.text(ARCHIVE+'product.rs');new=q.text(PRODUCT)
    start=new.index('    /// Read-only existing-effect recovery, not a new policy approval, claim or replay permit.\n')
    end=new.index('\n}',start)
    r.audit.inverse(new[:start]+new[end+1:],q.snapshots[ARCHIVE+'product.rs'],'HTTPS537_ALL_OLD_REQUEST_SCOPE_POLICY_LOOKUP_GUARDS_BYTE_IDENTICAL')
    text=q.text(COMMON)
    for addition in('#[path="sql23_storage/https_target_recovery.rs"]mod https_target_recovery;\n',
        'const HTTPS_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-target-537";\nstatic HTTPS_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n',
        'pub fn https_target_recovery_main(){HTTPS_MODE.store(true,std::sync::atomic::Ordering::Relaxed);LOOKUP_MODE.store(true,std::sync::atomic::Ordering::Relaxed);\n    let mode=env::args().nth(1).unwrap_or_default();finish(https_target_recovery::run(&mode),&mode)}\n'):
        r.c.require(text.count(addition)==1,'HTTPS537_ONE_CLOSED_NEW_FIXTURE_MODE');text=text.replace(addition,'')
    text=text.replace('if HTTPS_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_ROOT}else if SEARCH_MODE','if SEARCH_MODE')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'common.rs'],'HTTPS537_OLD_SQL_ROOTS_CRYPTO_REPOSITORIES_AND_BODY_UNCHANGED')
    text=q.text(CAMPAIGN).replace(",expected_artifacts=6",'').replace("    cluster.require(type(expected_artifacts)is int and expected_artifacts in(6,7),'PG_STORAGE_CLOSED_ARTIFACT_COUNT')\n",'')
    text=text.replace('artifacts=expected_artifacts,available=expected_artifacts','artifacts=6,available=6').replace("len(rows)==expected_artifacts,'PG_STORAGE_EXACT_REAL_ENCRYPTED_ARTIFACT_COUNT'","len(rows)==6,'PG_STORAGE_SIX_REAL_ENCRYPTED_ARTIFACTS'")
    r.audit.inverse(text,q.snapshots[ARCHIVE+'campaign.py'],'HTTPS537_DEFAULT_SIX_ARTIFACT_CAMPAIGN_RESTORED_NO_SAFETY_CHANGE')

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/worker.OBSERVATION).exists()and not worker.OWNED.exists(),'HTTPS537_FRESH_OWNED_RUN_ONLY_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;observation=None
    row=dict(state='FAILED_HTTPS_TARGET_SQL24',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,official249_SQL520_external003_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_policy_issuer_registry_release_or_keys_changed=False,production_route_worker_policy_issuer_or_key_custody_qualified=False,
        unchanged_536_eight_cases_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='89aae5ca981e89d13db9b322661a1660d861475f1273179042ed3d60593e444d'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==838 and base['current_qualified_cases']==8,'HTTPS537_EXACT536_CLOSURE')
        names=inventory.inventory(guard)|{SELF,BASE,PRODUCT,COMMON,PROBE,LEAF,WORKER,CAMPAIGN,MANIFEST,deps.CAPTURE,
            ARCHIVE+'common.rs',ARCHIVE+'product.rs',ARCHIVE+'campaign.py','tools/p09/search_sql_receipt.py','tools/p09/paced_postgres_hash.py',
            'tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py','tools/p09/native_postgres_ascii_campaign.py',
            'tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}
        names|=includes.test_inputs((PROBE,),guard)
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'HTTPS537_BOUNDED_COMPILE_INPUTS')
        for name in sorted(names):q.pin(name)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/')or'/src/'not in pin['path']:continue
            actual=q.snapshots[ARCHIVE+'product.rs']if pin['path']==PRODUCT else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS537_ALL_ORIGINAL_PRODUCT_LIBRARY_AND_COORDINATOR_GUARDS_PRESERVED')
        inverse(q)
        c.require(q.snapshots[MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','HTTPS537_EXACT_RUNTIME_MANIFEST')
        for path in(SELF,WORKER,CAMPAIGN):ast.parse(q.text(path))
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-sql-scratch537';c.require(not scratch.exists(),'HTTPS537_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(c.ROOT/'tools/p09'))
        artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql24_https_target_recovery'
        print(json.dumps(dict(state='HTTPS_SQL_PREFLIGHT',inputs=len(q.snapshots),SQL_cases=1,previous_tests_replayed=False,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_fresh_HTTPS_SQL24_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'HTTPS537_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d';artifact.pin(dep_path);declared=deps.dependencies(c.ROOT/dep_path)
        c.require(declared<=set(q.snapshots),'HTTPS537_ALL_ACTUAL_PROBE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_HTTPS_SQL24_job_and_readonly_recovery',[sys.executable,str(c.ROOT/WORKER),'--owned-schema24-https-target-537'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'HTTPS537_EXACT_OWNED_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_HTTPS_REAL_SQL24_ONE_GUARDED_JOB_AND_PUBLIC_REGISTERED_EFFECT_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['https_SQL_cases']==1,'HTTPS537_ACTUAL_JOB_RESTART_RECOVERY_NO_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['read_passes']>=3166 and io['full_fresh_hash_preserved']is True
            and io['raw_or_parsed_content_cached']is False and io['max_file_opens_per_second']==20,'HTTPS537_TWO_FULL_PACED_RUNTIME_READS_NO_CACHE')
        c.require(not any(scratch.iterdir()),'HTTPS537_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_TARGET_REAL_SQL24_ONE_GUARDED_JOB_PUBLIC_REGISTERED_RECOVERY_BEFORE_AFTER_RESTART_NOT_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL24_started=True,actual_claim_lease_registered_CAS_completion=True,actual_public_request_registered_effect_recovery=True,
            actual_SQL_counts=observation['snapshots'][0],compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS537_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        if observation is not None:row.update(database_stage=observation.get('stage'),database_error=observation.get('error_code'),
            last_probe=None if not observation['probes']else observation['probes'][-1],fresh_runtime_hash_io=observation.get('fresh_runtime_hash_io'),
            all_owned_postmasters_normal_stop=observation.get('all_owned_postmasters_normal_stop',False))
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','database_stage','database_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
