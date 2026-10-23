//! Scoped declared-font edits. Clone shared properties; never mutate their unselected users.
mod catalog;
mod readback;
pub mod inventory;
pub mod filtered;
use super::*;
use crate::{CharacterStyleCatalog,BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageGraphLimits,
    PreservationRuleProfile,PreservingPatchEngine,PreservingWriter};
use crate::document_import::fields::semantics::{ImportedDocumentFieldSemantics,
    catalog::{ImportedDocumentCatalog,fonts::{ImportedDocumentFonts,ImportedFontLanguage as L,
        names::{FontNameReplacementQuery,FontNameResolutionError,FontNameResolutionReceipt},
        replacement::{require_binary_resources,FontReferenceReplacementError}}}};
use std::io::Cursor;
use serde::Deserialize;
pub const SCOPED_FONT_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-font-replacement/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize,Deserialize)]
#[serde(rename_all="snake_case")]
pub enum SourceFontStyleAxis {RunProperty,TextStyle}
#[derive(Debug,Error)]
pub enum SourceFontReplacementError {
    #[error("SCOPED_FONT_SOURCE_REJECTED")]Source,
    #[error("SCOPED_FONT_NAME_REJECTED:{0}")]Name(#[from]FontNameResolutionError),
    #[error("SCOPED_FONT_SEARCH_REJECTED:{0}")]Search(#[from]SourceSearchError),
    #[error("SCOPED_FONT_COMPILE_REJECTED:{0}")]Compile(#[from]E),
    #[error("SCOPED_FONT_BINARY_REJECTED:{0}")]Binary(#[from]FontReferenceReplacementError),
}
type F=SourceFontReplacementError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceFontReplacementReceipt {
    pub profile:&'static str,pub names:FontNameResolutionReceipt,pub source_index_sha256:[u8;32],
    pub selector:SourceIndexScopeReceipt,pub body_policy:SourceReviewTextPolicy,pub axis:SourceFontStyleAxis,
    pub request_sha256:[u8;32],pub cloned_character_properties:usize,pub changed_source_scalars:usize,
    pub changed_parts:usize,pub compiled_edits_sha256:[u8;32],pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub original_text_controls_and_nonselected_references_preserved:bool,pub original_declarations_and_font_resources_preserved:bool,
    pub native_cascade_fallback_visibility_or_service_execution_qualified:bool,
}
pub struct SourceFontReplacementCandidate {artifact:PackageArtifact,receipt:SourceFontReplacementReceipt,edit_inventory:inventory::SourceFontEditInventory}
impl fmt::Debug for SourceFontReplacementCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceFontReplacementCandidate(<redacted>; declared_axis_not_native_cascade_or_authority)")}}
impl SourceFontReplacementCandidate {
    #[must_use]pub const fn receipt(&self)->&SourceFontReplacementReceipt{&self.receipt}
    #[must_use]pub const fn edit_inventory(&self)->&inventory::SourceFontEditInventory{&self.edit_inventory}
    /// # Errors
    /// Writer integrity only. Stored service consumers still need fresh ACL/head/AEAD/route checks.
    pub fn with_verified_bytes<T>(&self,f:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(f)}
}
struct FontPlan {edits:Edits,selected:BTreeMap<usize,u32>,before:Vec<verify::PointValue>,characters:CharacterStyleCatalog,
    clones:usize,bytes:usize,fragments:usize}
impl ImportedDocumentForms {
    /// # Errors
    /// Fresh source, exact policy-filtered windows and explicit run/text axis; no inferred fallback.
    pub fn lower_scoped_font_candidate(&self,fresh:&[u8],query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceFontReplacementCandidate,F>{
        query.validate(128)?;
        if query.query.len()>limits.0.query_bytes||query.replacement.len()>limits.0.query_bytes{return Err(FontNameResolutionError::Limit.into());}
        self.reconstruct_source_for_verification(fresh).map_err(|_|F::Source)?
            .lower_scoped_font_candidate(self,query,selector,policy,axis,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One original proof; original shared definitions survive unchanged, selected slices get clones.
    pub fn lower_scoped_font_candidate(&self,original:&ImportedDocumentForms,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceFontReplacementCandidate,F>{
        self.lower_scoped_font_candidate_checked(original,query,selector,policy,axis,None,limits,writer).map(|(candidate,_)|candidate)
    }
    fn lower_scoped_font_candidate_checked(&self,original:&ImportedDocumentForms,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:Option<crate::document_import::search::reviews::selector::styles::SourceReviewStyleFilter>,
        limits:SourceSearchLimits,writer:WriterLimits)->Result<(SourceFontReplacementCandidate,Option<filtered::SourceFontFilterReceipt>),F>{
        query.validate(128)?;
        if query.query.len()>limits.0.query_bytes||query.replacement.len()>limits.0.query_bytes{return Err(FontNameResolutionError::Limit.into());}
        let rebuilt=self.for_original(original).map_err(|_|F::Source)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|F::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|F::Source)?;
        let scope_index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(scope,windows,_,_)=scope_index.transformation_windows(selector,policy)?;let index=scope_index.source_index();
        let source=original.source();let source_parts:BTreeMap<_,_>=source.parts().iter().map(|p|(p.path(),p)).collect();
        let meanings=ImportedDocumentFieldSemantics::import(&fields).map_err(|_|F::Source)?;
        let original_catalog=ImportedDocumentCatalog::import(&meanings).map_err(|_|F::Source)?;
        let fonts=ImportedDocumentFonts::import(&original_catalog).map_err(|_|F::Source)?;
        source.observe_protection_signals().and_then(|p|p.require_no_observed_document_signals()).map_err(|_|E::Protection)?;
        require_binary_resources(&fonts)?;
        let before=verify::values(index)?;
        let(origins,filter_receipt)=if let Some(filter)=filter{let(origins,receipt)=filtered::select(index,&windows,filter)?;(origins,Some(receipt))}
        else{let mut origins=BTreeSet::new();
            for(&block,&(a,b))in &windows {for unit in index.blocks.get(block).and_then(|block|block.units.get(a..b)).ok_or(E::Selection)?{
                origins.extend(unit.origins.iter().copied());}}(origins,None)};
        let mut leaves:BTreeMap<usize,(PackagePath,usize,usize,u32)>=BTreeMap::new();let mut guards=BTreeMap::new();
        for &origin in &origins {
            if !matches!(before.get(origin).ok_or(E::Selection)?.scalar,verify::Scalar::Text(_)){continue;}
            let point=index.points.get(origin).ok_or(E::Selection)?;if leaves.contains_key(&point.segment){continue;}
            let resolved=source.resolve_anchor(&index.segments[point.segment]).map_err(|_|E::Selection)?;
            let part=resolved.part();let xml=part.xml().ok_or(E::Source)?;let text=resolved.element_index().ok_or(E::Selection)?;
            let run=xml.elements()[text].parent().ok_or(E::Selection)?;
            if !guards.contains_key(part.path()){
                let protected=crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?;
                let mut uncertain=Vec::with_capacity(xml.elements().len());
                let mut tracked=Vec::with_capacity(xml.elements().len());
                for node in xml.elements(){let parent=node.parent().map(|i|uncertain.get(i).copied().ok_or(E::Selection)).transpose()?.unwrap_or(false);
                    let local=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.name().local_name()=="ctrl"
                        &&node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charStyleIDRef");uncertain.push(parent||local);
                    let inherited=node.parent().map(|i|tracked.get(i).copied().ok_or(E::Selection)).transpose()?.unwrap_or(false);
                    let marker=match node.name().local_name(){"p"=>Some("paraTcId"),"run"=>Some("charTcId"),_=>None};
                    let observed=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
                        &&marker.is_some_and(|name|node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()==name));
                    tracked.push(inherited||observed);}
                guards.insert(part.path().clone(),(protected,uncertain,tracked));
            }
            if guards[part.path()].1[text]{return Err(E::Selection.into());}
            if guards[part.path()].2[text]{return Err(E::Protection.into());}
            let value=&before[origin];let old=match axis{
                SourceFontStyleAxis::RunProperty=>{if value.text.is_some(){return Err(E::Selection.into());}value.run},
                SourceFontStyleAxis::TextStyle=>value.text,
            }.ok_or(E::Selection)?;
            leaves.insert(point.segment,(part.path().clone(),text,run,old));
        }
        let names=fonts.resolve_name_replacements_with_budget(query,128,limits.0.query_bytes,limits.0.pattern_bytes,limits.0.dfa_bytes)?;
        let mapping:BTreeMap<_,_>=names.mappings().iter().map(|m|((m.language,m.from_native_id),m.to_native_id)).collect();
        let mut needed=BTreeSet::new();
        for(_,_,_,old)in leaves.values(){let style=original_catalog.character_catalog().styles.get(*old as usize).filter(|s|s.id==*old).ok_or(E::Selection)?;
            if catalog::remap(style.clone(),&mapping)!=*style{needed.insert(*old);}}
        if needed.is_empty(){return Err(E::NoMatches.into());}
        let mut plan=FontPlan{edits:BTreeMap::new(),selected:BTreeMap::new(),before,characters:original_catalog.character_catalog().clone(),clones:0,bytes:0,fragments:0};
        let mut edit_inventory=inventory::Builder::new(axis);
        let(mut intents,targets)=catalog::clone_properties(source,&original_catalog,&needed,&mapping,&mut plan,index.limits.0.result_bytes,&mut edit_inventory)?;
        let context=review::ReviewWriteContext::new(source,&fields,&review,policy)?;let intervals=context.field_intervals(source,&fields)?;
        let mut selected_ranges:BTreeMap<usize,Ranges>=BTreeMap::new();
        for origin in origins {
            if !matches!(plan.before[origin].scalar,verify::Scalar::Text(_)){continue;}
            let p=index.points[origin];let(path,text,run,old)=leaves.get(&p.segment).ok_or(E::Selection)?;
            let Some(&target)=targets.get(old)else{continue;};
            if plan.selected.len()>=limits.0.matches{return Err(E::Limit.into());}plan.selected.insert(origin,target);
            let part=source_parts.get(path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
            if guards[path].0[*text]{return Err(E::Protection.into());}
            let at=xml.elements()[*text].start_tag_span().start();if let Some(ranges)=intervals.get(path){let i=ranges.partition_point(|(a,_)|*a<at);if i>0&&at<ranges[i-1].1{return Err(E::FieldContent.into());}}
            if xml.elements()[*run].attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="charTcId"){return Err(E::Protection.into());}
            let ranges=selected_ranges.entry(p.segment).or_default().entry(*text).or_default();
            if let Some(last)=ranges.last_mut()&&last.0==p.atom&&last.2==p.scalar{last.2=last.2.checked_add(1).ok_or(E::Limit)?;}
            else{ranges.push((p.atom,p.scalar,p.scalar.checked_add(1).ok_or(E::Limit)?));}
        }
        let mut runs:BTreeMap<PackagePath,BTreeMap<usize,(usize,u32,Ranges)>>=BTreeMap::new();
        for(segment,ranges)in selected_ranges {
            let(path,text,run,old)=&leaves[&segment];let target=targets[old];let part=source_parts.get(path).ok_or(E::Source)?;
            let xml=part.xml().ok_or(E::Source)?;
            match axis{
                SourceFontStyleAxis::TextStyle=>{let pieces=super::text::render::text(xml,*text,&ranges[text],target,index.limits.0.result_bytes)?;
                    let edit=edit(xml.elements()[*text].outer_span().ok_or(E::Selection)?.end(),pieces,&mut plan,index.limits.0.result_bytes)?;
                    plan.edits.entry(path.clone()).or_default().insert(xml.elements()[*text].start_tag_span().start(),edit);},
                SourceFontStyleAxis::RunProperty=>{let entry=runs.entry(path.clone()).or_default().entry(xml.elements()[*run].start_tag_span().start())
                    .or_insert_with(||(*run,target,BTreeMap::new()));entry.2.extend(ranges);},
            }
        }
        for(path,runs)in runs{let part=source_parts.get(&path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;let mut overlays=BTreeMap::new();
            for(start,(run,target,ranges))in runs.into_iter().rev(){let outer=xml.elements()[run].outer_span().ok_or(E::Selection)?;
                let pieces=super::render::run(xml,run,&ranges,target,&overlays,index.limits.0.result_bytes)?;
                let compiled=edit(outer.end(),pieces,&mut plan,index.limits.0.result_bytes)?;
                let covered:Vec<_>=overlays.range(start..outer.end()).map(|(at,_)|*at).collect();for at in covered{overlays.remove(&at);}overlays.insert(start,compiled);}
            plan.edits.insert(path,overlays);
        }
        for(path,edits)in &plan.edits{if path.as_str()=="Contents/header.xml"{continue;}
            let part=source_parts.get(path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
            for(&start,edit)in edits{let i=xml.elements().binary_search_by_key(&start,|e|e.start_tag_span().start()).map_err(|_|E::Selection)?;
                edit_inventory.body(part,i,edit)?;
                intents.push(PatchIntent::SpliceElements{target:XmlElementSelector::bind(path,xml,i).map_err(|_|E::Selection)?,position:ElementSplicePosition::Subtree,fragments:edit.fragments.clone()});}}
        if intents.len()>PatchLimits::default().config().max_intents{return Err(E::Limit.into());}
        let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(rebuilt.source().original.as_ref()),zip).map_err(|_|E::Source)?;
        let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),IdRuleProfile::hwpml_2011_scoped_font_v11(),
            IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,&intents).map_err(|e|E::Patch(e.code()))?;
        if patch.changed_parts()!=plan.edits.len()||patch.added_parts()!=0||patch.parts().iter().any(|p|!plan.edits.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation.into());}
        let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
        readback::verify(index,&plan,axis,&artifact,&context)?;
        let mut hash=Output{bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        let edits:Vec<_>=plan.edits.iter().flat_map(|(p,edits)|edits.iter().map(move |(a,e)|(p.as_str(),*a,e.end,<[u8;32]>::from(Sha256::digest(&e.bytes))))).collect();
        serde_json::to_writer(&mut hash,&edits).map_err(|_|E::Limit)?;let compiled_edits_sha256=Sha256::digest(hash.bytes.ok_or(E::Limit)?).into();
        let mut binding=Output{bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SCOPED_FONT_REPLACEMENT_PROFILE,names.receipt(),&scope,policy,axis,compiled_edits_sha256)).map_err(|_|E::Limit)?;
        let receipt=SourceFontReplacementReceipt{profile:SCOPED_FONT_REPLACEMENT_PROFILE,names:names.receipt().clone(),source_index_sha256:index.receipt.index_sha256,
            selector:scope,body_policy:policy,axis,request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),cloned_character_properties:plan.clones,
            changed_source_scalars:plan.selected.len(),changed_parts:plan.edits.len(),compiled_edits_sha256,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            original_text_controls_and_nonselected_references_preserved:true,original_declarations_and_font_resources_preserved:true,native_cascade_fallback_visibility_or_service_execution_qualified:false};
        let edit_inventory=edit_inventory.finish(&receipt,intents.len())?;
        Ok((SourceFontReplacementCandidate{artifact,receipt,edit_inventory},filter_receipt))
    }
}
fn edit(end:usize,pieces:Vec<String>,plan:&mut FontPlan,maximum:usize)->Result<Edit,E>{
    let mut bytes=Vec::new();let mut fragments=Vec::new();for piece in pieces{
        plan.fragments=plan.fragments.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
        plan.bytes=plan.bytes.checked_add(piece.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;
        bytes.extend_from_slice(piece.as_bytes());fragments.push(ValidatedXmlFragment::parse(piece.as_bytes(),PatchLimits::default()).map_err(|_|E::Selection)?);
    }Ok(Edit{end,bytes,fragments})
}
