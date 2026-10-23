//! Explicit original typed header values, reused by core and stored-product tests.
#[allow(dead_code)] #[path="search_definition_fixture.rs"] pub mod definition;
use hwpx_package::PreservingXmlDocument;
pub fn header()->Result<String,Box<dyn std::error::Error>> {
    let header=definition::header()?;let xml=PreservingXmlDocument::parse(header.as_bytes())?;
    let node=xml.elements().iter().find(|n|n.name().local_name()=="charPr"&&n.attributes().iter().any(|a|
        a.name().local_name()=="id"&&&header[a.value_span().start()..a.value_span().end()]=="1")).ok_or("style1")?;
    let start=xml.tokens()[node.start_token()].span().start();let end=xml.tokens()[node.end_token().ok_or("end")?].span().end();
    let mut style=header[start..end].to_owned();
    for(old,new)in[("shadeColor=\"none\"","shadeColor=\"#010203\""),("useFontSpace=\"0\"","useFontSpace=\"1\""),
        ("useKerning=\"0\"","useKerning=\"1\""),("symMark=\"NONE\"","symMark=\"DOT_ABOVE\""),
        ("<hh:ratio hangul=\"100\"","<hh:ratio hangul=\"90\""),("<hh:spacing hangul=\"0\"","<hh:spacing hangul=\"-4\""),
        ("<hh:relSz hangul=\"100\"","<hh:relSz hangul=\"85\""),("<hh:offset hangul=\"0\"","<hh:offset hangul=\"2\""),
        ("<hh:underline type=\"NONE\" shape=\"SOLID\" color=\"#000000\"/>","<hh:underline type=\"BOTTOM\" shape=\"DOUBLE_SLIM\" color=\"#112233\"/>"),
        ("<hh:strikeout shape=\"NONE\" color=\"#000000\"/>","<hh:strikeout shape=\"DASH\" color=\"#223344\"/>"),
        ("<hh:outline type=\"NONE\"/>","<hh:outline type=\"DASH_DOT\"/>"),
        ("<hh:shadow type=\"NONE\" color=\"#B2B2B2\" offsetX=\"10\" offsetY=\"10\"/>","<hh:shadow type=\"DROP\" color=\"#334455\" offsetX=\"-2\" offsetY=\"3\"/><hh:emboss/><hh:supscript/>")] {
        if style.matches(old).count()!=1{return Err("exact detail fixture edit".into());}style=style.replace(old,new);
    }
    let mut result=header;result.replace_range(start..end,&style);Ok(result)
}
pub fn p(id:u32,text:&str,style:u32)->String {format!("<hp:p id='{id}' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='{style}'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn std::error::Error>> {definition::package_with_header(body,&header()?)}
pub fn predicates()->Vec<(serde_json::Value,serde_json::Value)> {
    use serde_json::json;
    vec![(json!({"shade_color":{"kind":"rgb","rgb":[1,2,3]}}),json!({"shade_color":{"kind":"none"}})),
        (json!({"use_font_space":true}),json!({"use_font_space":false})),(json!({"use_kerning":true}),json!({"use_kerning":false})),
        (json!({"emphasis":"dot_above"}),json!({"emphasis":"none"})),(json!({"border_fill":{"kind":"reference","id":2}}),json!({"border_fill":{"kind":"absent"}})),
        (json!({"underline_position":"bottom"}),json!({"underline_position":"top"})),(json!({"underline_shape":"double_slim"}),json!({"underline_shape":"solid"})),
        (json!({"underline_color":{"kind":"rgb","rgb":[17,34,51]}}),json!({"underline_color":{"kind":"none"}})),
        (json!({"strikeout_shape":"dash"}),json!({"strikeout_shape":"none"})),
        (json!({"strikeout_color":{"kind":"rgb","rgb":[34,51,68]}}),json!({"strikeout_color":{"kind":"rgb","rgb":[0,0,0]}})),
        (json!({"outline":"dash_dot"}),json!({"outline":"none"})),(json!({"shadow_type":"drop"}),json!({"shadow_type":"continuous"})),
        (json!({"shadow_color":{"kind":"rgb","rgb":[51,68,85]}}),json!({"shadow_color":{"kind":"none"}})),
        (json!({"shadow_offset_x":-2}),json!({"shadow_offset_x":0})),(json!({"shadow_offset_y":3}),json!({"shadow_offset_y":0})),
        (json!({"emboss":true}),json!({"emboss":false})),(json!({"engrave":false}),json!({"engrave":true})),
        (json!({"superscript":true}),json!({"superscript":false})),(json!({"subscript":false}),json!({"subscript":true})),
        (json!({"font_refs":{"hangul":0}}),json!({"font_refs":{"hangul":1}})),
        (json!({"ratios":{"hangul":90}}),json!({"ratios":{"hangul":100}})),
        (json!({"spacing":{"hangul":-4}}),json!({"spacing":{"hangul":0}})),
        (json!({"relative_sizes":{"hangul":85}}),json!({"relative_sizes":{"hangul":100}})),
        (json!({"offsets":{"hangul":2}}),json!({"offsets":{"hangul":0}}))]
}
