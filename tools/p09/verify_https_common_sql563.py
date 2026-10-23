"""Common product -> original SQL26 coordinator integration in a fresh owned root; no Native/Gate."""
import ast,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import search_sql_receipt as layout
import run_native_postgres_runtime_qualification as postgres_runner
import native_postgres_https_common_recovery as worker
SELF='tools/p09/verify_https_common_sql563.py'
OUTPUT='implementation/p09/evidence/p09-361-https-common-sql563.v1.json'
BASE='implementation/p09/evidence/p09-361-https-common-dispatch562.v1.json'
ATOMIC='implementation/p09/evidence/p09-361-https-atomic-sql543.v1.json'
DISPATCH='crates/product-cli/src/form_product_request/stored_operations/https_targets/dispatch.rs'
BRIDGE=DISPATCH[:-3]+'/atomic_sql.rs'
COMMON='crates/product-cli/examples/sql23_storage.rs'
LEAF='crates/product-cli/examples/sql23_storage/https_target_recovery.rs'
POLICY='crates/product-cli/examples/sql23_storage/https_policy_fixture.rs'
CASE='crates/product-cli/examples/sql23_storage/https_common_fixture.rs'
PROBE='crates/product-cli/examples/sql26_https_common_recovery.rs'
WORKER='tools/p09/native_postgres_https_common_recovery.py'
MANIFEST='target/p09-native-postgres-18.6-5-278/runtime-manifest.json'
ARCHIVE='implementation/p09/source-archive/p361-https-common-sql563/'
CHANGED={DISPATCH:'dispatch-before.rs',COMMON:'common-before.rs',LEAF:'case-before.rs',POLICY:'policy-before.rs'}

def inverse(q):
    r.audit.inverse(q.text(DISPATCH).replace('pub mod atomic_sql;\n',''),q.snapshots[ARCHIVE+CHANGED[DISPATCH]],'HTTPS563_ALL_ORIGINAL_COMMON_POLICY_DISPATCH_AND_CONSUMER_CHECKS_PRESERVED')
    text=q.text(COMMON).replace('const HTTPS_COMMON_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-https-common-563";\n','')
    text=text.replace('static HTTPS_COMMON_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n','')
    text=text.replace('if HTTPS_COMMON_MODE.load(std::sync::atomic::Ordering::Relaxed){HTTPS_COMMON_ROOT}else ','')
    text=text.replace('pub fn https_common_recovery_main(){HTTPS_COMMON_MODE.store(true,std::sync::atomic::Ordering::Relaxed);https_atomic_recovery_main()}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+CHANGED[COMMON]],'HTTPS563_ALL_OLD_SQL_FIXTURE_ROOTS_CONNECTORS_BOOTSTRAP_AND_CLOSED_MODES_PRESERVED')
    text=q.text(POLICY).replace('#[path="https_common_fixture.rs"]mod common;\npub(super) fn common_execute()->Result<Value>{common::execute()}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+CHANGED[POLICY]],'HTTPS563_ALL_OLD_POLICY_ISSUER_REVOKE_LOCK_AND_ADMISSION_FIXTURES_PRESERVED_NOT_REPLAYED')
    text=q.text(LEAF);start=text.index('    let version=if HTTPS_COMMON_MODE.load(Ordering::Relaxed){')
    end=text.index('HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed){source.prepare_https_policy_registration',start)
    text=text[:start]+'    let version=if '+text[end:]
    text=text.replace('&&!HTTPS_COMMON_MODE.load(Ordering::Relaxed)','')
    added='    if HTTPS_COMMON_MODE.load(Ordering::Relaxed){row["actual_two_current_SQL_policy_generations_without_old_negative_matrix"]=json!(true);}Ok(row)\n'
    r.c.require(text.count(added)==1,'HTTPS563_ONE_NEW_SEED_OBSERVATION')
    text=text.replace(added,'Ok(row)\n').replace('json!(!HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed));}\nOk(row)','json!(!HTTPS_LATE_REVOKE_MODE.load(Ordering::Relaxed));}Ok(row)')
    text=text.replace('    if HTTPS_COMMON_MODE.load(Ordering::Relaxed){return policy_fixture::common_execute();}\n','')
    r.audit.inverse(text,q.snapshots[ARCHIVE+CHANGED[LEAF]],'HTTPS563_ALL_OLD_SEED_EXECUTE_COLD_RECOVERY_BODY_PRESERVED_OUTSIDE_EXPLICIT_NEW_MODE')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--one-fresh-common-sql-only'],'HTTPS563_CLOSED_MODE')
    c.require(not(c.ROOT/OUTPUT).exists()and not worker.OWNED.exists(),'HTTPS563_IMMUTABLE_FRESH_SCOPE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;observation=None
    row=dict(state='FAILED_COMMON_HTTPS_SQL26',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_or_Native_started=False,previous_SQL_or_249_or_Native_replayed=False,new_native_execution_authorized=False,
        operating_database_or_trust_release_or_keys_changed=False,operating_registry_worker_publication_or_long_term_custody_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE));old=layout.unpack(q.json(ATOMIC))
        c.require(q.snapshots[BASE]['sha256']=='c677d9d4e72f2707e9e5ee51bf1f8a2070099e469d93ddf015f20249886d3da0'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==853 and base['distinct_qualified_cases']==8,'HTTPS563_EXACT562_COMMON_SOURCE_CLOSURE')
        c.require(q.snapshots[ATOMIC]['sha256']=='66854516e9f612e46f2ee55e97e289dd47673195c9f7bdb7af46308640bef8f7'
            and old['cleanup']is True and old['fresh_inputs']==old['final_fresh_hashes']==881,'HTTPS563_CLOSED543_ATOMIC_SQL_RESULTS_NOT_REPLAYED')
        names=inventory.inventory(guard)|{SELF,BASE,ATOMIC,DISPATCH,BRIDGE,COMMON,LEAF,POLICY,CASE,PROBE,WORKER,MANIFEST,deps.CAPTURE,
            'tools/p09/native_postgres_storage.py','tools/p09/paced_postgres_hash.py','tools/p09/native_postgres_cluster.py',
            'tools/p09/native_postgres_runtime.py','tools/p09/native_postgres_ascii_campaign.py','tools/p09/fixtures/native_postgres_hba.conf',
            'tools/p09/fixtures/postgres_revision_adapter.sql','tools/p09/fixtures/sql23_service_roles.sql'}|{ARCHIVE+v for v in CHANGED.values()}
        names|=includes.test_inputs((PROBE,),guard)
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'HTTPS563_BOUNDED_INPUTS')
        for path in sorted(names):q.pin(path)
        for pin in base['source_pins']:
            path=pin['path']
            if not path.startswith('crates/')or('/src/'not in path and path not in CHANGED):continue
            current=q.snapshots[ARCHIVE+CHANGED[path]]if path in CHANGED else q.snapshots[path]
            c.require((current['bytes'],current['sha256'])==(pin['bytes'],pin['sha256']),'HTTPS563_ALL_OTHER_CURRENT_PRODUCT_SOURCE_UNCHANGED_OR_EXACT_PREIMAGE')
        inverse(q)
        for path in(SELF,WORKER):ast.parse(q.text(path))
        scratch=c.ROOT/'target/p09-https-common-sql-scratch563';c.require(not scratch.exists(),'HTTPS563_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        name='sql26_https_common_recovery'
        print(json.dumps(dict(state='HTTPS_COMMON_SQL_PREFLIGHT',inputs=len(q.snapshots),SQL_cases=1,previous_case_replay=False,CPU_cap_percent=6.25)),flush=True)
        r.harness.run_one('compile_common_HTTPS_SQL26_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,
            '--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'HTTPS563_COMPILE_WITHOUT_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+name+'.exe');dep_path='target/debug/examples/'+name+'.d';artifact.pin(dep_path)
        declared=deps.dependencies(c.ROOT/dep_path);c.require(declared<=set(q.snapshots),'HTTPS563_ALL_ACTUAL_COMPILER_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        env['P09_STORAGE_PROBE_SHA256']=binary['sha256']
        try:reply=postgres_runner.run_owned('one_fresh_common_SQL26_and_new_result_recovery',[sys.executable,str(c.ROOT/WORKER),'--owned-schema26-https-common-563'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(observation is not None and reply['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']
            and reply['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'HTTPS563_EXACT_FRESH_SQL_OBSERVATION')
        c.require(observation['state']=='PASS_COMMON_HTTPS_SQL26_CURRENT_POLICY_ORIGINAL_CAS_AND_COLD_RECOVERY_NOT_NATIVE_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and observation['operational_database_accessed']is False
            and observation['actual_Hancom_COM_or_Native_started']is False and observation['https_SQL_cases']==1
            and observation['actual_common_dispatch_atomic_policy_CAS']is True and observation['old_policy_security_negative_matrix_replayed']is False,
            'HTTPS563_ACTUAL_COMMON_DISPATCH_ORIGINAL_SQL_AND_RESTART_CLOSURE_NOT_NATIVE')
        io=observation['fresh_runtime_hash_io'];c.require(io['full_fresh_hash_preserved']is True and io['raw_or_parsed_content_cached']is False
            and io['max_file_opens_per_second']==20,'HTTPS563_PACED_CURRENT_RUNTIME_READS_NO_CACHE')
        c.require(not any(scratch.iterdir()),'HTTPS563_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_HTTPS_SQL26_DISPATCH_ORIGINAL_ATOMIC_CAS_AND_COLD_RECOVERY_NOT_ADMISSION_NATIVE_OR_GATE',
            actual_owned_SQL26_started=True,actual_common_dispatch_claim_lease_registered_CAS_completion=True,actual_new_result_cold_recovery=True,
            actual_SQL_counts=observation['snapshots'][0],actual_SQL_policy_counts=observation['policy_snapshots'][0],
            policy_in_original_CAS_transaction=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'HTTPS563_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        if observation is not None:row.update(database_stage=observation.get('stage'),database_error=observation.get('error_code'),
            last_probe=None if not observation['probes']else observation['probes'][-1],fresh_runtime_hash_io=observation.get('fresh_runtime_hash_io'),
            all_owned_postmasters_normal_stop=observation.get('all_owned_postmasters_normal_stop',False))
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','database_stage','database_error','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
