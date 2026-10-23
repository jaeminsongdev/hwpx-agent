//! Preserve all original leaf bytes outside decoded-scalar selections in one bounded scan.
use super::{ByteEdit,PatchError,PatchIntent,PatchLimits,PatchText,PreservingXmlDocument,Transaction,XmlElementSelector,XmlTokenKind,escape_text};
use std::fmt;
#[derive(Clone,Eq,PartialEq)]
pub struct LeafTextRangeReplacement {start:u32,end:u32,value:PatchText}
impl fmt::Debug for LeafTextRangeReplacement {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {
    f.debug_struct("LeafTextRangeReplacement").field("start_scalar",&self.start).field("end_scalar",&self.end).finish_non_exhaustive()}}
impl LeafTextRangeReplacement {
    pub(super) fn data(&self)->(u32,u32,&str) {(self.start,self.end,self.value.value())}
    /// # Errors
    /// Validates a half-open decoded-scalar range and XML 1.0 semantic text.
    /// Source existence, ordering and current transaction limits are checked at apply.
    pub fn new(start_scalar:u32,end_scalar:u32,replacement:&str)->Result<Self,PatchError> {
        if start_scalar>end_scalar{return Err(PatchError::SelectorOutOfRange);}
        Ok(Self {start:start_scalar,end:end_scalar,value:PatchText::new(replacement)?})
    }
}
pub(super) fn preflight(intents:&[PatchIntent],limits:PatchLimits)->Result<(),PatchError> {
    let cap=limits.config();let(mut count,mut bytes)=(0_usize,0_usize);
    let mut seen=std::collections::BTreeSet::new();
    for intent in intents {if let PatchIntent::ReplaceLeafScalarRanges {target,ranges}=intent {
        if !seen.insert((target.part.collision_key(),target.element_index)){return Err(PatchError::Conflict);}
        if ranges.is_empty(){return Err(PatchError::ValueInvalid);}
        count=count.checked_add(ranges.len()).filter(|n|*n<=cap.max_intents).ok_or(PatchError::LimitExceeded {limit:"leaf_scalar_ranges"})?;
        for range in ranges {
            if range.value.value().len()>cap.max_value_bytes{return Err(PatchError::LimitExceeded {limit:"value_bytes"});}
            for ch in range.value.value().chars() {
                bytes=bytes.checked_add(match ch {'&'=>5,'<'=>4,'>'=>4,'\r'=>5,_=>ch.len_utf8()})
                    .filter(|n|*n<=cap.max_total_output_growth).ok_or(PatchError::LimitExceeded {limit:"leaf_scalar_escaped_bytes"})?;
            }
        }
        for pair in ranges.windows(2) {let(a,b)=(&pair[0],&pair[1]);
            if b.start<a.end||b.start==a.end&&(a.start==a.end||b.start==b.end){return Err(PatchError::Conflict);}}
    }}Ok(())
}
impl Transaction<'_> {
    pub(super) fn plan_leaf_scalar_ranges(&self,target:&XmlElementSelector,ranges:&[LeafTextRangeReplacement],origin:usize,edits:&mut Vec<ByteEdit>)->Result<(),PatchError> {
        let xml=self.element_context(target)?;let node=&xml.elements()[target.element_index];
        if node.parent().is_none(){return Err(PatchError::RootMutation);}
        if node.first_child().is_some(){return Err(PatchError::FragmentInvalid);}
        if node.is_empty() {
            if ranges.len()!=1||ranges[0].start!=0||ranges[0].end!=0{return Err(PatchError::SelectorOutOfRange);}
            return self.plan_leaf_text_edit(target,&ranges[0].value,origin,edits);
        }
        let mut points=Vec::new();points.try_reserve_exact(ranges.len().checked_mul(2).ok_or(PatchError::AllocationFailed)?)
            .map_err(|_|PatchError::AllocationFailed)?;
        // Preflight already requires ordered disjoint ranges; retain unique
        // endpoints linearly instead of sorting the same metadata again.
        for range in ranges {for point in [range.start,range.end] {if points.last()!=Some(&point){points.push(point);}}}
        let offsets=source_boundaries(xml,target.element_index,&points)?;
        let mut total=0_usize;
        for range in ranges {
            let start=offsets[points.binary_search(&range.start).map_err(|_|PatchError::SelectorOutOfRange)?];
            let end=offsets[points.binary_search(&range.end).map_err(|_|PatchError::SelectorOutOfRange)?];
            let escaped=escape_text(range.value.value())?;let escaped=if escaped.contains('\r'){escaped.replace('\r',"&#13;")}else{escaped};
            total=total.checked_add(escaped.len()).filter(|n|*n<=self.patch_limits.config().max_total_output_growth)
                .ok_or(PatchError::LimitExceeded {limit:"leaf_scalar_escaped_bytes"})?;
            edits.push(ByteEdit::new(target.part.collision_key(),start,end,escaped.into_bytes(),origin));
        }Ok(())
    }
}
// Only requested boundaries are stored. Adjacent ranges share one source scan;
// scalar counts follow XML literal CR/CRLF normalization, while references each
// retain their exact original byte span and one decoded Unicode scalar.
fn source_boundaries(xml:&PreservingXmlDocument,index:usize,points:&[u32])->Result<Vec<usize>,PatchError> {
    let node=&xml.elements()[index];let content=node.content_span().ok_or(PatchError::SelectorStale)?;
    token_boundaries(xml,index,node.start_token()+1..node.end_token().ok_or(PatchError::SelectorStale)?,content.end(),points)
}
pub(super) fn token_boundaries(xml:&PreservingXmlDocument,index:usize,tokens:std::ops::Range<usize>,content_end:usize,points:&[u32])->Result<Vec<usize>,PatchError> {
    let mut offsets=Vec::new();offsets.try_reserve_exact(points.len()).map_err(|_|PatchError::AllocationFailed)?;
    let mut scalar=0_u32;
    let record=|offsets:&mut Vec<usize>,scalar:u32,at:usize| {if points.get(offsets.len())==Some(&scalar){offsets.push(at);}};
    for token in xml.tokens().get(tokens).ok_or(PatchError::SelectorStale)? {
        if token.element_index()!=Some(index)||!matches!(token.kind(),XmlTokenKind::Text|XmlTokenKind::Whitespace|XmlTokenKind::Reference) {
            return Err(PatchError::FragmentInvalid);
        }
        let raw=xml.source_text(token.span()).map_err(|_|PatchError::SelectorStale)?;
        if token.kind()==XmlTokenKind::Reference {
            let decoded=quick_xml::escape::unescape(raw).map_err(|_|PatchError::ValueInvalid)?;
            if decoded.chars().count()!=1{return Err(PatchError::ValueInvalid);}
            record(&mut offsets,scalar,token.span().start());scalar=scalar.checked_add(1).ok_or(PatchError::SelectorOutOfRange)?;
        }else{
            let mut chars=raw.char_indices().peekable();
            while let Some((at,ch))=chars.next() {
                record(&mut offsets,scalar,token.span().start()+at);
                if ch=='\r'&&chars.peek().is_some_and(|(_,c)|*c=='\n'){chars.next();}
                scalar=scalar.checked_add(1).ok_or(PatchError::SelectorOutOfRange)?;
            }
        }
    }
    record(&mut offsets,scalar,content_end);
    if offsets.len()!=points.len(){return Err(PatchError::SelectorOutOfRange);}Ok(offsets)
}
