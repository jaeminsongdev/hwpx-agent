"""Registered read-only recovery10 + affected original recovery12, serial and resource-owned."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sql23_ack_loss as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-registered-recovery-components297.v1.json'
DRIVER='tools/p09/run_registered_recovery_components.py'
SOURCE='crates/product-cli/src/stored_revision_commit.rs'
INTENT='crates/product-cli/src/stored_revision_commit/intent.rs'
TYPES='crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/types.rs'
PARENT='crates/product-cli/tests/support/stored_registered_commit.rs'
TEST='crates/product-cli/tests/support/stored_registered_recovery.rs'
OLD_TEST='crates/product-cli/tests/support/stored_commit_recovery.rs'
CHANGED={SOURCE,INTENT,TYPES,PARENT};NEW={DRIVER,TEST}
CODE='implementation/p09/evidence/p09-361-stored-job-coordinator-checker-recovery275.v1.json'
SCRATCH='target/p09-registered-recovery-scratch-297'
def inverse(q,old):
    text=q.text(SOURCE);addition='pub use intent::{RegisteredStoredCommitRecoveryOutcome, reconcile_registered_stored_commit};\n'
    c.require(text.count(addition)==1,'ONE_REGISTERED_RECOVERY_EXPORT');audit.inverse(text.replace(addition,''),old[SOURCE],'ALL_ORIGINAL_STORAGE_CAS_CODE_UNCHANGED')
    text=q.text(PARENT);addition='#[path="stored_registered_recovery.rs"] mod recovery_read_v1;\n'
    c.require(text.endswith(addition),'ONE_NEW_REGISTERED_RECOVERY_TEST_CHILD');audit.inverse(text[:-len(addition)],old[PARENT],'ALL_ORIGINAL_REGISTERED_TESTS_UNCHANGED')
    text=q.text(TYPES);start=text.index('    /// Checks a saved encrypted request');end=text.index('    #[must_use] pub const fn intent_artifact_id',start)
    audit.inverse(text[:start]+text[end:],old[TYPES],'ALL_PREVIOUS_REGISTRATION_TYPES_AND_IDENTITY_VALIDATION_UNCHANGED')
    text=q.text(INTENT);start=text.index('    observe_bound_intent(artifacts,revisions,context,revision_context,binding,&mut clock,&intent)');end=text.index('    if intent.schema_version',start)
    restored=text[:start]+text[end:];start=restored.index('\n/// Registration and commit visibility are distinct.');end=restored.index('\nfn readable_intent',start)
    audit.inverse(restored[:start]+restored[end:],old[INTENT],'ORIGINAL_INTENT_WRITES_AUTH_AEAD_MANIFEST_SEALED_OBSERVATION_AND_RESULT_CHECKS_RECOMPOSE_EXACTLY')
def names(q,path,prefix):return{prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(path))}
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGISTERED_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGISTERED_RECOVERY_COMPONENTS',steps=[],own_cpu_selection=selection,actual_DB_or_Native_started=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,actual_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);last=compact.unpack(q.json(previous.OUTPUT));code=compact.unpack(q.json(CODE))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='c84559aaaa5b3e0185525e18febeec4c3c385f717e725983d3276676870a9485'and last['cleanup'],'EXACT295_PREVIOUS_SQL_ACK_SOURCE_CLOSURE')
        c.require(q.snapshots[CODE]['sha256']=='f7f8d8d21f6b30665222d40672d2bb2ff129441b2210108dea542833377e87b7'and code['cleanup'],'EXACT275_PREVIOUS_COMPONENT_TEST_SOURCE_CLOSURE')
        old={p['path']:p for p in code['source_pins']};old.update({p['path']:p for p in last['source_pins']})
        for n in CHANGED|NEW:q.pin(n)
        inverse(q,old)
        for n in sorted(previous.previous.inventory(guard.check)|CHANGED|NEW|{OLD_TEST,'crates/product-cli/tests/stored_revision_commit.rs'}):
            q.pin(n)
            if n not in CHANGED|NEW:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_CRYPTO_SQL_ENGINE_SOURCE_AND_PRIOR_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        new=names(q,TEST,'registered_v1::recovery_read_v1::');existing=names(q,OLD_TEST,'recovery_v1::')
        c.require(len(new)==10 and len(existing)==12,'EXACT_NEW10_AND_AFFECTED12_NO_TEST_BODY_WEAKENING')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'REGISTERED_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='REGISTERED_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_cases=10,affected_cases=12,official249_replayed=False)),flush=True)
        for label,pattern,cases in[('new_registered_recovery10','registered_v1::recovery_read_v1::',new),('affected_original_recovery12','recovery_v1::',existing)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_revision_commit','--message-format=short','--',pattern,'--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'REGISTERED_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_REGISTERED_READONLY_RECOVERY10_AND_AFFECTED12_NOT_DB_OR_PRODUCT_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=10,affected_original_cases=12,total_executed_cases=22,SQL_migrations_changed=False,
            next_work='actual_SQL_registered_receipts_only_restart_recovery_without_retained_plaintext_request')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        text=str(error);row.update(error_type=type(error).__name__,error_code=text if re.fullmatch('[A-Za-z0-9_]{1,160}',text)else'REGISTERED_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);rows=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,r))for r in rows]==samples,'REGISTERED_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=rows)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
