"""545: current product bytes unchanged; one new integrated actual SQL policy-revocation race, no native work."""
import ast,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_late_revoke as worker
SELF='tools/p09/verify_https_late_revoke_sql.py'
OUTPUT='implementation/p09/evidence/p09-361-https-late-revoke-sql545.v1.json'
BASE='implementation/p09/evidence/p09-361-https-atomic-sql543.v1.json'
COMMON='crates/product-cli/examples/sql23_storage.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
POLICY='crates/product-cli/examples/sql23_storage/https_policy_fixture.rs'
PROBE='crates/product-cli/examples/sql26_https_late_revoke.rs'
CASE='crates/product-cli/examples/sql23_storage/https_late_revoke.rs'
WORKER='tools/p09/native_postgres_https_late_revoke.py'
CAMPAIGN='tools/p09/native_postgres_storage.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
ARCHIVE='implementation/p09/source-archive/p361-https-late-revoke544/'
FAILED='implementation/p09/evidence/p09-361-https-late-revoke-sql544.v1.json'
FIX='implementation/p09/source-archive/p361-https-late-revoke545/'
FIXED={CASE:'case544.rs',COMMON:'common544.rs',SELF:'verifier544.py',WORKER:'worker544.py'}
def unchanged(q):
    text=q.text(COMMON).replace('const HTTPS_LATE_REVOKE_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-late-revoke-545";\nstatic HTTPS_LATE_REVOKE_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n','')
    text=text.replace('if HTTPS_LATE_REVOKE_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_LATE_REVOKE_ROOT}else if HTTPS_ATOMIC_MODE','if HTTPS_ATOMIC_MODE')
    text=text.replace('pub fn https_late_revoke_main(){HTTPS_LATE_REVOKE_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_atomic_recovery_main()}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'common.rs'],'HTTPS545_OLD_SUCCESS_CONNECTORS_KEYS_ROOTS_AND_MAIN_UNCHANGED')
    text=q.text(LEAF).replace('#[path="https_late_revoke.rs"]mod late_revoke;\n','')
    text=text.replace('''let version=if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed){source.prepare_https_policy_registration(&p,&policy,0,limits()?.targets,10)?
        .register(&p,&postgres::PostgresHttpsTargetPolicyProvider::new(repository()?),10)?}
        else if HTTPS_POLICY_MODE''','let version=if HTTPS_POLICY_MODE')
    text=text.replace('json!(!HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed))','json!(true)')
    text=text.replace('    if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed){return late_revoke::execute();}\n','')
    text=text.replace('if HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed)&&matches!(mode,"--restart-registered"|"--cold-recover"){return late_revoke::observe();}','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'case.rs'],'HTTPS545_OLD_PRODUCT_SUCCESS_AND_COLD_RECOVERY_BODY_UNCHANGED')
    r.audit.inverse(q.text(POLICY),q.snapshots[ARCHIVE+'policy-fixture.rs'],'HTTPS545_PREVIOUS_POLICY_AND_LOCK_TESTS_UNCHANGED_NOT_REPLAYED')
    text=q.text(CAMPAIGN).replace(",execution_outcome='completed'):",'):',1)
    a=text.index("    cluster.require(execution_outcome in(");b=text.index('    cluster.require(type(expected_artifacts)',a);text=text[:a]+text[b:]
    text=text.replace('            if denied:expected.update(succeeded_jobs=1,successful_records=1,revisions=1,seals=1,head=1)\n','')
    text=text.replace("        if not denied:probe('--wrong-key')\n        cluster.stop(process,capture,binary,data,env,receipt);process=capture=None",
        "        probe('--wrong-key');cluster.stop(process,capture,binary,data,env,receipt);process=capture=None")
    a=text.index("        if denied:receipt.update(state=");b=text.index('    finally:',a);text=text[:a]+text[b:]
    r.audit.inverse(text,q.snapshots[ARCHIVE+'campaign.py'],'HTTPS545_OLD_SQL_CAMPAIGN_DEFAULT_CHECKS_PROTECTIONS_AND_TEARDOWN_UNCHANGED')
def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/worker.OBSERVATION).exists()and not worker.OWNED.exists(),'HTTPS545_FRESH_OWNED_RUN_ONLY_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None;observation=None
    row=dict(state='FAILED_HTTPS_LATE_REVOKE_SQL26',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,prior_success_or_official249_SQL520_external003_or_Native_replayed=False,
        external003_cleanup_or_claim_changed=False,operating_database_or_trust_release_or_keys_changed=False,
        production_route_worker_issuer_or_key_custody_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='66854516e9f612e46f2ee55e97e289dd47673195c9f7bdb7af46308640bef8f7'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==881
            and base['atomic_policy_same_CAS_transaction']is True,'HTTPS545_EXACT543_CLOSED_BASELINE')
        names=inventory.inventory(guard)|{SELF,BASE,FAILED,*[FIX+n for n in FIXED.values()],COMMON,LEAF,POLICY,PROBE,CASE,WORKER,CAMPAIGN,MANIFEST,deps.CAPTURE,
            *[ARCHIVE+v for v in('common.rs','case.rs','policy-fixture.rs','campaign.py')],
            'tools/p09/search_sql_receipt.py','tools/p09/paced_postgres_hash.py','tools/p09/native_postgres_cluster.py',
            'tools/p09/native_postgres_runtime.py','tools/p09/native_postgres_ascii_campaign.py',
            'tools/p09/fixtures/native_postgres_hba.conf','tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}
        names|=includes.test_inputs((PROBE,),guard)
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'HTTPS545_BOUNDED_COMPILE_INPUTS')
        for name in sorted(names):q.pin(name)
        for pin in base['source_pins']:
            if not pin['path'].startswith('crates/')or'/src/'not in pin['path']:continue
            actual=q.snapshots[pin['path']];c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS545_ALL_CURRENT_PRODUCT_LIBRARIES_AND_ORIGINAL_COORDINATOR_BYTE_EXACT')
        unchanged(q)
        failed=layout.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='51e939001ee438827fc911bbded09b20c178510cff2937d2c6f4737e462e2f10'
            and failed['fresh_inputs']==865 and failed['final_fresh_hashes']==0 and failed['cleanup']is True and len(failed['steps'])==1
            and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0277'],'HTTPS545_PRESERVED544_COMPILE_FAILURE_NO_SQL_NO_FINAL_CLOSURE')
        for pin in failed['source_pins']:
            actual=q.snapshots[FIX+FIXED[pin['path']]]if pin['path']in FIXED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS545_ALL_OTHER544_INPUTS_PRESERVED')
        text=q.text(CASE).replace('use std::sync::atomic::AtomicBool;','use std::cell::Cell;')
        text=text.replace('phase:AtomicUsize,last_reads:AtomicUsize,revoked:AtomicBool','phase:Cell<usize>,last_reads:Cell<usize>,revoked:Cell<bool>')
        text=text.replace('self.phase.load(Ordering::SeqCst)','self.phase.get()').replace('let reads=self.last_reads.fetch_add(1,Ordering::SeqCst)+1;','let reads=self.last_reads.get()+1;self.last_reads.set(reads);')
        text=text.replace('self.revoked.swap(true,Ordering::SeqCst)','self.revoked.replace(true)')
        text=text.replace('phase:AtomicUsize::new(0),last_reads:AtomicUsize::new(0),revoked:AtomicBool::new(false)','phase:Cell::new(0),last_reads:Cell::new(0),revoked:Cell::new(false)')
        text=text.replace('policy.phase.fetch_add(1,Ordering::SeqCst);','policy.phase.set(policy.phase.get()+1);')
        text=text.replace('policy.phase.load(Ordering::SeqCst)','policy.phase.get()').replace('policy.last_reads.load(Ordering::SeqCst)','policy.last_reads.get()').replace('policy.revoked.load(Ordering::SeqCst)','policy.revoked.get()')
        r.audit.inverse(text,q.snapshots[FIX+'case544.rs'],'HTTPS545_ONLY_FIXTURE_CELL_TO_ATOMICS_NO_PRODUCT_OR_ASSERTION_WEAKENING')
        c.require(q.snapshots[MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','HTTPS545_EXACT_RUNTIME_MANIFEST')
        for path in(SELF,WORKER,CAMPAIGN):ast.parse(q.text(path))
        guard.check(force=True);scratch=c.ROOT/'target/p09-https-late-scratch545';c.require(not scratch.exists(),'HTTPS545_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(c.ROOT/'tools/p09'))
        artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql26_https_late_revoke'
        print(json.dumps(dict(state='HTTPS_LATE_SQL_PREFLIGHT',inputs=len(q.snapshots),new_SQL_denial_cases=1,previous_cases_replayed=False,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_new_late_revocation_SQL26_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'HTTPS545_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d';artifact.pin(dep_path);declared=deps.dependencies(c.ROOT/dep_path)
        c.require(declared<=set(q.snapshots),'HTTPS545_ALL_ACTUAL_PROBE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_new_actual_late_policy_revocation_and_restart_observation',[sys.executable,str(c.ROOT/WORKER),'--owned-schema26-https-late-revoke-545'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'HTTPS545_EXACT_OWNED_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_HTTPS_SQL26_LATE_POLICY_REVOCATION_ORIGINAL_CAS_DENIAL_AND_RESTART_NO_REEXECUTION_NOT_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['new_SQL_denial_cases']==1,'HTTPS545_ACTUAL_FINAL_BOUNDARY_DENIAL_NO_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['read_passes']>=3166 and io['full_fresh_hash_preserved']is True
            and io['raw_or_parsed_content_cached']is False and io['max_file_opens_per_second']==20,'HTTPS545_TWO_FULL_PACED_RUNTIME_READS_NO_CACHE')
        c.require(not any(scratch.iterdir()),'HTTPS545_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_HTTPS_SQL26_LATE_REVOCATION_ACTUAL_ORIGINAL_CAS_DENIAL_AND_RESTART_NOT_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL26_started=True,actual_original_CAS_denied_after_last_app_policy_read=True,
            actual_result_intent_precommit_retained_no_revision_or_head_change=True,actual_restart_existing_attempt_not_reexecuted=True,
            actual_SQL_counts=observation['snapshots'][0],actual_SQL_policy_counts=observation['policy_snapshots'][0],compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS545_FAILURE_NO_RAW_VALUES')
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
