//! Direct OUTLINE declaration -> exact represented paragraph presence, not effective headings or Native numbering/navigation.
use super::{hash_json,ImportedDocumentStructure,ReferenceTargetImportError as E};
use std::{collections::BTreeMap,fmt,io};
use domain_ir::{DocumentGraphLimits,Flow,LogicalId,Node,ReferenceAuxiliaryLimits,ReferenceTargetKind,ValidationTarget};
use serde::Serialize;
use crate::document_import::ImportedSourcePart;
use crate::{HANCOM_2020_HEAD_NAMESPACE as HH,HANCOM_2020_PARAGRAPH_NAMESPACE as HP,
    PreservingXmlDocument,XmlElementToken};
const XMLNS:&str="http://www.w3.org/2000/xmlns/";
pub const REFERENCE_HEADING_TARGET_PROFILE:&str="hwpx-agent.source-direct-outline-targets/v1";
pub mod declarations702;

#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct SourceHeadingTargetObservation{
    pub paragraph_id:LogicalId,pub paragraph_property_id:u32,pub source_numbering_id_ref:u32,pub raw_source_level:u32,
    pub paragraph_anchor_sha256:[u8;32],pub paragraph_definition_sha256:[u8;32],pub heading_declaration_sha256:[u8;32],
}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct ReferenceHeadingTargetReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub source_provenance_sha256:[u8;32],pub structure_graph_sha256:[u8;32],
    pub header_sha256:[u8;32],pub inventory_sha256:[u8;32],pub paragraph_definitions:usize,pub outline_definitions:usize,
    pub represented_paragraphs:usize,pub paragraphs_without_direct_property_reference:usize,pub heading_targets:usize,
    pub effective_style_cascade_qualified:bool,pub native_number_or_navigation_qualified:bool,pub complete_reference_state_qualified:bool,
}
pub struct ImportedReferenceHeadingTargets<'a>{source:&'a ImportedDocumentStructure,targets:Vec<ValidationTarget>,
    observations:Vec<SourceHeadingTargetObservation>,receipt:ReferenceHeadingTargetReceipt,maximum:usize}
impl fmt::Debug for ImportedReferenceHeadingTargets<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{
    f.debug_struct("ImportedReferenceHeadingTargets").field("source_direct_outline_targets",&self.targets.len()).finish_non_exhaustive()
}}
#[derive(Clone,Copy)]struct Definition{outline:bool,id_ref:u32,level:u32,paragraph_sha:[u8;32],heading_sha:[u8;32]}
fn named(node:&XmlElementToken,namespace:&str,local:&str)->bool{node.name().namespace()==Some(namespace)&&node.name().local_name()==local}
fn attr<'a>(node:&'a XmlElementToken,key:&str)->Option<&'a str>{node.attributes().iter()
    .find(|a|a.name().namespace().is_none()&&a.name().local_name()==key).map(|a|a.semantic_value())}
fn number(raw:&str)->Result<u32,E>{
    if raw.is_empty()||raw.len()>10||!raw.bytes().all(|b|b.is_ascii_digit()){return Err(E::Binding);}raw.parse().map_err(|_|E::Binding)
}
fn one(xml:&PreservingXmlDocument,parent:usize,local:&str)->Result<usize,E>{
    let mut found=None;let mut child=xml.elements()[parent].first_child();
    while let Some(index)=child{let node=&xml.elements()[index];child=node.next_sibling();
        if named(node,HH,local){if found.replace(index).is_some(){return Err(E::Binding);}}}
    found.ok_or(E::Binding)
}
fn header(source:&ImportedDocumentStructure,maximum:usize)->Result<(&ImportedSourcePart,BTreeMap<u32,Option<Definition>>),E>{
    let part=source.source().parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or(E::Binding)?;
    let xml=part.xml().ok_or(E::Binding)?;if !named(&xml.elements()[xml.root_element()],HH,"head"){return Err(E::Binding);}
    let refs=one(xml,xml.root_element(),"refList")?;let properties=one(xml,refs,"paraProperties")?;
    let mut definitions=BTreeMap::new();let mut observed_headings=0usize;
    for(index,node)in xml.elements().iter().enumerate(){
        if !named(node,HH,"paraPr"){continue;}
        if node.parent()!=Some(properties){return Err(E::Coverage);}
        if definitions.len()>=maximum{return Err(E::Limit);}let id=number(attr(node,"id").ok_or(E::Binding)?)?;
        let mut heading=None;let mut child=node.first_child();
        while let Some(i)=child{let e=&xml.elements()[i];child=e.next_sibling();if named(e,HH,"heading"){
            if heading.replace(i).is_some(){return Err(E::Binding);}}}
        let declaration=if let Some(i)=heading{
            let e=&xml.elements()[i];observed_headings=observed_headings.checked_add(1).ok_or(E::Limit)?;
            if e.first_child().is_some()||e.attributes().iter().any(|a|a.name().namespace()!=Some(XMLNS)
                &&(a.name().namespace().is_some()||!matches!(a.name().local_name(),"type"|"idRef"|"level"))){return Err(E::Binding);}
            if let Some(span)=e.content_span(){let empty=xml.with_source_bytes(|bytes|bytes[span.start()..span.end()].iter().all(|b|b.is_ascii_whitespace()));
                if !empty{return Err(E::Binding);}}
            let outline=match attr(e,"type").ok_or(E::Binding)?{"OUTLINE"=>true,"NONE"|"NUMBER"|"BULLET"=>false,_=>return Err(E::Binding)};
            Some(Definition{outline,id_ref:number(attr(e,"idRef").ok_or(E::Binding)?)?,level:number(attr(e,"level").ok_or(E::Binding)?)?,
                paragraph_sha:part.element_anchor(index).ok_or(E::Binding)?.fingerprint_sha256,
                heading_sha:part.element_anchor(i).ok_or(E::Binding)?.fingerprint_sha256})
        }else{None};
        if definitions.insert(id,declaration).is_some(){return Err(E::Binding);}
    }
    if xml.elements().iter().filter(|e|named(e,HH,"heading")).count()!=observed_headings{return Err(E::Coverage);}
    Ok((part,definitions))
}
struct Collector<'a>{source:&'a ImportedDocumentStructure,definitions:&'a BTreeMap<u32,Option<Definition>>,maximum:usize,output:usize,
    targets:Vec<ValidationTarget>,observations:Vec<SourceHeadingTargetObservation>,seen:BTreeMap<LogicalId,bool>,visited:usize,missing:usize}
impl Collector<'_>{
    fn flow(&mut self,flow:&Flow,depth:usize)->Result<(),E>{
        if depth>DocumentGraphLimits::default().max_depth{return Err(E::Limit);}
        for node in &flow.children{match node{
            Node::Paragraph(p)=>{
                self.visited=self.visited.checked_add(1).filter(|n|*n<=self.maximum).ok_or(E::Limit)?;
                let anchor=p.common.source_anchor.as_ref().ok_or(E::Binding)?;let resolved=self.source.source().resolve_anchor(anchor).map_err(|_|E::Binding)?;
                let element=resolved.element().ok_or(E::Binding)?;if !named(element,HP,"p"){return Err(E::Binding);}
                let Some(raw)=attr(element,"paraPrIDRef")else{self.missing+=1;continue};let id=number(raw)?;
                let declaration=self.definitions.get(&id).ok_or(E::Binding)?;
                if let Some(d)=declaration.filter(|d|d.outline){
                    if self.targets.len()>=self.maximum||self.seen.insert(anchor.opaque_handle.clone(),false).is_some(){return Err(E::Binding);}
                    let observation=SourceHeadingTargetObservation{paragraph_id:p.common.node_id.clone(),paragraph_property_id:id,
                        source_numbering_id_ref:d.id_ref,raw_source_level:d.level,paragraph_anchor_sha256:anchor.fingerprint_sha256,
                        paragraph_definition_sha256:d.paragraph_sha,heading_declaration_sha256:d.heading_sha};
                    self.targets.push(ValidationTarget{logical_target_id:p.common.node_id.clone(),target_kind:ReferenceTargetKind::Heading,
                        anchor:None,active:true,target_state_sha256:super::super::hex_digest(hash_json(&observation,self.output)?)});
                    self.observations.push(observation);
                }
            },
            Node::Table(t)=>{for cell in &t.cells{self.flow(&cell.body,depth+1)?;}},
            Node::Drawing(d)=>self.flow(&d.children,depth+1)?,_=>{},
        }}Ok(())
    }
}
#[derive(Serialize)]struct Envelope<'a>{receipt:&'a ReferenceHeadingTargetReceipt,targets:&'a [ValidationTarget],observations:&'a [SourceHeadingTargetObservation]}
impl<'a> ImportedReferenceHeadingTargets<'a>{
    /// # Errors
    /// An unobserved header declaration model is unavailable, not an empty native heading inventory.
    /// Any actual HH heading marker invokes the strict whole-source importer; errors are never swallowed.
    pub fn for_partial_source_assessment(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Option<Self>,E>{
        if source.source().parts().iter().filter_map(|p|p.xml()).any(|xml|xml.elements().iter().any(|e|named(e,HH,"heading"))){
            Ok(Some(Self::import(source,limits)?))
        }else{Ok(None)}
    }
    /// # Errors
    /// Exact direct OUTLINE declarations and represented paragraphs, with whole-source coverage. No named-style/counter/page inference.
    pub fn import(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Self,E>{
        let config=limits.config();if source.graph().sections().len()>config.sections{return Err(E::Limit);}
        let(part,definitions)=header(source,config.items_per_kind)?;
        let mut collect=Collector{source,definitions:&definitions,maximum:config.items_per_kind,output:config.output_bytes,
            targets:Vec::new(),observations:Vec::new(),seen:BTreeMap::new(),visited:0,missing:0};
        for section in source.graph().sections(){collect.flow(&section.body,0)?;}
        for note in source.graph().notes(){collect.flow(&note.body,0)?;}
        // One whole XML scan; nonspine/header/opaque heading paragraphs may not disappear from a partial graph.
        for p in source.source().parts(){let Some(xml)=p.xml()else{continue};
            if p.path()!=part.path()&&xml.elements().iter().any(|e|named(e,HH,"heading")||named(e,HH,"paraPr")){return Err(E::Coverage);}
            for(index,e)in xml.elements().iter().enumerate(){if !named(e,HP,"p"){continue;}
                let Some(id)=attr(e,"paraPrIDRef")else{continue};let d=definitions.get(&number(id)?).ok_or(E::Binding)?;
                if d.is_some_and(|d|d.outline){let a=p.element_anchor(index).ok_or(E::Binding)?;
                    let seen=collect.seen.get_mut(&a.opaque_handle).ok_or(E::Coverage)?;if *seen{return Err(E::Binding);}*seen=true;}
            }
        }
        if collect.seen.values().any(|seen|!*seen){return Err(E::Coverage);}
        let receipt=ReferenceHeadingTargetReceipt{profile:REFERENCE_HEADING_TARGET_PROFILE,source_package_sha256:source.receipt().source_package_sha256,
            source_provenance_sha256:source.receipt().source_provenance_sha256,structure_graph_sha256:source.receipt().graph_sha256,
            header_sha256:part.anchor().fingerprint_sha256,inventory_sha256:hash_json(&(&collect.targets,&collect.observations),config.output_bytes)?,
            paragraph_definitions:definitions.len(),outline_definitions:definitions.values().filter(|d|d.is_some_and(|d|d.outline)).count(),
            represented_paragraphs:collect.visited,paragraphs_without_direct_property_reference:collect.missing,heading_targets:collect.targets.len(),
            effective_style_cascade_qualified:false,native_number_or_navigation_qualified:false,complete_reference_state_qualified:false};
        hash_json(&Envelope{receipt:&receipt,targets:&collect.targets,observations:&collect.observations},config.output_bytes)?;
        Ok(Self{source,targets:collect.targets,observations:collect.observations,receipt,maximum:config.output_bytes})
    }
    #[must_use]pub fn targets(&self)->&[ValidationTarget]{&self.targets}
    #[must_use]pub fn observations(&self)->&[SourceHeadingTargetObservation]{&self.observations}
    #[must_use]pub const fn receipt(&self)->&ReferenceHeadingTargetReceipt{&self.receipt}
    /// # Errors
    /// Whole current source/graph verification; a retained receipt is not a fresh source or service permit.
    pub fn verify_source(&self,bytes:&[u8])->Result<ReferenceHeadingTargetReceipt,E>{
        let observed=self.source.verify_source(bytes).map_err(|_|E::Binding)?;
        if observed!=*self.source.receipt(){return Err(E::Binding);}Ok(self.receipt.clone())
    }
    /// # Errors
    /// Bounded metadata without paragraph text/XML/names, not complete reference state or Native acceptance.
    pub fn canonical_json(&self)->Result<Vec<u8>,E>{
        struct Output{bytes:Vec<u8>,maximum:usize}
        impl io::Write for Output{
            fn write(&mut self,b:&[u8])->io::Result<usize>{if self.bytes.len().checked_add(b.len()).is_none_or(|n|n>self.maximum){return Err(io::Error::other("heading_target_metadata_limit"));}
                self.bytes.try_reserve(b.len()).map_err(|_|io::Error::other("heading_target_metadata_allocation"))?;self.bytes.extend_from_slice(b);Ok(b.len())}
            fn flush(&mut self)->io::Result<()>{Ok(())}
        }
        let mut out=Output{bytes:Vec::new(),maximum:self.maximum};serde_json::to_writer(&mut out,&Envelope{receipt:&self.receipt,targets:&self.targets,observations:&self.observations}).map_err(|_|E::Limit)?;Ok(out.bytes)
    }
}
