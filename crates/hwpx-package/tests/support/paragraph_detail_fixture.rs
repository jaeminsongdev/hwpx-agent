//! Whole original packages with exact typed paragraph values, not observed rendering.
#[allow(dead_code)] #[path="search_definition_fixture.rs"] pub mod definition;
use hwpx_package::{CompatibleHeading,Heading,HeadingType,ParagraphStyleCatalogReader,ParagraphStyleCatalogWriter,
    ParagraphStyleLimits,PreservingXmlDocument,MeasurementUnit as Unit,LineSpacingType as Spacing,TextDirection,VerticalAlignment,WordBreak,LineWrap};
use std::error::Error;
pub fn heading()->CompatibleHeading {CompatibleHeading::MetaTag {current:Heading {heading_type:HeadingType::Outline,id_ref:0,level:4},
    fallback:Heading {heading_type:HeadingType::None,id_ref:0,level:0}}}
pub fn header_with_heading(heading:CompatibleHeading)->Result<String,Box<dyn Error>> {
    let original=definition::header()?;let mut catalog=ParagraphStyleCatalogReader::read(original.as_bytes(),ParagraphStyleLimits::default())?;
    let p=&mut catalog.styles[1];p.tab_property_id_ref=1;p.condense=17;p.font_line_height=true;p.snap_to_grid=false;
    p.suppress_line_numbers=true;p.checked=true;p.text_direction=Some(TextDirection::RightToLeft);p.vertical_alignment=VerticalAlignment::Bottom;p.heading=heading;
    p.break_settings.latin_word=WordBreak::Hyphenation;p.break_settings.non_latin_word=WordBreak::BreakWord;
    p.break_settings.widow_orphan=true;p.break_settings.keep_with_next=true;p.break_settings.keep_lines=false;p.break_settings.page_break_before=true;
    p.break_settings.line_wrap=LineWrap::Squeeze;p.auto_spacing.e_asian_english=true;p.auto_spacing.e_asian_number=false;
    p.layout.current.margin.intent.value=-720;p.layout.current.margin.intent.unit=Unit::Character;
    p.layout.current.margin.left.value=120;p.layout.current.margin.right.value=34;p.layout.current.margin.previous.value=56;p.layout.current.margin.next.value=78;
    p.layout.current.line_spacing.spacing_type=Spacing::Fixed;p.layout.current.line_spacing.value=1200;p.layout.current.line_spacing.unit=Unit::Character;
    p.layout.fallback.margin.intent.value=-1440;p.layout.fallback.margin.left.value=1500;p.layout.fallback.margin.right.value=68;
    p.layout.fallback.margin.previous.value=112;p.layout.fallback.margin.next.value=156;
    p.layout.fallback.line_spacing.spacing_type=Spacing::AtLeast;p.layout.fallback.line_spacing.value=1600;
    p.border.border_fill_id_ref=1;p.border.offset_left=-1;p.border.offset_right=2;p.border.offset_top=-3;p.border.offset_bottom=4;
    p.border.connect=true;p.border.ignore_margin=false;
    let lowered=String::from_utf8(ParagraphStyleCatalogWriter::lower(&catalog,ParagraphStyleLimits::default())?)?;
    fn range(text:&str)->Result<std::ops::Range<usize>,Box<dyn Error>> {
        let xml=PreservingXmlDocument::parse(text.as_bytes())?;
        let node=xml.elements().iter().find(|n|n.name().local_name()=="paraProperties").ok_or("paragraph catalog")?;
        Ok(xml.tokens()[node.start_token()].span().start()..xml.tokens()[node.end_token().ok_or("catalog end")?].span().end())
    }
    let replacement=range(&lowered)?;let target=range(&original)?;let mut header=original;
    header.replace_range(target,&lowered[replacement]);Ok(header)
}
pub fn header()->Result<String,Box<dyn Error>> {header_with_heading(heading())}
pub fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='1' styleIDRef='0'><hp:run charPrIDRef='1'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn package(body:&str)->Result<Vec<u8>,Box<dyn Error>> {definition::package_with_header(body,&header()?)}
pub fn predicates()->Vec<(serde_json::Value,serde_json::Value)> {
    use serde_json::json;
    vec![(json!({"tab_property_id_ref":1}),json!({"tab_property_id_ref":0})),(json!({"condense":17}),json!({"condense":0})),
        (json!({"font_line_height":true}),json!({"font_line_height":false})),(json!({"snap_to_grid":false}),json!({"snap_to_grid":true})),
        (json!({"suppress_line_numbers":true}),json!({"suppress_line_numbers":false})),(json!({"checked":true}),json!({"checked":false})),
        (json!({"text_direction":"right_to_left"}),json!({"text_direction":"absent"})),(json!({"vertical_alignment":"bottom"}),json!({"vertical_alignment":"baseline"})),
        (json!({"heading":{"kind":"meta_tag","current":{"heading_type":"outline","id_ref":0,"level":4}}}),
            json!({"heading":{"kind":"direct","heading":{"heading_type":"outline","id_ref":0,"level":4}}})),
        (json!({"latin_word":"hyphenation"}),json!({"latin_word":"keep_word"})),(json!({"non_latin_word":"break_word"}),json!({"non_latin_word":"keep_word"})),
        (json!({"widow_orphan":true}),json!({"widow_orphan":false})),(json!({"keep_with_next":true}),json!({"keep_with_next":false})),
        (json!({"keep_lines":false}),json!({"keep_lines":true})),(json!({"page_break_before":true}),json!({"page_break_before":false})),
        (json!({"line_wrap":"squeeze"}),json!({"line_wrap":"keep"})),(json!({"auto_spacing_english":true}),json!({"auto_spacing_english":false})),
        (json!({"auto_spacing_number":false}),json!({"auto_spacing_number":true})),
        (json!({"current_layout":{"indent":{"value":-720,"unit":"character"}}}),json!({"current_layout":{"indent":{"value":-720,"unit":"hwp_unit"}}})),
        (json!({"fallback_layout":{"left":{"value":1500,"unit":"hwp_unit"}}}),json!({"fallback_layout":{"left":{"value":120,"unit":"hwp_unit"}}})),
        (json!({"border_fill_id_ref":1}),json!({"border_fill_id_ref":2})),(json!({"border_offset_left":-1}),json!({"border_offset_left":0})),
        (json!({"border_offset_right":2}),json!({"border_offset_right":0})),(json!({"border_offset_top":-3}),json!({"border_offset_top":0})),
        (json!({"border_offset_bottom":4}),json!({"border_offset_bottom":0})),(json!({"border_connect":true}),json!({"border_connect":false})),
        (json!({"border_ignore_margin":false}),json!({"border_ignore_margin":true}))]
}
