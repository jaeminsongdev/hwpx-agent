//! Whole-string authority plus scalar provenance partition; no older regex property tables.
use super::*;
use crate::document_import::search::Point;
use super::super::unicode::transform::Change;
fn width(ch:char,mode:SourceCaseMode)->(usize,usize) {
    let add=|(n,b),c:char|(n+1,b+c.len_utf8());
    match mode{SourceCaseMode::Uppercase=>ch.to_uppercase().fold((0,0),add),SourceCaseMode::Lowercase=>ch.to_lowercase().fold((0,0),add)}
}
pub(super) fn convert(index:&SourceTextIndex<'_>,raw:&[char],ids:&[usize],mode:SourceCaseMode,maximum:usize,bytes:usize)->Result<(Vec<Change>,usize),E> {
    if raw.len()!=ids.len(){return Err(E::Selection);}let(mut scalars,mut length)=(0usize,0usize);
    // Exact size preflight before allocating the whole-string result. Final sigma keeps width.
    for &ch in raw{let(n,b)=width(ch,mode);scalars=scalars.checked_add(n).filter(|n|*n<=maximum).ok_or(E::Limit)?;
        length=length.checked_add(b).filter(|n|*n<=bytes).ok_or(E::Limit)?;}
    let source: String=raw.iter().collect();let mapped=match mode{SourceCaseMode::Uppercase=>source.to_uppercase(),SourceCaseMode::Lowercase=>source.to_lowercase()};
    if mapped.len()!=length{return Err(E::Readback);}let mut output=mapped.chars();let mut changes:Vec<Change>=Vec::new();let mut previous=None;
    for(i,&ch)in raw.iter().enumerate(){let(n,_)=width(ch,mode);if n==0||n>3{return Err(E::Readback);}let mut value=['\0';3];
        for c in value.iter_mut().take(n){*c=output.next().ok_or(E::Readback)?;}
        let local=match mode{SourceCaseMode::Uppercase=>ch.to_uppercase().eq(value[..n].iter().copied()),
            SourceCaseMode::Lowercase=>if ch=='Σ'{n==1&&matches!(value[0],'σ'|'ς')}else{ch.to_lowercase().eq(value[..n].iter().copied())}};
        if !local{return Err(E::Readback);}let point=*index.points.get(ids[i]).ok_or(E::Selection)?;
        if n==1&&value[0]==ch{previous=None;continue;}
        let adjacent=previous.is_some_and(|p:Point|p.segment==point.segment&&p.atom==point.atom&&p.scalar.checked_add(1)==Some(point.scalar));
        if adjacent&&changes.last().is_some_and(|c|c.input.end==i){changes.last_mut().ok_or(E::Selection)?.input.end=i+1;}
        else{if changes.len()>=index.limits.0.matches{return Err(E::Limit);}changes.push(Change {input:i..i+1,value:String::new()});}
        let target=&mut changes.last_mut().ok_or(E::Selection)?.value;
        for &c in &value[..n]{let mut buf=[0u8;4];append(target,c.encode_utf8(&mut buf),bytes)?;}previous=Some(point);
    }
    if output.next().is_some(){return Err(E::Readback);}Ok((changes,scalars))
}
