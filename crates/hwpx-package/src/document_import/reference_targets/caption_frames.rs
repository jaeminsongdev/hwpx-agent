//! Source text/style/control frames, not inferred labels or counter semantics.
use super::{hash_json, ImportedDocumentStructure};
use super::captions::ImportedReferenceCaptions;
use super::numbering::{CaptionNumberingImportError as Error, CaptionNumberingImportReceipt,
    NativeNumberControlKind, NativeNumberControlObservation, context::NumberingSourcePosition};
use crate::{PreservingXmlDocument, XmlElementToken, XmlTokenKind};
use domain_ir::{LogicalId, ReferenceAuxiliaryLimits};
use quick_xml::escape::unescape;
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{borrow::Cow, collections::{BTreeMap, BTreeSet}, fmt};

const HP: &str = crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
const HH: &str = "http://www.hancom.co.kr/hwpml/2011/head";

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionStyleFamily { Character, Paragraph, Named }
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionStyleReferenceStatus {
    MissingReference, MissingDeclaration, UniqueSourceDeclaration,
    AmbiguousDeclarations, UnverifiedDeclarationLocation,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CaptionStyleReference {
    pub reference_id: Option<u32>,
    pub status: CaptionStyleReferenceStatus,
    /// Exact declared subtree only, not effective/inherited formatting.
    pub declaration_sha256: Option<[u8; 32]>,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CaptionParagraphFrame {
    pub logical_paragraph_id: LogicalId,
    pub paragraph_style: CaptionStyleReference,
    pub named_style: CaptionStyleReference,
    pub source_fingerprint_sha256: [u8; 32],
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CaptionRunFrame {
    pub logical_run_id: LogicalId,
    pub logical_paragraph_id: LogicalId,
    pub character_style: CaptionStyleReference,
    pub source_fingerprint_sha256: [u8; 32],
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CaptionFrameSegmentKind { PlainText, AutoNumber, Restart, Opaque }
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CaptionFrameSegment {
    pub logical_source_id: LogicalId,
    pub kind: CaptionFrameSegmentKind,
    pub logical_paragraph_id: Option<LogicalId>,
    pub logical_run_id: Option<LogicalId>,
    pub number_control_id: Option<LogicalId>,
    pub source_fingerprint_sha256: [u8; 32],
    pub decoded_text_sha256: Option<[u8; 32]>,
    pub decoded_text_bytes: usize,
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct CaptionSourceFrame {
    pub logical_caption_id: LogicalId,
    pub logical_object_id: LogicalId,
    pub source_position: NumberingSourcePosition,
    pub paragraphs: Vec<CaptionParagraphFrame>,
    pub runs: Vec<CaptionRunFrame>,
    pub segments: Vec<CaptionFrameSegment>,
    pub mixed_structural_containers: usize,
    /// Structural observation only. A label, separator, counter sequence,
    /// rendered cache and effective font/style have not been inferred.
    pub single_auto_number_linear_layout_observed: bool,
    pub source_fingerprint_sha256: [u8; 32],
}
macro_rules! redacted_debug {
    ($($name:ty),+ $(,)?) => {$(impl fmt::Debug for $name {
        fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result { f.write_str(concat!(stringify!($name),"(<redacted>; source_frame_only)")) }
    })+};
}
redacted_debug!(CaptionParagraphFrame, CaptionRunFrame, CaptionFrameSegment, CaptionSourceFrame);

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CaptionFrameImportReceipt {
    pub profile: &'static str,
    pub numbering: CaptionNumberingImportReceipt,
    pub frames_sha256: [u8; 32],
    pub captions: usize,
    pub paragraphs: usize,
    pub runs: usize,
    pub segments: usize,
    pub plain_text_segments: usize,
    pub decoded_text_bytes: usize,
    pub number_segments: usize,
    pub opaque_segments: usize,
    pub mixed_structural_containers: usize,
    pub unresolved_style_references: usize,
    pub effective_style_and_sequence_semantics_qualified: bool,
    pub complete_auxiliary_state_and_protection_qualified: bool,
    pub execution_publication_authority: bool,
}
pub struct ImportedCaptionFrames<'a> {
    source: &'a ImportedDocumentStructure,
    frames: Vec<CaptionSourceFrame>,
    plain_text: BTreeMap<LogicalId, String>,
    styles: Styles,
    receipt: CaptionFrameImportReceipt,
}
impl fmt::Debug for ImportedCaptionFrames<'_> {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result { f.write_str("ImportedCaptionFrames(<redacted>; not_native_or_service_authority)") }
}
type Styles = BTreeMap<(CaptionStyleFamily,u32), (CaptionStyleReferenceStatus,Option<[u8;32]>)>;

impl<'a> ImportedCaptionFrames<'a> {
    pub(super) fn import(source:&'a ImportedDocumentStructure,captions:&ImportedReferenceCaptions<'_>,
        controls:&[NativeNumberControlObservation],numbering:&CaptionNumberingImportReceipt,
        limits:ReferenceAuxiliaryLimits,
    )->Result<Self,Error> {
        if captions.envelopes().len()>limits.config().items_per_kind
            || source.graph().sections().len()>limits.config().sections {return Err(Error::Limit);}
        let styles=styles(source,limits)?;
        let expected:BTreeMap<_,_>=captions.envelopes().iter().map(|c|(c.logical_caption_id().as_str(),c)).collect();
        let numbered:BTreeMap<_,_>=controls.iter().filter(|c|c.logical_caption_id.is_some()).map(|c|(&c.logical_control_id,c)).collect();
        let spine:BTreeMap<_,_>=source.source().spine().iter().enumerate().map(|(i,path)|(path,i)).collect();
        let mut result=Self {source,frames:Vec::new(),plain_text:BTreeMap::new(),styles:Styles::new(),receipt:CaptionFrameImportReceipt {
            profile:"hwpx-agent.caption-source-frames/text-style-control-v1",numbering:numbering.clone(),frames_sha256:[0;32],
            captions:0,paragraphs:0,runs:0,segments:0,plain_text_segments:0,decoded_text_bytes:0,number_segments:0,opaque_segments:0,
            mixed_structural_containers:0,unresolved_style_references:0,effective_style_and_sequence_semantics_qualified:false,
            complete_auxiliary_state_and_protection_qualified:false,execution_publication_authority:false}};
        let mut seen=BTreeSet::new();let mut seen_numbers=BTreeSet::new();
        for part in source.source().parts() {
            let Some(xml)=part.xml() else {continue};
            // One token pass per original part, not a repeated descendant token
            // scan for every paragraph/run/caption. No XML reparsing.
            let mixed:BTreeSet<_>=xml.tokens().iter().filter(|t|matches!(t.kind(),XmlTokenKind::Text|XmlTokenKind::Reference)).filter_map(crate::XmlToken::element_index).collect();
            for (index,node) in xml.elements().iter().enumerate() {
                if !named(node,"caption"){continue;}
                let anchor=part.element_anchor(index).ok_or(Error::Binding)?;
                let caption_id=id("caption",anchor)?;
                let envelope=*expected.get(caption_id.as_str()).ok_or(Error::Coverage)?;
                if !seen.insert(caption_id.clone()){return Err(Error::Binding);}
                let mut frame=CaptionSourceFrame {logical_caption_id:caption_id,logical_object_id:envelope.logical_object_id().clone(),
                    source_position:NumberingSourcePosition {spine_ordinal:*spine.get(part.path()).ok_or(Error::Coverage)?,xml_element_ordinal:index},
                    paragraphs:Vec::new(),runs:Vec::new(),segments:Vec::new(),mixed_structural_containers:0,
                    single_auto_number_linear_layout_observed:false,source_fingerprint_sha256:anchor.fingerprint_sha256};
                let mut walk=Walk {part,xml,mixed:&mixed,styles:&styles,numbered:&numbered,seen_numbers:&mut seen_numbers,result:&mut result,limits};
                walk.check_mixed(index,&mut frame)?;
                let mut child=node.first_child();
                while let Some(i)=child {let element=&xml.elements()[i];child=element.next_sibling();
                    if named(element,"subList") {walk.sublist(i,&mut frame)?;} else {walk.segment(i,None,None,&mut frame)?;}}
                frame.single_auto_number_linear_layout_observed=frame.paragraphs.len()==1&&frame.mixed_structural_containers==0
                    &&frame.segments.iter().filter(|s|s.kind==CaptionFrameSegmentKind::AutoNumber).count()==1
                    &&frame.segments.iter().all(|s|matches!(s.kind,CaptionFrameSegmentKind::PlainText|CaptionFrameSegmentKind::AutoNumber));
                result.frames.try_reserve(1).map_err(|_|Error::Limit)?;result.frames.push(frame);
            }
        }
        if seen.len()!=expected.len()||seen_numbers.len()!=numbered.len(){return Err(Error::Coverage);}
        result.frames.sort_by_key(|f|f.source_position);
        result.receipt.captions=result.frames.len();
        result.receipt.frames_sha256=hash_json(&result.frames,limits.config().output_bytes).map_err(|_|Error::Limit)?;
        result.styles=styles;
        Ok(result)
    }
    #[must_use] pub fn frames(&self)->&[CaptionSourceFrame] {&self.frames}
    #[must_use] pub const fn receipt(&self)->&CaptionFrameImportReceipt {&self.receipt}
    /// Explicit original-snapshot text access for the typed compiler. Neither
    /// this getter nor a retained frame is a fresh service/ACL/head authorization.
    /// Text is never included in Debug or serialized observations/receipts.
    #[must_use] pub fn plain_text(&self,source_id:&LogicalId)->Option<&str> {self.plain_text.get(source_id).map(String::as_str)}
    /// Exact original declaration lookup, including declarations not yet used by
    /// a caption. This does not resolve inheritance or qualify effective styling.
    #[must_use] pub fn style_declaration(&self,family:CaptionStyleFamily,id:u32)->CaptionStyleReference {
        let (status,declaration_sha256)=self.styles.get(&(family,id)).copied()
            .unwrap_or((CaptionStyleReferenceStatus::MissingDeclaration,None));
        CaptionStyleReference {reference_id:Some(id),status,declaration_sha256}
    }
    /// # Errors
    /// Whole original source/graph reconstruction, including masked/opaque text.
    pub fn verify_source(&self,fresh:&[u8])->Result<CaptionFrameImportReceipt,Error> {
        if self.source.verify_source(fresh).map_err(|_|Error::Binding)?!=*self.source.receipt(){return Err(Error::Binding);}
        Ok(self.receipt.clone())
    }
}

struct Walk<'a,'s> {
    part:&'a crate::document_import::ImportedSourcePart,
    xml:&'a PreservingXmlDocument,
    mixed:&'a BTreeSet<usize>,
    styles:&'a Styles,
    numbered:&'a BTreeMap<&'a LogicalId,&'a NativeNumberControlObservation>,
    seen_numbers:&'a mut BTreeSet<LogicalId>,
    result:&'a mut ImportedCaptionFrames<'s>,
    limits:ReferenceAuxiliaryLimits,
}
impl Walk<'_,'_> {
    fn check_mixed(&mut self,index:usize,frame:&mut CaptionSourceFrame)->Result<(),Error> {
        if self.mixed.contains(&index){increment(&mut frame.mixed_structural_containers,usize::MAX)?;increment(&mut self.result.receipt.mixed_structural_containers,usize::MAX)?;}Ok(())
    }
    fn sublist(&mut self,index:usize,frame:&mut CaptionSourceFrame)->Result<(),Error> {
        self.check_mixed(index,frame)?;let mut child=self.xml.elements()[index].first_child();
        while let Some(i)=child {let node=&self.xml.elements()[i];child=node.next_sibling();
            if !named(node,"p"){self.segment(i,None,None,frame)?;continue;}
            self.check_mixed(i,frame)?;increment(&mut self.result.receipt.paragraphs,self.limits.config().items_per_kind)?;
            let anchor=self.part.element_anchor(i).ok_or(Error::Binding)?;let paragraph=id("caption-p",anchor)?;
            let paragraph_style=reference(node,"paraPrIDRef",CaptionStyleFamily::Paragraph,self.styles)?;
            let named_style=reference(node,"styleIDRef",CaptionStyleFamily::Named,self.styles)?;
            self.unresolved(&paragraph_style)?;self.unresolved(&named_style)?;
            frame.paragraphs.try_reserve(1).map_err(|_|Error::Limit)?;
            frame.paragraphs.push(CaptionParagraphFrame {logical_paragraph_id:paragraph.clone(),paragraph_style,named_style,source_fingerprint_sha256:anchor.fingerprint_sha256});
            let mut run=node.first_child();while let Some(r)=run {let node=&self.xml.elements()[r];run=node.next_sibling();
                if !named(node,"run"){self.segment(r,Some(&paragraph),None,frame)?;continue;}
                self.check_mixed(r,frame)?;increment(&mut self.result.receipt.runs,self.limits.config().items_per_kind)?;
                let anchor=self.part.element_anchor(r).ok_or(Error::Binding)?;let run_id=id("caption-run",anchor)?;
                let character_style=reference(node,"charPrIDRef",CaptionStyleFamily::Character,self.styles)?;self.unresolved(&character_style)?;
                frame.runs.try_reserve(1).map_err(|_|Error::Limit)?;
                frame.runs.push(CaptionRunFrame {logical_run_id:run_id.clone(),logical_paragraph_id:paragraph.clone(),character_style,source_fingerprint_sha256:anchor.fingerprint_sha256});
                let mut child=node.first_child();while let Some(c)=child {let node=&self.xml.elements()[c];child=node.next_sibling();
                    if named(node,"ctrl") {
                        self.check_mixed(c,frame)?;
                        let mut control=node.first_child();let mut any=false;
                        while let Some(n)=control {control=self.xml.elements()[n].next_sibling();any=true;self.segment(n,Some(&paragraph),Some(&run_id),frame)?;}
                        if !any {self.segment(c,Some(&paragraph),Some(&run_id),frame)?;}
                    } else {self.segment(c,Some(&paragraph),Some(&run_id),frame)?;}
                }
            }
        }Ok(())
    }
    fn unresolved(&mut self,style:&CaptionStyleReference)->Result<(),Error> {
        if style.status!=CaptionStyleReferenceStatus::UniqueSourceDeclaration {increment(&mut self.result.receipt.unresolved_style_references,usize::MAX)?;}Ok(())
    }
    fn segment(&mut self,index:usize,paragraph:Option<&LogicalId>,run:Option<&LogicalId>,frame:&mut CaptionSourceFrame)->Result<(),Error> {
        increment(&mut self.result.receipt.segments,self.limits.config().items_per_kind)?;
        let node=&self.xml.elements()[index];let anchor=self.part.element_anchor(index).ok_or(Error::Binding)?;
        let source_id=id("caption-segment",anchor)?;
        let mut segment=CaptionFrameSegment {logical_source_id:source_id.clone(),kind:CaptionFrameSegmentKind::Opaque,
            logical_paragraph_id:paragraph.cloned(),logical_run_id:run.cloned(),number_control_id:None,
            source_fingerprint_sha256:anchor.fingerprint_sha256,decoded_text_sha256:None,decoded_text_bytes:0};
        if named(node,"t")&&run.is_some()&&node.first_child().is_none()
            &&node.parent().is_some_and(|p|named(&self.xml.elements()[p],"run")) {
            let lexical=self.xml.source_text(node.content_span().ok_or(Error::Binding)?).map_err(|_|Error::Binding)?;
            // Comments and any structured content stay opaque. No concatenation
            // into a purported label; CDATA/DTD/PI remain rejected upstream.
            if !lexical.contains('<') {
                if lexical.len()>self.limits.config().text_bytes {return Err(Error::Limit);}
                let normalized=normalize_line_ends(lexical)?;
                let text=unescape(&normalized).map_err(|_|Error::Value)?;
                if text.len()>self.limits.config().text_bytes {return Err(Error::Limit);}
                let total=self.result.receipt.decoded_text_bytes.checked_add(text.len()).filter(|n|*n<=self.limits.config().output_bytes).ok_or(Error::Limit)?;
                segment.kind=CaptionFrameSegmentKind::PlainText;segment.decoded_text_bytes=text.len();segment.decoded_text_sha256=Some(Sha256::digest(text.as_bytes()).into());
                let mut owned=String::new();owned.try_reserve_exact(text.len()).map_err(|_|Error::Limit)?;owned.push_str(&text);
                if self.result.plain_text.insert(source_id,owned).is_some(){return Err(Error::Binding);}
                self.result.receipt.decoded_text_bytes=total;increment(&mut self.result.receipt.plain_text_segments,self.limits.config().items_per_kind)?;
            }
        } else if named(node,"autoNum")||named(node,"newNum") {
            let control=id("native-number",anchor)?;
            let observed=*self.numbered.get(&control).ok_or(Error::Coverage)?;
            if observed.logical_caption_id.as_ref()!=Some(&frame.logical_caption_id)||!self.seen_numbers.insert(control.clone()){return Err(Error::Binding);}
            segment.kind=match observed.kind {NativeNumberControlKind::AutoNumber=>CaptionFrameSegmentKind::AutoNumber,NativeNumberControlKind::Restart=>CaptionFrameSegmentKind::Restart};
            segment.number_control_id=Some(control);increment(&mut self.result.receipt.number_segments,self.limits.config().items_per_kind)?;
        }
        if segment.kind==CaptionFrameSegmentKind::Opaque {increment(&mut self.result.receipt.opaque_segments,self.limits.config().items_per_kind)?;}
        frame.segments.try_reserve(1).map_err(|_|Error::Limit)?;frame.segments.push(segment);Ok(())
    }
}
fn named(node:&XmlElementToken,name:&str)->bool {node.name().namespace()==Some(HP)&&node.name().local_name()==name}
fn normalize_line_ends(text:&str)->Result<Cow<'_,str>,Error> {
    if !text.contains('\r'){return Ok(Cow::Borrowed(text));}
    let mut output=String::new();output.try_reserve_exact(text.len()).map_err(|_|Error::Limit)?;
    let mut chars=text.chars().peekable();
    while let Some(ch)=chars.next() {
        if ch=='\r' {if chars.peek()==Some(&'\n'){chars.next();}output.push('\n');} else {output.push(ch);}
    }
    // Normalize the lexical entity before expanding references: &#13; remains CR.
    Ok(Cow::Owned(output))
}
fn attr<'a>(node:&'a XmlElementToken,name:&str)->Option<&'a str> {
    node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name).map(crate::XmlAttributeToken::semantic_value)
}
fn id(prefix:&str,anchor:&domain_ir::SourceAnchorHandle)->Result<LogicalId,Error> {LogicalId::parse(format!("{prefix}-{}",anchor.opaque_handle.as_str())).map_err(|_|Error::Binding)}
fn increment(value:&mut usize,maximum:usize)->Result<(),Error> {*value=value.checked_add(1).filter(|n|*n<=maximum).ok_or(Error::Limit)?;Ok(())}
fn reference(node:&XmlElementToken,name:&str,family:CaptionStyleFamily,styles:&Styles)->Result<CaptionStyleReference,Error> {
    let Some(raw)=attr(node,name) else {return Ok(CaptionStyleReference {reference_id:None,status:CaptionStyleReferenceStatus::MissingReference,declaration_sha256:None});};
    let id=raw.parse::<u32>().map_err(|_|Error::Value)?;
    let (status,declaration_sha256)=styles.get(&(family,id)).copied().unwrap_or((CaptionStyleReferenceStatus::MissingDeclaration,None));
    Ok(CaptionStyleReference {reference_id:Some(id),status,declaration_sha256})
}
fn styles(source:&ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Styles,Error> {
    use CaptionStyleFamily::{Character,Paragraph,Named};
    let mut result=Styles::new();let mut count=0;
    for part in source.source().parts() {let Some(xml)=part.xml() else {continue};
        for (i,node) in xml.elements().iter().enumerate() {
            if node.name().namespace()!=Some(HH){continue;}
            let (family,parent)=match node.name().local_name() {"charPr"=>(Character,"charProperties"),"paraPr"=>(Paragraph,"paraProperties"),"style"=>(Named,"styles"),_=>continue};
            increment(&mut count,limits.config().items_per_kind)?;
            let key=attr(node,"id").ok_or(Error::Value)?.parse::<u32>().map_err(|_|Error::Value)?;
            let mut ancestor=node.parent();let mut proper=part.path().as_str()=="Contents/header.xml";
            for name in [parent,"refList","head"] {
                let current=ancestor.and_then(|index|xml.elements().get(index));
                proper&=current.is_some_and(|n|n.name().namespace()==Some(HH)&&n.name().local_name()==name);
                ancestor=current.and_then(XmlElementToken::parent);
            }
            proper&=ancestor.is_none();
            let value=if proper {(CaptionStyleReferenceStatus::UniqueSourceDeclaration,Some(part.element_anchor(i).ok_or(Error::Binding)?.fingerprint_sha256))}
                else {(CaptionStyleReferenceStatus::UnverifiedDeclarationLocation,None)};
            result.entry((family,key)).and_modify(|entry|*entry=(CaptionStyleReferenceStatus::AmbiguousDeclarations,None)).or_insert(value);
        }
    }Ok(result)
}
