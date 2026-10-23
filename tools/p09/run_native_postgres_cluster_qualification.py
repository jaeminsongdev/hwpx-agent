"""New owned cluster model10 then exact SQL1..23 catalogue and clean restart; not app admission."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_native_postgres_runtime_qualification as runner
shared,c,a,tools,compact=runner.shared,runner.c,runner.a,runner.tools,runner.compact
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-cluster-qualification280.v1.json'
DRIVER='tools/p09/run_native_postgres_cluster_qualification.py'
WORKER='tools/p09/native_postgres_cluster.py'
TEST='tools/p09/tests/test_native_postgres_cluster.py'
RUNTIME='implementation/p09/evidence/p09-361-native-postgres-runtime-boundary-recovery279.v1.json'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NATIVE_PG_CLUSTER_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NATIVE_POSTGRES_CLUSTER_QUALIFICATION',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_application_role_admission_or_job_functions=False,
        actual_P09_product_or_Native_execution=False,actual_Docker_WSL_or_service_started=False,system_or_security_settings_changed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(RUNTIME))
        c.require(q.snapshots[RUNTIME]['sha256']=='cf772540317b4521d565ea3f9662e7a213f7b1e2e8d82b47194a396e3bd86682'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==156 and previous['versions_checked']==3,'EXACT279_OWNED_RUNTIME_VERSION3_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for path in(runner.WORKER,'tools/p09/owned_sql_job.py','tools/p09/bounded_process_progress.py'):
            q.pin(path);c.require(q.snapshots[path]==old[path],'RUNTIME_ACQUISITION_AND_RESOURCE_OWNERSHIP_CODE_UNCHANGED')
        import native_postgres_cluster as cluster
        for path in(DRIVER,WORKER,TEST,cluster.HBA,cluster.MANIFEST):q.pin(path)
        c.require(q.snapshots[cluster.MANIFEST]['sha256']=='f1460896778a1037ce4022d30984bbb8d0983ace215b3ef28c12119594c897ce','EXACT279_RUNTIME_FILE_MANIFEST')
        root=c.ROOT/cluster.CLUSTER;scratch=c.ROOT/'target/p09-native-postgres-cluster-model-scratch-280';parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not root.exists()and not scratch.exists()
            and root.resolve().is_relative_to(parent.resolve())and scratch.resolve().is_relative_to(parent.resolve()),'NEW280_CLUSTER_AND_MODEL_TEMP_ONLY')
        for item in cluster.migration_rows():q.pin(item['path'])
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=dict(os.environ,PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1',TEMP=str(scratch),TMP=str(scratch))
        models=runner.run_owned('owned_native_cluster_models10',[sys.executable,str(c.ROOT/TEST)],guard,env,row,60)
        c.require(models==dict(state='PASS_NATIVE_PG_CLUSTER_MODELS10',tests_run=10,failures=[],actual_database=False),'EXACT_CLUSTER10_MODELS_NO_SKIP')
        result=runner.run_owned('owned_pg18_6_migration23_catalogue_restart',[sys.executable,str(c.ROOT/WORKER),'--owned-migration23-and-restart'],guard,env,row,300)
        c.require(result['state']=='PASS_OWNED_PG18_6_MIGRATIONS23_CATALOGUE_AND_CLEAN_RESTART_NOT_APPLICATION_PRIVILEGES_OR_PRODUCT'
            and result['migrations_applied']==list(range(1,24))and result['normal_restart_verified']and len(result['cluster_attestations'])==2
            and len(result['postmasters'])==2 and result['all_owned_postmasters_normal_stop']and not result['actual_application_role_admission_or_job_functions'],'EXACT23_SQL_CATALOGUES_TWO_AUTHENTICATED_FOREGROUND_STARTS_AND_NORMAL_STOPS')
        for pin in result['migration_inputs']:c.require(q.snapshots[pin['path']]==pin,'EXACT_SQL_BYTES_APPLIED_IN_NEW_OWNED_DATABASE')
        c.require(not any(scratch.iterdir()),'CLUSTER_MODEL_TEMP_SCRATCH_EMPTY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NATIVE_PG18_6_CLUSTER_MODELS10_MIGRATIONS23_AND_RESTART_NOT_APPLICATION_JOB_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            model_cases=10,actual_database_root=cluster.CLUSTER,clean_restart_verified=True,previous_Rust_and249_cases_reexecuted=0,
            next_work='actual_ArtifactService_RevisionService_SQL23_role_admission_worker_and_registered_job_CAS_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PG_CLUSTER_QUALIFICATION_FAILURE_NO_RAW_VALUES')
    finally:
        for step in row['steps']:
            result=step.get('result',{})
            if step['stage']=='owned_pg18_6_migration23_catalogue_restart':
                row['actual_owned_postmaster_started']=result.get('actual_owned_postmaster_started',False)
                row['actual_SQL23_applied_in_owned_test_database']=result.get('actual_SQL23_applied_in_owned_test_database',False)
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'LOSSLESS_NATIVE_CLUSTER_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_owned_postmaster_started','actual_SQL23_applied_in_owned_test_database')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),result={k:s.get('result',{}).get(k)for k in('state','stage','tests_run','failures','error_type','error_code','migrations_applied','normal_restart_verified')},
                last_command=s.get('result',{}).get('commands',[None])[-1],cleanup=s['cleanup'])for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
