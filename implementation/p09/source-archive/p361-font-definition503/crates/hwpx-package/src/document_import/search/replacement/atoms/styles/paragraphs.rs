//! Explicit whole matched paragraph references; never widen a clipped selector or infer effective styles.
mod verify;
pub mod named;
use super::*;
use crate::{PatchAttributeValue,PatchText,XmlAttributeSelector,XmlElementToken};
pub use crate::document_import::search::inspection::definitions::SourceParagraphStyleTarget;
use serde::Deserialize;
pub const SOURCE_PARAGRAPH_STYLE_REPLACEMENT_PROFILE:&str="hwpx-agent.source-selector-paragraph-style-replacement/v1";
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceParagraphStyleExtent {WholeMatchedParagraphWithinScope}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum SourceParagraphStyleReplacementError {
    #[error("SOURCE_PARAGRAPH_STYLE_SOURCE_REJECTED")] Source,
    #[error("SOURCE_PARAGRAPH_STYLE_SEARCH_REJECTED:{0}")] Search(#[from] SourceSearchError),
    #[error("SOURCE_PARAGRAPH_STYLE_COMPILER_REJECTED:{0}")] Compile(#[from] SourceLiteralReplacementError),
    #[error("SOURCE_PARAGRAPH_STYLE_FULL_PARAGRAPH_OUTSIDE_SCOPE")] IncompleteParagraphScope,
}
type R=SourceParagraphStyleReplacementError;
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphStyleChange {pub paragraph_anchor:SourceAnchorHandle,pub previous_reference:Option<u32>,pub target_reference:u32}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphStyleReplacementReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub selector:SourceIndexScopeReceipt,
    pub body_policy:SourceReviewTextPolicy,pub filter:SourceReviewStyleFilter,pub target:SourceParagraphStyleTarget,pub extent:SourceParagraphStyleExtent,
    pub target_declaration:SourceAnchorHandle,pub search_request_sha256:[u8;32],pub replacement_request_sha256:[u8;32],
    pub matched_occurrences:usize,pub match_regions:Vec<SourceTextRegion>,pub matched_paragraphs:usize,pub changes:Vec<SourceParagraphStyleChange>,
    pub source_review_import:ReviewBodyImportReceipt,pub output_review_import:ReviewBodyImportReceipt,pub changed_parts:usize,pub compiled_attribute_bytes:usize,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub whole_paragraph_scope_verified:bool,pub all_original_scalars_controls_run_and_text_references_preserved:bool,
    pub every_paragraph_reference_read_back:bool,pub outside_selected_attribute_edits_exact:bool,
    pub effective_style_native_or_service_authority:bool,
}
pub struct SourceParagraphStyleReplacementCandidate {artifact:PackageArtifact,receipt:SourceParagraphStyleReplacementReceipt}
impl fmt::Debug for SourceParagraphStyleReplacementCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceParagraphStyleReplacementCandidate(<redacted>; explicit_paragraph_axis_not_effective_style)")}}
impl SourceParagraphStyleReplacementCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceParagraphStyleReplacementReceipt {&self.receipt}
    /// # Errors
    /// Writer integrity only; no current service access, commit or execution authority.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
impl ImportedDocumentForms {
    /// # Errors
    /// Matches select whole paragraphs only when their full indexed extent is in the caller scope.
    pub fn lower_review_selector_paragraph_style_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,target:SourceParagraphStyleTarget,extent:SourceParagraphStyleExtent,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphStyleReplacementCandidate,R> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|R::Source)?
            .lower_review_selector_paragraph_style_candidate(self,query,selector,policy,filter,target,extent,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// One original proof/catalog/search/transaction/output import, no per-match source or header scan.
    pub fn lower_review_selector_paragraph_style_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,
        filter:SourceReviewStyleFilter,target:SourceParagraphStyleTarget,extent:SourceParagraphStyleExtent,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceParagraphStyleReplacementCandidate,R> {
        let rebuilt=self.for_original(original).map_err(|_|R::Source)?;let fields=ImportedDocumentFields::import(original).map_err(|_|R::Source)?;
        let review=ImportedDocumentReviewBodies::import_bound_fields(original,&fields).map_err(|_|R::Source)?;
        let index=SourceReviewScopeIndex::from_review(original,&review,limits)?;
        let(found,declaration,windows)=index.find_style_for_paragraph_replacement(query,selector,policy,filter,target)?;
        let text=index.source_index();let search=found.search();let result=search.result();
        if result.matches().is_empty(){return Err(E::NoMatches.into());}
        let context=review::ReviewWriteContext::new(text.original.source(),&fields,&review,policy)?;
        let plan=compile(text,&fields,&context,result,&windows,target)?;
        let parts=plan.edits.keys().map(|p|(p,())).collect();
        let artifact=super::text::output::build(text.original.source(),rebuilt.source().original.as_ref(),&plan.intents,&parts,writer)?;
        let output_review=verify::output(text,&plan,target,&artifact,&context)?;
        let mut binding=Output {bytes:Some(Vec::new()),length:0,maximum:limits.0.result_bytes};
        serde_json::to_writer(&mut binding,&(SOURCE_PARAGRAPH_STYLE_REPLACEMENT_PROFILE,search.request_sha256(),target,extent,&declaration,&plan.changes)).map_err(|_|E::Limit)?;
        let receipt=SourceParagraphStyleReplacementReceipt {profile:SOURCE_PARAGRAPH_STYLE_REPLACEMENT_PROFILE,source_package_sha256:text.original.source().receipt().source_package_sha256,
            source_index_sha256:text.receipt.index_sha256,selector:search.scope_receipt().clone(),body_policy:policy,filter,target,extent,target_declaration:declaration,
            search_request_sha256:search.request_sha256(),replacement_request_sha256:Sha256::digest(binding.bytes.ok_or(E::Limit)?).into(),matched_occurrences:result.matches().len(),
            match_regions:search.match_regions().to_vec(),matched_paragraphs:plan.matched_paragraphs,changes:plan.changes,source_review_import:review.receipt().clone(),output_review_import:output_review,
            changed_parts:plan.edits.len(),compiled_attribute_bytes:plan.bytes,output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),
            observed_protection_parts:plan.protection_parts,observed_protection_element_visits:plan.visits,whole_paragraph_scope_verified:true,
            all_original_scalars_controls_run_and_text_references_preserved:true,every_paragraph_reference_read_back:true,outside_selected_attribute_edits_exact:true,effective_style_native_or_service_authority:false};
        let mut count=Output {bytes:None,length:0,maximum:limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
        Ok(SourceParagraphStyleReplacementCandidate {artifact,receipt})
    }
}
struct AttributeEdit {start:usize,end:usize,bytes:Vec<u8>}
struct Plan {edits:BTreeMap<PackagePath,Vec<AttributeEdit>>,intents:Vec<PatchIntent>,paragraphs:BTreeMap<PackagePath,BTreeSet<usize>>,
    changes:Vec<SourceParagraphStyleChange>,matched_paragraphs:usize,bytes:usize,protection_parts:usize,visits:usize}
fn paragraph(node:&XmlElementToken)->bool {node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)&&node.name().local_name()=="p"}
struct Guard {prefix:Vec<usize>}
impl Guard {
    fn new(xml:&PreservingXmlDocument)->Result<Self,E> {
        let protected=crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?;
        let mut tracked=Vec::<bool>::new();let mut prefix=vec![0usize];
        for(i,node)in xml.elements().iter().enumerate() {
            let own=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
                &&(matches!(node.name().local_name(),"insertBegin"|"insertEnd"|"deleteBegin"|"deleteEnd")
                ||node.attributes().iter().any(|a|a.name().namespace().is_none()&&matches!(a.name().local_name(),"paraTcId"|"charTcId")));
            let inherited=match node.parent(){Some(p)if p<i=>tracked[p],Some(_)=>return Err(E::Source),None=>false};
            let flag=own||inherited;tracked.push(flag);prefix.push(prefix.last().copied().ok_or(E::Source)?.checked_add(usize::from(flag||protected[i])).ok_or(E::Limit)?);
        }Ok(Self {prefix})
    }
    fn blocked(&self,xml:&PreservingXmlDocument,index:usize)->Result<bool,E> {
        let end=xml.elements()[index].outer_span().ok_or(E::Selection)?.end();
        let stop=xml.elements().partition_point(|n|n.start_tag_span().start()<end);
        Ok(self.prefix.get(stop).ok_or(E::Selection)?!=self.prefix.get(index).ok_or(E::Selection)?)
    }
}
fn compile(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,found:&crate::document_import::search::SourceSearchResult,
    windows:&BTreeMap<usize,(usize,usize)>,target:SourceParagraphStyleTarget)->Result<Plan,R> {
    let source=index.original.source();let mut full:BTreeMap<&domain_ir::LogicalId,bool>=BTreeMap::new();
    for(i,b)in index.blocks.iter().enumerate(){*full.entry(&b.paragraph.opaque_handle).or_insert(true)&=windows.get(&i)==Some(&(0,b.units.len()));}
    let mut matched:BTreeMap<PackagePath,BTreeMap<usize,SourceAnchorHandle>>=BTreeMap::new();
    for m in found.matches() {
        let _=selected_origins(index,m)?;
        if full.get(&m.paragraph_anchor.opaque_handle)!=Some(&true){return Err(R::IncompleteParagraphScope);}
        let resolved=source.resolve_anchor(&m.paragraph_anchor).map_err(|_|E::Selection)?;let i=resolved.element_index().ok_or(E::Selection)?;
        if !paragraph(resolved.element().ok_or(E::Selection)?){return Err(E::Selection.into());}
        matched.entry(resolved.part().path().clone()).or_default().insert(i,m.paragraph_anchor.clone());
    }
    compile_matched(index,fields,context,matched,target)
}
fn compile_matched(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    matched:BTreeMap<PackagePath,BTreeMap<usize,SourceAnchorHandle>>,target:SourceParagraphStyleTarget)->Result<Plan,R>{
    let source=index.original.source();
    let intervals=context.field_intervals(source,fields)?;let mut plan=Plan {edits:BTreeMap::new(),intents:Vec::new(),paragraphs:BTreeMap::new(),
        changes:Vec::new(),matched_paragraphs:0,bytes:0,protection_parts:0,visits:0};
    for(path,paragraphs)in matched {
        let xml=source.parts().iter().find(|p|p.path()==&path).and_then(|p|p.xml()).ok_or(E::Source)?;let guard=Guard::new(xml)?;
        plan.protection_parts+=1;plan.visits=plan.visits.checked_add(xml.elements().len().checked_mul(3).ok_or(E::Limit)?).ok_or(E::Limit)?;
        for(i,anchor)in paragraphs {
            let node=&xml.elements()[i];let span=node.outer_span().ok_or(E::Selection)?;
            // Whole paragraph changes must consider unqueried cache/fields and descendants too.
            if guard.blocked(xml,i)?{return Err(E::Protection.into());}
            if let Some(ranges)=intervals.get(&path){let j=ranges.partition_point(|(_,b)|*b<=span.start());
                if ranges.get(j).is_some_and(|(a,_)|*a<span.end()){return Err(E::FieldContent.into());}}
            plan.matched_paragraphs+=1;plan.paragraphs.entry(path.clone()).or_default().insert(i);
            let old=super::render::reference(node,target.attribute())?;if old==Some(target.declaration_id()){continue;}
            if plan.intents.len()>=PatchLimits::default().config().max_intents{return Err(E::Limit.into());}
            let value=target.declaration_id().to_string();
            let edit=if let Some((a,attribute))=node.attributes().iter().enumerate().find(|(_,a)|a.name().namespace().is_none()&&a.name().local_name()==target.attribute()) {
                plan.intents.push(PatchIntent::ReplaceAttribute {target:XmlAttributeSelector::bind(&path,xml,i,a).map_err(|_|E::Selection)?,value:PatchAttributeValue::Text(PatchText::new(&value).map_err(|_|E::Value)?)});
                AttributeEdit {start:attribute.value_span().start(),end:attribute.value_span().end(),bytes:value.into_bytes()}
            }else {
                let mut attributes=BTreeMap::new();attributes.insert(target.attribute().to_owned(),target.declaration_id());
                plan.intents.push(PatchIntent::InsertUnsignedAttributes {target:XmlElementSelector::bind(&path,xml,i).map_err(|_|E::Selection)?,attributes});
                let at=node.start_tag_span().end().checked_sub(if node.is_empty(){2}else{1}).ok_or(E::Selection)?;
                AttributeEdit {start:at,end:at,bytes:format!(" {}=\"{}\"",target.attribute(),target.declaration_id()).into_bytes()}
            };
            plan.bytes=plan.bytes.checked_add(edit.bytes.len()).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
            plan.edits.entry(path.clone()).or_default().push(edit);
            plan.changes.push(SourceParagraphStyleChange {paragraph_anchor:anchor,previous_reference:old,target_reference:target.declaration_id()});
        }
    }
    if plan.edits.is_empty(){return Err(E::NoChange.into());}
    for edits in plan.edits.values_mut(){edits.sort_by_key(|e|e.start);if edits.windows(2).any(|w|w[0].end>w[1].start){return Err(E::Selection.into());}}
    Ok(plan)
}
