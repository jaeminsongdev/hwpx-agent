//! Explicit v2 literal candidates with original TextSpan controls retained, not flattened.
mod readback;
pub mod review;
pub mod regex;
pub mod styles;
pub mod unicode;
pub mod case;
pub mod width;
pub mod whitespace;
pub mod controls;
pub mod number_controls;
pub mod sort;
pub mod personal_info;
use super::*;
use crate::{TextAtom,TextSpan,TextAtomRangeReplacement};
use std::ops::Range;
pub const SOURCE_LITERAL_TEXT_ATOM_PROFILE:&str="hwpx-agent.source-literal-replacement-candidate/v2";
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceReplacementTextSpanChange {
    pub source_text_anchor:SourceAnchorHandle,pub source_span_sha256:[u8;32],pub output_span_sha256:[u8;32],
    pub output_text_bytes:usize,pub changed_scalar_ranges:usize,pub changed_original_text_atoms:usize,pub preserved_controls:usize,
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceLiteralTextAtomReceipt {
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_index_sha256:[u8;32],pub scope_sha256:[u8;32],
    pub query_sha256:[u8;32],pub replacement_sha256:[u8;32],pub replacement_bytes:usize,pub run_policy:SourceReplacementRunPolicy,
    pub matched_occurrences:usize,pub changed_scalar_ranges:usize,pub changes:Vec<SourceReplacementTextSpanChange>,pub changed_parts:usize,
    pub output_package_sha256:[u8;32],pub output_bytes:usize,pub observed_protection_parts:usize,pub observed_protection_element_visits:usize,
    pub original_selection_contiguity_verified:bool,pub outside_selected_text_atoms_exact:bool,pub output_text_span_values_verified:bool,
    pub original_control_bytes_preserved:bool,pub control_atom_replacement_qualified:bool,pub field_cached_content_edit_qualified:bool,
    pub full_protection_native_or_execution_authority:bool,
}
pub struct SourceLiteralTextAtomCandidate {artifact:PackageArtifact,receipt:SourceLiteralTextAtomReceipt}
impl fmt::Debug for SourceLiteralTextAtomCandidate {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result {f.write_str("SourceLiteralTextAtomCandidate(<redacted>; not_full_protection_or_authority)")}}
impl SourceLiteralTextAtomCandidate {
    #[must_use] pub const fn receipt(&self)->&SourceLiteralTextAtomReceipt {&self.receipt}
    /// # Errors
    /// Writer integrity only, not current service authorization or a revision commit.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError> {self.artifact.with_verified_bytes(consume)}
}
#[derive(Clone,Copy)] enum AtomEditKind {Text,PointEdge(bool),ControlBoundary,Empty}
struct AtomEdit<'a> {atom:u32,start:u32,end:u32,value:&'a str,kind:AtomEditKind}
struct PlannedSpan {element:usize,expected:TextSpan,old_slots:Vec<Range<usize>>,changed_slots:Vec<usize>,change:SourceReplacementTextSpanChange,expanded_empty:bool}

impl ImportedDocumentForms {
    /// # Errors
    /// v2 mapped body/note literal replacement; controls are retained and never editable.
    pub fn lower_literal_text_atom_candidate(&self,fresh:&[u8],query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceLiteralTextAtomCandidate,E> {
        self.reconstruct_source_for_verification(fresh).map_err(|_|E::Source)?
            .lower_literal_text_atom_candidate(self,query,scope,replacement,run_policy,limits,writer)
    }
}
impl VerifiedFormReconstruction<'_> {
    /// # Errors
    /// Reuses the exact original's call-local proof; no caller graph or trusted flags.
    pub fn lower_literal_text_atom_candidate(&self,original:&ImportedDocumentForms,query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
        run_policy:SourceReplacementRunPolicy,limits:SourceSearchLimits,writer:WriterLimits)->Result<SourceLiteralTextAtomCandidate,E> {
        let rebuilt=self.for_original(original).map_err(|_|E::Source)?;
        if query.mode!=SourceSearchMode::Literal{return Err(E::Value);}
        validate_literal_replacement(replacement)?;
        let fields=ImportedDocumentFields::import(original).map_err(|_|E::Source)?;
        let index=extract::build(original.body_structure(),limits)?;
        lower(&index,&fields,rebuilt.source().original.as_ref(),query,scope,replacement,run_policy,writer)
    }
}

fn lower(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],query:SourceSearchQuery<'_>,scope:SourceSearchScope<'_>,replacement:&str,
    run_policy:SourceReplacementRunPolicy,writer:WriterLimits)->Result<SourceLiteralTextAtomCandidate,E> {
    let found=index.find_scoped(query,scope)?;
    lower_found(index,fields,fresh,found.result(),found.scope_receipt().scope_sha256,replacement,run_policy,writer,None)
        .map(|(candidate,_)|candidate)
}
fn lower_found(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],found:&super::super::SourceSearchResult,scope_sha256:[u8;32],replacement:&str,
    run_policy:SourceReplacementRunPolicy,writer:WriterLimits,review:Option<&review::ReviewWriteContext>)->Result<(SourceLiteralTextAtomCandidate,Option<review::ReviewBodyImportReceipt>),E> {
    lower_found_with_expansions(index,fields,fresh,found,scope_sha256,replacement,run_policy,writer,review,None)
}
struct RegexExpansions<'a> {values:&'a [String],sha256:[u8;32],bytes:usize}
fn lower_found_with_expansions(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],found:&super::super::SourceSearchResult,scope_sha256:[u8;32],replacement:&str,
    run_policy:SourceReplacementRunPolicy,writer:WriterLimits,review:Option<&review::ReviewWriteContext>,expansions:Option<&RegexExpansions<'_>>)->Result<(SourceLiteralTextAtomCandidate,Option<review::ReviewBodyImportReceipt>),E> {
    lower_found_with_insertions(index,fields,fresh,found,scope_sha256,replacement,run_policy,writer,review,expansions,None)
}
fn lower_found_with_insertions(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,fresh:&[u8],found:&super::super::SourceSearchResult,scope_sha256:[u8;32],replacement:&str,
    run_policy:SourceReplacementRunPolicy,writer:WriterLimits,review:Option<&review::ReviewWriteContext>,expansions:Option<&RegexExpansions<'_>>,insertions:Option<&regex::insertions::Insertions>)->Result<(SourceLiteralTextAtomCandidate,Option<review::ReviewBodyImportReceipt>),E> {
    if found.matches().is_empty(){return Err(E::NoMatches);}
    if expansions.is_some_and(|e|e.values.len()!=found.matches().len()){return Err(E::Selection);}
    let source=index.original.source();let mut used=BTreeSet::new();let mut leaves:BTreeMap<usize,Vec<AtomEdit<'_>>>=BTreeMap::new();let mut range_count=0_usize;
    for (ordinal,m) in found.matches().iter().enumerate() {
        let replacement=expansions.map_or(replacement,|e|e.values[ordinal].as_str());
        if m.zero_width&&let Some(insertions)=insertions {
            let caret=*insertions.carets.get(&ordinal).ok_or(E::Selection)?;
            let(atom,scalar,kind)=match caret {
                regex::insertions::Caret::Point {point,after}=>(point.atom,point.scalar,AtomEditKind::PointEdge(after)),
                regex::insertions::Caret::Empty {..}=>(0,0,AtomEditKind::Empty),
            };
            range_count=range_count.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            leaves.entry(caret.segment()).or_default().push(AtomEdit {atom,start:scalar,end:scalar,value:replacement,kind});continue;
        }
        let origins=selected_origins(index,m)?;let mut groups:Vec<(usize,u32,u32,u32)>=Vec::new();
        for origin in origins {
            if !used.insert(origin){return Err(E::Selection);}let p=index.points[origin];
            if let Some(last)=groups.last_mut(){if last.0==p.segment&&last.1==p.atom&&last.3==p.scalar {last.3+=1;continue;}}
            groups.push((p.segment,p.atom,p.scalar,p.scalar+1));
        }
        for (i,(segment,atom,start,end)) in groups.into_iter().enumerate() {
            range_count=range_count.checked_add(1).filter(|n|*n<=PatchLimits::default().config().max_intents).ok_or(E::Limit)?;
            leaves.entry(segment).or_default().push(AtomEdit {atom,start,end,value:if i==0{replacement}else{""},kind:AtomEditKind::Text});
        }
    }
    let intervals=match review {Some(review)=>review.field_intervals(source,fields)?,None=>field_intervals(source,fields)?};
    let(mut guards,mut visits,mut intents,mut plans)=(BTreeMap::new(),0_usize,Vec::new(),BTreeMap::new());
    let(mut changes,mut changed_ranges,mut output_text_bytes)=(Vec::new(),0_usize,0_usize);
    for (segment,mut edits) in leaves {
        let anchor=&index.segments[segment];let resolved=source.resolve_anchor(anchor).map_err(|_|E::Selection)?;
        let part=resolved.part();let xml=part.xml().ok_or(E::Selection)?;let element=resolved.element_index().ok_or(E::Selection)?;
        if !guards.contains_key(part.path()) {
            visits=visits.checked_add(xml.elements().len().checked_mul(2).ok_or(E::Limit)?).ok_or(E::Limit)?;
            guards.insert(part.path(),crate::document_import::structure::caption_text_batch::observed_protection(xml).map_err(|_|E::Protection)?);
        }
        if guards.get(part.path()).and_then(|g|g.get(element)).copied().ok_or(E::Selection)?{return Err(E::Protection);}
        let point=xml.elements()[element].start_tag_span().start();
        if let Some(fields)=intervals.get(part.path()) {let i=fields.partition_point(|(start,_)|*start<point);
            if i>0&&point<fields[i-1].1{return Err(E::FieldContent);}}
        let before=crate::text_flow::read_source_text_span(xml,element).map_err(|_|E::Selection)?;
        for edit in &mut edits {if let AtomEditKind::PointEdge(after)=edit.kind {
            let atom=before.atoms.get(edit.atom as usize).ok_or(E::Selection)?;
            if matches!(atom,TextAtom::Text(_)) {
                edit.start=edit.start.checked_add(u32::from(after)).ok_or(E::Limit)?;edit.end=edit.start;edit.kind=AtomEditKind::Text;
            }else{
                if edit.start!=0{return Err(E::Selection);}
                edit.atom=edit.atom.checked_add(u32::from(after)).ok_or(E::Limit)?;edit.start=0;edit.end=0;edit.kind=AtomEditKind::ControlBoundary;
            }
        }}
        edits.sort_by_key(|e|(e.atom,e.start));
        if edits.windows(2).any(|w|w[0].atom==w[1].atom&&(w[0].end>w[1].start||w[0].start==w[0].end&&w[0].start==w[1].start)){return Err(E::Selection);}
        let mut after=before.clone();let mut ranges=Vec::new();let mut changed_slots=Vec::new();
        // Original reader atom order includes controls. Map it once to control-separated source slots.
        let mut slots=Vec::new();let mut slot=0_usize;
        for atom in &before.atoms {slots.push(slot);if !matches!(atom,TextAtom::Text(_)){slot+=1;}}
        let mut first=0;let mut additions=Vec::new();let mut empty_value=None;let mut original_text_changes=0;
        while first<edits.len() {
            let atom=edits[first].atom;let mut last=first+1;while last<edits.len()&&edits[last].atom==atom{last+=1;}
            match edits[first].kind {
                AtomEditKind::Empty=>{
                    if edits.len()!=1||!before.atoms.is_empty(){return Err(E::Selection);}
                    if !edits[first].value.is_empty(){empty_value=Some(edits[first].value);after.atoms.push(TextAtom::Text(edits[first].value.to_owned()));changed_slots.push(0);}
                    first=last;continue;
                },
                AtomEditKind::ControlBoundary=>{
                    if last!=first+1{return Err(E::Selection);}
                    if !edits[first].value.is_empty(){ranges.push(TextAtomRangeReplacement::at_control_boundary(atom,edits[first].value).map_err(|_|E::Value)?);
                        additions.push((atom as usize,edits[first].value.to_owned()));changed_slots.push(*slots.get(atom as usize).unwrap_or(&slot));}
                    first=last;continue;
                },
                AtomEditKind::Text=>{},AtomEditKind::PointEdge(_)=>return Err(E::Selection),
            }
            let TextAtom::Text(value)=before.atoms.get(atom as usize).ok_or(E::Selection)? else{return Err(E::Selection);};
            let mut offsets:Vec<_>=value.char_indices().map(|(i,_)|i).collect();offsets.push(value.len());
            let mut next=String::new();let mut previous=0;let start_count=ranges.len();
            for edit in &edits[first..last] {
                let start=*offsets.get(edit.start as usize).ok_or(E::Selection)?;let end=*offsets.get(edit.end as usize).ok_or(E::Selection)?;
                if &value[start..end]==edit.value{continue;}
                append(&mut next,&value[previous..start],index.limits.0.result_bytes)?;append(&mut next,edit.value,index.limits.0.result_bytes)?;previous=end;
                ranges.push(TextAtomRangeReplacement::new(atom,edit.start,edit.end,edit.value).map_err(|_|E::Value)?);
            }
            if ranges.len()>start_count {
                append(&mut next,&value[previous..],index.limits.0.result_bytes)?;after.atoms[atom as usize]=TextAtom::Text(next);
                changed_slots.push(slots[atom as usize]);
                original_text_changes+=1;
            }first=last;
        }
        let changed_count=ranges.len()+usize::from(empty_value.is_some());if changed_count==0{continue;}
        // Boundary insertion can make two adjacent original/new text atoms; the original reader
        // merges those tokens. Construct the same canonical atom sequence before readback.
        if insertions.is_some(){regex::insertions::materialize(&mut after,additions,index.limits.0.result_bytes)?;}
        // The source reader does not materialize empty Text atoms after a complete deletion.
        after.atoms.retain(|a|!matches!(a,TextAtom::Text(v)if v.is_empty()));
        let bytes=text_bytes(&after)?;output_text_bytes=output_text_bytes.checked_add(bytes).filter(|n|*n<=index.limits.0.result_bytes).ok_or(E::Limit)?;
        changed_ranges=changed_ranges.checked_add(changed_count).ok_or(E::Limit)?;
        changed_slots.sort_unstable();changed_slots.dedup();
        let change=SourceReplacementTextSpanChange {source_text_anchor:anchor.clone(),source_span_sha256:span_sha(&before),output_span_sha256:span_sha(&after),
            output_text_bytes:bytes,changed_scalar_ranges:changed_count,changed_original_text_atoms:original_text_changes,
            preserved_controls:before.atoms.iter().filter(|a|!matches!(a,TextAtom::Text(_))).count()};
        let target=XmlElementSelector::bind(part.path(),xml,element).map_err(|_|E::Selection)?;
        if let Some(value)=empty_value{intents.push(PatchIntent::ReplaceLeafScalarRanges {target,ranges:vec![LeafTextRangeReplacement::new(0,0,value).map_err(|_|E::Value)?]});}
        else{intents.push(PatchIntent::ReplaceTextAtomScalarRanges {target,ranges});}
        let expanded_empty=empty_value.is_some()&&xml.elements()[element].is_empty();
        let old_slots=if expanded_empty{vec![readback::empty_shell(xml,element)?]}else{readback::slots(xml,element)?};
        changes.push(change.clone());plans.entry(part.path()).or_insert_with(Vec::new).push(PlannedSpan {element,expected:after,old_slots,changed_slots,change,expanded_empty});
    }
    if intents.is_empty(){return Err(E::NoChange);}
    let (artifact,output_review)=readback::build(source,fresh,&intents,&plans,writer,review)?;
    let receipt=SourceLiteralTextAtomReceipt {profile:if insertions.is_some(){regex::SOURCE_REGEX_INSERTION_ATOM_PROFILE}else if expansions.is_some(){regex::SOURCE_REGEX_TEXT_ATOM_PROFILE}else if review.is_some(){review::SOURCE_REVIEW_LITERAL_PROFILE}else{SOURCE_LITERAL_TEXT_ATOM_PROFILE},source_package_sha256:source.receipt().source_package_sha256,
        source_index_sha256:index.receipt.index_sha256,scope_sha256,query_sha256:found.query_sha256(),
        replacement_sha256:expansions.map_or_else(||Sha256::digest(replacement.as_bytes()).into(),|e|e.sha256),replacement_bytes:expansions.map_or(replacement.len(),|e|e.bytes),run_policy,
        matched_occurrences:found.matches().len(),changed_scalar_ranges:changed_ranges,changes,changed_parts:plans.len(),
        output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),observed_protection_parts:guards.len(),observed_protection_element_visits:visits,
        original_selection_contiguity_verified:true,outside_selected_text_atoms_exact:true,output_text_span_values_verified:true,
        original_control_bytes_preserved:true,control_atom_replacement_qualified:false,field_cached_content_edit_qualified:false,full_protection_native_or_execution_authority:false};
    let mut count=Output {bytes:None,length:0,maximum:index.limits.0.result_bytes};serde_json::to_writer(&mut count,&receipt).map_err(|_|E::Limit)?;
    Ok((SourceLiteralTextAtomCandidate {artifact,receipt},output_review))
}
fn text_bytes(span:&TextSpan)->Result<usize,E> {
    span.atoms.iter().try_fold(0_usize,|n,a|n.checked_add(match a {TextAtom::Text(v)=>v.len(),_=>0}).ok_or(E::Limit))
}
fn span_sha(span:&TextSpan)->[u8;32] {
    let mut sha=Sha256::new();sha.update(b"hwpx-agent.source-text-span/atom-sequence-v1");
    if let Some(id)=span.character_style_id_ref {sha.update([1]);sha.update(id.to_le_bytes());}else{sha.update([0]);}
    sha.update((span.atoms.len()as u64).to_le_bytes());
    for atom in &span.atoms {match atom {
        TextAtom::Text(value)=>{sha.update([0]);sha.update((value.len()as u64).to_le_bytes());sha.update(value.as_bytes());},
        TextAtom::Tab {width,leader,tab_type}=>{sha.update([1]);for n in [width,leader,tab_type]{sha.update(n.to_le_bytes());}},
        TextAtom::LineBreak=>sha.update([2]),
    }}sha.finalize().into()
}
