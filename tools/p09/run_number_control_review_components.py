"""Actual review-bound input/output number-stream recovery, old closed branch preserved,67 serial cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_number_control_source_selection_recovery as prior
harness,shared,c,a,audit,snapshot,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot,prior.tools
base=prior.prior;source=base.source
OUTPUT='implementation/p09/evidence/p09-361-number-control-review-components200.v1.json'
TARGETS='crates/hwpx-package/src/document_import/reference_targets.rs'
STATE='crates/hwpx-package/src/document_import/reference_targets/caption_source_state.rs'
EDIT='crates/hwpx-package/src/document_import/structure/caption_edit_batch.rs'
TEXT='crates/hwpx-package/src/document_import/structure/caption_text_batch.rs'
CORE=base.CORE;PARENT=base.TEST
MODEL=TEXT[:-3]+'/review_output.rs';TEST='crates/hwpx-package/tests/support/number_control_review_admission.rs'
NEW={MODEL,TEST};CHANGED={TARGETS,STATE,EDIT,TEXT,CORE,PARENT}
WRAPPER='''        pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,CaptionNumberingImportError> {
            Self::import_with_review_paragraphs(source,limits,BTreeSet::new(),None)
        }
        /// Exact immutable Form/review identity, not a caller paragraph allowlist or Native visibility claim.
        /// # Errors
        /// Rejects foreign review/model bindings, finite bounds and the original coverage/value failures.
        pub fn import_review_bound(forms:&'a crate::document_import::forms::ImportedDocumentForms,
            review:&crate::document_import::structure::review::ImportedDocumentReviewBodies<'_>,limits:ReferenceAuxiliaryLimits)
            ->Result<Self,CaptionNumberingImportError> {
            use CaptionNumberingImportError as E;
            if !review.is_for_original(forms)||review.receipt().source_package_sha256!=forms.source().receipt().source_package_sha256{return Err(E::Binding);}
            let mut observed=BTreeSet::new();
            for item in review.observations(){if let Some(flow)=&item.body{walk(flow,&mut observed,0)?;
                if observed.len()>limits.config().items_per_kind{return Err(E::Limit);}}}
            let paragraphs=observed.into_iter().cloned().collect();
            Self::import_with_review_paragraphs(forms.body_structure(),limits,paragraphs,Some(review.receipt().body_observations_sha256))
        }
        fn import_with_review_paragraphs(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits,
            review_paragraphs:BTreeSet<LogicalId>,review_body_inventory_sha256:Option<[u8;32]>)->Result<Self,CaptionNumberingImportError> {
'''
STATE_ADDITION='''    /// # Errors
    /// The actual immutable Form/review pair, never caller-created paragraph IDs or inferred visibility.
    pub fn import_review_bound(forms:&'a crate::document_import::forms::ImportedDocumentForms,
        review:&crate::document_import::structure::review::ImportedDocumentReviewBodies<'_>,limits:ReferenceAuxiliaryLimits)->Result<Self,E> {
        ImportedCaptionNumbering::import_review_bound(forms,review,limits)?.assemble_source_state(limits)
    }
'''
OLD_READBACK='''        let output_review=output.with_verified_bytes(|bytes|{
            let rebuilt=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let forms=ImportedDocumentForms::import(rebuilt).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
            context.readback(&forms,&fields)
        }).map_err(|_|E::Readback)??;
'''


def inventory(check):return base.inventory(check)|NEW


def change(text,new,old):
    c.require(text.count(new)==1,'ONE_EXACT_REVIEW_ADMISSION_ADDITIVE_OR_MECHANICAL_CHANGE');return text.replace(new,old)


def inverse(q,old):
    text=q.text(TARGETS)
    text=change(text,'        #[serde(skip_serializing_if="Option::is_none")]\n        pub review_body_inventory_sha256:Option<[u8;32]>,\n','')
    text=change(text,'        review_paragraphs:BTreeSet<LogicalId>,\n','')
    text=change(text,WRAPPER,"        pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,CaptionNumberingImportError> {\n")
    text=change(text,'let logical_caption_id=if require_paragraph(part,paragraph,&paragraphs).is_ok()\n                        ||part.element_anchor(paragraph).is_some_and(|a|review_paragraphs.contains(&a.opaque_handle)) {None} else {',
        'let logical_caption_id=if require_paragraph(part,paragraph,&paragraphs).is_ok() {None} else {')
    text=change(text,'profile:if review_body_inventory_sha256.is_some(){"hwpx-agent.document-import-caption-numbering/source-review-observations-v2"}else{"hwpx-agent.document-import-caption-numbering/source-observations-v1"}',
        'profile:"hwpx-agent.document-import-caption-numbering/source-observations-v1"')
    text=change(text,'section_start_inventory_sha256:hash_json(&starts,limits.config().output_bytes).map_err(|_|E::Limit)?,review_body_inventory_sha256,',
        'section_start_inventory_sha256:hash_json(&starts,limits.config().output_bytes).map_err(|_|E::Limit)?,')
    text=change(text,'paragraphs,review_paragraphs,receipt','paragraphs,receipt')
    text=change(text,'self.paragraphs.contains(id)||self.review_paragraphs.contains(id)','self.paragraphs.contains(id)')
    audit.inverse(text,old[TARGETS],'ENTIRE_OLD_NUMBERING_AND_OTHER_TARGET_IMPORTS_CONTEXT_VALUE_FORMAT_COVERAGE_AND_LEGACY_RECEIPT_BODY_RESTORED')
    audit.inverse(change(q.text(STATE),STATE_ADDITION,''),old[STATE],'ENTIRE_OLD_SOURCE_STATE_IMPORT_AND_JOIN_BODIES_UNCHANGED')
    audit.inverse(change(q.text(EDIT),'    #[serde(skip_serializing_if="Option::is_none")]\n    pub output_review_import:Option<super::review::ReviewBodyImportReceipt>,\n',''),
        old[EDIT],'ENTIRE_OLD_BATCH_TYPES_AND_ENTRY_BODIES_EXCEPT_OPTIONAL_OMITTED_REVIEW_RECEIPT_FIELD')
    text=change(q.text(TEXT),'mod review_output;\n','');text=change(text,'        let mut output_review_import=None;\n','')
    text=change(text,'            let output_model=review_output::BatchOutputImport::import(output,numbering.receipt().review_body_inventory_sha256.is_some())?;\n            let rebuilt=output_model.structure();\n            let after_numbers=output_model.numbering(limits,&mut output_review_import)?;\n',
        '            let rebuilt=ImportedDocumentStructure::import(output).map_err(|_|E::Readback)?;\n            let after_numbers=ImportedCaptionNumbering::import(&rebuilt,limits).map_err(|_|E::Readback)?;\n')
    text=change(text,'outside_selected_edits_exact:true,output_review_import,','outside_selected_edits_exact:true,')
    audit.inverse(text,old[TEXT],'ENTIRE_OLD_COMPILER_PROTECTION_PATCH_WRITER_OUTPUT_VALUES_FRAMES_AND_EXACT_BYTE_READBACK_EXCEPT_OUTPUT_IMPORT_SELECTION')
    text=change(q.text(CORE),'numbering::NativeNumberControlKind as Kind}};','numbering::NativeNumberControlKind as Kind},ImportedSourcePackage};')
    text=change(text,'ImportedCaptionSourceState::import_review_bound(original,&review,limits)','ImportedCaptionSourceState::import(original.body_structure(),limits)')
    text=change(text,'        let output_review=context.readback_receipt(stream.content.output.output_review_import.as_ref().ok_or(E::Readback)?)?;\n',OLD_READBACK)
    audit.inverse(text,old[CORE],'ENTIRE_ORIGINAL_NUMBER_SELECTOR_REQUEST_GUARDS_ORDER_NOOP_REFERENCE_AND_RESPONSE_BODIES_EXCEPT_BOUND_REVIEW_IMPORT_AND_SHARED_READBACK')
    audit.inverse(change(q.text(PARENT),'#[path="support/number_control_review_admission.rs"] mod review_admission;\n',''),old[PARENT],
        'ALL_ORIGINAL21_TESTS_INCLUDING_REQUIRED_REVIEW_POSITIVE_AND_LEGACY_COVERAGE_DIAGNOSIS_UNCHANGED')
    model=q.text(MODEL)
    for marker in('Self::Body(s)=>ImportedCaptionNumbering::import(s,limits)','ImportedDocumentFields::import(forms)',
        'ImportedDocumentReviewBodies::import_bound_fields(forms,&fields)','ImportedCaptionNumbering::import_review_bound(forms,&review,limits)',
        '*receipt=Some(review.receipt().clone())'):
        c.require(marker in model,'OLD_STRICT_BRANCH_OR_ONE_ACTUAL_OUTPUT_FORM_FIELD_REVIEW_NUMBERING_IMPORT_NO_REPARSE')


def expected(q):
    result=source.expected(q)
    for file,prefix,count in[(PARENT,'numbers::',21),(TEST,'numbers::review_admission::',10)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(file));c.require(len(names)==len(set(names))==count,'EXACT_ORIGINAL21_AND_NEW10_REVIEW_IDENTITIES');result.update(prefix+n for n in names)
    c.require(len(result)==67 and prior.UNRESOLVED in result,'ORIGINAL_REQUIRED_REVIEW_SUCCESS_CASE_MUST_RUN_NOT_SKIPPED');return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_REVIEW_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_REVIEW_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,number_control_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='9d03de8ada7504b1909c2fa89451f84c6b6f7d5d9fa9e004403a26d0d0b77f2a'
            and baseline['state']=='MIXED_NUMBER_CONTROL_SOURCE19_DIAGNOSTIC1_REQUIRED_REVIEW_CASE_UNRESOLVED'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==721 and baseline['original_required_review_case_still_failed']
            and not baseline['full_number_control_source_qualified'],'EXACT198_MIXED_BASELINE_REQUIRED_FAILURE_NOT_ERASED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_REVIEW_OUTPUT_MODEL_AND_TESTS_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_GUARDS_WRITERS_GEOMETRY_PRODUCTS_TESTS_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='NUMBER_CONTROL_REVIEW_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),original_functional20_diagnostic1=21,new_admission_cases=10,affected_cases=36,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_original_number_cases_one_diagnosis_ten_review_and_thirty_six_affected_controls',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','control_replacement_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_NUMBER_CONTROL_REVIEW_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_BOUND_NUMBER_SOURCE30_DIAGNOSTIC1_AFFECTED36_NOT_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_number_functional_cases=20,legacy_coverage_diagnostic_cases=1,new_review_admission_cases=10,affected_control_cases=36,total_executed_cases=67,
            original_required_review_case_now_passed=True,old266_products_and_official249_reexecuted=False,
            original_strict_import_and_legacy_wire_preserved=True,original_protection_scope_number_value_reference_and_byte_checks_preserved=True,
            actual_form_review_identity_not_caller_allowlist=True,one_shared_output_form_fields_review_numbering_import=True,
            next_work='SEARCH009_number_control_current_store_strict_product_other_families_full_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_REVIEW_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NUMBER_CONTROL_REVIEW_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
