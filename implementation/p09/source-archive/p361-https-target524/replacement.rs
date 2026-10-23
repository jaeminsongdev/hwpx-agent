//! Actual original literal matches -> one preserving scalar-range candidate transaction.
mod output;
mod font_profile;
pub mod atoms;
use super::{SourceSearchQuery,SourceSearchMode,SourceSearchLimits,SourceTextIndex,SourceSearchError,Output,extract};
use super::scope::SourceSearchScope;
use crate::document_import::{forms::{ImportedDocumentForms,VerifiedFormReconstruction},fields::ImportedDocumentFields};
use crate::{LeafTextRangeReplacement,PackageArtifact,PatchIntent,PatchLimits,PatchText,PreservingXmlDocument,WriterError,WriterLimits,XmlElementSelector,XmlTokenKind,PackagePath};
use domain_ir::SourceAnchorHandle;
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt};
use thiserror::Error;
pub const SOURCE_LITERAL_REPLACEMENT_PROFILE:&str="hwpx-agent.source-literal-replacement-candidate/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceReplacementRunPolicy {FirstOriginalRunRetainAllRuns}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReplacementLeafChange {
    pub source_text_anchor:SourceAnchorHandle,pub source_text_sha256:[u8;32],pub output_text_sha256:[u8;32],
    pub output_text_bytes:usize,pub changed_scalar_ranges:usize,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceLiteralReplacementReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub scope_sha256:[u8;32],
    pub query_sha256:[u8;32],pub replacement_sha256:[u8;32],pub replacement_bytes:usize,pub run_policy:SourceReplacementRunPolicy,
    pub matched_occurrences:usize,pub changed_scalar_ranges:usize,pub changes:Vec<SourceReplacementLeafChange>,pub changed_parts:usize,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub original_selection_contiguity_verified:bool,pub outside_selected_leaf_contents_exact:bool,pub output_plain_leaf_values_verified:bool,
    pub field_cached_content_edit_qualified:bool,pub full_protection_native_or_execution_authority:bool,
}
pub struct SourceLiteralReplacementCandidate {artifact:PackageArtifact,receipt:SourceLiteralReplacementReceipt}
impl fmt::Debug for SourceLiteralReplacementCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceLiteralReplacementCandidate(<redacted>; not_full_protection_or_authority)")}}
impl SourceLiteralReplacementCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceLiteralReplacementReceipt {&self.receipt}
    /// # Errors
    /// Writer integrity only; never fresh service authorization or revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceLiteralReplacementError {
    #[error("SOURCE_LITERAL_REPLACEMENT_SOURCE_REJECTED")] Source,
    #[error("SOURCE_LITERAL_REPLACEMENT_SEARCH:{0}")] Search(#[from] SourceSearchError),
    #[error("SOURCE_LITERAL_REPLACEMENT_VALUE_OR_MODE_REJECTED")] Value,
    #[error("SOURCE_LITERAL_REPLACEMENT_SELECTION_NOT_CONTIGUOUS_PLAIN_TEXT")] Selection,
    #[error("SOURCE_LITERAL_REPLACEMENT_OBSERVED_PROTECTION")] Protection,
    #[error("SOURCE_LITERAL_REPLACEMENT_FIELD_CONTENT_UNQUALIFIED")] FieldContent,
    #[error("SOURCE_LITERAL_REPLACEMENT_NO_MATCHES")] NoMatches,
    #[error("SOURCE_LITERAL_REPLACEMENT_NO_CHANGE")] NoChange,
    #[error("SOURCE_LITERAL_REPLACEMENT_LIMIT")] Limit,
    #[error("SOURCE_LITERAL_REPLACEMENT_PATCH:{0}")] Patch(&'static str),
    #[error("SOURCE_LITERAL_REPLACEMENT_WRITER_REJECTED")] Writer,
    #[error("SOURCE_LITERAL_REPLACEMENT_READBACK_REJECTED")] Readback,
    #[error("SOURCE_LITERAL_REPLACEMENT_PRESERVATION_REJECTED")] Preservation,
}
type E=SourceLiteralReplacementError;
/// # Errors
/// Pure preflight shared by product parsing and lowering; never a source or access grant.
pub fn validate_literal_replacement(replacement:&str)->Result<(),SourceLiteralReplacementError> {
    if replacement.len()>PatchLimits::default().config().max_value_bytes{return Err(E::Limit);}
    PatchText::new(replacement).map_err(|_|E::Value)?;
    crate::text_flow::validate_text(replacement).map_err(|_|E::Value)
}
struct Edit<'a> {start:u32,end:u32,value:&'a str}
struct PlannedLeaf {element:usize,expected:String,change:SourceReplacementLeafChange}
impl ImportedDocumentForms {
    /// # Errors
    /// Actual mapped body/note literal replacement with fresh whole Form proof.
    /// Field caches/mixed leaves/ambiguous NFC selections are rejected, not skipped.
    pub fn lower_literal_search_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceLiteralReplacementCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_literal_search_candidate(self,query,scope,replacement,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Reuses this exact original's operation-local whole-source reconstruction.
    pub fn lower_literal_search_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceLiteralReplacementCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        if query.mode!=SourceSearchMode::Literal{return Err(E::Value);}
        validate_literal_replacement(replacement)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let index=extract::build(original.body_structure(),limits)?;
        lower(&index,&fields,rebuilt.source().original.as_ref(),query,scope,replacement,run_policy,writer)
    }
}
fn lower(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
    run_policy:SourceReplacementRunPolicy,writer:WriterLimits)->Result<SourceLiteralReplacementCandidate,E> {
    let found=index.find_scoped(query,scope)?;if found.result().matches().is_empty(){return Err(E::NoMatches);}
    let source=index.original.source();let mut used=BTreeSet::new();let mut leaves:BTreeMap<usize,Vec<Edit<'_>>>=BTreeMap::new();let mut range_count=0_usize;
    for m in found.result().matches() {
        let origins=selected_origins(index,m)?;
        let mut groups:Vec<(usize,u32,u32)>=Vec::new();
        for origin in origins {if !used.insert(origin){return Err(E::Selection);}let p=index.points[origin];
            if p.atom!=0{return Err(E::Selection);}
            if let Some(last)=groups.last_mut(){if last.0==p.segment&&last.2==p.scalar {last.2+=1;continue;}}
            groups.push((p.segment,p.scalar,p.scalar+1));
        }
        for (i,(segment,start,end)) in groups.into_iter().enumerate() {
            range_count=range_count.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            leaves.entry(segment).or_default().push(Edit {start,end,value:if i==0 {replacement}else{""}});
        }
    }
    let field_intervals=field_intervals(source,fields)?;
    let mut guards=BTreeMap::new();let mut visits=0_usize;let mut intents=Vec::new();let mut plans:BTreeMap<&PackagePath,Vec<PlannedLeaf>>=BTreeMap::new();
    let mut changes=Vec::new();let mut changed_ranges=0_usize;let mut output_text_bytes=0_usize;
    for (segment,mut edits) in leaves {
        edits.sort_by_key(|e|e.start);if edits.windows(2).any(|w|w[0].end>w[1].start){return Err(E::Selection);}
        let anchor=&index.segments[segment];let resolved=source.resolve_anchor(anchor).map_err(|_|E::Selection)?;
        let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let element=resolved.element_index().ok_or(E::Selection)?;
        if !guards.contains_key(part.path()) {
            visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            guards.insert(part.path(),crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?);
        }
        if guards.get(part.path()).and_then(|v|v.get(element)).copied().ok_or(E::Selection)? {return Err(E::Protection);}
        let point=xml.elements()[element].start_tag_span().start();
        if let Some(intervals)=field_intervals.get(part.path()) {
            let i=intervals.partition_point(|(start,_)|*start<point);if i>0&&point<intervals[i-1].1{return Err(E::FieldContent);}
        }
        let before=plain_leaf(xml,element)?;let mut offsets:Vec<_>=before.char_indices().map(|(i,_)|i).collect();offsets.push(before.len());
        let mut after=String::new();let mut previous=0;let mut ranges=Vec::new();
        for edit in edits {
            let start=*offsets.get(edit.start as usize).ok_or(E::Selection)?;let end=*offsets.get(edit.end as usize).ok_or(E::Selection)?;
            if &before[start..end]==edit.value {continue;}
            append(&mut after,&before[previous..start],index.limits.0.result_bytes)?;append(&mut after,edit.value,index.limits.0.result_bytes)?;previous=end;
            ranges.push(LeafTextRangeReplacement::new(edit.start,edit.end,edit.value).map_err(|_|E::Value)?);
        }
        if ranges.is_empty(){continue;}
        append(&mut after,&before[previous..],index.limits.0.result_bytes)?;
        output_text_bytes=output_text_bytes.checked_add(after.len()).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
        changed_ranges=changed_ranges.checked_add(ranges.len()).ok_or(E::Limit)?;
        let change=SourceReplacementLeafChange {source_text_anchor:anchor.clone(),source_text_sha256:Sha256::digest(before.as_bytes()).into(),
            output_text_sha256:Sha256::digest(after.as_bytes()).into(),output_text_bytes:after.len(),changed_scalar_ranges:ranges.len()};
        intents.push(PatchIntent::ReplaceLeafScalarRanges {target:XmlElementSelector::bind(part.path(),xml,element).map_err(|_|E::Selection)?,ranges});
        changes.push(change.clone());plans.entry(part.path()).or_default().push(PlannedLeaf {element,expected:after,change});
    }
    if intents.is_empty(){return Err(E::NoChange);}
    let artifact=output::build(source,fresh,&intents,&plans,writer)?;
    let receipt=SourceLiteralReplacementReceipt {profile:SOURCE_LITERAL_REPLACEMENT_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
        source_index_sha256:index.receipt.index_sha256,scope_sha256:found.scope_receipt().scope_sha256,query_sha256:found.result().query_sha256(),
        replacement_sha256:Sha256::digest(replacement.as_bytes()).into(),replacement_bytes:replacement.len(),run_policy,
        matched_occurrences:found.result().matches().len(),changed_scalar_ranges:changed_ranges,changes,changed_parts:plans.len(),
        output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),observed_protection_parts:guards.len(),observed_protection_element_visits:visits,
        original_selection_contiguity_verified:true,outside_selected_leaf_contents_exact:true,output_plain_leaf_values_verified:true,
        field_cached_content_edit_qualified:false,full_protection_native_or_execution_authority:false};
    let mut count=Output {bytes:None,length:0,maximum:index.limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
    Ok(SourceLiteralReplacementCandidate {artifact,receipt})
}
fn append(target:&mut String,value:&str,maximum:usize)->Result<(),E> {
    target.len().checked_add(value.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;target.try_reserve(value.len()).map_err(|_|E::Limit)?;target.push_str(value);Ok(())
}
fn selected_origins(index:&SourceTextIndex<'_>,m:&super::SourceSearchMatch)->Result<BTreeSet<usize>,E> {
        if m.zero_width||!m.source_scalar_selection_exact{return Err(E::Selection);}
        let block=index.blocks.get(m.block_index).ok_or(E::Selection)?;let mut origins=BTreeSet::new();
        for unit in block.units.get(m.start_normalized_scalar..m.end_normalized_scalar).ok_or(E::Selection)? {origins.extend(unit.origins.iter().copied());}
        let first=*origins.first().ok_or(E::Selection)?;let last=*origins.last().ok_or(E::Selection)?;
        if last-first+1!=origins.len(){return Err(E::Selection);}
    Ok(origins)
}
fn plain_leaf(xml:&PreservingXmlDocument,index:usize)->Result<String,E> {
    let node=xml.elements().get(index).ok_or(E::Selection)?;
    if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!="t"||node.first_child().is_some(){return Err(E::Selection);}
    let mut text=String::new();if node.is_empty(){return Ok(text);}
    for token in &xml.tokens()[node.start_token()+1..node.end_token().ok_or(E::Selection)?] {
        if token.element_index()!=Some(index)||!matches!(token.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference){return Err(E::Selection);}
        let raw=xml.source_text(token.span()).map_err(|_|E::Selection)?;
        let normalized=raw.replace("\r\n","\n").replace('\r',"\n");let decoded=quick_xml::escape::unescape(&normalized).map_err(|_|E::Value)?;
        append(&mut text,&decoded,PatchLimits::HARD_MAX_VALUE_BYTES)?;
    }Ok(text)
}
fn field_intervals<'a>(source:&'a crate::document_import::ImportedSourcePackage,fields:&ImportedDocumentFields<'_>)->Result<BTreeMap<&'a PackagePath,Vec<(usize,usize)>>,E> {
    let mut all:BTreeMap<&PackagePath,Vec<(usize,usize)>>=BTreeMap::new();
    for field in fields.fields() {let begin=source.resolve_anchor(&field.begin_anchor).map_err(|_|E::Source)?;let end=source.resolve_anchor(&field.end_anchor).map_err(|_|E::Source)?;
        if begin.part().path()!=end.part().path(){return Err(E::Source);}
        let start=begin.element().ok_or(E::Source)?.start_tag_span().start();let stop=end.element().ok_or(E::Source)?.start_tag_span().start();
        if start>=stop{return Err(E::Source);}all.entry(begin.part().path()).or_default().push((start,stop));
    }
    for intervals in all.values_mut() {intervals.sort_unstable();let mut merged:Vec<(usize,usize)>=Vec::new();
        for &(start,end) in intervals.iter() {if let Some(last)=merged.last_mut(){if start<=last.1 {last.1=last.1.max(end);continue;}}merged.push((start,end));}*intervals=merged;}
    Ok(all)
}
