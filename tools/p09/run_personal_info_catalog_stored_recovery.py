"""416: fix one test's early ? propagation; rerun only its failed case, retain24."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_catalog_stored as prior
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-stored-recovery416.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_stored_recovery.py'
CASE='stored_catalog::source_kind_and_unverified_scanner_do_not_become_current_catalog_results'
AFTER='''    let bytes=raw("MARK")?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);let f=feed("MARK");
        let result=p.import_actual_forms(s.head,4).map_err(CE::from).and_then(|source|source.into_personal_info_catalog(&p,&f,sha(&f),&FAMILIES,Scope::Document,policy(),Default::default(),4));
        assert!(result.is_err());}Ok(())
'''
BEFORE='''    let bytes=raw("MARK")?;for(kind,unverified)in [(ArtifactKind::Source,false),(ArtifactKind::Result,true)]{let s=StoredFixture::new(&bytes,kind,unverified)?;writer!(s,actor,p);let f=feed("MARK");assert!(detect!(&p,&s,&f).is_err());}Ok(())
'''


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'STORED_CATALOG_RECOVERY416_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CURRENT_STORED_CATALOG_RECOVERY416',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        production_algorithms_changed=False,installed_or_private_user_config_read=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_format_identity_or_execution_qualified=False,whole_package_personal_data_removed=False,previous_successes_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='2ac27f289279991f0a833d4e7b4183718013baaa13085d5b47e3fc6823f814b0'
            and failed['state']=='FAILED_CURRENT_STORED_CATALOG415'and failed['cleanup']is True
            and failed['fresh_inputs']==failed['final_fresh_hashes']==769 and len(failed['steps'])==1,'EXACT415_FAILED_TEST_PROPAGATION_ORIGINAL_RETAINED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and len(step['tests'])==25 and [n for n,status in step['tests']if status!='ok']==[CASE]
            and step['safe_error_variants']==['Source']and step['panic_locations']==[],'EXACT24_SUCCESS_AND_ONE_EARLY_SOURCE_PROPAGATION_TEST_FAILURE')
        old={p['path']:p for p in failed['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            pin=q.pin(path)
            if path in old and path!=prior.TEST:c.require(pin==old[path],'ALL_PRODUCTION_SOURCE_GUARDS_AND_SUCCESSFUL_TESTS_UNCHANGED')
        text=q.text(prior.TEST);c.require(text.count(AFTER)==1,'ONE_EXACT_FAILED_CASE_ERROR_CAPTURE_FIX')
        r.audit.inverse(text.replace(AFTER,BEFORE),old[prior.TEST],'ONLY_FAILED_CASE_CAPTURES_IMPORT_ERROR_WITHOUT_CHANGING_PASSED_HELPER_OR_24_BODIES')
        scratch=c.ROOT/'target/p09-personal-info-catalog-stored-scratch-416';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_RECOVERY416_UNIQUE_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));env.pop('P09_INSTALLED_FORMAT_CATALOG',None)
        print(json.dumps(dict(state='CURRENT_STORED_CATALOG416_PREFLIGHT',inputs=len(q.snapshots),failed_case_to_execute=1,prior_successes_retained=24)),flush=True)
        r.harness.run_one('only_failed_catalog_kind_scanner_rejection1',[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',
            'personal_info_mask_product','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],{CASE});c.require(row['steps'][-1]['diagnostics']==[],'FAILED_CASE1_PASS_WITHOUT_WARNINGS')
        c.require(not any(scratch.iterdir()),'CATALOG_RECOVERY416_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_STORED_CATALOG_FAILED1_RETAINED24_CURRENT25_NOT_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_service_cases=23,affected_previous_detection_cases=2,current_distinct_cases=25,last_executed_cases=1,retained_cases=24,
            next_work='strict_full_catalog_product_request_binding_and_explicit_installed_config_stored_fixture_then_native_matching_target_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'STORED_CATALOG416_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
