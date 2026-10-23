"""Artifact SQL23 model6 + pure expected precommit9/affected engine26, no DB or target claim."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_job_registration_confirmed as predecessor
core=predecessor.base
harness,shared,c,a,audit,tools,compact=core.harness,core.shared,core.c,core.a,core.audit,core.tools,core.compact
OUTPUT='implementation/p09/evidence/p09-361-artifact23-precommit-plan-components270.v1.json'
DRIVER='tools/p09/run_artifact23_precommit_plan_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-stored-job-registration-sync269.v1.json'
ART_ROOT='crates/artifact-service/src/store/postgres_repository.rs'
ART='crates/artifact-service/src/store/postgres_repository/schema23.rs'
MODEL='crates/operation-engine/src/transaction.rs'
LIB='crates/operation-engine/src/lib.rs'
PREPARE='crates/operation-engine/src/transaction/precommit.rs'
PARENT='crates/operation-engine/tests/workspace_transaction.rs'
TEST='crates/operation-engine/tests/support/prepared_precommit.rs'
SCRATCH='target/p09-artifact23-precommit-plan-scratch-270'
NEW={DRIVER,ART,PREPARE,TEST}
CHANGED={ART_ROOT,MODEL,LIB,PARENT}
TEST_CHILD='#[path="support/prepared_precommit.rs"]mod prepared_precommit;\n'
PREFIX='store::postgres_repository::schema23::tests::'


def inventory(check):return predecessor.inventory(check)|NEW|CHANGED|{
    'tools/p09/run_stored_job_registration_sync.py'}


def names(q,path):return re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))


def inverse(q,old):
    text=q.text(ART_ROOT);marker='pub mod schema23;\n';c.require(text.count(marker)==1,'ONE_SEPARATE_ARTIFACT_SCHEMA23_MODULE')
    audit.inverse(text.replace(marker,''),old[ART_ROOT],'ALL_EXISTING_ARTIFACT_CONNECTION_ROLE_RLS_STORAGE_AUDIT_AND_PRIVILEGE_LOGIC_UNCHANGED')
    text=q.text(LIB);marker='    PreparedPrecommitIdentity,\n';c.require(text.count(marker)==1,'ONE_EXPECTED_IDENTITY_EXPORT')
    audit.inverse(text.replace(marker,''),old[LIB],'ALL_EXISTING_ENGINE_EXPORTS_UNCHANGED')
    text=q.text(MODEL);marker='mod precommit;\npub use precommit::PreparedPrecommitIdentity;\n';c.require(text.count(marker)==1,'ONE_PRIVATE_PLANNING_MODULE')
    text=text.replace(marker,'')
    after='        RevisionCommitRequest::from_manifest_result(&self.manifest,self.manifest_sha256,result_sha256,result_size)\n'
    before='''        let result_artifact_id = artifact_id(result_sha256)?;
        Ok(RevisionCommitRequest {
            transaction_id: self.manifest.transaction_id().clone(),
            base_revision: self.manifest.base_revision().clone(),
            source_artifact_id: self.manifest.source_artifact_id().clone(),
            result_artifact_id,
            manifest_sha256: self.manifest_sha256,
            result_sha256,
            result_size,
        })
'''
    c.require(text.count(after)==1,'ONE_SHARED_PRECOMMIT_IDENTITY_CONSTRUCTOR')
    audit.inverse(text.replace(after,before),old[MODEL],'ALL_SOURCE_FILE_BYTES_VALIDATOR_PUBLICATION_INTEGRITY_CAS_UNKNOWN_FAULT_AND_RECOVERY_PIPELINE_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(TEST_CHILD)and text.count(TEST_CHILD)==1,'ONE_NEW_PREPARED_IDENTITY_TEST_CHILD')
    audit.inverse(text[:-len(TEST_CHILD)],old[PARENT],'ALL26_EXISTING_TRANSACTION_TEST_BODIES_UNCHANGED')
    text=q.text(PREPARE)
    for marker in('struct PreparedPrecommitIdentity{expected:RevisionCommitRequest}','#[derive(Clone,Eq,PartialEq)]',
        'pub(super) fn from_manifest_result','limits.validate()?','size>limits.max_output_bytes','self.expected==*actual'):
        c.require(marker in text,'BOUNDED_EXPECTED_IDENTITY_AND_SEALED_ACTUAL_REQUEST_REMAIN_DISTINCT')
    for marker in('std::fs','fs::','std::process','pub fn canonical_json','pub fn into_','impl From','impl std::ops::Deref','Serialize,Deserialize','ValidationOutcome::Valid'):
        c.require(marker not in text,'NO_FS_EXECUTION_VALIDATION_AUTHORITY_SERIALIZATION_OR_ACTUAL_REQUEST_CONVERSION')
    c.require(text.index('size>limits.max_output_bytes')<text.index('Sha256::digest(output)'),'CANDIDATE_OUTPUT_CAP_BEFORE_HASH_NO_EXTRA_OUTPUT_COPY')
    c.require('output.to_vec()'not in text and 'pub fn request('not in text,'NO_FULL_OUTPUT_CLONE_OR_SEALED_REQUEST_REFERENCE_ESCAPE')
    text=q.text(ART)
    for marker in('Self::connect_diagnosed(config,tenant)?','rows.len()!=23','row.1!=NAMES[i]','LIMIT 24','rolreplication',
        'has_any_column_privilege','stored_revision_commit_intents','has_function_privilege','reject(value(&r,"allowed")?)?'):
        c.require(marker in text,'ORIGINAL_ARTIFACT_GUARDS_WITH_EXACT23_NAMES_SHA_AND_DENIED_JOB_AUTHORITY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'ARTIFACT23_PLANNING_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_ARTIFACT23_PRECOMMIT_PLAN_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_PostgreSQL_or_process_restart=False,SQL23_applied=False,SQL23_catalog_privilege_or_runtime_qualified=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,artifact_admission_model_only=True,
        prepared_identity_not_execution_receipt_or_CAS_request=True,manifest_validator_and_CAS_synthetic=True,
        typed_claim_lease_complete_coordinator_not_connected=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target';c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()
            and not scratch.exists()and scratch.resolve().is_relative_to(parent.resolve()),'EARLY_NEW270_OWNED_TEMP_PARENT_ONLY')
        previous=compact.unpack(q.json(predecessor.OUTPUT));docs=q.json(DOC_BASE)
        c.require(q.snapshots[predecessor.OUTPUT]['sha256']=='3d106c605c830a79488bf2584704231790ec38a2ec670c109b59c8b738a9400d'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==901,'EXACT268_CONFIRMED_CALLBACK_SOURCE_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='28e2573ddba10bcd7ef4300537ec84cf621d1af36807fab5aac36e85021ca617'and docs['cleanup'],'EXACT269_SELECTED_SOURCE_AND_DOC_CLOSURE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(NEW|CHANGED):q.pin(name)
        inverse(q,old)
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SERVICE23_CALLBACK_SQL_NATIVE_ROUTES_AND_OLD_TEST_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        models={PREFIX+n for n in names(q,ART)}
        engine=set(names(q,PARENT))|{'bytes_v1::'+n for n in names(q,'crates/operation-engine/tests/support/bytes_transaction.rs')}|{
            'unknown_cas::'+n for n in names(q,'crates/operation-engine/tests/support/unknown_cas_transaction.rs')}|{'prepared_precommit::'+n for n in names(q,TEST)}
        c.require(len(models)==6 and len(engine)==35 and len(names(q,TEST))==9,'EXACT6_ARTIFACT_MODELS9_PLANNING26_AFFECTED_ENGINE')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=core.prior.base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='ARTIFACT23_PLANNING_PREFLIGHT',inputs=len(q.snapshots),models6_planning9_affected26=True,actual_DB=False)),flush=True)
        for stage,package,target,selectors,cases in[
            ('artifact_schema23_model6','artifact-service',['--lib'],[*sorted(models),'--exact'],models),
            ('prepared_identity9_and_affected_transaction26','operation-engine',['--test','workspace_transaction'],[],engine)]:
            harness.run_one(stage,[harness.CARGO,'test','--offline','--locked','-j','1','-p',package,*target,'--message-format=short','--',*selectors,'--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_ARTIFACT_PLANNING_TEMP_TEST_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ARTIFACT23_MODELS6_PREPARED_IDENTITY9_AFFECTED_ENGINE26_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=41,new_cases=15,affected_cases=26,
            all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='typed_claim_lease_complete_with_expected_precommit_identity_then_owned_SQL23_runtime_restart_campaign')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'ARTIFACT_PLANNING_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_ARTIFACT_PLANNING_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
