"""Typed source definition search: nine new core + six new/fourteen affected product tests."""
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
OUTPUT='implementation/p09/evidence/p09-361-search-definition-recovery054.v1.json'
PRIOR='implementation/p09/evidence/p09-361-search-inspection-components048.v1.json'
TEST='crates/hwpx-package/tests/document_import_search_definitions.rs'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
HEADER='crates/hwpx-package/src/hancom_2020_minimal_header.xml'
RETAINED=('document_import_search','document_import_search_scope','document_import_search_inspection')
CATALOG='crates/hwpx-package/src/document_import/fields/semantics/catalog.rs'


def inverse(text,pin,label):
    c.require(pin['sha256']in{hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\n','\r\n').encode()).hexdigest()},label)


def inventory(check):return shared.source_inventory(check)|{TEST,PRODUCT,HEADER}|{'crates/hwpx-package/tests/'+n+'.rs'for n in RETAINED}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_DEFINITION_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_DEFINITION_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,retained_core_thirty_nine_reexecuted=False,
        implicit_cascade_hidden_visibility_native_or_full_search_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='25f6409f12938e9706e53adb2f9a518d3e1213102287a03f3fdd42e4c673b5c9'
            and prior['state'].startswith('PASS_')and prior['cleanup'],'EXACT_PRIOR_INSPECTION_PASS')
        old={p['path']:p for p in prior['source_pins']}
        failed_name='implementation/p09/evidence/p09-361-search-definition-components051.v1.json'
        failed=q.json(failed_name);failed_pins={p['path']:p for p in failed['source_pins']}
        c.require(failed['state']=='FAILED_SEARCH_DEFINITION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,
            'ORIGINAL_SIX_DEFINITION_FAILURES_AND_THREE_RESULTS_PRESERVED')
        for name in names-{TEST,'crates/hwpx-package/tests/support/search_definition_fixture.rs'}:
            c.require(q.snapshots[name]==failed_pins[name],'NO_PRODUCTION_OR_OTHER_INPUT_CHANGE_DURING_FIXTURE_RECOVERY')
        expected_retained=set()
        for name in RETAINED:
            path='crates/hwpx-package/tests/'+name+'.rs';c.require(q.snapshots[path]==old[path],'ORIGINAL_THIRTY_NINE_CORE_BODIES_UNCHANGED')
            expected_retained|=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path)))
        c.require(len(expected_retained)==39 and {n for n,s in prior['steps'][0]['tests']}==expected_retained
            and all(s=='ok'for n,s in prior['steps'][0]['tests']),'EXACT_PRIOR_THIRTY_NINE_CORE_PASSES')
        for path,addition in (('crates/hwpx-package/src/document_import/search.rs','    #[error("SOURCE_SEARCH_STYLE_DEFINITION_REJECTED")] Definition,\n'),
            ('crates/hwpx-package/src/document_import/search/inspection.rs','pub mod definitions;\n')):
            text=q.text(path);c.require(text.count(addition)==1,'ONLY_ADDITIVE_CORE_DEFINITION_DECLARATION');inverse(text.replace(addition,''),old[path],'ORIGINAL_CORE_MATCHER_AND_INSPECTION_EXACT_INVERSE')
        helper=('pub(in crate::document_import) fn source_style_catalogs_for_search(\n'
            '    source: &ImportedSourcePackage,\n'
            ') -> Result<(Vec<ImportedCatalogDefinition>, CharacterStyleCatalog, ParagraphStyleCatalog), CatalogImportError> {\n'
            '    let header = read_header(source)?;\n'
            '    Ok((header.definitions, header.characters, header.paragraphs))\n}\n\n')
        catalog=q.text(CATALOG);c.require(catalog.count(helper)==1,'ONE_PRIVATE_ORIGINAL_HEADER_DELEGATION');inverse(catalog.replace(helper,''),old[CATALOG],'ORIGINAL_CATALOG_AND_TYPED_READERS_UNCHANGED')
        prefix=q.text(PRODUCT).split('// Additive v3 definition cases;',1)[0]
        c.require(prefix.endswith('\n\n'),'ONE_APPENDED_V3_TEST_SEPARATOR');inverse(prefix[:-1],old[PRODUCT],'ORIGINAL_FOURTEEN_PRODUCT_TEST_BODIES_EXACT_INVERSE')
        declared_core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        independent='definition_style_conditions_need_explicit_used_axes_and_reject_empty_filters'
        c.require(dict(failed['steps'][0]['tests'])[independent]=='ok','RETAIN_ONE_INDEPENDENT_FILTER_VALIDATION_PASS')
        core=declared_core-{independent}
        product={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        c.require(len(declared_core)==10 and len(core)==9 and len(product)==20,'EXACT_NINE_AFFECTED_CORE_ONE_RETAINED_TWENTY_PRODUCT')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),CARGO_PROFILE_TEST_OPT_LEVEL='0',
            CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',
            CARGO_PROFILE_TEST_CODEGEN_UNITS='16',CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='SEARCH_DEFINITION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),prior_core_passes_preserved_without_replay=39)),flush=True)
        harness.run_one('eight_fixture_affected_and_one_independent_header_diagnostic',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_search_definitions','--','--test-threads=1','--skip',independent],core,guard,env,row)
        harness.run_one('six_v3_and_fourteen_affected_v1_v2_product_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_DEFINITION_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TYPED_STYLE_DEFINITIONS_NINE_CORE_ONE_INDEPENDENT_RETAINED_TWENTY_PRODUCT_PRIOR_THIRTY_NINE_PRESERVED_NOT_CASCADE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_core_tests=9,independent_filter_pass_preserved=1,new_product_tests=6,affected_product_tests=14,
            prior_core_passes_preserved=39,original_core_and_header_helpers_inverse_verified=True,original_fourteen_product_bodies_unchanged=True,
            caller_catalog_or_source_import_required=False,unrelated_stored_suites_reexecuted=False,command_line_or_server_route_added=False,idempotency_key_claimed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_DEFINITION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_DEFINITION_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
