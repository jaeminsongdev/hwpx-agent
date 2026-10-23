//! Typed insertion/deletion of native number controls. No caller XML, inferred
//! counter values, persisted permission or Native execution qualification.
use super::{ImportedDocumentStructure,caption_text::CaptionTextOutputError as E,
    caption_text_batch::{PartEdits,Edit,observed_protection},caption_style_batch::subtree_protection,
    caption_edit_map::OutputEditMap,caption_numbering_sequence::{NativeDocumentStartValues,NativePageStartsOn,category_text}};
use crate::{NumberFormat,ElementSplicePosition as Position,PackagePath,PatchIntent,PatchText,PatchLimits,
    ValidatedXmlFragment,XmlElementSelector,XmlQuoteStyle};
use crate::document_import::{ImportedSourcePart,reference_targets::{caption_source_state::ImportedCaptionSourceState,
    numbering::{ImportedCaptionNumbering,context::ImportedNumberingContext,NativeNumberCategory as Category,NativeNumberControlKind as Kind,NativeNumberFormatObservation}}};
use domain_ir::{LogicalId,ReferenceAuxiliaryLimits,SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt};
const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
const HH:&str="http://www.hancom.co.kr/hwpml/2011/head";
#[derive(Clone,Copy)]
pub struct NativeInsertedNumberFormat<'a> {pub format:NumberFormat,pub user_character:&'a str,pub prefix:&'a str,pub suffix:&'a str,pub superscript:bool}
#[derive(Clone,Copy)]
pub enum NativeInsertedNumberControl<'a> {
    AutoNumber {category:Category,stored_number:i32,format:NativeInsertedNumberFormat<'a>},
    Restart {category:Category,stored_number:i32,format:Option<NativeInsertedNumberFormat<'a>>},
    SectionStart {page_starts_on:NativePageStartsOn,page:u32,picture:u32,table:u32,equation:u32},
    DocumentStart(NativeDocumentStartValues),
}
#[derive(Clone,Copy)]
pub struct NativeNumberDeletion<'a> {pub source_control_id:&'a LogicalId,pub source_fingerprint_sha256:[u8;32],pub remove_owned_empty_wrapper:bool}
pub struct NativeNumberInsertion<'a> {pub local_id:&'a LogicalId,pub target:&'a SourceAnchorHandle,pub position:Position,pub controls:&'a[NativeInsertedNumberControl<'a>]}
pub struct NativeNumberTopologyRequest<'a> {
    pub expected_joined_state_sha256:[u8;32],pub deletions:&'a[NativeNumberDeletion<'a>],pub insertions:&'a[NativeNumberInsertion<'a>],
}
macro_rules! redact {($($t:ty),+)=>{$(impl fmt::Debug for $t {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("NativeNumberTopologyRequest(<redacted>; not_counter_or_service_authority)")}})+}}
redact!(NativeInsertedNumberFormat<'_>,NativeInsertedNumberControl<'_>,NativeNumberDeletion<'_>,NativeNumberInsertion<'_>,NativeNumberTopologyRequest<'_>);
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NativeNumberDeletionBinding {pub source_control_id:LogicalId,pub source_sha256:[u8;32],pub owned_empty_wrapper_removed:bool}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NativeNumberInsertionBinding {pub request_ordinal:usize,pub item_ordinal:usize,pub local_id_sha256:[u8;32],pub output_control_id:LogicalId,pub requested_state_sha256:[u8;32]}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct NativeNumberTopologyOutputReceipt {
    pub profile:&'static str,pub source_joined_state_sha256:[u8;32],pub caller_request_sha256:[u8;32],
    pub deleted:Vec<NativeNumberDeletionBinding>,pub inserted:Vec<NativeNumberInsertionBinding>,
    pub original_controls:usize,pub retained_controls:usize,pub output_controls:usize,
    pub complete_original_and_inserted_inventory_read_back:bool,pub native_counter_recalculation_qualified:bool,pub execution_publication_authority:bool,
}
#[derive(Clone,Eq,PartialEq,Serialize)]
struct FormatState {kind:&'static str,user:[u8;32],prefix:[u8;32],suffix:[u8;32],superscript:bool,empty:bool}
impl FormatState {
    fn observed(v:&NativeNumberFormatObservation)->Self {Self {kind:v.native_type,user:v.user_character_sha256,prefix:v.prefix_sha256,suffix:v.suffix_sha256,superscript:v.superscript,empty:v.affixes_and_user_character_empty}}
    fn requested(v:NativeInsertedNumberFormat<'_>)->Self {Self {kind:v.format.as_str(),user:Sha256::digest(v.user_character.as_bytes()).into(),prefix:Sha256::digest(v.prefix.as_bytes()).into(),suffix:Sha256::digest(v.suffix.as_bytes()).into(),superscript:v.superscript,empty:v.user_character.is_empty()&&v.prefix.is_empty()&&v.suffix.is_empty()}}
}
#[derive(Clone,Eq,PartialEq,Serialize)]
enum ControlState {
    Number {kind:Kind,category:Category,value:i32,format:Option<FormatState>},
    Section {starts:&'static str,page:u32,picture:u32,table:u32,equation:u32},Document(NativeDocumentStartValues),
}
impl ControlState {fn requested(v:NativeInsertedNumberControl<'_>)->Self {match v {
    NativeInsertedNumberControl::AutoNumber {category,stored_number,format}=>Self::Number {kind:Kind::AutoNumber,category,value:stored_number,format:Some(FormatState::requested(format))},
    NativeInsertedNumberControl::Restart {category,stored_number,format}=>Self::Number {kind:Kind::Restart,category,value:stored_number,format:format.map(FormatState::requested)},
    NativeInsertedNumberControl::SectionStart {page_starts_on,page,picture,table,equation}=>Self::Section {starts:page_starts_on.text(),page,picture,table,equation},
    NativeInsertedNumberControl::DocumentStart(v)=>Self::Document(v),
}}}
fn hash(value:&impl Serialize,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E> {let bytes=serde_json::to_vec(value).map_err(|_|E::Limit)?;if bytes.len()>limits.config().output_bytes{return Err(E::Limit);}Ok(Sha256::digest(bytes).into())}
fn position_name(p:Position)->&'static str {match p {Position::Before=>"before",Position::After=>"after",Position::FirstChild=>"first_child",Position::LastChild=>"last_child",Position::Subtree=>"subtree"}}
impl NativeNumberTopologyRequest<'_> {
    /// Request identity only; neither cached source/access nor execution authority.
    /// # Errors
    /// Rejects empty/oversized requests, invalid XML values and byte limits.
    pub fn canonical_sha256(&self,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E> {
        preflight(self,limits)?;
        let deleted=self.deletions.iter().map(|d|(d.source_control_id,d.source_fingerprint_sha256,d.remove_owned_empty_wrapper)).collect::<Vec<_>>();
        let inserted=self.insertions.iter().map(|i|(Sha256::digest(i.local_id.as_str().as_bytes()).to_vec(),&i.target.opaque_handle,i.target.fingerprint_sha256,position_name(i.position),i.controls.iter().copied().map(ControlState::requested).collect::<Vec<_>>())).collect::<Vec<_>>();
        hash(&(self.expected_joined_state_sha256,deleted,inserted),limits)
    }
}
pub(super) fn preflight(request:&NativeNumberTopologyRequest<'_>,limits:ReferenceAuxiliaryLimits)->Result<usize,E> {
    if request.deletions.is_empty()&&request.insertions.is_empty(){return Err(E::Value);}
    let maximum=limits.config().items_per_kind.min(PatchLimits::default().config().max_intents);
    let mut count=request.deletions.len().checked_add(request.insertions.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;let mut bytes=0usize;
    for insertion in request.insertions {
        if insertion.position==Position::Subtree||insertion.controls.is_empty(){return Err(E::Value);}
        count=count.checked_add(insertion.controls.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;
        for control in insertion.controls {
            let format=match *control {NativeInsertedNumberControl::AutoNumber {format,..}=>Some(format),NativeInsertedNumberControl::Restart {format,..}=>format,_=>None};
            if let Some(f)=format{for text in [f.user_character,f.prefix,f.suffix] {
                if text.len()>limits.config().text_bytes{return Err(E::Limit);}
                bytes=bytes.checked_add(text.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;PatchText::new(text).map_err(|_|E::Value)?;
            }}
        }
    }Ok(count)
}
pub(super) struct Tracked {pub id:LogicalId,anchor:SourceAnchorHandle,pub path:PackagePath,index:usize,pub point:usize,state:ControlState}
impl Tracked {pub fn same_value(&self,other:&Self)->bool {self.state==other.state}}
pub(super) fn control_digest(control:NativeInsertedNumberControl<'_>,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E>{hash(&ControlState::requested(control),limits)}
pub(super) fn inventory(source:&ImportedDocumentStructure,numbers:&ImportedCaptionNumbering<'_>,context:&ImportedNumberingContext<'_>)->Result<Vec<Tracked>,E> {
    let mut rows=Vec::new();
    for c in numbers.controls(){rows.push((&c.logical_control_id,c.source_fingerprint_sha256,ControlState::Number {kind:c.kind,category:c.category,value:c.stored_number,format:c.format.as_ref().map(FormatState::observed)}));}
    for c in numbers.section_starts(){rows.push((&c.logical_control_id,c.source_fingerprint_sha256,ControlState::Section {starts:c.page_starts_on,page:c.page,picture:c.picture,table:c.table,equation:c.equation}));}
    if let Some(c)=context.document_start(){rows.push((&c.logical_control_id,c.source_fingerprint_sha256,ControlState::Document(NativeDocumentStartValues {page:c.page,footnote:c.footnote,endnote:c.endnote,picture:c.picture,table:c.table,equation:c.equation})));}
    rows.into_iter().map(|(id,fp,state)|{
        let opaque=id.as_str().strip_prefix("native-number-").ok_or(E::Selection)?;let anchor=SourceAnchorHandle {opaque_handle:LogicalId::parse(opaque).map_err(|_|E::Selection)?,fingerprint_sha256:fp};
        let resolved=source.source().resolve_anchor(&anchor).map_err(|_|E::Selection)?;let index=resolved.element_index().ok_or(E::Selection)?;
        let point=resolved.part().xml().ok_or(E::Selection)?.elements()[index].start_tag_span().start();
        Ok(Tracked {id:id.clone(),anchor,path:resolved.part().path().clone(),index,point,state})
    }).collect()
}
struct NewExpected {request:usize,item:usize,local_sha:[u8;32],relative:usize,state:ControlState}
struct Operation<'a> {part:&'a ImportedSourcePart,index:usize,position:Position,start:usize,end:usize,fragments:Vec<ValidatedXmlFragment>,payload_bytes:usize,new:Vec<NewExpected>}
struct Inserted {path:PackagePath,start:usize,end:usize,relative:usize,request:usize,item:usize,local_sha:[u8;32],state:ControlState}
pub(super) struct TopologyPlan {pub receipt:Option<NativeNumberTopologyOutputReceipt>,retained:Vec<Tracked>,inserted:Vec<Inserted>}
impl TopologyPlan {
    pub fn verify(&mut self,output:&ImportedDocumentStructure,numbers:&ImportedCaptionNumbering<'_>,maps:&OutputEditMap<'_>,limits:ReferenceAuxiliaryLimits)->Result<(),E> {
        let Some(receipt)=self.receipt.as_mut()else{return Ok(())};
        let context=numbers.import_context(limits).map_err(|_|E::Readback)?;
        let after=inventory(output,numbers,&context)?;let mut actual=BTreeMap::new();
        for control in after {if actual.insert((control.path.clone(),control.point),control).is_some(){return Err(E::Readback);}}
        if actual.len()!=self.retained.len().checked_add(self.inserted.len()).ok_or(E::Limit)?{return Err(E::Readback);}
        for old in &self.retained {let point=maps.original_position(&old.path,old.point)?;let found=actual.remove(&(old.path.clone(),point)).ok_or(E::Readback)?;if found.state!=old.state{return Err(E::Readback);}}
        for new in &self.inserted {
            let point=maps.edit_start(&new.path,new.start,new.end)?.checked_add(new.relative).ok_or(E::Limit)?;
            let found=actual.remove(&(new.path.clone(),point)).ok_or(E::Readback)?;if found.state!=new.state{return Err(E::Readback);}
            receipt.inserted.push(NativeNumberInsertionBinding {request_ordinal:new.request,item_ordinal:new.item,local_id_sha256:new.local_sha,output_control_id:found.id,requested_state_sha256:hash(&new.state,limits)?});
        }
        if !actual.is_empty(){return Err(E::Readback);}receipt.complete_original_and_inserted_inventory_read_back=true;Ok(())
    }
}
pub(super) fn protected<'a>(part:&'a ImportedSourcePart,index:usize,guards:&mut BTreeMap<&'a PackagePath,Vec<bool>>,subtree:&mut BTreeMap<&'a PackagePath,Vec<bool>>,visits:&mut usize)->Result<(),E> {
    let xml=part.xml().ok_or(E::Selection)?;
    if !guards.contains_key(part.path()){*visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;guards.insert(part.path(),observed_protection(xml)?);}
    if !subtree.contains_key(part.path()){*visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;subtree.insert(part.path(),subtree_protection(xml)?);}
    if guards.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?||subtree.get(part.path()).and_then(|g|g.get(index)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
    if part.path().as_str()=="Contents/header.xml"{let mut parent=Some(index);while let Some(i)=parent {let n=&xml.elements()[i];parent=n.parent();
        if n.attributes().iter().any(|a|a.name().namespace().is_none()&&matches!(a.name().local_name(),"lock"|"protect")&&!matches!(a.semantic_value(),"0"|"false")){return Err(E::Protection);}}}Ok(())
}
pub(super) fn plan<'a>(source:&'a ImportedDocumentStructure,state:Option<&ImportedCaptionSourceState<'_>>,request:Option<&NativeNumberTopologyRequest<'_>>,limits:ReferenceAuxiliaryLimits,
    parts:&mut BTreeMap<&'a PackagePath,PartEdits<'a>>,guards:&mut BTreeMap<&'a PackagePath,Vec<bool>>,subtree:&mut BTreeMap<&'a PackagePath,Vec<bool>>,visits:&mut usize,escaped:&mut usize,intents:&mut Vec<PatchIntent>)->Result<TopologyPlan,E> {
    let Some(request)=request else{return Ok(TopologyPlan {receipt:None,retained:Vec::new(),inserted:Vec::new()})};let state=state.ok_or(E::Source)?;
    if request.expected_joined_state_sha256!=state.receipt().joined_state_sha256{return Err(E::Source);}
    let original=inventory(source,state.numbering(),state.context())?;let original_count=original.len();let by_id:BTreeMap<_,_>=original.iter().map(|c|(&c.id,c)).collect();
    let part_index:BTreeMap<_,_>=source.source().parts().iter().map(|p|(p.path(),p)).collect();
    let mut deleted=BTreeSet::new();let mut deletion_bindings=Vec::new();
    let mut deletion_roots=BTreeMap::<(&PackagePath,usize),Vec<usize>>::new();
    for deletion in request.deletions {
        if !deleted.insert(deletion.source_control_id){return Err(E::Selection);}let old=*by_id.get(deletion.source_control_id).ok_or(E::Selection)?;
        if old.anchor.fingerprint_sha256!=deletion.source_fingerprint_sha256{return Err(E::Selection);}
        let part=*part_index.get(&old.path).ok_or(E::Selection)?;protected(part,old.index,guards,subtree,visits)?;
        let ordinal=deletion_bindings.len();deletion_bindings.push(NativeNumberDeletionBinding {source_control_id:old.id.clone(),source_sha256:deletion.source_fingerprint_sha256,owned_empty_wrapper_removed:false});
        deletion_roots.entry((part.path(),old.index)).or_default().push(ordinal);
    }
    let caption_runs:BTreeSet<_>=state.frames().frames().iter().flat_map(|f|f.runs.iter()).filter_map(|r|r.logical_run_id.as_str().strip_prefix("caption-run-")).collect();
    let mut local_ids=BTreeSet::new();let mut inserted=BTreeMap::<(&PackagePath,usize,usize),Operation<'a>>::new();
    for (ordinal,insertion) in request.insertions.iter().enumerate() {
        if !local_ids.insert(insertion.local_id){return Err(E::Selection);}
        let resolved=source.source().resolve_anchor(insertion.target).map_err(|_|E::Selection)?;let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let index=resolved.element_index().ok_or(E::Selection)?;
        let parent=if matches!(insertion.position,Position::Before|Position::After){xml.elements()[index].parent().ok_or(E::Selection)?}else{index};
        protected(part,parent,guards,subtree,visits)?;
        let mut fragments=Vec::new();let mut expected=Vec::new();let mut payload=0usize;
        for (item,control) in insertion.controls.iter().copied().enumerate() {
            let (bytes,relative)=generate(control,part,parent,state,&caption_runs)?;
            expected.push(NewExpected {request:ordinal,item,local_sha:Sha256::digest(insertion.local_id.as_str().as_bytes()).into(),relative:payload.checked_add(relative).ok_or(E::Limit)?,state:ControlState::requested(control)});
            payload=payload.checked_add(bytes.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
            fragments.push(ValidatedXmlFragment::parse(&bytes,PatchLimits::default()).map_err(|_|E::Value)?);
        }
        let edit=crate::patch::element_splice::source_edit(xml,index,insertion.position,&fragments,PatchLimits::default()).map_err(|_|E::Selection)?;
        let key=(part.path(),edit.start,edit.end);
        if let Some(previous)=inserted.get_mut(&key) {
            for mut new in expected{new.relative=new.relative.checked_add(previous.payload_bytes).ok_or(E::Limit)?;previous.new.push(new);}
            previous.payload_bytes=previous.payload_bytes.checked_add(payload).ok_or(E::Limit)?;previous.fragments.extend(fragments);
        }else{inserted.insert(key,Operation {part,index,position:insertion.position,start:edit.start,end:edit.end,fragments,payload_bytes:payload,new:expected});}
    }
    // Remove a ctrl wrapper only when all its element children were selected,
    // it has no unknown attributes/content and no new insertion remains inside.
    let mut wrappers=BTreeSet::new();
    let mut insertion_points=BTreeMap::<&PackagePath,Vec<usize>>::new();
    for operation in inserted.values(){insertion_points.entry(operation.part.path()).or_default().push(operation.start);}
    for deletion in request.deletions.iter().filter(|d|d.remove_owned_empty_wrapper) {let old=*by_id.get(deletion.source_control_id).ok_or(E::Selection)?;let part=*part_index.get(&old.path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;
        if let Some(parent)=xml.elements()[old.index].parent().filter(|p|super::named(&xml.elements()[*p],"ctrl")){wrappers.insert((part.path(),parent));}}
    for (path,parent) in wrappers {
        let part=*part_index.get(path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;let node=&xml.elements()[parent];let outer=node.outer_span().ok_or(E::Selection)?;
        let inserted_inside=insertion_points.get(path).is_some_and(|points|{let i=points.partition_point(|p|*p<=outer.start());points.get(i).is_some_and(|p|*p<outer.end())});
        if node.attributes().iter().any(|a|!a.is_namespace_declaration())||inserted_inside{continue;}
        let mut child=node.first_child();let mut children=Vec::new();let mut all=true;
        while let Some(i)=child{child=xml.elements()[i].next_sibling();if !deletion_roots.get(&(path,i)).is_some_and(|ordinals|ordinals.iter().all(|o|request.deletions[*o].remove_owned_empty_wrapper)){all=false;break;}children.push(i);}
        if !all||children.is_empty(){continue;}
        let content=node.content_span().ok_or(E::Selection)?;
        let whitespace=xml.with_source_bytes(|raw|{let mut cursor=content.start();for &i in &children {let Some(span)=xml.elements()[i].outer_span()else{return false};if !raw[cursor..span.start()].iter().all(|b|matches!(b,b' '|b'\r'|b'\n'|b'\t')){return false;}cursor=span.end();}raw[cursor..content.end()].iter().all(|b|matches!(b,b' '|b'\r'|b'\n'|b'\t'))});
        if !whitespace{continue;}let mut ordinals=Vec::new();
        for child in children {for ordinal in deletion_roots.remove(&(path,child)).ok_or(E::Selection)? {deletion_bindings[ordinal].owned_empty_wrapper_removed=true;ordinals.push(ordinal);}}
        deletion_roots.insert((path,parent),ordinals);
    }
    let mut operations=Vec::new();
    for ((path,index),_) in deletion_roots {
        let part=*part_index.get(path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;let outer=xml.elements()[index].outer_span().ok_or(E::Selection)?;
        operations.push(Operation {part,index,position:Position::Subtree,start:outer.start(),end:outer.end(),fragments:Vec::new(),payload_bytes:0,new:Vec::new()});
    }
    let mut boundaries=BTreeMap::new();
    // Prefer a deletion starting at a shared boundary over the preceding one.
    for (i,o) in operations.iter().enumerate(){boundaries.entry((o.part.path(),o.end)).or_insert(i);}
    for (i,o) in operations.iter().enumerate(){boundaries.insert((o.part.path(),o.start),i);}
    for (_,mut insertion) in inserted {
        // Collapse insertion at a deleted node boundary into one source-bound
        // forest replacement. Original overlap rules are not relaxed.
        let compatible=if insertion.start==insertion.end {boundaries.get(&(insertion.part.path(),insertion.start)).copied()}else{None};
        if let Some(i)=compatible {let target=&mut operations[i];for mut new in insertion.new.drain(..){new.relative=new.relative.checked_add(target.payload_bytes).ok_or(E::Limit)?;target.new.push(new);}target.payload_bytes=target.payload_bytes.checked_add(insertion.payload_bytes).ok_or(E::Limit)?;target.fragments.extend(insertion.fragments);}else{operations.push(insertion);}
    }
    let mut new_rows=Vec::new();
    for operation in operations {
        let xml=operation.part.xml().ok_or(E::Selection)?;
        let edit=crate::patch::element_splice::source_edit(xml,operation.index,operation.position,&operation.fragments,PatchLimits::default()).map_err(|_|E::Selection)?;
        *escaped=escaped.checked_add(edit.replacement.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        for new in operation.new {new_rows.push(Inserted {path:operation.part.path().clone(),start:edit.start,end:edit.end,relative:new.relative.checked_add(edit.fragment_offset).ok_or(E::Limit)?,request:new.request,item:new.item,local_sha:new.local_sha,state:new.state});}
        parts.entry(operation.part.path()).or_insert_with(||PartEdits {xml,edits:Vec::new()}).edits.push(Edit {start:edit.start,end:edit.end,bytes:edit.replacement});
        intents.push(PatchIntent::SpliceElements {target:XmlElementSelector::bind(operation.part.path(),xml,operation.index).map_err(|_|E::Selection)?,position:operation.position,fragments:operation.fragments});
    }
    drop(by_id);
    let retained=original.into_iter().filter(|c|!deleted.contains(&c.id)).collect::<Vec<_>>();
    let output_controls=retained.len().checked_add(new_rows.len()).ok_or(E::Limit)?;
    let receipt=NativeNumberTopologyOutputReceipt {profile:"hwpx-agent.caption-native-number-topology/output-v1",source_joined_state_sha256:state.receipt().joined_state_sha256,caller_request_sha256:request.canonical_sha256(limits)?,
        original_controls:original_count,retained_controls:retained.len(),output_controls,deleted:deletion_bindings,inserted:Vec::new(),complete_original_and_inserted_inventory_read_back:false,native_counter_recalculation_qualified:false,execution_publication_authority:false};
    Ok(TopologyPlan {receipt:Some(receipt),retained,inserted:new_rows})
}
fn generate(control:NativeInsertedNumberControl<'_>,part:&ImportedSourcePart,parent:usize,state:&ImportedCaptionSourceState<'_>,caption_runs:&BTreeSet<&str>)->Result<(Vec<u8>,usize),E> {
    let xml=part.xml().ok_or(E::Selection)?;let node=&xml.elements()[parent];
    let is_document=matches!(control,NativeInsertedNumberControl::DocumentStart(_));
    let is_section=matches!(control,NativeInsertedNumberControl::SectionStart {..});
    let (run,wrap)=if is_document {
        if part.path().as_str()!="Contents/header.xml"||parent!=xml.root_element()||node.name().namespace()!=Some(HH)||node.name().local_name()!="head"{return Err(E::Selection);} (None,false)
    }else if super::named(node,"run"){(Some(parent),true)}
    else if super::named(node,"ctrl")&&!is_section{(node.parent().filter(|p|super::named(&xml.elements()[*p],"run")),false)}
    else if super::named(node,"secPr")&&is_section{(node.parent().filter(|p|super::named(&xml.elements()[*p],"run")),false)}else{return Err(E::Selection)};
    if !is_document {
        let run=run.ok_or(E::Selection)?;let paragraph=xml.elements()[run].parent().filter(|p|super::named(&xml.elements()[*p],"p")).ok_or(E::Selection)?;
        let p=part.element_anchor(paragraph).ok_or(E::Selection)?;let r=part.element_anchor(run).ok_or(E::Selection)?;
        if !state.numbering().admits_number_paragraph(&p.opaque_handle)&&!caption_runs.contains(r.opaque_handle.as_str()){return Err(E::Selection);}
        if is_section&&(xml.elements()[paragraph].parent()!=Some(xml.root_element())||!state.numbering().admits_number_paragraph(&p.opaque_handle)){return Err(E::Selection);}
    }
    render_control(control,wrap)
}
pub(super) fn render_control(control:NativeInsertedNumberControl<'_>,wrap:bool)->Result<(Vec<u8>,usize),E> {
    let is_document=matches!(control,NativeInsertedNumberControl::DocumentStart(_));
    let is_section=matches!(control,NativeInsertedNumberControl::SectionStart {..});
    let namespace=if is_document{HH}else{HP};let prefix=if is_document{"hh"}else{"hp"};
    let (tag,attributes,format)=match control {
        NativeInsertedNumberControl::AutoNumber {category,stored_number,format}=>("autoNum",format!(" num=\"{stored_number}\" numType=\"{}\"",category_text(category)),Some(format)),
        NativeInsertedNumberControl::Restart {category,stored_number,format}=>("newNum",format!(" num=\"{stored_number}\" numType=\"{}\"",category_text(category)),format),
        NativeInsertedNumberControl::SectionStart {page_starts_on,page,picture,table,equation}=>("startNum",format!(" pageStartsOn=\"{}\" page=\"{page}\" pic=\"{picture}\" tbl=\"{table}\" equation=\"{equation}\"",page_starts_on.text()),None),
        NativeInsertedNumberControl::DocumentStart(v)=>("beginNum",format!(" page=\"{}\" footnote=\"{}\" endnote=\"{}\" pic=\"{}\" tbl=\"{}\" equation=\"{}\"",v.page,v.footnote,v.endnote,v.picture,v.table,v.equation),None),
    };
    let wrapper=if wrap {Some(if is_section{"secPr"}else{"ctrl"})}else{None};
    let mut text=String::new();if let Some(wrapper)=wrapper{text.push_str(&format!("<{prefix}:{wrapper} xmlns:{prefix}=\"{namespace}\">"));}
    let offset=text.len();let declaration=if wrapper.is_none(){format!(" xmlns:{prefix}=\"{namespace}\"")}else{String::new()};
    text.push_str(&format!("<{prefix}:{tag}{declaration}{attributes}"));
    if let Some(f)=format {
        let user=crate::patch::escape_attribute(f.user_character,XmlQuoteStyle::Double).map_err(|_|E::Value)?;
        let before=crate::patch::escape_attribute(f.prefix,XmlQuoteStyle::Double).map_err(|_|E::Value)?;
        let after=crate::patch::escape_attribute(f.suffix,XmlQuoteStyle::Double).map_err(|_|E::Value)?;
        text.push_str(&format!("><hp:autoNumFormat type=\"{}\" userChar=\"{user}\" prefixChar=\"{before}\" suffixChar=\"{after}\" supscript=\"{}\"/></{prefix}:{tag}>",f.format.as_str(),u8::from(f.superscript)));
    }else{text.push_str("/>");}
    if let Some(wrapper)=wrapper{text.push_str(&format!("</{prefix}:{wrapper}>"));}Ok((text.into_bytes(),offset))
}
