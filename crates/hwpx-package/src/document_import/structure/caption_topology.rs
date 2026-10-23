//! Typed creation/deletion of whole captions; no caller XML or native defaults.
use super::{ImportedDocumentStructure,caption_text::CaptionTextOutputError as E,caption_layout::CaptionLayout,
    caption_text_batch::{PartEdits,Edit},caption_edit_map::OutputEditMap,caption_number_topology::{self as numbers,NativeInsertedNumberControl as Number}};
use crate::{IdIndex,PackagePath,PatchIntent,PatchLimits,PatchText,ValidatedXmlFragment,XmlElementSelector,ElementSplicePosition as Position};
use crate::document_import::{reference_targets::{caption_source_state::ImportedCaptionSourceState,caption_frames::{ImportedCaptionFrames,CaptionStyleFamily as Family,CaptionStyleReferenceStatus as Status},
    numbering::{ImportedCaptionNumbering,context::NativeOwnerNumberingType}}};
use domain_ir::{CaptionObjectKind,LogicalId,ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::{collections::{BTreeMap,BTreeSet},fmt};
#[derive(Clone,Copy)]
pub enum CaptionContent<'a> {Text(&'a str),Number(Number<'a>)}
pub struct CaptionRun<'a> {pub character_style:u32,pub content:&'a[CaptionContent<'a>]}
pub struct CaptionParagraph<'a> {pub paragraph_style:u32,pub named_style:u32,pub runs:&'a[CaptionRun<'a>]}
pub struct CaptionCreation<'a> {pub local_id:&'a LogicalId,pub object_id:&'a LogicalId,pub object_fingerprint_sha256:[u8;32],pub layout:CaptionLayout,pub paragraphs:&'a[CaptionParagraph<'a>]}
#[derive(Clone,Copy)]
pub struct CaptionDeletion<'a> {pub caption_id:&'a LogicalId,pub caption_fingerprint_sha256:[u8;32]}
pub struct SourceCaptionTopologyRequest<'a> {pub expected_joined_state_sha256:[u8;32],pub deletions:&'a[CaptionDeletion<'a>],pub creations:&'a[CaptionCreation<'a>]}
macro_rules! redact {($($t:ty),+)=>{$(impl fmt::Debug for $t {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CaptionTopology(<redacted>; not_native_or_service_authority)")}})+}}
redact!(CaptionContent<'_>,CaptionRun<'_>,CaptionParagraph<'_>,CaptionCreation<'_>,CaptionDeletion<'_>,SourceCaptionTopologyRequest<'_>);
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionDeletionBinding {pub source_caption_id:LogicalId,pub source_caption_sha256:[u8;32]}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionCreationBinding {pub local_id_sha256:[u8;32],pub source_object_id:LogicalId,pub output_object_id:LogicalId,pub output_caption_id:LogicalId,pub generated_subtree_sha256:[u8;32],pub allocated_paragraph_ids:Vec<u32>}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct CaptionTopologyOutputReceipt {
    pub profile:&'static str,pub source_joined_state_sha256:[u8;32],pub caller_request_sha256:[u8;32],
    pub deleted:Vec<CaptionDeletionBinding>,pub created:Vec<CaptionCreationBinding>,pub original_captions:usize,pub output_captions:usize,
    pub retained_native_controls:usize,pub created_native_controls:usize,pub paragraph_id_elements_scanned:usize,
    pub complete_owner_caption_and_native_control_inventory_read_back:bool,pub native_counter_recalculation_qualified:bool,pub execution_publication_authority:bool,
}
fn hash(value:&impl Serialize,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E>{let bytes=serde_json::to_vec(value).map_err(|_|E::Limit)?;if bytes.len()>limits.config().output_bytes{return Err(E::Limit);}Ok(Sha256::digest(bytes).into())}
fn layout_valid(layout:CaptionLayout,limits:ReferenceAuxiliaryLimits)->Result<(),E>{
    if layout.width_hwpunit< -1{return Err(E::Value);}if layout.width_hwpunit.max(0) as u32>limits.config().extent_hwpunit||layout.gap_hwpunit>limits.config().extent_hwpunit||layout.last_width_hwpunit>limits.config().extent_hwpunit{return Err(E::Limit);}Ok(())
}
pub(super) fn preflight(request:&SourceCaptionTopologyRequest<'_>,limits:ReferenceAuxiliaryLimits)->Result<usize,E>{
    if request.deletions.is_empty()&&request.creations.is_empty(){return Err(E::Value);}
    let maximum=limits.config().items_per_kind.min(PatchLimits::default().config().max_intents);let mut count=request.deletions.len().checked_add(request.creations.len()).ok_or(E::Limit)?;let mut bytes=0usize;
    let mut text=|value:&str|->Result<(),E>{if value.len()>limits.config().text_bytes{return Err(E::Limit);}bytes=bytes.checked_add(value.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;PatchText::new(value).map_err(|_|E::Value)?;Ok(())};
    for creation in request.creations {layout_valid(creation.layout,limits)?;if creation.paragraphs.is_empty(){return Err(E::Value);}
        for paragraph in creation.paragraphs {count=count.checked_add(1).filter(|n|*n<=maximum).ok_or(E::Limit)?;if paragraph.runs.is_empty(){return Err(E::Value);}
            for run in paragraph.runs {count=count.checked_add(1).filter(|n|*n<=maximum).ok_or(E::Limit)?;if run.content.is_empty(){return Err(E::Value);}
                for item in run.content {count=count.checked_add(1).filter(|n|*n<=maximum).ok_or(E::Limit)?;match *item {
                    CaptionContent::Text(value)=>text(value)?,CaptionContent::Number(control)=>{
                        let format=match control {Number::AutoNumber {format,..}=>Some(format),Number::Restart {format,..}=>format,_=>return Err(E::Value)};
                        if let Some(f)=format{for value in [f.user_character,f.prefix,f.suffix]{text(value)?;}}
                    }
                }}
            }
        }
    }if count>maximum{return Err(E::Limit);}Ok(count)
}
impl SourceCaptionTopologyRequest<'_>{
    /// Bounded request identity only. Plain text/affixes/local labels are hashed.
    /// # Errors
    /// Rejects unsupported controls, malformed values and finite request limits.
    pub fn canonical_sha256(&self,limits:ReferenceAuxiliaryLimits)->Result<[u8;32],E>{
        preflight(self,limits)?;let deleted=self.deletions.iter().map(|d|(d.caption_id,d.caption_fingerprint_sha256)).collect::<Vec<_>>();let mut created=Vec::new();
        for creation in self.creations {let mut paragraphs=Vec::new();for p in creation.paragraphs {let mut runs=Vec::new();for r in p.runs {
            let mut content=Vec::new();for item in r.content {content.push(match *item {CaptionContent::Text(value)=>("text",<[u8;32]>::from(Sha256::digest(value.as_bytes()))),CaptionContent::Number(value)=>("number",numbers::control_digest(value,limits)?)});}runs.push((r.character_style,content));
        }paragraphs.push((p.paragraph_style,p.named_style,runs));}created.push((<[u8;32]>::from(Sha256::digest(creation.local_id.as_str().as_bytes())),creation.object_id,creation.object_fingerprint_sha256,creation.layout,paragraphs));}
        hash(&(self.expected_joined_state_sha256,deleted,created),limits)
    }
}
#[derive(Clone,Copy)]
enum ExpectedCaption {Retained(usize),Created(usize)}
struct Owner {path:PackagePath,point:usize,kind:CaptionObjectKind,numbering_type:Option<NativeOwnerNumberingType>,caption:Option<ExpectedCaption>}
struct Created {path:PackagePath,start:usize,end:usize,offset:usize,sha:[u8;32],bytes:usize,local_sha:[u8;32],object_id:LogicalId,ids:Vec<u32>,numbers:usize}
pub(super) struct CaptionPlan {pub receipt:Option<CaptionTopologyOutputReceipt>,owners:Vec<Owner>,created:Vec<Created>,retained:Vec<numbers::Tracked>}
impl CaptionPlan {
    pub fn expected_count(&self,original:usize)->usize{self.receipt.as_ref().map_or(original,|r|r.output_captions)}
    pub fn verify(&mut self,output:&ImportedDocumentStructure,after:&ImportedCaptionNumbering<'_>,frames:&ImportedCaptionFrames<'_>,maps:&OutputEditMap<'_>,limits:ReferenceAuxiliaryLimits)->Result<(),E>{
        let Some(receipt)=self.receipt.as_mut()else{return Ok(())};let context=after.import_context(limits).map_err(|_|E::Readback)?;
        if context.owners().len()!=self.owners.len()||frames.frames().len()!=receipt.output_captions{return Err(E::Readback);}
        let parts:BTreeMap<_,_>=output.source().parts().iter().map(|p|(p.path(),p)).collect();
        let mut actual_owners=BTreeMap::new();for owner in context.owners(){let path=output.source().spine().get(owner.source_position.spine_ordinal).ok_or(E::Readback)?;let part=*parts.get(path).ok_or(E::Readback)?;let point=part.xml().ok_or(E::Readback)?.elements()[owner.source_position.xml_element_ordinal].start_tag_span().start();if actual_owners.insert((path,point),owner).is_some(){return Err(E::Readback);}}
        let mut actual_frames=BTreeMap::new();for frame in frames.frames(){let path=output.source().spine().get(frame.source_position.spine_ordinal).ok_or(E::Readback)?;let part=*parts.get(path).ok_or(E::Readback)?;let point=part.xml().ok_or(E::Readback)?.elements()[frame.source_position.xml_element_ordinal].start_tag_span().start();if actual_frames.insert((path,point),frame).is_some(){return Err(E::Readback);}}
        let mut new_ranges=BTreeMap::<&PackagePath,Vec<(usize,usize,usize)>>::new();
        for owner in &self.owners {let point=maps.original_position(&owner.path,owner.point)?;let actual=actual_owners.remove(&(&owner.path,point)).ok_or(E::Readback)?;
            if actual.structural_kind!=owner.kind||actual.numbering_type!=owner.numbering_type{return Err(E::Readback);}
            let caption_point=match owner.caption {None=>None,Some(ExpectedCaption::Retained(point))=>Some(maps.original_position(&owner.path,point)?),Some(ExpectedCaption::Created(i))=>{let created=&self.created[i];Some(maps.edit_start(&created.path,created.start,created.end)?.checked_add(created.offset).ok_or(E::Limit)?)}};
            if let Some(point)=caption_point {let frame=actual_frames.remove(&(&owner.path,point)).ok_or(E::Readback)?;if actual.logical_caption_id.as_ref()!=Some(&frame.logical_caption_id)||frame.logical_object_id!=actual.logical_object_id{return Err(E::Readback);}
                if let Some(ExpectedCaption::Created(i))=owner.caption {let created=&self.created[i];let part=*parts.get(&owner.path).ok_or(E::Readback)?;let xml=part.xml().ok_or(E::Readback)?;let node=&xml.elements()[frame.source_position.xml_element_ordinal];let span=node.outer_span().ok_or(E::Readback)?;
                    if span.end()-span.start()!=created.bytes||xml.with_source_bytes(|raw|<[u8;32]>::from(Sha256::digest(&raw[span.start()..span.end()])))!=created.sha||frame.paragraphs.len()!=created.ids.len(){return Err(E::Readback);}
                    new_ranges.entry(&created.path).or_default().push((span.start(),span.end(),i));
                    receipt.created.push(CaptionCreationBinding {local_id_sha256:created.local_sha,source_object_id:created.object_id.clone(),output_object_id:actual.logical_object_id.clone(),output_caption_id:frame.logical_caption_id.clone(),generated_subtree_sha256:created.sha,allocated_paragraph_ids:created.ids.clone()});
                }
            }else if actual.logical_caption_id.is_some(){return Err(E::Readback);}
        }
        if !actual_owners.is_empty()||!actual_frames.is_empty(){return Err(E::Readback);}
        let mut actual=BTreeMap::new();for control in numbers::inventory(output,after,&context)?{if actual.insert((control.path.clone(),control.point),control).is_some(){return Err(E::Readback);}}
        if actual.len()!=receipt.retained_native_controls.checked_add(receipt.created_native_controls).ok_or(E::Limit)?{return Err(E::Readback);}
        for old in &self.retained {let point=maps.original_position(&old.path,old.point)?;let found=actual.remove(&(old.path.clone(),point)).ok_or(E::Readback)?;if !old.same_value(&found){return Err(E::Readback);}}
        for ranges in new_ranges.values_mut(){ranges.sort_by_key(|r|r.0);}let mut counts=vec![0usize;self.created.len()];
        for ((path,point),_) in actual {let ranges=new_ranges.get(&path).ok_or(E::Readback)?;let i=ranges.partition_point(|r|r.0<=point).checked_sub(1).ok_or(E::Readback)?;let &(start,end,created)=&ranges[i];if point<start||point>=end{return Err(E::Readback);}counts[created]+=1;}
        if counts.iter().zip(&self.created).any(|(count,c)|*count!=c.numbers){return Err(E::Readback);}receipt.complete_owner_caption_and_native_control_inventory_read_back=true;Ok(())
    }
}
pub(super) fn reject_deleted_selections(request:&SourceCaptionTopologyRequest<'_>,texts:&[super::caption_text_batch::CaptionTextReplacement<'_>],layouts:&[super::caption_edit_batch::CaptionLayoutReplacement<'_>],styles:&[super::caption_style_batch::CaptionStyleReplacement<'_>])->Result<(),E>{
    let deleted:BTreeSet<_>=request.deletions.iter().map(|d|d.caption_id).collect();
    if texts.iter().any(|r|deleted.contains(r.caption_id))||layouts.iter().any(|r|deleted.contains(r.caption_id))||styles.iter().any(|r|deleted.contains(r.caption_id)){return Err(E::Selection);}Ok(())
}
pub(super) fn plan<'a>(source:&'a ImportedDocumentStructure,state:Option<&ImportedCaptionSourceState<'_>>,request:Option<&SourceCaptionTopologyRequest<'_>>,limits:ReferenceAuxiliaryLimits,
    parts:&mut BTreeMap<&'a PackagePath,PartEdits<'a>>,guards:&mut BTreeMap<&'a PackagePath,Vec<bool>>,subtree:&mut BTreeMap<&'a PackagePath,Vec<bool>>,visits:&mut usize,escaped:&mut usize,intents:&mut Vec<PatchIntent>)->Result<CaptionPlan,E>{
    let Some(request)=request else{return Ok(CaptionPlan {receipt:None,owners:vec![],created:vec![],retained:vec![]})};let state=state.ok_or(E::Source)?;
    if request.expected_joined_state_sha256!=state.receipt().joined_state_sha256{return Err(E::Source);}
    let part_index:BTreeMap<_,_>=source.source().parts().iter().map(|p|(p.path(),p)).collect();
    let frame_index:BTreeMap<_,_>=state.frames().frames().iter().map(|f|(&f.logical_caption_id,f)).collect();
    let owner_index:BTreeMap<_,_>=state.context().owners().iter().map(|o|(&o.logical_object_id,o)).collect();
    let mut deleted=BTreeMap::new();let mut deleted_ranges=BTreeMap::<&PackagePath,Vec<(usize,usize)>>::new();let mut deletion_bindings=Vec::new();
    for deletion in request.deletions {let frame=*frame_index.get(deletion.caption_id).ok_or(E::Selection)?;if frame.source_fingerprint_sha256!=deletion.caption_fingerprint_sha256||deleted.contains_key(deletion.caption_id){return Err(E::Selection);}
        let path=source.source().spine().get(frame.source_position.spine_ordinal).ok_or(E::Selection)?;let part=*part_index.get(path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;let index=frame.source_position.xml_element_ordinal;
        if !super::named(&xml.elements()[index],"caption"){return Err(E::Selection);}numbers::protected(part,index,guards,subtree,visits)?;
        let outer=xml.elements()[index].outer_span().ok_or(E::Selection)?;deleted_ranges.entry(part.path()).or_default().push((outer.start(),outer.end()));deleted.insert(deletion.caption_id,(part,index));
        deletion_bindings.push(CaptionDeletionBinding {source_caption_id:frame.logical_caption_id.clone(),source_caption_sha256:frame.source_fingerprint_sha256});
    }
    let mut local_ids=BTreeSet::new();let mut targets=BTreeSet::new();let mut style_cache=BTreeSet::new();let mut next_ids=BTreeMap::<&PackagePath,u64>::new();let mut scanned=0usize;
    let mut created=Vec::new();let mut creation_owner=BTreeMap::new();
    for creation in request.creations {
        if !local_ids.insert(creation.local_id)||!targets.insert(creation.object_id){return Err(E::Selection);}let owner=*owner_index.get(creation.object_id).ok_or(E::Selection)?;
        if owner.source_fingerprint_sha256!=creation.object_fingerprint_sha256{return Err(E::Selection);}
        let path=source.source().spine().get(owner.source_position.spine_ordinal).ok_or(E::Selection)?;let part=*part_index.get(path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;let index=owner.source_position.xml_element_ordinal;
        numbers::protected(part,index,guards,subtree,visits)?;
        let replacement=owner.logical_caption_id.as_ref().map(|id|deleted.remove(id).ok_or(E::Selection)).transpose()?;
        if !next_ids.contains_key(part.path()){let mut maximum=None;for node in xml.elements(){scanned=scanned.checked_add(1).ok_or(E::Limit)?;if super::named(node,"p") {if let Some(id)=node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()=="id") {let id=id.semantic_value().parse::<u64>().map_err(|_|E::Source)?;maximum=Some(maximum.map_or(id,|old:u64|old.max(id)));}}}next_ids.insert(part.path(),IdIndex::next_decimal_after_maximum(maximum).map_err(|_|E::Limit)?);}
        let mut ids=Vec::new();for paragraph in creation.paragraphs {
            for (family,id) in [(Family::Paragraph,paragraph.paragraph_style),(Family::Named,paragraph.named_style)] {check_style(state,family,id,&mut style_cache)?;}
            for run in paragraph.runs{check_style(state,Family::Character,run.character_style,&mut style_cache)?;}
            let next=next_ids.get_mut(part.path()).ok_or(E::Selection)?;ids.push(u32::try_from(*next).map_err(|_|E::Limit)?);*next=next.checked_add(1).ok_or(E::Limit)?;
        }
        let (bytes,count)=render(creation,&ids,limits)?;let sha=Sha256::digest(&bytes).into();let length=bytes.len();let fragments=vec![ValidatedXmlFragment::parse(&bytes,PatchLimits::default()).map_err(|_|E::Value)?];
        let (target,position)=replacement.map_or((index,Position::LastChild),|(_,index)|(index,Position::Subtree));
        let edit=crate::patch::element_splice::source_edit(xml,target,position,&fragments,PatchLimits::default()).map_err(|_|E::Selection)?;
        *escaped=escaped.checked_add(edit.replacement.len()).filter(|n|*n<=limits.config().output_bytes).ok_or(E::Limit)?;
        creation_owner.insert(creation.object_id,created.len());created.push(Created {path:part.path().clone(),start:edit.start,end:edit.end,offset:edit.fragment_offset,sha,bytes:length,local_sha:Sha256::digest(creation.local_id.as_str().as_bytes()).into(),object_id:owner.logical_object_id.clone(),ids,numbers:count});
        parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:vec![]}).edits.push(Edit {start:edit.start,end:edit.end,bytes:edit.replacement});
        intents.push(PatchIntent::SpliceElements {target:XmlElementSelector::bind(part.path(),xml,target).map_err(|_|E::Selection)?,position,fragments});
    }
    for (_,(part,index)) in deleted {let xml=part.xml().ok_or(E::Selection)?;let outer=xml.elements()[index].outer_span().ok_or(E::Selection)?;
        parts.entry(part.path()).or_insert_with(||PartEdits {xml,edits:vec![]}).edits.push(Edit {start:outer.start(),end:outer.end(),bytes:vec![]});
        intents.push(PatchIntent::SpliceElements {target:XmlElementSelector::bind(part.path(),xml,index).map_err(|_|E::Selection)?,position:Position::Subtree,fragments:vec![]});
    }
    let deleted_ids:BTreeSet<_>=request.deletions.iter().map(|d|d.caption_id).collect();let mut owners=Vec::new();
    for owner in state.context().owners(){let path=source.source().spine().get(owner.source_position.spine_ordinal).ok_or(E::Selection)?;let part=*part_index.get(path).ok_or(E::Selection)?;let xml=part.xml().ok_or(E::Selection)?;
        let caption=if let Some(&i)=creation_owner.get(&owner.logical_object_id){Some(ExpectedCaption::Created(i))}else if let Some(id)=owner.logical_caption_id.as_ref().filter(|id|!deleted_ids.contains(id)) {let frame=*frame_index.get(id).ok_or(E::Selection)?;Some(ExpectedCaption::Retained(xml.elements()[frame.source_position.xml_element_ordinal].start_tag_span().start()))}else{None};
        owners.push(Owner {path:path.clone(),point:xml.elements()[owner.source_position.xml_element_ordinal].start_tag_span().start(),kind:owner.structural_kind,numbering_type:owner.numbering_type,caption});
    }
    for ranges in deleted_ranges.values_mut(){ranges.sort_unstable();}
    let retained=numbers::inventory(source,state.numbering(),state.context())?.into_iter().filter(|control|{let Some(ranges)=deleted_ranges.get(&control.path)else{return true};let i=ranges.partition_point(|r|r.0<=control.point);!i.checked_sub(1).and_then(|i|ranges.get(i)).is_some_and(|r|control.point<r.1)}).collect::<Vec<_>>();
    let output_captions=state.frames().frames().len().checked_sub(request.deletions.len()).and_then(|n|n.checked_add(created.len())).ok_or(E::Limit)?;
    let created_native_controls=created.iter().try_fold(0usize,|n,c|n.checked_add(c.numbers)).ok_or(E::Limit)?;
    let receipt=CaptionTopologyOutputReceipt {profile:"hwpx-agent.caption-topology/typed-structure-output-v1",source_joined_state_sha256:request.expected_joined_state_sha256,caller_request_sha256:request.canonical_sha256(limits)?,deleted:deletion_bindings,created:vec![],original_captions:state.frames().frames().len(),output_captions,
        retained_native_controls:retained.len(),created_native_controls,paragraph_id_elements_scanned:scanned,complete_owner_caption_and_native_control_inventory_read_back:false,native_counter_recalculation_qualified:false,execution_publication_authority:false};
    Ok(CaptionPlan {receipt:Some(receipt),owners,created,retained})
}
fn check_style(state:&ImportedCaptionSourceState<'_>,family:Family,id:u32,cache:&mut BTreeSet<(Family,u32)>)->Result<(),E>{if cache.insert((family,id)){let reference=state.frames().style_declaration(family,id);if reference.status!=Status::UniqueSourceDeclaration||reference.declaration_sha256.is_none(){return Err(E::Selection);}}Ok(())}
fn render(creation:&CaptionCreation<'_>,ids:&[u32],limits:ReferenceAuxiliaryLimits)->Result<(Vec<u8>,usize),E>{
    let layout=creation.layout;let side=match layout.side {domain_ir::NativeCaptionSide::Left=>"LEFT",domain_ir::NativeCaptionSide::Right=>"RIGHT",domain_ir::NativeCaptionSide::Top=>"TOP",domain_ir::NativeCaptionSide::Bottom=>"BOTTOM"};
    let mut xml=format!("<hp:caption xmlns:hp=\"{}\" side=\"{side}\" fullSz=\"{}\" width=\"{}\" gap=\"{}\" lastWidth=\"{}\"><hp:subList>",crate::HANCOM_2020_PARAGRAPH_NAMESPACE,u8::from(layout.full_size),layout.width_hwpunit,layout.gap_hwpunit,layout.last_width_hwpunit);let mut count=0usize;
    for (paragraph,id) in creation.paragraphs.iter().zip(ids){xml.push_str(&format!("<hp:p id=\"{id}\" paraPrIDRef=\"{}\" styleIDRef=\"{}\">",paragraph.paragraph_style,paragraph.named_style));for run in paragraph.runs {xml.push_str(&format!("<hp:run charPrIDRef=\"{}\">",run.character_style));for item in run.content {match *item {
        CaptionContent::Text(value)=>{let escaped=super::caption_text::escaped_expected(value,limits.config().output_bytes)?;xml.push_str("<hp:t>");xml.push_str(&escaped);xml.push_str("</hp:t>");},
        CaptionContent::Number(control)=>{let (bytes,_)=numbers::render_control(control,true)?;xml.push_str(std::str::from_utf8(&bytes).map_err(|_|E::Value)?);count=count.checked_add(1).ok_or(E::Limit)?;}
    }if xml.len()>limits.config().output_bytes{return Err(E::Limit);}}xml.push_str("</hp:run>");}xml.push_str("</hp:p>");}xml.push_str("</hp:subList></hp:caption>");if xml.len()>limits.config().output_bytes{return Err(E::Limit);}Ok((xml.into_bytes(),count))
}
