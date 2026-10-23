"""515: preserve zero-case514 compile failure; use original tuple/hash/value path for number controls."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as inputs
import character_detail_receipt as layout
SELF='tools/p09/verify_search_request_lookup_number.py'
OUTPUT='implementation/p09/evidence/p09-361-search-lookup515.v1.json'
SCRATCH='target/p09-search-lookup-scratch515'
BASE='implementation/p09/evidence/p09-361-search-storage513.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-search-lookup514/'
CHANGED=set(["crates/product-cli/src/form_product_request/stored_literal_replacement.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/review.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/regex.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/regex/insertions.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/styles.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/text_styles.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/paragraph_styles.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/unicode.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/unicode/matches.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/case.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/width.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/whitespace.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/controls.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/number_controls.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/sort.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/sort_groups.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/fonts.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/fonts/options/mutation.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/mutation.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/options/mutation.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/mutation.rs","crates/product-cli/src/form_product_request/stored_literal_replacement/compiler_view.rs","crates/product-cli/src/form_product_request/stored_operations/search_mutations.rs","crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs","crates/product-cli/tests/form_stored_provider/actual_import/search_storage_product.rs"])
FAMILY_LINKS=[["crates/product-cli/src/form_product_request/stored_literal_replacement.rs","search_lookup_product!(StoredLiteralReplacementProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs","search_lookup_product!(StoredLiteralTextAtomProductRequest,|raw|Request::parse_profile(raw,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA),root,atoms,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/review.rs","search_lookup_product!(StoredReviewLiteralProductRequest,|raw|ReviewRequest::parse(raw),base,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs","search_lookup_product!(StoredSelectorLiteralProductRequest,|raw|RequestWithPolicy::parse(raw),base,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/regex.rs","search_lookup_product!(StoredRegexReplacementProductRequest,|raw|RegexRequest::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/regex/insertions.rs","search_lookup_product!(StoredRegexInsertionProductRequest,|raw|InsertionRequest::parse(raw),inner,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/styles.rs","search_lookup_product!(StoredCharacterStyleProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/text_styles.rs","search_lookup_product!(StoredTextStyleProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/paragraph_styles.rs","search_lookup_product!(StoredParagraphStyleProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/unicode.rs","search_lookup_product!(StoredUnicodeProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/unicode/matches.rs","search_lookup_product!(StoredUnicodeMatchProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/case.rs","search_lookup_product!(StoredCaseProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/width.rs","search_lookup_product!(StoredWidthProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/whitespace.rs","search_lookup_product!(StoredWhitespaceProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/controls.rs","search_lookup_product!(StoredControlProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/number_controls.rs","impl StoredNumberControlProductRequest {\n    pub(crate) fn prepare_request_lookup_json<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8])\n        ->Result<crate::form_product_request::stored_operations::compiled_search::request_lookup::PreparedSearchRequestLookup,\n            crate::form_product_request::stored_operations::compiled_search::request_lookup::SearchRequestLookupError>\n    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {\n        use crate::form_product_request::stored_operations::compiled_search::request_lookup::{PreparedSearchRequestLookup,SearchRequestLookupError as LE};\n        let(request,canonical)=Request::parse(raw).map_err(|_|LE::Request)?;\n        let limits=crate::form_product_request::stored_operations::search_mutations::SearchMutationLimits::standard().map_err(|_|LE::Request)?;\n        let _values=ValidatedNumberControlValues::new(request.operation.control_kind,request.operation.stored_number,request.operation.format.native(),limits.search,limits.auxiliary)\n            .map_err(|_|LE::Request)?;\n        let scope=provider.source_search_product_scope(&request.project_id,&request.document_id)?;\n        let scoped=Request::scoped_sha(scope,&canonical).map_err(|_|LE::Request)?;\n        let source=artifact_service::ContentDigest::parse(&request.expected_source_package_sha256).map_err(|_|LE::Request)?;\n        let head=request.head().map_err(|_|LE::Request)?;\n        PreparedSearchRequestLookup::bind(provider,&request.project_id,&request.document_id,&request.idempotency_key,&canonical,&scoped,source,head,scope)\n    }\n}\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/sort.rs","search_lookup_product!(StoredParagraphSortProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/sort_groups.rs","search_lookup_product!(StoredParagraphSortGroupsProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/fonts.rs","search_lookup_product!(StoredFontProductRequest,|raw|Request::parse(raw),root,normal,no_preview);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/fonts/options/mutation.rs","search_lookup_product!(StoredFontOptionsMutationRequest,|raw|Request::parse(raw),root,normal,mutation);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/mutation.rs","search_lookup_product!(StoredNamedStyleMutationRequest,|raw|Request::parse(raw),root,normal,mutation);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles/options/mutation.rs","search_lookup_product!(StoredNamedStyleOptionsMutationRequest,|raw|Request::parse(raw),root,normal,mutation);\n"],["crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/mutation.rs","search_lookup_product!(StoredPersonalInfoMaskMutationRequest,|raw|Request::parse(raw),root,normal,mutation);\n"]]
PREFIX='crates/product-cli/src/form_product_request/'
CORE=PREFIX+'stored_operations/compiled_search/request_lookup.rs'
PARENT='crates/product-cli/tests/definition_detail_product.rs'
HOST='crates/product-cli/tests/form_stored_provider/actual_import/search_storage_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_request_lookup_product.rs'
DISPATCH='''        pub(super) fn prepare_lookup<R,B,S,V>(family:Family,provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8])
            ->Result<super::compiled_search::request_lookup::PreparedSearchRequestLookup,super::compiled_search::request_lookup::SearchRequestLookupError>
        where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository {
            match family {$ (Family::$variant=>$module::$request::prepare_request_lookup_json(provider,raw)),+}
        }
'''

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/SCRATCH).exists(),'LOOKUP514_FRESH_RUN_AND_SCRATCH_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_COMMON_SEARCH_REQUEST_LOOKUP',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,external003_replayed_or_cleanup_changed=False,
        operational_SQL_registry_custody_or_native_product_route_qualified=False,previous31_storage_tests_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='dc8c09d6b7afd3d4327eeb5ff205f67c1b16dd19fcdd93c9eb1b7f5f87034a79'
            and old['cleanup']is True and old['fresh_inputs']==old['final_fresh_hashes']==984 and old['qualified_test_cases']==31,'LOOKUP514_EXACT513_PRIOR_RESULT_PRESERVED')
        failed='implementation/p09/evidence/p09-361-search-lookup514.v1.json';archive_number=ARCHIVE+'failed-number514.rs'
        bad=layout.unpack(q.json(failed));q.pin(archive_number)
        c.require(q.snapshots[failed]['sha256']=='420a3154ae8dd1f762f3b977444deb87697e763cdb325e2de46a5a26aaca5e3f'
            and bad['cleanup']is True and bad['fresh_inputs']==1015 and bad['final_fresh_hashes']==0
            and len(bad['steps'])==1 and bad['steps'][0]['tests']==[] and bad['steps'][0]['exit_code']==101,'LOOKUP515_EXACT514_COMPILER_FAILURE_NO_TEST_REPLAY')
        number='crates/product-cli/src/form_product_request/stored_literal_replacement/number_controls.rs'
        pin=next(pin for pin in bad['source_pins']if pin['path']==number)
        c.require((pin['bytes'],pin['sha256'])==(q.snapshots[archive_number]['bytes'],q.snapshots[archive_number]['sha256']),'LOOKUP515_FAILED_NUMBER_SOURCE_ARCHIVED')
        names=inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,BASE,CORE,PARENT,TEST}|{ARCHIVE+name for name in CHANGED}
        names|=inputs.test_inputs((PARENT,),guard)
        for path in sorted(names):q.pin(path)
        for pin in old['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+pin['path']]
                c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'LOOKUP514_CHANGED_INPUT_EXACT513_ARCHIVE')
            else:c.require(q.snapshots[pin['path']]==pin,'LOOKUP514_OTHER_LIBRARY_RUNTIME_SOURCE_AND_PREVIOUS_BODIES_UNCHANGED')
        for path,link in FAMILY_LINKS:
            text=q.text(path);c.require(text.count(link)==1,'LOOKUP514_ONE_ORIGINAL_STRICT_PARSER_ADAPTER_PER_FAMILY')
            r.audit.inverse(text.replace(link,''),q.snapshots[ARCHIVE+path],'LOOKUP514_ALL_PREVIOUS_FAMILY_PARSERS_AND_MUTATORS_UNCHANGED')
        for path,link in [(PREFIX+'stored_operations/compiled_search.rs','pub mod request_lookup;\n'),
            (HOST,'#[path="search_request_lookup_product.rs"] mod request_lookup;\n'),
            (PREFIX+'stored_operations/search_mutations.rs',DISPATCH)]:
            text=q.text(path);c.require(text.count(link)==1,'LOOKUP514_ONE_CLOSED_LOOKUP_DISPATCH_LINK')
            r.audit.inverse(text.replace(link,''),q.snapshots[ARCHIVE+path],'LOOKUP514_PREVIOUS_ENTRY_COMPILER_AND_31_STORAGE_BODIES_UNCHANGED')
        macro=PREFIX+'stored_literal_replacement/compiler_view.rs';text=q.text(macro)
        start=text.index('macro_rules! lookup_request_fields');end=text.index('macro_rules! compiler_inventory',start)
        c.require(start<end,'LOOKUP514_ONLY_NEW_LOOKUP_ADAPTER_MACROS')
        r.audit.inverse(text[:start]+text[end:],q.snapshots[ARCHIVE+macro],'LOOKUP514_ORIGINAL_COMPILER_VIEW_PROJECTIONS_UNCHANGED')
        cases=helpers.tests(q,TEST,'product_host::detail_axes::search_storage::request_lookup::');c.require(len(cases)==30,'LOOKUP514_EXACT30_ENABLED_CASES')
        row.update(selected_cases=sorted(cases),lookup_and_existing_to_unobserved_product_bindings=23,common_negative_and_recovery_cases=7)
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.301693333880961,'LOOKUP514_RAM95_COMPILER_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists(),'LOOKUP514_CURRENT_UNIQUE_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='SEARCH_LOOKUP_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),families=23,CPU_cap_percent=6.25)),flush=True)
        target='definition_detail_product';command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'LOOKUP514_NO_COMPILER_WARNINGS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'LOOKUP514_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'LOOKUP514_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs']=actual
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_SEARCH_LOOKUP_CURRENT30_23_FAMILIES_NOT_NATIVE_OR_GATE',qualified_test_cases=30,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'LOOKUP514_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('panic_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
