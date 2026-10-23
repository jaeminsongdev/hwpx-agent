"""384: strengthen one exact limit-error assertion, retain29 PASS; run affected1 and previously-unrun review3 only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_catalog as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-limits384.v1.json';DRIVER='tools/p09/run_personal_info_catalog_limits.py'
FAILED='implementation/p09/evidence/p09-361-personal-info-catalog-recovery383.v1.json';PREVIOUS_DRIVER='tools/p09/run_personal_info_catalog_recovery.py'
CASE='catalog::match_and_reported_original_point_limits_fail_without_partial_catalog_results'
OLD='assert!(index.find_personal_info_catalog(&c.prepare(&[F::Telephone],Default::default())?,Scope::Document,all()).is_err());}Ok(())'
NEW='assert!(matches!(index.find_personal_info_catalog(&c.prepare(&[F::Telephone],Default::default())?,Scope::Document,all()),Err(CE::Search(SourceSearchError::Limit))));}Ok(())'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_LIMITS_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_CATALOG_EXACT_LIMITS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_DB_or_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,old_suites_replayed=False,
        production_algorithms_changed=False,original_installation_config_mutated=False,private_user_ini_accessed=False,actual_installed_config_tests_replayed=False,
        installed_vendor_authenticity_or_native_semantics_qualified=False,whole_package_personal_data_removed=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-personal-info-catalog-scratch-384';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_LIMITS_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='0355cf3f46fe5779e9f4ddde56da9d7b508ab486a3665de9c7e378032e2c7a4c'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==889 and failed['external_final_fresh_hashes']==1 and len(failed['steps'])==1
            and failed['error_code']=='COMPLETE_CATALOG_AND_UNCHANGED_SHARED_REGRESSIONS_NO_WARNINGS','EXACT383_WARNING_STOP_AFTER_ALL30_PASS_NOT_WHOLE_OR_NATIVE_ACCEPTANCE')
        step=failed['steps'][0];c.require(step['exit_code']==0 and len(step['tests'])==30 and all(v=='ok'for _,v in step['tests'])and len(step['diagnostics'])==1,'EXACT383_NEW27_AND_AFFECTED_DETECTION3_PASS_WITH_UNUSED_TEST_IMPORT_WARNING')
        pins={p['path']:p for p in failed['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(pins)|{DRIVER}):
            q.pin(path)
            if path in pins and path!=base.TEST:c.require(q.snapshots[path]==pins[path],'ALL_PRODUCTION_CATALOG_SOURCE_PATTERN_TEXT_SHARED_SCANNER_GUARDS_AND_OTHER_TESTS_UNCHANGED')
            elif path not in pins:c.require(path==DRIVER,'ONLY_EXACT_LIMIT_ERROR_VERIFIER_ADDED')
        text=q.text(base.TEST);c.require(text.count(NEW)==1,'ONE_EXACT_SOURCE_SEARCH_LIMIT_VARIANT_ASSERTION')
        audit.inverse(text.replace(NEW,OLD),pins[base.TEST],'ONLY_ONE_ASSERTION_STRENGTHENED_IMPORT_USED_NOT_REMOVED_ALL_OTHER_TEST_BODIES_UNCHANGED')
        original=compact.unpack(q.json(base.BASE));base.inverse(q,{p['path']:p for p in original['source_pins']})
        image=a.AcceptanceReader(base.EXTERNAL.parent,guard.check);pin=image.pin(base.EXTERNAL.name);c.require(pin['bytes']==17020 and pin['sha256']==base.CONFIG_SHA,'SAME_COMPLETE_READONLY_INSTALLATION_CONFIG_NOT_VENDOR_TRUST_OR_NATIVE_MATCHING')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),P09_INSTALLED_FORMAT_CATALOG=str(base.EXTERNAL));print(json.dumps(dict(state='CATALOG_LIMITS_PREFLIGHT',inputs=len(q.snapshots),affected_cases=1,unrun_review_cases=3,retained_cases=29)),flush=True)
        for binary,label,selected in [('personal_info_mask','catalog_exact_limit_variant_affected1',{CASE}),('document_import_review_selector','previously_unrun_original_review_selector3',base.REVIEW_CASES)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
            tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'CATALOG_EXACT_LIMIT_AND_PREVIOUSLY_UNRUN_REVIEW_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'CATALOG_LIMITS_TEMP_EMPTY');image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMPLETE_CATALOG_SOURCE27_AFFECTED6_CURRENT33_RETAINED29_RERUN1_UNRUN3_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_final_fresh_hashes=image.final_fresh_hashes,new_source_cases=27,affected_original_cases=6,current_distinct_cases=33,retained_cases=29,affected_rerun_cases=1,previously_unrun_cases=3,
            next_work='current_stored_catalog_provenance_and_strict_product_selection_then_native_matching_and_target_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'CATALOG_LIMITS_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            external_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'CATALOG_LIMITS_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','external_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
