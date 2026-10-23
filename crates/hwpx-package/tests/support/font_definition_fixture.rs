//! Explicit declaration-only font resources; no font files, installation or native evidence.
#[allow(dead_code)] #[path="search_definition_fixture.rs"] pub mod definition;
use hwpx_package::{CharacterStyleCatalogReader,CharacterStyleCatalogWriter,PreservingXmlDocument,FontType,FontFamily,
    SubstituteFont,BinaryProperty,LanguageValues};
use std::error::Error;
pub fn header()->Result<String,Box<dyn Error>> {
    let original=definition::header()?;let mut catalog=CharacterStyleCatalogReader::read(original.as_bytes(),Default::default())?;
    for group in &mut catalog.font_faces {
        let language=format!("{:?}",group.language);
        let first=&mut group.fonts[0];first.face=format!("P09.{language}.Font");first.font_type=FontType::TrueType;first.is_embedded=true;
        first.binary_item_id_ref=Some(format!("declared-font-{language}"));
        first.substitute=Some(SubstituteFont {face:format!("P09.{language}.Substitute"),font_type:FontType::Representative,
            binary_item_id_ref:Some(format!("declared-substitute-{language}"))});
        let info=first.type_info.as_mut().ok_or("type info fixture")?;info.family=FontFamily::NonRectGothic;info.serif_style=Some("declared-serif".into());
        info.weight=-7;info.proportion=12;info.contrast=-3;info.stroke_variation=4;info.arm_style=BinaryProperty::Off;
        info.letterform=BinaryProperty::On;info.midline=BinaryProperty::Off;info.x_height=BinaryProperty::On;
        let second=&mut group.fonts[1];second.face=format!("Other.{language}.Font");second.font_type=FontType::HancomFont;second.is_embedded=false;
        second.binary_item_id_ref=None;second.substitute=None;second.type_info=None;
    }
    catalog.styles[0].font_refs=LanguageValues {hangul:0,latin:0,hanja:0,japanese:0,other:0,symbol:0,user:0};
    catalog.styles[1].font_refs=LanguageValues {hangul:1,latin:1,hanja:1,japanese:1,other:1,symbol:1,user:1};
    let lowered=String::from_utf8(CharacterStyleCatalogWriter::lower(&catalog,Default::default())?)?;
    fn range(text:&str,name:&str)->Result<std::ops::Range<usize>,Box<dyn Error>> {
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()==name).ok_or("catalog subtree")?;
        Ok(xml.tokens()[node.start_token()].span().start()..xml.tokens()[node.end_token().ok_or("end")?].span().end())
    }
    let mut edits=Vec::new();for name in["fontfaces","charProperties"] {edits.push((range(&original,name)?,lowered[range(&lowered,name)?].to_owned()));}
    edits.sort_by_key(|(r,_)|std::cmp::Reverse(r.start));let mut result=original;for(target,value)in edits{result.replace_range(target,&value);}Ok(result)
}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package_with_header(body,&header()?)}
pub fn p(id:u32,text:&str,character:u32)->String {format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='{character}'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn predicates(language:&str)->Vec<(serde_json::Value,serde_json::Value)> {
    use serde_json::json;
    let name=|value:String|json!({"query":value,"regex":false,"case_sensitive":true,"whole_word":false});
    let mut values=vec![(json!({"face":name(format!("P09.{language}.Font"))}),json!({"face":name(format!("Other.{language}.Font"))})),
        (json!({"font_type":"true_type"}),json!({"font_type":"hancom_font"})),(json!({"is_embedded":true}),json!({"is_embedded":false})),
        (json!({"binary_item_id_ref":{"kind":"present","value":format!("declared-font-{language}")}}),json!({"binary_item_id_ref":{"kind":"absent"}})),
        (json!({"substitute":{"kind":"present"}}),json!({"substitute":{"kind":"absent"}})),
        (json!({"type_info":{"kind":"present"}}),json!({"type_info":{"kind":"absent"}}))];
    for(yes,no)in[(json!({"face":name(format!("P09.{language}.Substitute"))}),json!({"face":name("missing".into())})),
        (json!({"font_type":"representative"}),json!({"font_type":"true_type"})),
        (json!({"binary_item_id_ref":{"kind":"present","value":format!("declared-substitute-{language}")}}),json!({"binary_item_id_ref":{"kind":"absent"}}))] {
        values.push((json!({"substitute":{"kind":"present","filter":yes}}),json!({"substitute":{"kind":"present","filter":no}})));
    }
    for(yes,no)in[(json!({"family":"non_rect_gothic"}),json!({"family":"unknown"})),
        (json!({"serif_style":{"kind":"present","value":"declared-serif"}}),json!({"serif_style":{"kind":"absent"}})),
        (json!({"weight":-7}),json!({"weight":7})),(json!({"proportion":12}),json!({"proportion":0})),
        (json!({"contrast":-3}),json!({"contrast":3})),(json!({"stroke_variation":4}),json!({"stroke_variation":0})),
        (json!({"arm_style":false}),json!({"arm_style":true})),(json!({"letterform":true}),json!({"letterform":false})),
        (json!({"midline":false}),json!({"midline":true})),(json!({"x_height":true}),json!({"x_height":false}))] {
        values.push((json!({"type_info":{"kind":"present","filter":yes}}),json!({"type_info":{"kind":"present","filter":no}})));
    }values
}
