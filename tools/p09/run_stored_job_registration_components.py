"""Compiled SQL23 connector + model admission5 + registered service9/affected29, not actual DB."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_revision_jobs_checker_recovery as predecessor
prior=predecessor.base
harness,shared,c,a,audit,tools,compact=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools,prior.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-job-registration-components265.v1.json'
DRIVER='tools/p09/run_stored_job_registration_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-stored-revision-jobs-sync264.v1.json'
ISSUER='crates/revision-service/src/postgres/source_formula_policy/issuer_registry.rs'
CONNECTOR=ISSUER[:-3]+'/stored_revision_jobs.rs'
ADMISSION=CONNECTOR[:-3]+'/admission.rs'
TYPES=CONNECTOR[:-3]+'/types.rs'
ADAPTER=prior.base.ADAPTER
CHILD=ADAPTER[:-3]+'/registered.rs'
PARENT=prior.base.PARENT
TEST='crates/product-cli/tests/support/stored_registered_commit.rs'
TEST_CHILD='#[path="support/stored_registered_commit.rs"] mod registered_v1;\n'
SCRATCH='target/p09-stored-job-registration-scratch-265'
NEW={DRIVER,CONNECTOR,ADMISSION,TYPES,CHILD,TEST}
CHANGED={ISSUER,ADAPTER,PARENT}
PREFIX='postgres::source_formula_policy::issuer_registry::stored_revision_jobs::admission::tests::'


def migration_inputs(check):
    paths=sorted((c.ROOT/'migrations/postgres').glob('*.up.sql'));check(force=True)
    c.require(len(paths)==23 and [p.name[:4]for p in paths]==[f'{i:04}'for i in range(1,24)],'EXACT23_COMPILED_MIGRATION_INPUTS_NO_FUTURE_SCHEMA')
    return {p.relative_to(c.ROOT).as_posix()for p in paths}


def inventory(check):return prior.inventory(check)|NEW|CHANGED|migration_inputs(check)|{
    predecessor.DRIVER,predecessor.origin.DRIVER,'tools/p09/run_stored_revision_jobs_sync.py','protocol/migrations/p09-stored-revision-jobs-v1.md'}


def inverse(q,old):
    text=q.text(ISSUER);marker='pub mod stored_revision_jobs;\n';c.require(text.count(marker)==1,'ONE_SEPARATE_SQL23_MODULE_NO_SCHEMA22_CONSTRUCTOR_CHANGE')
    audit.inverse(text.replace(marker,''),old[ISSUER],'ENTIRE_SQL22_CONNECTOR_ADMISSION_READERS_WRITERS_AND_TESTS_UNCHANGED')
    text=q.text(ADAPTER)
    markers=['mod registered;\n',
        'use revision_service::postgres::source_formula_policy::issuer_registry::stored_revision_jobs::{\n    StoredJobLease,StoredCommitIntentRecord,StoredRevisionJobRepository,\n};\n',
        "    job_registration: Option<(&'a dyn StoredRevisionJobRepository,StoredJobLease)>,\n    registered_job_intent: Option<StoredCommitIntentRecord>,\n",
        '            .field("job_registered", &self.registered_job_intent.is_some())\n',
        '            job_registration: None, registered_job_intent: None,\n',
        '    #[must_use]\n    pub const fn registered_job_intent(&self) -> Option<&StoredCommitIntentRecord> { self.registered_job_intent.as_ref() }\n',
        '        self.register_job_intent(&service_request)?;\n']
    for marker in markers:c.require(text.count(marker)==1,'EXACT_TYPED_REGISTRATION_ADDITIONS');text=text.replace(marker,'')
    audit.inverse(text,old[ADAPTER],'PRIOR_SOURCE_ACL_AEAD_PRECOMMIT_INTENT_CAS_UNKNOWN_RECOVERY_AND_PLAIN_BIND_BEHAVIOR_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(TEST_CHILD)and text.count(TEST_CHILD)==1,'ONE_NEW_REGISTERED_TEST_CHILD')
    audit.inverse(text[:-len(TEST_CHILD)],old[PARENT],'ALL29_ORIGINAL_TEST_BODIES_AND_FIXTURE_SCANNERS_UNMODIFIED')
    text=q.text(CHILD)
    for marker in('revisions.repository(),lease','repository.register_commit_intent','record.validate_for','RevisionError::CommitOutcomeUnknown'):
        c.require(marker in text,'SAME_REPOSITORY_REGISTRATION_AND_TYPED_RECORD_VALIDATION_BEFORE_CAS')
    for path in(CONNECTOR,ADMISSION,TYPES,CHILD):
        text=q.text(path);c.require(all(x not in text for x in('std::process','SignatureVerified','NoTls).unwrap','CREATE ROLE','ALTER ROLE','GRANT EXECUTE')),
            'NO_NATIVE_TRUST_ISSUANCE_OR_AUTOMATIC_DATABASE_GRANTS')
    text=q.text(ADMISSION)
    for marker in('LIMIT 24','rows.len()!=23','row.1!=NAMES[i]','ContentDigest::of(migration'[:-9],
        'has_any_column_privilege','p.prosrc','no_public','revision_commit_receipts_stored_intent_guard','schema_versions'):
        c.require(marker in text,'EXACT_SCHEMA_SOURCE_ROLE_COLUMN_PRIVILEGE_FUNCTION_BODY_AND_TRIGGER_CHECKS')


def names(q,path):return re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGISTRATION_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_JOB_REGISTRATION_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,in_memory_repositories=True,
        model_SQL23_admission_only=True,model_registry_not_SQL_authority=True,manifest_scanner_and_validator_synthetic=True,
        ArtifactService_SQL23_connector_not_implemented=True,full_claim_lease_complete_coordinator_not_connected=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(predecessor.OUTPUT));docs=q.json(DOC_BASE)
        c.require(q.snapshots[predecessor.OUTPUT]['sha256']=='e6144affdc1e37d38e23bc64046981ec4984c0bdb5ead262e42a5a245bb6bb1c'
            and passed['cleanup']and passed['total_executed_cases']==29 and passed['fresh_inputs']==passed['final_fresh_hashes']==872,'EXACT263_RUST29_AND_SOURCE_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='78a75141ba6c7ce3d4a09407626843451edc01b985bf6c00d4902c4617edae10'and docs['cleanup'],'EXACT264_SELECTED_SOURCE_DOC_CLOSURE')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(NEW|CHANGED):q.pin(name)
        inverse(q,old)
        migrations=migration_inputs(guard.check);new_migrations=[]
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name))
                if pin is None:
                    c.require(name in migrations and name!='migrations/postgres/0023_p09_stored_revision_jobs.up.sql','ONLY_NEWLY_SCOPED_EXISTING_COMPILED_MIGRATIONS_ALLOWED')
                    new_migrations.append(q.snapshots[name])
                else:c.require(q.snapshots[name]==pin,'ALL_OTHER_PRODUCT_SQL23_MIGRATIONS_NATIVE_ROUTES_AND_TEST_INPUTS_UNCHANGED')
        row['newly_scoped_existing_compilation_migrations']=new_migrations
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        models={PREFIX+n for n in names(q,ADMISSION)}
        product=set(names(q,PARENT))|{'recovery_v1::'+n for n in names(q,prior.RECOVERY_TEST)}|{'precommit_v1::'+n for n in names(q,prior.TEST)}|{'registered_v1::'+n for n in names(q,TEST)}
        c.require(len(models)==5 and len(product)==38 and len(names(q,TEST))==9,'EXACT5_ADMISSION_MODELS9_REGISTERED_AND29_AFFECTED_CASES')
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_OWNED_REGISTRATION_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='REGISTERED_JOB_PREFLIGHT',inputs=len(q.snapshots),all23_migration_inputs=True,models5_registered9_affected29=True,actual_DB=False)),flush=True)
        for stage,package,target,selectors,cases in[
            ('schema23_admission_model5','revision-service',['--lib'],[*sorted(models),'--exact'],models),
            ('registered9_and_affected29','hwpx-agent-cli',['--test','stored_revision_commit'],[],product)]:
            harness.run_one(stage,[harness.CARGO,'test','--offline','--locked','-j','1','-p',package,*target,'--message-format=short','--',*selectors,'--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_REGISTERED_JOB_TEST_TEMP_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_COMPILED_SCHEMA23_CONNECTOR_MODELS5_REGISTERED9_AFFECTED29_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=43,new_cases=14,affected_cases=29,
            all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='ArtifactService_exact_schema23_profile_and_typed_claim_lease_complete_then_owned_DB_runtime_restart_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGISTRATION_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGISTRATION_COMPONENT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
