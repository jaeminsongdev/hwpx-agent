//! Source-bound partial-run character-property replacement; not effective formatting or execution.
mod render;
mod verify;
pub mod text;
pub mod paragraphs;
pub mod intents;
pub mod fonts;
use super::*;
use crate::{ValidatedXmlFragment,ElementSplicePosition};
use crate::document_import::{search::{selector::{SourceIndexScopeSelector,SourceIndexScopeReceipt},reviews::{selector::{SourceReviewScopeIndex,styles::SourceReviewStyleFilter},SourceReviewTextPolicy,SourceTextRegion}},
    structure::review::{ImportedDocumentReviewBodies,ReviewBodyImportReceipt},ImportedSourcePackage};
pub const SOURCE_SELECTOR_STYLE_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-character-style-replacement/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceStyleReplacementError {
    #[error("SOURCE_STYLE_REPLACEMENT_SOURCE_REJECTED")] Source,
    #[error("SOURCE_STYLE_REPLACEMENT_SEARCH_REJECTED:{0}")] Search(#[from] SourceSearchError),
    #[error("SOURCE_STYLE_REPLACEMENT_COMPILER_REJECTED:{0}")] Compile(#[from] SourceLiteralReplacementError),
}
type R=SourceStyleReplacementError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceStyleReplacementReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,
    #[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::review")]
    pub filter:SourceReviewStyleFilter,pub character_property:u32,pub target_declaration:SourceAnchorHandle,
    pub search_request_sha256:[u8;32],pub replacement_request_sha256:[u8;32],pub matched_occurrences:usize,pub match_regions:Vec<SourceTextRegion>,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,
    pub original_changed_runs:usize,pub generated_run_fragments:usize,pub changed_source_scalar_ranges:usize,pub changed_parts:usize,
    pub compiled_fragment_bytes:usize,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub all_original_scalars_and_control_values_preserved:bool,pub every_original_scalar_style_read_back:bool,
    pub outside_original_run_edits_exact:bool,pub original_run_boundaries_not_merged:bool,
    pub paragraph_named_text_style_effective_visibility_or_execution_qualified:bool,pub full_protection_native_or_service_authority:bool,
}
pub struct SourceStyleReplacementCandidate {artifact:PackageArtifact,receipt:SourceStyleReplacementReceipt,splice_inventory:intents::SourceStyleSpliceInventory}
impl fmt::Debug for SourceStyleReplacementCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceStyleReplacementCandidate(<redacted>; declared_character_property_not_effective_style)")}}
impl SourceStyleReplacementCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceStyleReplacementReceipt {&self.receipt}
    /// Metadata only. Stored consumers must use their current-access verified delivery method.
    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceStyleSpliceInventory {&self.splice_inventory}
    /// # Errors
    /// Writer integrity only, not stored access, a revision commit or Native authority.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
struct Edit {end:usize,bytes:Vec<u8>,fragments:Vec<ValidatedXmlFragment>}
type Edits=BTreeMap<PackagePath,BTreeMap<usize,Edit>>;
type Ranges=BTreeMap<usize,Vec<(u32,u32,u32)>>;
struct Run {index:usize,leaves:Ranges}
impl ImportedDocumentForms {
    /// # Errors
    /// Select actual nonempty source style matches and restyle their exact Text scalar ranges.
    pub fn lower_review_selector_style_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,character_property:u32,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceStyleReplacementCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|R::Source)?
            .lower_review_selector_style_candidate(self,query,selector,policy,filter,character_property,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One original proof, field/review/index, style match pass and preserving output transaction.
    pub fn lower_review_selector_style_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,character_property:u32,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceStyleReplacementCandidate,R> {
        let rebuilt=self.for_original(original).map_err(|_|R::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|R::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|R::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(found,declaration)=index.find_style_for_character_replacement(query,selector,policy,filter.clone(),character_property)?;
        let text=index.source_index();let search=found.search();let result=search.result();
        if result.matches().is_empty(){return Err(E::NoMatches.into());}
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let plan=compile(text,&fields,&context,result,character_property)?;
        let mut intents=Vec::new();let mut parts=BTreeMap::new();let source=text.original.source();
        let mut splice_targets=intents::Builder::new(intents::StyleSpliceAxis::RunCharacterProperty);
        for(path,edits)in &plan.edits {
            let part=source.parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
            for(&start,edit)in edits {
                let i=xml.elements().binary_search_by_key(&start,|e|e.start_tag_span().start()).map_err(|_|E::Selection)?;
                intents.push(PatchIntent::SpliceElements {target:XmlElementSelector::bind(path,xml,i).map_err(|_|E::Selection)?,position:ElementSplicePosition::Subtree,fragments:edit.fragments.clone()});
                splice_targets.observe(part,i,edit)?;
            }parts.insert(part.path(),());
        }
        let artifact=super::super::output::build_artifact(source,rebuilt.source().original.as_ref(),&intents,&parts,writer)?;
        let output_review=verify::output(text,&plan,character_property,&artifact,&context)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_SELECTOR_STYLE_REPLACEMENT_PROFILE,search.request_sha256(),character_property,&declaration)).map_err(|_|E::Limit)?;
        let receipt=SourceStyleReplacementReceipt {profile:SOURCE_SELECTOR_STYLE_REPLACEMENT_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),body_policy:policy,filter,character_property,target_declaration:declaration,
            search_request_sha256:search.request_sha256(),replacement_request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),matched_occurrences:result.matches().len(),match_regions:search.match_regions().to_vec(),
            source_review_import:review.receipt().clone(),output_review_import:output_review,
            original_changed_runs:plan.runs,generated_run_fragments:plan.fragments,changed_source_scalar_ranges:plan.ranges,changed_parts:plan.edits.len(),compiled_fragment_bytes:plan.bytes,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,
            all_original_scalars_and_control_values_preserved:true,every_original_scalar_style_read_back:true,outside_original_run_edits_exact:true,original_run_boundaries_not_merged:true,
            paragraph_named_text_style_effective_visibility_or_execution_qualified:false,full_protection_native_or_service_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let splice_inventory=splice_targets.finish(receipt.source_package_sha256,receipt.output_package_sha256,&receipt,intents.len(),limits.0.result_bytes)?;
        Ok(SourceStyleReplacementCandidate {artifact,receipt,splice_inventory})
    }
}
struct Plan {edits:Edits,selected:BTreeSet<usize>,runs:usize,fragments:usize,ranges:usize,bytes:usize,protection_parts:usize,visits:usize}
fn compile(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,found:&crate::document_import::search::SourceSearchResult,target:u32)->Result<Plan,E> {
    let mut leaves:BTreeMap<usize,Vec<(u32,u32,u32)>>=BTreeMap::new();let mut selected=BTreeSet::new();let mut range_count=0usize;
    for m in found.matches() {
        for origin in selected_origins(index,m)? {
            if !selected.insert(origin){return Err(E::Selection);}let p=index.points[origin];let edits=leaves.entry(p.segment).or_default();
            if let Some(last)=edits.last_mut()&&last.0==p.atom&&last.2==p.scalar {last.2=last.2.checked_add(1).ok_or(E::Limit)?;continue;}
            range_count=range_count.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            edits.push((p.atom,p.scalar,p.scalar.checked_add(1).ok_or(E::Limit)?));
        }
    }
    let source=index.original.source();let intervals=context.field_intervals(source,fields)?;
    let mut guards=BTreeMap::new();let mut visits=0usize;let mut runs:BTreeMap<PackagePath,BTreeMap<usize,Run>>=BTreeMap::new();
    for(segment,ranges)in leaves {
        let resolved=source.resolve_anchor(&index.segments[segment]).map_err(|_|E::Selection)?;let part=resolved.part();let xml=part.xml().ok_or(E::Source)?;
        let text=resolved.element_index().ok_or(E::Selection)?;let run=xml.elements()[text].parent().ok_or(E::Selection)?;
        if !guards.contains_key(part.path()) {visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            guards.insert(part.path(),crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?);}
        if guards.get(part.path()).and_then(|g|g.get(text)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
        let at=xml.elements()[text].start_tag_span().start();if let Some(ranges)=intervals.get(part.path()) {let i=ranges.partition_point(|(a,_)|*a<at);if i>0&&at<ranges[i-1].1{return Err(E::FieldContent);}}
        if xml.elements()[run].attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charTcId"){return Err(E::Protection);}
        // Controls are not editable style scalars, even when a query crosses them.
        let span=crate::text_flow::read_source_text_span(xml,text).map_err(|_|E::Selection)?;
        if ranges.iter().any(|(a,_,_)|!matches!(span.atoms.get(*a as usize),Some(TextAtom::Text(_)))){return Err(E::Selection);}
        if render::reference(&xml.elements()[run],"charPrIDRef")?==Some(target){continue;}
        runs.entry(part.path().clone()).or_default().entry(xml.elements()[run].start_tag_span().start()).or_insert_with(||Run {index:run,leaves:BTreeMap::new()}).leaves.insert(text,ranges);
    }
    if runs.is_empty(){return Err(E::NoChange);}
    let mut plan=Plan {edits:BTreeMap::new(),selected,runs:0,fragments:0,ranges:range_count,bytes:0,protection_parts:guards.len(),visits};
    for(path,runs)in runs {
        let part=source.parts().iter().find(|p|p.path()==&path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;let mut overlays=BTreeMap::new();
        // Nested review/note/table runs are rendered before their enclosing source run. Consume
        // child overlays into the enclosing edit so the original patch sees no overlapping ranges.
        for(start,run)in runs.into_iter().rev() {
            let outer=xml.elements()[run.index].outer_span().ok_or(E::Selection)?;
            let rendered=render::run(xml,run.index,&run.leaves,target,&overlays,index.limits.0.result_bytes)?;
            plan.runs+=1;plan.fragments=plan.fragments.checked_add(rendered.len()).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            let mut bytes=Vec::new();let mut fragments=Vec::new();
            for fragment in rendered {
                plan.bytes=plan.bytes.checked_add(fragment.len()).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
                bytes.extend_from_slice(fragment.as_bytes());fragments.push(ValidatedXmlFragment::parse(fragment.as_bytes(),PatchLimits::default()).map_err(|_|E::Selection)?);
            }
            let covered:Vec<_>=overlays.range(start..outer.end()).map(|(a,_)|*a).collect();for a in covered{overlays.remove(&a);}
            overlays.insert(start,Edit {end:outer.end(),bytes,fragments});
        }plan.edits.insert(path,overlays);
    }Ok(plan)
}
