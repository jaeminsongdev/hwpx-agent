use super::*;
use crate::{ParagraphChild,TextAtom,TextFlowLimits,TextFlowReader,TextRunItem};
use domain_ir::{Flow,LogicalId,Node};
use std::collections::BTreeSet;
const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
pub(super) fn paragraphs(flow:&Flow,anchors:&mut BTreeSet<LogicalId>,maximum:usize,depth:usize)->Result<(),E> {
    if depth>128{return Err(E::Limit);}
    for node in &flow.children {match node {
        Node::Paragraph(p)=>{let anchor=p.common.source_anchor.as_ref().ok_or(E::Source)?;if !anchors.insert(anchor.opaque_handle.clone()){return Err(E::Mapping);}if anchors.len()>maximum{return Err(E::Limit);}},
        Node::Table(t)=>for c in &t.cells {paragraphs(&c.body,anchors,maximum,depth+1)?;},
        Node::Drawing(d)=>paragraphs(&d.children,anchors,maximum,depth+1)?,_=>{},
    }}Ok(())
}
pub(super) fn build(original:&ImportedDocumentStructure,limits:SourceSearchLimits)->Result<SourceTextIndex<'_>,E> {
    build_extended(original,limits,None)
}
pub(super) fn build_extended<'a>(original:&'a ImportedDocumentStructure,limits:SourceSearchLimits,
    review:Option<&reviews::ReviewProjection>)->Result<SourceTextIndex<'a>,E> {
    let cap=limits.0;let mut wanted=BTreeSet::new();let graph=original.graph();
    for s in graph.sections() {paragraphs(&s.body,&mut wanted,cap.paragraphs,0)?;}
    for n in graph.notes() {paragraphs(&n.body,&mut wanted,cap.paragraphs,0)?;}
    if let Some(review)=review {for id in review.regions.keys() {
        if !wanted.insert(id.clone()){return Err(E::Mapping);}if wanted.len()>cap.paragraphs{return Err(E::Limit);}
    }}
    let mut index=SourceTextIndex {original,limits,segments:Vec::new(),points:Vec::new(),usage:Vec::new(),blocks:Vec::new(),
        receipt:SourceSearchIndexReceipt {profile:if review.is_some(){reviews::REVIEW_TEXT_INDEX_PROFILE}else{SOURCE_SEARCH_PROFILE},source_package_sha256:original.receipt().source_package_sha256,
            graph_sha256:original.receipt().graph_sha256,index_sha256:[0;32],normalization_unicode_version:unicode_normalization::UNICODE_VERSION,
            paragraphs:0,blocks:0,text_elements:0,original_scalars:0,normalized_scalars:0,decomposed_scalars:0,control_or_opaque_barriers:0,
            skipped_unmapped_source_paragraphs:0,source_opaque_nodes:original.receipt().opaque_nodes,
            whole_document_visibility_and_search_qualified:false,edit_or_service_access_authority:false}};
    for path in original.source().spine() {
        let part=original.source().parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
        for (i,node) in xml.elements().iter().enumerate().filter(|(_,n)|n.name().namespace()==Some(HP)&&n.name().local_name()=="p") {
            let anchor=part.element_anchor(i).ok_or(E::Source)?;
            if !wanted.remove(&anchor.opaque_handle){index.receipt.skipped_unmapped_source_paragraphs+=1;continue;}
            index.receipt.paragraphs+=1;
            let flow=TextFlowReader::read_preserving_xml_context(xml,i,TextFlowLimits::default()).map_err(|_|E::Source)?;
            let mut run_index=node.first_child();let mut units=Vec::new();
            for child in flow.children {
                let ri=run_index.ok_or(E::Mapping)?;run_index=xml.elements()[ri].next_sibling();
                let ParagraphChild::Run(run)=child else{flush(&mut index,anchor,&mut units)?;index.receipt.control_or_opaque_barriers+=1;continue};
                let mut text_index=xml.elements()[ri].first_child();
                for item in run.items {
                    let ti=text_index.ok_or(E::Mapping)?;text_index=xml.elements()[ti].next_sibling();
                    let TextRunItem::Text(span)=item else{flush(&mut index,anchor,&mut units)?;index.receipt.control_or_opaque_barriers+=1;continue};
                    if index.segments.len()>=cap.segments{return Err(E::Limit);}
                    let segment=index.segments.len();index.segments.push(part.element_anchor(ti).ok_or(E::Source)?.clone());
                    for (atom_index,atom) in span.atoms.into_iter().enumerate() {
                        let text=match atom {TextAtom::Text(s)=>s,TextAtom::Tab {..}=>"\t".into(),TextAtom::LineBreak=>"\n".into()};
                        for (scalar,ch) in text.chars().enumerate() {
                            if index.points.len()>=cap.scalars{return Err(E::Limit);}
                            let origin=index.points.len();index.points.push(Point {segment,atom:u32::try_from(atom_index).map_err(|_|E::Limit)?,scalar:u32::try_from(scalar).map_err(|_|E::Limit)?});
                            index.usage.push((usize::MAX,0));units.push(Unit {ch,origins:vec![origin]});
                        }
                    }
                }
                if text_index.is_some(){return Err(E::Mapping);}
            }
            if run_index.is_some(){return Err(E::Mapping);}
            if units.is_empty()&&index.blocks.last().is_none_or(|b|&b.paragraph!=anchor) {
                if index.blocks.len()>=cap.blocks{return Err(E::Limit);}
                index.blocks.push(Block {paragraph:anchor.clone(),text:String::new(),offsets:vec![0],units:Vec::new()});
            }else{flush(&mut index,anchor,&mut units)?;}
        }
    }
    if !wanted.is_empty(){return Err(E::Mapping);}
    if review.is_some(){reviews::order_source_blocks(&mut index)?;}
    index.receipt.blocks=index.blocks.len();index.receipt.text_elements=index.segments.len();index.receipt.original_scalars=index.points.len();
    let mut hash=Sha256::new();hash.update(index.receipt.profile.as_bytes());hash.update(index.receipt.source_package_sha256);hash.update(index.receipt.graph_sha256);
    if let Some(review)=review {hash.update(review.binding_sha256(limits.0.result_bytes)?);}
    let(v1,v2,v3)=index.receipt.normalization_unicode_version;hash.update([v1,v2,v3]);
    for block in &index.blocks {hash.update((block.text.len()as u64).to_le_bytes());hash.update(block.text.as_bytes());
        for unit in &block.units {hash.update((unit.origins.len()as u64).to_le_bytes());for &origin in &unit.origins {hash.update((origin as u64).to_le_bytes());}}
    }
    index.receipt.index_sha256=hash.finalize().into();Ok(index)
}
fn flush(index:&mut SourceTextIndex<'_>,paragraph:&SourceAnchorHandle,units:&mut Vec<Unit>)->Result<(),E> {
    if units.is_empty(){return Ok(());}let cap=index.limits.0;
    if index.blocks.len()>=cap.blocks{return Err(E::Limit);}
    let remaining=cap.decomposed_scalars.checked_sub(index.receipt.decomposed_scalars).ok_or(E::Limit)?;
    let(normalized,count)=normalization::nfc(std::mem::take(units),remaining)?;index.receipt.decomposed_scalars+=count;
    index.receipt.normalized_scalars=index.receipt.normalized_scalars.checked_add(normalized.len()).filter(|n|*n<=cap.decomposed_scalars).ok_or(E::Limit)?;
    let mut text=String::new();let mut offsets=Vec::new();
    for (i,u) in normalized.iter().enumerate() {offsets.push(text.len());text.push(u.ch);
        for &origin in &u.origins {let usage=&mut index.usage[origin];usage.0=usage.0.min(i);usage.1=usage.1.max(i);}
    }offsets.push(text.len());
    index.blocks.push(Block {paragraph:paragraph.clone(),text,offsets,units:normalized});Ok(())
}
