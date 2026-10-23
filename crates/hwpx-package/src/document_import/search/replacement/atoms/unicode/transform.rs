//! Bounded provenance normalization and minimal contiguous input/output closure components.
use super::*;
use unicode_normalization::{UnicodeNormalization as _,char::{canonical_combining_class as class,compose,decompose_canonical,decompose_compatible}};
struct Unit {ch:char,origins:Vec<usize>}
pub(in crate::document_import::search::replacement::atoms) struct Change {
    pub(in crate::document_import::search::replacement::atoms) input:Range<usize>,
    pub(in crate::document_import::search::replacement::atoms) value:String,
}
pub(super) fn normalize(raw:&[char],form:SourceUnicodeNormalizationForm,maximum:usize,bytes:usize)->Result<(Vec<Change>,usize),E> {
    let mut decomposed=Vec::new();let mut overflow=false;
    for(i,&ch)in raw.iter().enumerate() {
        let mut push=|ch|{if decomposed.len()>=maximum {overflow=true;}else{decomposed.push(Unit {ch,origins:vec![i]});}};
        match form {SourceUnicodeNormalizationForm::Nfc|SourceUnicodeNormalizationForm::Nfd=>decompose_canonical(ch,&mut push),
            SourceUnicodeNormalizationForm::Nfkc|SourceUnicodeNormalizationForm::Nfkd=>decompose_compatible(ch,&mut push)}
        if overflow{return Err(E::Limit);}
    }
    let mut start=0;
    for i in 0..decomposed.len(){if class(decomposed[i].ch)==0 {decomposed[start..i].sort_by_key(|u|class(u.ch));start=i+1;}}
    decomposed[start..].sort_by_key(|u|class(u.ch));let count=decomposed.len();
    let out=if matches!(form,SourceUnicodeNormalizationForm::Nfc|SourceUnicodeNormalizationForm::Nfkc) {
        let mut out:Vec<Unit>=Vec::new();let mut starter:Option<usize>=None;let mut last_class=0;
        for unit in decomposed {let cc=class(unit.ch);
            if let Some(i)=starter {if(last_class==0||last_class<cc)&&let Some(composite)=compose(out[i].ch,unit.ch) {
                out[i].ch=composite;out[i].origins.extend(unit.origins);out[i].origins.sort_unstable();out[i].origins.dedup();continue;
            }}if cc==0{starter=Some(out.len());}last_class=cc;out.push(unit);
        }out
    }else{decomposed};
    let source=raw.iter().copied();let actual=||out.iter().map(|u|u.ch);
    let exact=match form {SourceUnicodeNormalizationForm::Nfc=>source.nfc().eq(actual()),SourceUnicodeNormalizationForm::Nfd=>source.nfd().eq(actual()),
        SourceUnicodeNormalizationForm::Nfkc=>source.nfkc().eq(actual()),SourceUnicodeNormalizationForm::Nfkd=>source.nfkd().eq(actual())};
    if !exact{return Err(E::Readback);}
    let mut last=vec![None;raw.len()];let mut output_bytes=0usize;
    for(i,u)in out.iter().enumerate(){output_bytes=output_bytes.checked_add(u.ch.len_utf8()).filter(|n|*n<=bytes).ok_or(E::Limit)?;
        for &origin in &u.origins {*last.get_mut(origin).ok_or(E::Selection)?=Some(i);}}
    // Each source origin must survive. No character removal or synthetic provenance is permitted.
    if last.iter().any(Option::is_none){return Err(E::Selection);}
    let(mut a,mut b)=(0usize,0usize);let mut changes=Vec::new();
    while a<raw.len() {
        let(mut end_a,mut end_b,mut scan_a,mut scan_b)=(a+1,b,a,b);
        loop {
            while scan_a<end_a {end_b=end_b.max(last[scan_a].ok_or(E::Selection)?+1);scan_a+=1;}
            while scan_b<end_b {for &origin in &out[scan_b].origins {
                if origin<a{return Err(E::Selection);}end_a=end_a.max(origin+1);
            }scan_b+=1;}
            if scan_a==end_a&&scan_b==end_b{break;}
        }
        if !raw[a..end_a].iter().copied().eq(out[b..end_b].iter().map(|u|u.ch)) {
            let value=out[b..end_b].iter().map(|u|u.ch).collect();changes.push(Change {input:a..end_a,value});
        }a=end_a;b=end_b;
    }
    if b!=out.len(){return Err(E::Selection);}Ok((changes,count))
}
