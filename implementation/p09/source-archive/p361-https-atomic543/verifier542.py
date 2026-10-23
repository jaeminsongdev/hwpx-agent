"""542: original SQL CAS with atomic HTTPS policy locks, one fresh actual26 integration; no Native/admission/Gate."""
import ast,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_atomic_recovery as worker
SELF='tools/p09/verify_https_atomic_sql.py'
OUTPUT='implementation/p09/evidence/p09-361-https-atomic-sql542.v1.json'
BASE='implementation/p09/evidence/p09-361-https-policy-sql541.v1.json'
PRODUCT='crates/revision-service/src/postgres.rs'
COMMON='crates/product-cli/examples/sql23_storage.rs'
PROBE='crates/product-cli/examples/sql26_https_atomic_recovery.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
WORKER='tools/p09/native_postgres_https_atomic_recovery.py'
CAMPAIGN='tools/p09/native_postgres_storage.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
ARCHIVE='implementation/p09/source-archive/p361-https-atomic542/'

POLICY_FIXTURE='crates/product-cli/examples/sql23_storage/https_policy_fixture.rs'
CHANGED={PRODUCT:'revision.rs',
 'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs.rs':'jobs.rs',
 'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/admission.rs':'admission.rs',
 'crates/artifact-service/src/store/postgres_repository.rs':'artifact-parent.rs',
 'crates/artifact-service/src/store/postgres_repository/schema25.rs':'artifact25.rs',
 'crates/product-cli/src/form_stored_provider/actual_import/https_target_output/compiled.rs':'compiled.rs',
 'crates/product-cli/src/form_product_request/stored_operations/https_targets/routing.rs':'routing.rs',
 COMMON:'common.rs',LEAF:'case.rs',POLICY_FIXTURE:'policy-fixture.rs',CAMPAIGN:'campaign.py','tools/p09/native_postgres_cluster.py':'cluster.py'}

def inverse(q):
    # Prove the original CAS body was moved, not replaced, and executes after exactly one precondition in the SAME transaction.
    original=q.text(ARCHIVE+'revision.rs');text=q.text(PRODUCT)
    a=original.index('    fn compare_and_swap(\n',original.index('impl RevisionRepository for LocalPostgresRevisionRepository'))
    b=original.index('    fn head(\n',a);old_function=original[a:b];old_body=old_function[old_function.index('        self.authorize_context(context)?;'):]
    h=text.index('    pub(crate) fn compare_and_swap_precondition(');end=text.index('    fn scoped<T>(',h);helper=text[h:end]
    new_body=helper[helper.index('        self.authorize_context(context)?;'):]
    r.c.require(new_body.count('            precondition(tx)?;\n')==1 and new_body.replace('            precondition(tx)?;\n','')==old_body,
        'HTTPS542_ORIGINAL_CAS_LEASE_HASH_PARAMETERS_SQL_READCOMMITTED_AND_OUTCOME_BODY_EXACT')
    text=text[:h]+text[end:];a=text.index('    fn compare_and_swap(\n',text.index('impl RevisionRepository for LocalPostgresRevisionRepository'));b=text.index('    fn head(\n',a)
    r.c.require(text[a:b]==old_function[:old_function.index('        self.authorize_context(context)?;')]+'        self.compare_and_swap_precondition(context,request,|_|Ok(()))\n    }\n','HTTPS542_OLD_DEFAULT_CAS_IS_ONLY_NOOP_PRECONDITION')
    r.audit.inverse(text[:a]+old_function+text[b:],q.snapshots[ARCHIVE+'revision.rs'],'HTTPS542_ENTIRE_ORIGINAL_REVISION_SERVICE_BODY_RESTORED')
    text=q.text('crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs.rs').replace('pub mod atomic_https;\n','')
    text=text.replace(',atomic_https_qualified:bool,commit_policy:Option<atomic_https::HttpsCommitPolicyBinding>','')
    a=text.index('    /// # Errors\n    /// Exact26,');b=text.index('    fn connect_mode',a);text=text[:a]+text[b:]
    text=text.replace('lease,false,false,false)','lease,false,false)').replace('lease,true,false,false)','lease,true,false)').replace('lease,true,true,false)','lease,true,true)')
    text=text.replace('https:bool,atomic:bool)','https:bool)')
    text=text.replace('if atomic{admission::admit_with_atomic_https(&mut client)?;}else if https','if https')
    text=text.replace(',atomic_https_qualified:atomic,commit_policy:None','').replace(',atomic_https_qualified:self.atomic_https_qualified,commit_policy:self.commit_policy.clone()','')
    text=text.replace('''        if let Some(policy)=&self.commit_policy{
            policy.matches(context,request)?;
            repository.compare_and_swap_precondition(context,request,|tx|policy.require_in_transaction(tx,context))
        }else{repository.compare_and_swap(context,request)}''','        repository.compare_and_swap(context,request)')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'jobs.rs'],'HTTPS542_ALL_OLD_CONNECTORS_LEASE_REGISTRATION_AND_LIFECYCLE_GUARDS_UNCHANGED')
    path='crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/admission.rs'
    text=q.text(path).replace('pub(super) fn admit_with_atomic_https(client:&mut Client)->Result<(),RevisionError>{admit_mode(client,true,true,true)}\n','')
    text=text.replace('admit_mode(client,false,false,false)','admit_mode(client,false,false)').replace('admit_mode(client,true,false,false)','admit_mode(client,true,false)').replace('admit_mode(client,true,true,false)','admit_mode(client,true,true)')
    text=text.replace('https:bool,atomic:bool)','https:bool)')
    text=text.replace('if atomic{"SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 27"}\n        else if https','if https')
    text=text.replace('if atomic{atomic_https::schema26(&rows)?;https_policy::schema25(&rows[..25])?;request_lookup::schema24(&rows[..24])?;schema(&rows[..23])?;}\n    else if https','if https')
    text=text.replace('if atomic{atomic_https::admit(client)?;}','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'admission.rs'],'HTTPS542_ALL_ORIGINAL_EXACT23_24_25_PRIVILEGE_FUNCTION_TABLE_AND_LOOKUP_CHECKS')
    r.audit.inverse(q.text('crates/artifact-service/src/store/postgres_repository.rs').replace('pub mod schema26;\n',''),q.snapshots[ARCHIVE+'artifact-parent.rs'],'HTTPS542_OLD_ARTIFACT_SERVICE_BODY_UNCHANGED')
    r.audit.inverse(q.text('crates/artifact-service/src/store/postgres_repository/schema25.rs').replace('pub(super) fn validate','fn validate'),q.snapshots[ARCHIVE+'artifact25.rs'],'HTTPS542_ENTIRE_OLD_METADATA25_GUARDS_UNCHANGED')
    path='crates/product-cli/src/form_stored_provider/actual_import/https_target_output/compiled.rs'
    r.audit.inverse(q.text(path).replace('    pub(crate) fn policy_version(&self)->&HttpsTargetPolicyVersion{&self.candidate.version}\n',''),q.snapshots[ARCHIVE+'compiled.rs'],'HTTPS542_ORIGINAL_POLICY_LOWERER_AND_COMPILER_UNCHANGED')
    path='crates/product-cli/src/form_product_request/stored_operations/https_targets/routing.rs'
    r.audit.inverse(q.text(path).replace('pub mod atomic_sql;\n','').replace('    #[error("HTTPS_TARGET_MANIFEST_ATOMIC_POLICY_BINDING_DENIED")]AtomicPolicy,\n',''),q.snapshots[ARCHIVE+'routing.rs'],'HTTPS542_ORIGINAL_MANIFEST_STORAGE_AND_CURRENT_GUARDS_UNCHANGED')
    text=q.text(COMMON).replace('const HTTPS_ATOMIC_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-atomic-542";\nstatic HTTPS_ATOMIC_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n','')
    text=text.replace('if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_ATOMIC_ROOT}else if HTTPS_POLICY_MODE','if HTTPS_POLICY_MODE')
    text=text.replace('if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresStoredRevisionJobsRepository::connect_with_atomic_https_policy(&config,context()?,None)?}\n        else if HTTPS_POLICY_MODE','if HTTPS_POLICY_MODE')
    text=text.replace('if HTTPS_ATOMIC_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresMetadataRepository::connect_schema26(&config,tenant()?)?}\n        else if HTTPS_POLICY_MODE','if HTTPS_POLICY_MODE')
    text=text.replace('pub fn https_atomic_recovery_main(){HTTPS_ATOMIC_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_policy_recovery_main()}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'common.rs'],'HTTPS542_OLD_SQL_ROOTS_KEYS_CRYPTO_FIXTURES_AND_CLOSED_ERRORS_PRESERVED')
    text=q.text(LEAF).replace('''fn execute()->Result<Value>{
    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){return policy_fixture::atomic_execute();}
    let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);''',
        'fn execute()->Result<Value>{let a=artifacts()?;let ctx=actor()?;let rc=context()?;let revisions=RevisionService::new(repository()?);')
    text=text.replace('''    if HTTPS_POLICY_MODE.load(Ordering::Relaxed){row["actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives"]=json!(true);}
    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){row["actual_atomic_policy_lock_and_binding_checks"]=json!(true);}Ok(row)''',
        '''    if HTTPS_POLICY_MODE.load(Ordering::Relaxed){row["actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives"]=json!(true);}Ok(row)''')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'case.rs'],'HTTPS542_ENTIRE_CONSUMED541_CASE_AND_RECOVERY_BODY_PRESERVED_NO_REPLAY')
    text=q.text(POLICY_FIXTURE).replace('#[path="https_atomic_fixture.rs"]mod atomic;\npub(super) fn atomic_execute()->Result<Value>{atomic::execute()}\n','')
    a=text.index('fn admitted_revision(');b=text.index('fn config()',a);text=text[:a]+text[b:]
    text=text.replace('row["migrations"]=json!(25);\n    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){atomic::install(&mut c,&mut row)?;}Ok(row)','row["migrations"]=json!(25);Ok(row)')
    text=text.replace('admitted_artifact(&artcfg,tenant()?)','LocalPostgresMetadataRepository::connect_schema25(&artcfg,tenant()?)')
    text=text.replace('admitted_revision(&cfg,rc.clone())','LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc.clone(),None)')
    text=text.replace('admitted_revision(&cfg,rc)','LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&cfg,rc,None)')
    text=text.replace('.is_ok()&&LocalPostgresMetadataRepository::connect_schema25','.is_ok()\n        &&LocalPostgresMetadataRepository::connect_schema25')
    text=text.replace('    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){atomic::revoked_denied(&first)?;}\n','').replace('    if HTTPS_ATOMIC_MODE.load(Ordering::Relaxed){atomic::locks_and_binding(&second)?;}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'policy-fixture.rs'],'HTTPS542_OLD_POLICY_ISSUER_NEGATIVE_CASES_AND_INVARIANTS_PRESERVED')
    r.audit.inverse(q.text(CAMPAIGN).replace('schema_version in(23,24,25,26)','schema_version in(23,24,25)'),q.snapshots[ARCHIVE+'campaign.py'],'HTTPS542_DEFAULT_CAMPAIGN_RESOURCE_AND_COUNTER_CONTROLS_UNCHANGED')
    text=q.text('tools/p09/native_postgres_cluster.py').replace("expected_version in(23,24,25,26),'PG_EXPLICIT23_OR24_OR25_OR26_MIGRATION_SCOPE'","expected_version in(23,24,25),'PG_EXPLICIT23_OR24_OR25_MIGRATION_SCOPE'")
    r.audit.inverse(text,q.snapshots[ARCHIVE+'cluster.py'],'HTTPS542_ALL_OLD_CLUSTER_LIFECYCLE_AND_RESOURCE_CONTROLS_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/worker.OBSERVATION).exists()and not worker.OWNED.exists(),'HTTPS542_FRESH_OWNED_RUN_ONLY_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;observation=None
    row=dict(state='FAILED_HTTPS_ATOMIC_SQL26',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,official249_SQL520_external003_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_database_or_trust_release_or_keys_changed=False,production_route_worker_policy_issuer_or_key_custody_qualified=False,
        consumed541_SQL_or_old_cases_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e245e19d43d0accb4bf455bef1357962caa757e2c6c1778922edc0f4ac950358'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==885 and base['actual_SQL_policy_register_revoke_select_and_negative_security_checks']is True,'HTTPS542_EXACT541_CLOSURE')
        names=inventory.inventory(guard)|{SELF,BASE,PRODUCT,COMMON,PROBE,LEAF,WORKER,CAMPAIGN,MANIFEST,deps.CAPTURE,
            *[ARCHIVE+v for v in CHANGED.values()],'tools/p09/search_sql_receipt.py','tools/p09/paced_postgres_hash.py',
            'tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py','tools/p09/native_postgres_ascii_campaign.py',
            'tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}
        names|=includes.test_inputs((PROBE,),guard)
        names|={'crates/product-cli/examples/sql25_https_policy_recovery.rs','migrations/postgres/0026_p09_https_policy_atomic_commit.down.sql'}
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'HTTPS542_BOUNDED_COMPILE_INPUTS')
        for name in sorted(names):q.pin(name)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/')or('/src/'not in pin['path']and pin['path']not in(COMMON,LEAF,POLICY_FIXTURE)):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS542_ALL_ORIGINAL_PRODUCT_LIBRARY_AND_COORDINATOR_GUARDS_PRESERVED')
        inverse(q)
        c.require(q.snapshots[MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','HTTPS542_EXACT_RUNTIME_MANIFEST')
        for path in(SELF,WORKER,CAMPAIGN):ast.parse(q.text(path))
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-sql-scratch542';c.require(not scratch.exists(),'HTTPS542_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(c.ROOT/'tools/p09'))
        artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql26_https_atomic_recovery'
        print(json.dumps(dict(state='HTTPS_SQL_PREFLIGHT',inputs=len(q.snapshots),SQL_cases=1,previous_tests_replayed=False,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_fresh_HTTPS_SQL26_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'HTTPS542_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d';artifact.pin(dep_path);declared=deps.dependencies(c.ROOT/dep_path)
        c.require(declared<=set(q.snapshots),'HTTPS542_ALL_ACTUAL_PROBE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_HTTPS_SQL26_job_and_readonly_recovery',[sys.executable,str(c.ROOT/WORKER),'--owned-schema26-https-atomic-542'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'HTTPS542_EXACT_OWNED_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_HTTPS_SQL26_ATOMIC_POLICY_LOCKS_ORIGINAL_CAS_AND_PUBLIC_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['https_SQL_cases']==1
            and observation['actual_atomic_policy_guard']is True,'HTTPS542_ACTUAL_JOB_RESTART_RECOVERY_NO_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['read_passes']>=3166 and io['full_fresh_hash_preserved']is True
            and io['raw_or_parsed_content_cached']is False and io['max_file_opens_per_second']==20,'HTTPS542_TWO_FULL_PACED_RUNTIME_READS_NO_CACHE')
        c.require(not any(scratch.iterdir()),'HTTPS542_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_SQL26_ATOMIC_POLICY_ORIGINAL_CAS_AND_PUBLIC_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL26_started=True,actual_claim_lease_registered_CAS_completion=True,actual_public_request_registered_effect_recovery=True,
            actual_SQL_counts=observation['snapshots'][0],actual_SQL_policy_counts=observation['policy_snapshots'][0],atomic_policy_same_CAS_transaction=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS542_FAILURE_NO_RAW_VALUES')
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
