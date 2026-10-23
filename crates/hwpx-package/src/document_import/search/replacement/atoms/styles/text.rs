//! Explicit text character-style reference edits; original run and paragraph shells are not changed.
pub(super) mod render;
pub(in crate::document_import::search::replacement::atoms) mod output;
use super::*;
pub const SOURCE_TEXT_STYLE_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-text-style-replacement/v1";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceTextStyleReplacementReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,
    #[serde(serialize_with="crate::document_import::search::inspection::definitions::font_details::output::review")]
    pub filter:SourceReviewStyleFilter,pub text_character_style:u32,pub target_declaration:SourceAnchorHandle,
    pub search_request_sha256:[u8;32],pub replacement_request_sha256:[u8;32],pub matched_occurrences:usize,pub match_regions:Vec<SourceTextRegion>,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,
    pub original_changed_text_elements:usize,pub generated_text_fragments:usize,pub changed_source_scalar_ranges:usize,pub changed_parts:usize,
    pub compiled_fragment_bytes:usize,pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub original_scalars_controls_and_run_references_preserved:bool,pub every_original_scalar_text_style_read_back:bool,
    pub outside_original_text_edits_exact:bool,pub original_run_boundaries_preserved:bool,
    pub effective_paragraph_named_style_native_or_service_authority:bool,
}
pub struct SourceTextStyleReplacementCandidate {artifact:PackageArtifact,receipt:SourceTextStyleReplacementReceipt,splice_inventory:intents::SourceStyleSpliceInventory}
impl fmt::Debug for SourceTextStyleReplacementCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceTextStyleReplacementCandidate(<redacted>; explicit_text_axis_only)")}}
impl SourceTextStyleReplacementCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceTextStyleReplacementReceipt {&self.receipt}
    /// Metadata only. Stored consumers must use their current-access verified delivery method.
    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceStyleSpliceInventory {&self.splice_inventory}
    /// # Errors
    /// Writer integrity only; not stored authorization, revision CAS or effective formatting.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Exact source Text contributors and an existing original character declaration are required.
    pub fn lower_review_selector_text_style_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,text_character_style:u32,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceTextStyleReplacementCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|R::Source)?
            .lower_review_selector_text_style_candidate(self,query,selector,policy,filter,text_character_style,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One exact original proof, review/style search, preserving transaction and complete output import.
    pub fn lower_review_selector_text_style_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,text_character_style:u32,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceTextStyleReplacementCandidate,R> {
        let rebuilt=self.for_original(original).map_err(|_|R::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|R::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|R::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        // Both admitted explicit character axes resolve to the original typed character-property domain.
        let(found,declaration)=index.find_style_for_character_replacement(query,selector,policy,filter.clone(),text_character_style)?;
        let text=index.source_index();let search=found.search();let result=search.result();
        if result.matches().is_empty(){return Err(E::NoMatches.into());}
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let plan=compile_text(text,&fields,&context,result,text_character_style)?;let mut intents=Vec::new();let mut parts=BTreeMap::new();
        let source=text.original.source();
        let mut splice_targets=intents::Builder::new(intents::StyleSpliceAxis::TextCharacterStyle);
        for(path,edits)in &plan.edits {
            let part=source.parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
            for(&start,edit)in edits {
                let i=xml.elements().binary_search_by_key(&start,|e|e.start_tag_span().start()).map_err(|_|E::Selection)?;
                intents.push(PatchIntent::SpliceElements {target:XmlElementSelector::bind(path,xml,i).map_err(|_|E::Selection)?,position:ElementSplicePosition::Subtree,fragments:edit.fragments.clone()});
                splice_targets.observe(part,i,edit)?;
            }parts.insert(part.path(),());
        }
        let artifact=output::build(source,rebuilt.source().original.as_ref(),&intents,&parts,writer)?;
        let output_review=readback(text,&plan,text_character_style,&artifact,&context)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_TEXT_STYLE_REPLACEMENT_PROFILE,search.request_sha256(),text_character_style,&declaration)).map_err(|_|E::Limit)?;
        let receipt=SourceTextStyleReplacementReceipt {profile:SOURCE_TEXT_STYLE_REPLACEMENT_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),body_policy:policy,filter,text_character_style,target_declaration:declaration,
            search_request_sha256:search.request_sha256(),replacement_request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),matched_occurrences:result.matches().len(),match_regions:search.match_regions().to_vec(),
            source_review_import:review.receipt().clone(),output_review_import:output_review,original_changed_text_elements:plan.leaves,generated_text_fragments:plan.fragments,
            changed_source_scalar_ranges:plan.ranges,changed_parts:plan.edits.len(),compiled_fragment_bytes:plan.bytes,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,
            original_scalars_controls_and_run_references_preserved:true,every_original_scalar_text_style_read_back:true,
            outside_original_text_edits_exact:true,original_run_boundaries_preserved:true,effective_paragraph_named_style_native_or_service_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        let splice_inventory=splice_targets.finish(receipt.source_package_sha256,receipt.output_package_sha256,&receipt,intents.len(),limits.0.result_bytes)?;
        Ok(SourceTextStyleReplacementCandidate {artifact,receipt,splice_inventory})
    }
}
struct TextPlan {edits:Edits,selected:BTreeSet<usize>,leaves:usize,fragments:usize,ranges:usize,bytes:usize,protection_parts:usize,visits:usize}
fn compile_text(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,found:&crate::document_import::search::SourceSearchResult,target:u32)->Result<TextPlan,E> {
    let mut leaves:BTreeMap<usize,Vec<(u32,u32,u32)>>=BTreeMap::new();let mut selected=BTreeSet::new();let mut count=0usize;
    for m in found.matches() {for origin in selected_origins(index,m)? {
        if !selected.insert(origin){return Err(E::Selection);}let p=index.points[origin];let ranges=leaves.entry(p.segment).or_default();
        if let Some(last)=ranges.last_mut()&&last.0==p.atom&&last.2==p.scalar {last.2=last.2.checked_add(1).ok_or(E::Limit)?;continue;}
        count=count.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
        ranges.push((p.atom,p.scalar,p.scalar.checked_add(1).ok_or(E::Limit)?));
    }}
    let source=index.original.source();let intervals=context.field_intervals(source,fields)?;let mut guards=BTreeMap::new();
    let mut plan=TextPlan {edits:BTreeMap::new(),selected,leaves:0,fragments:0,ranges:count,bytes:0,protection_parts:0,visits:0};
    for(segment,ranges)in leaves {
        let resolved=source.resolve_anchor(&index.segments[segment]).map_err(|_|E::Selection)?;let part=resolved.part();let xml=part.xml().ok_or(E::Source)?;
        let text=resolved.element_index().ok_or(E::Selection)?;let run=xml.elements()[text].parent().ok_or(E::Selection)?;
        if !guards.contains_key(part.path()) {
            plan.visits=plan.visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            guards.insert(part.path(),crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?);
        }
        if guards.get(part.path()).and_then(|g|g.get(text)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
        let at=xml.elements()[text].start_tag_span().start();if let Some(ranges)=intervals.get(part.path()) {let i=ranges.partition_point(|(a,_)|*a<at);if i>0&&at<ranges[i-1].1{return Err(E::FieldContent);}}
        if xml.elements()[run].attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charTcId"){return Err(E::Protection);}
        let span=crate::text_flow::read_source_text_span(xml,text).map_err(|_|E::Selection)?;
        if ranges.iter().any(|(a,_,_)|!matches!(span.atoms.get(*a as usize),Some(TextAtom::Text(_)))){return Err(E::Selection);}
        if super::render::reference(&xml.elements()[text],"charStyleIDRef")?==Some(target){continue;}
        let outer=xml.elements()[text].outer_span().ok_or(E::Selection)?;let rendered=render::text(xml,text,&ranges,target,index.limits.0.result_bytes)?;
        let mut bytes=Vec::new();let mut fragments=Vec::new();
        for fragment in rendered {
            plan.fragments=plan.fragments.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            plan.bytes=plan.bytes.checked_add(fragment.len()).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
            bytes.extend_from_slice(fragment.as_bytes());fragments.push(ValidatedXmlFragment::parse(fragment.as_bytes(),PatchLimits::default()).map_err(|_|E::Selection)?);
        }
        plan.leaves+=1;plan.edits.entry(part.path().clone()).or_default().insert(outer.start(),Edit {end:outer.end(),bytes,fragments});
    }
    if plan.edits.is_empty(){return Err(E::NoChange);}plan.protection_parts=guards.len();Ok(plan)
}
fn readback(index:&SourceTextIndex<'_>,plan:&TextPlan,target:u32,artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<ReviewBodyImportReceipt,E> {
    artifact.with_verified_bytes(|bytes|->Result<ReviewBodyImportReceipt,E>{
        let source=index.original.source();let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(&rebuilt,&fields).map_err(|_|E::Readback)?;
        let output_review=context.readback_receipt(review.receipt())?;
        for(path,edits)in &plan.edits {
            let old=source.parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            old.with_source_bytes(|a|new.with_source_bytes(|b|->Result<(),E>{let(mut left,mut right)=(0usize,0usize);
                for(&start,edit)in edits {
                    let edge=right.checked_add(start.checked_sub(left).ok_or(E::Readback)?).ok_or(E::Limit)?;
                    if a.get(left..start)!=b.get(right..edge){return Err(E::Preservation);}
                    let end=edge.checked_add(edit.bytes.len()).ok_or(E::Limit)?;if b.get(edge..end)!=Some(edit.bytes.as_slice()){return Err(E::Readback);}
                    left=edit.end;right=end;
                }if a.get(left..)!=b.get(right..){return Err(E::Preservation);}Ok(())
            }))?;
        }
        let after=SourceReviewScopeIndex::from_review(&rebuilt,&review,index.limits).map_err(|_|E::Readback)?;let after=after.source_index();
        if index.blocks.len()!=after.blocks.len()||index.blocks.iter().zip(&after.blocks).any(|(a,b)|a.text!=b.text){return Err(E::Readback);}
        let before=super::verify::values(index)?;let after=super::verify::values(after)?;if before.len()!=after.len(){return Err(E::Readback);}
        for(i,(before,after))in before.into_iter().zip(after).enumerate() {
            if before.scalar!=after.scalar||before.run!=after.run||after.text!=if plan.selected.contains(&i){Some(target)}else{before.text}{return Err(E::Readback);}
        }Ok(output_review)
    }).map_err(|_|E::Writer)?
}
