use super::*;
use crate::{TextControlKind as Kind,TextControlAtomReplacement as Replacement};
use super::super::whitespace::{plan::Span,lexical::LexicalEdit};
pub(super) struct Plan<'a>{pub(super) intents:Vec<PatchIntent>,pub(super) spans:BTreeMap<&'a PackagePath,Vec<Span>>,
    pub(super) changes:Vec<SourceControlAtomChange>,pub(super) span_changes:Vec<SourceReplacementTextSpanChange>,
    pub(super) protection_parts:usize,pub(super) visits:usize,pub(super) bytes:usize}
fn add(total:&mut usize,n:usize,max:usize)->Result<(),E>{*total=total.checked_add(n).filter(|v|*v<=max).ok_or(E::Limit)?;Ok(())}
fn encoded_size(output:&[TextAtom],prefix:&str)->Result<usize,E>{
    let digits=|v:u32|if v==0{1}else{v.ilog10() as usize+1};let mut size=0usize;
    for a in output{let n=match a{TextAtom::Text(t)=>t.chars().try_fold(0usize,|n,c|n.checked_add(match c{'&'=>5,'<'=>4,'>'=>4,_=>c.len_utf8()}).ok_or(E::Limit))?,
        TextAtom::Tab{width,leader,tab_type}=>prefix.len().checked_add(b"<tab width=\"\" leader=\"\" type=\"\"/>".len()+digits(*width)+digits(*leader)+digits(*tab_type)).ok_or(E::Limit)?,
        TextAtom::LineBreak=>prefix.len().checked_add(b"<lineBreak/>".len()).ok_or(E::Limit)?};add(&mut size,n,usize::MAX)?;}Ok(size)
}
pub(super) fn validate_output(output:&[TextAtom],limits:SourceSearchLimits)->Result<([u8;32],usize),E>{
    if output.len()>PatchLimits::default().config().max_intents{return Err(E::Limit);}let mut text_bytes=0usize;
    let mut hash=Sha256::new();hash.update(b"hwpx-agent.source-text-control-output/v1\0");hash.update((output.len() as u64).to_le_bytes());
    for a in output{match a{TextAtom::Text(t)=>{
        if t.is_empty(){return Err(E::Value);}if t.len()>PatchLimits::default().config().max_value_bytes{return Err(E::Limit);}
        crate::text_flow::validate_text(t).map_err(|_|E::Value)?;add(&mut text_bytes,t.len(),limits.0.result_bytes)?;
        hash.update([0]);hash.update((t.len() as u64).to_le_bytes());hash.update(t.as_bytes());
    },TextAtom::Tab{width,leader,tab_type}=>{hash.update([1]);for n in[width,leader,tab_type]{hash.update(n.to_le_bytes());}},TextAtom::LineBreak=>hash.update([2])}}
    if encoded_size(output,"")?>limits.0.result_bytes.min(PatchLimits::default().config().max_value_bytes){return Err(E::Limit);}
    Ok((hash.finalize().into(),text_bytes))
}
fn encode(output:&[TextAtom],prefix:&str,size:usize)->Result<Vec<u8>,E>{
    let mut out=String::new();out.try_reserve_exact(size).map_err(|_|E::Limit)?;
    // Independent expected-byte encoder; the actual patch uses its own bounded streaming renderer.
    for a in output{match a{TextAtom::Text(t)=>for c in t.chars(){match c{'&'=>out.push_str("&amp;"),'<'=>out.push_str("&lt;"),'>'=>out.push_str("&gt;"),_=>out.push(c)}},
        TextAtom::Tab{width,leader,tab_type}=>out.push_str(&format!("<{prefix}tab width=\"{width}\" leader=\"{leader}\" type=\"{tab_type}\"/>")),
        TextAtom::LineBreak=>out.push_str(&format!("<{prefix}lineBreak/>"))}}
    if out.len()!=size{return Err(E::Limit);}Ok(out.into_bytes())
}
fn append_atom(atoms:&mut Vec<TextAtom>,a:&TextAtom,max:usize)->Result<(),E>{
    if let TextAtom::Text(t)=a{if t.is_empty(){return Ok(());}if let Some(TextAtom::Text(last))=atoms.last_mut(){append(last,t,max)?;}
        else{if t.len()>max{return Err(E::Limit);}atoms.push(a.clone());}}else{atoms.push(a.clone());}Ok(())
}
pub(super) fn compile<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    search:&SourceReviewSelectorControlResult,windows:&BTreeMap<usize,(usize,usize)>,expected:Kind,output:&[TextAtom],output_sha:[u8;32])->Result<Plan<'a>,E>{
    let cap=PatchLimits::default().config();if search.controls().len()>cap.max_intents{return Err(E::Limit);}
    let source=index.original.source();let intervals=context.field_intervals(source,fields)?;
    type Targets= BTreeMap<usize,BTreeMap<usize,(usize,SourceAnchorHandle)>>;
    let mut parts:BTreeMap<&PackagePath,Targets>=BTreeMap::new();let mut seen=BTreeSet::new();let mut wanted_parents=BTreeSet::new();
    for(ordinal,m)in search.controls().iter().enumerate(){
        if !seen.insert(&m.control_anchor.opaque_handle){return Err(E::Selection);}
        let resolved=source.resolve_anchor(&m.control_anchor).map_err(|_|E::Selection)?;let control=resolved.element().ok_or(E::Selection)?;
        let xml=resolved.part().xml().ok_or(E::Selection)?;let parent=control.parent().ok_or(E::Selection)?;let t=&xml.elements()[parent];
        if t.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||t.name().local_name()!="t"{return Err(E::Selection);}
        wanted_parents.insert(resolved.part().element_anchor(parent).ok_or(E::Selection)?.opaque_handle.clone());
        if parts.entry(resolved.part().path()).or_default().entry(parent).or_default()
            .insert(resolved.element_index().ok_or(E::Selection)?,(ordinal,m.control_anchor.clone())).is_some(){return Err(E::Selection);}
    }
    // Whole atomic coverage must come from this same selector's complete original unit, not merely
    // an enclosing paragraph or an anchor-start discovery match. Retain only selected parents/kind.
    let mut allowed=BTreeSet::new();let wanted=match expected{Kind::Tab=>'\t',Kind::LineBreak=>'\n'};
    for(&block,&(a,b))in windows{for(pos,unit)in index.blocks.get(block).ok_or(E::Selection)?.units.get(a..b).ok_or(E::Selection)?.iter().enumerate(){
        if unit.ch!=wanted||unit.origins.len()!=1{continue;}let origin=unit.origins[0];let p=index.points.get(origin).ok_or(E::Selection)?;
        if !wanted_parents.contains(&index.segments[p.segment].opaque_handle){continue;}
        if p.scalar!=0||index.usage.get(origin)!=Some(&(a+pos,a+pos)){return Err(E::Selection);}
        allowed.insert((index.segments[p.segment].opaque_handle.clone(),p.atom));
    }}
    let mut plan=Plan{intents:Vec::new(),spans:BTreeMap::new(),changes:Vec::new(),span_changes:Vec::new(),protection_parts:parts.len(),visits:0,bytes:0};
    let(mut changes,mut spans_order,mut total_atoms,mut span_bytes)=(BTreeMap::new(),BTreeMap::new(),0usize,0usize);
    let mut encoded:BTreeMap<String,Vec<u8>>=BTreeMap::new();
    for(path,parents)in parts{
        let part=source.parts().iter().find(|p|p.path()==path).ok_or(E::Source)?;let xml=part.xml().ok_or(E::Source)?;
        let guard=unicode::plan::guard(xml)?;add(&mut plan.visits,xml.elements().len().checked_mul(3).ok_or(E::Limit)?,usize::MAX)?;
        for(element,targets)in parents{
            if *guard.get(element).ok_or(E::Selection)?{return Err(E::Protection);}
            let node=&xml.elements()[element];let at=node.start_tag_span().start();if let Some(r)=intervals.get(path){let j=r.partition_point(|(a,_)|*a<at);if j>0&&at<r[j-1].1{return Err(E::FieldContent);}}
            let before=crate::text_flow::read_source_text_span(xml,element).map_err(|_|E::Selection)?;
            let parent_anchor=part.element_anchor(element).ok_or(E::Selection)?;let mut after=TextSpan{character_style_id_ref:before.character_style_id_ref,atoms:Vec::new()};
            let prefix=xml.with_source_bytes(|b|{let r=node.start_name_span();let name=&b[r.start()..r.end()];name.iter().rposition(|c|*c==b':')
                .map_or_else(String::new,|i|String::from_utf8_lossy(&name[..=i]).into_owned())});
            let outer=node.outer_span().ok_or(E::Selection)?;let mut output_outer_bytes=outer.len();
            let mut child=node.first_child();let(mut observed,mut changed,mut replacements,mut lexical,mut first)=(0usize,0usize,Vec::new(),Vec::new(),usize::MAX);
            for(atom,a)in before.atoms.iter().enumerate(){
                if matches!(a,TextAtom::Text(_)){append_atom(&mut after.atoms,a,index.limits.0.result_bytes)?;continue;}
                let at=child.ok_or(E::Selection)?;let control=&xml.elements()[at];child=control.next_sibling();
                let Some((ordinal,anchor))=targets.get(&at)else{append_atom(&mut after.atoms,a,index.limits.0.result_bytes)?;continue;};observed+=1;
                let atom=u32::try_from(atom).map_err(|_|E::Limit)?;
                if !allowed.contains(&(parent_anchor.opaque_handle.clone(),atom)){return Err(E::Selection);}
                let kind=match a{TextAtom::Tab{..}=>Kind::Tab,TextAtom::LineBreak=>Kind::LineBreak,_=>return Err(E::Selection)};
                if kind!=expected{return Err(E::Selection);}if output==std::slice::from_ref(a){append_atom(&mut after.atoms,a,index.limits.0.result_bytes)?;continue;}
                // Check actual namespace/escaping and aggregate output BEFORE any per-control clone.
                let size=if let Some(value)=encoded.get(&prefix){value.len()}else{encoded_size(output,&prefix)?};
                if size>cap.max_value_bytes||output.iter().any(|a|!matches!(a,TextAtom::Text(_)))&&size>cap.max_fragment_bytes{return Err(E::Limit);}
                let outer=control.outer_span().ok_or(E::Selection)?;
                output_outer_bytes=output_outer_bytes.checked_sub(outer.len()).and_then(|n|n.checked_add(size))
                    .filter(|n|*n<=crate::TextFlowLimits::default().config().input_bytes).ok_or(E::Limit)?;
                add(&mut plan.bytes,size,index.limits.0.result_bytes.min(cap.max_total_output_growth))?;add(&mut total_atoms,output.len(),cap.max_intents)?;
                if !encoded.contains_key(&prefix){encoded.insert(prefix.clone(),encode(output,&prefix,size)?);}
                for a in output{append_atom(&mut after.atoms,a,index.limits.0.result_bytes)?;}
                replacements.push(Replacement::new(atom,expected,output.to_vec()).map_err(|_|E::Value)?);
                lexical.push(LexicalEdit{old:outer.start()..outer.end(),output:encoded[&prefix].clone()});
                changes.insert(*ordinal,SourceControlAtomChange{source_control_anchor:anchor.clone(),original_atom:atom,original_kind:search.controls()[*ordinal].kind,
                    output_atoms:output.len(),output_semantic_sha256:output_sha});changed+=1;first=first.min(*ordinal);
            }
            if child.is_some()||observed!=targets.len(){return Err(E::Selection);}if replacements.is_empty(){continue;}
            let bytes=text_bytes(&after)?;if bytes>crate::TextFlowLimits::default().config().text_bytes{return Err(E::Limit);}
            add(&mut span_bytes,bytes,index.limits.0.result_bytes)?;
            spans_order.insert(first,SourceReplacementTextSpanChange{source_text_anchor:parent_anchor.clone(),source_span_sha256:span_sha(&before),output_span_sha256:span_sha(&after),
                output_text_bytes:bytes,changed_scalar_ranges:changed,changed_original_text_atoms:0,
                preserved_controls:before.atoms.iter().filter(|a|!matches!(a,TextAtom::Text(_))).count()-changed});
            plan.intents.push(PatchIntent::ReplaceTextControlAtoms{target:XmlElementSelector::bind(path,xml,element).map_err(|_|E::Selection)?,replacements});
            plan.spans.entry(path).or_default().push(Span{element,expected:after,lexical});
        }
    }
    if plan.intents.is_empty(){return Err(E::NoChange);}plan.changes=changes.into_values().collect();plan.span_changes=spans_order.into_values().collect();Ok(plan)
}
