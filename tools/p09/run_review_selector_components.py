"""16 new review/window compiler cases +36 affected source cases, no stored/Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_scope_product_components as prior
base=prior.base
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
audit=base.prior.prior.base.prior.audit
OUTPUT='implementation/p09/evidence/p09-361-review-selector-components094.v1.json'
CORE=prior.CORE
INVENTORY=prior.INVENTORY
REVIEW='crates/hwpx-package/src/document_import/search/reviews.rs'
LITERAL='crates/hwpx-package/src/document_import/search/replacement/atoms/review.rs'
SCOPE=REVIEW[:-3]+'/selector.rs'
COMPILER=LITERAL[:-3]+'/selector.rs'
TESTS=('document_import_review_selector','document_import_review_selector_replacement')
OLD=('document_import_search_selector','document_import_search_selector_inventory','document_import_search_review_text','document_import_search_review_replacement')
FIXTURE='crates/hwpx-package/tests/support/review_scope_fixture.rs'
NEW={SCOPE,COMPILER,FIXTURE}|{'crates/hwpx-package/tests/'+n+'.rs'for n in TESTS}
CHANGED={CORE,INVENTORY,REVIEW,LITERAL}
SCOPE_BRIDGE=('        self.resolve_index_selector_with_nodes(selector,None)\n    }\n'
    "    pub(in crate::document_import::search) fn resolve_index_selector_with_nodes(&self,selector:SourceIndexScopeSelector<'_>,supplemental:Option<&SupplementalNodes>)->Result<(SourceIndexScopeReceipt,Windows),E> {\n")
SCOPE_EXTRA=('                if let Some(extra)=supplemental {for (id,anchor) in extra {\n'
    '                    if catalog.len()>=self.limits.0.blocks{return Err(E::Limit);}\n'
    '                    let resolved=self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;let element=resolved.element().ok_or(E::Mapping)?;\n'
    '                    let xml=resolved.part().xml().ok_or(E::Source)?;let stop=xml.tokens()[element.end_token().unwrap_or(element.start_token())].span().end();\n'
    '                    if catalog.insert(id.clone(),(resolved.part().path().as_str().to_owned(),element.start_tag_span().start(),stop)).is_some(){return Err(E::Mapping);}\n'
    '                }}\n')
INVENTORY_BRIDGE=('        self.scope_inventory_with_nodes(None)\n    }\n'
    '    pub(in crate::document_import::search) fn scope_inventory_with_nodes(&self,supplemental:Option<&SupplementalNodes>)->Result<SourceScopeInventory,E> {\n')
INVENTORY_EXTRA=('        if let Some(extra)=supplemental {for (id,anchor) in extra {\n'
    '            if nodes.len()>=self.limits.0.blocks{return Err(E::Limit);}\n'
    '            self.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;\n'
    '            if nodes.insert(id.clone(),SourceIndexNodeDescriptor {node_id:id.clone(),source_handle:anchor.opaque_handle.clone()}).is_some(){return Err(E::Mapping);}\n'
    '        }}\n')
CALL=('        compile_review_found(index.source_index(),&fields,&review,rebuilt.source().original.as_ref(),\n'
    '            ReviewMatches {result:found.matches(),scope_sha:found.scope_receipt().scope_sha256,request_sha:found.request_sha256(),regions:found.match_regions()},\n'
    '            policy,replacement,run_policy,limits,writer)\n')
HELPER_HEADER=("struct ReviewMatches<'a> {result:&'a crate::document_import::search::SourceSearchResult,scope_sha:[u8;32],request_sha:[u8;32],regions:&'a [SourceTextRegion]}\n"
    "fn compile_review_found(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,review:&ImportedDocumentReviewBodies<'_>,fresh:&[u8],found:ReviewMatches<'_>,\n"
    '    policy:SourceReviewTextPolicy,replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceReviewLiteralCandidate,E> {\n')


def inventory(check):return prior.inventory(check)|{'crates/hwpx-package/tests/'+n+'.rs'for n in TESTS}


def inverse(q,old):
    for name,changes in ((CORE,((SCOPE_BRIDGE,''),(SCOPE_EXTRA,''),('pub(in crate::document_import::search) type SupplementalNodes=BTreeMap<LogicalId,SourceAnchorHandle>;\n',''))),
        (INVENTORY,((INVENTORY_BRIDGE,''),(INVENTORY_EXTRA,''))),(REVIEW,(('pub mod selector;\n',''),))):
        text=q.text(name)
        for current,previous in changes:c.require(text.count(current)==1,'ONLY_OPTIONAL_SUPPLEMENTAL_NODES_OR_ADDITIVE_REVIEW_MODULE');text=text.replace(current,previous)
        audit.inverse(text,old[name],'ORIGINAL_NONE_SCOPE_INVENTORY_AND_REVIEW_PROJECTION_BODIES_EXACT_INVERSE')
    text=q.text(LITERAL);c.require(text.count('pub mod selector;\n')==1 and text.count(CALL)==1,'ONE_NEW_SELECTOR_AND_QUALIFIED_REVIEW_COMPILER_EXTRACTION')
    text=text.replace('pub mod selector;\n','');start=text.index(HELPER_HEADER);end=text.index('pub(super) struct ReviewWriteContext',start);helper=text[start:end]
    c.require(helper.startswith(HELPER_HEADER)and helper.endswith('}\n'),'EXACT_SHARED_REVIEW_COMPILER_HELPER_BOUNDARIES')
    body=helper[len(HELPER_HEADER):-2]
    for current,previous in (('ReviewWriteContext::new(index.original.source(),fields,review,policy)','ReviewWriteContext::new(original.source(),&fields,&review,policy)'),
        ('lower_found(index,fields,fresh,found.result,found.scope_sha,replacement,run_policy,writer,Some(&context))',
         'lower_found(index.source_index(),&fields,rebuilt.source().original.as_ref(),found.matches(),\n        found.scope_receipt().scope_sha256,replacement,run_policy,writer,Some(&context))'),
        ('review_search_request_sha256:found.request_sha,match_regions:found.regions.to_vec()',
         'review_search_request_sha256:found.request_sha256(),match_regions:found.match_regions().to_vec()')):
        c.require(body.count(current)==1,'ONLY_TYPED_MATCH_METADATA_OR_ORIGINAL_INDEX_PARAMETER_SUBSTITUTION');body=body.replace(current,previous)
    restored=''.join('    '+line+'\n'for line in body.splitlines())
    text=text[:start]+text[end:];text=text.replace(CALL,restored)
    audit.inverse(text,old[LITERAL],'ORIGINAL_V3_REVIEW_CONTEXT_COMPILER_FLAGS_LIMITS_WRITER_AND_READBACK_BODIES_EXACT_INVERSE')


def test_names(q,target):return set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+target+'.rs')))


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SELECTOR_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_SELECTOR_COMPONENTS',steps=[],actual_Hangul_or_COM=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='98214dc9224d34ad162616ea8a8184078332147401c2574e5e8cad8177f33c7e'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==47,'EXACT_PREVIOUS_SCOPE_V5_FORTY_SEVEN_PASSES')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_REVIEW_SCOPE_COMPILER_TEST_FIXTURE_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_MATCHER_PROOF_STORED_PRODUCT_OR_EXISTING_TEST_CHANGE')
        inverse(q,old);groups=[test_names(q,n)for n in TESTS+OLD]
        c.require(tuple(map(len,groups))==(8,8,12,4,8,12),'EXACT_SIXTEEN_NEW_THIRTY_SIX_AFFECTED_CORE_CASES')
        expected=set().union(*groups);c.require(len(expected)==52,'FIFTY_TWO_DISTINCT_EXPECTED_CORE_CASES')
        args=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        for name in TESTS+OLD:args.extend(['--test',name])
        args.extend(['--','--test-threads=1'])
        print(json.dumps(dict(state='REVIEW_SELECTOR_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=16,affected_cases=36,
            original_compiler_and_none_paths_inverse_verified=True)),flush=True)
        harness.run_one('sixteen_review_scope_literal_thirty_six_affected_core_cases',args,expected,guard,audit.environment(),row,observe_capture=base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_SELECTOR_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_SELECTOR_SIXTEEN_NEW_THIRTY_SIX_AFFECTED_NOT_STORED_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_review_scope_cases=8,new_selector_literal_cases=8,affected_cases=36,total_executed_cases=52,
            supplemental_node_ids_from_bound_original_review_graph=True,policy_exclusion_before_window_matching_and_limits=True,
            literal_compiler_reuses_exact_source_matches_windows_protection_and_readback=True,whole_paragraph_expansion_or_field_cache_grant_added=False,
            stored_json_or_native_qualification_added=False,previous_stored_product_cases_reexecuted=False,
            next_work='Stored_review_selector_and_literal_window_candidates_with_strict_product_requests')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SELECTOR_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SELECTOR_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
