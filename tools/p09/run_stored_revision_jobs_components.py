"""Real receipt storage29 + static pending SQL23 source contracts; no DB/Native execution."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_commit_intent_components as base
import stored_revision_jobs_source_contract as sql_contract
harness,shared,c,a,audit,tools,compact=base.harness,base.shared,base.c,base.a,base.audit,base.tools,base.compact
OUTPUT='implementation/p09/evidence/p09-361-stored-revision-jobs-components261.v1.json'
DRIVER='tools/p09/run_stored_revision_jobs_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-stored-commit-intent-sync260.v1.json'
MODEL='crates/operation-engine/src/transaction.rs'
TEST='crates/product-cli/tests/support/stored_precommit_receipt.rs'
RECOVERY_TEST=base.TEST
SCRATCH='target/p09-stored-revision-jobs-scratch-261'
NEW={DRIVER,TEST,'tools/p09/stored_revision_jobs_source_contract.py',sql_contract.UP,sql_contract.DOWN}
CHANGED={MODEL,base.ADAPTER,base.INTENT,base.PARENT,RECOVERY_TEST}
CHILD='#[path="support/stored_precommit_receipt.rs"] mod precommit_v1;\n'


def inventory(check):return base.inventory(check)|NEW|CHANGED|{sql_contract.OLD,
    'tools/p09/run_stored_commit_intent_sync.py','protocol/migrations/p09-stored-commit-intent-v1.md'}


def inverse(q,old):
    text=q.text(MODEL)
    marker='''    /// Exact precommit receipt bytes for immutable receipt storage; does not authorize CAS.
    /// # Errors
    /// Returns the same stable serialization error as the precommit digest.
    pub fn canonical_json(&self) -> Result<Vec<u8>, TransactionError> {
        serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)
    }

'''
    c.require(text.count(marker)==1,'ONE_READONLY_PRECOMMIT_JSON_GETTER');text=text.replace(marker,'')
    after='        let bytes = self.canonical_json()?;\n';before='        let bytes = serde_json::to_vec(self).map_err(|_| TransactionError::ReceiptSerialization)?;\n'
    c.require(text.count(after)==1,'PRECOMMIT_DIGEST_SAME_SERIALIZATION');audit.inverse(text.replace(after,before),old[MODEL],'ALL_ENGINE_FILE_BYTES_INTEGRITY_CAS_UNKNOWN_STATE_FAULT_AND_CANONICAL_FIELDS_UNCHANGED')
    text=q.text(base.ADAPTER)
    markers=['    retained_precommit: Option<ArtifactDescriptor>,\n',
        '            .field("precommit_retained", &self.retained_precommit.is_some())\n',
        '    #[must_use]\n    pub const fn retained_precommit(&self) -> Option<&ArtifactDescriptor> { self.retained_precommit.as_ref() }\n',
        '        self.persist_precommit(request)?;\n']
    for marker in markers:c.require(text.count(marker)==1,'EXACT_ADDITIVE_PRECOMMIT_STORAGE_BEFORE_INTENT_AND_CAS');text=text.replace(marker,'')
    after='retained_intent: None, retained_precommit: None, intent_sha256: None'
    c.require(text.count(after)==1,'EMPTY_PRECOMMIT_INITIAL_STATE');audit.inverse(text.replace(after,'retained_intent: None, intent_sha256: None'),old[base.ADAPTER],'ALL_OLD_SERVICE_AUTH_BINDING_JOURNAL_CAS_AND_RECOVERY_LOGIC_UNCHANGED')
    text=q.text(base.INTENT);start=text.index('    pub(super) fn persist_precommit(');end=text.index('    pub(super) fn persist_intent(',start)
    audit.inverse(text[:start]+text[end:],old[base.INTENT],'ORIGINAL_INTENT_FORMAT_AND_READONLY_RECOVERY_UNCHANGED')
    text=q.text(base.PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_NEW_PRECOMMIT_TEST_CHILD')
    audit.inverse(text[:-len(CHILD)],old[base.PARENT],'ALL13_ORIGINAL_SERVICE_TEST_BODIES_UNCHANGED')
    text=q.text(RECOVERY_TEST);after='request.kind == ArtifactKind::Receipt && request.file_name.as_str() == "revision-intent.json"'
    c.require(text.count(after)==1,'OLD_NEGATIVE_SCANNER_STILL_DENIES_ONLY_ITS_INTENT_UNDER_TEST')
    audit.inverse(text.replace(after,'request.kind == ArtifactKind::Receipt'),old[RECOVERY_TEST],'ALL12_ORIGINAL_RECOVERY_TEST_BODIES_UNCHANGED_ONLY_SCANNER_TARGET_NAMED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_JOBS_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVISION_JOBS_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,durable_idempotency_complete=False,actual_PostgreSQL_or_process_restart=False,
        SQL23_applied=False,SQL23_parse_or_runtime_qualified=False,SQL23_Rust_connector_or_job_registration_connected=False,
        actual_ArtifactService_and_RevisionService_code=True,in_memory_repositories=True,manifest_scanner_and_validator_synthetic=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(base.OUTPUT));docs=q.json(DOC_BASE)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='b36cc802d704a9c8b58fd035a2d97646970b856c57a5b1e1edb21de6516b13fc'
            and previous['cleanup']and previous['total_executed_cases']==25 and previous['fresh_inputs']==previous['final_fresh_hashes']==860,'EXACT259_PRIOR_INTENT25_AND_SOURCE_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='0b756f8f61961f75ac7640c57db3971e67bd627bd5f759ab640d5dfe9910f54e'and docs['cleanup'],'EXACT260_PRIOR_DOC_CLOSURE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_PRODUCT_POSTGRES_SQL1_TO22_ROUTING_NATIVE_AND_TEST_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);row['SQL23_static_source_contract']=sql_contract.check(q,c)
        names=lambda path:re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
        cases=set(names(base.PARENT))|{'recovery_v1::'+n for n in names(RECOVERY_TEST)}|{'precommit_v1::'+n for n in names(TEST)}
        c.require(len(cases)==29 and len(names(TEST))==4,'EXACT4_NEW25_AFFECTED_RUST_CASES_SEPARATE_FROM_STATIC_SQL_CONTRACT')
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_OWNED_PRECOMMIT_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        snapshot=base.base.base.base.base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        print(json.dumps(dict(state='STORED_JOBS_PREFLIGHT',inputs=len(q.snapshots),Rust_new4_affected25=True,SQL_static_only=True,official249_reexecuted=False)),flush=True)
        harness.run_one('precommit4_and_affected_storage_recovery25',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','stored_revision_commit','--message-format=short','--','--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_PRECOMMIT_TEMP_TEST_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_PRECOMMIT4_AFFECTED25_AND_PENDING_SQL23_SOURCE_CONTRACT_NOT_SQL_RUNTIME_P09_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=29,new_cases=4,affected_cases=25,
            all_prior_test_bodies_unmodified=True,test_scratch_empty=True,
            next_work='strict_schema23_connector_and_intent_registration_before_CAS_then_owned_DB_runtime_and_restart_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_JOBS_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_JOB_COMPONENT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','bounded_output_observation')},'pass_count':sum(v=='ok'for _,v in s.get('tests',[])),
                'failures':[n for n,v in s.get('tests',[])if v!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
