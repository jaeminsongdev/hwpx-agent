//! Source declarations assembled with the original typed tab reader/writer.
#[allow(dead_code)] #[path="search_definition_fixture.rs"] pub mod definition;
use hwpx_package::{TabDefinitionCatalogReader,TabDefinitionCatalogWriter,TabStop,TabItem,TabStopAlignment as A,TabPositionUnit as U,LineType2 as L,PreservingXmlDocument};
use serde_json::{json,Value};
use std::error::Error;
pub fn header_from(original:&str)->Result<String,Box<dyn Error>> {
    let mut catalog=TabDefinitionCatalogReader::read(original.as_bytes(),Default::default())?;
    let first=catalog.definitions.get_mut(0).ok_or("tab0")?;first.auto_tab_left=true;first.auto_tab_right=false;
    first.stops=vec![TabStop::Direct(TabItem {position:0,alignment:A::Center,leader:L::Dash,unit:None}),
        TabStop::HwpUnitChar {current:TabItem {position:100,alignment:A::Decimal,leader:L::Dot,unit:Some(U::HwpUnit)},
            fallback:TabItem {position:201,alignment:A::Decimal,leader:L::Dot,unit:None}},
        TabStop::Direct(TabItem {position:300,alignment:A::Right,leader:L::Solid,unit:Some(U::HwpUnit)})];
    let second=catalog.definitions.get_mut(1).ok_or("tab1")?;second.auto_tab_left=false;second.auto_tab_right=true;second.stops.clear();
    let lowered=String::from_utf8(TabDefinitionCatalogWriter::lower(&catalog,Default::default())?)?;
    fn range(text:&str)->Result<std::ops::Range<usize>,Box<dyn Error>> {
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().namespace()==Some(hwpx_package::HANCOM_2020_HEAD_NAMESPACE)&&n.name().local_name()=="tabProperties").ok_or("tabs")?;
        Ok(xml.tokens()[node.start_token()].span().start()..xml.tokens()[node.end_token().ok_or("end")?].span().end())
    }
    let mut result=original.to_owned();result.replace_range(range(original)?,&lowered[range(&lowered)?]);
    let xml=PreservingXmlDocument::parse(result.as_bytes())?;let mut edits=Vec::new();
    for node in xml.elements().iter().filter(|n|n.name().namespace()==Some(hwpx_package::HANCOM_2020_HEAD_NAMESPACE)&&n.name().local_name()=="paraPr") {
        let id=node.attributes().iter().find(|a|a.name().local_name()=="id").map(|a|a.semantic_value());
        if matches!(id,Some("0"|"1")) {
            let attr=node.attributes().iter().find(|a|a.name().local_name()=="tabPrIDRef").ok_or("tab ref")?;
            edits.push((attr.value_span().start()..attr.value_span().end(),id.ok_or("id")?.to_owned()));
        }
    }
    if edits.len()!=2{return Err("two paragraph bindings".into());}
    edits.sort_by_key(|(range,_)|std::cmp::Reverse(range.start));for (range,value) in edits {result.replace_range(range,&value);}Ok(result)
}
pub fn header()->Result<String,Box<dyn Error>> {header_from(&definition::header()?)}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package_with_header(body,&header()?)}
pub fn p(id:u32,text:&str,paragraph:u32)->String {format!("<hp:p id='{id}' paraPrIDRef='{paragraph}' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn indexed(index:u32,stop:Value)->Value {json!({"stops":[{"index":index,"stop":stop}]})}
pub fn direct(index:u32,item:Value)->Value {indexed(index,json!({"kind":"direct","item":item}))}
pub fn branch(branch:&str,item:Value)->Value {indexed(1,json!({"kind":"hwp_unit_char",branch:item}))}
pub fn predicates()->Vec<(Value,Value)> {
    let mut rows=vec![(json!({"auto_tab_left":true}),json!({"auto_tab_left":false})),
        (json!({"auto_tab_right":false}),json!({"auto_tab_right":true})),(json!({"stop_count":3}),json!({"stop_count":0}))];
    for (yes,no) in[(json!({"position":0}),json!({"position":1})),(json!({"alignment":"center"}),json!({"alignment":"left"})),
        (json!({"leader":"dash"}),json!({"leader":"none"})),(json!({"unit":{"kind":"absent"}}),json!({"unit":{"kind":"present","unit":"hwp_unit"}}))] {
        rows.push((direct(0,yes),direct(0,no)));
    }
    for(name,pos,present)in[("current",100,true),("fallback",201,false)] {
        for(yes,no)in[(json!({"position":pos}),json!({"position":pos+1})),(json!({"alignment":"decimal"}),json!({"alignment":"right"})),
            (json!({"leader":"dot"}),json!({"leader":"solid"})),
            (if present{json!({"unit":{"kind":"present","unit":"hwp_unit"}})}else{json!({"unit":{"kind":"absent"}})},
             if present{json!({"unit":{"kind":"absent"}})}else{json!({"unit":{"kind":"present","unit":"hwp_unit"}})})] {rows.push((branch(name,yes),branch(name,no)));}
    }
    rows.push((direct(2,json!({"unit":{"kind":"present","unit":"hwp_unit"}})),direct(2,json!({"unit":{"kind":"absent"}}))));rows
}
