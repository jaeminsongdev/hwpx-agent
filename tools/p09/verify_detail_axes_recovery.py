"""497: preserve old9 bodies, extend only the warning-affected protection case with actual AEAD denial."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import verify_detail_axes_product as prior
import character_detail_receipt as layout
r=prior.r
SELF='tools/p09/verify_detail_axes_recovery.py'
OUTPUT='implementation/p09/evidence/p09-361-detail-axes-recovery497.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-detail-axes496/'
CASE='product_host::detail_axes::retained_v3_v7_details_still_require_current_write_acl_and_deny_quarantine'
ADDED='''    // A clean independent source must also fail AEAD before any earlier ACL/quarantine denial.
    {
        let fresh=StoredFixture::new(&raw,ArtifactKind::Result,false)?;write_provider!(fresh,fresh_actor,fresh_provider);
        let filter=json!({"paragraph_source":"direct_property","paragraph_details":{"condense":17}});
        let a=definition(&fresh,&raw,filter.clone())?;let b=selector(&fresh,&raw,filter)?;
        let first=legacy(&fresh_provider,&a)?;let second=scoped(&fresh_provider,&b)?;
        fresh.blobs.tamper.store(true,Ordering::SeqCst);let called=Cell::new(false);
        assert!(first.with_verified_json(&fresh_provider,6,|_|called.set(true)).is_err());
        assert!(second.with_verified_json(&fresh_provider,6,|_|called.set(true)).is_err());
        assert!(legacy(&fresh_provider,&a).is_err());assert!(scoped(&fresh_provider,&b).is_err());assert!(!called.get());
    }
'''

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DETAIL_AXES497_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_DETAIL_AXES_WARNING_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,previous495_or_unmodified496_bodies_replayed=False,
        original496_failure_and_missing_final_closure_preserved=True,shared_fixture_or_production_warning_suppressed=False,
        full_effective_style_native_visibility_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=layout.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='a377d253950be6619715b4658a95980b2c6600299722941de94b0c9726121a0d'
            and failed['state']=='FAILED_DETAIL_AXES_PRODUCT_CONNECTION'and failed['error_code']=='DETAIL_AXES_NO_COMPILER_DIAGNOSTICS'
            and failed['cleanup']is True and failed['final_fresh_hashes']==0 and len(failed['steps'])==1,'EXACT496_COMPILE_WARNING_FAILURE_NOT_REWRITTEN')
        step=failed['steps'][0];tests=step['tests'];warnings=step['bounded_output_observation']['safe_warning_locations']
        c.require(step['exit_code']==0 and step['cleanup']is True and len(tests)==10 and all(status=='ok'for name,status in tests)
            and len(warnings)==1 and warnings[0]['path']=='crates/product-cli/tests/support/stored_source_fixture.rs'
            and warnings[0]['symbols']==['blobs'],'EXACT496_TEN_RETURNED_BODIES_AND_ONLY_UNUSED_FIXTURE_FIELD_WARNING')
        for pin in failed['source_pins']:
            if pin['path']!=prior.TEST:c.require(q.pin(pin['path'])==pin,'ALL496_PRODUCT_MATCHER_GUARD_SHARED_FIXTURE_AND_PARSER_INPUTS_UNCHANGED')
        for path in(SELF,prior.TEST,ARCHIVE+'product496.rs',ARCHIVE+'runner496.py'):q.pin(path)
        for current,saved in((prior.SELF,'runner496.py'),(prior.TEST,'product496.rs')):
            old=next(pin for pin in failed['source_pins']if pin['path']==current);archive=q.snapshots[ARCHIVE+saved]
            c.require((old['bytes'],old['sha256'])==(archive['bytes'],archive['sha256']),'EXACT496_ORIGINAL_RUNNER_AND_TEST_FILE_ARCHIVED')
        current=q.text(prior.TEST);c.require(current.count(ADDED)==1,'ONE_ACTUAL_AEAD_PROTECTION_BLOCK_NOT_UNUSED_WARNING_SUPPRESSION')
        r.audit.inverse(current.replace(ADDED,''),q.snapshots[ARCHIVE+'product496.rs'],'ALL_NINE_OTHER_BODIES_AND_EVERY_SHARED_HELPER_RESTORED_EXACTLY')
        accepted={name for name,status in tests};c.require(CASE in accepted,'EXACT_ONE_UPDATED_PROTECTION_CASE')
        row['retained_test_names']=sorted(accepted-{CASE});row['retained_product_bodies']=9
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];c.require(available>11.139219593950513,'DETAIL_AXES_RECOVERY_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-detail-axes-recovery-scratch497';c.require(not scratch.exists(),'DETAIL_AXES_RECOVERY_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='DETAIL_AXES_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained_bodies=9,executed_updated_cases=1,previous36_replayed=False)),flush=True)
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','definition_detail_product','--message-format=short','--',CASE,'--exact','--test-threads=1']
        r.harness.run_one('updated_v3_v7_acl_quarantine_aead_only',command,{CASE},guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],{CASE});observed=row['steps'][-1]['bounded_output_observation']
        c.require(not row['steps'][-1]['diagnostics']and not observed['safe_warning_locations'],'UPDATED_PROTECTION_BODY_NO_COMPILER_WARNINGS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob('definition_detail_product-*.d'):
            declared=prior.prior.prior.dependencies(path);c.require(declared<=set(q.snapshots),'ACTUAL497_COMPILER_INPUT_CLOSURE_PINNED_BEFORE_RUN')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'RECOVERY497_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs']=actual
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_EXPLICIT_DETAIL_PRODUCTS_RETAINED9_UPDATED_AEAD1_CURRENT_INPUT_CLOSURE_NOT_NATIVE_OR_GATE',
            current_qualified_product_bodies=10,executed_updated_product_cases=1,character_and_paragraph_predicate_families=51,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'DETAIL_AXES_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
