use super::*;
struct CachedSpan {span:TextSpan,offsets:Vec<Vec<usize>>}
struct Edit {atom:u32,start:u32,end:u32,value:String}
pub(in crate::document_import::search::replacement::atoms) struct Plan<'a> {
    pub(in crate::document_import::search::replacement::atoms) intents:Vec<PatchIntent>,
    pub(in crate::document_import::search::replacement::atoms) spans:BTreeMap<&'a PackagePath,Vec<PlannedSpan>>,
    pub(in crate::document_import::search::replacement::atoms) selected:usize,
    pub(in crate::document_import::search::replacement::atoms) groups:usize,
    pub(in crate::document_import::search::replacement::atoms) decomposed:usize,
    pub(in crate::document_import::search::replacement::atoms) components:usize,
    pub(in crate::document_import::search::replacement::atoms) ranges:usize,
    pub(in crate::document_import::search::replacement::atoms) changes:Vec<SourceReplacementTextSpanChange>,
    pub(in crate::document_import::search::replacement::atoms) protection_parts:usize,
    pub(in crate::document_import::search::replacement::atoms) visits:usize,
}
pub(in crate::document_import::search::replacement::atoms) fn guard(xml:&PreservingXmlDocument)->Result<Vec<bool>,E> {
    let mut protected=crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?;
    let mut tracked=Vec::new();
    for(i,node)in xml.elements().iter().enumerate(){let own=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
        &&(matches!(node.name().local_name(),"insertBegin"|"insertEnd"|"deleteBegin"|"deleteEnd")
        ||node.attributes().iter().any(|a|a.name().namespace().is_none()&&matches!(a.name().local_name(),"paraTcId"|"charTcId")));
        let inherited=match node.parent(){Some(p)if p<i=>tracked[p],Some(_)=>return Err(E::Source),None=>false};
        tracked.push(own||inherited);protected[i]|=own||inherited;
    }Ok(protected)
}
pub(super) fn compile<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    windows:&BTreeMap<usize,(usize,usize)>,form:SourceUnicodeNormalizationForm)->Result<Plan<'a>,E> {
    let mut selected=BTreeSet::new();let mut groups=Vec::new();
    for(&block,&(start,end))in windows {
        let units=&index.blocks.get(block).ok_or(E::Selection)?.units;let mut origins=BTreeSet::new();
        for u in units.get(start..end).ok_or(E::Selection)? {origins.extend(u.origins.iter().copied());}
        let origins:Vec<_>=origins.into_iter().collect();
        if origins.windows(2).any(|w|w[0]+1!=w[1]){return Err(E::Selection);}
        for &origin in &origins {
            let &(a,b)=index.usage.get(origin).ok_or(E::Selection)?;
            if a<start||b>=end||!selected.insert(origin){return Err(E::Selection);}
        }groups.push(origins);
    }
    compile_selected(index,fields,context,groups,selected,form)
}
pub(super) fn compile_found<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    found:&crate::document_import::search::SourceSearchResult,form:SourceUnicodeNormalizationForm)->Result<Plan<'a>,E> {
    if found.matches().is_empty(){return Err(E::NoMatches);}
    let mut selected=BTreeSet::new();let mut groups=Vec::new();
    for m in found.matches() {
        let origins=selected_origins(index,m)?;
        for &origin in &origins {if !selected.insert(origin){return Err(E::Selection);}}
        // Each match is a separate normalization group, even when matches are adjacent.
        groups.push(origins.into_iter().collect());
    }compile_selected(index,fields,context,groups,selected,form)
}
fn compile_selected<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    groups:Vec<Vec<usize>>,selected:BTreeSet<usize>,form:SourceUnicodeNormalizationForm)->Result<Plan<'a>,E> {
    compile_mapped(index,fields,context,groups,selected,|chars,_ids,remaining,bytes|transform::normalize(chars,form,remaining,bytes))
}
pub(in crate::document_import::search::replacement::atoms) fn compile_mapped<'a,F>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    groups:Vec<Vec<usize>>,selected:BTreeSet<usize>,mut mapper:F)->Result<Plan<'a>,E>
where F:FnMut(&[char],&[usize],usize,usize)->Result<(Vec<transform::Change>,usize),E> {
    let source=index.original.source();
    let intervals=context.field_intervals(source,fields)?;let mut caches=BTreeMap::new();let mut guards=BTreeMap::new();let mut visits=0usize;
    for &origin in &selected {
        let p=*index.points.get(origin).ok_or(E::Selection)?;if caches.contains_key(&p.segment){continue;}
        let resolved=source.resolve_anchor(&index.segments[p.segment]).map_err(|_|E::Selection)?;
        let path=resolved.part().path();let xml=resolved.part().xml().ok_or(E::Selection)?;let i=resolved.element_index().ok_or(E::Selection)?;
        if !guards.contains_key(path) {visits=visits.checked_add(xml.elements().len().checked_mul(3).ok_or(E::Limit)?).ok_or(E::Limit)?;guards.insert(path,guard(xml)?);}
        if guards.get(path).and_then(|g|g.get(i)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
        let at=xml.elements()[i].start_tag_span().start();if let Some(ranges)=intervals.get(path){let j=ranges.partition_point(|(a,_)|*a<at);
            if j>0&&at<ranges[j-1].1{return Err(E::FieldContent);}}
        let span=crate::text_flow::read_source_text_span(xml,i).map_err(|_|E::Selection)?;
        let offsets=span.atoms.iter().map(|a|match a {TextAtom::Text(t)=>{let mut v:Vec<_>=t.char_indices().map(|(i,_)|i).collect();v.push(t.len());v},_=>Vec::new()}).collect();
        caches.insert(p.segment,CachedSpan {span,offsets});
    }
    let mut plan=Plan {intents:Vec::new(),spans:BTreeMap::new(),selected:selected.len(),groups:0,decomposed:0,components:0,ranges:0,changes:Vec::new(),protection_parts:guards.len(),visits};
    let mut edits:BTreeMap<usize,Vec<Edit>>=BTreeMap::new();let mut total_ranges=0usize;let mut replacement_bytes=0usize;
    for origins in groups {
        let(mut chars,mut ids)=(Vec::new(),Vec::new());
        for origin in origins {let p=index.points[origin];let cache=caches.get(&p.segment).ok_or(E::Selection)?;
            match cache.span.atoms.get(p.atom as usize).ok_or(E::Selection)? {
                TextAtom::Text(text)=>{let offsets=&cache.offsets[p.atom as usize];let a=*offsets.get(p.scalar as usize).ok_or(E::Selection)?;
                    let b=*offsets.get(p.scalar as usize+1).ok_or(E::Selection)?;let ch=text.get(a..b).and_then(|v|v.chars().next()).ok_or(E::Selection)?;
                    chars.push(ch);ids.push(origin);},
                _=>{lower_group(index,&chars,&ids,&mut mapper,&mut plan,&mut edits,&mut total_ranges,&mut replacement_bytes)?;chars.clear();ids.clear();}
            }
        }lower_group(index,&chars,&ids,&mut mapper,&mut plan,&mut edits,&mut total_ranges,&mut replacement_bytes)?;
    }
    let mut output_bytes=0usize;
    for(segment,mut edits)in edits {
        let cache=caches.remove(&segment).ok_or(E::Selection)?;let before=cache.span;let mut after=before.clone();let mut ranges=Vec::new();
        edits.sort_by_key(|e|(e.atom,e.start));if edits.windows(2).any(|w|w[0].atom==w[1].atom&&w[0].end>w[1].start){return Err(E::Selection);}
        let mut slots=Vec::new();let mut slot=0usize;for atom in &before.atoms {slots.push(slot);if !matches!(atom,TextAtom::Text(_)){slot+=1;}}
        let(mut first,mut changed_slots,mut changed_atoms)=(0usize,Vec::new(),0usize);
        while first<edits.len(){let atom=edits[first].atom as usize;let mut last=first+1;while last<edits.len()&&edits[last].atom as usize==atom{last+=1;}
            let TextAtom::Text(text)=&before.atoms[atom]else{return Err(E::Selection)};let offsets=&cache.offsets[atom];let mut next=String::new();let mut previous=0;
            for e in &edits[first..last]{let a=*offsets.get(e.start as usize).ok_or(E::Selection)?;let b=*offsets.get(e.end as usize).ok_or(E::Selection)?;
                if text.get(a..b)==Some(e.value.as_str()){continue;}
                append(&mut next,&text[previous..a],index.limits.0.result_bytes)?;append(&mut next,&e.value,index.limits.0.result_bytes)?;previous=b;
                ranges.push(TextAtomRangeReplacement::new(e.atom,e.start,e.end,&e.value).map_err(|_|E::Value)?);
            }
            if previous!=0 {append(&mut next,&text[previous..],index.limits.0.result_bytes)?;after.atoms[atom]=TextAtom::Text(next);changed_slots.push(slots[atom]);changed_atoms+=1;}
            first=last;
        }
        if ranges.is_empty(){continue;}after.atoms.retain(|a|!matches!(a,TextAtom::Text(t)if t.is_empty()));
        let bytes=text_bytes(&after)?;output_bytes=output_bytes.checked_add(bytes).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
        let anchor=&index.segments[segment];let resolved=source.resolve_anchor(anchor).map_err(|_|E::Selection)?;
        let path=resolved.part().path();let xml=resolved.part().xml().ok_or(E::Selection)?;let i=resolved.element_index().ok_or(E::Selection)?;
        changed_slots.sort_unstable();changed_slots.dedup();let change=SourceReplacementTextSpanChange {source_text_anchor:anchor.clone(),source_span_sha256:span_sha(&before),
            output_span_sha256:span_sha(&after),output_text_bytes:bytes,changed_scalar_ranges:ranges.len(),changed_original_text_atoms:changed_atoms,
            preserved_controls:before.atoms.iter().filter(|a|!matches!(a,TextAtom::Text(_))).count()};
        plan.ranges=plan.ranges.checked_add(ranges.len()).ok_or(E::Limit)?;plan.changes.push(change.clone());
        plan.intents.push(PatchIntent::ReplaceTextAtomScalarRanges {target:XmlElementSelector::bind(path,xml,i).map_err(|_|E::Selection)?,ranges});
        plan.spans.entry(path).or_default().push(PlannedSpan {element:i,expected:after,old_slots:readback::slots(xml,i)?,changed_slots,change,expanded_empty:false});
    }
    if plan.intents.is_empty(){return Err(E::NoChange);}Ok(plan)
}
fn lower_group<F>(index:&SourceTextIndex<'_>,chars:&[char],ids:&[usize],mapper:&mut F,plan:&mut Plan<'_>,
    edits:&mut BTreeMap<usize,Vec<Edit>>,ranges:&mut usize,bytes:&mut usize)->Result<(),E>
where F:FnMut(&[char],&[usize],usize,usize)->Result<(Vec<transform::Change>,usize),E> {
    if chars.is_empty(){return Ok(());}plan.groups+=1;
    let(changes,count)=mapper(chars,ids,index.limits.0.decomposed_scalars.checked_sub(plan.decomposed).ok_or(E::Limit)?,index.limits.0.result_bytes)?;
    plan.decomposed=plan.decomposed.checked_add(count).ok_or(E::Limit)?;
    for change in changes {plan.components=plan.components.checked_add(1).filter(|n|*n<=index.limits.0.matches).ok_or(E::Limit)?;
        *bytes=bytes.checked_add(change.value.len()).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
        let mut pieces:Vec<(usize,u32,u32,u32)>=Vec::new();
        for &origin in &ids[change.input] {let p=index.points[origin];if let Some(last)=pieces.last_mut(){if last.0==p.segment&&last.1==p.atom&&last.3==p.scalar {last.3+=1;continue;}}
            pieces.push((p.segment,p.atom,p.scalar,p.scalar+1));}
        for(i,(segment,atom,start,end))in pieces.into_iter().enumerate(){*ranges=ranges.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            edits.entry(segment).or_default().push(Edit {atom,start,end,value:if i==0{change.value.clone()}else{String::new()}});}
    }Ok(())
}
