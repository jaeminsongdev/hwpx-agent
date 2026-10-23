//! Complete original number-control stream requests, not inferred native counters.
use super::{ImportedDocumentStructure,caption_text::CaptionTextOutputError as E,
    caption_text_batch::{PartEdits,Edit,observed_protection},caption_style_batch::subtree_protection};
use crate::{NumberFormat,PackagePath,XmlName,PatchIntent,PatchText,
    PatchAttributeValue,XmlAttributeSelector};
use crate::document_import::{ImportedSourcePart,reference_targets::{
    caption_source_state::ImportedCaptionSourceState,
    numbering::{ImportedCaptionNumbering,NativeNumberCategory as Category,NativeNumberControlKind as Kind,
        context::NumberingSourcePosition}}};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits,SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::BTreeMap,fmt};

#[derive(Clone,Copy)]
pub enum NativeNumberFormatReplacement<'a> {
    Preserve,
    Replace {format:NumberFormat,user_character:&'a str,prefix:&'a str,suffix:&'a str,superscript:bool},
}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub enum NativePageStartsOn {Both,Even,Odd}
impl NativePageStartsOn {pub(super) fn text(self)->&'static str {match self {Self::Both=>"BOTH",Self::Even=>"EVEN",Self::Odd=>"ODD"}}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub struct NativeDocumentStartValues {pub page:u32,pub footnote:u32,pub endnote:u32,pub picture:u32,pub table:u32,pub equation:u32}
#[derive(Clone,Copy)]
pub struct NativeDocumentStartReplacement<'a> {pub source_control_id:&'a LogicalId,pub source_fingerprint_sha256:[u8;32],pub values:NativeDocumentStartValues}
#[derive(Clone,Copy)]
pub enum NativeNumberEventValues<'a> {
    AutoNumber {category:Category,stored_number:i32,format:NativeNumberFormatReplacement<'a>},
    Restart {category:Category,stored_number:i32,format:NativeNumberFormatReplacement<'a>},
    SectionStart {page_starts_on:NativePageStartsOn,page:u32,picture:u32,table:u32,equation:u32},
}
#[derive(Clone,Copy)]
pub struct NativeNumberEventReplacement<'a> {pub source_control_id:&'a LogicalId,pub source_fingerprint_sha256:[u8;32],pub values:NativeNumberEventValues<'a>}
pub struct NativeNumberSequenceReplacement<'a> {
    pub expected_joined_state_sha256:[u8;32],
    /// Must match the original presence and identity; no fabricated default.
    pub document_start:Option<NativeDocumentStartReplacement<'a>>,
    /// Every original auto/restart/section-start control, in exact spine/XML order.
    /// No omission, duplicate, reordering, insertion or deletion is implied.
    pub events:&'a [NativeNumberEventReplacement<'a>],
}
impl NativeNumberSequenceReplacement<'_> {
    /// Bounded request identity only, not source/access/execution authorization.
    /// Every source ID/fingerprint, ordered value and Preserve/Replace choice is
    /// bound. Affix plaintext is hashed before serialization, never returned.
    /// # Errors
    /// Rejects invalid XML characters, request/value and serialized-byte limits.
    pub fn canonical_sha256(&self,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E> {
        preflight(self,limits)?;
        #[derive(Serialize)]
        enum FormatDigest {Preserve,Replace {format:&'static str,user:[u8;32],prefix:[u8;32],suffix:[u8;32],superscript:bool}}
        #[derive(Serialize)]
        enum EventDigest<'a> {
            Control(&'static str,&'a LogicalId,[u8;32],Category,i32,FormatDigest),
            SectionStart(&'a LogicalId,[u8;32],NativePageStartsOn,u32,u32,u32,u32),
        }
        let mut events=Vec::new();events.try_reserve_exact(self.events.len()).map_err(|_|E::Limit)?;
        for event in self.events {
            events.push(match event.values {
                NativeNumberEventValues::AutoNumber {category,stored_number,format}|NativeNumberEventValues::Restart {category,stored_number,format}=>{
                    let kind=if matches!(event.values,NativeNumberEventValues::AutoNumber {..}){"auto"}else{"restart"};
                    let format=match format {
                        NativeNumberFormatReplacement::Preserve=>FormatDigest::Preserve,
                        NativeNumberFormatReplacement::Replace {format,user_character,prefix,suffix,superscript}=>FormatDigest::Replace {
                            format:format.as_str(),user:Sha256::digest(user_character.as_bytes()).into(),prefix:Sha256::digest(prefix.as_bytes()).into(),suffix:Sha256::digest(suffix.as_bytes()).into(),superscript},
                    };
                    EventDigest::Control(kind,event.source_control_id,event.source_fingerprint_sha256,category,stored_number,format)
                },
                NativeNumberEventValues::SectionStart {page_starts_on,page,picture,table,equation}=>EventDigest::SectionStart(event.source_control_id,event.source_fingerprint_sha256,page_starts_on,page,picture,table,equation),
            });
        }
        let begin=self.document_start.map(|b|(b.source_control_id,b.source_fingerprint_sha256,b.values));
        hash(&(self.expected_joined_state_sha256,begin,events),limits)
    }
}
macro_rules! redacted {($($t:ty),+)=>{$(impl fmt::Debug for $t {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeNumberSequenceRequest(<redacted>; stored_values_not_resolved_counters)")}
})+}}
redacted!(NativeNumberFormatReplacement<'_>,NativeDocumentStartReplacement<'_>,NativeNumberEventValues<'_>,NativeNumberEventReplacement<'_>,NativeNumberSequenceReplacement<'_>);
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum NativeNumberNodeRole {DocumentStart,Control,SectionStart,Format}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NativeNumberNodeBinding {
    pub source_control_id:LogicalId,pub role:NativeNumberNodeRole,pub source_node_sha256:[u8;32],
    pub requested_values_sha256:[u8;32],pub changed_attributes:usize,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NativeNumberSequenceOutputReceipt {
    pub profile:&'static str,pub requested_events:usize,pub document_start_bound:bool,
    pub nodes:Vec<NativeNumberNodeBinding>,pub complete_request_sha256:[u8;32],
    pub caller_request_sha256:[u8;32],
    pub complete_original_control_order_checked:bool,pub all_requested_values_read_back:bool,
    pub native_counter_interpretation_and_recalculation_qualified:bool,pub execution_publication_authority:bool,
}
#[derive(Serialize)]
enum Value {Signed(i32),Unsigned(u32),Text(String),Boolean(bool)}
impl Value {
    fn matches(&self,text:&str)->bool {match self {Self::Signed(v)=>text.parse::<i32>()==Ok(*v),Self::Unsigned(v)=>text.parse::<u32>()==Ok(*v),Self::Text(v)=>text==v,
        Self::Boolean(v)=>match text {"0"|"false"=>!*v,"1"|"true"=>*v,_=>false}}}
    fn text(&self)->String {match self {Self::Signed(v)=>v.to_string(),Self::Unsigned(v)=>v.to_string(),Self::Text(v)=>v.clone(),Self::Boolean(v)=>if *v{"1"}else{"0"}.to_owned()}}
}
struct ExpectedNode {path:PackagePath,index:usize,name:XmlName,values:Vec<(&'static str,Value)>}
pub(super) struct NumberPlan {
    pub receipt:Option<NativeNumberSequenceOutputReceipt>,nodes:Vec<ExpectedNode>,order:Vec<NumberingSourcePosition>,
    controls:usize,starts:usize,beginning:bool,
}
impl NumberPlan {
    pub fn verify(&self,output:&ImportedDocumentStructure,numbers:&ImportedCaptionNumbering<'_>,limits:ReferenceAuxiliaryLimits)->Result<(),E> {
        if self.receipt.is_none(){return Ok(());}
        if numbers.controls().len()!=self.controls||numbers.section_starts().len()!=self.starts{return Err(E::Readback);}
        let context=numbers.import_context(limits).map_err(|_|E::Readback)?;
        if context.document_start().is_some()!=self.beginning||context.ordered_controls().iter().map(|c|c.source_position).collect::<Vec<_>>()!=self.order{return Err(E::Readback);}
        let parts:BTreeMap<_,_>=output.source().parts().iter().map(|p|(p.path(),p)).collect();
        for expected in &self.nodes {
            let xml=parts.get(&expected.path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let node=xml.elements().get(expected.index).ok_or(E::Readback)?;
            if node.name()!=&expected.name{return Err(E::Readback);}
            for (name,value) in &expected.values {
                let attribute=node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==*name).ok_or(E::Readback)?;
                if !value.matches(attribute.semantic_value()){return Err(E::Readback);}
            }
        }Ok(())
    }
}
pub(super) fn preflight(request:&NativeNumberSequenceReplacement<'_>,limits:ReferenceAuxiliaryLimits)->Result<usize,E> {
    let count=request.events.len().checked_add(usize::from(request.document_start.is_some())).ok_or(E::Limit)?;
    if count>limits.config().items_per_kind.min(crate::PatchLimits::default().config().max_intents){return Err(E::Limit);}
    let mut bytes=0usize;
    for event in request.events {
        let format=match event.values {NativeNumberEventValues::AutoNumber {format,..}|NativeNumberEventValues::Restart {format,..}=>format,_=>continue};
        if let NativeNumberFormatReplacement::Replace {user_character,prefix,suffix,..}=format {
            for text in [user_character,prefix,suffix] {
                if text.len()>limits.config().text_bytes{return Err(E::Limit);}
                bytes=bytes.checked_add(text.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
                PatchText::new(text).map_err(|_|E::Value)?;
            }
        }
    }
    Ok(count)
}
struct Builder<'a,'b> {
    source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits,
    parts:&'b mut BTreeMap<&'a PackagePath,PartEdits<'a>>,guards:&'b mut BTreeMap<&'a PackagePath,Vec<bool>>,
    subtree:&'b mut BTreeMap<&'a PackagePath,Vec<bool>>,visits:&'b mut usize,escaped:&'b mut usize,intents:&'b mut Vec<PatchIntent>,
    resolved:BTreeMap<LogicalId,(&'a ImportedSourcePart,usize)>,nodes:Vec<ExpectedNode>,bindings:Vec<NativeNumberNodeBinding>,
}
impl<'a> Builder<'a,'_> {
    fn node(&mut self,id:&LogicalId,fingerprint:[u8;32],role:NativeNumberNodeRole,format_fp:Option<[u8;32]>,values:Vec<(&'static str,Value)>)->Result<(),E> {
        if !self.resolved.contains_key(id) {
            let opaque=id.as_str().strip_prefix("native-number-").ok_or(E::Selection)?;
            let anchor=SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:fingerprint};
            let resolved=self.source.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;
            self.resolved.insert(id.clone(),(resolved.part(),resolved.element_index().ok_or(E::Selection)?));
        }
        let &(part,mut index)=self.resolved.get(id).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;
        if let Some(expected)=format_fp {
            let mut child=xml.elements()[index].first_child();let mut found=None;
            while let Some(i)=child {let node=&xml.elements()[i];child=node.next_sibling();if super::named(node,"autoNumFormat") {if found.replace(i).is_some(){return Err(E::Selection);}}}
            index=found.ok_or(E::Selection)?;
            if part.element_anchor(index).ok_or(E::Selection)?.fingerprint_sha256!=expected{return Err(E::Selection);}
        }
        let node=&xml.elements()[index];let source_node=part.element_anchor(index).ok_or(E::Selection)?.fingerprint_sha256;
        let mut selected=Vec::new();
        for (name,value) in &values {
            let (ordinal,attribute)=node.attributes().iter().enumerate().find(|(_,a)|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==*name).ok_or(E::Source)?;
            if !value.matches(attribute.semantic_value()){selected.push((ordinal,attribute,value));}
        }
        if !selected.is_empty() {
            if !self.guards.contains_key(part.path()) {
                *self.visits=self.visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                self.guards.insert(part.path(),observed_protection(xml)?);
            }
            if !self.subtree.contains_key(part.path()) {
                *self.visits=self.visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
                self.subtree.insert(part.path(),subtree_protection(xml)?);
            }
            if self.guards.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?
                ||self.subtree.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)? {return Err(E::Protection);}
            if role==NativeNumberNodeRole::DocumentStart {
                let mut ancestor=Some(index);
                while let Some(i)=ancestor {let e=&xml.elements()[i];ancestor=e.parent();
                    if e.attributes().iter().any(|a|a.name().namespace().is_none()&&matches!(a.name().local_name(),"lock"|"protect")&&!matches!(a.semantic_value(),"0"|"false")){return Err(E::Protection);}}
            }
            for (ordinal,attribute,value) in &selected {
                let text=value.text();let escaped=crate::patch::escape_attribute(&text,attribute.quote_style()).map_err(|_|E::Value)?;
                *self.escaped=self.escaped.checked_add(escaped.len()).filter(|n|*n<=self.limits.config().output_bytes).ok_or(E::Limit)?;
                let span=attribute.value_span();
                self.parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(Edit {start:span.start(),end:span.end(),bytes:escaped.into_bytes()});
                self.intents.push(PatchIntent::ReplaceAttribute {target:XmlAttributeSelector::bind(part.path(),xml,index,*ordinal).map_err(|_|E::Selection)?,value:PatchAttributeValue::Text(PatchText::new(&text).map_err(|_|E::Value)?)});
            }
        }
        self.bindings.push(NativeNumberNodeBinding {source_control_id:id.clone(),role,source_node_sha256:source_node,requested_values_sha256:hash(&values,self.limits)?,changed_attributes:selected.len()});
        self.nodes.push(ExpectedNode {path:part.path().clone(),index,name:node.name().clone(),values});Ok(())
    }
}
pub(super) fn plan<'a>(source:&'a ImportedDocumentStructure,state:Option<&ImportedCaptionSourceState<'_>>,request:Option<&NativeNumberSequenceReplacement<'_>>,
    limits:ReferenceAuxiliaryLimits,parts:&mut BTreeMap<&'a PackagePath,PartEdits<'a>>,guards:&mut BTreeMap<&'a PackagePath,Vec<bool>>,
    subtree:&mut BTreeMap<&'a PackagePath,Vec<bool>>,visits:&mut usize,escaped:&mut usize,intents:&mut Vec<PatchIntent>,
)->Result<NumberPlan,E> {
    let Some(request)=request else{return Ok(NumberPlan {receipt:None,nodes:Vec::new(),order:Vec::new(),controls:0,starts:0,beginning:false});};
    let state=state.ok_or(E::Source)?;
    if request.expected_joined_state_sha256!=state.receipt().joined_state_sha256{return Err(E::Source);}
    if request.events.len()!=state.context().ordered_controls().len(){return Err(E::Selection);}
    let mut builder=Builder {source,limits,parts,guards,subtree,visits,escaped,intents,resolved:BTreeMap::new(),nodes:Vec::new(),bindings:Vec::new()};
    match (state.context().document_start(),request.document_start) {
        (None,None)=>{},(Some(before),Some(after))=>{
            if after.source_control_id!=&before.logical_control_id||after.source_fingerprint_sha256!=before.source_fingerprint_sha256{return Err(E::Selection);}
            let v=after.values;
            builder.node(after.source_control_id,after.source_fingerprint_sha256,NativeNumberNodeRole::DocumentStart,None,
                unsigned(&[("page",v.page),("footnote",v.footnote),("endnote",v.endnote),("pic",v.picture),("tbl",v.table),("equation",v.equation)]))?;
        },_=>return Err(E::Selection),
    }
    let controls:BTreeMap<_,_>=state.numbering().controls().iter().map(|c|(&c.logical_control_id,c)).collect();
    let starts:BTreeMap<_,_>=state.numbering().section_starts().iter().map(|c|(&c.logical_control_id,c)).collect();
    for (expected,event) in state.context().ordered_controls().iter().zip(request.events) {
        if event.source_control_id!=&expected.logical_control_id{return Err(E::Selection);}
        match event.values {
            NativeNumberEventValues::SectionStart {page_starts_on,page,picture,table,equation}=>{
                let before=*starts.get(event.source_control_id).ok_or(E::Selection)?;
                if event.source_fingerprint_sha256!=before.source_fingerprint_sha256{return Err(E::Selection);}
                let mut values=unsigned(&[("page",page),("pic",picture),("tbl",table),("equation",equation)]);
                values.push(("pageStartsOn",Value::Text(page_starts_on.text().to_owned())));
                builder.node(event.source_control_id,event.source_fingerprint_sha256,NativeNumberNodeRole::SectionStart,None,values)?;
            },
            NativeNumberEventValues::AutoNumber {category,stored_number,format}|NativeNumberEventValues::Restart {category,stored_number,format}=>{
                let before=*controls.get(event.source_control_id).ok_or(E::Selection)?;
                let kind=if matches!(event.values,NativeNumberEventValues::AutoNumber {..}){Kind::AutoNumber}else{Kind::Restart};
                if kind!=before.kind||event.source_fingerprint_sha256!=before.source_fingerprint_sha256{return Err(E::Selection);}
                builder.node(event.source_control_id,event.source_fingerprint_sha256,NativeNumberNodeRole::Control,None,
                    vec![("num",Value::Signed(stored_number)),("numType",Value::Text(category_text(category).to_owned()))])?;
                if let NativeNumberFormatReplacement::Replace {format,user_character,prefix,suffix,superscript}=format {
                    let before=before.format.as_ref().ok_or(E::Selection)?;
                    builder.node(event.source_control_id,event.source_fingerprint_sha256,NativeNumberNodeRole::Format,Some(before.source_fingerprint_sha256),
                        vec![("type",Value::Text(format.as_str().to_owned())),("userChar",Value::Text(user_character.to_owned())),("prefixChar",Value::Text(prefix.to_owned())),
                            ("suffixChar",Value::Text(suffix.to_owned())),("supscript",Value::Boolean(superscript))])?;
                }
            },
        }
    }
    let digest=hash(&(request.expected_joined_state_sha256,&builder.bindings),limits)?;
    let receipt=NativeNumberSequenceOutputReceipt {profile:"hwpx-agent.caption-native-number-stream/output-v2",requested_events:request.events.len(),document_start_bound:request.document_start.is_some(),
        nodes:builder.bindings,complete_request_sha256:digest,caller_request_sha256:request.canonical_sha256(limits)?,complete_original_control_order_checked:true,all_requested_values_read_back:true,native_counter_interpretation_and_recalculation_qualified:false,execution_publication_authority:false};
    Ok(NumberPlan {receipt:Some(receipt),nodes:builder.nodes,order:state.context().ordered_controls().iter().map(|c|c.source_position).collect(),controls:controls.len(),starts:starts.len(),beginning:request.document_start.is_some()})
}
fn unsigned(values:&[(&'static str,u32)])->Vec<(&'static str,Value)> {values.iter().map(|(name,value)|(*name,Value::Unsigned(*value))).collect()}
fn hash(value:&impl Serialize,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E> {
    let bytes=serde_json::to_vec(value).map_err(|_|E::Limit)?;if bytes.len()>limits.config().output_bytes{return Err(E::Limit);}Ok(Sha256::digest(bytes).into())
}
pub(super) fn category_text(category:Category)->&'static str {match category {Category::Page=>"PAGE",Category::Footnote=>"FOOTNOTE",Category::Endnote=>"ENDNOTE",Category::Picture=>"PICTURE",Category::Table=>"TABLE",Category::Equation=>"EQUATION",Category::TotalPage=>"TOTAL_PAGE"}}
