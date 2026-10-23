//! NFC with original decoded scalar provenance. No compatibility folding.
use super::{E,Unit};
use unicode_normalization::{UnicodeNormalization as _,char::{canonical_combining_class as class,compose,decompose_canonical}};
pub(super) fn nfc(source:Vec<Unit>,maximum:usize)->Result<(Vec<Unit>,usize),E> {
    let mut decomposed=Vec::new();let mut overflow=false;
    for unit in &source {decompose_canonical(unit.ch,|ch|{
        if decomposed.len()>=maximum {overflow=true;}else{decomposed.push(Unit {ch,origins:unit.origins.clone()});}
    });if overflow{return Err(E::Limit);}}
    let mut start=0;
    for i in 0..decomposed.len() {if class(decomposed[i].ch)==0 {decomposed[start..i].sort_by_key(|u|class(u.ch));start=i+1;}}
    decomposed[start..].sort_by_key(|u|class(u.ch));
    let count=decomposed.len();let mut out:Vec<Unit>=Vec::new();let mut starter:Option<usize>=None;let mut last_class=0;
    for unit in decomposed {
        let cc=class(unit.ch);
        if let Some(i)=starter {if (last_class==0||last_class<cc)&&let Some(composite)=compose(out[i].ch,unit.ch) {
            out[i].ch=composite;out[i].origins.extend(unit.origins);out[i].origins.sort_unstable();out[i].origins.dedup();continue;
        }}
        if cc==0 {starter=Some(out.len());}last_class=cc;out.push(unit);
    }
    // Independent library normalization oracle, streaming without another String.
    if !source.iter().map(|u|u.ch).nfc().eq(out.iter().map(|u|u.ch)){return Err(E::Mapping);}Ok((out,count))
}
