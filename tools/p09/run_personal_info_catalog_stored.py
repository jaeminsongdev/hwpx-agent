"""415: new current-catalog stored service23 plus affected detection2, serial; no Native/DB."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-stored415.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_stored.py'
BASE='implementation/p09/evidence/p09-361-personal-info-catalog-fixture-profile385.v1.json'
ENTRY_READY='implementation/p09/evidence/p09-361-crossref-qualified-entry-runtime-ready413.v1.json'
CORE='crates/hwpx-package/src/document_import/search/personal_info/catalog.rs'
PARENT='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
METADATA='crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info.rs'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info_catalog.rs'
ROOT_TEST='crates/product-cli/tests/personal_info_mask_product.rs'
TEST='crates/product-cli/tests/support/personal_info_catalog_stored.rs'
CHANGED={CORE,PARENT,METADATA,ROOT_TEST};NEW={DRIVER,SERVICE,TEST}
AFFECTED={'detection::owned_service_and_product_retain_the_same_original_result_and_policy',
    'detection::metadata_debug_and_followups_never_contain_private_rule_query_key_or_body'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'STORED_CATALOG415_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CURRENT_STORED_CATALOG415',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        installed_or_private_user_config_read=False,source_document_mutation=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_format_identity_or_execution_qualified=False,whole_package_personal_data_removed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);before=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='4763da74572210f2e1ce57dbbbd367041f88f234b1d11f1120f181e709d19588'
            and before['cleanup']is True and before['fresh_inputs']==before['final_fresh_hashes']==893
            and before['current_distinct_cases']==33,'EXACT385_COMPLETE_SOURCE_CATALOG33_AND_EXPLICIT_INSTALLATION_FIXTURE_PRESERVED')
        old={p['path']:p for p in before['source_pins']};rust={p for p in old if p.startswith('crates/')or p in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        for path in sorted(r.closure.inventory(guard.check)|rust|NEW|CHANGED):
            pin=q.pin(path)
            if path in rust-CHANGED:c.require(pin==old[path],'ALL_UNAFFECTED_SOURCE_SEARCH_MASKING_PROTECTION_SERVICE_PRODUCT_COMPILER_AND_TESTS_UNCHANGED')
        text=q.text(CORE)
        for added in('    #[must_use]pub const fn catalog_receipt(&self)->&PersonalInfoCatalogReceipt{&self.receipt}\n',
            '    #[must_use]pub const fn catalog_receipt(&self)->&PersonalInfoCatalogReceipt{&self.catalog}\n',
            '    #[must_use]pub const fn policy_sha256(&self)->[u8;32]{self.policy_sha256}\n',
            '    #[must_use]pub const fn selected_pattern_count(&self)->usize{self.selected_patterns}\n'):
            c.require(text.count(added)==1,'EXACT_FOUR_READ_ONLY_PROVENANCE_ACCESSORS');text=text.replace(added,'')
        r.audit.inverse(text,old[CORE],'ALL_ORIGINAL_CATALOG_PARSER_COMPILER_SCANNER_AND_SOURCE_LIMITS_UNCHANGED')
        text=q.text(PARENT);added='pub mod personal_info_catalog;\n';c.require(text.count(added)==1,'ONE_STORED_CATALOG_EXPORT')
        r.audit.inverse(text.replace(added,''),old[PARENT],'ALL_PREVIOUS_CURRENT_SOURCE_ACCESS_GUARDS_AND_SERVICES_UNCHANGED')
        text=q.text(METADATA);c.require(text.count('pub(crate) fn metadata_sha(')==1,'ONE_EXISTING_STREAMING_METADATA_HASH_VISIBILITY_CHANGE')
        r.audit.inverse(text.replace('pub(crate) fn metadata_sha(','fn metadata_sha('),old[METADATA],'EXISTING_DETECTION_ALGORITHMS_AND_METADATA_LIMITS_UNCHANGED')
        text=q.text(ROOT_TEST);added='#[path="support/personal_info_catalog_stored.rs"]mod stored_catalog;\n';c.require(text.count(added)==1,'ONE_STORED_CATALOG_TEST_CHILD')
        r.audit.inverse(text.replace(added,''),old[ROOT_TEST],'ALL_PREVIOUS_MASK_DETECTION_AND_COMPILED_TEST_BODIES_PRESERVED')
        entry=r.compact.unpack(q.json(ENTRY_READY));c.require(q.snapshots[ENTRY_READY]['sha256']=='9dd98eafde1218df44d63f92c5f0ff6fe17d021f7da3fc7fffbbc27135c59cc0'
            and entry['cleanup']is True and not set(entry['entry_dependency_paths'])&(CHANGED|NEW),'EXTERNAL_NATIVE_EXECUTION_INPUTS_NOT_TOUCHED_BY_SEPARATE_RUST_SERVICE')
        cases={'stored_catalog::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}
        c.require(len(cases)==23 and '#[ignore]'not in q.text(TEST),'EXACT_NEW23_CASES_NO_SKIPS')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-personal-info-catalog-stored-scratch-415'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'STORED_CATALOG_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));env.pop('P09_INSTALLED_FORMAT_CATALOG',None)
        selected=cases|AFFECTED
        print(json.dumps(dict(state='CURRENT_STORED_CATALOG415_PREFLIGHT',inputs=len(q.snapshots),new_cases=23,affected_cases=2,
            only_current_source_proof_and_scan_once=True,whole_suites_or_official249_replayed=False)),flush=True)
        r.harness.run_one('new_current_catalog_stored23_affected_detection2',[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','personal_info_mask_product','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'NEW23_AND_AFFECTED2_PASS_WITHOUT_WARNINGS')
        c.require(not any(scratch.iterdir()),'STORED_CATALOG_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_STORED_CATALOG23_AFFECTED_DETECTION2_NOT_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=23,affected_cases=2,source_catalog33_not_replayed=True,external_crossref_inputs_unchanged=True,
            next_work='strict_full_catalog_product_request_binding_and_explicit_installed_config_stored_fixture_then_native_matching_target_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'STORED_CATALOG415_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),
            elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
