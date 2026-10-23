"""Immutable service intent + read-only sealed commit observation; no DB restart/Native claim."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_revision_commit_recovery as base
harness,shared,c,a,audit,tools,compact=base.harness,base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-commit-intent-components259.v1.json'
DRIVER='tools/p09/run_stored_commit_intent_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-stored-revision-commit-sync-recovery258.v1.json'
ADAPTER=base.base.ADAPTER
PARENT=base.base.SERVICE_TEST
REV_LIB='crates/revision-service/src/lib.rs'
RECON='crates/revision-service/src/reconciliation.rs'
INTENT='crates/product-cli/src/stored_revision_commit/intent.rs'
TEST='crates/product-cli/tests/support/stored_commit_recovery.rs'
SCRATCH='target/p09-stored-commit-intent-scratch-259'
NEW={DRIVER,RECON,INTENT,TEST}
CHANGED={ADAPTER,PARENT,REV_LIB}
CHILD='#[path="support/stored_commit_recovery.rs"] mod recovery_v1;\n'


def inventory(check):return base.inventory(check)|NEW|CHANGED|{'tools/p09/run_stored_revision_commit_sync.py',
    'tools/p09/run_stored_revision_commit_sync_recovery.py','protocol/migrations/p09-stored-revision-cas-v1.md'}


def inverse(q,old):
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_RECOVERY_TEST_CHILD_ONLY')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL13_PRIOR_SERVICE_TEST_BODIES_UNCHANGED')
    text=q.text(REV_LIB);marker='mod reconciliation;\npub use reconciliation::CommitObservation;\n'
    c.require(text.count(marker)==1,'ONE_ADDITIVE_READONLY_REVISION_MODULE');audit.inverse(text.replace(marker,''),old[REV_LIB],'OLD_REVISION_EXPORTS_UNCHANGED')
    text=q.text(ADAPTER)
    after='''//! output digest for reconciliation. The immutable intent is stored before CAS; a durable
//! job must retain its identity. This adapter is single-use, not complete durable idempotency.
mod intent;
pub use intent::{RecoveredResult, StoredCommitRecoveryBinding, StoredCommitRecoveryOutcome, reconcile_stored_commit};
'''
    before='//! output digest for reconciliation. This adapter is single-use, not durable idempotency.\n'
    c.require(text.count(after)==1,'ADAPTER_SCOPE_AND_PRIVATE_INTENT_CHILD');text=text.replace(after,before)
    markers=[
        '    retained_intent: Option<ArtifactDescriptor>,\n    intent_sha256: Option<ContentDigest>,\n',
        '            .field("intent_retained", &self.retained_intent.is_some())\n',
        '    #[must_use]\n    pub const fn retained_intent(&self) -> Option<&ArtifactDescriptor> { self.retained_intent.as_ref() }\n    #[must_use]\n    pub const fn intent_sha256(&self) -> Option<ContentDigest> { self.intent_sha256 }\n',
        '''        self.persist_intent(&service_request)?;
        // Intent storage itself crosses service boundaries: recheck before the only CAS.
        if self.fresh_source()? != source { return Err(StoredCommitError::Source); }
        let final_result = self.artifacts.get_descriptor(self.context, result.artifact_id, (self.clock)())
            .map_err(|_| StoredCommitError::Artifact)?;
        if !available(&final_result) || final_result.sha256 != result.sha256 || final_result.size_bytes != result.size_bytes {
            return Err(StoredCommitError::Artifact);
        }
''',
    ]
    for marker in markers:
        c.require(text.count(marker)==1,'EXACT_INTENT_STORAGE_AND_POST_INTENT_CURRENT_SOURCE_RESULT_CHECKS');text=text.replace(marker,'')
    after='retained_result: None, retained_intent: None, intent_sha256: None, service_request: None'
    c.require(text.count(after)==1,'EXACT_INITIAL_EMPTY_RECOVERY_IDENTITIES');text=text.replace(after,'retained_result: None, service_request: None')
    audit.inverse(text,old[ADAPTER],'PRIOR_SERVICE_BINDING_SOURCE_AEAD_INGEST_CAS_UNKNOWN_RECOVERY_AND_NO_DELETE_LOGIC_UNCHANGED')
    for path in(RECON,INTENT):
        value=q.text(path)
        c.require(all(marker not in value for marker in('std::process','SignatureVerified','SecurityModify','.quarantine(','.remove(','.delete(')),
            'NO_NATIVE_TRUST_GRANT_OR_SHARED_ARTIFACT_DESTRUCTION')
    reconcile=q.text(INTENT).split('pub fn reconcile_stored_commit',1)[1]
    c.require(all(marker not in reconcile for marker in('.commit(','.ingest(','.compare_and_swap(')), 'RECOVERY_IS_READONLY_NEVER_BLIND_RETRY')
    c.require('.commit('not in q.text(RECON)and 'RevisionNode::sealed_from(request'in q.text(RECON),'EXACT_ALL_FIELD_SEALED_NODE_COMPARISON_NO_WRITE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_INTENT_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_COMMIT_INTENT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,durable_idempotency_complete=False,
        actual_PostgreSQL_or_process_restart=False,actual_ArtifactService_and_RevisionService_code=True,
        in_memory_repositories=True,manifest_scanner_and_validator_synthetic=True,scratch_parent=SCRATCH,
        persistent_job_handle_registration_not_connected=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(base.OUTPUT));docs=q.json(DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='288d3306b6ec71d3040528d7a619a901a4e33c276671b4a0d09c3264d16bcd56'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==852 and previous['total_executed_cases']==13,'EXACT256_ACTUAL_SERVICE13_AND_SOURCE_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='f782542be153960bb40253165c0ebce577bce5cabe9a323a76dfa3d9129a8130'
            and docs['cleanup'],'EXACT258_SELECTED_SOURCE_DOC_CLOSURE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SERVICES_POSTGRES_SCHEMA_NATIVE_GUARDS_AND_ENGINE_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old)
        names=lambda path:re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
        prior=set(names(PARENT));new={'recovery_v1::'+name for name in names(TEST)};cases=prior|new
        c.require(len(prior)==13 and len(new)==12 and len(cases)==25,'EXACT13_AFFECTED12_NEW_INTENT_RECOVERY_CASES')
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_OWNED_INTENT_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='STORED_INTENT_PREFLIGHT',inputs=len(q.snapshots),new12_affected13=True,engine26_and_official249_reexecuted=False)),flush=True)
        harness.run_one('intent_recovery12_and_affected_storage13',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','stored_revision_commit','--message-format=short','--','--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_INTENT_TEST_TEMP_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_IMMUTABLE_COMMIT_INTENT_READONLY_RECOVERY12_AFFECTED_STORAGE13_NOT_DB_RESTART_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=25,new_cases=12,affected_cases=13,
            all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='durable_job_intent_handle_join_and_existing_v2_idempotency_authority_then_owned_DB_restart_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_INTENT_COMPONENTS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INTENT_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
