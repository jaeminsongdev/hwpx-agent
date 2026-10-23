"""Actual service ingest/CAS on synthetic storage fixtures, never P09/Native qualification."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_transaction_bytes_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
compact=base.base.base.prior.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-commit-components255.v1.json'
DRIVER='tools/p09/run_stored_revision_commit_components.py'
MODEL='crates/operation-engine/src/transaction.rs'
PARENT='crates/operation-engine/tests/workspace_transaction.rs'
LIB='crates/product-cli/src/lib.rs'
ADAPTER='crates/product-cli/src/stored_revision_commit.rs'
ENGINE_TEST='crates/operation-engine/tests/support/unknown_cas_transaction.rs'
SERVICE_TEST='crates/product-cli/tests/stored_revision_commit.rs'
FIXTURE='crates/product-cli/tests/support/stored_commit_manifest.rs'
DOC_BASE='implementation/p09/evidence/p09-361-transaction-bytes-sync254.v1.json'
SCRATCH='target/p09-stored-revision-commit-scratch-255'
NEW={DRIVER,ADAPTER,ENGINE_TEST,SERVICE_TEST,FIXTURE}
CHANGED={MODEL,PARENT,LIB}
CHILD='#[path="support/unknown_cas_transaction.rs"]mod unknown_cas;\n'


def inventory(check):return base.inventory(check)|NEW|CHANGED|{'tools/p09/run_transaction_bytes_sync.py','protocol/migrations/p09-transaction-byte-source-v1.md'}


def names(q,path):return re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))


def inverse(q,old):
    text=q.text(MODEL)
    markers=[
        '    /// The commit may have happened. Preserve artifacts; reconcile instead of retrying.\n    Unknown,\n',
        '    #[must_use]\n    pub const fn source_artifact_id(&self) -> &ArtifactId {\n        &self.source_artifact_id\n    }\n\n    #[must_use]\n    pub const fn manifest_sha256(&self) -> [u8; 32] {\n        self.manifest_sha256\n    }\n\n',
        '    #[error("workspace transaction revision commit outcome is unknown; reconciliation required")]\n    RevisionOutcomeUnknown,\n',
        '            Self::RevisionOutcomeUnknown => "workspace_transaction_revision_outcome_unknown",\n',
        '            RevisionCasOutcome::Unknown => {\n                self.machine.mark_recovery(TransactionState::Incomplete);\n                self.artifact_disposition = ArtifactDisposition::CommittedOutcomeUncertain;\n                return Err(TransactionError::RevisionOutcomeUnknown);\n            }\n',
    ]
    for marker in markers:
        c.require(text.count(marker)==1,'EXACT_UNKNOWN_ADDITIONS_AND_READONLY_ENGINE_BINDING_GETTERS');text=text.replace(marker,'')
    audit.inverse(text,old[MODEL],'PRIOR_SOURCE_FILE_BYTES_INTEGRITY_STATES_CAS_FAILURE_AND_FAULT_PIPELINE_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_UNKNOWN_TEST_CHILD_ONLY')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL23_EXISTING_TRANSACTION_TESTS_UNMODIFIED')
    text=q.text(LIB);marker='pub mod stored_revision_commit;\n';c.require(text.count(marker)==1,'ONE_STORAGE_PRIMITIVE_MODULE_NO_EXECUTION_ROUTE')
    audit.inverse(text.replace(marker,''),old[LIB],'EXISTING_PRODUCT_CLI_AND_EXECUTION_ROUTES_UNCHANGED')
    text=q.text(ADAPTER)
    for marker in('self.fresh_source()?','self.artifacts.ingest','self.artifacts.download','self.revisions.commit',
        'Err(RevisionError::CommitOutcomeUnknown)','self.retained_result = Some(result.clone())','self.service_request = Some(service_request.clone())',
        'self.service_receipt = Some(receipt)','request.manifest_sha256()','request.source_artifact_id()',
        'AuthScope::DocumentWrite','FnMut() -> u64','MAX_BYTES: u64 = 32 * 1024 * 1024'):
        c.require(marker in text,'ACTUAL_BOUND_SERVICE_OPERATIONS_AND_RECOVERY_IDENTITIES')
    c.require(all(x not in text for x in('std::process','std::fs','SignatureVerified','SecurityModify','.quarantine(','.remove(','.delete(')),
        'NO_NATIVE_RAW_ROUTE_FS_WRITE_SECURITY_GRANT_OR_SHARED_ARTIFACT_DESTRUCTION')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_REVISION_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVISION_COMMIT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,durable_database_or_idempotency_qualified=False,
        actual_ArtifactService_and_RevisionService_code=True,in_memory_repositories=True,manifest_scanner_and_validator_synthetic=True,
        service_artifact_and_revision_CAS_not_distributed_atomic=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(base.OUTPUT));docs=q.json(DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='77d9c82ec55f7537e85abe637cab3b54ead17d846ee0762500e0e487e77eb79c'
            and previous['cleanup']and previous['total_executed_cases']==23,'EXACT253_BYTE_FILE_TRANSACTION_AND_INTEGRITY_LINEAGE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='fe7099ccd1a7b5844a0f69b6e0699a965fceae56f698581a43433e0faa45a26e'and docs['cleanup'],'EXACT254_DOC_LINEAGE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SERVICES_NATIVE_ROUTES_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old)
        engine=set(names(q,PARENT))|{'bytes_v1::'+n for n in names(q,base.base.base.TEST)}|{'unknown_cas::'+n for n in names(q,ENGINE_TEST)}
        service=set(names(q,SERVICE_TEST))
        c.require(len(engine)==26 and len(service)==13,'EXACT23_AFFECTED3_NEW_ENGINE13_SERVICE_TESTS')
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_OWNED_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='STORED_REVISION_PREFLIGHT',inputs=len(q.snapshots),engine26_service13=True,official249_reexecuted=False)),flush=True)
        for stage,package,test,cases in [('engine_unknown3_and_affected23','operation-engine','workspace_transaction',engine),
            ('actual_services_on_synthetic_storage_fixture13','hwpx-agent-cli','stored_revision_commit',service)]:
            harness.run_one(stage,[harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',test,'--message-format=short','--','--test-threads=1'],
                cases,guard,environment,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_OWNED_SERVICE_TEST_TEMP_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_STORAGE_SERVICE_CAS13_UNKNOWN_ENGINE3_AFFECTED23_NOT_P09_EXECUTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=39,new_cases=16,affected_cases=23,
            all_previous_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='durable_reconciliation_and_idempotency_and_current_P09_qualified_execution_path_NOT_component_promotion')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVISION_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORAGE_SERVICE_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
