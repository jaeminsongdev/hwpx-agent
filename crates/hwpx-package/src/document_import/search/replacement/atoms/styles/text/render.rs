//! Split original text elements at exact scalar edges; retain control bytes under the old text style.
use super::*;
fn append(output:&mut String,value:&str,maximum:usize)->Result<(),E> {
    if output.len().checked_add(value.len()).is_none_or(|n|n>maximum){return Err(E::Limit);}output.push_str(value);Ok(())
}
fn tag(raw:&str,xml:&PreservingXmlDocument,text:usize,style:Option<u32>,bindings:&BTreeMap<String,String>,maximum:usize)->Result<String,E> {
    let node=&xml.elements()[text];let span=node.start_tag_span();let old=super::super::render::reference(node,"charStyleIDRef")?;
    let mut out=String::new();let mut at=span.start();
    if style!=old {
        let id=style.ok_or(E::Selection)?.to_string();
        if let Some(a)=node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="charStyleIDRef") {
            append(&mut out,&raw[at..a.value_span().start()],maximum)?;append(&mut out,&id,maximum)?;at=a.value_span().end();
        }else {append(&mut out,&raw[at..span.end()-1],maximum)?;append(&mut out,&format!(" charStyleIDRef=\"{id}\""),maximum)?;at=span.end()-1;}
    }
    append(&mut out,&raw[at..span.end()-1],maximum)?;
    let local:BTreeSet<_>=node.attributes().iter().filter(|a|a.is_namespace_declaration()).map(|a|a.name().qualified_name()).collect();
    for(name,value)in bindings {if !local.contains(name.as_str()) {
        let value=crate::patch::escape_attribute(value,crate::XmlQuoteStyle::Double).map_err(|_|E::Value)?;
        append(&mut out,&format!(" {name}=\"{value}\""),maximum)?;
    }}append(&mut out,">",maximum)?;Ok(out)
}
pub(in crate::document_import::search::replacement::atoms::styles) fn text(xml:&PreservingXmlDocument,text:usize,ranges:&[(u32,u32,u32)],target:u32,maximum:usize)->Result<Vec<String>,E> {
    let node=&xml.elements()[text];let content=node.content_span().ok_or(E::Selection)?;
    if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!="t"
        ||node.attributes().iter().any(|a|!a.is_namespace_declaration()&&!(a.name().namespace().is_none()&&a.name().local_name()=="charStyleIDRef")){return Err(E::Selection);}
    let old=super::super::render::reference(node,"charStyleIDRef")?;let bindings=super::super::render::namespaces(xml,text)?;
    let mut requested:BTreeMap<u32,Vec<u32>>=BTreeMap::new();
    for &(atom,start,end)in ranges {requested.entry(atom).or_default().extend([start,end]);}
    for edges in requested.values_mut(){edges.sort_unstable();edges.dedup();}
    let edges=crate::patch::text_atom_ranges::scalar_edges(xml,text,&requested).map_err(|_|E::Selection)?;
    let mut selected:Vec<(usize,usize)>=Vec::new();
    for &(atom,start,end)in ranges {
        let cuts=&requested[&atom];let offsets=&edges[&atom];
        let a=offsets[cuts.binary_search(&start).map_err(|_|E::Selection)?];let b=offsets[cuts.binary_search(&end).map_err(|_|E::Selection)?];
        if a>=b{return Err(E::Selection);}selected.push((a,b));
    }
    selected.sort_unstable();if selected.windows(2).any(|w|w[0].1>w[1].0){return Err(E::Selection);}
    let mut pieces:Vec<(Option<u32>,usize,usize)>=Vec::new();let mut at=content.start();
    for(a,b)in selected {
        if a<at||b>content.end(){return Err(E::Selection);}if a>at{pieces.push((old,at,a));}
        if let Some((style,_,end))=pieces.last_mut()&&*style==Some(target)&&*end==a{*end=b;}else{pieces.push((Some(target),a,b));}
        at=b;
    }
    if at<content.end(){pieces.push((old,at,content.end()));}
    if pieces.len()>PatchLimits::default().config().max_intents{return Err(E::Limit);}
    xml.with_source_bytes(|bytes|->Result<Vec<String>,E>{
        let raw=std::str::from_utf8(bytes).map_err(|_|E::Selection)?;let close=xml.tokens()[node.end_token().ok_or(E::Selection)?].span();
        let close=&raw[close.start()..close.end()];let mut result=Vec::new();let mut total=0usize;
        for(style,a,b)in pieces {
            let mut value=tag(raw,xml,text,style,&bindings,maximum)?;append(&mut value,&raw[a..b],maximum)?;append(&mut value,close,maximum)?;
            total=total.checked_add(value.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;result.push(value);
        }Ok(result)
    })
}
