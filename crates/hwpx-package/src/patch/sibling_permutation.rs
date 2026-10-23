//! One exact original subtree per destination slot; same parent means identical inherited namespaces.
//! This is a byte-edit primitive, not a sorting rule, domain protection check or execution authority.
use super::{PatchError as E,PatchIntent,PatchLimits,PreservingXmlDocument};

pub(super) fn preflight(intents:&[PatchIntent],limits:PatchLimits)->Result<usize,E>{
    let mut count=intents.len();
    for intent in intents{if let PatchIntent::PermuteSiblingElements{targets,source_order}=intent{
        if targets.len()<2||targets.len()!=source_order.len(){return Err(E::ValueInvalid);}
        count=count.checked_sub(1).and_then(|n|n.checked_add(targets.len())).filter(|n|*n<=limits.config().max_intents)
            .ok_or(E::LimitExceeded{limit:"permutation_targets"})?;
    }}Ok(count)
}
pub(super) struct SourceEdit{pub start:usize,pub end:usize,pub replacement:Vec<u8>}
pub(super) fn source_edits(xml:&PreservingXmlDocument,indexes:&[usize],order:&[usize],remaining:&mut usize)->Result<Vec<SourceEdit>,E>{
    if indexes.len()<2||indexes.len()!=order.len(){return Err(E::ValueInvalid);}
    let mut seen=Vec::new();seen.try_reserve_exact(indexes.len()).map_err(|_|E::AllocationFailed)?;seen.resize(indexes.len(),false);
    for &i in order{let slot=seen.get_mut(i).ok_or(E::ValueInvalid)?;if std::mem::replace(slot,true){return Err(E::ValueInvalid);}}
    if order.iter().enumerate().all(|(i,&source)|i==source){return Err(E::ValueInvalid);}
    let mut spans=Vec::new();spans.try_reserve_exact(indexes.len()).map_err(|_|E::AllocationFailed)?;
    let mut parent=None;let mut end=0;
    for &i in indexes{
        let node=xml.elements().get(i).ok_or(E::SelectorOutOfRange)?;let actual=node.parent().ok_or(E::RootMutation)?;
        if parent.is_some_and(|parent|parent!=actual){return Err(E::ValueInvalid);}parent=Some(actual);
        let span=node.outer_span().ok_or(E::SelectorKind)?;
        if span.start()<end{return Err(E::ValueInvalid);}end=span.end();spans.push((span.start(),span.end()));
    }
    let mut bytes=0usize;
    for(destination,&source)in order.iter().enumerate(){if destination!=source{
        bytes=bytes.checked_add(spans[source].1-spans[source].0).filter(|n|*n<=*remaining).ok_or(E::LimitExceeded{limit:"permutation_bytes"})?;
    }}
    let mut edits=Vec::new();edits.try_reserve_exact(indexes.len()).map_err(|_|E::AllocationFailed)?;
    xml.with_source_bytes(|raw|->Result<(),E>{
        for(destination,&source)in order.iter().enumerate(){if destination!=source{
            let(start,end)=spans[destination];let(a,b)=spans[source];let mut replacement=Vec::new();
            replacement.try_reserve_exact(b-a).map_err(|_|E::AllocationFailed)?;replacement.extend_from_slice(raw.get(a..b).ok_or(E::SelectorOutOfRange)?);
            edits.push(SourceEdit{start,end,replacement});
        }}Ok(())
    })?;
    *remaining=remaining.checked_sub(bytes).ok_or(E::ValueInvalid)?;Ok(edits)
}
