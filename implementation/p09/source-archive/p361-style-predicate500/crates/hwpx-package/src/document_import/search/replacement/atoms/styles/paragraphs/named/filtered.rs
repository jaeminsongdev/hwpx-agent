//! A whole-paragraph predicate over actual indexed source text; no vacuous empty match or cascade.
use super::*;
use crate::document_import::search::inspection::{SourceInspectionReceipt,definitions::SourceStyleDefinitionReceipt};
pub const FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE:&str="hwpx-agent.source-filtered-named-paragraph-style-replacement/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceNamedParagraphFilterReceipt{
    pub filter:SourceReviewStyleFilter,pub inspection:SourceInspectionReceipt,pub definitions:Option<SourceStyleDefinitionReceipt>,
    pub extent:&'static str,pub examined_normalized_units:usize,pub examined_source_segments:usize,
    pub selected_paragraphs:usize,pub filtered_paragraphs:usize,pub empty_paragraphs:usize,
    pub effective_style_visibility_or_execution_authority:bool,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceFilteredNamedParagraphStyleReceipt{
    pub profile:&'static str,pub source:SourceNamedParagraphStyleReceipt,pub style_filter:SourceNamedParagraphFilterReceipt,
    pub request_sha256:[u8;32],pub full_style_native_or_service_authority:bool,
}
pub struct SourceFilteredNamedParagraphStyleCandidate{candidate:SourceNamedParagraphStyleCandidate,receipt:SourceFilteredNamedParagraphStyleReceipt}
impl fmt::Debug for SourceFilteredNamedParagraphStyleCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceFilteredNamedParagraphStyleCandidate(<redacted>; not_effective_style_or_authority)")}}
impl SourceFilteredNamedParagraphStyleCandidate{
    #[must_use]pub const fn receipt(&self)->&SourceFilteredNamedParagraphStyleReceipt{&self.receipt}
    /// # Errors
    /// Writer integrity only. Does not grant current service access, execution or commit authority.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.candidate.with_verified_bytes(consume)}
    fn finish(candidate:SourceNamedParagraphStyleCandidate,style_filter:SourceNamedParagraphFilterReceipt,maximum:usize)->Result<Self,N>{
        let request_sha256=bounded_hash(&(FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE,candidate.receipt(),&style_filter),maximum)?;
        let receipt=SourceFilteredNamedParagraphStyleReceipt{profile:FILTERED_NAMED_PARAGRAPH_STYLE_PROFILE,source:candidate.receipt().clone(),style_filter,request_sha256,full_style_native_or_service_authority:false};
        let mut count=Output{bytes:None,length:0,maximum};serde_json::to_writer(&mut count,&receipt).map_err(|_|N::Limit)?;
        Ok(Self{candidate,receipt})
    }
}
impl ImportedDocumentForms{
    /// # Errors
    /// Strict declared/definition filters over fresh source; every indexed unit in a paragraph must match.
    pub fn lower_filtered_named_paragraph_style_candidate(&self,fresh:&[u8],query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceFilteredNamedParagraphStyleCandidate,N>{
        filter.validate()?;query.validate()?;check_budget(query,limits)?;
        self.reconstruct_source_for_verification(fresh).map_err(|_|N::Source)?
            .lower_filtered_named_paragraph_style_candidate(self,query,selector,policy,filter,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_>{
    /// # Errors
    /// One source proof/catalog/review index/compiler/output. No per-paragraph reconstruction or query replay.
    pub fn lower_filtered_named_paragraph_style_candidate(&self,original:&ImportedDocumentForms,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:SourceReviewStyleFilter,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceFilteredNamedParagraphStyleCandidate,N>{
        filter.validate()?;
        let(candidate,receipt)=self.lower_named_paragraph_style_candidate_checked(original,query,selector,policy,Some(filter),limits,writer)?;
        SourceFilteredNamedParagraphStyleCandidate::finish(candidate,receipt.ok_or(SourceSearchError::Mapping)?,limits.0.result_bytes)
    }
}
pub(super) fn select(index:&SourceTextIndex<'_>,windows:&BTreeMap<usize,(usize,usize)>,filter:SourceReviewStyleFilter)
    ->Result<(BTreeSet<domain_ir::LogicalId>,SourceNamedParagraphFilterReceipt),N>{
    filter.validate()?;let inspection=index.inspection()?;
    let definitions=if matches!(filter,SourceReviewStyleFilter::Definition(_)){Some(inspection.resolve_style_definitions()?)}else{None};
    // Reference/definition predicates depend on a segment, not a scalar offset. Cache once per segment.
    let mut accepts=vec![None;index.segments.len()];let mut singleton=BTreeSet::new();
    let mut paragraphs=BTreeMap::new();let(mut units,mut segments)=(0usize,0usize);
    for(&block,&(start,end))in windows{
        let b=index.blocks.get(block).ok_or(SourceSearchError::Mapping)?;
        let entry=paragraphs.entry(b.paragraph.opaque_handle.clone()).or_insert((false,true));
        for unit in b.units.get(start..end).ok_or(SourceSearchError::Mapping)?{
            if unit.origins.is_empty(){return Err(SourceSearchError::Mapping.into());}entry.0=true;units+=1;
            for &origin in &unit.origins{
                let segment=index.points.get(origin).ok_or(SourceSearchError::Mapping)?.segment;
                let cached=accepts.get_mut(segment).ok_or(SourceSearchError::Mapping)?;
                let accepted=if let Some(v)=*cached{v}else{
                    singleton.clear();singleton.insert(origin);segments+=1;
                    let v=match filter{SourceReviewStyleFilter::Declared(f)=>inspection.accepts_declared_points(&singleton,f),
                        SourceReviewStyleFilter::Definition(f)=>definitions.as_ref().ok_or(SourceSearchError::Mapping)?.accepts_points(&singleton,f)};
                    *cached=Some(v);v
                };entry.1&=accepted;
            }
        }
    }
    let mut allowed=BTreeSet::new();let(mut filtered,mut empty)=(0usize,0usize);
    for(id,(has_units,all))in paragraphs{if !has_units{empty+=1;}else if all{allowed.insert(id);}else{filtered+=1;}}
    let receipt=SourceNamedParagraphFilterReceipt{filter,inspection:inspection.receipt().clone(),definitions:definitions.as_ref().map(|d|d.receipt().clone()),
        extent:"all_indexed_source_units_of_whole_paragraph",examined_normalized_units:units,examined_source_segments:segments,
        selected_paragraphs:allowed.len(),filtered_paragraphs:filtered,empty_paragraphs:empty,effective_style_visibility_or_execution_authority:false};
    Ok((allowed,receipt))
}
fn bounded_hash(value:&impl Serialize,maximum:usize)->Result<[u8;32],N>{
    struct Hash{state:Sha256,length:usize,maximum:usize}
    impl std::io::Write for Hash{
        fn write(&mut self,b:&[u8])->std::io::Result<usize>{let n=self.length.checked_add(b.len()).filter(|n|*n<=self.maximum).ok_or_else(||std::io::Error::other("named_filter_limit"))?;
            self.state.update(b);self.length=n;Ok(b.len())}
        fn flush(&mut self)->std::io::Result<()>{Ok(())}
    }
    let mut out=Hash{state:Sha256::new(),length:0,maximum};serde_json::to_writer(&mut out,value).map_err(|_|N::Limit)?;Ok(out.state.finalize().into())
}
