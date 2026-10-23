//! Original typed writer builds distinct referenced resources; no platform or native assumption.
#[allow(dead_code)] #[path="search_definition_fixture.rs"] pub mod definition;
use hwpx_package::{ParagraphStyleCatalogReader,ParagraphStyleCatalogWriter,ParagraphStyleLimits,PreservingXmlDocument,
    BorderWidth,LineType2,Color,CenterLine,SlashType,FillBrush,WindowBrush,HatchStyle};
use std::error::Error;
pub fn header()->Result<String,Box<dyn Error>> {
    let original=definition::header()?;let mut catalog=ParagraphStyleCatalogReader::read(original.as_bytes(),Default::default())?;
    let first=&mut catalog.border_fills[0];first.three_d=true;first.shadow=false;first.center_line=CenterLine::Cross;first.break_cell_separate_line=true;
    first.slash.slash_type=SlashType::CenterAbove;first.slash.crooked=true;first.slash.is_counter=false;
    first.back_slash.slash_type=SlashType::All;first.back_slash.crooked=false;first.back_slash.is_counter=true;
    for(line,kind,width,rgb)in[(&mut first.left,LineType2::Dash,BorderWidth::Mm0_3,(1,2,3)),
        (&mut first.right,LineType2::Dot,BorderWidth::Mm0_4,(4,5,6)),(&mut first.top,LineType2::DoubleSlim,BorderWidth::Mm0_5,(7,8,9)),
        (&mut first.bottom,LineType2::DashDot,BorderWidth::Mm0_6,(10,11,12)),(&mut first.diagonal,LineType2::Solid,BorderWidth::Mm0_7,(13,14,15))] {
        line.line_type=kind;line.width=width;line.color=Color::Rgb(rgb.0,rgb.1,rgb.2);
    }
    first.fill_brush=Some(FillBrush {window:WindowBrush {face_color:Color::None,hatch_color:Some(Color::None),hatch_style:Some(HatchStyle::CrossDiagonal),alpha:0}});
    catalog.border_fills[1].fill_brush=None;
    let lowered=String::from_utf8(ParagraphStyleCatalogWriter::lower(&catalog,ParagraphStyleLimits::default())?)?;
    fn range(text:&str)->Result<std::ops::Range<usize>,Box<dyn Error>> {
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|v|v.name().local_name()=="borderFills").ok_or("border fills")?;
        Ok(xml.tokens()[node.start_token()].span().start()..xml.tokens()[node.end_token().ok_or("end")?].span().end())
    }
    let target=range(&original)?;let source=range(&lowered)?;let mut result=original;result.replace_range(target,&lowered[source]);
    let xml=PreservingXmlDocument::parse(result.as_bytes())?;let mut edits=Vec::new();
    for node in xml.elements() {
        let is_id0=|index:usize|xml.elements()[index].attributes().iter().any(|a|a.name().local_name()=="id"&&&result[a.value_span().start()..a.value_span().end()]=="0");
        let selected=node.name().local_name()=="charPr"&&node.attributes().iter().any(|a|a.name().local_name()=="id"&&&result[a.value_span().start()..a.value_span().end()]=="0")
            ||node.name().local_name()=="border"&&node.parent().is_some_and(is_id0);
        if selected {let attribute=node.attributes().iter().find(|a|a.name().local_name()=="borderFillIDRef").ok_or("border ref")?;
            edits.push(attribute.value_span().start()..attribute.value_span().end());}
    }
    if edits.len()!=2{return Err("two referenced resource fixture edits".into());}
    edits.sort_by_key(|r|std::cmp::Reverse(r.start));for target in edits{result.replace_range(target,"1");}Ok(result)
}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package_with_header(body,&header()?)}
pub fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn predicates()->Vec<(serde_json::Value,serde_json::Value)> {
    use serde_json::json;
    let mut result=vec![(json!({"three_d":true}),json!({"three_d":false})),(json!({"shadow":false}),json!({"shadow":true})),
        (json!({"center_line":"cross"}),json!({"center_line":"none"})),(json!({"break_cell_separate_line":true}),json!({"break_cell_separate_line":false}))];
    for(name,kind,crooked,counter)in[("slash","center_above",true,false),("back_slash","all",false,true)] {
        result.extend([(json!({name:{"slash_type":kind}}),json!({name:{"slash_type":"none"}})),
            (json!({name:{"crooked":crooked}}),json!({name:{"crooked":!crooked}})),(json!({name:{"is_counter":counter}}),json!({name:{"is_counter":!counter}}))]);
    }
    for(name,kind,width,rgb)in[("left","dash","mm0_3",[1,2,3]),("right","dot","mm0_4",[4,5,6]),("top","double_slim","mm0_5",[7,8,9]),
        ("bottom","dash_dot","mm0_6",[10,11,12]),("diagonal","solid","mm0_7",[13,14,15])] {
        result.extend([(json!({name:{"line_type":kind}}),json!({name:{"line_type":"none"}})),
            (json!({name:{"width":width}}),json!({name:{"width":"mm5_0"}})),(json!({name:{"rgb":rgb}}),json!({name:{"rgb":[255,255,255]}}))]);
    }
    for(yes,no)in[(json!({"face_color":{"kind":"none"}}),json!({"face_color":{"kind":"rgb","rgb":[0,0,0]}})),
        (json!({"hatch_color":{"kind":"present","color":{"kind":"none"}}}),json!({"hatch_color":{"kind":"absent"}})),
        (json!({"hatch_style":{"kind":"present","style":"cross_diagonal"}}),json!({"hatch_style":{"kind":"absent"}})),(json!({"alpha":0}),json!({"alpha":255}))] {
        result.push((json!({"fill_brush":{"kind":"window","filter":yes}}),json!({"fill_brush":{"kind":"window","filter":no}})));
    }result.push((json!({"fill_brush":{"kind":"window","filter":{"alpha":0}}}),json!({"fill_brush":{"kind":"absent"}})));result
}
