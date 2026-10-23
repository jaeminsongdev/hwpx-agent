//! Bounded source-atom edits; controls never become text or editable byte ranges.
use super::{ByteEdit,LeafTextRangeReplacement,PatchError,PatchIntent,PatchLimits,Transaction,XmlElementSelector,escape_text};
use crate::{PreservingXmlDocument,TextAtom};
use std::{collections::BTreeSet,fmt,ops::Range};

#[derive(Clone,Eq,PartialEq)]
pub struct TextAtomRangeReplacement {atom:u32,range:LeafTextRangeReplacement,boundary:bool}
impl fmt::Debug for TextAtomRangeReplacement {
    fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
        f.debug_struct("TextAtomRangeReplacement").field("source_atom",&self.atom).field("range",&self.range).field("control_boundary",&self.boundary).finish_non_exhaustive()
    }
}
impl TextAtomRangeReplacement {
    pub(super) fn replacement_value(&self)->&str{self.range.data().2}
    /// # Errors
    /// Coordinates address one original TextSpan Text atom, never a control atom.
    /// Values obey the existing HWPX text policy; tabs/newlines need a distinct operation.
    pub fn new(source_atom:u32,start_scalar:u32,end_scalar:u32,replacement:&str)->Result<Self,PatchError> {
        crate::text_flow::validate_text(replacement).map_err(|_|PatchError::ValueInvalid)?;
        Ok(Self {atom:source_atom,range:LeafTextRangeReplacement::new(start_scalar,end_scalar,replacement)?,boundary:false})
    }
    /// # Errors
    /// Insert immediately before an original control atom, or after the last control.
    /// This never edits a control or creates a synthetic Text atom coordinate.
    /// Existence and control adjacency are checked against the original qualified reader.
    pub fn at_control_boundary(source_atom_boundary:u32,replacement:&str)->Result<Self,PatchError> {
        crate::text_flow::validate_text(replacement).map_err(|_|PatchError::ValueInvalid)?;
        Ok(Self {atom:source_atom_boundary,range:LeafTextRangeReplacement::new(0,0,replacement)?,boundary:true})
    }
}

pub(super) fn preflight(intents:&[PatchIntent],limits:PatchLimits)->Result<(),PatchError> {
    if !intents.iter().any(|i|matches!(i,PatchIntent::ReplaceTextAtomScalarRanges {..})){return Ok(());}
    let cap=limits.config();let(mut count,mut escaped_bytes)=(0_usize,0_usize);let mut seen=BTreeSet::new();
    for intent in intents {
        let(target,len)=match intent {
            PatchIntent::ReplaceTextAtomScalarRanges {target,ranges}=>{
                for pair in ranges.windows(2) {
                    let(a,b)=(&pair[0],&pair[1]);let(astart,aend,_)=a.range.data();let(bstart,_,_)=b.range.data();
                    if b.atom<a.atom||b.atom==a.atom&&(bstart<aend||bstart==aend&&(astart==aend||b.range.data().0==b.range.data().1)){
                        return Err(PatchError::Conflict);
                    }
                }
                (target,ranges.len())
            },
            PatchIntent::ReplaceLeafScalarRanges {target,ranges}=>(target,ranges.len()),
            _=>continue,
        };
        if len==0{return Err(PatchError::ValueInvalid);}
        if !seen.insert((target.part.collision_key(),target.element_index)){return Err(PatchError::Conflict);}
        count=count.checked_add(len).filter(|n|*n<=cap.max_intents).ok_or(PatchError::LimitExceeded {limit:"text_atom_scalar_ranges"})?;
        // Include both range-intent families: splitting a budget across types is not an escape.
        for i in 0..len {
            let value=match intent {
                PatchIntent::ReplaceTextAtomScalarRanges {ranges,..}=>ranges[i].range.data().2,
                PatchIntent::ReplaceLeafScalarRanges {ranges,..}=>ranges[i].data().2,
                _=>unreachable!(),
            };
            if value.len()>cap.max_value_bytes{return Err(PatchError::LimitExceeded {limit:"value_bytes"});}
            for ch in value.chars() {
                escaped_bytes=escaped_bytes.checked_add(match ch {'&'=>5,'<'=>4,'>'=>4,'\r'=>5,_=>ch.len_utf8()})
                    .filter(|n|*n<=cap.max_total_output_growth).ok_or(PatchError::LimitExceeded {limit:"text_atom_escaped_bytes"})?;
            }
        }
    }Ok(())
}

/// Original reader qualifies controls/attributes and merges adjacent entity/text tokens.
/// This parallel lexical inventory uses that same atom order; it never decodes controls.
fn source_atoms(xml:&PreservingXmlDocument,index:usize,atoms:&[TextAtom])->Result<Vec<Option<Range<usize>>>,PatchError> {
    let node=&xml.elements()[index];let end=node.end_token().ok_or(PatchError::FragmentInvalid)?;
    let mut ranges=Vec::new();let mut next=node.start_token()+1;let mut child=node.first_child();
    while let Some(i)=child {
        let control=&xml.elements()[i];
        if next<control.start_token(){ranges.push(Some(next..control.start_token()));}
        ranges.push(None);
        next=control.end_token().map_or(control.start_token()+1,|last|last+1);
        child=control.next_sibling();
    }
    if next<end{ranges.push(Some(next..end));}
    if ranges.len()!=atoms.len()||ranges.iter().zip(atoms).any(|(r,a)|r.is_some()!=matches!(a,TextAtom::Text(_))){return Err(PatchError::FragmentInvalid);}
    Ok(ranges)
}

impl Transaction<'_> {
    pub(super) fn plan_text_atom_scalar_ranges(&self,target:&XmlElementSelector,ranges:&[TextAtomRangeReplacement],origin:usize,edits:&mut Vec<ByteEdit>)->Result<(),PatchError> {
        let xml=self.element_context(target)?;let node=&xml.elements()[target.element_index];
        if node.parent().is_none(){return Err(PatchError::RootMutation);}
        let span=crate::text_flow::read_source_text_span(xml,target.element_index).map_err(|_|PatchError::FragmentInvalid)?;
        let sources=source_atoms(xml,target.element_index,&span.atoms)?;
        let mut control_edges=Vec::new();
        if ranges.iter().any(|r|r.boundary) {
            let mut child=node.first_child();
            for atom in &span.atoms {
                if matches!(atom,TextAtom::Text(_)){control_edges.push(None);continue;}
                let i=child.ok_or(PatchError::FragmentInvalid)?;let element=&xml.elements()[i];
                control_edges.push(Some(element.outer_span().ok_or(PatchError::FragmentInvalid)?));child=element.next_sibling();
            }
            if child.is_some(){return Err(PatchError::FragmentInvalid);}
        }
        let mut first=0;
        while first<ranges.len() {
            let atom=ranges[first].atom;let mut last=first+1;
            while last<ranges.len()&&ranges[last].atom==atom{last+=1;}
            if ranges[first].boundary {
                if last!=first+1{return Err(PatchError::Conflict);}
                let ordinal=atom as usize;
                let control=if ordinal==span.atoms.len() {
                    ordinal.checked_sub(1).filter(|i|!matches!(span.atoms[*i],TextAtom::Text(_)))
                }else{Some(ordinal).filter(|i|span.atoms.get(*i).is_some_and(|a|!matches!(a,TextAtom::Text(_))))}.ok_or(PatchError::SelectorOutOfRange)?;
                let edge=control_edges.get(control).and_then(Option::as_ref).ok_or(PatchError::FragmentInvalid)?;
                let at=if ordinal==span.atoms.len(){edge.end()}else{edge.start()};
                edits.push(ByteEdit::new(target.part.collision_key(),at,at,escape_text(ranges[first].range.data().2)?.into_bytes(),origin));
                first=last;continue;
            }
            if ranges[first..last].iter().any(|r|r.boundary){return Err(PatchError::Conflict);}
            let tokens=sources.get(atom as usize).and_then(Option::as_ref).ok_or(PatchError::SelectorOutOfRange)?;
            let TextAtom::Text(value)=span.atoms.get(atom as usize).ok_or(PatchError::SelectorOutOfRange)? else{return Err(PatchError::FragmentInvalid);};
            let scalars=value.chars().count();
            if ranges[last-1].range.data().1 as usize>scalars{return Err(PatchError::SelectorOutOfRange);}
            let mut points=Vec::new();points.try_reserve_exact((last-first).checked_mul(2).ok_or(PatchError::AllocationFailed)?)
                .map_err(|_|PatchError::AllocationFailed)?;
            for range in &ranges[first..last] {let(start,end,_)=range.range.data();
                for point in [start,end] {if points.last()!=Some(&point){points.push(point);}}}
            let end=xml.tokens().get(tokens.end-1).ok_or(PatchError::SelectorStale)?.span().end();
            let offsets=super::leaf_scalar_ranges::token_boundaries(xml,target.element_index,tokens.clone(),end,&points)?;
            for range in &ranges[first..last] {
                let(start,end,value)=range.range.data();
                let start=offsets[points.binary_search(&start).map_err(|_|PatchError::SelectorOutOfRange)?];
                let end=offsets[points.binary_search(&end).map_err(|_|PatchError::SelectorOutOfRange)?];
                edits.push(ByteEdit::new(target.part.collision_key(),start,end,escape_text(value)?.into_bytes(),origin));
            }
            first=last;
        }Ok(())
    }
}

/// Requested original scalar edges, sharing the original qualified atom inventory and XML token
/// scanner. No caller byte offsets or control-content decoding; one scan per requested Text atom.
pub(crate) fn scalar_edges(xml:&PreservingXmlDocument,index:usize,requested:&std::collections::BTreeMap<u32,Vec<u32>>)->Result<std::collections::BTreeMap<u32,Vec<usize>>,PatchError> {
    let span=crate::text_flow::read_source_text_span(xml,index).map_err(|_|PatchError::FragmentInvalid)?;
    let sources=source_atoms(xml,index,&span.atoms)?;let mut result=std::collections::BTreeMap::new();
    for(&atom,points)in requested {
        if points.is_empty()||points.windows(2).any(|w|w[0]>=w[1]){return Err(PatchError::SelectorOutOfRange);}
        let Some(TextAtom::Text(value))=span.atoms.get(atom as usize)else{return Err(PatchError::FragmentInvalid)};
        if points.last().copied().unwrap_or(0)as usize>value.chars().count(){return Err(PatchError::SelectorOutOfRange);}
        let tokens=sources.get(atom as usize).and_then(Option::as_ref).ok_or(PatchError::FragmentInvalid)?;
        let end=xml.tokens()[tokens.end-1].span().end();
        result.insert(atom,super::leaf_scalar_ranges::token_boundaries(xml,index,tokens.clone(),end,points)?);
    }Ok(result)
}
