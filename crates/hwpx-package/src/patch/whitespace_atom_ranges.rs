//! Typed whitespace-only byte edits. No source/authorization/Native policy is inferred here.
use super::{ByteEdit,PatchError,PatchIntent,PatchLimits,Transaction,XmlElementSelector,escape_text};
use crate::TextAtom;
use std::{collections::{BTreeMap,BTreeSet},fmt,ops::Range};
// Unicode17 White_Space minus the six control characters excluded by the original Text reader.
fn text_space(ch:char)->bool{matches!(ch,'\u{20}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')}
#[derive(Clone,Eq,PartialEq)]
pub struct WhitespaceText(String);
impl fmt::Debug for WhitespaceText{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("WhitespaceText(<redacted>)")}}
impl WhitespaceText{
    /// # Errors
    /// Only the19 Unicode17 model-admitted whitespace characters; tab/newline need typed controls.
    pub fn new(value:&str)->Result<Self,PatchError>{
        if value.is_empty()||value.len()>PatchLimits::default().config().max_value_bytes||!value.chars().all(text_space){return Err(PatchError::ValueInvalid);}
        crate::text_flow::validate_text(value).map_err(|_|PatchError::ValueInvalid)?;Ok(Self(value.to_owned()))
    }
}
#[derive(Clone,Debug,Eq,PartialEq)]
pub enum WhitespaceOutputAtom{Text(WhitespaceText),Tab{width:u32,leader:u32,tab_type:u32},LineBreak}
#[derive(Clone,Copy,Debug,Eq,PartialEq)]
pub enum WhitespaceControlKind{Tab,LineBreak}
#[derive(Clone,Copy,Debug,Eq,PartialEq)]
enum Kind{Text,Control(WhitespaceControlKind),Empty}
#[derive(Clone,Eq,PartialEq)]
pub struct WhitespaceAtomRangeReplacement{atom:u32,start:u32,end:u32,kind:Kind,output:Vec<WhitespaceOutputAtom>}
impl fmt::Debug for WhitespaceAtomRangeReplacement{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.debug_struct("WhitespaceAtomRangeReplacement").field("atom",&self.atom).field("start",&self.start).field("end",&self.end).field("kind",&self.kind).finish_non_exhaustive()}}
impl WhitespaceAtomRangeReplacement{
    pub(super) fn output_atom_count(&self)->usize{self.output.len()}
    /// # Errors
    /// Non-empty original whitespace selection, or a whitespace insertion at a real Text boundary.
    pub fn text(atom:u32,start:u32,end:u32,output:Vec<WhitespaceOutputAtom>)->Result<Self,PatchError>{
        if start>end{return Err(PatchError::SelectorOutOfRange);}if start==end&&output.is_empty(){return Err(PatchError::ValueInvalid);}
        Ok(Self{atom,start,end,kind:Kind::Text,output})
    }
    #[must_use]
    pub fn control(atom:u32,expected:WhitespaceControlKind,output:Vec<WhitespaceOutputAtom>)->Self{Self{atom,start:0,end:1,kind:Kind::Control(expected),output}}
    /// # Errors
    /// Explicit empty TextSpan insertion; no invented Text atom coordinate is accepted.
    pub fn empty(output:Vec<WhitespaceOutputAtom>)->Result<Self,PatchError>{
        if output.is_empty(){return Err(PatchError::ValueInvalid);}Ok(Self{atom:0,start:0,end:0,kind:Kind::Empty,output})
    }
}
fn add(value:&mut usize,n:usize,cap:usize,label:&'static str)->Result<(),PatchError>{*value=value.checked_add(n).filter(|v|*v<=cap).ok_or(PatchError::LimitExceeded{limit:label})?;Ok(())}
fn escaped_size(text:&str)->Result<usize,PatchError>{text.chars().try_fold(0usize,|n,ch|n.checked_add(match ch{'&'=>5,'<'=>4,'>'=>4,'\r'=>5,_=>ch.len_utf8()}).ok_or(PatchError::AllocationFailed))}
pub(super) fn preflight(intents:&[PatchIntent],limits:PatchLimits)->Result<usize,PatchError>{
    if !intents.iter().any(|i|matches!(i,PatchIntent::ReplaceWhitespaceAtomRanges{..})){return Ok(0);}
    let cap=limits.config();let(mut ranges,mut atoms,mut old_bytes)=(0usize,0usize,0usize);let mut seen=BTreeSet::new();
    for intent in intents{
        let(target,len)=match intent{
            PatchIntent::ReplaceWhitespaceAtomRanges{target,ranges}=>{
                for pair in ranges.windows(2){let(a,b)=(&pair[0],&pair[1]);if b.atom<a.atom||b.atom==a.atom&&(b.start<a.end||b.start==a.end&&(a.start==a.end||b.start==b.end)){return Err(PatchError::Conflict);}}
                for range in ranges{add(&mut atoms,range.output.len(),cap.max_intents,"whitespace_output_atoms")?;}
                (target,ranges.len())
            },
            PatchIntent::ReplaceTextAtomScalarRanges{target,ranges}=>{for r in ranges{add(&mut old_bytes,escaped_size(r.replacement_value())?,cap.max_total_output_growth,"whitespace_joint_output_bytes")?;}(target,ranges.len())},
            PatchIntent::ReplaceLeafScalarRanges{target,ranges}=>{for r in ranges{add(&mut old_bytes,escaped_size(r.data().2)?,cap.max_total_output_growth,"whitespace_joint_output_bytes")?;}(target,ranges.len())},
            _=>continue,
        };
        if len==0{return Err(PatchError::ValueInvalid);}if !seen.insert((target.part.collision_key(),target.element_index)){return Err(PatchError::Conflict);}
        add(&mut ranges,len,cap.max_intents,"whitespace_joint_ranges")?;
    }Ok(old_bytes)
}
fn push(out:&mut String,value:&str,cap:usize)->Result<(),PatchError>{
    let _=out.len().checked_add(value.len()).filter(|n|*n<=cap).ok_or(PatchError::LimitExceeded{limit:"whitespace_output_value"})?;out.push_str(value);Ok(())
}
fn render(output:&[WhitespaceOutputAtom],prefix:&str,limits:PatchLimits)->Result<Vec<u8>,PatchError>{
    let config=limits.config();let cap=if output.iter().any(|a|!matches!(a,WhitespaceOutputAtom::Text(_))){config.max_value_bytes.min(config.max_fragment_bytes)}else{config.max_value_bytes};let mut out=String::new();
    for atom in output{match atom{
        WhitespaceOutputAtom::Text(text)=>push(&mut out,&escape_text(&text.0)?,cap)?,
        WhitespaceOutputAtom::Tab{width,leader,tab_type}=>{
            push(&mut out,"<",cap)?;push(&mut out,prefix,cap)?;push(&mut out,&format!("tab width=\"{width}\" leader=\"{leader}\" type=\"{tab_type}\"/>"),cap)?;
        },
        WhitespaceOutputAtom::LineBreak=>{push(&mut out,"<",cap)?;push(&mut out,prefix,cap)?;push(&mut out,"lineBreak/>",cap)?;},
    }}Ok(out.into_bytes())
}
impl Transaction<'_>{
    pub(super) fn plan_whitespace_atom_ranges(&self,target:&XmlElementSelector,ranges:&[WhitespaceAtomRangeReplacement],origin:usize,budget:&mut usize,edits:&mut Vec<ByteEdit>)->Result<(),PatchError>{
        let xml=self.element_context(target)?;let node=&xml.elements()[target.element_index];if node.parent().is_none(){return Err(PatchError::RootMutation);}
        let span=crate::text_flow::read_source_text_span(xml,target.element_index).map_err(|_|PatchError::FragmentInvalid)?;
        let prefix=xml.with_source_bytes(|bytes|std::str::from_utf8(&bytes[node.start_name_span().start()..node.start_name_span().end()])
            .map(|name|name.split_once(':').map_or(String::new(),|(p,_)|format!("{p}:")))).map_err(|_|PatchError::FragmentInvalid)?;
        if span.atoms.is_empty(){
            if ranges.len()!=1||ranges[0].kind!=Kind::Empty{return Err(PatchError::SelectorOutOfRange);}
            let value=render(&ranges[0].output,&prefix,self.patch_limits)?;
            let(start,end,value)=if node.is_empty(){
                let name=xml.with_source_bytes(|b|b[node.start_name_span().start()..node.start_name_span().end()].to_vec());
                let mut expanded=Vec::new();let size=value.len().checked_add(name.len()).and_then(|n|n.checked_add(4)).filter(|n|*n<=self.patch_limits.config().max_fragment_bytes).ok_or(PatchError::LimitExceeded{limit:"whitespace_empty_shell"})?;
                expanded.try_reserve_exact(size).map_err(|_|PatchError::AllocationFailed)?;expanded.push(b'>');expanded.extend_from_slice(&value);expanded.extend_from_slice(b"</");expanded.extend_from_slice(&name);expanded.push(b'>');
                let tag=node.start_tag_span();(tag.end()-2,tag.end(),expanded)
            }else{let content=node.content_span().ok_or(PatchError::FragmentInvalid)?;if content.start()!=content.end(){return Err(PatchError::FragmentInvalid);}(content.start(),content.end(),value)};
            add(budget,value.len(),self.patch_limits.config().max_total_output_growth,"whitespace_joint_output_bytes")?;edits.push(ByteEdit::new(target.part.collision_key(),start,end,value,origin));return Ok(());
        }
        let mut points:BTreeMap<u32,Vec<u32>>=BTreeMap::new();
        for range in ranges{if range.kind==Kind::Text{let p=points.entry(range.atom).or_default();for i in[range.start,range.end]{if p.last()!=Some(&i){p.push(i);}}}}
        let offsets=if points.is_empty(){BTreeMap::new()}else{super::text_atom_ranges::scalar_edges(xml,target.element_index,&points)?};
        let mut controls:BTreeMap<u32,Range<usize>>=BTreeMap::new();let mut child=node.first_child();
        for(i,atom)in span.atoms.iter().enumerate(){if matches!(atom,TextAtom::Text(_)){continue;}let at=child.ok_or(PatchError::FragmentInvalid)?;
            let control=&xml.elements()[at];let outer=control.outer_span().ok_or(PatchError::FragmentInvalid)?;
            controls.insert(u32::try_from(i).map_err(|_|PatchError::AllocationFailed)?,outer.start()..outer.end());child=control.next_sibling();}
        if child.is_some(){return Err(PatchError::FragmentInvalid);}let mut first=0;
        while first<ranges.len(){let atom=ranges[first].atom;let mut last=first+1;while last<ranges.len()&&ranges[last].atom==atom{last+=1;}
            let source=span.atoms.get(atom as usize).ok_or(PatchError::SelectorOutOfRange)?;
            if let TextAtom::Text(text)=source{
                let mut chars=text.chars();let mut consumed=0u32;
                for range in &ranges[first..last]{if range.kind!=Kind::Text{return Err(PatchError::SelectorKind);}
                    while consumed<range.end{let ch=chars.next().ok_or(PatchError::SelectorOutOfRange)?;if consumed>=range.start&&!text_space(ch){return Err(PatchError::ValueInvalid);}consumed+=1;}
                    let p=points.get(&atom).ok_or(PatchError::SelectorOutOfRange)?;let o=offsets.get(&atom).ok_or(PatchError::SelectorOutOfRange)?;
                    let start=o[p.binary_search(&range.start).map_err(|_|PatchError::SelectorOutOfRange)?];let end=o[p.binary_search(&range.end).map_err(|_|PatchError::SelectorOutOfRange)?];
                    let value=render(&range.output,&prefix,self.patch_limits)?;add(budget,value.len(),self.patch_limits.config().max_total_output_growth,"whitespace_joint_output_bytes")?;
                    edits.push(ByteEdit::new(target.part.collision_key(),start,end,value,origin));
                }
            }else{
                if last!=first+1{return Err(PatchError::Conflict);}let range=&ranges[first];let expected=match source{TextAtom::Tab{..}=>WhitespaceControlKind::Tab,TextAtom::LineBreak=>WhitespaceControlKind::LineBreak,_=>return Err(PatchError::FragmentInvalid)};
                if range.kind!=Kind::Control(expected){return Err(PatchError::SelectorKind);}let span=controls.get(&atom).ok_or(PatchError::SelectorOutOfRange)?;
                let value=render(&range.output,&prefix,self.patch_limits)?;add(budget,value.len(),self.patch_limits.config().max_total_output_growth,"whitespace_joint_output_bytes")?;
                edits.push(ByteEdit::new(target.part.collision_key(),span.start,span.end,value,origin));
            }first=last;
        }Ok(())
    }
}
