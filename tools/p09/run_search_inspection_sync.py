"""Declared inspection code/result/docs closure, without test or Native replay."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
ROOT='implementation/p09/evidence/p09-361-'
OUTPUT=ROOT+'search-inspection-sync050.v1.json'
PASSED=ROOT+'search-inspection-components048.v1.json'
BASELINE=ROOT+'scoped-search-product-components045.v1.json'
FAILURE=ROOT+'search-inspection-components047.v1.json'
NEW={'crates/hwpx-package/src/document_import/search/inspection.rs','crates/hwpx-package/tests/document_import_search_inspection.rs'}
CHANGED={'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/scope.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'}
RETAINED={'crates/hwpx-package/tests/document_import_search.rs','crates/hwpx-package/tests/document_import_search_scope.rs',
    'crates/hwpx-package/src/document_import/forms.rs','crates/hwpx-package/src/document_import/search/extract.rs',
    'crates/hwpx-package/src/document_import/search/normalization.rs','crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider.rs'}
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-search-product-request-v1.md','protocol/migrations/p09-source-search-inspection-v2.md')
OFFICIAL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/'


def inverse(text,pin,label):
    normalized=text.replace('\r\n','\n')
    c.require(pin['sha256']in{hashlib.sha256(normalized.encode()).hexdigest(),hashlib.sha256(normalized.replace('\n','\r\n').encode()).hexdigest()},label)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_INSPECTION_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SEARCH_INSPECTION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed,baseline,failure=q.json(PASSED),q.json(BASELINE),q.json(FAILURE)
        previous_sync=q.json(ROOT+'search-inspection-sync049.v1.json')
        c.require(previous_sync['state']=='FAILED_SEARCH_INSPECTION_SYNC'and previous_sync['error_code']=='INSPECTION_PROFILE_SEMANTIC_AND_GATE_BOUNDARIES'
            and not previous_sync['actual_Cargo_or_tests']and previous_sync['cleanup'],'ORIGINAL_DOCUMENT_MARKER_MISMATCH_PRESERVED_WITHOUT_TEST_REPLAY')
        for name,sha in ((PASSED,'25f6409f12938e9706e53adb2f9a518d3e1213102287a03f3fdd42e4c673b5c9'),
            (BASELINE,'f0070c1d7bacd15c37e596b516b6b44b31472de03e388239ba650f676ee9e83c'),
            (FAILURE,'dfa160839bfab8e95c93c0ce46141c3a0aa8122f7bfff731c15b5a82296d96ba')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_INSPECTION_AND_BASELINE_FAILURE_RECEIPTS')
        c.require(passed['state']=='PASS_DECLARED_STYLE_STRUCTURAL_CONTROL_NINE_NEW_THIRTY_AFFECTED_FOURTEEN_PRODUCT_NOT_EFFECTIVE_STYLE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==449 and passed['cleanup']
            and passed['original_thirty_nine_test_bodies_preserved'],'EXACT_VERIFIED_INSPECTION_RESULT')
        c.require(failure['state']=='FAILED_SEARCH_INSPECTION_COMPONENTS'and failure['error_code']=='ORIGINAL_NINE_PRODUCT_TEST_BODIES_EXACT_INVERSE'
            and failure['steps']==[]and failure['cleanup'],'PRESERVED_ZERO_EXECUTION_PREFLIGHT_FAILURE')
        tested={p['path']:p for p in passed['source_pins']};old={p['path']:p for p in baseline['source_pins']}
        source_names={n for n in tested if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(source_names-set(old)==NEW,'ONLY_TWO_NEW_INSPECTION_SOURCE_FILES')
        for name in source_names-NEW-CHANGED:c.require(tested[name]==old[name],'ALL_OTHER_ORIGINAL_SOURCE_PINS_RETAINED_IN_PASS')
        for name in sorted(NEW|CHANGED|RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_INSPECTION_CODE_MATCHES_PASS')
        search=q.text('crates/hwpx-package/src/document_import/search.rs')
        wrapper=('        self.find_filtered(query,selected,None)\n    }\n'
            '    fn find_filtered(&self,query:SourceSearchQuery<\'_>,selected:Option<&BTreeSet<domain_ir::LogicalId>>,accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>)->Result<SourceSearchResult,E> {\n')
        for fragment in ('pub mod inspection;\n','    #[error("SOURCE_SEARCH_FILTER_INVALID")] Filter,\n',wrapper,
            '                if accept.is_some_and(|predicate|!predicate(&origins)){continue;}\n'):
            c.require(search.count(fragment)==1,'EXACT_ADDITIVE_MATCH_FILTER_DISPATCH');search=search.replace(fragment,'')
        limit='                if matches.len()>=query.max_results{return Err(E::Limit);}\n'
        c.require(search.count(limit)==1,'ONLY_ACCEPTED_MATCH_LIMIT_MOVED_AFTER_PREDICATE');search=search.replace(limit,'')
        search=search.replace('            for found in expression.find_iter(&block.text) {\n','            for found in expression.find_iter(&block.text) {\n'+limit)
        inverse(search,old['crates/hwpx-package/src/document_import/search.rs'],'ORIGINAL_UNFILTERED_MATCHER_EXACT_INVERSE')
        scope=q.text('crates/hwpx-package/src/document_import/search/scope.rs')
        prefix=('        let(receipt,selected)=self.resolve_search_scope(scope)?;\n'
            '        let result=self.find_selected(query,Some(&selected))?;\n'
            '        let scoped=ScopedSourceSearchResult {profile:SCOPED_SOURCE_SEARCH_PROFILE,scope:receipt,result};\n'
            '        let mut count=Output {bytes:None,length:0,maximum:self.limits.0.result_bytes};\n'
            '        serde_json::to_writer(&mut count,&scoped).map_err(|_|E::Output)?;Ok(scoped)\n    }\n'
            '    pub(super) fn resolve_search_scope(&self,scope:SourceSearchScope<\'_>)->Result<(SourceSearchScopeReceipt,BTreeSet<LogicalId>),E> {\n')
        c.require(scope.count(prefix)==1,'SINGLE_SHARED_SCOPE_RESOLUTION_EXTRACTION');scope=scope.replace(prefix,'')
        tail=('        Ok((SourceSearchScopeReceipt {kind,scope_sha256:Sha256::digest(binding).into(),selected_paragraphs:selected.len(),selected_blocks,\n'
            '                whole_document_visibility_qualified:false},selected))\n')
        original=('        let result=self.find_selected(query,Some(&selected))?;\n'
            '        let scoped=ScopedSourceSearchResult {profile:SCOPED_SOURCE_SEARCH_PROFILE,\n'
            '            scope:SourceSearchScopeReceipt {kind,scope_sha256:Sha256::digest(binding).into(),selected_paragraphs:selected.len(),selected_blocks,\n'
            '                whole_document_visibility_qualified:false},result};\n'
            '        let mut count=Output {bytes:None,length:0,maximum:self.limits.0.result_bytes};\n'
            '        serde_json::to_writer(&mut count,&scoped).map_err(|_|E::Output)?;Ok(scoped)\n')
        c.require(scope.count(tail)==1,'SINGLE_SHARED_SCOPE_RECEIPT_RETURN');scope=scope.replace(tail,original)
        inverse(scope,old['crates/hwpx-package/src/document_import/search/scope.rs'],'ORIGINAL_SCOPE_RESOLUTION_AND_FORM_PROOF_EXACT_INVERSE')
        product=q.text('crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs')
        retained=product.split('// Additive v2 inspection cases;',1)[0]
        c.require(retained.endswith('\n\n'),'ONE_ADDED_PRODUCT_TEST_SEPARATOR')
        inverse(retained[:-1],old['crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'],'NINE_ORIGINAL_V1_PRODUCT_TEST_BODIES_EXACT_INVERSE')
        core=set()
        for name in ('document_import_search','document_import_search_scope','document_import_search_inspection'):
            core|=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+name+'.rs')))
        product_names={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',product)}
        c.require(len(core)==39 and len(product_names)==14 and len(passed['steps'])==2,'EXACT_FIFTY_THREE_CASE_INVENTORY')
        for step,expected in zip(passed['steps'],(core,product_names),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])
                and step['diagnostics']==[],'ALL_FIFTY_THREE_CASES_PASS_NO_DIAGNOSTICS')
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_INSPECTION_JOBS_TERMINAL_EMPTY_CLOSED')
        for name in ('runType.cpp','ctrl.cpp','t.cpp'):q.pin(OFFICIAL+name);c.require(q.snapshots[OFFICIAL+name]==tested[OFFICIAL+name],'REVIEWED_CACHED_TAG_MAPS_UNCHANGED')
        c.require(passed['cached_official_tag_site_counts']==dict(Run=28,Control=15,Text=14),'COMPLETE_CACHED_FIFTY_SEVEN_PARENT_TAG_PLACEMENTS')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('총 53개 PASS','449 fresh/final449','286개','57개 부모/태그','서식 정의의 실제 결속','047','v2 제품 요청'):
            c.require(marker in progress,'INSPECTION_PROGRESS_RESULTS_AND_LIMITS')
        profile=q.text(DOCS[3])
        for marker in ('Missing values remain missing','28 run-site','15 ctrl-site','14 text-site','does not rerun the search','449 fresh/final449','P09/A12/A13 OPEN'):
            c.require(marker in profile,'INSPECTION_PROFILE_SEMANTIC_AND_GATE_BOUNDARIES')
        c.require('p09-source-search-inspection-v2.md'in q.text(DOCS[2]),'LEGACY_AND_V2_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 범위별 원본 검색 제품 경로',1)[0]
        for marker in ('53pass','449fresh/final449','58.33%','21.0979%','4.9645%','잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_INSPECTION_RESULT_AND_UNCHANGED_GATE')
        q.pin('tools/p09/run_search_inspection_components.py');c.require(q.snapshots['tools/p09/run_search_inspection_components.py']==tested['tools/p09/run_search_inspection_components.py'],'VERIFIED_INSPECTION_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SEARCH_INSPECTION_CODE_DOCUMENT_SYNC_FIFTY_THREE_CASES_NOT_EFFECTIVE_STYLE_OR_GATE',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,distinct_component_tests=53,original_matcher_scope_and_v1_test_bodies_inverse_verified=True,
            original_other_source_pins_preserved=True,whole_449_input_inventory_reaudited=False,
            effective_style_hidden_control_semantics_or_full_search_qualified=False,next_work='Bind_declared_style_references_to_source_definitions_and_visibility_coverage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'INSPECTION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSPECTION_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
