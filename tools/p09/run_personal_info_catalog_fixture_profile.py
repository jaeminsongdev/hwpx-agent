"""385: explicit opt-in Windows installation fixture; four affected tests plus default-without-env1, retain28."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_catalog as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-fixture-profile385.v1.json';DRIVER='tools/p09/run_personal_info_catalog_fixture_profile.py'
BASE='implementation/p09/evidence/p09-361-personal-info-catalog-limits384.v1.json';MANIFEST='crates/hwpx-package/Cargo.toml'
CFG='#[cfg(all(windows,feature="p09-installed-format-fixture"))]\n';FEATURE='[features]\np09-installed-format-fixture = []\n\n'
DEFAULT_CASE='catalog::complete_ten_family_catalog_keeps_order_counts_and_false_native_authority'
INSTALLED_CASES={'catalog::full_installed_catalog_has_exact_ten_families_sixty_four_patterns_and_no_address_assumption',
    'catalog::installed_telephone_patterns_find_ascii_fullwidth_and_cross_run_source_without_changing_it',
    'catalog::installed_unparenthesized_ip_alternation_is_not_silently_fixed_or_claimed_validated',
    'catalog::identical_resident_and_foreigner_patterns_keep_distinct_source_families_and_indices'}

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_FIXTURE_PROFILE_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_CATALOG_FIXTURE_PROFILE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_DB_or_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,old_suites_replayed=False,
        production_algorithms_changed=False,original_installation_config_mutated=False,private_user_ini_accessed=False,
        installed_vendor_authenticity_or_native_semantics_qualified=False,whole_package_personal_data_removed=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-personal-info-catalog-scratch-385';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_FIXTURE_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);previous=compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='302017786dacab614d4bfc13f0c8284fd3e6794a087656be37ea1865758d6402'and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==891 and previous['current_distinct_cases']==33 and previous['external_final_fresh_hashes']==1,'EXACT384_CURRENT33_WITH_STRICT_LIMIT_VARIANT_AND_ORIGINAL_WARN_FAILURE_RETAINED')
        pins={p['path']:p for p in previous['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(pins)|{DRIVER}):
            q.pin(path)
            if path in pins and path not in {MANIFEST,base.TEST}:c.require(q.snapshots[path]==pins[path],'ALL_PRODUCTION_CATALOG_SEARCH_GUARDS_AND_OTHER_TEST_BODIES_UNCHANGED')
            elif path not in pins:c.require(path==DRIVER,'ONLY_EXPLICIT_FIXTURE_PROFILE_VERIFIER_ADDED')
        manifest=q.text(MANIFEST);c.require(manifest.count(FEATURE)==1,'ONE_OPT_IN_FIXTURE_FEATURE_WITHOUT_DEFAULT_OR_DEPENDENCY_CHANGE')
        audit.inverse(manifest.replace(FEATURE,''),pins[MANIFEST],'ALL_PREVIOUS_CARGO_MANIFEST_DEPENDENCIES_AND_LINTS_UNCHANGED')
        text=q.text(base.TEST);c.require(text.count(CFG)==8 and '#[ignore]'not in text,'EXACT4_FIXTURE_TESTS_AND4_HELPERS_CFG_GATED_NOT_IGNORED')
        audit.inverse(text.replace(CFG,''),pins[base.TEST],'ALL27_TEST_BODIES_UNCHANGED_ONLY_EXPLICIT_LOCAL_FIXTURE_ACTIVATION_ADDED')
        for name in INSTALLED_CASES:
            c.require(CFG+'#[test]\nfn '+name.removeprefix('catalog::')+'('in text,'ALL_FOUR_PINNED_INSTALLATION_TESTS_REQUIRE_EXPLICIT_WINDOWS_FEATURE')
        image=a.AcceptanceReader(base.EXTERNAL.parent,guard.check);pin=image.pin(base.EXTERNAL.name);c.require(pin['bytes']==17020 and pin['sha256']==base.CONFIG_SHA,'SAME_READONLY_COMPLETE11_SECTION64_PATTERN_INSTALLATION_CONFIG')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));env.pop('P09_INSTALLED_FORMAT_CATALOG',None)
        print(json.dumps(dict(state='CATALOG_FIXTURE_PROFILE_PREFLIGHT',inputs=len(q.snapshots),default_without_fixture_env=1,affected_explicit_fixture_cases=4,retained_cases=28)),flush=True)
        common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','personal_info_mask','--message-format=short']
        harness.run_one('default_catalog_without_installation_fixture_env1',common+['--',DEFAULT_CASE,'--exact','--test-threads=1'],{DEFAULT_CASE},guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],{DEFAULT_CASE});c.require(row['steps'][-1]['diagnostics']==[],'DEFAULT_PROFILE_NO_FIXTURE_ENV_OR_WARNINGS')
        env['P09_INSTALLED_FORMAT_CATALOG']=str(base.EXTERNAL)
        harness.run_one('explicit_installed_catalog_feature_affected4',common+['--features','p09-installed-format-fixture','--',*sorted(INSTALLED_CASES),'--test-threads=1'],INSTALLED_CASES,guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],INSTALLED_CASES);c.require(row['steps'][-1]['diagnostics']==[],'ALL_FOUR_AFFECTED_ACTUAL_INSTALLATION_TESTS_EXECUTED_WITHOUT_WARNINGS_OR_SKIPS')
        c.require(not any(scratch.iterdir()),'CATALOG_FIXTURE_TEMP_EMPTY');image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CATALOG_DEFAULT_NO_ENV1_EXPLICIT_INSTALLATION4_RETAINED28_CURRENT33_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_final_fresh_hashes=image.final_fresh_hashes,current_distinct_cases=33,new_source_cases=27,affected_original_cases=6,last_executed_cases=5,retained_cases=28,
            next_work='current_stored_catalog_provenance_and_strict_product_selection_then_native_matching_and_target_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'CATALOG_FIXTURE_PROFILE_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            external_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'CATALOG_FIXTURE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','external_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
