"""Eight exact-window style combinations plus27 affected core cases, no stored/Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_navigation_components as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-selector-styles-components103.v1.json'
REVIEW=prior.REVIEW
STYLE=REVIEW[:-3]+'/styles.rs'
INSPECT='crates/hwpx-package/src/document_import/search/inspection.rs'
DEFINITION=INSPECT[:-3]+'/definitions.rs'
TEST='crates/hwpx-package/tests/document_import_selector_styles.rs'
BUNDLE='crates/hwpx-package/tests/selector_styles_bundle.rs'
NEW={STYLE,TEST,BUNDLE};CHANGED={REVIEW,INSPECT,DEFINITION}
TARGETS=('document_import_selector_styles','document_import_search_inspection','document_import_search_definitions','document_import_review_selector')
MODULES=('selector_styles','declared_styles','definition_styles','review_selector')
DECLARED_HELPER=('    pub(in crate::document_import::search) fn accepts_declared_points(&self,points:&BTreeSet<usize>,filter:SourceDeclaredStyleFilter)->bool {\n'
    '        !points.is_empty()&&points.iter().all(|p|filter.matches(self.styles[self.text.points[*p].segment]))\n    }\n')
DEFINITION_HELPER=('    pub(in crate::document_import::search) fn accepts_points(&self,points:&BTreeSet<usize>,filter:SourceDefinitionStyleFilter)->bool {\n'
    '        let text=self.inspection.text;!points.is_empty()&&points.iter().all(|p|self.accepts(self.refs[text.points[*p].segment],filter))\n    }\n')
RESOLVED='struct ResolvedReviewWindows {scope:SourceIndexScopeReceipt,windows:BTreeMap<usize,(usize,usize)>,searched_paragraphs:usize,hidden:usize,memo:usize}\n'
RETURN='        Ok(ResolvedReviewWindows {scope,windows:eligible,searched_paragraphs:paragraphs.len(),hidden:hidden.len(),memo:memo.len()})\n'
ORIGINAL_MATCH=('        let result=self.base.index.find_windowed(query,None,None,Some(&eligible))?;\n'
    '        let mut hash=BindingHash {length:0,maximum:self.base.limits.0.result_bytes,sha:Sha256::new()};\n'
    '        serde_json::to_writer(&mut hash,&(REVIEW_SELECTOR_SEARCH_PROFILE,self.base.index.receipt.index_sha256,scope.scope_sha256,query,policy)).map_err(|_|E::Output)?;\n')


def inventory(check):return prior.inventory(check)|{TEST,BUNDLE}


def inverse(q,old):
    for name,helper,current,previous in((INSPECT,DECLARED_HELPER,
        'let accept=|points:&BTreeSet<usize>|self.accepts_declared_points(points,filter);',
        'let accept=|points:&BTreeSet<usize>|!points.is_empty()&&points.iter().all(|p|filter.matches(self.styles[self.text.points[*p].segment]));'),
        (DEFINITION,DEFINITION_HELPER,'let accept=|points:&BTreeSet<usize>|self.accepts_points(points,filter);',
        'let accept=|points:&BTreeSet<usize>|!points.is_empty()&&points.iter().all(|p|self.accepts(self.refs[text.points[*p].segment],filter));')):
        text=q.text(name);c.require(text.count(helper)==1 and text.count(current)==1,'ONLY_ORIGINAL_POINT_PREDICATE_EXTRACTED_WITH_SAME_NFC_ALL_CONTRIBUTOR_RULE')
        audit.inverse(text.replace(helper,'').replace(current,previous),old[name],'WHOLE_ORIGINAL_STYLE_INDEX_DEFINITIONS_PREDICATES_MATCHER_LIMITS_AND_NAVIGATION_EXACT_INVERSE')
    text=q.text(REVIEW)
    for addition in('pub mod styles;\n',RESOLVED):c.require(text.count(addition)==1,'ONLY_TYPED_STYLE_MODULE_AND_PRIVATE_WINDOW_AGGREGATE');text=text.replace(addition,'')
    start=text.index('    pub fn find(&self,query:SourceSearchQuery');body_start=text.index('\n',start)+1
    resolve=text.index('    fn resolve_windows',body_start);finish=text.index('    fn finish_resolved',resolve);end=text.index('\n}\nfn collect_nodes',finish)
    selected=text[text.index('\n',resolve)+1:finish]
    c.require(selected.endswith('    }\n')and selected.count(RETURN)==1,'SAME_SCOPE_RESOLVER_AND_POLICY_EXCLUSION_LOOP_EXTRACTED_ONCE')
    selected=selected[:-len('    }\n')].replace(RETURN,'')
    result=text[text.index('\n',finish)+1:end]
    c.require(result.endswith('    }'),'EXACT_ORIGINAL_RESULT_ASSEMBLY_HELPER_BOUNDARY');result=result[:-len('    }')]
    for current,previous in(('SourceReviewSelectorResult {profile,','SourceReviewSelectorResult {profile:REVIEW_SELECTOR_SEARCH_PROFILE,'),
        ('scope:selected.scope,policy,','scope,policy,'),('request_sha256,match_regions:','request_sha256:hash.sha.finalize().into(),match_regions:'),
        ('searched_paragraphs:selected.searched_paragraphs,searched_blocks:selected.windows.len(),excluded_hidden_paragraphs:selected.hidden,excluded_memo_paragraphs:selected.memo,',
        'searched_paragraphs:paragraphs.len(),searched_blocks:eligible.len(),excluded_hidden_paragraphs:hidden.len(),excluded_memo_paragraphs:memo.len(),')):
        c.require(result.count(current)==1,'ONLY_PREVALIDATED_WINDOW_COUNTS_AND_ORIGINAL_PROFILE_DIGEST_PARAMETERS');result=result.replace(current,previous)
    restored=text[:body_start]+selected+ORIGINAL_MATCH+result+'    }'+text[end:]
    audit.inverse(restored,old[REVIEW],'WHOLE_ORIGINAL_REVIEW_FIND_RESOLUTION_EXCLUSIONS_HASH_RESULT_BOUNDS_AND_NATIVE_FLAGS_EXACT_INVERSE')


def expected(q):
    groups=[]
    for target,module in zip(TARGETS,MODULES,strict=True):groups.append({module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+target+'.rs'))})
    c.require(tuple(map(len,groups))==(8,9,10,8),'EXACT_EIGHT_NEW_TWENTY_SEVEN_AFFECTED_CORE_IDENTITIES');return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_STYLES_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_STYLES_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_control_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='01bde329542d9c59a77e9457a7e74af803c4fed0bf99e3d0085e49c4a3276fd2'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==33 and previous['cleanup'],'EXACT_PREVIOUS_THIRTY_THREE_NAVIGATION_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.prior.prior.base.prior.base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_NEW_STYLE_MODULE_AND_TWO_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_MATCHER_SELECTOR_WRITER_HEADER_STORED_PRODUCT_NAV_ENGINE_OR_OLD_TEST_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SELECTOR_STYLES_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=8,affected_cases=27,test_binaries=1)),flush=True)
        harness.run_one('eight_selector_style_and_twenty_seven_affected_core_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','selector_styles_bundle','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.prior.prior.prior.base.base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_SELECTOR_STYLES_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_STYLE_EIGHT_NEW_TWENTY_SEVEN_AFFECTED_NOT_STORED_CONTROL_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=8,affected_cases=27,total_executed_cases=35,
            previous_thirty_three_navigation_and_other_completed_suites_reexecuted=False,original_predicates_review_resolution_exclusion_hash_and_bounds_inverse_verified=True,
            all_four_selector_windows_and_policy_before_style_match_caps=True,effective_cascade_or_control_coordinate_semantics_inferred=False,
            next_work='Stored_and_strict_product_binding_of_review_selector_styles_then_exact_control_scope_projection')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_STYLES_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_STYLES_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
