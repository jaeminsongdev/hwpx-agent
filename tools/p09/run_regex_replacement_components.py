"""Sixteen capture/template atom-writer cases and72 affected original core cases in one bounded binary."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_control_product_components as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-regex-replacement-components112.v1.json'
SEARCH='crates/hwpx-package/src/document_import/search.rs';CAPTURES=SEARCH[:-3]+'/captures.rs'
ATOMS='crates/hwpx-package/src/document_import/search/replacement/atoms.rs';REGEX=ATOMS[:-3]+'/regex.rs';TEMPLATE=REGEX[:-3]+'/template.rs'
REVIEW=ATOMS[:-3]+'/review.rs';SELECTOR='crates/hwpx-package/src/document_import/search/reviews/selector.rs'
TEST='crates/hwpx-package/tests/document_import_regex_replacement.rs';BUNDLE='crates/hwpx-package/tests/regex_replacement_bundle.rs'
NEW={CAPTURES,REGEX,TEMPLATE,TEST,BUNDLE};CHANGED={SEARCH,ATOMS,REVIEW,SELECTOR}
SEARCH_WRAPPER=('        self.find_windowed_captured(query,selected,accept,windows,None)\n    }\n'
    '    fn find_windowed_captured(&self,query:SourceSearchQuery<\'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,\n'
    '        windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>,mut capture:Option<&mut dyn captures::CaptureSink>)->Result<SourceSearchResult,E> {\n')
REVIEW_WRAPPER=('        self.find_with_captures(query,selector,policy,None)\n    }\n'
    '    pub(in crate::document_import::search) fn find_with_captures(&self,query:SourceSearchQuery<\'_>,selector:SourceIndexScopeSelector<\'_>,policy:SourceReviewTextPolicy,capture:Option<&mut dyn crate::document_import::search::captures::CaptureSink>)->Result<SourceReviewSelectorResult,E> {\n')
ATOM_WRAPPER=('    lower_found_with_expansions(index,fields,fresh,found,scope_sha256,replacement,run_policy,writer,review,None)\n}\n'
    'struct RegexExpansions<\'a> {values:&\'a [String],sha256:[u8;32],bytes:usize}\n'
    'fn lower_found_with_expansions(index:&SourceTextIndex<\'_>,fields:&ImportedDocumentFields<\'_>,fresh:&[u8],found:&super::super::SourceSearchResult,scope_sha256:[u8;32],replacement:&str,\n'
    '    run_policy:SourceReplacementRunPolicy,writer:WriterLimits,review:Option<&review::ReviewWriteContext>,expansions:Option<&RegexExpansions<\'_>>)->Result<(SourceLiteralTextAtomCandidate,Option<review::ReviewBodyImportReceipt>),E> {\n')


def inventory(check):return prior.inventory(check)|{TEST,BUNDLE}


def one(text,current,previous,label):
    c.require(text.count(current)==1,label);return text.replace(current,previous)


def inverse(q,old):
    text=q.text(SEARCH)
    for addition in('mod captures;\n',SEARCH_WRAPPER,'        if let Some(sink)=capture.as_deref_mut(){sink.compiled(&expression)?;}\n',
        '                if let Some(sink)=capture.as_deref_mut(){sink.matched(scanned.captures().ok_or(E::Mapping)?)?;}\n'):
        text=one(text,addition,'','ONLY_OPTIONAL_CAPTURE_SINK_WRAPPER_AND_CALLBACKS')
    text=one(text,'            for scanned in captures::scan(&expression,window,capture.is_some()) {\n                let found=scanned.whole().ok_or(E::Mapping)?;\n',
        '            for found in expression.find_iter(window) {\n','SAME_ORIGINAL_NONCAPTURE_MATCH_ITERATOR_WITHOUT_ALLOCATION')
    audit.inverse(text,old[SEARCH],'WHOLE_ORIGINAL_PATTERN_BUDGET_WINDOWS_MATCH_PROVENANCE_PREDICATES_CAPS_HASH_AND_OUTPUT_EXACT_INVERSE')
    text=one(q.text(SELECTOR),REVIEW_WRAPPER,'','ONLY_OPERATION_LOCAL_CAPTURE_FORWARDER_NOT_NEW_SCOPE_RESOLVER')
    text=one(text,'self.base.index.find_windowed_captured(query,None,None,Some(&selected.windows),capture)?;',
        'self.base.index.find_windowed(query,None,None,Some(&selected.windows))?;','SAME_ORIGINAL_REVIEW_SCOPE_POLICY_HASH_AND_RESULT_ASSEMBLY')
    audit.inverse(text,old[SELECTOR],'WHOLE_ORIGINAL_REVIEW_TEXT_STYLE_CONTROL_SCOPE_ENGINE_EXACT_INVERSE')
    text=q.text(ATOMS)
    for addition in('pub mod regex;\n',ATOM_WRAPPER,'    if expansions.is_some_and(|e|e.values.len()!=found.matches().len()){return Err(E::Selection);}\n'):
        text=one(text,addition,'','ONLY_PER_OCCURRENCE_EXPANSION_COMPILER_WRAPPER')
    for current,previous in(
        ('    for (ordinal,m) in found.matches().iter().enumerate() {\n        let replacement=expansions.map_or(replacement,|e|e.values[ordinal].as_str());\n','    for m in found.matches() {\n'),
        ('profile:if expansions.is_some(){regex::SOURCE_REGEX_TEXT_ATOM_PROFILE}else if review.is_some()','profile:if review.is_some()'),
        ('replacement_sha256:expansions.map_or_else(||Sha256::digest(replacement.as_bytes()).into(),|e|e.sha256),replacement_bytes:expansions.map_or(replacement.len(),|e|e.bytes),run_policy,',
            'replacement_sha256:Sha256::digest(replacement.as_bytes()).into(),replacement_bytes:replacement.len(),run_policy,')):
        text=one(text,current,previous,'ONLY_VARIABLE_VALUES_AND_EXPLICIT_REGEX_RECEIPT_IDENTITY_ADDED')
    audit.inverse(text,old[ATOMS],'WHOLE_ORIGINAL_NFC_CONTIGUITY_OVERLAP_FIELD_PROTECTION_ATOM_EDIT_WRITER_READBACK_AND_LIMITS_EXACT_INVERSE')
    text=one(q.text(REVIEW),'    pub(super) fn new(source:&ImportedSourcePackage,','    fn new(source:&ImportedSourcePackage,','ONLY_SIBLING_CONTEXT_CONSTRUCTOR_VISIBILITY')
    audit.inverse(text,old[REVIEW],'WHOLE_ORIGINAL_MEMO_PAYLOAD_CARVING_PARENT_FIELDS_AND_REVIEW_READBACK_UNCHANGED')
    text=q.text(REGEX)
    c.require(text.count('ImportedDocumentFields::import(original)')==1 and text.count('ImportedDocumentReviewBodies::import_bound_fields(original,&fields)')==1
        and text.count('SourceReviewScopeIndex::from_review(original,&review,limits)')==1 and text.count('index.find_with_captures(query,selector,policy,Some(&mut collector))')==1,
        'ONE_ORIGINAL_FIELD_REVIEW_INDEX_AND_REGEX_CAPTURE_PASS_NOT_QUERY_PER_MATCH')


def expected(q):
    paths=('document_import_regex_replacement','document_import_search','document_import_search_atom_replacement','document_import_search_review_replacement',
        'document_import_review_selector_replacement','document_import_review_selector','document_import_selector_styles')
    modules=('regex_replacement','source_search','atom_literal','review_literal','selector_literal','review_selector','selector_styles')
    groups=[{module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+name+'.rs'))}for name,module in zip(paths,modules,strict=True)]
    c.require(tuple(map(len,groups))==(16,24,12,12,8,8,8),'EXACT_SIXTEEN_NEW_SEVENTY_TWO_AFFECTED_CORE_IDENTITIES');return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_REPLACEMENT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_REPLACEMENT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_zero_width_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='4965fe2b5d8e247f4ab7849a7aee4e1e2fb7d2cb980747f85d72cd67a8d383f3'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==46 and previous['cleanup'],'EXACT_PREVIOUS_FORTY_SIX_CONTROL_PRODUCTS_RETAINED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_CAPTURE_TEMPLATE_MODULES_AND_TWO_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_STORED_PRODUCT_WRITER_PATCH_PROTECTION_GEOMETRY_OR_EXISTING_TEST_INPUT_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='REGEX_REPLACEMENT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=16,affected_cases=72,test_binaries=1)),flush=True)
        harness.run_one('sixteen_regex_candidates_seventy_two_original_core_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_replacement_bundle','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_REGEX_REPLACEMENT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_REPLACEMENT_SIXTEEN_NEW_SEVENTY_TWO_AFFECTED_NOT_STORED_PRODUCT_ZERO_WIDTH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=16,affected_cases=72,total_executed_cases=88,
            previous_forty_six_control_products_and_unaffected_suites_reexecuted=False,original_matcher_literal_compiler_and_review_context_inverse_verified=True,
            one_regex_pass_and_one_original_protected_writer_for_variable_capture_expansions=True,all_four_selector_scopes_and_explicit_body_policies_bound=True,
            next_work='Current_stored_and_strict_product_binding_of_regex_capture_candidates_then_remaining_full_contract_and_zero_width_insertions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_REPLACEMENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_REPLACEMENT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
