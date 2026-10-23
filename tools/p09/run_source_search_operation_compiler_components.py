"""All16 actual product compilers,30 new integration cases and6 actual-source owner refusal units."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_splice_inventory_components as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
snapshot=prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-source-search-operation-compiler-components213.v1.json'
BASELINE='implementation/p09/evidence/p09-361-style-splice-inventory-recovery210.v1.json'
ROOT='crates/product-cli/src/form_product_request/stored_operations.rs'
MODEL=ROOT[:-3]+'/compiled_search.rs';PROJECTION=MODEL[:-3]+'/projection.rs';OWNERS=MODEL[:-3]+'/owners.rs';BUILD=MODEL[:-3]+'/build.rs'
UNIT=MODEL[:-3]+'/owners/tests.rs'
ACTUAL='crates/product-cli/src/form_stored_provider/actual_import.rs'
TABLE=ROOT[:-3]+'/search_mutations.rs'
STORED_ROOT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
PRODUCT_ROOT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORE_MACRO=STORED_ROOT[:-3]+'/compiler_view.rs';PRODUCT_MACRO=PRODUCT_ROOT[:-3]+'/compiler_view.rs'
PARENT=prior.PARENT;TEST='crates/product-cli/tests/form_stored_provider/actual_import/compiled_search_product.rs'
DRIVER='tools/p09/run_source_search_operation_compiler_components.py'
STORED=[["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs","PreparedStoredLiteralSearchCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms.rs","PreparedStoredLiteralTextAtomCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review.rs","PreparedStoredReviewLiteralCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review/selector.rs","PreparedStoredSelectorLiteralCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/regex.rs","PreparedStoredSelectorRegexCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/regex/insertions.rs","PreparedStoredSelectorRegexInsertionCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/styles.rs","PreparedStoredCharacterStyleCandidate","style"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/text_styles.rs","PreparedStoredTextStyleCandidate","style"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/paragraph_styles.rs","PreparedStoredParagraphStyleCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/unicode.rs","PreparedStoredUnicodeCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/unicode/matches.rs","PreparedStoredUnicodeMatchCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/case.rs","PreparedStoredCaseCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/width.rs","PreparedStoredWidthCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/whitespace.rs","PreparedStoredWhitespaceCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/controls.rs","PreparedStoredControlCandidate","plain"],["crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/number_controls.rs","PreparedStoredNumberControlCandidate","plain"]]
PRODUCT=[["crates/product-cli/src/form_product_request/stored_literal_replacement.rs","PreparedStoredLiteralReplacementProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/atoms.rs","PreparedStoredLiteralTextAtomProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/review.rs","PreparedStoredReviewLiteralProduct","request.base","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/selector.rs","PreparedStoredSelectorLiteralProduct","request.base","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/regex.rs","PreparedStoredRegexReplacementProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/regex/insertions.rs","PreparedStoredRegexInsertionProduct","request.inner","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/styles.rs","PreparedStoredCharacterStyleProduct","request","style"],["crates/product-cli/src/form_product_request/stored_literal_replacement/text_styles.rs","PreparedStoredTextStyleProduct","request","style"],["crates/product-cli/src/form_product_request/stored_literal_replacement/paragraph_styles.rs","PreparedStoredParagraphStyleProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/unicode.rs","PreparedStoredUnicodeProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/unicode/matches.rs","PreparedStoredUnicodeMatchProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/case.rs","PreparedStoredCaseProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/width.rs","PreparedStoredWidthProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/whitespace.rs","PreparedStoredWhitespaceProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/controls.rs","PreparedStoredControlProduct","request","plain"],["crates/product-cli/src/form_product_request/stored_literal_replacement/number_controls.rs","PreparedStoredNumberControlProduct","request","plain"]]
NEW={MODEL,PROJECTION,OWNERS,BUILD,UNIT,STORE_MACRO,PRODUCT_MACRO,TEST,DRIVER}
CHANGED={p for p,_,_ in STORED}|{p for p,_,_,_ in PRODUCT}|{ACTUAL,ROOT,TABLE,PARENT}
PREFIX=prior.prior.base.PREFIX+'compiled_v1::'
UNIT_PREFIX='form_product_request::stored_operations::compiled_search::owners::tests::'
HEAD='''    pub(crate) const fn compiler_head(&self) -> RevisionHead { self.source.head }
    pub(crate) fn check_compiler_head<R, B, S, V>(&self, provider: &StoredFormProvider<'_, R, B, S, V>) -> Result<(), StoredActualFormImportError>
    where R: ArtifactMetadataRepository, B: EncryptedBlobStore, S: ArtifactScanner, V: RevisionRepository {
        provider.check_head(self.source.head).map_err(Into::into)
    }
'''
VIEW='''            pub(crate) fn compiler_view(&self) -> super::compiled_search::CompilationView<'_> {
                match self { $(Self::$variant(candidate) => candidate.compiler_view()),+ }
            }
'''


def inventory(check):return prior.inventory(check)|{'tools/p09/run_style_splice_inventory_recovery.py'}|NEW


def inverse(q,old):
    for path,ty,style in STORED:
        text=q.text(path);marker='compiler_source!('+ty+(', style'if style=='style'else'')+');\n'
        c.require(text.count(marker)==1,'ONE_CRATE_PRIVATE_SOURCE_BORROW_PER_PREPARED_FAMILY');text=text.replace(marker,'')
        if path==STORED_ROOT:text=text.replace('#[macro_use] mod compiler_view;\n','')
        audit.inverse(text,old[path],'ENTIRE_ORIGINAL_STORED_PREPARATION_ACCESS_OWNER_TRANSFER_RECEIPT_AND_DELIVERY_BODIES_UNCHANGED')
    for path,ty,fields,style in PRODUCT:
        text=q.text(path);marker=f'compiler_product!({ty}, {fields}, {style});\n'
        c.require(text.count(marker)==1,'ONE_ORIGINAL_PARSED_IDENTITY_AND_SOURCE_BORROW_PER_PRODUCT');text=text.replace(marker,'')
        if path==PRODUCT_ROOT:text=text.replace('#[macro_use] mod compiler_view;\n','')
        audit.inverse(text,old[path],'ENTIRE_ORIGINAL16_STRICT_PRODUCT_PARSERS_BINDINGS_CURRENT_ACCESS_OUTPUT_AND_ROUTE_BODIES_UNCHANGED')
    text=q.text(ACTUAL);c.require(text.count(HEAD)==1,'ONE_ADDITIVE_SOURCE_HEAD_BORROW_AND_POST_COMPILER_HEAD_CHECK')
    audit.inverse(text.replace(HEAD,''),old[ACTUAL],'ENTIRE_ORIGINAL_ACTUAL_SOURCE_IMPORT_RECONSTRUCTION_AND_SECURITY_BODIES_UNCHANGED')
    audit.inverse(q.text(ROOT).replace('pub mod compiled_search;\n',''),old[ROOT],'ENTIRE_ORIGINAL_COMMON_FORM_FORMULA_SEARCH_DISPATCH_UNCHANGED')
    text=q.text(TABLE);c.require(text.count(VIEW)==1,'ONE_CLOSED16_FAMILY_COMPILER_VIEW_DISPATCH')
    audit.inverse(text.replace(VIEW,''),old[TABLE],'ENTIRE_ORIGINAL_CLOSED16_SCHEMA_TABLE_PREPARATION_RECEIPT_VERIFY_DELIVERY_ROUTE_BODIES_UNCHANGED')
    text=q.text(PARENT);marker='#[path="compiled_search_product.rs"] mod compiled_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_COMPILER_TEST_CHILD')
    audit.inverse(text.replace(marker,''),old[PARENT],'ALL26_COMMON_AND12_SPLICE_TEST_BODIES_AND_HELPERS_UNCHANGED')
    owner=q.text(OWNERS);build=q.text(BUILD);model=q.text(MODEL)
    for marker in('source.resolve_anchor(anchor)','direct.entry(&anchor.opaque_handle).and_modify','parent>=i','inherited[parent]','!seen.insert(&edits[n].anchor.opaque_handle)'):
        c.require(owner.count(marker)==1,'ACTUAL_ANCHORS_AMBIGUITY_DUPLICATES_AND_ONE_FORWARD_PARENT_MAP_NOT_FIRST_NODE_FALLBACK')
    for marker in('SelectorSnapshot::build(','owners::resolve(v,p)?','Selector::by_logical_id(owner)','OperationPlanCompiler::new(limits)',
        'max_total_argument_bytes:8*1024*1024','max_serialized_bytes:MAX_PLAN_BYTES'):
        c.require(build.count(marker)==1,'ORIGINAL_SNAPSHOT_SELECTOR_AND_OPERATION_COMPILER_WITH_FINITE_PLAN_LIMITS')
    for marker in('self.with_verified_bytes(provider,now,','view.source.check_compiler_head(provider)?','candidate:self',
        'self.candidate.with_verified_bytes(provider,now,consume)','self.candidate.require_current_product_route(provider,now)',
        'self.candidate.verify(provider,now)?','self.length.checked_add(b.len())'):
        c.require(model.count(marker)==1,'ONE_CURRENT_SOURCE_OWNER_MOVE_BOUNDED_METADATA_AND_ORIGINAL_FRESH_BYTE_ROUTE_GUARDS')
    c.require('ImportedSourcePackage::import'not in model+owner+build+q.text(PROJECTION),'NO_NEW_PACKAGE_REIMPORT_OR_SEARCH_COMPILER_REPLAY')
    variants=re.findall(r'Receipt::([A-Za-z]+)\(',q.text(PROJECTION))
    c.require(len(variants)==len(set(variants))==16,'ALL16_TYPED_MUTATION_RECEIPT_PROJECTIONS_NOT_SERIALIZED_GUESSING')


def expected(q):
    text=q.text(TEST);ordinary=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)
    generated=re.findall(r'^compiled_case!\(([A-Za-z0-9_]+),',text,re.M)
    units=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(UNIT))
    c.require(len(ordinary)==14 and len(generated)==16 and len(set(ordinary+generated))==30 and len(units)==len(set(units))==6,'EXACT30_PRODUCT_AND6_ACTUAL_OWNER_UNIT_IDENTITIES')
    return {UNIT_PREFIX+n for n in units},{PREFIX+n for n in ordinary+generated}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SEARCH_COMPILER_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_SEARCH_OPERATION_COMPILER_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,trusted_route_full_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(BASELINE)
        c.require(q.snapshots[BASELINE]['sha256']=='e2c57b62d8e165d39709e1aaa60bceeb40ad9dfa5884190b6f7f05c3db67a974'
            and baseline['state']=='PASS_STYLE_SPLICE_INVENTORY12_AFFECTED38_NOT_COMPILED_OPERATION_NATIVE_TRANSACTION_OR_GATE'
            and baseline['cleanup']and baseline['fresh_inputs']==baseline['final_fresh_hashes']==737,'EXACT210_CURRENT_SOURCE_SPLICE_PRODUCT50_AND_FRESH_CLOSURE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'COMPILER_MODELS_TESTS_AND_MACROS_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_MATCHERS_COMPILERS_WRITERS_PRODUCTS_TESTS_FIXTURES_AND_SECURITY_UNCHANGED')
        inverse(q,old);units,products=expected(q)
        print(json.dumps(dict(state='SOURCE_SEARCH_OPERATION_COMPILER_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=30,owner_unit_cases=6,old50_and_official249_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('six_actual_source_owner_refusal_units',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--lib','--message-format=short','--',UNIT_PREFIX,'--test-threads=1'],units,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],units)
        harness.run_one('thirty_actual_sixteen_family_compiled_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],products,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],products);q.finish();guard.check(force=True)
        row.update(state='PASS_SIXTEEN_FAMILY_SOURCE_OPERATION_COMPILER30_OWNER6_NOT_TRUSTED_ROUTE_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=30,actual_owner_unit_cases=6,total_executed_cases=36,
            old50_products_reexecuted=False,original16_parsers_source_security_delivery_and_route_bodies_inverse_verified=True,
            one_borrowed_source_graph_selected_part_parent_maps_original_snapshot_and_operation_compiler=True,
            no_candidate_clone_reimport_matcher_replay_or_invented_owner=True,
            next_work='real_target_registry_route_manifest_and_durable_transaction_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_OPERATION_COMPILER_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_OPERATION_COMPILER_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())

