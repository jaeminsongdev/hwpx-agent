//! Copy source XML slices, split only qualified text edges, retain controls once and never merge original runs.
use super::*;
pub(super) fn reference(node:&crate::XmlElementToken,name:&str)->Result<Option<u32>,E> {
    node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name)
        .map(|a|a.semantic_value().parse().map_err(|_|E::Selection)).transpose()
}
pub(super) fn namespaces(xml:&PreservingXmlDocument,run:usize)->Result<BTreeMap<String,String>,E> {
    let mut parents=Vec::new();let mut next=Some(run);
    while let Some(i)=next {if parents.len()>=128{return Err(E::Limit);}parents.push(i);next=xml.elements()[i].parent();}
    let mut bindings=BTreeMap::new();for i in parents.into_iter().rev() {for a in xml.elements()[i].attributes().iter().filter(|a|a.is_namespace_declaration()) {
        bindings.insert(a.name().qualified_name().to_owned(),a.semantic_value().to_owned());
    }}Ok(bindings)
}
fn source_chunk(raw:&str,start:usize,end:usize,overlays:&BTreeMap<usize,Edit>,maximum:usize)->Result<String,E> {
    let mut output=String::new();let mut before=start;
    for(&a,edit)in overlays.range(start..end) {
        if a<before||edit.end>end{return Err(E::Selection);}
        append(&mut output,raw.get(before..a).ok_or(E::Selection)?,maximum)?;
        append(&mut output,std::str::from_utf8(&edit.bytes).map_err(|_|E::Selection)?,maximum)?;before=edit.end;
    }
    append(&mut output,raw.get(before..end).ok_or(E::Selection)?,maximum)?;Ok(output)
}
fn tag(raw:&str,xml:&PreservingXmlDocument,run:usize,style:Option<u32>,bindings:&BTreeMap<String,String>,maximum:usize)->Result<String,E> {
    let node=&xml.elements()[run];let span=node.start_tag_span();let old=reference(node,"charPrIDRef")?;
    let mut output=String::new();let mut before=span.start();
    if style!=old {let id=style.ok_or(E::Selection)?.to_string();
        if let Some(attribute)=node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="charPrIDRef") {
            append(&mut output,&raw[before..attribute.value_span().start()],maximum)?;append(&mut output,&id,maximum)?;before=attribute.value_span().end();
        }else{append(&mut output,&raw[before..span.end()-1],maximum)?;append(&mut output,&format!(" charPrIDRef=\"{id}\""),maximum)?;before=span.end()-1;}
    }
    append(&mut output,&raw[before..span.end()-1],maximum)?;
    // Standalone fragments use the exact original in-scope namespaces. New declarations belong
    // to run shells only; text/control bytes are copied, not reserialized with guessed prefixes.
    let local:BTreeSet<_>=node.attributes().iter().filter(|a|a.is_namespace_declaration()).map(|a|a.name().qualified_name()).collect();
    for(name,value)in bindings {if !local.contains(name.as_str()) {
        let value=crate::patch::escape_attribute(value,crate::XmlQuoteStyle::Double).map_err(|_|E::Value)?;
        append(&mut output,&format!(" {name}=\"{value}\""),maximum)?;
    }}append(&mut output,">",maximum)?;Ok(output)
}
struct Groups {groups:Vec<(Option<u32>,String)>,prefix:String,maximum:usize,bytes:usize}
impl Groups {
    fn push(&mut self,style:Option<u32>,value:&str,whitespace:bool)->Result<(),E> {
        if value.is_empty(){return Ok(());}
        self.bytes=self.bytes.checked_add(value.len()).filter(|n|*n<=self.maximum).ok_or(E::Limit)?;
        if whitespace {return if let Some((_,previous))=self.groups.last_mut(){append(previous,value,self.maximum)}else{append(&mut self.prefix,value,self.maximum)};}
        if self.groups.last().is_none_or(|(previous,_)|*previous!=style) {
            self.groups.push((style,std::mem::take(&mut self.prefix)));
        }
        append(&mut self.groups.last_mut().ok_or(E::Selection)?.1,value,self.maximum)
    }
}
pub(super) fn run(xml:&PreservingXmlDocument,run:usize,leaves:&Ranges,target:u32,overlays:&BTreeMap<usize,Edit>,maximum:usize)->Result<Vec<String>,E> {
    let node=&xml.elements()[run];let content=node.content_span().ok_or(E::Selection)?;
    if node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!="run"
        ||node.attributes().iter().any(|a|!a.is_namespace_declaration()&&!(a.name().namespace().is_none()&&a.name().local_name()=="charPrIDRef")){return Err(E::Selection);}
    let old=reference(node,"charPrIDRef")?;let bindings=namespaces(xml,run)?;
    xml.with_source_bytes(|bytes|->Result<Vec<String>,E>{
        let raw=std::str::from_utf8(bytes).map_err(|_|E::Selection)?;let mut groups=Groups {groups:Vec::new(),prefix:String::new(),maximum,bytes:0};
        let mut before=content.start();let mut next=node.first_child();
        while let Some(i)=next {
            let child=&xml.elements()[i];next=child.next_sibling();let outer=child.outer_span().ok_or(E::Selection)?;
            let gap=source_chunk(raw,before,outer.start(),overlays,maximum)?;
            if !gap.chars().all(char::is_whitespace){return Err(E::Selection);}groups.push(old,&gap,true)?;
            if let Some(ranges)=leaves.get(&i) {
                if child.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||child.name().local_name()!="t"{return Err(E::Selection);}
                let content=child.content_span().ok_or(E::Selection)?;let mut requested:BTreeMap<u32,Vec<u32>>=BTreeMap::new();
                for &(atom,start,end) in ranges {let points=requested.entry(atom).or_default();points.extend([start,end]);}
                for points in requested.values_mut(){points.sort_unstable();points.dedup();}
                let edges=crate::patch::text_atom_ranges::scalar_edges(xml,i,&requested).map_err(|_|E::Selection)?;
                let mut spans=Vec::new();for &(atom,start,end)in ranges {let points=&requested[&atom];let offsets=&edges[&atom];
                    let a=offsets[points.binary_search(&start).map_err(|_|E::Selection)?];let b=offsets[points.binary_search(&end).map_err(|_|E::Selection)?];
                    if a>=b{return Err(E::Selection);}spans.push((a,b));
                }spans.sort_unstable();if spans.windows(2).any(|w|w[0].1>w[1].0){return Err(E::Selection);}
                let mut at=content.start();let open=&raw[child.start_tag_span().start()..child.start_tag_span().end()];
                let close=xml.tokens()[child.end_token().ok_or(E::Selection)?].span();let close=&raw[close.start()..close.end()];
                let wrap=|a,b|->Result<String,E>{let mut value=String::new();append(&mut value,open,maximum)?;
                    append(&mut value,&source_chunk(raw,a,b,overlays,maximum)?,maximum)?;append(&mut value,close,maximum)?;Ok(value)};
                for(a,b)in spans {
                    if a<at||b>content.end(){return Err(E::Selection);}if a>at{groups.push(old,&wrap(at,a)?,false)?;}
                    groups.push(Some(target),&wrap(a,b)?,false)?;at=b;
                }
                if at<content.end(){groups.push(old,&wrap(at,content.end())?,false)?;}
            }else{groups.push(old,&source_chunk(raw,outer.start(),outer.end(),overlays,maximum)?,false)?;}
            before=outer.end();
        }
        let gap=source_chunk(raw,before,content.end(),overlays,maximum)?;if !gap.chars().all(char::is_whitespace){return Err(E::Selection);}groups.push(old,&gap,true)?;
        if !groups.prefix.is_empty()||groups.groups.is_empty(){return Err(E::Selection);}
        let end=xml.tokens()[node.end_token().ok_or(E::Selection)?].span();let close=&raw[end.start()..end.end()];let mut result=Vec::new();let mut bytes=0usize;
        for(style,body)in groups.groups {let mut value=tag(raw,xml,run,style,&bindings,maximum)?;append(&mut value,&body,maximum)?;append(&mut value,close,maximum)?;
            bytes=bytes.checked_add(value.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;result.push(value);
        }Ok(result)
    })
}
