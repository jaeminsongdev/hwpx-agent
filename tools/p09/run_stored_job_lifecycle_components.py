"""SQL23 typed lifecycle15 models; preserves all previous SQL/service/engine evidence."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_artifact23_precommit_plan_components as predecessor
core=predecessor.core
harness,shared,c,a,audit,tools,compact=core.harness,core.shared,core.c,core.a,core.audit,core.tools,core.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-lifecycle-components271.v1.json'
DRIVER='tools/p09/run_stored_job_lifecycle_components.py'
ROOT='crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs.rs'
LIFE=ROOT[:-3]+'/lifecycle.rs'
SQL=LIFE[:-3]+'/sql.rs'
TEST=LIFE[:-3]+'/tests.rs'
SCRATCH='target/p09-stored-job-lifecycle-scratch-271'
NEW={DRIVER,LIFE,SQL,TEST}
PREFIX='postgres::source_formula_policy::issuer_registry::stored_revision_jobs::lifecycle::'

def inventory(check):return predecessor.inventory(check)|NEW|{predecessor.DRIVER}

def inverse(q,old):
    text=q.text(ROOT)
    for marker in('pub mod lifecycle;\n','        lifecycle::admit_controls(&mut client)?;\n'):
        c.require(text.count(marker)==1,'EXACT_TYPED_LIFECYCLE_MODULE_AND_EXTRA_CONTROL_ADMISSION');text=text.replace(marker,'')
    audit.inverse(text,old[ROOT],'ALL_EXISTING_SQL23_SCHEMA_ADMISSION_SOURCE_CAS_REGISTRATION_READ_AND_LEASE_BINDING_UNCHANGED')
    for path in(LIFE,SQL):
        text=q.text(path)
        for forbidden in('std::process','CREATE ROLE','ALTER ROLE','GRANT EXECUTE','DROP SCHEMA','std::thread','loop {','no_effect','claim_idempotent_job_v2('):
            c.require(forbidden not in text,'NO_NATIVE_GRANT_INSTALL_AUTO_RETRY_OR_NO_EFFECT_AUTHORITY')
    text=q.text(SQL)
    for marker in('self.inner.scoped','self.authorize_context','tx.query_one','r.expect','admit_controls','control_security','MIGRATIONS[6]','returned_commit_authorization_id'):
        c.require(marker in text,'SCOPED_SQL_TRANSACTIONS_EXACT_TYPED_RESPONSES_AND_FROZEN_CONTROL_ADMISSION')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LIFECYCLE_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_JOB_LIFECYCLE_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,lifecycle_models_not_SQL_authority=True,
        expected_precommit_to_full_execution_coordinator_not_connected=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target';c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
            and not scratch.exists()and scratch.resolve().is_relative_to(parent.resolve()),'EARLY_UNIQUE271_OWNED_TEMP_PARENT_ONLY')
        previous=compact.unpack(q.json(predecessor.OUTPUT))
        c.require(q.snapshots[predecessor.OUTPUT]['sha256']=='32c22842f7f39818cc863cfdff99be65bac269ef51381bec7c48b75e65678221'
            and previous['cleanup']and previous['total_executed_cases']==41 and previous['fresh_inputs']==previous['final_fresh_hashes'],'EXACT270_COMPONENT41_TERMINAL_SOURCE_CLOSURE')
        old={p['path']:p for p in previous['source_pins']}
        for name in sorted(NEW|{ROOT}):q.pin(name)
        inverse(q,old)
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|{ROOT}:c.require(q.snapshots[name]==old[name],'ALL_OTHER23_MIGRATIONS_SERVICES_ROUTES_NATIVE_AND_PRIOR_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        cases={PREFIX+'tests::'+n for n in predecessor.names(q,TEST)}|{PREFIX+'sql::tests::'+n for n in predecessor.names(q,SQL)}
        c.require(len(cases)==15,'EXACT_LIFECYCLE_MODEL15')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=core.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='LIFECYCLE_PREFLIGHT',inputs=len(q.snapshots),new_models15=True,actual_DB=False)),flush=True)
        harness.run_one('typed_lifecycle15',[harness.CARGO,'test','--offline','--locked','-j','1','-p','revision-service','--lib',
            '--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'LIFECYCLE_TEST_SCRATCH_EMPTY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_TYPED_SQL23_LIFECYCLE15_NOT_SQL_RUNTIME_P09_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            total_executed_cases=15,new_cases=15,all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='expected_precommit_bound_one_shot_coordinator_then_owned_SQL23_runtime_restart_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LIFECYCLE_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LIFECYCLE_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
