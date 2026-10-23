//! Width pairs only, bounded one-pass kana fusion and same-original-atom patch coalescing.
use super::*;
use crate::document_import::search::Point;
use super::super::unicode::transform::Change;
struct Unit {input:Range<usize>,value:[char;2],len:usize,changed:bool}
fn mapped(ch:char,mode:SourceWidthMode)->Result<([char;2],usize),E>{
    match mode{
        SourceWidthMode::Fullwidth=>Ok(([table::to_full(ch).unwrap_or(ch),'\0'],1)),
        SourceWidthMode::Halfwidth=>{
            if let Some(c)=table::to_half(ch){return Ok(([c,'\0'],1));}
            if let Some((base,mark))=table::split_kana(ch){return Ok(([table::to_half(base).ok_or(E::Readback)?,table::to_half(mark).ok_or(E::Readback)?],2));}
            Ok(([ch,'\0'],1))
        }
    }
}
fn emit(index:&SourceTextIndex<'_>,raw:&[char],ids:&[usize],unit:Unit,changes:&mut Vec<Change>,previous:&mut Option<Point>,bytes:usize)->Result<(),E>{
    if raw[unit.input.clone()]==unit.value[..unit.len]{*previous=None;return Ok(());}
    let first=*index.points.get(ids[unit.input.start]).ok_or(E::Selection)?;
    let last=*index.points.get(ids[unit.input.end-1]).ok_or(E::Selection)?;
    let single_atom=first.segment==last.segment&&first.atom==last.atom&&first.scalar.checked_add(u32::try_from(unit.input.len()-1).map_err(|_|E::Limit)?)==Some(last.scalar);
    let adjacent=single_atom&&previous.is_some_and(|p|p.segment==first.segment&&p.atom==first.atom&&p.scalar.checked_add(1)==Some(first.scalar));
    if adjacent&&changes.last().is_some_and(|c|c.input.end==unit.input.start){changes.last_mut().ok_or(E::Selection)?.input.end=unit.input.end;}
    else{if changes.len()>=index.limits.0.matches{return Err(E::Limit);}changes.push(Change {input:unit.input,value:String::new()});}
    let target=&mut changes.last_mut().ok_or(E::Selection)?.value;
    for &ch in &unit.value[..unit.len]{let mut buf=[0u8;4];append(target,ch.encode_utf8(&mut buf),bytes)?;}
    *previous=if single_atom{Some(last)}else{None};Ok(())
}
pub(super) fn convert(index:&SourceTextIndex<'_>,raw:&[char],ids:&[usize],mode:SourceWidthMode,maximum:usize,bytes:usize)->Result<(Vec<Change>,usize),E>{
    if raw.len()!=ids.len(){return Err(E::Selection);}let(mut count,mut length)=(0usize,0usize);
    // Bound pre-composition work and bytes before any output accumulation. No general NFKC/NFC.
    for &ch in raw{let(value,n)=mapped(ch,mode)?;count=count.checked_add(n).filter(|n|*n<=maximum).ok_or(E::Limit)?;
        for c in &value[..n]{length=length.checked_add(c.len_utf8()).filter(|n|*n<=bytes).ok_or(E::Limit)?;}}
    let mut pending:Option<Unit>=None;let mut changes=Vec::new();let mut previous=None;
    for(i,&ch)in raw.iter().enumerate(){let(value,len)=mapped(ch,mode)?;let unit=Unit {input:i..i+1,value,len,changed:len!=1||value[0]!=ch};
        if mode==SourceWidthMode::Fullwidth&&let Some(before)=pending.as_mut(){
            if before.len==1&&unit.len==1&&(before.changed||unit.changed)&&let Some(composite)=table::compose_kana(before.value[0],unit.value[0]){
                before.input.end=i+1;before.value[0]=composite;before.changed=true;continue;
            }
        }
        if let Some(before)=pending.take(){emit(index,raw,ids,before,&mut changes,&mut previous,bytes)?;}pending=Some(unit);
    }
    if let Some(before)=pending{emit(index,raw,ids,before,&mut changes,&mut previous,bytes)?;}Ok((changes,count))
}
