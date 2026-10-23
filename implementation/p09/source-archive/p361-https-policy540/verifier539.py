"""539: real exact25 HTTPS policy publication/selection/revocation and job/recovery; not attested issuer/admission/Native/Gate."""
import ast,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_policy_recovery as worker
SELF='tools/p09/verify_https_policy_sql.py'
OUTPUT='implementation/p09/evidence/p09-361-https-policy-sql539.v1.json'
BASE='implementation/p09/evidence/p09-361-https-target-sql537.v1.json'
PRODUCT='crates/product-cli/src/form_stored_provider/actual_import/https_target_output.rs'
COMMON='crates/product-cli/examples/sql23_storage.rs'
PROBE='crates/product-cli/examples/sql25_https_policy_recovery.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
WORKER='tools/p09/native_postgres_https_policy_recovery.py'
CAMPAIGN='tools/p09/native_postgres_storage.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
ARCHIVE='implementation/p09/source-archive/p361-https-policy538/'

CHANGED={
 'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs.rs':'jobs.rs',
 'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/admission.rs':'admission.rs',
 'crates/artifact-service/src/store/postgres_repository.rs':'artifact-parent.rs',
 'crates/artifact-service/src/store/postgres_repository/schema24.rs':'artifact24.rs',
 PRODUCT:'product.rs',COMMON:'common.rs',LEAF:'case.rs',CAMPAIGN:'campaign.py','tools/p09/native_postgres_cluster.py':'cluster.py'}

RECOVERY_ARCHIVE='implementation/p09/source-archive/p361-https-policy539/'
FAILED='implementation/p09/evidence/p09-361-https-policy-sql538.v1.json'
LOW='crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/https_policy.rs'
RECOVERY_CHANGED={SELF:'verifier538.py',WORKER:'worker538.py',COMMON:'common538.rs',LOW:'policy538.rs'}

def inverse(q):
    text=q.text('crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs.rs')
    text=text.replace('pub mod https_policy;\n','').replace(',https_policy_qualified:bool','')
    start=text.index('    /// Exact schema25 plus');end=text.index('    fn connect_mode',start);text=text[:start]+text[end:]
    text=text.replace('lease,false,false)','lease,false)').replace('lease,true,false)','lease,true)')
    text=text.replace('lookup:bool,https:bool)','lookup:bool)')
    text=text.replace('if https{admission::admit_with_https(&mut client)?;}else if lookup','if lookup')
    text=text.replace(',https_policy_qualified:https','').replace(',https_policy_qualified:self.https_policy_qualified','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'jobs.rs'],'HTTPS539_ALL_OLD_23_24_JOB_CONNECTOR_GUARDS_AND_LIFECYCLE_BODY_RESTORED')
    text=q.text('crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/admission.rs')
    text=text.replace('pub(super) fn admit_with_https(client:&mut Client)->Result<(),RevisionError>{admit_mode(client,true,true)}\n','')
    text=text.replace('admit_mode(client,false,false)','admit_mode(client,false)').replace('admit_mode(client,true,false)','admit_mode(client,true)')
    text=text.replace('lookup:bool,https:bool)','lookup:bool)')
    text=text.replace('if https{"SELECT version,migration_name,migration_sha256::text FROM hwpx_agent.schema_versions ORDER BY version LIMIT 26"}\n        else if lookup','if lookup')
    text=text.replace('if https{https_policy::schema25(&rows)?;request_lookup::schema24(&rows[..24])?;schema(&rows[..23])?;}\n    else if lookup','if lookup')
    text=text.replace('if https{https_policy::admit(client)?;}','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'admission.rs'],'HTTPS539_OLD_EXACT_SCHEMA_FUNCTION_TABLE_ROLE_AND_LOOKUP_CHECKS_BYTE_IDENTICAL')
    r.audit.inverse(q.text('crates/artifact-service/src/store/postgres_repository.rs').replace('pub mod schema25;\n',''),q.snapshots[ARCHIVE+'artifact-parent.rs'],'HTTPS539_ALL_ORIGINAL_ARTIFACT_SERVICE_GUARDS_UNCHANGED')
    r.audit.inverse(q.text('crates/artifact-service/src/store/postgres_repository/schema24.rs').replace('pub(super) fn validate','fn validate'),q.snapshots[ARCHIVE+'artifact24.rs'],'HTTPS539_ENTIRE_ORIGINAL_ARTIFACT24_CONSTRUCTOR_AND_SCHEMA_CHECK_UNCHANGED')
    text=q.text(PRODUCT).replace('pub mod registration;\n','').replace('pub mod postgres;\n','')
    text=text.replace('latest version and revocation. No stale fallback. SQL adapters do not attest external issuers or execution.','latest version and revocation. No stale fallback. An SQL/issuer adapter is not supplied here.')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'product.rs'],'HTTPS539_ALL_ORIGINAL_SOURCE_POLICY_LOWERING_FRESH_AND_PUBLICATION_GUARDS_UNCHANGED')
    text=q.text(COMMON).replace('const HTTPS_POLICY_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-policy-539";\nstatic HTTPS_POLICY_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n','')
    text=text.replace('if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_POLICY_ROOT}else if HTTPS_MODE','if HTTPS_MODE')
    text=text.replace('if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresStoredRevisionJobsRepository::connect_with_https_policy(&config,context()?,None)?}\n        else if LOOKUP_MODE','if LOOKUP_MODE')
    text=text.replace('if HTTPS_POLICY_MODE.load(std::sync::atomic::Ordering::Relaxed){LocalPostgresMetadataRepository::connect_schema25(&config,tenant()?)?}\n        else if LOOKUP_MODE','if LOOKUP_MODE')
    text=text.replace('pub fn https_policy_recovery_main(){HTTPS_POLICY_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_target_recovery_main()}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'common.rs'],'HTTPS539_ALL_OLD_SQL_ROOTS_CRYPTO_SOURCE_JOB_AND_RECOVERY_FIXTURES_PRESERVED')
    text=q.text(LEAF).replace('#[path="https_policy_fixture.rs"]mod policy_fixture;\n','')
    text=text.replace(',sql:Option<postgres::PostgresHttpsTargetPolicyProvider>','')
    text=text.replace('        if let Some(sql)=&self.sql{self.reads.fetch_add(1,Ordering::SeqCst);return sql.read_current(s);}\n','')
    text=text.replace('''    let version=if HTTPS_POLICY_MODE.load(Ordering::Relaxed){policy_fixture::publish_and_check(&a,&revisions,&p,&source,&policy)?}
        else{let d=ingest(&a,&serde_json::to_vec(&json!({"schema_version":HTTPS_TARGET_POLICY_SCHEMA,"binding":b,"policy":policy}))?,ArtifactKind::Evidence,
            HTTPS_TARGET_POLICY_MEDIA_TYPE,"isolated-https-policy.json")?;HttpsTargetPolicyVersion{binding:b,artifact:d.artifact_id,digest:d.sha256}};
    save_value("https-policy-version.json",&json!({"binding":version.binding,"artifact":version.artifact.public_id(),"digest":version.digest.hex()}))?;''','''    let d=ingest(&a,&serde_json::to_vec(&json!({"schema_version":HTTPS_TARGET_POLICY_SCHEMA,"binding":b,"policy":policy}))?,ArtifactKind::Evidence,
        HTTPS_TARGET_POLICY_MEDIA_TYPE,"isolated-https-policy.json")?;
    save_value("https-policy-version.json",&json!({"binding":b,"artifact":d.artifact_id.public_id(),"digest":d.sha256.hex()}))?;''')
    text=text.replace('''    row["actual_policy_AEAD_artifact"]=json!(true);row["policy_selector_isolated_not_operational"]=json!(!HTTPS_POLICY_MODE.load(Ordering::Relaxed));
    if HTTPS_POLICY_MODE.load(Ordering::Relaxed){row["actual_SQL_policy_registration_revocation_current_ACLs_and_admission_negatives"]=json!(true);}Ok(row)''','''    row["actual_policy_AEAD_artifact"]=json!(true);row["policy_selector_isolated_not_operational"]=json!(true);Ok(row)''')
    text=text.replace('''reads:AtomicUsize::new(0),
        sql:if HTTPS_POLICY_MODE.load(Ordering::Relaxed){Some(postgres::PostgresHttpsTargetPolicyProvider::new(repository()?))}else{None}};''','reads:AtomicUsize::new(0)};')
    text=text.replace('if HTTPS_POLICY_MODE.load(Ordering::Relaxed){policy_fixture::install()}else{lookup24::run("--fixture")}','lookup24::run("--fixture")')
    text=text.replace('if HTTPS_POLICY_MODE.load(Ordering::Relaxed){"PASS_HTTPS_REAL_SQL25_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION"}else{"PASS_HTTPS_REAL_SQL24_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION"}','"PASS_HTTPS_REAL_SQL24_GUARDED_JOB_REGISTERED_CAS_COMPLETION_NOT_ADMISSION"')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'case.rs'],'HTTPS539_CONSUMED537_FIXTURE_ENTIRE_OLD_BODY_PRESERVED_NOT_REPLAYED')
    text=q.text(CAMPAIGN).replace(',after_restart=None','').replace('        if after_restart is not None:after_restart(sql,probe)\n','')
    text=text.replace('expected_artifacts in(6,7,9)','expected_artifacts in(6,7)').replace('schema_version in(23,24,25)','schema_version in(23,24)')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'campaign.py'],'HTTPS539_ALL_OLD_DEFAULT_CAMPAIGN_RESOURCE_OWNER_AND_COUNTER_GUARDS_UNCHANGED')
    text=q.text('tools/p09/native_postgres_cluster.py').replace("expected_version in(23,24,25),'PG_EXPLICIT23_OR24_OR25_MIGRATION_SCOPE'","expected_version in(23,24),'PG_EXPLICIT23_OR24_MIGRATION_SCOPE'")
    r.audit.inverse(text,q.snapshots[ARCHIVE+'cluster.py'],'HTTPS539_ALL_OLD_CLUSTER_RUNTIME_AUTH_RESOURCE_AND_CLEANUP_CODE_UNCHANGED')

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/worker.OBSERVATION).exists()and not worker.OWNED.exists(),'HTTPS539_FRESH_OWNED_RUN_ONLY_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;observation=None
    row=dict(state='FAILED_HTTPS_POLICY_SQL25',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,official249_SQL520_external003_or_previous_Native_replayed=False,external003_cleanup_or_claim_changed=False,
        operating_database_or_trust_release_or_keys_changed=False,production_route_worker_policy_issuer_or_key_custody_qualified=False,
        unchanged_536_eight_cases_and_consumed_SQL537_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='a4a5ef0909eb1506d0ed81876a439fbf257aa701d2ff7d6584bf8d24efaaac5c'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==850 and base['actual_claim_lease_registered_CAS_completion']is True,'HTTPS539_EXACT537_CLOSURE')
        names=inventory.inventory(guard)|{SELF,BASE,PRODUCT,COMMON,PROBE,LEAF,WORKER,CAMPAIGN,MANIFEST,deps.CAPTURE,
            *[ARCHIVE+v for v in CHANGED.values()],'tools/p09/search_sql_receipt.py','tools/p09/paced_postgres_hash.py',
            'tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py','tools/p09/native_postgres_ascii_campaign.py',
            'tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}
        names|=includes.test_inputs((PROBE,),guard)
        names|={FAILED,LOW,RECOVERY_ARCHIVE+'observed538.d'}|{RECOVERY_ARCHIVE+n for n in RECOVERY_CHANGED.values()}
        names|={'crates/product-cli/examples/sql24_https_target_recovery.rs','migrations/postgres/0025_p09_source_https_target_policy.down.sql'}
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'HTTPS539_BOUNDED_COMPILE_INPUTS')
        for name in sorted(names):q.pin(name)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/'):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS539_ALL_ORIGINAL_PRODUCT_LIBRARY_AND_COORDINATOR_GUARDS_PRESERVED')
        inverse(q)
        failed=layout.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='69a78fcdec42f54982a1f7fac556535a0ea60427881205ceb3d25b9e23502187'
            and failed['fresh_inputs']==863 and failed['final_fresh_hashes']==0 and failed['cleanup']is True
            and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==0 and len(failed['steps'][0]['diagnostics'])==1
            and failed.get('database_stage')is None,'HTTPS539_ORIGINAL538_WARNING_NO_SQL_AND_NO_FINAL_CLOSURE_PRESERVED')
        c.require(not (c.ROOT.parent.parent/'devdata/hwpx-agent-p09-pg18-https-policy-538').exists()
            and not(c.ROOT/'target/p09-https-policy-sql25-observation-538.json').exists(),'HTTPS539_ORIGINAL538_NEVER_REPLAYED')
        for pin in failed['source_pins']:
            actual=q.snapshots[RECOVERY_ARCHIVE+RECOVERY_CHANGED[pin['path']]]if pin['path']in RECOVERY_CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS539_ALL_UNRELATED538_INPUTS_AND_ALL_PRODUCT_SQL_BODIES_PRESERVED')
        fix='impl fmt::Debug for HttpsPolicySource{fn fmt(&self,f:&mut fmt::Formatter<\'_>)->fmt::Result{f.write_str("HttpsPolicySource(<redacted>)")}}\n'
        c.require(q.text(LOW).count(fix)==1,'HTTPS539_ONE_REDACTED_DEBUG_ONLY')
        r.audit.inverse(q.text(LOW).replace(fix,''),q.snapshots[RECOVERY_ARCHIVE+'policy538.rs'],'HTTPS539_ALL538_POLICY_QUERY_AND_SECURITY_BODIES_BYTE_IDENTICAL')
        row['failed538_SQL_or_product_cases_replayed']=False
        c.require(q.snapshots[MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','HTTPS539_EXACT_RUNTIME_MANIFEST')
        for path in(SELF,WORKER,CAMPAIGN):ast.parse(q.text(path))
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-sql-scratch539';c.require(not scratch.exists(),'HTTPS539_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(c.ROOT/'tools/p09'))
        artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql25_https_policy_recovery'
        print(json.dumps(dict(state='HTTPS_SQL_PREFLIGHT',inputs=len(q.snapshots),SQL_cases=1,previous_tests_replayed=False,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_fresh_HTTPS_SQL25_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'HTTPS539_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d';artifact.pin(dep_path);declared=deps.dependencies(c.ROOT/dep_path)
        c.require(declared<=set(q.snapshots),'HTTPS539_ALL_ACTUAL_PROBE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_HTTPS_SQL25_policy_job_and_readonly_recovery',[sys.executable,str(c.ROOT/WORKER),'--owned-schema25-https-policy-539'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'HTTPS539_EXACT_OWNED_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_ACTUAL_HTTPS_SQL25_POLICY_REGISTER_REVOKE_SELECT_GUARDED_JOB_AND_PUBLIC_RECOVERY_NOT_ATTESTED_ISSUER_ADMISSION_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['https_SQL_cases']==1,'HTTPS539_ACTUAL_JOB_RESTART_RECOVERY_NO_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['read_passes']>=3166 and io['full_fresh_hash_preserved']is True
            and io['raw_or_parsed_content_cached']is False and io['max_file_opens_per_second']==20,'HTTPS539_TWO_FULL_PACED_RUNTIME_READS_NO_CACHE')
        c.require(not any(scratch.iterdir()),'HTTPS539_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_POLICY_SQL25_REGISTER_REVOKE_SELECT_REAL_GUARDED_JOB_PUBLIC_RECOVERY_NOT_ATTESTED_ISSUER_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL25_started=True,actual_claim_lease_registered_CAS_completion=True,actual_public_request_registered_effect_recovery=True,
            actual_SQL_counts=observation['snapshots'][0],actual_SQL_policy_counts=observation['policy_snapshots'][0],actual_SQL_policy_register_revoke_select_and_negative_security_checks=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS539_FAILURE_NO_RAW_VALUES')
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
