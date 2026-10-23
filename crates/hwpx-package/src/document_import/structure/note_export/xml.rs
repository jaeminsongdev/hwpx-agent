//! Exact subtree copies with namespace and XML lang/space closure, never caller XML.
use super::E;
use crate::{PreservingXmlDocument as Xml, XmlElementToken as Node, XmlQuoteStyle};
use std::collections::{BTreeMap,BTreeSet};
const XML_NS:&str="http://www.w3.org/XML/1998/namespace";

fn inherited_context(xml:&Xml,index:usize)->Result<BTreeMap<&str,&str>,E> {
    let node=xml.elements().get(index).ok_or(E::Source)?;
    let mut values=BTreeMap::new();let mut current=Some(index);let mut depth=0usize;
    while let Some(i)=current {
        depth=depth.checked_add(1).filter(|d|*d<=512).ok_or(E::Limit)?;
        let ancestor=xml.elements().get(i).ok_or(E::Source)?;
        for a in ancestor.attributes().iter().filter(|a|a.name().namespace()==Some(XML_NS)) {
            match a.name().local_name() {
                "lang"|"space"=>{values.entry(a.name().local_name()).or_insert(a.semantic_value());},
                // The source section/path stays in place; its base stays in scope.
                // A removed intermediate base needs URI resolution, not copying
                // only its nearest lexical value. Do not silently change links.
                "base" if i!=index&&i!=xml.root_element()=>return Err(E::InheritedContext),
                _=>{},
            }
        }
        current=ancestor.parent();
    }
    if values.get("space").is_some_and(|v|!matches!(*v,"default"|"preserve")){return Err(E::InheritedContext);}
    for a in node.attributes().iter().filter(|a|a.name().namespace()==Some(XML_NS)) {values.remove(a.name().local_name());}
    Ok(values)
}
fn context_attributes(xml:&Xml,index:usize,max:usize)->Result<(Vec<u8>,BTreeMap<&str,&str>),E> {
    let mut insert=namespace_attributes(xml,index,max)?;let extra=inherited_context(xml,index)?;
    for (name,value) in &extra {
        let escaped=crate::patch::escape_attribute(value,XmlQuoteStyle::Double).map_err(|_|E::Namespace)?;
        append(&mut insert,format!(" xml:{name}=\"{escaped}\"").as_bytes(),max)?;
    }
    Ok((insert,extra))
}
fn same_attributes(original:&Node,closed:&Node,extra:&BTreeMap<&str,&str>)->bool {
    let a:Vec<_>=original.attributes().iter().filter(|a|!a.is_namespace_declaration()).collect();
    let b:Vec<_>=closed.attributes().iter().filter(|a|!a.is_namespace_declaration()).collect();
    if b.len()!=a.len()+extra.len(){return false;}
    if !a.iter().zip(&b).all(|(x,y)|x.name()==y.name()&&x.semantic_value()==y.semantic_value()){return false;}
    b[a.len()..].iter().all(|a|a.name().namespace()==Some(XML_NS)&&extra.get(a.name().local_name())==Some(&a.semantic_value()))
}

pub(super) fn named(node:&Node,name:&str)->bool {
    node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE) && node.name().local_name()==name
}
pub(super) fn attr<'a>(node:&'a Node,name:&str)->Option<&'a str> {
    node.attributes().iter().find(|a|!a.is_namespace_declaration()&&a.name().namespace().is_none()&&a.name().local_name()==name).map(|a|a.semantic_value())
}
fn namespace_attributes(xml:&Xml,index:usize,max:usize)->Result<Vec<u8>,E> {
    let node=xml.elements().get(index).ok_or(E::Source)?;
    let mut env=BTreeMap::new();let mut parent=node.parent();let mut depth=0usize;
    while let Some(i)=parent {
        depth=depth.checked_add(1).filter(|d|*d<=512).ok_or(E::Limit)?;
        let ancestor=xml.elements().get(i).ok_or(E::Source)?;
        for a in ancestor.attributes().iter().filter(|a|a.is_namespace_declaration()) {
            env.entry(a.name().qualified_name()).or_insert(a.semantic_value());
        }
        parent=ancestor.parent();
    }
    let local:BTreeSet<_>=node.attributes().iter().filter(|a|a.is_namespace_declaration()).map(|a|a.name().qualified_name()).collect();
    let mut insert=Vec::new();
    for (name,value) in env {
        if local.contains(name){continue;}
        let escaped=crate::patch::escape_attribute(value,XmlQuoteStyle::Double).map_err(|_|E::Namespace)?;
        append(&mut insert,format!(" {name}=\"{escaped}\"").as_bytes(),max)?;
    }
    Ok(insert)
}
pub(super) fn close(xml:&Xml,index:usize,max:usize)->Result<Vec<u8>,E> {
    let node=xml.elements().get(index).ok_or(E::Source)?;
    let(insert,extra)=context_attributes(xml,index,max)?;
    let outer=node.outer_span().ok_or(E::Source)?;
    let at=node.start_tag_span().end().checked_sub(if node.is_empty(){2}else{1}).ok_or(E::Source)?;
    let bytes=xml.with_source_bytes(|source|->Result<Vec<u8>,E>{
        let mut out=Vec::new();append(&mut out,source.get(outer.start()..at).ok_or(E::Source)?,max)?;
        append(&mut out,&insert,max)?;append(&mut out,source.get(at..outer.end()).ok_or(E::Source)?,max)?;Ok(out)
    })?;
    let closed=Xml::parse(&bytes).map_err(|_|E::Namespace)?;
    // Namespace closure must not alter expanded names or any original attributes.
    let end=xml.elements().partition_point(|n|n.start_tag_span().start()<outer.end());
    if closed.elements().len()!=end-index{return Err(E::Namespace);}
    let empty=BTreeMap::new();
    for (offset,(a,b)) in xml.elements()[index..end].iter().zip(closed.elements()).enumerate() {
        if a.name()!=b.name(){return Err(E::Namespace);}
        if !same_attributes(a,b,if offset==0{&extra}else{&empty}){return Err(E::Namespace);}
    }
    Ok(bytes)
}
pub(super) fn append(out:&mut Vec<u8>,bytes:&[u8],max:usize)->Result<(),E> {
    out.len().checked_add(bytes.len()).filter(|n|*n<=max).ok_or(E::Limit)?;
    out.try_reserve(bytes.len()).map_err(|_|E::Limit)?;out.extend_from_slice(bytes);Ok(())
}
pub(super) fn replace(bytes:&[u8],start:usize,end:usize,value:&[u8],max:usize)->Result<Vec<u8>,E> {
    let mut out=Vec::new();append(&mut out,bytes.get(..start).ok_or(E::Source)?,max)?;
    append(&mut out,value,max)?;append(&mut out,bytes.get(end..).ok_or(E::Source)?,max)?;Ok(out)
}
pub(super) fn prepend_child(bytes:&[u8],child:&[u8],max:usize)->Result<Vec<u8>,E> {
    let xml=Xml::parse(bytes).map_err(|_|E::Namespace)?;let root=&xml.elements()[xml.root_element()];
    let at=root.start_tag_span().end();
    if root.is_empty(){
        let mut value=Vec::new();append(&mut value,b">",max)?;append(&mut value,child,max)?;
        append(&mut value,format!("</{}>",root.name().qualified_name()).as_bytes(),max)?;
        replace(bytes,at-2,at,&value,max)
    }else{replace(bytes,at,at,child,max)}
}
pub(super) fn section_properties_run(xml:&Xml,max:usize)->Result<Option<Vec<u8>>,E> {
    let root=xml.root_element();let mut selected=None;
    for (i,n) in xml.elements().iter().enumerate().filter(|(_,n)|named(n,"secPr")) {
        let run=n.parent().ok_or(E::Shape)?;let p=xml.elements()[run].parent().ok_or(E::Shape)?;
        if !named(&xml.elements()[run],"run")||!named(&xml.elements()[p],"p")||xml.elements()[p].parent()!=Some(root)||selected.is_some(){return Err(E::Shape);}
        selected=Some((run,i));
    }
    let Some((run,pr))=selected else{return Ok(None)};
    let node=&xml.elements()[run];let outer=node.outer_span().ok_or(E::Shape)?;
    let content=node.content_span().ok_or(E::Shape)?;let at=node.start_tag_span().end()-1;
    let(insert,extra)=context_attributes(xml,run,max)?;let properties=close(xml,pr,max)?;
    // Read only envelope spans and the selected properties. In particular, never
    // materialize or reparse the run's unselected main text/notes/objects.
    let bytes=xml.with_source_bytes(|source|->Result<Vec<u8>,E>{
        let mut out=Vec::new();append(&mut out,source.get(outer.start()..at).ok_or(E::Source)?,max)?;
        append(&mut out,&insert,max)?;append(&mut out,source.get(at..content.start()).ok_or(E::Source)?,max)?;
        append(&mut out,&properties,max)?;append(&mut out,source.get(content.end()..outer.end()).ok_or(E::Source)?,max)?;Ok(out)
    })?;
    let parsed=Xml::parse(&bytes).map_err(|_|E::Namespace)?;let next=&parsed.elements()[parsed.root_element()];
    let child=next.first_child().and_then(|i|parsed.elements().get(i)).ok_or(E::Shape)?;
    if next.name()!=node.name()||!same_attributes(node,next,&extra)||!named(child,"secPr")||child.next_sibling().is_some(){return Err(E::Namespace);}
    Ok(Some(bytes))
}
