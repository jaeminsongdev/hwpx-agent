"""417: catalog product default1 + opt-in remaining32/installed1/affected2, no replays or Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_catalog_stored as previous

OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-product417.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_product.py'
BASE='implementation/p09/evidence/p09-361-personal-info-catalog-stored-recovery416.v1.json'
PARENT='crates/product-cli/src/form_product_request/stored_source_search.rs'
PRODUCT=PARENT[:-3]+'/personal_info_catalog.rs'
TEST='crates/product-cli/tests/support/personal_info_catalog_product.rs'
MANIFEST='crates/product-cli/Cargo.toml'
FEATURE='[features]\np09-installed-format-fixture = []\n\n'
LINK='\nmod product{include!("personal_info_catalog_product.rs");}\n'
HELPER='''    pub(crate) fn check_final_inputs<R,B,S,V>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,catalog:&impl CurrentPersonalInfoCatalogSource)->Result<(),D>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        verify_catalog(catalog,&self.receipt.catalog)?;provider.check_head(self.source.source.head).map_err(StoredActualFormImportError::from)?;Ok(())
    }
'''
CHANGED={PARENT,MANIFEST,previous.SERVICE,previous.TEST};NEW={DRIVER,PRODUCT,TEST}
PREFIX='stored_catalog::product::'
DEFAULT=PREFIX+'full_catalog_product_and_direct_service_have_same_original_result_and_provenance'
INSTALLED=PREFIX+'explicit_installed_catalog_current_store_and_product_bind_all_sixty_four_original_patterns'
AFFECTED={'stored_catalog::complete_sixty_four_patterns_and_full_source_provenance_are_not_truncated_to_legacy_sixteen',
    'stored_catalog::current_acl_revocation_and_regrant_apply_to_all_retained_deliveries'}
CONFIG=Path(r'C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin\PrivateInfo.ini')


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_PRODUCT417_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CURRENT_CATALOG_PRODUCT417',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        private_user_config_accessed=False,original_installation_config_mutated=False,source_document_mutation=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,whole_package_personal_data_removed=False,
        installed_vendor_authenticity_or_native_semantics_qualified=False,unaffected_successful_tests_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='7dfc8dcd477ffe62e40b6289dbb121180c04a0f15d3f025fd14fd20bcc98f55a'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==771
            and base['current_distinct_cases']==25 and base['retained_cases']==24 and base['last_executed_cases']==1,'EXACT416_SOURCE_SERVICE25_WITH_FAILURE415_PRESERVED')
        old={p['path']:p for p in base['source_pins']}
        for path in sorted(set(old)|r.closure.inventory(guard.check)|NEW|CHANGED):
            pin=q.pin(path)
            if path in old and path not in CHANGED:c.require(pin==old[path],'ALL_OTHER_CORE_CATALOG_MATCHER_MASKING_SOURCE_SERVICES_PRODUCTS_AND_RESOURCE_GUARDS_UNCHANGED')
        text=q.text(PARENT);added='pub mod personal_info_catalog;\n';c.require(text.count(added)==1,'ONE_CATALOG_PRODUCT_MODULE_EXPORT')
        r.audit.inverse(text.replace(added,''),old[PARENT],'ALL_EXISTING_STRICT_PRODUCT_REQUESTS_UNCHANGED')
        text=q.text(MANIFEST);c.require(text.count(FEATURE)==1,'ONE_EXPLICIT_INSTALLED_FIXTURE_FEATURE_NO_DEPENDENCY_OR_DEFAULT_CHANGE')
        r.audit.inverse(text.replace(FEATURE,''),old[MANIFEST],'ALL_ORIGINAL_CARGO_DEPENDENCIES_AND_LINTS_PRESERVED')
        text=q.text(previous.SERVICE);c.require(text.count(HELPER)==1,'ONE_ADDITIVE_PRODUCT_FINAL_CONFIG_AND_HEAD_CHECK')
        r.audit.inverse(text.replace(HELPER,''),old[previous.SERVICE],'ALL_PREVIOUS_SERVICE_ALGORITHMS_AND_CURRENT_ACCESS_GUARDS_UNCHANGED')
        text=q.text(previous.TEST);c.require(text.count(LINK)==1,'ONE_NESTED_PRODUCT_TEST_LINK_REUSING_UNCHANGED_SYNTHETIC_CATALOG_HELPERS')
        r.audit.inverse(text.replace(LINK,''),old[previous.TEST],'ALL23_STORED_TEST_BODIES_AND_HELPERS_UNCHANGED')
        text=q.text(TEST);cases={PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(cases)==34 and {DEFAULT,INSTALLED}<=cases and '#[ignore]'not in text
            and '#[cfg(all(windows,feature="p09-installed-format-fixture"))]\n#[test]\nfn '+INSTALLED.removeprefix(PREFIX)+'('in text,
            'EXACT_SYNTHETIC33_AND_ONE_EXPLICIT_INSTALLED_FIXTURE_NO_IGNORES')
        image=a.AcceptanceReader(CONFIG.parent,guard.check);pin=image.pin(CONFIG.name)
        c.require(pin['bytes']==17020 and pin['sha256']=='fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434','EXACT_COMPLETE_INSTALLED_CONFIG_SOURCE_NO_PRIVATE_USER_INI')
        entry=r.compact.unpack(q.json(previous.ENTRY_READY));c.require(not set(entry['entry_dependency_paths'])&(CHANGED|NEW),'EXTERNAL_CROSSREF_NATIVE_INPUTS_DISJOINT_FROM_PRODUCT_CHANGES')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-personal-info-catalog-product-scratch-417';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_PRODUCT417_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));env.pop('P09_INSTALLED_FORMAT_CATALOG',None)
        common=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--message-format=short']
        print(json.dumps(dict(state='CATALOG_PRODUCT417_PREFLIGHT',inputs=len(q.snapshots),default_without_fixture_env=1,
            remaining_synthetic=32,explicit_installed_fixture=1,affected_stored=2,old_suites_or_native_replayed=False)),flush=True)
        r.harness.run_one('catalog_product_default_no_fixture_env1',common+['--',DEFAULT,'--exact','--test-threads=1'],{DEFAULT},guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],{DEFAULT});c.require(row['steps'][-1]['diagnostics']==[],'DEFAULT_CATALOG_PRODUCT_NO_INSTALLATION_DEPENDENCY_OR_WARNINGS')
        selected=(cases-{DEFAULT})|AFFECTED
        r.harness.run_one('catalog_product_remaining32_installed1_affected2',common+['--features','p09-installed-format-fixture','--',*sorted(selected),'--test-threads=1'],selected,
            guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'ALL_SELECTED35_CASES_EXECUTED_WITHOUT_WARNINGS_OR_SKIPS')
        c.require(not any(scratch.iterdir()),'CATALOG_PRODUCT417_COMPILER_TEMP_EMPTY');final_attempted=True;image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CATALOG_PRODUCT_SYNTHETIC33_INSTALLED1_AFFECTED2_NOT_NATIVE_DEFAULTS_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_config_final_hashes=image.final_fresh_hashes,new_synthetic_cases=33,new_installed_fixture_cases=1,affected_cases=2,current_distinct_cases=36,
            external_crossref_execution_inputs_unchanged=True,next_work='native_catalog_match_set_semantics_and_full_search_options_then_remaining_P09_acceptance')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_PRODUCT417_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:
                final_attempted=True
                if image is not None:image.finish();row['external_config_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','external_config_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
