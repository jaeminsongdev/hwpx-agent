"""Four source selector forms:12 new plus38 affected matcher/scope/review cases, not Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_literal_product_components as prior
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-search-selector-components090.v1.json'
PRIOR=prior.OUTPUT
CORE='crates/hwpx-package/src/document_import/search.rs'
MODULE=CORE[:-3]+'/selector.rs'
TEST='crates/hwpx-package/tests/document_import_search_selector.rs'
NEW={MODULE,TEST};CHANGED={CORE}
TARGETS=('document_import_search_selector','document_import_search','document_import_search_scope','document_import_search_review_text')
BRIDGE=('        self.find_windowed(query,selected,accept,None)\n    }\n'
    "    fn find_windowed(&self,query:SourceSearchQuery<'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,\n"
    '        windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>)->Result<SourceSearchResult,E> {\n')
WINDOW=('            let (offset,window)=if let Some(windows)=windows {\n'
    '                let Some(&(a,b))=windows.get(&block_index)else{continue};\n'
    '                let start=*block.offsets.get(a).ok_or(E::Mapping)?;let end=*block.offsets.get(b).ok_or(E::Mapping)?;\n'
    '                if start>end{return Err(E::Mapping);}(start,block.text.get(start..end).ok_or(E::Mapping)?)\n'
    '            }else{(0,block.text.as_str())};\n'
    '            for found in expression.find_iter(window) {\n')


def inventory(check):return prior.inventory(check)|{TEST}


def inverse(q,old):
    text=q.text(CORE)
    for current,previous in (('pub mod selector;\n',''),(BRIDGE,''),(WINDOW,'            for found in expression.find_iter(&block.text) {\n'),
        ('binary_search(&(offset+found.start()))','binary_search(&found.start())'),('binary_search(&(offset+found.end()))','binary_search(&found.end())')):
        c.require(text.count(current)==1,'ONLY_ADDITIVE_SELECTOR_AND_OPTIONAL_PREMATCH_WINDOW_EXTRACTION');text=text.replace(current,previous)
    prior.prior.base.prior.audit.inverse(text,old[CORE],'ORIGINAL_MATCHER_PROVENANCE_NFC_FILTER_LIMIT_AND_RESULT_BODY_EXACT_INVERSE')


def test_names(q,target):return set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+target+'.rs')))


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_SELECTOR_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_SEARCH_SELECTOR_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search_selector_product_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='3905c914aea2a4f55b241675b7fa120615a0530b619c9763979b0dc80cd392c4'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==35,'EXACT_PREVIOUS_PRODUCT_THIRTY_FIVE_PASS_RECORD')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_SOURCE_SELECTOR_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_PROOF_REVIEW_PROVIDER_PRODUCT_OR_OLD_TEST_CHANGE')
        inverse(q,old);groups=[test_names(q,t)for t in TARGETS]
        c.require(tuple(map(len,groups))==(12,24,6,8),'EXACT_TWELVE_NEW_THIRTY_EIGHT_AFFECTED_SOURCE_CASES')
        expected=set().union(*groups);c.require(len(expected)==50,'NO_DUPLICATE_CASE_NAMES_ACROSS_FOUR_TARGETS')
        env=prior.prior.base.prior.audit.environment()
        args=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        for target in TARGETS:args.extend(['--test',target])
        args.extend(['--','--test-threads=1'])
        print(json.dumps(dict(state='SOURCE_SELECTOR_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=38,
            unchanged_original_matcher_body=True,selected_windows_before_regex=True)),flush=True)
        harness.run_one('twelve_selector_thirty_eight_affected_source_cases',args,expected,guard,env,row,observe_capture=prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_SELECTOR_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SELECTOR_TWELVE_NEW_THIRTY_EIGHT_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_source_cases=12,affected_cases=38,total_executed_cases=50,
            original_matcher_nfc_provenance_filter_limit_body_inverse_verified=True,actual_graph_section_and_node_ids_not_paragraph_aliases=True,
            selection_index_fingerprint_and_paragraph_block_scalar_boundaries_checked=True,selection_clipped_before_regex_and_word_boundaries=True,
            full_selector_revision_product_or_native_authority=False,stored_product_and_unrelated_core_suites_reexecuted=False,
            next_work='Current_stored_selector_API_revision_binding_and_explicit_source_scope_JSON')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_SELECTOR_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
