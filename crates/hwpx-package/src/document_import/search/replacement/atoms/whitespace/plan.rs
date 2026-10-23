use super::*;
use crate::{WhitespaceAtomRangeReplacement as Replacement,WhitespaceControlKind as Control,
    WhitespaceOutputAtom as Out,WhitespaceText};
struct Cached {span:TextSpan,offsets:Vec<Vec<usize>>}
struct Edit {atom:u32,start:u32,end:u32,output:Option<TextAtom>}
use super::lexical::LexicalEdit;
pub(in crate::document_import::search::replacement::atoms) struct Span {
    pub(in crate::document_import::search::replacement::atoms) element:usize,
    pub(in crate::document_import::search::replacement::atoms) expected:TextSpan,
    pub(in crate::document_import::search::replacement::atoms) lexical:Vec<LexicalEdit>,
}
pub(super) struct Plan<'a>{
    pub(super) intents:Vec<PatchIntent>,pub(super) spans:BTreeMap<&'a PackagePath,Vec<Span>>,
    pub(super) sequences:usize,pub(super) ranges:usize,pub(super) controls:usize,
    pub(super) protection_parts:usize,pub(super) visits:usize,pub(super) changes:Vec<SourceReplacementTextSpanChange>,
}
fn admitted(ch:char,policy:SourceWhitespaceTextPolicy)->bool{
    let all=matches!(ch,'\u{20}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}');
    match policy{SourceWhitespaceTextPolicy::None=>false,SourceWhitespaceTextPolicy::AsciiSpace=>ch==' ',
        SourceWhitespaceTextPolicy::Unicode17Breaking=>all&&!matches!(ch,'\u{a0}'|'\u{2007}'|'\u{202f}'),SourceWhitespaceTextPolicy::Unicode17AllModelAdmitted=>all}
}
fn value(policy:SourceWhitespaceOutput)->Option<TextAtom>{match policy{
    SourceWhitespaceOutput::Spaces{count}=>Some(TextAtom::Text(" ".repeat(usize::from(count)))),
    SourceWhitespaceOutput::Tab{width,leader,tab_type}=>Some(TextAtom::Tab{width,leader,tab_type}),
    SourceWhitespaceOutput::LineBreak=>Some(TextAtom::LineBreak),SourceWhitespaceOutput::Remove=>None}}
fn typed(atom:&Option<TextAtom>)->Result<Vec<Out>,E>{Ok(match atom{
    None=>Vec::new(),Some(TextAtom::Text(t))=>vec![Out::Text(WhitespaceText::new(t).map_err(|_|E::Value)?)],
    Some(TextAtom::Tab{width,leader,tab_type})=>vec![Out::Tab{width:*width,leader:*leader,tab_type:*tab_type}],Some(TextAtom::LineBreak)=>vec![Out::LineBreak]})}
fn output_cost(atom:&Option<TextAtom>)->usize{match atom{None=>0,Some(TextAtom::Text(t))=>t.len(),Some(_)=>96}}
fn add(total:&mut usize,n:usize,max:usize)->Result<(),E>{*total=total.checked_add(n).filter(|v|*v<=max).ok_or(E::Limit)?;Ok(())}
fn lexical_output(atom:&Option<TextAtom>,prefix:&str,total:&mut usize,limit:usize)->Result<Vec<u8>,E>{
    let digits=|v:u32|if v==0{1}else{v.ilog10() as usize+1};
    let size=match atom{None=>0,Some(TextAtom::Text(t))=>t.len(),
        Some(TextAtom::Tab{width,leader,tab_type})=>prefix.len().checked_add(b"<tab width=\"\" leader=\"\" type=\"\"/>".len())
            .and_then(|n|n.checked_add(digits(*width)+digits(*leader)+digits(*tab_type))).ok_or(E::Limit)?,
        Some(TextAtom::LineBreak)=>prefix.len().checked_add(b"<lineBreak/>".len()).ok_or(E::Limit)?};
    // Budget the actual namespace/numeric byte lengths BEFORE allocating any rendered control.
    add(total,size,limit)?;
    let output=match atom{None=>Vec::new(),Some(TextAtom::Text(t))=>t.as_bytes().to_vec(),
        Some(TextAtom::Tab{width,leader,tab_type})=>format!("<{prefix}tab width=\"{width}\" leader=\"{leader}\" type=\"{tab_type}\"/>").into_bytes(),
        Some(TextAtom::LineBreak)=>format!("<{prefix}lineBreak/>").into_bytes()};
    if output.len()!=size{return Err(E::Limit);}Ok(output)
}
fn append_atom(atoms:&mut Vec<TextAtom>,atom:TextAtom,limit:usize)->Result<(),E>{
    if let TextAtom::Text(text)=atom{if text.is_empty(){return Ok(());}if let Some(TextAtom::Text(last))=atoms.last_mut(){append(last,&text,limit)?;}
        else{if text.len()>limit{return Err(E::Limit);}atoms.push(TextAtom::Text(text));}}
    else{atoms.push(atom);}Ok(())
}
fn flush(index:&SourceTextIndex<'_>,pending:&mut Vec<usize>,edits:&mut BTreeMap<usize,Vec<Edit>>,policy:SourceWhitespacePolicy,
    sequences:&mut usize,ranges:&mut usize,bytes:&mut usize)->Result<(),E>{
    if pending.is_empty(){return Ok(());}add(sequences,1,index.limits.0.decomposed_scalars)?;
    let mut pieces:Vec<(usize,u32,u32,u32)>=Vec::new();
    for &origin in pending.iter(){let p=index.points[origin];if let Some(last)=pieces.last_mut(){if last.0==p.segment&&last.1==p.atom&&last.3==p.scalar{last.3+=1;continue;}}
        pieces.push((p.segment,p.atom,p.scalar,p.scalar+1));}
    for(i,(segment,atom,start,end))in pieces.into_iter().enumerate(){
        add(ranges,1,PatchLimits::default().config().max_intents)?;
        let output=if i==0{value(policy.output)}else{None};add(bytes,output_cost(&output),index.limits.0.result_bytes)?;
        edits.entry(segment).or_default().push(Edit{atom,start,end,output});
    }pending.clear();Ok(())
}
pub(super) fn compile<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    groups:Vec<Vec<usize>>,selected:&BTreeSet<usize>,policy:SourceWhitespacePolicy)->Result<Plan<'a>,E>{
    let source=index.original.source();let intervals=context.field_intervals(source,fields)?;
    let mut caches=BTreeMap::new();let mut guards=BTreeMap::new();let mut visits=0usize;
    // Check all selected source segments, including no-op/non-whitespace matches, BEFORE discarding edits.
    for &origin in selected{let p=index.points[origin];if caches.contains_key(&p.segment){continue;}
        let resolved=source.resolve_anchor(&index.segments[p.segment]).map_err(|_|E::Selection)?;
        let path=resolved.part().path();let xml=resolved.part().xml().ok_or(E::Selection)?;let element=resolved.element_index().ok_or(E::Selection)?;
        if !guards.contains_key(path){add(&mut visits,xml.elements().len().checked_mul(3).ok_or(E::Limit)?,usize::MAX)?;guards.insert(path,unicode::plan::guard(xml)?);}
        if *guards.get(path).and_then(|g|g.get(element)).ok_or(E::Selection)?{return Err(E::Protection);}
        let at=xml.elements()[element].start_tag_span().start();if let Some(r)=intervals.get(path){let j=r.partition_point(|(a,_)|*a<at);if j>0&&at<r[j-1].1{return Err(E::FieldContent);}}
        let span=crate::text_flow::read_source_text_span(xml,element).map_err(|_|E::Selection)?;
        let offsets=span.atoms.iter().map(|a|match a{TextAtom::Text(t)=>{let mut v:Vec<_>=t.char_indices().map(|(i,_)|i).collect();v.push(t.len());v},_=>Vec::new()}).collect();
        caches.insert(p.segment,Cached{span,offsets});
    }
    let mut plan=Plan{intents:Vec::new(),spans:BTreeMap::new(),sequences:0,ranges:0,controls:0,protection_parts:guards.len(),visits,changes:Vec::new()};
    let(mut edits,mut ranges,mut output_bytes)=(BTreeMap::new(),0usize,0usize);
    for origins in groups{let mut pending=Vec::new();for origin in origins{let p=index.points[origin];let cache=caches.get(&p.segment).ok_or(E::Selection)?;
        let included=match cache.span.atoms.get(p.atom as usize).ok_or(E::Selection)?{
            TextAtom::Text(t)=>{let offsets=&cache.offsets[p.atom as usize];let a=*offsets.get(p.scalar as usize).ok_or(E::Selection)?;
                let b=*offsets.get(p.scalar as usize+1).ok_or(E::Selection)?;admitted(t.get(a..b).and_then(|s|s.chars().next()).ok_or(E::Selection)?,policy.text)},
            TextAtom::Tab{..}=>policy.tabs,TextAtom::LineBreak=>policy.line_breaks};
        if included{pending.push(origin);}
        if !included||policy.sequence==SourceWhitespaceSequencePolicy::EachOriginalScalar{
            flush(index,&mut pending,&mut edits,policy,&mut plan.sequences,&mut ranges,&mut output_bytes)?;}
    }flush(index,&mut pending,&mut edits,policy,&mut plan.sequences,&mut ranges,&mut output_bytes)?;}
    let(mut total_span_bytes,mut lexical_bytes)=(0usize,0usize);
    for(segment,mut edits)in edits{
        let cache=caches.remove(&segment).ok_or(E::Selection)?;let before=cache.span;
        edits.sort_by_key(|e|(e.atom,e.start));if edits.windows(2).any(|w|w[0].atom==w[1].atom&&w[0].end>w[1].start){return Err(E::Selection);}
        // Remove semantic no-ops without rewriting their original entities or control attributes.
        edits.retain(|e|match &before.atoms[e.atom as usize]{TextAtom::Text(t)=>{
            let offsets=&cache.offsets[e.atom as usize];match &e.output{Some(TextAtom::Text(v))=>&t[offsets[e.start as usize]..offsets[e.end as usize]]!=v,_=>true}},a=>e.output.as_ref()!=Some(a)});
        if edits.is_empty(){continue;}
        let resolved=source.resolve_anchor(&index.segments[segment]).map_err(|_|E::Selection)?;
        let path=resolved.part().path();let xml=resolved.part().xml().ok_or(E::Selection)?;let element=resolved.element_index().ok_or(E::Selection)?;
        let mut requested:BTreeMap<u32,Vec<u32>>=BTreeMap::new();
        for e in &edits{if matches!(before.atoms[e.atom as usize],TextAtom::Text(_)){let p=requested.entry(e.atom).or_default();p.extend([e.start,e.end]);}}
        for points in requested.values_mut(){points.sort_unstable();points.dedup();}
        let offsets=if requested.is_empty(){BTreeMap::new()}else{crate::patch::text_atom_ranges::scalar_edges(xml,element,&requested).map_err(|_|E::Selection)?};
        let node=&xml.elements()[element];let mut child=node.first_child();let mut control_ranges=BTreeMap::new();
        for(i,a)in before.atoms.iter().enumerate(){if matches!(a,TextAtom::Text(_)){continue;}
            let at=child.ok_or(E::Selection)?;let n=&xml.elements()[at];let r=n.outer_span().ok_or(E::Selection)?;
            control_ranges.insert(i,r.start()..r.end());child=n.next_sibling();}if child.is_some(){return Err(E::Selection);}
        let prefix=xml.with_source_bytes(|b|{let r=node.start_name_span();let name=&b[r.start()..r.end()];
            name.iter().rposition(|v|*v==b':').map_or_else(String::new,|i|String::from_utf8_lossy(&name[..=i]).into_owned())});
        let mut replacements=Vec::new();let mut lexical=Vec::new();let mut after=TextSpan{character_style_id_ref:before.character_style_id_ref,atoms:Vec::new()};
        let(mut edit_index,mut changed_text,mut changed_controls)=(0usize,0usize,0usize);
        for(atom,a)in before.atoms.iter().enumerate(){let first=edit_index;while edit_index<edits.len()&&edits[edit_index].atom as usize==atom{edit_index+=1;}
            let current=&edits[first..edit_index];if current.is_empty(){append_atom(&mut after.atoms,a.clone(),index.limits.0.result_bytes)?;continue;}
            let mut previous=0usize;if matches!(a,TextAtom::Text(_)){changed_text+=1;}else{changed_controls+=1;}
            for e in current{
                let old=if let TextAtom::Text(t)=a{let local=&cache.offsets[atom];let start=local[e.start as usize];let end=local[e.end as usize];
                    append_atom(&mut after.atoms,TextAtom::Text(t[previous..start].to_owned()),index.limits.0.result_bytes)?;previous=end;
                    let points=&requested[&e.atom];let edges=&offsets[&e.atom];
                    let start=edges[points.binary_search(&e.start).map_err(|_|E::Selection)?];let end=edges[points.binary_search(&e.end).map_err(|_|E::Selection)?];
                    replacements.push(Replacement::text(e.atom,e.start,e.end,typed(&e.output)?).map_err(|_|E::Value)?);start..end
                }else{let kind=match a{TextAtom::Tab{..}=>Control::Tab,TextAtom::LineBreak=>Control::LineBreak,_=>return Err(E::Selection)};
                    replacements.push(Replacement::control(e.atom,kind,typed(&e.output)?));control_ranges.get(&atom).ok_or(E::Selection)?.clone()};
                if let Some(a)=&e.output{append_atom(&mut after.atoms,a.clone(),index.limits.0.result_bytes)?;}
                // Independent canonical encoding for exact byte readback, not the low-level patch renderer.
                let output=lexical_output(&e.output,&prefix,&mut lexical_bytes,index.limits.0.result_bytes)?;
                lexical.push(LexicalEdit{old,output});
            }
            if let TextAtom::Text(t)=a{append_atom(&mut after.atoms,TextAtom::Text(t[previous..].to_owned()),index.limits.0.result_bytes)?;}
        }
        let bytes=text_bytes(&after)?;add(&mut total_span_bytes,bytes,index.limits.0.result_bytes)?;
        let change=SourceReplacementTextSpanChange{source_text_anchor:index.segments[segment].clone(),source_span_sha256:span_sha(&before),output_span_sha256:span_sha(&after),
            output_text_bytes:bytes,changed_scalar_ranges:replacements.len(),changed_original_text_atoms:changed_text,
            preserved_controls:before.atoms.iter().filter(|a|!matches!(a,TextAtom::Text(_))).count()-changed_controls};
        plan.ranges+=replacements.len();plan.controls+=changed_controls;plan.changes.push(change);
        plan.intents.push(PatchIntent::ReplaceWhitespaceAtomRanges{target:XmlElementSelector::bind(path,xml,element).map_err(|_|E::Selection)?,ranges:replacements});
        plan.spans.entry(path).or_default().push(Span{element,expected:after,lexical});
    }
    if plan.intents.is_empty(){return Err(E::NoChange);}Ok(plan)
}
