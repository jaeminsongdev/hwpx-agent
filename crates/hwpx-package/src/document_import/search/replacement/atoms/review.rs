//! Explicit original hidden/MEMO body replacement; cached fields stay protected.
pub mod selector;
use super::*;
use crate::document_import::{ImportedSourcePackage,structure::review::{ImportedDocumentReviewBodies,ReviewBodyKind}};
pub(super) use crate::document_import::structure::review::ReviewBodyImportReceipt;
use crate::document_import::search::reviews::{SourceReviewTextIndex,SourceReviewTextPolicy,SourceTextRegion};
pub const SOURCE_REVIEW_LITERAL_PROFILE:&str="hwpx-agent.source-literal-replacement-candidate/v3";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReviewLiteralReceipt {
    pub profile:&'static str,pub body_policy:SourceReviewTextPolicy,pub source_review_import:ReviewBodyImportReceipt,
    pub output_review_import:ReviewBodyImportReceipt,pub review_search_request_sha256:[u8;32],pub match_regions:Vec<SourceTextRegion>,
    pub permitted_memo_payload_bodies:usize,pub output:SourceLiteralTextAtomReceipt,
    pub memo_payload_not_cached_result_verified:bool,pub native_author_visibility_resolution_or_execution_qualified:bool,
}
pub struct SourceReviewLiteralCandidate {inner:SourceLiteralTextAtomCandidate,receipt:SourceReviewLiteralReceipt}
impl fmt::Debug for SourceReviewLiteralCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceReviewLiteralCandidate(<redacted>; explicit_source_body_policy_only)")}}
impl SourceReviewLiteralCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceReviewLiteralReceipt {&self.receipt}
    /// # Errors
    /// Pure writer integrity, not fresh service access or Native/comment state authority.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.inner.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Original body/note and explicitly included hidden/MEMO payload Text atoms only.
    pub fn lower_review_literal_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceReviewLiteralCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_review_literal_candidate(self,query,scope,policy,replacement,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One exact original proof, field collector and review-body projection for the batch.
    pub fn lower_review_literal_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,policy:SourceReviewTextPolicy,
        replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceReviewLiteralCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        if query.mode!=SourceSearchMode::Literal{return Err(E::Value);}validate_literal_replacement(replacement)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|E::Source)?;
        let index=SourceReviewTextIndex::from_review(original,&review,limits)?;
        let found=index.find(query,scope,policy)?;
        compile_review_found(index.source_index(),&fields,&review,rebuilt.source().original.as_ref(),
            ReviewMatches {result:found.matches(),scope_sha:found.scope_receipt().scope_sha256,request_sha:found.request_sha256(),regions:found.match_regions()},
            policy,replacement,run_policy,limits,writer)
    }
}
struct ReviewMatches<'a> {result:&'a crate::document_import::search::SourceSearchResult,scope_sha:[u8;32],request_sha:[u8;32],regions:&'a [SourceTextRegion]}
fn compile_review_found(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,review:&ImportedDocumentReviewBodies<'_>,fresh:&[u8],found:ReviewMatches<'_>,
    policy:SourceReviewTextPolicy,replacement:&str,run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceReviewLiteralCandidate,E> {
    let context=ReviewWriteContext::new(index.original.source(),fields,review,policy)?;
    let (inner,readback)=lower_found(index,fields,fresh,found.result,found.scope_sha,replacement,run_policy,writer,Some(&context))?;
    let receipt=SourceReviewLiteralReceipt {profile:SOURCE_REVIEW_LITERAL_PROFILE,body_policy:policy,source_review_import:context.source.clone(),
        output_review_import:readback.ok_or(E::Readback)?,review_search_request_sha256:found.request_sha,match_regions:found.regions.to_vec(),
        permitted_memo_payload_bodies:context.memo.len(),output:inner.receipt().clone(),memo_payload_not_cached_result_verified:true,
        native_author_visibility_resolution_or_execution_qualified:false};
    let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
    Ok(SourceReviewLiteralCandidate {inner,receipt})
}
pub(super) struct ReviewWriteContext {source:ReviewBodyImportReceipt,memo:BTreeMap<domain_ir::LogicalId,(PackagePath,usize,usize)>}
impl ReviewWriteContext {
    pub(super) fn new(source:&ImportedSourcePackage,fields:&ImportedDocumentFields<'_>,review:&ImportedDocumentReviewBodies<'_>,policy:SourceReviewTextPolicy)->Result<Self,E> {
        let by_begin:BTreeMap<_,_>=fields.fields().iter().map(|f|(&f.begin_anchor.opaque_handle,f)).collect();let mut memo=BTreeMap::new();
        if policy.include_memo_bodies {for observation in review.observations().iter().filter(|o|o.kind==ReviewBodyKind::MemoField) {
            let Some(body_anchor)=&observation.body_anchor else{continue};
            let field=by_begin.get(&observation.marker_anchor.opaque_handle).ok_or(E::Source)?;
            if field.native_kind!="MEMO"||observation.end_anchor.as_ref()!=Some(&field.end_anchor){return Err(E::Source);}
            let body=source.resolve_anchor(body_anchor).map_err(|_|E::Source)?;let begin=source.resolve_anchor(&field.begin_anchor).map_err(|_|E::Source)?;
            if body.part().path()!=begin.part().path()||body.element().ok_or(E::Source)?.parent()!=begin.element_index(){return Err(E::Source);}
            let span=body.element().ok_or(E::Source)?.content_span().ok_or(E::Source)?;
            if memo.insert(field.begin_anchor.opaque_handle.clone(),(body.part().path().clone(),span.start(),span.end())).is_some(){return Err(E::Source);}
        }}Ok(Self {source:review.receipt().clone(),memo})
    }
    pub(super) fn field_intervals<'a>(&self,source:&'a ImportedSourcePackage,fields:&ImportedDocumentFields<'_>)->Result<BTreeMap<&'a PackagePath,Vec<(usize,usize)>>,E> {
        let mut all:BTreeMap<&PackagePath,Vec<(usize,usize)>>=BTreeMap::new();
        for field in fields.fields() {
            let begin=source.resolve_anchor(&field.begin_anchor).map_err(|_|E::Source)?;let end=source.resolve_anchor(&field.end_anchor).map_err(|_|E::Source)?;
            if begin.part().path()!=end.part().path(){return Err(E::Source);}
            let start=begin.element().ok_or(E::Source)?.start_tag_span().start();let stop=end.element().ok_or(E::Source)?.start_tag_span().start();
            if start>=stop{return Err(E::Source);}
            let ranges=all.entry(begin.part().path()).or_default();
            if let Some((path,a,b))=self.memo.get(&field.begin_anchor.opaque_handle) {
                if path!=begin.part().path()||!(start<*a&&a<b&&*b<stop){return Err(E::Source);}
                ranges.push((start,*a));ranges.push((*b,stop));
            }else{ranges.push((start,stop));}
        }
        // Union all OTHER field ranges after carving each exact owning MEMO payload.
        // An enclosing field still covers that payload; caches and hidden comments stay blocked.
        for ranges in all.values_mut() {ranges.sort_unstable();let mut merged:Vec<(usize,usize)>=Vec::new();
            for &(start,end) in ranges.iter(){if let Some(last)=merged.last_mut(){if start<=last.1{last.1=last.1.max(end);continue;}}merged.push((start,end));}*ranges=merged;}
        Ok(all)
    }
    pub(super) fn readback(&self,forms:&ImportedDocumentForms,fields:&ImportedDocumentFields<'_>)->Result<ReviewBodyImportReceipt,E> {
        let output=ImportedDocumentReviewBodies::import_bound_fields(forms,fields).map_err(|_|E::Readback)?;
        self.readback_receipt(output.receipt())
    }
    pub(super) fn readback_receipt(&self,r:&ReviewBodyImportReceipt)->Result<ReviewBodyImportReceipt,E> {
        if r.profile!=self.source.profile||r.qualification!=self.source.qualification||r.hidden_explanations!=self.source.hidden_explanations
            ||r.memo_fields!=self.source.memo_fields||r.memo_fields_without_body!=self.source.memo_fields_without_body
            ||r.native_author_time_binding_verified||r.native_visibility_resolution_binding_verified{return Err(E::Readback);}
        Ok(r.clone())
    }
}
