"""18 partial style candidates plus40 affected original tests, one CPU2 binary, unchanged guards."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_product_recovery as prior
from run_literal_text_atom_product_components import CAPTURE
from run_regex_replacement_focused import select_own_single_cpu
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-style-replacement-components126.v1.json'
ATOMS='crates/hwpx-package/src/document_import/search/replacement/atoms.rs';STYLE=ATOMS[:-3]+'/styles.rs'
RENDER=STYLE[:-3]+'/render.rs';VERIFY=STYLE[:-3]+'/verify.rs';REVIEW=ATOMS[:-3]+'/review.rs'
PATCH='crates/hwpx-package/src/patch.rs';EDGES='crates/hwpx-package/src/patch/text_atom_ranges.rs'
DEFS='crates/hwpx-package/src/document_import/search/inspection/definitions.rs';MATCHER='crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs'
TARGET='crates/hwpx-package/tests/style_replacement_focused.rs';TEST='crates/hwpx-package/tests/document_import_style_replacement.rs'
NEW={STYLE,RENDER,VERIFY,TARGET,TEST};CHANGED={ATOMS,REVIEW,PATCH,EDGES,DEFS,MATCHER}
WRAPPER='''        self.find_style_checked(query,selector,policy,filter,None).map(|(found,_)|found)
    }
    pub(in crate::document_import::search) fn find_style_for_character_replacement(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,target:u32)->Result<(SourceReviewSelectorStyleResult,SourceAnchorHandle),E> {
        let(found,declaration)=self.find_style_checked(query,selector,policy,filter,Some(target))?;Ok((found,declaration.ok_or(E::Definition)?))
    }
    fn find_style_checked(&self,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,target:Option<u32>)->Result<(SourceReviewSelectorStyleResult,Option<SourceAnchorHandle>),E> {
'''
BOUND='''        let bound=if target.is_some()||matches!(filter,SourceReviewStyleFilter::Definition(_)){Some(inspection.resolve_style_definitions()?)}else{None};
        let declaration=target.map(|id|bound.as_ref().ok_or(E::Definition)?.character_declaration(id)).transpose()?;
'''
READBACK='''        let output=ImportedDocumentReviewBodies::import_bound_fields(forms,fields).map_err(|_|E::Readback)?;
        self.readback_receipt(output.receipt())
    }
    pub(super) fn readback_receipt(&self,r:&ReviewBodyImportReceipt)->Result<ReviewBodyImportReceipt,E> {
'''


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    text=q.text(ATOMS);c.require(text.count('pub mod styles;\n')==1,'ONLY_STYLE_MODULE_ADDITION_TO_ORIGINAL_ATOM_COMPILER')
    audit.inverse(text.replace('pub mod styles;\n',''),old[ATOMS],'WHOLE_ORIGINAL_LITERAL_REGEX_ZERO_WIDTH_COMPILER_UNCHANGED')
    text=q.text(PATCH);c.require(text.count('pub(crate) mod text_atom_ranges;')==1,'ONLY_CRATE_INTERNAL_EDGE_HELPER_VISIBILITY')
    audit.inverse(text.replace('pub(crate) mod text_atom_ranges;','mod text_atom_ranges;'),old[PATCH],'WHOLE_ORIGINAL_PATCH_TRANSACTION_AND_PUBLIC_API_UNCHANGED')
    text=q.text(EDGES);marker='\n/// Requested original scalar edges';c.require(text.count(marker)==1,'ONE_ADDITIVE_ORIGINAL_TOKEN_SCANNER_BRIDGE')
    audit.inverse(text.split(marker,1)[0],old[EDGES],'WHOLE_ORIGINAL_ATOM_RANGE_AND_CONTROL_BOUNDARY_WRITER_UNCHANGED')
    text=q.text(DEFS);start=text.index('    pub(in crate::document_import::search) fn character_declaration(');end=text.index('    pub(in crate::document_import::search) fn accepts_points(',start)
    audit.inverse(text[:start]+text[end:],old[DEFS],'WHOLE_ORIGINAL_TYPED_HEADER_BINDINGS_AND_DEFINITION_SEARCH_UNCHANGED')
    text=q.text(REVIEW);c.require(text.count(READBACK)==1,'ONE_ORIGINAL_REVIEW_RECEIPT_VALIDATION_EXTRACTION')
    audit.inverse(text.replace(READBACK,'        let output=ImportedDocumentReviewBodies::import_bound_fields(forms,fields).map_err(|_|E::Readback)?;let r=output.receipt();\n'),old[REVIEW],
        'WHOLE_ORIGINAL_MEMO_CARVE_FIELDS_AND_REVIEW_READBACK_BODY_EXACT_INVERSE')
    text=q.text(MATCHER)
    for current,original in[(WRAPPER,''),(BOUND,''),('bound.as_ref().map(|d|d.receipt().clone())','None'),
        ('let definitions=bound.as_ref().ok_or(E::Definition)?;','let definitions=inspection.resolve_style_definitions()?;'),('Ok((value,declaration))','Ok(value)')]:
        c.require(text.count(current)==1,'ONLY_OPTIONAL_OPERATION_LOCAL_DECLARATION_PROOF_AND_SHARED_DEFINITIONS');text=text.replace(current,original)
    audit.inverse(text,old[MATCHER],'WHOLE_ORIGINAL_NO_TARGET_STYLE_MATCH_WINDOWS_PREDICATES_CAPS_HASH_AND_RESULTS_EXACT_INVERSE')
    style=q.text(STYLE);c.require(style.count('ImportedDocumentFields::import(original)')==1 and style.count('ImportedDocumentReviewBodies::import_bound_fields(original,&fields)')==1
        and style.count('SourceReviewScopeIndex::from_review(original,&review,limits)')==1 and style.count('find_style_for_character_replacement(query,selector,policy,filter,character_property)')==1
        and style.count('output::build_artifact(')==1,'ONE_ORIGINAL_PROOF_FIELD_REVIEW_INDEX_MATCH_AND_PRESERVING_TRANSACTION')
    c.require('plan.bytes=plan.bytes.checked_add(fragment.len()).filter(|n|*n<=index.limits.0.result_bytes)'in style and 'overlays.remove(&a)'in style
        and 'self.bytes=self.bytes.checked_add(value.len())'in q.text(RENDER),'CUMULATIVE_COMPILED_OUTPUT_AND_PIECE_BUDGET_WITH_NESTED_EDIT_COMPOSITION')
    c.require('context.readback_receipt(review.receipt())'in q.text(VERIFY)and 'context.readback(&rebuilt'not in q.text(VERIFY),
        'OUTPUT_REVIEW_IMPORT_ONCE_NOT_A_SECOND_IMPORT_FOR_RECEIPT_VALIDATION')


def expected(q):
    result=set()
    for module,file,count in(('style_replacement','document_import_style_replacement',18),('definitions','document_import_search_definitions',10),
        ('selector_styles','document_import_selector_styles',8),('review_literal','document_import_search_review_replacement',12),('atom_ranges','patch_text_atom_ranges',10)):
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+file+'.rs'))
        c.require(len(names)==len(set(names))==count,'EXACT_EIGHTEEN_NEW_FORTY_AFFECTED_CASE_IDENTITIES');result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_REPLACEMENT_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_REPLACEMENT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='7e4e9727580a7c6dbc2ca335b10aa40e7f387990907dd2251816d5a0ddb1f3b9'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==47 and previous['cleanup'],'EXACT_PRIOR_QUALIFIED_REGEX_V2_PRODUCT_RESULTS_PRESERVED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_STYLE_SOURCE_MODULES_AND_TWO_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CURRENT_STORED_PRODUCT_MATCHER_CORE_GUARD_FIXTURE_OR_ORIGINAL_TEST_BODY_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='STYLE_REPLACEMENT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,affected_cases=40,test_binaries=1,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_partial_style_and_forty_original_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','style_replacement_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_STYLE_REPLACEMENT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_REPLACEMENT_EIGHTEEN_NEW_FORTY_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_core_cases=18,affected_cases=40,total_executed_cases=58,previous_product_and_unaffected_suites_reexecuted=False,
            original_common_code_and_test_bodies_inverse_verified=True,one_original_match_and_preserving_transaction=True,
            partial_original_run_and_nested_review_edits_composed=True,all_source_scalar_control_values_and_each_scalar_style_read_back=True,
            next_work='Current_stored_and_strict_product_binding_of_partial_character_style_candidates_then_paragraph_named_effective_style_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_REPLACEMENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_REPLACEMENT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')},
                'short_diagnostics':s.get('bounded_output_observation',{}).get('short_error_locations',[]),'rust_error_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
