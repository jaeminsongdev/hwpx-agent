"""Compare the verified native binaries in a fresh ASCII-only owned directory, preserving failures."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_native_postgres_cluster_qualification as origin
shared,c,a,tools,compact=origin.shared,origin.c,origin.a,origin.tools,origin.compact
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-ascii-campaign282.v1.json'
DRIVER='tools/p09/run_native_postgres_ascii_campaign.py'
WORKER='tools/p09/native_postgres_ascii_campaign.py'
DIAGNOSTIC='implementation/p09/evidence/p09-361-native-postgres-init-diagnostic281.v1.json'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PG_ASCII_CAMPAIGN_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NATIVE_POSTGRES_ASCII_CAMPAIGN',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_owned_postmaster_started=False,actual_SQL23_applied_in_owned_test_database=False,actual_application_role_admission_or_job_functions=False,
        actual_P09_product_or_Native_execution=False,actual_Docker_WSL_or_service_started=False,system_or_security_settings_changed=False,
        model10_reused=True,original_binary_archive_and_failed_data_preserved=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);diagnostic=compact.unpack(q.json(DIAGNOSTIC))
        c.require(q.snapshots[DIAGNOSTIC]['sha256']=='b83019bfbcd0a6ae4bdaabb866f7455bb6a968c45af1c335effa150ea999f314'
            and diagnostic['cleanup']and diagnostic['model10_reused']and diagnostic['diagnostic_result']['initdb_exit_code']==1
            and 'invalid byte sequence'in diagnostic['diagnostic_result']['diagnostics']['first_error_sanitized'],'EXACT281_UTF8_INITDB_FAILURE_NO_POSTMASTER_OR_MIGRATION')
        old={p['path']:p for p in diagnostic['source_pins']}
        for path,pin in old.items():q.pin(path);c.require(q.snapshots[path]==pin,'ALL_PREVIOUS_VERIFIED_BINARIES_MODELS_SQL_AND_GUARD_SOURCES_UNCHANGED')
        for path in(DRIVER,WORKER):q.pin(path)
        import native_postgres_ascii_campaign as candidate
        c.require(str(candidate.OWNED).isascii()and candidate.OWNED.parent==candidate.PARENT and candidate.PARENT.is_dir()
            and not candidate.PARENT.is_symlink()and not candidate.PARENT.is_junction()and not candidate.OWNED.exists(),'FRESH_ASCII_DEVDATA_OWNER_SCOPE')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        env=dict(os.environ,PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        result=origin.runner.run_owned('owned_ascii_pg18_6_migration23_restart',[sys.executable,str(c.ROOT/WORKER),'--owned-ascii-migration23-and-restart'],guard,env,row,300)
        c.require(result['state']=='PASS_ASCII_OWNED_PG18_6_MIGRATIONS23_CATALOGUE_RESTART_NOT_APPLICATION_JOB_OR_PRODUCT'
            and result['initdb_ascii_succeeded']and result['migrations_applied']==list(range(1,24))and result['normal_restart_verified']
            and len(result['cluster_attestations'])==2 and len(result['postmasters'])==2 and result['all_owned_postmasters_normal_stop']
            and result['runtime_files_copied']==1583 and result['runtime_bytes_copied']==147885345 and result['original_runtime_and_failures_preserved']
            and result['actual_application_role_admission_or_job_functions']is False,'ASCII_IDENTICAL_RUNTIME_INITDB23_CATALOGUE_AND_DURABLE_RESTART_SCOPE')
        for pin in result['migration_inputs']:c.require(q.snapshots[pin['path']]==pin,'EXACT_UNCHANGED_SQL_BYTES_APPLIED_IN_OWNED_ASCII_DATABASE')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ASCII_OWNED_PG18_6_SQL23_CATALOGUE_RESTART_NOT_APP_JOB_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_database_root=result['database_root'],clean_restart_verified=True,previous_Rust249_or_model10_reexecuted=0,
            next_work='actual_ArtifactService_RevisionService_SQL23_role_admission_worker_and_registered_job_CAS_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PG_ASCII_QUALIFICATION_FAILURE_NO_RAW_VALUES')
    finally:
        for step in row['steps']:
            result=step.get('result',{});row['actual_owned_postmaster_started']=result.get('actual_owned_postmaster_started',False)
            row['actual_SQL23_applied_in_owned_test_database']=result.get('actual_SQL23_applied_in_owned_test_database',False)
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'LOSSLESS_ASCII_NATIVE_CLUSTER_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_owned_postmaster_started','actual_SQL23_applied_in_owned_test_database')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),result={k:s.get('result',{}).get(k)for k in('state','stage','initdb_ascii_succeeded','error_type','error_code','migrations_applied','normal_restart_verified')},
                last_command=s.get('result',{}).get('commands',[None])[-1],cleanup=s['cleanup'])for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
