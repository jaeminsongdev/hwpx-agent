//! Exact declared style references only; no inherited/effective style inference.
use super::{ImportedDocumentStructure,caption_text::CaptionTextOutputError as E,
    caption_text_batch::{Edit,PartEdits,observed_protection}};
use crate::document_import::reference_targets::caption_frames::{ImportedCaptionFrames,
    CaptionStyleFamily as Family,CaptionStyleReference,CaptionStyleReferenceStatus as Status};
use crate::{PackagePath,PatchIntent,PatchAttributeValue,PatchText,PreservingXmlDocument,
    XmlElementSelector,XmlAttributeSelector};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits,SourceAnchorHandle};
use serde::Serialize;
use std::{collections::{BTreeMap,BTreeSet},fmt};
use super::caption_edit_map::OutputEditMap;

#[derive(Clone,Copy)]
pub struct CaptionStyleReplacement<'a> {
    pub caption_id:&'a LogicalId,pub source_node_id:&'a LogicalId,
    pub family:Family,pub declaration_id:u32,
}
impl fmt::Debug for CaptionStyleReplacement<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("CaptionStyleReplacement(<redacted>)")}
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionStyleBatchChange {
    pub source_caption_id:LogicalId,pub source_node_id:LogicalId,pub family:Family,
    pub source_reference:CaptionStyleReference,pub output_reference:CaptionStyleReference,
    pub inserted_attribute:bool,
}
struct Expected {path:PackagePath,caption_point:usize,node_point:usize,family:Family,reference:CaptionStyleReference}
pub(super) struct StylePlan {pub changes:Vec<CaptionStyleBatchChange>,expected:Vec<Expected>}
impl StylePlan {
    pub fn verify(&self,after:&ImportedCaptionFrames<'_>,maps:&OutputEditMap<'_>)->Result<(),E> {
        if self.expected.is_empty(){return Ok(());}
        let mut references=BTreeMap::new();
        for frame in after.frames(){
            for run in &frame.runs {references.insert((&frame.logical_caption_id,&run.logical_run_id,Family::Character),&run.character_style);}
            for paragraph in &frame.paragraphs {references.insert((&frame.logical_caption_id,&paragraph.logical_paragraph_id,Family::Paragraph),&paragraph.paragraph_style);references.insert((&frame.logical_caption_id,&paragraph.logical_paragraph_id,Family::Named),&paragraph.named_style);}
        }
        for expected in &self.expected {
            let (part,caption)=maps.original_element(&expected.path,expected.caption_point)?;
            let (_,node)=maps.original_element(&expected.path,expected.node_point)?;
            let caption_id=LogicalId::parse(format!("caption-{}",part.element_anchor(caption).ok_or(E::Readback)?.opaque_handle.as_str())).map_err(|_|E::Readback)?;
            let prefix=if expected.family==Family::Character{"caption-run-"}else{"caption-p-"};
            let node_id=LogicalId::parse(format!("{prefix}{}",part.element_anchor(node).ok_or(E::Readback)?.opaque_handle.as_str())).map_err(|_|E::Readback)?;
            if references.get(&(&caption_id,&node_id,expected.family)).copied()!=Some(&expected.reference){return Err(E::Readback);}
        }Ok(())
    }
}
pub(super) fn plan<'a>(source:&'a ImportedDocumentStructure,frames:&ImportedCaptionFrames<'_>,
    requests:&[CaptionStyleReplacement<'_>],limits:ReferenceAuxiliaryLimits,
    parts:&mut BTreeMap<&'a PackagePath,PartEdits<'a>>,guards:&mut BTreeMap<&'a PackagePath,Vec<bool>>,
    subtree:&mut BTreeMap<&'a PackagePath,Vec<bool>>,
    visits:&mut usize,escaped_bytes:&mut usize,intents:&mut Vec<PatchIntent>,
)->Result<StylePlan,E> {
    let mut plan=StylePlan {changes:Vec::new(),expected:Vec::new()};
    if requests.is_empty(){return Ok(plan);}
    let mut index=BTreeMap::new();
    for (f,frame) in frames.frames().iter().enumerate() {
        for (n,node) in frame.runs.iter().enumerate() {
            if index.insert((&node.logical_run_id,Family::Character),(f,n,&node.character_style,node.source_fingerprint_sha256)).is_some(){return Err(E::Selection);}
        }
        for (n,node) in frame.paragraphs.iter().enumerate() {
            for (family,reference) in [(Family::Paragraph,&node.paragraph_style),(Family::Named,&node.named_style)] {
                if index.insert((&node.logical_paragraph_id,family),(f,n,reference,node.source_fingerprint_sha256)).is_some(){return Err(E::Selection);}
            }
        }
    }
    // Canonical order binds receipts and grouped insertions independently of
    // request order. A duplicate is rejected even when both requests are no-ops.
    let mut ordered:Vec<_>=requests.iter().collect();ordered.sort_by_key(|r|(r.source_node_id,r.family));
    let mut seen=BTreeSet::new();
    let mut insertions=BTreeMap::<(&PackagePath,usize),(&PreservingXmlDocument,BTreeMap<String,u32>)>::new();
    for request in ordered {
        if !seen.insert((request.source_node_id,request.family)){return Err(E::Selection);}
        let &(f,_n,before,fingerprint)=index.get(&(request.source_node_id,request.family)).ok_or(E::Selection)?;
        if &frames.frames()[f].logical_caption_id!=request.caption_id{return Err(E::Selection);}
        let after=frames.style_declaration(request.family,request.declaration_id);
        if after.status!=Status::UniqueSourceDeclaration||after.declaration_sha256.is_none(){return Err(E::Selection);}
        let (prefix,tag,name)=match request.family {
            Family::Character=>("caption-run-","run","charPrIDRef"),
            Family::Paragraph=>("caption-p-","p","paraPrIDRef"),
            Family::Named=>("caption-p-","p","styleIDRef"),
        };
        let opaque=request.source_node_id.as_str().strip_prefix(prefix).ok_or(E::Selection)?;
        let anchor=SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:fingerprint};
        let resolved=source.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;
        let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let i=resolved.element_index().ok_or(E::Selection)?;
        let node=&xml.elements()[i];if !super::named(node,tag){return Err(E::Selection);}
        let caption=xml.elements().get(frames.frames()[f].source_position.xml_element_ordinal).ok_or(E::Selection)?;
        if !super::named(caption,"caption"){return Err(E::Selection);}
        plan.expected.push(Expected {path:part.path().clone(),caption_point:caption.start_tag_span().start(),node_point:node.start_tag_span().start(),family:request.family,reference:after.clone()});
        if before.reference_id==Some(request.declaration_id){continue;}
        if !guards.contains_key(part.path()) {
            *visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            guards.insert(part.path(),observed_protection(xml)?);
        }
        if !subtree.contains_key(part.path()) {
            *visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            subtree.insert(part.path(),subtree_protection(xml)?);
        }
        if guards.get(part.path()).and_then(|g|g.get(i)).copied().ok_or(E::Selection)?
            ||subtree.get(part.path()).and_then(|g|g.get(i)).copied().ok_or(E::Selection)? {return Err(E::Protection);}
        let attribute=node.attributes().iter().enumerate().find(|(_,a)|!a.is_namespace_declaration()
            &&a.name().namespace().is_none()&&a.name().local_name()==name);
        if let Some((ordinal,attribute))=attribute {
            if Some(attribute.semantic_value().parse::<u32>().map_err(|_|E::Source)?)!=before.reference_id{return Err(E::Source);}
            let value=request.declaration_id.to_string();
            *escaped_bytes=escaped_bytes.checked_add(value.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            let span=attribute.value_span();
            parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(Edit {start:span.start(),end:span.end(),bytes:value.as_bytes().to_vec()});
            intents.push(PatchIntent::ReplaceAttribute {target:XmlAttributeSelector::bind(part.path(),xml,i,ordinal).map_err(|_|E::Selection)?,
                value:PatchAttributeValue::Text(PatchText::new(&value).map_err(|_|E::Value)?)});
        }else{
            if before.reference_id.is_some(){return Err(E::Source);}
            let (_,attributes)=insertions.entry((part.path(),i)).or_insert_with(||(xml,BTreeMap::new()));
            if attributes.insert(name.to_owned(),request.declaration_id).is_some(){return Err(E::Selection);}
        }
        plan.changes.push(CaptionStyleBatchChange {source_caption_id:request.caption_id.clone(),source_node_id:request.source_node_id.clone(),
            family:request.family,source_reference:before.clone(),output_reference:after,inserted_attribute:attribute.is_none()});
    }
    for ((path,i),(xml,attributes)) in insertions {
        let node=&xml.elements()[i];let at=node.start_tag_span().end().checked_sub(if node.is_empty(){2}else{1}).ok_or(E::Selection)?;
        let bytes=attributes.iter().map(|(name,value)|format!(" {name}=\"{value}\"")).collect::<String>().into_bytes();
        *escaped_bytes=escaped_bytes.checked_add(bytes.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        parts.entry(path).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(Edit {start:at,end:at,bytes});
        intents.push(PatchIntent::InsertUnsignedAttributes {target:XmlElementSelector::bind(path,xml,i).map_err(|_|E::Selection)?,attributes});
    }
    Ok(plan)
}
pub(super) fn subtree_protection(xml:&PreservingXmlDocument)->Result<Vec<bool>,E> {
    let mut blocked=Vec::new();blocked.try_reserve_exact(xml.elements().len()).map_err(|_|E::Limit)?;
    for node in xml.elements() {
        blocked.push(node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
            &&node.attributes().iter().any(|a|a.name().namespace().is_none()
                &&(a.name().local_name()=="lock"||a.name().local_name()=="protect"
                    &&(super::named(node,"tc")||super::named(node,"sz")&&node.parent().is_some_and(|p|super::named(&xml.elements()[p],"tbl"))))
                &&!matches!(a.semantic_value(),"0"|"false")));
    }
    for i in (0..xml.elements().len()).rev() {
        if let Some(parent)=xml.elements()[i].parent(){if parent>=i{return Err(E::Source);}let child=blocked[i];blocked[parent]|=child;}
    }Ok(blocked)
}
