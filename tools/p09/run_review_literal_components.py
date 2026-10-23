"""Explicit hidden/MEMO literal candidates:12 new plus12 v2 and8 review-search cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_text_atom_product_components as prior
import run_search_review_text_components as audit
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-review-literal-components081.v1.json'
PRIOR=prior.OUTPUT
TEST='crates/hwpx-package/tests/document_import_search_review_replacement.rs'
REVIEW='crates/hwpx-package/src/document_import/structure/review.rs'
INDEX='crates/hwpx-package/src/document_import/search/reviews.rs'
CORE='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
READBACK=CORE[:-3]+'/readback.rs'
NEW={TEST,CORE[:-3]+'/review.rs'};CHANGED={REVIEW,INDEX,CORE,READBACK}
V2_TEST='crates/hwpx-package/tests/document_import_search_atom_replacement.rs'
SEARCH_TEST='crates/hwpx-package/tests/document_import_search_review_text.rs'
BRIDGE=('    let found=index.find_scoped(query,scope)?;\n'
    '    lower_found(index,fields,fresh,found.result(),found.scope_receipt().scope_sha256,replacement,run_policy,writer,None)\n'
    '        .map(|(candidate,_)|candidate)\n}\n'
    "fn lower_found(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],found:&super::super::SourceSearchResult,scope_sha256:[u8;32],replacement:&str,\n"
    '    run_policy:SourceReplacementRunPolicy,writer:WriterLimits,review:Option<&review::ReviewWriteContext>)->Result<(SourceLiteralTextAtomCandidate,Option<review::ReviewBodyImportReceipt>),E> {\n'
    '    if found.matches().is_empty(){return Err(E::NoMatches);}\n')
READ_REVIEW=('        let output_review=if let Some(review)=review {\n'
    '            let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;\n'
    '            Some(review.readback(&rebuilt,&fields)?)\n'
    '        }else{let _=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;None};\n')


def inventory(check):return prior.inventory(check)|{TEST}


def replace_once(text,current,previous,label):
    c.require(text.count(current)==1,label);return text.replace(current,previous)


def inverse(q,old):
    text=q.text(REVIEW);text=replace_once(text,'    pub(in crate::document_import) fn is_for_original(&self,forms:&ImportedDocumentForms)->bool {std::ptr::eq(self.forms,forms)}\n','',
        'ONLY_INTERNAL_REVIEW_ORIGINAL_POINTER_BRIDGE');audit.inverse(text,old[REVIEW],'ORIGINAL_REVIEW_COLLECTOR_ENVELOPE_AND_BODY_MAPPER_EXACT_INVERSE')
    text=q.text(INDEX)
    for current in ('        Self::from_review(forms,&review,limits)\n    }\n'
        "    pub(super) fn from_review(forms:&'a ImportedDocumentForms,review:&ImportedDocumentReviewBodies<'_>,limits:SourceSearchLimits)->Result<Self,E> {\n"
        '        if !review.is_for_original(forms){return Err(E::Source);}\n',
        "    pub(super) fn source_index(&self)->&SourceTextIndex<'a> {&self.index}\n"):
        text=replace_once(text,current,'','ONLY_ORIGINAL_REVIEW_PROJECTION_EXTRACTION_AND_INTERNAL_ACCESS')
    audit.inverse(text,old[INDEX],'ORIGINAL_REVIEW_SEARCH_PROJECTION_SCOPE_POLICY_AND_MATCHER_EXACT_INVERSE')
    text=q.text(CORE)
    for current,previous in (('pub mod review;\n',''),(BRIDGE,'    let found=index.find_scoped(query,scope)?;if found.result().matches().is_empty(){return Err(E::NoMatches);}\n'),
        ('for m in found.matches() {','for m in found.result().matches() {'),
        ('let intervals=match review {Some(review)=>review.field_intervals(source,fields)?,None=>field_intervals(source,fields)?};','let intervals=field_intervals(source,fields)?;'),
        ('let (artifact,output_review)=readback::build(source,fresh,&intents,&plans,writer,review)?;','let artifact=readback::build(source,fresh,&intents,&plans,writer)?;'),
        ('profile:if review.is_some(){review::SOURCE_REVIEW_LITERAL_PROFILE}else{SOURCE_LITERAL_TEXT_ATOM_PROFILE},','profile:SOURCE_LITERAL_TEXT_ATOM_PROFILE,'),
        ('scope_sha256,query_sha256:found.query_sha256(),','scope_sha256:found.scope_receipt().scope_sha256,query_sha256:found.result().query_sha256(),'),
        ('matched_occurrences:found.matches().len(),','matched_occurrences:found.result().matches().len(),'),
        ('Ok((SourceLiteralTextAtomCandidate {artifact,receipt},output_review))','Ok(SourceLiteralTextAtomCandidate {artifact,receipt})')):
        text=replace_once(text,current,previous,'ONLY_ORIGINAL_V2_FOUND_MATCH_COMPILER_REUSE_WITH_EXPLICIT_REVIEW_CONTEXT')
    audit.inverse(text,old[CORE],'ORIGINAL_V2_NFC_MATCH_GROUP_RUN_POLICY_PROTECTION_AND_SCALAR_PLANNING_EXACT_INVERSE')
    text=q.text(READBACK)
    for current,previous in (
        ('writer:WriterLimits,\n    review:Option<&review::ReviewWriteContext>)->Result<(PackageArtifact,Option<review::ReviewBodyImportReceipt>),E> {','writer:WriterLimits)->Result<PackageArtifact,E> {'),
        ('let output_review=artifact.with_verified_bytes(|bytes|->Result<Option<review::ReviewBodyImportReceipt>,E>{','artifact.with_verified_bytes(|bytes|->Result<(),E>{'),
        (READ_REVIEW,'        let _=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;\n'),
        ('}Ok(output_review)\n    }).map_err(|_|E::Writer)??;Ok((artifact,output_review))','}Ok(())\n    }).map_err(|_|E::Writer)??;Ok(artifact)')):
        text=replace_once(text,current,previous,'ONLY_REUSED_OUTPUT_FIELD_IMPORT_AND_OPTIONAL_BOUND_REVIEW_READBACK')
    audit.inverse(text,old[READBACK],'ORIGINAL_V2_OUTPUT_FORM_TEXT_CONTROL_AND_OUTSIDE_ATOM_BYTE_READBACK_EXACT_INVERSE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_LITERAL_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_LITERAL_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='1fcfe918bac8737dc57a41b5a2246b3cc457d2504941e828a15f6c7618f63b4c'
            and previous['state'].startswith('PASS_')and previous['cleanup'],'EXACT_PREVIOUS_V2_PRODUCT_PASS_RETAINED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_REVIEW_LITERAL_COMPILER_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_READER_PATCH_FIELD_COLLECTOR_STORED_OR_PRODUCT_CHANGE')
        inverse(q,old)
        def cases(path):return set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path)))
        new,v2,search=cases(TEST),cases(V2_TEST),cases(SEARCH_TEST);affected=v2|search
        c.require((len(new),len(v2),len(search),len(affected))==(12,12,8,20),'EXACT_TWELVE_NEW_AND_TWENTY_AFFECTED_CASES')
        env=audit.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        print(json.dumps(dict(state='REVIEW_LITERAL_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=20,original_v2_and_review_search_bodies_inverse_verified=True)),flush=True)
        harness.run_one('twelve_original_hidden_memo_literal_candidate_cases',common+['--test','document_import_search_review_replacement','--','--test-threads=1'],new,guard,env,row)
        harness.run_one('twenty_affected_v2_literal_and_review_search_cases',common+['--test','document_import_search_atom_replacement','--test','document_import_search_review_text','--',*sorted(affected),'--exact','--test-threads=1'],affected,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_LITERAL_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_LITERAL_TWELVE_NEW_TWENTY_AFFECTED_NOT_STORED_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=12,affected_cases=20,total_executed_cases=32,
            original_v2_compiler_and_review_search_bodies_inverse_verified=True,original_fields_and_review_projection_imported_once_per_batch=True,
            whole_output_form_fields_and_review_import_shared_once=True,owning_memo_sublist_exemption_only_with_outer_field_union=True,
            cached_field_and_control_editing_unqualified=True,metadata_and_outside_selected_atom_bytes_preserved=True,
            existing_product_and_stored_cases_reexecuted=False,stored_service_or_product_request_added=False,
            next_work='Bind_review_literal_candidate_to_current_stored_scope_head_and_output_delivery')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_LITERAL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_LITERAL_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
