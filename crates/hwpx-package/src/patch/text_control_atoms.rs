//! Typed text-control edits. Selection, field/review protection and Native authority remain upstream.
use super::{ByteEdit,PatchError as E,PatchIntent,PatchLimits,Transaction,XmlElementSelector,WhitespaceControlKind as Kind};
use crate::TextAtom;
use std::{collections::BTreeSet,fmt};
#[derive(Clone,Eq,PartialEq)]
pub struct TextControlAtomReplacement{atom:u32,expected:Kind,output:Vec<TextAtom>}
impl fmt::Debug for TextControlAtomReplacement{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.debug_struct("TextControlAtomReplacement").field("atom",&self.atom).field("expected",&self.expected).field("output_atoms",&self.output.len()).finish_non_exhaustive()}}
impl TextControlAtomReplacement{
    /// # Errors
    /// Only real original control atoms are writable. Empty output deletes a control, not Text.
    /// Text output obeys the existing TextSpan reader; use typed Tab/LineBreak for those controls.
    pub fn new(atom:u32,expected:Kind,output:Vec<TextAtom>)->Result<Self,E>{
        if output.len()>PatchLimits::default().config().max_intents{return Err(E::ValueInvalid);}
        let mut bytes=0usize;
        for a in &output{match a{TextAtom::Text(t)=>{
            if t.is_empty(){return Err(E::ValueInvalid);}crate::text_flow::validate_text(t).map_err(|_|E::ValueInvalid)?;
            add(&mut bytes,t.len(),PatchLimits::default().config().max_value_bytes,"text_control_value")?;
        },_=>add(&mut bytes,1,PatchLimits::default().config().max_value_bytes,"text_control_value")?}}
        Ok(Self{atom,expected,output})
    }
}
fn add(total:&mut usize,n:usize,max:usize,label:&'static str)->Result<(),E>{
    *total=total.checked_add(n).filter(|v|*v<=max).ok_or(E::LimitExceeded{limit:label})?;Ok(())
}
fn escaped_size(text:&str)->Result<usize,E>{text.chars().try_fold(0usize,|n,ch|n.checked_add(match ch{'&'=>5,'<'=>4,'>'=>4,'\r'=>5,_=>ch.len_utf8()}).ok_or(E::AllocationFailed))}
pub(super) fn preflight(intents:&[PatchIntent],limits:PatchLimits)->Result<usize,E>{
    if !intents.iter().any(|i|matches!(i,PatchIntent::ReplaceTextControlAtoms{..})){return Ok(0);}
    let cap=limits.config();let(mut ranges,mut atoms,mut old_bytes)=(0usize,0usize,0usize);let mut seen=BTreeSet::new();
    for intent in intents{let(target,len)=match intent{
        PatchIntent::ReplaceTextControlAtoms{target,replacements}=>{
            if replacements.windows(2).any(|w|w[0].atom>=w[1].atom){return Err(E::Conflict);}
            for r in replacements{add(&mut atoms,r.output.len(),cap.max_intents,"text_control_joint_output_atoms")?;}(target,replacements.len())
        },
        PatchIntent::ReplaceWhitespaceAtomRanges{target,ranges}=>{
            for r in ranges{add(&mut atoms,r.output_atom_count(),cap.max_intents,"text_control_joint_output_atoms")?;}(target,ranges.len())
        },
        PatchIntent::ReplaceTextAtomScalarRanges{target,ranges}=>{
            for r in ranges{add(&mut old_bytes,escaped_size(r.replacement_value())?,cap.max_total_output_growth,"text_control_joint_output_bytes")?;}(target,ranges.len())
        },
        PatchIntent::ReplaceLeafScalarRanges{target,ranges}=>{
            for r in ranges{add(&mut old_bytes,escaped_size(r.data().2)?,cap.max_total_output_growth,"text_control_joint_output_bytes")?;}(target,ranges.len())
        },_=>continue};
        if len==0{return Err(E::ValueInvalid);}if !seen.insert((target.part.collision_key(),target.element_index)){return Err(E::Conflict);}
        add(&mut ranges,len,cap.max_intents,"text_control_joint_ranges")?;
    }Ok(old_bytes)
}
fn push(out:&mut String,s:&str,max:usize)->Result<(),E>{
    let _=out.len().checked_add(s.len()).filter(|n|*n<=max).ok_or(E::LimitExceeded{limit:"text_control_encoded_value"})?;out.push_str(s);Ok(())
}
fn render(atoms:&[TextAtom],prefix:&str,limits:PatchLimits,remaining:usize)->Result<Vec<u8>,E>{
    let cap=limits.config().max_value_bytes.min(remaining).min(if atoms.iter().any(|a|!matches!(a,TextAtom::Text(_))){limits.config().max_fragment_bytes}else{usize::MAX});
    let mut out=String::new();for atom in atoms{match atom{
        TextAtom::Text(t)=>{if t.is_empty(){return Err(E::ValueInvalid);}crate::text_flow::validate_text(t).map_err(|_|E::ValueInvalid)?;
            // Stream escaped text under the cap: never allocate a 5x temporary escaped value.
            for ch in t.chars(){match ch{'&'=>push(&mut out,"&amp;",cap)?,'<'=>push(&mut out,"&lt;",cap)?,'>'=>push(&mut out,"&gt;",cap)?,
                _=>{let mut buf=[0u8;4];push(&mut out,ch.encode_utf8(&mut buf),cap)?;}}}
        },
        TextAtom::Tab{width,leader,tab_type}=>{push(&mut out,"<",cap)?;push(&mut out,prefix,cap)?;
            push(&mut out,&format!("tab width=\"{width}\" leader=\"{leader}\" type=\"{tab_type}\"/>"),cap)?;},
        TextAtom::LineBreak=>{push(&mut out,"<",cap)?;push(&mut out,prefix,cap)?;push(&mut out,"lineBreak/>",cap)?;},
    }}Ok(out.into_bytes())
}
impl Transaction<'_>{
    pub(super) fn plan_text_control_atoms(&self,target:&XmlElementSelector,replacements:&[TextControlAtomReplacement],origin:usize,budget:&mut usize,edits:&mut Vec<ByteEdit>)->Result<(),E>{
        let xml=self.element_context(target)?;let node=&xml.elements()[target.element_index];if node.parent().is_none(){return Err(E::RootMutation);}
        let span=crate::text_flow::read_source_text_span(xml,target.element_index).map_err(|_|E::FragmentInvalid)?;
        let prefix=xml.with_source_bytes(|b|{let n=&b[node.start_name_span().start()..node.start_name_span().end()];
            n.iter().rposition(|c|*c==b':').map_or_else(String::new,|i|String::from_utf8_lossy(&n[..=i]).into_owned())});
        let mut next=0usize;let mut child=node.first_child();
        for(i,a)in span.atoms.iter().enumerate(){
            if matches!(a,TextAtom::Text(_)){if replacements.get(next).is_some_and(|r|r.atom as usize==i){return Err(E::SelectorKind);}continue;}
            let at=child.ok_or(E::FragmentInvalid)?;let control=&xml.elements()[at];child=control.next_sibling();
            let Some(r)=replacements.get(next).filter(|r|r.atom as usize==i)else{continue;};
            let kind=match a{TextAtom::Tab{..}=>Kind::Tab,TextAtom::LineBreak=>Kind::LineBreak,_=>return Err(E::FragmentInvalid)};
            if r.expected!=kind{return Err(E::SelectorKind);}let outer=control.outer_span().ok_or(E::FragmentInvalid)?;
            let remaining=self.patch_limits.config().max_total_output_growth.checked_sub(*budget).ok_or(E::LimitExceeded{limit:"text_control_joint_output_bytes"})?;
            let value=render(&r.output,&prefix,self.patch_limits,remaining)?;
            add(budget,value.len(),self.patch_limits.config().max_total_output_growth,"text_control_joint_output_bytes")?;
            edits.push(ByteEdit::new(target.part.collision_key(),outer.start(),outer.end(),value,origin));next+=1;
        }
        if child.is_some(){return Err(E::FragmentInvalid);}if next!=replacements.len(){return Err(E::SelectorOutOfRange);}Ok(())
    }
}
