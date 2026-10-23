"""Real isolated byte/file transactions and streaming integrity, not P09 route/commit qualification."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_transaction_bytes_probe_recovery as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-transaction-bytes-components253.v1.json'
DRIVER='tools/p09/run_transaction_bytes_components.py'
INTEGRITY=base.base.MODEL[:-3]+'/integrity.rs'
SCRATCH='target/p09-transaction-byte-scratch-253'
AFTER_CAS='''        if let Err(error) = self.verify_published_result_identity() {
            // CAS already reported committed: never roll back or report this artifact as complete.
            self.machine.mark_recovery(TransactionState::Incomplete);
            self.artifact_disposition = ArtifactDisposition::CommittedOutcomeUncertain;
            return Err(error);
        }
'''


def inventory(check):return base.inventory(check)|{DRIVER,INTEGRITY}


def expected(q):
    names=lambda path:re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
    old=names(base.base.PARENT);new=names(base.base.TEST)
    c.require(len(old)==len(set(old))==9 and len(new)==len(set(new))==14,'EXACT9_AFFECTED_FILE14_NEW_BYTE_AND_INTEGRITY_CASES')
    return set(old)|{'bytes_v1::'+name for name in new}


def inverse(q,old):
    text=q.text(base.base.MODEL)
    for marker in('mod integrity;\n','        self.verify_staged_result_identity()?;\n','        self.verify_published_result_identity()?;\n',AFTER_CAS):
        c.require(text.count(marker)==1,'EXACT_ADDITIVE_CALLBACK_AND_PUBLICATION_IDENTITY_GUARDS');text=text.replace(marker,'')
    audit.inverse(text,old[base.base.MODEL],'ALL_PRIOR_BYTE_FILE_ADAPTER_STATE_PIPELINE_FAULTS_AND_CAS_RECOVERY_UNCHANGED_OUTSIDE_INTEGRITY_GUARDS')
    text=q.text(base.base.TEST);start=text.index('#[test]\nfn file_validator_same_size_staging_tamper_also_fails_before_publication_or_cas')
    audit.inverse(text[:start],old[base.base.TEST],'ALL12_ORIGINAL_NEW_CASES_INCLUDING_REPRODUCED_NEGATIVE_UNCHANGED')
    text=q.text(INTEGRITY)
    for marker in('[0_u8; 64 * 1024]','reader.take(self.limits.max_output_bytes.saturating_add(1))','*n <= expected_size',
        'self.workspace.open_staged(staged)','self.workspace.open_output(relative)','size != expected_size',
        '<[u8; 32]>::from(digest.finalize()) != expected_sha256'):
        c.require(marker in text,'BOUNDED_STREAMING_RESULT_SIZE_AND_DIGEST_AFTER_VALIDATOR_PUBLISH_AND_CAS')
    c.require(all(x not in text for x in('Vec::','read_to_end','fs::write','unsafe','SignatureVerified')),'NO_SECOND_OUTPUT_BUFFER_SOURCE_WRITE_OR_TRUST_PROMOTION')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'BYTE_TRANSACTION_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_BYTE_TRANSACTION_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,actual_registry_target_or_native_qualified=False,ArtifactService_ingest_or_RevisionService_CAS=False,
        real_filesystem_only_owned_test_scratch=True,validator_and_CAS_synthetic=True,scratch_parent=SCRATCH)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);probe=base.base.prior.compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='45315df255c1338aa631d3ecb7a1f2afa741dce71800b1e9e3121cdb9ad640d9'
            and probe['state']=='REPRODUCED_STAGED_OUTPUT_TAMPER_TEST_FAILURE_NOT_ACCEPTANCE_OR_GATE'and probe['cleanup']
            and probe['fresh_inputs']==probe['final_fresh_hashes']==844,'EXACT252_ACTUAL_NEGATIVE_FAILURE_AND_SOURCE_CLOSURE')
        c.require(probe['steps'][0]['exit_code']==101 and probe['steps'][0]['tests']==[[base.base.CASE,'FAILED']],'ORIGINAL_SECURITY_NEGATIVE_FAILURE_RETAINED')
        old={p['path']:p for p in probe['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,INTEGRITY,base.base.MODEL,base.base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_OTHER_PRODUCT_SOURCE_BYTE_ADAPTER_ROUTE_NATIVE_GUARDS_AND_OLD9_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        parent=c.ROOT/'target';scratch=c.ROOT/SCRATCH
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()
            and scratch.resolve().is_relative_to(parent.resolve()),'NEW_OWNED_PROJECT_TARGET_TEMP_PARENT_ONLY')
        scratch.mkdir();environment=audit.environment();environment.update(TEMP=str(scratch),TMP=str(scratch))
        row['test_TEMP_and_TMP_only_child_environment']=True
        print(json.dumps(dict(state='BYTE_TRANSACTION_PREFLIGHT',inputs=len(q.snapshots),new=14,affected_file=9,official249_reexecuted=False,only_child_temp_under_project=True)),flush=True)
        snapshot=base.base.prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        harness.run_one('fourteen_byte_integrity_and_nine_existing_file_transaction_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','operation-engine',
            '--test','workspace_transaction','--message-format=short','--','--test-threads=1'],cases,guard,environment,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'ALL_OWNED_TEMPFILE_TEST_DIRECTORIES_CLEANED')
        q.finish();guard.check(force=True)
        row.update(state='PASS_BYTE_SOURCE_TRANSACTION14_AFFECTED_FILE9_STREAMING_INTEGRITY_NOT_P09_EXECUTION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            total_executed_cases=23,new_cases=14,affected_file_cases=9,all_original_file_tests_unmodified=True,test_scratch_empty=True,
            next_work='provider_owned_verified_source_and_result_ingest_then_RevisionService_CAS_and_durable_idempotency_behind_real_execution_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'BYTE_TRANSACTION_COMPONENTS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_BYTE_TRANSACTION_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,base.base.prior.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','test_scratch_empty','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
