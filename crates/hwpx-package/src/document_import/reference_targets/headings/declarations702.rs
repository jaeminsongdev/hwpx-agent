//! Original declaration alternatives only. No branch, effective target or Native permit.
use super::{attr,named,number,one,E,ImportedDocumentStructure,HH,HP,XMLNS};
use crate::PreservingXmlDocument;
use domain_ir::{DocumentGraphLimits,Flow,LogicalId,Node,ReferenceAuxiliaryLimits};
use serde::Serialize;
use sha2::{Digest as _,Sha256};
use std::collections::{BTreeMap,BTreeSet};

#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SourceHeadingDeclarationType{None,Outline,Number,Bullet}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHeadingDeclarationValue{pub heading_type:SourceHeadingDeclarationType,pub id_ref:u32,pub level:u32,pub source_sha256:[u8;32]}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHeadingDeclarationBranch{pub is_default:bool,pub required_namespace_sha256:Option<[u8;32]>,pub value:SourceHeadingDeclarationValue}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",rename_all="snake_case")]
pub enum SourceHeadingDeclaration{Absent,Direct{value:SourceHeadingDeclarationValue},Conditional{branches:Vec<SourceHeadingDeclarationBranch>}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceParagraphHeadingDeclaration{pub paragraph_property_id:u32,pub paragraph_definition_sha256:[u8;32],pub declaration:SourceHeadingDeclaration}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct HeadingDeclarationReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_provenance_sha256:[u8;32],pub structure_graph_sha256:[u8;32],
    pub header_sha256:[u8;32],pub inventory_sha256:[u8;32],pub paragraph_definitions:usize,pub direct_definitions:usize,
    pub conditional_definitions:usize,pub heading_elements:usize,pub represented_paragraphs:usize,pub conditional_paragraphs:usize,
    pub selected_conditional_branch:bool,pub effective_headings_qualified:bool,pub native_or_complete_reference_state_qualified:bool,
}
/// Not deserializable or accepted as caller input. Serialized declarations are observations only.
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHeadingDeclarationInventory{pub receipt:HeadingDeclarationReceipt,pub definitions:Vec<SourceParagraphHeadingDeclaration>}

fn children(xml:&PreservingXmlDocument,index:usize)->Result<Vec<usize>,E>{
    let mut out=Vec::new();let node=&xml.elements()[index];let mut child=node.first_child();
    while let Some(i)=child{out.push(i);child=xml.elements()[i].next_sibling();}
    if let Some(content)=node.content_span(){
        let mut cursor=content.start();
        for &i in &out{let span=xml.elements()[i].outer_span().ok_or(E::Binding)?;
            if span.start()<cursor||span.end()>content.end()||!xml.with_source_bytes(|b|b[cursor..span.start()].iter().all(u8::is_ascii_whitespace)){return Err(E::Binding);}
            cursor=span.end();}
        if !xml.with_source_bytes(|b|b[cursor..content.end()].iter().all(u8::is_ascii_whitespace)){return Err(E::Binding);}
    }else if !out.is_empty(){return Err(E::Binding);}
    Ok(out)
}
fn attributes(xml:&PreservingXmlDocument,index:usize,allowed:&[(Option<&str>,&str)])->Result<(),E>{
    if xml.elements()[index].attributes().iter().any(|a|a.name().namespace()!=Some(XMLNS)
        &&!allowed.iter().any(|(ns,name)|a.name().namespace()==*ns&&a.name().local_name()==*name)){return Err(E::Binding);}Ok(())
}
fn value(part:&crate::document_import::ImportedSourcePart,index:usize,seen:&mut BTreeSet<usize>)->Result<SourceHeadingDeclarationValue,E>{
    let xml=part.xml().ok_or(E::Binding)?;let node=&xml.elements()[index];
    if !named(node,HH,"heading")||!seen.insert(index)||!children(xml,index)?.is_empty(){return Err(E::Binding);}
    attributes(xml,index,&[(None,"type"),(None,"idRef"),(None,"level")])?;
    let kind=match attr(node,"type").ok_or(E::Binding)?{"NONE"=>SourceHeadingDeclarationType::None,"OUTLINE"=>SourceHeadingDeclarationType::Outline,
        "NUMBER"=>SourceHeadingDeclarationType::Number,"BULLET"=>SourceHeadingDeclarationType::Bullet,_=>return Err(E::Binding)};
    Ok(SourceHeadingDeclarationValue{heading_type:kind,id_ref:number(attr(node,"idRef").ok_or(E::Binding)?)?,level:number(attr(node,"level").ok_or(E::Binding)?)?,
        source_sha256:part.element_anchor(index).ok_or(E::Binding)?.fingerprint_sha256})
}
fn conditional(part:&crate::document_import::ImportedSourcePart,index:usize,seen:&mut BTreeSet<usize>,limits:ReferenceAuxiliaryLimits)->Result<SourceHeadingDeclaration,E>{
    let xml=part.xml().ok_or(E::Binding)?;attributes(xml,index,&[])?;let arms=children(xml,index)?;
    if arms.len()<2||arms.len()>limits.config().items_per_kind{return Err(E::Binding);}
    let mut branches=Vec::new();let mut namespaces=BTreeSet::new();
    for(pos,arm)in arms.iter().copied().enumerate(){let node=&xml.elements()[arm];let default=pos==arms.len()-1;
        let namespace=if default{
            if !named(node,HP,"default"){return Err(E::Binding);}attributes(xml,arm,&[])?;None
        }else{
            if !named(node,HP,"case"){return Err(E::Binding);}attributes(xml,arm,&[(Some(HP),"required-namespace")])?;
            let raw=node.attributes().iter().find(|a|a.name().namespace()==Some(HP)&&a.name().local_name()=="required-namespace").ok_or(E::Binding)?.semantic_value();
            if raw.is_empty()||raw.len()>limits.config().text_bytes||!namespaces.insert(raw){return Err(E::Binding);}Some(Sha256::digest(raw.as_bytes()).into())
        };
        let inner=children(xml,arm)?;if inner.len()!=1{return Err(E::Binding);}
        branches.push(SourceHeadingDeclarationBranch{is_default:default,required_namespace_sha256:namespace,value:value(part,inner[0],seen)?});
    }
    Ok(SourceHeadingDeclaration::Conditional{branches})
}
fn potential(value:&SourceHeadingDeclaration)->bool{match value{
    SourceHeadingDeclaration::Conditional{..}=>true,SourceHeadingDeclaration::Direct{value}=>value.heading_type==SourceHeadingDeclarationType::Outline,_=>false}}
fn paragraphs(flow:&Flow,depth:usize,source:&ImportedDocumentStructure,maximum:usize,out:&mut BTreeSet<LogicalId>)->Result<(),E>{
    if depth>DocumentGraphLimits::default().max_depth{return Err(E::Limit);}
    for node in &flow.children{match node{
        Node::Paragraph(p)=>{if out.len()>=maximum{return Err(E::Limit);}let anchor=p.common.source_anchor.as_ref().ok_or(E::Binding)?;
            let resolved=source.source().resolve_anchor(anchor).map_err(|_|E::Binding)?;
            if !named(resolved.element().ok_or(E::Binding)?,HP,"p")||!out.insert(anchor.opaque_handle.clone()){return Err(E::Binding);}},
        Node::Table(t)=>{for cell in &t.cells{paragraphs(&cell.body,depth+1,source,maximum,out)?;}},
        Node::Drawing(d)=>paragraphs(&d.children,depth+1,source,maximum,out)?,_=>{},
    }}Ok(())
}
impl SourceHeadingDeclarationInventory{
    /// Keeps legacy direct-heading import and serialization unchanged. A switch
    /// containing any observed heading invokes strict alternative coverage.
    /// # Errors
    /// Invalid observed alternatives and finite source budgets remain fatal.
    pub fn observe_conditional(source:&ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Option<Self>,E>{
        for part in source.source().parts(){let Some(xml)=part.xml()else{continue};
            for node in xml.elements(){if !named(node,HH,"heading"){continue;}
                let mut parent=node.parent();let mut depth=0;
                while let Some(i)=parent{depth+=1;if depth>DocumentGraphLimits::default().max_depth{return Err(E::Limit);}
                    if named(&xml.elements()[i],HP,"switch"){return Self::observe(source,limits);}
                    parent=xml.elements()[i].parent();}
            }
        }Ok(None)
    }
    /// Whole source/header coverage; None means no observed HH heading model, never an empty target inventory.
    /// # Errors
    /// Rejects malformed/nested/missing alternatives, changed source, hidden declarations/paragraphs and budgets.
    pub fn observe(source:&ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Option<Self>,E>{
        if source.graph().sections().len()>limits.config().sections{return Err(E::Limit);}
        let any=source.source().parts().iter().filter_map(|p|p.xml()).any(|xml|xml.elements().iter().any(|e|named(e,HH,"heading")));
        if !any{return Ok(None);}
        let part=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or(E::Binding)?;
        let xml=part.xml().ok_or(E::Binding)?;if !named(&xml.elements()[xml.root_element()],HH,"head"){return Err(E::Binding);}
        let refs=one(xml,xml.root_element(),"refList")?;let properties=one(xml,refs,"paraProperties")?;
        let mut owners:BTreeMap<usize,BTreeSet<usize>>=BTreeMap::new();let mut all=BTreeSet::new();
        for(i,node)in xml.elements().iter().enumerate(){if !named(node,HH,"heading"){continue;}
            if all.len()>=limits.config().items_per_kind{return Err(E::Limit);}all.insert(i);
            let mut ancestor=i;let mut depth=0;
            loop{depth+=1;if depth>DocumentGraphLimits::default().max_depth{return Err(E::Limit);}
                let parent=xml.elements()[ancestor].parent().ok_or(E::Coverage)?;
                if named(&xml.elements()[parent],HH,"paraPr"){owners.entry(parent).or_default().insert(ancestor);break;}ancestor=parent;}
        }
        let mut definitions=Vec::new();let mut seen=BTreeSet::new();let mut ids=BTreeSet::new();
        for(i,node)in xml.elements().iter().enumerate(){if !named(node,HH,"paraPr"){continue;}
            if node.parent()!=Some(properties){return Err(E::Coverage);}if definitions.len()>=limits.config().items_per_kind{return Err(E::Limit);}
            let id=number(attr(node,"id").ok_or(E::Binding)?)?;if !ids.insert(id){return Err(E::Binding);}children(xml,i)?;
            let declaration=if let Some(roots)=owners.remove(&i){if roots.len()!=1{return Err(E::Binding);}let root=*roots.iter().next().ok_or(E::Binding)?;
                if named(&xml.elements()[root],HH,"heading"){SourceHeadingDeclaration::Direct{value:value(part,root,&mut seen)?}}
                else if named(&xml.elements()[root],HP,"switch"){conditional(part,root,&mut seen,limits)?}else{return Err(E::Coverage);}
            }else{SourceHeadingDeclaration::Absent};
            definitions.push(SourceParagraphHeadingDeclaration{paragraph_property_id:id,paragraph_definition_sha256:part.element_anchor(i).ok_or(E::Binding)?.fingerprint_sha256,declaration});
        }
        if !owners.is_empty()||seen!=all{return Err(E::Coverage);}
        let by_id:BTreeMap<_,_>=definitions.iter().map(|d|(d.paragraph_property_id,&d.declaration)).collect();
        let mut represented=BTreeSet::new();
        for section in source.graph().sections(){paragraphs(&section.body,0,source,limits.config().items_per_kind,&mut represented)?;}
        for note in source.graph().notes(){paragraphs(&note.body,0,source,limits.config().items_per_kind,&mut represented)?;}
        let mut conditional_paragraphs=0usize;
        for current in source.source().parts(){let Some(doc)=current.xml()else{continue};
            if current.path()!=part.path()&&doc.elements().iter().any(|e|named(e,HH,"heading")||named(e,HH,"paraPr")){return Err(E::Coverage);}
            for(i,node)in doc.elements().iter().enumerate(){if !named(node,HP,"p"){continue;}let Some(raw)=attr(node,"paraPrIDRef")else{continue};
                let declaration=by_id.get(&number(raw)?).ok_or(E::Binding)?;
                if potential(declaration){let anchor=current.element_anchor(i).ok_or(E::Binding)?;if !represented.contains(&anchor.opaque_handle){return Err(E::Coverage);}}
                if matches!(declaration,SourceHeadingDeclaration::Conditional{..}){conditional_paragraphs=conditional_paragraphs.checked_add(1).filter(|n|*n<=limits.config().items_per_kind).ok_or(E::Limit)?;}
            }
        }
        let receipt=HeadingDeclarationReceipt{profile:"hwpx-agent.source-heading-declaration-alternatives/unresolved-v1",
            source_package_sha256:source.receipt().source_package_sha256,source_provenance_sha256:source.receipt().source_provenance_sha256,
            structure_graph_sha256:source.receipt().graph_sha256,header_sha256:part.anchor().fingerprint_sha256,
            inventory_sha256:super::super::hash_json(&definitions,limits.config().output_bytes)?,paragraph_definitions:definitions.len(),
            direct_definitions:definitions.iter().filter(|d|matches!(d.declaration,SourceHeadingDeclaration::Direct{..})).count(),
            conditional_definitions:definitions.iter().filter(|d|matches!(d.declaration,SourceHeadingDeclaration::Conditional{..})).count(),
            heading_elements:all.len(),represented_paragraphs:represented.len(),conditional_paragraphs,
            selected_conditional_branch:false,effective_headings_qualified:false,native_or_complete_reference_state_qualified:false};
        let result=Self{receipt,definitions};super::super::hash_json(&result,limits.config().output_bytes)?;Ok(Some(result))
    }
    /// # Errors
    /// A retained declaration inventory cannot be rebound to changed bytes or a different source graph.
    pub fn verify_source(&self,source:&ImportedDocumentStructure,bytes:&[u8],limits:ReferenceAuxiliaryLimits)->Result<(),E>{
        source.verify_source(bytes).map_err(|_|E::Binding)?;
        if Self::observe(source,limits)?.as_ref()!=Some(self){return Err(E::Binding);}Ok(())
    }
}
