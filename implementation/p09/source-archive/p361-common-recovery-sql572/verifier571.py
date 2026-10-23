"""One fresh SQL26 common prepare/atomic-CAS/restart/cold observation, never consumed DB replay."""
import ast,hashlib,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import crossref_inline_receipt567 as model_layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_common571_recovery as worker
SELF='tools/p09/verify_common_recovery_sql571.py'
OUTPUT='implementation/p09/evidence/p09-361-common-recovery-sql571.v1.json'
BASE='implementation/p09/evidence/p09-361-source-lease-and-common-recovery570.v1.json'
FAILED='implementation/p09/evidence/p09-361-https-common-sql564.v1.json'
OLD_OBS='target/p09-https-common-sql26-observation-564.json'
ARCHIVE='implementation/p09/source-archive/p361-common-recovery-sql571/'
COMMON='crates/product-cli/examples/sql23_storage.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
CASE='crates/product-cli/examples/sql23_storage/https_common_fixture.rs'
PROBE='crates/product-cli/examples/sql26_https_common571_recovery.rs'
WORKER='tools/p09/native_postgres_https_common571_recovery.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
PREIMAGES={COMMON:'storage570.rs',LEAF:'recovery570.rs',CASE:'common570.rs'}

def inverse(q):
    text=q.text(COMMON)
    for addition in('const HTTPS_COMMON571_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-common-571";\n',
        'static HTTPS_COMMON571_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n',
        'if HTTPS_COMMON571_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_COMMON571_ROOT}else ',
        'pub fn https_common_recovery571_main(){HTTPS_COMMON571_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_common_recovery_main()}\n'):
        r.c.require(text.count(addition)==1,'SQL571_ONE_FIXED_FRESH_ROOT_NO_CALLER_CHOICE');text=text.replace(addition,'',1)
    r.audit.inverse(text,q.snapshots[ARCHIVE+PREIMAGES[COMMON]],'SQL571_OLD_MODE_ROOTS_CONNECTORS_AND_CLOSED_COMMANDS_UNCHANGED')
    text=q.text(CASE);start=text.index('    let prepare=||->Result<_>{');end=text.index('    let denied=prepare()?',start)
    new=text[start:end];r.c.require(new.count('prepare_json_or_observe_with_https_policy')==1 and 'PolicyBoundRequestEntry::Prepared(product)'in new,'SQL571_COMMON_FRESH_PREPARATION_VARIANT_ONLY')
    text=text[:start]+'    let prepare=||Product::prepare_json_with_https_policy(&provider,&policy,&wire,None,PolicyBoundOperationLimits::standard()?,10);\n'+text[end:]
    r.audit.inverse(text,q.snapshots[ARCHIVE+PREIMAGES[CASE]],'SQL571_ORIGINAL_GUARDED_COORDINATOR_AND_ALL_OUTPUT_ASSERTIONS_UNCHANGED')
    original=q.text(ARCHIVE+PREIMAGES[LEAF]);text=q.text(LEAF)
    start=text.index('        let job=if HTTPS_COMMON571_MODE');end=text.index('        check(job.state()',start)
    new=text[start:end];r.c.require('PolicyBoundRequestEntry::ExistingHttps(job)'in new and '&NoPolicyReads'in new and 'prepare_json_or_observe_with_https_policy'in new,'SQL571_COMMON_EXISTING_OBSERVATION_WITHOUT_POLICY_OR_COMPILATION')
    old_start=original.index('        let HttpsTargetRequestEntry::Existing(job)=');old_end=original.index('        check(job.state()',old_start)
    text=text[:start]+original[old_start:old_end]+text[end:]
    start=text.index('        if HTTPS_COMMON571_MODE.load(Ordering::Relaxed){');end=text.index('        check(matches!(Product::prepare_https_targets_lookup_json',start)
    r.c.require('StoredRequestLookupError::KeyConflict'in text[start:end],'SQL571_EXACT_COMMON_CONFLICT_NOT_GENERIC_ERROR');text=text[:start]+text[end:]
    start=text.index('        let mut row=json!({"state":"PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES"');end=text.index('    })();let mut restored',start)
    old_start=original.index('        Ok(json!({"state":"PASS_HTTPS_PUBLIC_REQUEST_REGISTERED_EFFECT_RECOVERY_NO_LOCAL_HANDLES"');old_end=original.index('    })();let mut restored',old_start)
    text=text[:start]+original[old_start:old_end]+text[end:]
    r.audit.inverse(text,q.snapshots[ARCHIVE+PREIMAGES[LEAF]],'SQL571_ALL_ORIGINAL_ACL_READBACK_RECOVERY_CONFLICT_AND_RESTORE_BODY_PRESERVED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--one-fresh-common-sql-only'],'SQL571_CLOSED_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'SQL571_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=observation=None;started=time.monotonic()
    row=dict(state='FAILED_COMMON_RECOVERY_SQL571',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Hancom_COM_Native_or_249_started=False,consumed563_564_databases_restarted_or_product_replayed=False,external004_replayed=False,
        operating_database_registry_worker_custody_or_admission_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=model_layout.unpack(q.json(BASE));failed=layout.unpack(q.json(FAILED))
        c.require(q.snapshots[BASE]['sha256']=='d761f02315d379d2de7e8704e0bcf941eb57826c8bb5ce88450571509817d515'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==859 and base['new_common_product_cases']==5,'SQL571_EXACT570_COMMON_API_MODELS_NOT_REPLAYED')
        c.require(q.snapshots[FAILED]['sha256']=='bbb66ab756929c1b3f923f60acb88aa5ac395ff94bc9176e9a11692fb3439436'
            and failed['cleanup']is True and failed['final_fresh_hashes']==0 and failed['database_stage']=='completed_before_restart'
            and failed['database_error']=='PG_STORAGE_EXACT_COMPLETED_SINGLE_ATTEMPTS_AND_SEALED_HEAD','SQL571_ORIGINAL564_FAILURE_AND_MISSING_RESTART_PRESERVED')
        names=inventory.inventory(guard)|includes.test_inputs((PROBE,),guard)|{SELF,BASE,FAILED,OLD_OBS,COMMON,LEAF,CASE,PROBE,WORKER,MANIFEST,deps.CAPTURE,
            'tools/p09/native_postgres_storage.py','tools/p09/paced_postgres_hash.py','tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_runtime.py',
            'tools/p09/native_postgres_ascii_campaign.py','tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql',
            'tools/p09/fixtures/sql23_service_roles.sql'}|{ARCHIVE+v for v in PREIMAGES.values()}|{ARCHIVE+'worker564.py',ARCHIVE+'verifier564.py'}
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'SQL571_CLOSED_CURRENT_INPUT_COUNT')
        for name in sorted(names):q.pin(name)
        for pin in base['source_pins']:
            if pin['path'].startswith('crates/')and'/src/'in pin['path']:
                c.require(q.snapshots[pin['path']]==pin,'SQL571_QUALIFIED_COMMON_PRODUCT_AND_POLICY_SQL_LIBRARY_UNCHANGED')
        inverse(q)
        oldpins={p['path']:p for p in failed['source_pins']};c.require(q.snapshots[OLD_OBS]==oldpins[OLD_OBS],'SQL571_EXACT_FAILED564_OBSERVATION_NO_RECONSTRUCTION')
        command,=[v for v in q.json(OLD_OBS)['commands']if v['stage']=='completed_before_restart']
        projection=dict(artifacts=8,available=8,jobs=2,succeeded_jobs=2,successful_records=2,attempts=2,authorizations=0,intents=1,revisions=2,seals=2,head=2)
        raw=(json.dumps(projection,separators=(', ',' : '))+'\r\n').encode()
        c.require(command['exit_code']==0 and len(raw)==command['stdout_bytes']==191 and hashlib.sha256(raw).hexdigest()==command['stdout_sha256'],
            'SQL571_EIGHT_ARTIFACT_EXPECTATION_PROVEN_BY_EXACT_RECORDED_STDOUT_NOT_GUESSED')
        c.require(q.snapshots['tools/p09/native_postgres_storage.py']['sha256']=='ba068a5c8d8a8e2e5f767044fc6f0431bf0a690b9b24947cc2dc7de6ebdac4ae','SQL571_CURRENT_STRICT_SNAPSHOT_HELPER_UNCHANGED')
        c.require(not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'SQL571_FRESH_DATABASE_AND_OBSERVATION_ONLY')
        for name in(SELF,WORKER):ast.parse(q.text(name))
        scratch=c.ROOT/'target/p09-common-recovery-sql571-scratch';c.require(not scratch.exists(),'SQL571_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql26_https_common571_recovery'
        print(json.dumps(dict(state='COMMON_SQL571_PREFLIGHT',inputs=len(q.snapshots),fresh_SQL_cases=1,cold_recovery_calls=1,duplicate_recovery_calls=0,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_common_SQL571',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'SQL571_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep='target/debug/examples/'+name+'.d';artifact.pin(dep)
        declared=deps.dependencies(c.ROOT/dep);c.require(declared<=set(q.snapshots),'SQL571_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_SQL571_common_prepare_CAS_restart_cold_observation',[sys.executable,str(c.ROOT/WORKER),'--owned-schema26-https-common-571'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'SQL571_EXACT_WORKER_OBSERVATION')
        c.require(observation['state']=='PASS_COMMON_HTTPS_SQL26_CURRENT_POLICY_ORIGINAL_CAS_AND_COLD_RECOVERY_NOT_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['common_prepare_and_recovery_entry']is True
            and observation['duplicate_equivalent_cold_recovery_probe_executed']is False,'SQL571_ACTUAL_SQL_AND_COMMON_RECOVERY_NOT_NATIVE_OR_ADMISSION')
        io=observation['fresh_runtime_hash_io'];c.require(io['full_fresh_hash_preserved']is True and io['raw_or_parsed_content_cached']is False
            and io['max_file_opens_per_second']==20,'SQL571_FULL_FRESH_RUNTIME_HASHES_ORIGINAL_PACER_NO_CACHE')
        c.require(observation['snapshots']==[projection,projection],'SQL571_EXACT_BEFORE_AFTER_SINGLE_ATTEMPT_HEAD_AND_ARTIFACT_COUNTS')
        c.require(not any(scratch.iterdir()),'SQL571_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_SQL571_PREPARE_ORIGINAL_ATOMIC_CAS_AND_SINGLE_COLD_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL26_started=True,actual_common_prepare_claim_lease_registered_CAS_completion=True,actual_common_existing_cold_recovery=True,
            SQL_counts=projection,SQL_policy_counts=observation['policy_snapshots'][0],policy_in_original_CAS_transaction=True,
            duplicate_equivalent_recovery_calls=0,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'SQL571_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        if observation is not None:row.update(database_stage=observation.get('stage'),database_error=observation.get('error_code'),
            last_probe=None if not observation['probes']else observation['probes'][-1],fresh_runtime_hash_io=observation.get('fresh_runtime_hash_io'),
            all_owned_postmasters_normal_stop=observation.get('all_owned_postmasters_normal_stop',False))
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        proof=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','database_stage','database_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]))for s in row['steps']],'receipt':proof}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
