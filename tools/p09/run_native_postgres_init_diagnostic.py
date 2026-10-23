"""Reuse unchanged280 model10; one fresh reject-auth initdb and bounded sanitized error evidence."""
import json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_native_postgres_cluster_qualification as origin
shared,c,a,tools,compact=origin.shared,origin.c,origin.a,origin.tools,origin.compact
OUTPUT='implementation/p09/evidence/p09-361-native-postgres-init-diagnostic281.v1.json'
DRIVER='tools/p09/run_native_postgres_init_diagnostic.py'
WORKER='tools/p09/native_postgres_init_diagnostic.py'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PG_INIT_DIAGNOSTIC_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NATIVE_PG_INIT_DIAGNOSTIC',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_postmaster_or_migration_or_password=False,actual_cases_reexecuted=0,model10_reused=False,raw_logs_retained=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(origin.OUTPUT))
        c.require(q.snapshots[origin.OUTPUT]['sha256']=='359ca1846f619fddb19ff9a4960899d4dbdd504ede8d53daca985534b5d78d05'
            and previous['cleanup']and previous['steps'][0]['result']==dict(state='PASS_NATIVE_PG_CLUSTER_MODELS10',tests_run=10,failures=[],actual_database=False)
            and previous['steps'][1]['result']['stage']=='initialize_new_reject_auth_cluster','ORIGINAL280_INITDB_FAILURE_AND_MODEL10_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        for path,pin in old.items():q.pin(path);c.require(q.snapshots[path]==pin,'ALL280_RUNTIME_CLUSTER_MODELS_MIGRATIONS_AND_RESOURCE_INPUTS_UNCHANGED')
        for path in(DRIVER,WORKER):q.pin(path)
        import native_postgres_init_diagnostic as diagnostic
        for message in('initdb: error: could not open file "D:/private path/key"\nmore details','FATAL: invalid value for parameter \'private-marker\''):
            value=diagnostic.safe_init_error(message);c.require('private'not in json.dumps(value)and'more details'not in json.dumps(value),'SANITIZED_INIT_ERROR_NEVER_EMITS_QUOTED_VALUES_OR_FULL_LOG')
        row['model10_reused']=True
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        environment=dict(os.environ,PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        result=origin.runner.run_owned('one_fresh_initdb_diagnostic',[sys.executable,str(c.ROOT/WORKER),'--new-reject-initdb-only'],guard,environment,row,90)
        c.require(result['state']=='OBSERVED_NEW_INITDB_RESULT_NOT_DATABASE_QUALIFICATION'and result['actual_postmaster_or_migration_or_password']is False
            and result['raw_logs_retained']is False,'INITDB_DIAGNOSTIC_ONLY_NO_PASSWORD_SERVER_OR_MIGRATION')
        q.finish();guard.check(force=True)
        row.update(state='PASS_OBSERVED_NEW_INITDB_DIAGNOSTIC_NOT_POSTMASTER_SQL23_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            diagnostic_result=result,next_work='resolve_exact_initdb_failure_without_relaxing_owned_Job_or_security_policy')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PG_INIT_DIAGNOSTIC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'LOSSLESS_PG_INIT_DIAGNOSTIC_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','diagnostic_result')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
