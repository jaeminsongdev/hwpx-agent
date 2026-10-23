//! Explicit original style filters. No inferred cascade, visibility or current-service authority.
use super::*;
use crate::document_import::search::{inspection::{SourceInspectionReceipt,
    definitions::SourceStyleDefinitionReceipt},reviews::selector::styles::SourceReviewStyleFilter};

pub const FILTERED_FONT_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-filtered-font-replacement/v1";

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceFontFilterReceipt {
    #[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::review")]
    pub filter:SourceReviewStyleFilter,pub inspection:SourceInspectionReceipt,
    pub definitions:Option<SourceStyleDefinitionReceipt>,pub selected_normalized_units:usize,
    pub filtered_normalized_units:usize,pub selected_source_points:usize,
    pub effective_style_visibility_or_execution_authority:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceFontFilteredReplacementReceipt {
    pub profile:&'static str,pub source:SourceFontReplacementReceipt,pub style_filter:SourceFontFilterReceipt,
    pub request_sha256:[u8;32],pub service_execution_or_native_qualified:bool,
}
pub struct SourceFontFilteredReplacementCandidate {
    candidate:SourceFontReplacementCandidate,receipt:SourceFontFilteredReplacementReceipt,
}
impl fmt::Debug for SourceFontFilteredReplacementCandidate {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceFontFilteredReplacementCandidate(<redacted>; not_authority)")}
}
impl SourceFontFilteredReplacementCandidate {
    #[must_use]pub const fn receipt(&self)->&SourceFontFilteredReplacementReceipt{&self.receipt}
    #[must_use]pub const fn edit_inventory(&self)->&inventory::SourceFontEditInventory{self.candidate.edit_inventory()}
    /// # Errors
    /// Writer integrity only. This pure result grants no service access, commit or execution.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.candidate.with_verified_bytes(consume)}
    fn finish(candidate:SourceFontReplacementCandidate,style_filter:SourceFontFilterReceipt,maximum:usize)->Result<Self,F>{
        let mut hash=Output{bytes:Some(Vec::new()),length:0,maximum};
        serde_json::to_writer(&mut hash,&(FILTERED_FONT_REPLACEMENT_PROFILE,candidate.receipt(),&style_filter)).map_err(|_|E::Limit)?;
        let receipt=SourceFontFilteredReplacementReceipt{profile:FILTERED_FONT_REPLACEMENT_PROFILE,source:candidate.receipt().clone(),style_filter,
            request_sha256:Sha256::digest(hash.bytes.ok_or(E::Limit)?).into(),service_execution_or_native_qualified:false};
        let mut count=Output{bytes:None,length:0,maximum};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(Self{candidate,receipt})
    }
}
impl ImportedDocumentForms {
    /// # Errors
    /// Strict declared/definition predicates over fresh original NFC windows. No match-all filter.
    pub fn lower_scoped_font_filtered_candidate(&self,fresh:&[u8],query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:SourceReviewStyleFilter,limits:SourceSearchLimits,writer:WriterLimits)
        ->Result<SourceFontFilteredReplacementCandidate,F>{
        filter.validate()?;query.validate(128)?;
        if query.query.len()>limits.0.query_bytes||query.replacement.len()>limits.0.query_bytes{return Err(FontNameResolutionError::Limit.into());}
        self.reconstruct_source_for_verification(fresh).map_err(|_|F::Source)?
            .lower_scoped_font_filtered_candidate(self,query,selector,policy,axis,filter,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Reuses one original proof/index. Every contributing scalar must satisfy the same predicate.
    pub fn lower_scoped_font_filtered_candidate(&self,original:&ImportedDocumentForms,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:SourceReviewStyleFilter,limits:SourceSearchLimits,writer:WriterLimits)
        ->Result<SourceFontFilteredReplacementCandidate,F>{
        filter.validate()?;
        let(candidate,receipt)=self.lower_scoped_font_candidate_checked(original,query,selector,policy,axis,Some(filter),limits,writer)?;
        SourceFontFilteredReplacementCandidate::finish(candidate,receipt.ok_or(E::Selection)?,limits.0.result_bytes)
    }
}

pub(super) fn select(index:&SourceTextIndex<'_>,windows:&BTreeMap<usize,(usize,usize)>,filter:SourceReviewStyleFilter)
    ->Result<(BTreeSet<usize>,SourceFontFilterReceipt),F>{
    filter.validate()?;let inspection=index.inspection()?;
    let definitions=if matches!(filter,SourceReviewStyleFilter::Definition(_)){Some(inspection.resolve_style_definitions()?)}else{None};
    let definition_filter=match &filter {SourceReviewStyleFilter::Definition(f)=>Some(f),_=>None};
    let definition_matcher=definitions.as_ref().zip(definition_filter).map(|(definitions,filter)|definitions.matcher(filter)).transpose()?;
    // One representative per segment: predicates inspect segment references, never text positions.
    // This avoids a predicate allocation or definition/XML resolution for every scalar or NFC unit.
    let mut accepts=vec![None;index.segments.len()];let mut singleton=BTreeSet::new();
    let(mut selected,mut rejected)=(BTreeSet::new(),BTreeSet::new());let(mut allowed_units,mut filtered_units)=(0usize,0usize);
    for(&block,&(start,end))in windows{
        for unit in index.blocks.get(block).and_then(|b|b.units.get(start..end)).ok_or(E::Selection)?{
            if unit.origins.is_empty(){return Err(E::Selection.into());}
            let mut allowed=true;
            for &origin in &unit.origins{
                let segment=index.points.get(origin).ok_or(E::Selection)?.segment;
                let entry=accepts.get_mut(segment).ok_or(E::Selection)?;
                let value=if let Some(value)=*entry{value}else{
                    singleton.clear();singleton.insert(origin);
                    let value=match &filter{
                        SourceReviewStyleFilter::Declared(f)=>inspection.accepts_declared_points(&singleton,*f),
                        SourceReviewStyleFilter::Definition(_)=>definition_matcher.as_ref().ok_or(E::Selection)?(&singleton),
                    };*entry=Some(value);value
                };allowed&=value;
            }
            if allowed{allowed_units+=1;selected.extend(unit.origins.iter().copied());}
            else{filtered_units+=1;rejected.extend(unit.origins.iter().copied());}
        }
    }
    // One original scalar may contribute to several normalized units. Do not partly style it.
    if !selected.is_disjoint(&rejected){return Err(E::Selection.into());}
    drop(definition_matcher);
    let receipt=SourceFontFilterReceipt{filter,inspection:inspection.receipt().clone(),definitions:definitions.as_ref().map(|d|d.receipt().clone()),
        selected_normalized_units:allowed_units,filtered_normalized_units:filtered_units,selected_source_points:selected.len(),
        effective_style_visibility_or_execution_authority:false};
    Ok((selected,receipt))
}
