//! Exact inverse NFC cuts, built once per selected block rather than scanning every prefix per hit.
use super::*;
use crate::document_import::search::{Point,SourceSearchResult};

#[derive(Clone,Copy,Debug,Eq,PartialEq,serde::Deserialize,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceRegexInsertionPolicy {RightOriginalPointElseLeftFirstEmptyText}

#[derive(Clone,Copy)]
pub(in crate::document_import::search::replacement::atoms) enum Caret {Point {point:Point,after:bool},Empty {segment:usize}}
impl Caret {pub(in crate::document_import::search::replacement::atoms) fn segment(self)->usize {match self {Self::Point {point,..}=>point.segment,Self::Empty {segment}=>segment}}}
pub(in crate::document_import::search::replacement::atoms) struct Insertions {pub(in crate::document_import::search::replacement::atoms) carets:BTreeMap<usize,Caret>,pub(in crate::document_import::search::replacement::atoms) sha256:[u8;32]}
#[derive(Serialize)]
struct BoundCaret<'a> {ordinal:usize,block:usize,cut:usize,text:&'a SourceAnchorHandle,atom:Option<u32>,scalar:Option<u32>,after:bool}

impl Insertions {
    pub(in crate::document_import::search::replacement::atoms) fn build(index:&SourceTextIndex<'_>,found:&SourceSearchResult,policy:SourceRegexInsertionPolicy)->Result<Self,E> {
        let wanted:BTreeSet<_>=found.matches().iter().filter(|m|m.zero_width).map(|m|m.block_index).collect();
        let mut cuts=BTreeMap::new();let mut empty=BTreeMap::new();
        let empty_paragraphs:BTreeSet<_>=wanted.iter().filter_map(|i|index.blocks.get(*i))
            .filter(|b|b.units.is_empty()).map(|b|b.paragraph.opaque_handle.clone()).collect();
        // Empty blocks have no original points. Only an admitted original hp:t supplies an insertion
        // owner; do not invent a run, implicit style, or a location in an opaque paragraph.
        if !empty_paragraphs.is_empty() {for (segment,anchor) in index.segments.iter().enumerate() {
            let resolved=index.original.source().resolve_anchor(anchor).map_err(|_|E::Selection)?;
            let xml=resolved.part().xml().ok_or(E::Selection)?;
            let run=resolved.element().and_then(|n|n.parent()).ok_or(E::Selection)?;
            let paragraph=xml.elements()[run].parent().ok_or(E::Selection)?;
            let handle=&resolved.part().element_anchor(paragraph).ok_or(E::Selection)?.opaque_handle;
            if empty_paragraphs.contains(handle){empty.entry(handle.clone()).or_insert(segment);}
        }}
        for block_index in wanted {
            let block=index.blocks.get(block_index).ok_or(E::Selection)?;
            let mut suffix=vec![None;block.units.len()+1];
            for i in (0..block.units.len()).rev() {suffix[i]=block.units[i].origins.iter().copied().chain(suffix[i+1]).min();}
            let mut prefix:Option<usize>=None;let mut boundaries=Vec::with_capacity(suffix.len());
            for (cut,right) in suffix.into_iter().enumerate() {
                // The prefix and suffix must be disjoint, correctly ordered contiguous original
                // contributions. Reject reordering and decomposition cuts, not just a guessed edge.
                let valid=!prefix.zip(right).is_some_and(|(a,b)|a>=b||a.checked_add(1)!=Some(b));
                let caret=if !valid {None}else if let Some(origin)=right {
                    Some(Caret::Point {point:*index.points.get(origin).ok_or(E::Selection)?,after:false})
                }else if let Some(origin)=prefix {
                    Some(Caret::Point {point:*index.points.get(origin).ok_or(E::Selection)?,after:true})
                }else{empty.get(&block.paragraph.opaque_handle).copied().map(|segment|Caret::Empty {segment})};
                boundaries.push(caret);
                if let Some(unit)=block.units.get(cut){prefix=unit.origins.iter().copied().chain(prefix).max();}
            }
            cuts.insert(block_index,boundaries);
        }
        let mut carets=BTreeMap::new();let mut bound=Vec::new();
        for (ordinal,m) in found.matches().iter().enumerate().filter(|(_,m)|m.zero_width) {
            if m.start_normalized_scalar!=m.end_normalized_scalar||!m.pieces.is_empty(){return Err(E::Selection);}
            let block=index.blocks.get(m.block_index).ok_or(E::Selection)?;
            if block.paragraph!=m.paragraph_anchor{return Err(E::Selection);}
            let caret=cuts.get(&m.block_index).and_then(|c|c.get(m.start_normalized_scalar)).copied().flatten().ok_or(E::Selection)?;
            let(atom,scalar,after)=match caret {Caret::Point {point,after}=>(Some(point.atom),Some(point.scalar),after),Caret::Empty {..}=>(None,None,false)};
            bound.push(BoundCaret {ordinal,block:m.block_index,cut:m.start_normalized_scalar,text:&index.segments[caret.segment()],atom,scalar,after});
            carets.insert(ordinal,caret);
        }
        let mut output=Output {bytes:Some(Vec::new()),length:0,maximum:index.limits.0.result_bytes};
        serde_json::to_writer(&mut output,&("hwpx-agent.regex-original-insertions/v1",policy,index.receipt.index_sha256,bound)).map_err(|_|E::Limit)?;
        let sha256=Sha256::digest(output.bytes.ok_or(E::Limit)?).into();Ok(Self {carets,sha256})
    }
}

/// Merge sorted original atom edges and inserted text in a single pass. Repeated Vec::insert
/// would move the remaining atom array for each zero-width match (quadratic on control-only text).
/// This is called only by explicit v2; the original None/v1 compiler path is untouched.
pub(in crate::document_import::search::replacement::atoms) fn materialize(span:&mut TextSpan,additions:Vec<(usize,String)>,maximum:usize)->Result<(),E> {
    let length=span.atoms.len();let mut original=std::mem::take(&mut span.atoms).into_iter();
    let mut additions=additions.into_iter().peekable();let mut merged:Vec<TextAtom>=Vec::new();
    let push=|merged:&mut Vec<TextAtom>,atom:TextAtom|->Result<(),E> {match atom {
        TextAtom::Text(value)=>if let Some(TextAtom::Text(previous))=merged.last_mut(){append(previous,&value,maximum)?;}else{merged.push(TextAtom::Text(value));},
        atom=>merged.push(atom),
    }Ok(())};
    for boundary in 0..=length {
        if additions.peek().is_some_and(|(at,_)|*at<boundary){return Err(E::Selection);}
        while additions.peek().is_some_and(|(at,_)|*at==boundary) {
            let(_,value)=additions.next().ok_or(E::Selection)?;push(&mut merged,TextAtom::Text(value))?;
        }
        if let Some(atom)=original.next(){push(&mut merged,atom)?;}
    }
    if additions.next().is_some(){return Err(E::Selection);}span.atoms=merged;Ok(())
}
