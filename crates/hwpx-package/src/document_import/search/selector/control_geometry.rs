//! Exact lexical control-start membership; NFC scalar coordinates never become guessed byte edits.
use super::*;
use crate::{PreservingXmlDocument,TextAtom};

/// A scalar edge inside an original lexical atom. There are no XML elements inside a text atom;
/// scalar edges distinguish before/after a tab or lineBreak without decoding XML a second way.
#[derive(Clone,Copy,Eq,PartialEq,Ord,PartialOrd)]
pub(in crate::document_import::search) struct Position {part:usize,atom_start:usize,scalar_edge:u64}
pub(in crate::document_import::search) enum ControlGeometry {
    All,Parts(BTreeSet<String>),Nodes(BTreeMap<String,Vec<(usize,usize)>>),
    Selection {parts:BTreeMap<String,usize>,start:Position,end:Position},
}
impl ControlGeometry {
    /// Whole original outer range, not the start-only discovery predicate.
    pub(in crate::document_import::search) fn contains_whole(&self,index:&SourceTextIndex<'_>,anchor:&SourceAnchorHandle)->Result<bool,E> {
        let resolved=index.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;
        let outer=resolved.element().and_then(|n|n.outer_span()).ok_or(E::Mapping)?;let path=resolved.part().path().as_str();
        Ok(match self {
            Self::All=>true,Self::Parts(parts)=>parts.contains(path),
            Self::Nodes(parts)=>parts.get(path).is_some_and(|ranges|{let n=ranges.partition_point(|(a,_)|*a<=outer.start());n>0&&outer.end()<=ranges[n-1].1}),
            Self::Selection {parts,start,end}=>{let part=*parts.get(path).ok_or(E::Mapping)?;
                *start<=Position{part,atom_start:outer.start(),scalar_edge:0}&&Position{part,atom_start:outer.end(),scalar_edge:0}<=*end},
        })
    }
    pub(super) fn selection(index:&SourceTextIndex<'_>,start:&SourceIndexBoundary,end:&SourceIndexBoundary)->Result<Self,E> {
        let parts=index.original.source().spine().iter().enumerate().map(|(i,p)|(p.as_str().to_owned(),i)).collect();
        // At most two original text elements are read, once each, for the two endpoint projections.
        let mut atoms=BTreeMap::new();
        let a=boundary(index,start,&parts,&mut atoms)?;let b=boundary(index,end,&parts,&mut atoms)?;
        if a>b{return Err(E::Scope);}Ok(Self::Selection {parts,start:a,end:b})
    }
    pub(in crate::document_import::search) fn contains(&self,index:&SourceTextIndex<'_>,anchor:&SourceAnchorHandle)->Result<bool,E> {
        let resolved=index.original.source().resolve_anchor(anchor).map_err(|_|E::Source)?;
        let element=resolved.element().ok_or(E::Mapping)?;let path=resolved.part().path().as_str();let at=element.start_tag_span().start();
        Ok(match self {
            Self::All=>true,Self::Parts(parts)=>parts.contains(path),
            Self::Nodes(parts)=>parts.get(path).is_some_and(|ranges|{let n=ranges.partition_point(|(a,_)|*a<=at);n>0&&at<ranges[n-1].1}),
            Self::Selection {parts,start,end}=>{let point=Position {part:*parts.get(path).ok_or(E::Mapping)?,atom_start:at,scalar_edge:0};*start<=point&&point<*end},
        })
    }
}
fn boundary(index:&SourceTextIndex<'_>,boundary:&SourceIndexBoundary,parts:&BTreeMap<String,usize>,cache:&mut BTreeMap<usize,Vec<usize>>)->Result<Position,E> {
    let block=&index.blocks[boundary.block_index];let cut=boundary.normalized_scalar;
    let before=block.units[..cut].iter().flat_map(|u|u.origins.iter().copied()).max();
    let after=block.units[cut..].iter().flat_map(|u|u.origins.iter().copied()).min();
    // A legal text selection need not be a contiguous original prefix after NFC reordering.
    // Such an endpoint cannot locate intervening structural controls and must not be widened.
    if before.zip(after).is_some_and(|(a,b)|a>=b){return Err(E::Scope);}
    let Some(origin)=before.or(after) else {
        let resolved=index.original.source().resolve_anchor(&block.paragraph).map_err(|_|E::Source)?;
        return Ok(Position {part:*parts.get(resolved.part().path().as_str()).ok_or(E::Mapping)?,
            atom_start:resolved.element().ok_or(E::Mapping)?.start_tag_span().end(),scalar_edge:0});
    };
    let point=&index.points[origin];let resolved=index.original.source().resolve_anchor(&index.segments[point.segment]).map_err(|_|E::Source)?;
    if let std::collections::btree_map::Entry::Vacant(entry)=cache.entry(point.segment) {
        let xml=resolved.part().xml().ok_or(E::Source)?;let element=resolved.element_index().ok_or(E::Mapping)?;
        let span=crate::text_flow::read_source_text_span(xml,element).map_err(|_|E::Mapping)?;
        entry.insert(atom_starts(xml,element,&span.atoms)?);
    }
    let start=*cache.get(&point.segment).and_then(|a|a.get(point.atom as usize)).ok_or(E::Mapping)?;
    Ok(Position {part:*parts.get(resolved.part().path().as_str()).ok_or(E::Mapping)?,atom_start:start,
        scalar_edge:u64::from(point.scalar)*2+u64::from(before.is_some())})
}
fn atom_starts(xml:&PreservingXmlDocument,index:usize,atoms:&[TextAtom])->Result<Vec<usize>,E> {
    let node=&xml.elements()[index];let end=node.end_token().ok_or(E::Mapping)?;
    let mut inventory=Vec::new();let mut next=node.start_token()+1;let mut child=node.first_child();
    while let Some(i)=child {let element=&xml.elements()[i];
        if next<element.start_token(){inventory.push((xml.tokens()[next].span().start(),true));}
        inventory.push((element.start_tag_span().start(),false));
        next=element.end_token().map_or(element.start_token()+1,|last|last+1);child=element.next_sibling();
    }
    if next<end{inventory.push((xml.tokens()[next].span().start(),true));}
    if inventory.len()!=atoms.len()||inventory.iter().zip(atoms).any(|((_,text),atom)|*text!=matches!(atom,TextAtom::Text(_))){return Err(E::Mapping);}
    Ok(inventory.into_iter().map(|(start,_)|start).collect())
}
