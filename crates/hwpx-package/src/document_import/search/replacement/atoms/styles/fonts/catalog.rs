//! Append exact source charPr copies with new IDs; retain all old definitions verbatim.
use super::*;
use crate::{CharacterStyle,CharacterStyleLimits,PatchAttributeValue,PatchText,XmlAttributeSelector};
use crate::document_import::fields::semantics::catalog::ImportedCatalogKind;
const LANGUAGES:[(L,&str);7]=[(L::Hangul,"hangul"),(L::Latin,"latin"),(L::Hanja,"hanja"),(L::Japanese,"japanese"),(L::Other,"other"),(L::Symbol,"symbol"),(L::User,"user")];
pub(super) fn remap(mut style:CharacterStyle,mapping:&BTreeMap<(L,u32),u32>)->CharacterStyle{
    for(language,value)in [(L::Hangul,&mut style.font_refs.hangul),(L::Latin,&mut style.font_refs.latin),(L::Hanja,&mut style.font_refs.hanja),
        (L::Japanese,&mut style.font_refs.japanese),(L::Other,&mut style.font_refs.other),(L::Symbol,&mut style.font_refs.symbol),(L::User,&mut style.font_refs.user)]{
        if let Some(&target)=mapping.get(&(language,*value)){*value=target;}
    }style
}
pub(super) fn clone_properties(source:&ImportedSourcePackage,original:&ImportedDocumentCatalog<'_, '_, '_>,needed:&BTreeSet<u32>,
    mapping:&BTreeMap<(L,u32),u32>,plan:&mut FontPlan,maximum:usize,inventory:&mut inventory::Builder)->Result<(Vec<PatchIntent>,BTreeMap<u32,u32>),E>{
    let header=source.parts().iter().find(|p|p.path().as_str()=="Contents/header.xml").ok_or(E::Source)?;
    let xml=header.xml().ok_or(E::Source)?;
    let declarations:BTreeMap<_,_>=original.definitions().iter().filter(|d|d.kind==ImportedCatalogKind::CharacterProperty).map(|d|(d.native_id,d)).collect();
    let total=plan.characters.styles.len().checked_add(needed.len()).filter(|n|*n<=CharacterStyleLimits::default().config().styles).ok_or(E::Limit)?;
    if needed.len()>PatchLimits::default().config().max_intents{return Err(E::Limit);}
    let last=declarations.values().last().ok_or(E::Selection)?;
    let last=source.resolve_anchor(&last.source_anchor).map_err(|_|E::Selection)?.element_index().ok_or(E::Selection)?;
    let container=xml.elements()[last].parent().ok_or(E::Selection)?;
    let count=xml.elements()[container].attributes().iter().position(|a|a.name().namespace().is_none()&&a.name().local_name()=="itemCnt").ok_or(E::Selection)?;
    let mut copies=Vec::new();let mut targets=BTreeMap::new();let mut copied_bytes=Vec::new();
    for &old in needed{
        let definition=declarations.get(&old).ok_or(E::Selection)?;
        let resolved=source.resolve_anchor(&definition.source_anchor).map_err(|_|E::Selection)?;
        if resolved.part().path()!=header.path(){return Err(E::Selection);}
        let i=resolved.element_index().ok_or(E::Selection)?;let node=&xml.elements()[i];let outer=node.outer_span().ok_or(E::Selection)?;
        let target=u32::try_from(plan.characters.styles.len()).map_err(|_|E::Limit)?;
        let mut expected=remap(plan.characters.styles.get(old as usize).filter(|s|s.id==old).ok_or(E::Selection)?.clone(),mapping);expected.id=target;
        let id=node.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()=="id").ok_or(E::Selection)?.value_span();
        let mut changes=vec![(id.start(),id.end(),target.to_string())];
        let mut children=node.first_child();let mut font_ref=None;
        while let Some(child)=children{let child_node=&xml.elements()[child];children=child_node.next_sibling();
            if child_node.name().namespace()==Some(crate::HANCOM_2020_HEAD_NAMESPACE)&&child_node.name().local_name()=="fontRef"{
                if font_ref.replace(child).is_some(){return Err(E::Selection);}
            }}
        let font_ref=&xml.elements()[font_ref.ok_or(E::Selection)?];
        for (language,name)in LANGUAGES{
            let a=font_ref.attributes().iter().find(|a|a.name().namespace().is_none()&&a.name().local_name()==name).ok_or(E::Selection)?;
            let old:u32=a.semantic_value().parse().map_err(|_|E::Selection)?;
            if let Some(&new)=mapping.get(&(language,old)){let span=a.value_span();changes.push((span.start(),span.end(),new.to_string()));}
        }
        let local:BTreeSet<_>=node.attributes().iter().filter(|a|a.is_namespace_declaration()).map(|a|a.name().qualified_name()).collect();
        let mut namespace=String::new();
        for(name,value)in super::super::render::namespaces(xml,i)?{if !local.contains(name.as_str()){
            let value=crate::patch::escape_attribute(&value,crate::XmlQuoteStyle::Double).map_err(|_|E::Value)?;
            namespace.push_str(&format!(" {name}=\"{value}\""));
        }}
        if !namespace.is_empty(){let at=node.start_name_span().end();changes.push((at,at,namespace));}
        let rendered=xml.with_source_bytes(|bytes|->Result<String,E>{
            let text=std::str::from_utf8(bytes).map_err(|_|E::Source)?;let mut copy=text[outer.start()..outer.end()].to_owned();
            changes.sort_by_key(|e|e.0);for(a,b,value)in changes.into_iter().rev(){copy.replace_range(a-outer.start()..b-outer.start(),&value);}Ok(copy)
        })?;
        plan.bytes=plan.bytes.checked_add(rendered.len()).filter(|n|*n<=maximum).ok_or(E::Limit)?;
        copied_bytes.extend_from_slice(rendered.as_bytes());copies.push(ValidatedXmlFragment::parse(rendered.as_bytes(),PatchLimits::default()).map_err(|_|E::Selection)?);
        targets.insert(old,target);plan.characters.styles.push(expected);
    }
    plan.clones=needed.len();plan.fragments=copies.len();
    let span=xml.elements()[container].attributes()[count].value_span();let insertion=xml.elements()[last].outer_span().ok_or(E::Selection)?.end();
    let edits=plan.edits.entry(header.path().clone()).or_default();
    edits.insert(span.start(),Edit{end:span.end(),bytes:total.to_string().into_bytes(),fragments:Vec::new()});
    edits.insert(insertion,Edit{end:insertion,bytes:copied_bytes,fragments:Vec::new()});
    inventory.count(header,container,count,total-needed.len(),total,&edits[&span.start()])?;
    inventory.append(header,last,needed.len(),&edits[&insertion])?;
    Ok((vec![PatchIntent::ReplaceAttribute{target:XmlAttributeSelector::bind(header.path(),xml,container,count).map_err(|_|E::Selection)?,
        value:PatchAttributeValue::Text(PatchText::new(&total.to_string()).map_err(|_|E::Value)?)},
        PatchIntent::SpliceElements{target:XmlElementSelector::bind(header.path(),xml,last).map_err(|_|E::Selection)?,position:ElementSplicePosition::After,fragments:copies}],targets))
}
