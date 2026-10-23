//! Shared exact source-range planning; the transaction retains original overlap,
//! source identity, namespace, ID-index, preservation and writer validation.
use super::{ElementSplicePosition as Position,PatchError as E,PatchLimits,ValidatedXmlFragment};
use crate::PreservingXmlDocument;
pub(crate) struct SourceSplice {
    pub start:usize,pub end:usize,pub replacement:Vec<u8>,pub fragment_offset:usize,
}
pub(crate) fn source_edit(xml:&PreservingXmlDocument,index:usize,position:Position,
    fragments:&[ValidatedXmlFragment],limits:PatchLimits)->Result<SourceSplice,E> {
    let node=xml.elements().get(index).ok_or(E::SelectorOutOfRange)?;
    if fragments.len()>limits.config().max_intents{return Err(E::LimitExceeded {limit:"splice_fragments"});}
    if fragments.is_empty()&&position!=Position::Subtree{return Err(E::ValueInvalid);}
    if node.parent().is_none()&&matches!(position,Position::Before|Position::After){return Err(E::RootMutation);}
    if node.parent().is_none()&&position==Position::Subtree&&fragments.len()!=1{return Err(E::RootMutation);}
    let mut size=0usize;
    for fragment in fragments {
        size=size.checked_add(fragment.bytes.len()).filter(|v|*v<=limits.config().max_fragment_bytes).ok_or(E::LimitExceeded {limit:"splice_fragment_bytes"})?;
    }
    let outer=node.outer_span().ok_or(E::SelectorStale)?;
    let (start,end,empty_child)=match position {
        Position::Before=>(outer.start(),outer.start(),false),Position::After=>(outer.end(),outer.end(),false),
        Position::Subtree=>(outer.start(),outer.end(),false),
        Position::FirstChild|Position::LastChild if node.is_empty()=>
            (node.start_tag_span().end().checked_sub(2).ok_or(E::SelectorStale)?,node.start_tag_span().end(),true),
        Position::FirstChild=>{let s=node.content_span().ok_or(E::SelectorStale)?;(s.start(),s.start(),false)},
        Position::LastChild=>{let s=node.content_span().ok_or(E::SelectorStale)?;(s.end(),s.end(),false)},
    };
    let name=if empty_child{Some(xml.source_text(node.start_name_span()).map_err(|_|E::SelectorStale)?)}else{None};
    let extra=name.map_or(0,|s|s.len()+4);
    let capacity=size.checked_add(extra).ok_or(E::AllocationFailed)?;
    let mut bytes=Vec::new();bytes.try_reserve_exact(capacity).map_err(|_|E::AllocationFailed)?;
    if empty_child{bytes.push(b'>');}
    for fragment in fragments{bytes.extend_from_slice(&fragment.bytes);}
    if let Some(name)=name{bytes.extend_from_slice(b"</");bytes.extend_from_slice(name.as_bytes());bytes.push(b'>');}
    Ok(SourceSplice {start,end,replacement:bytes,fragment_offset:usize::from(empty_child)})
}
