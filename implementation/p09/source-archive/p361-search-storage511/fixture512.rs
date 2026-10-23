//! Small real-package inputs for every schema in the current closed mutation table.
use super::*;
#[path="../../../../hwpx-package/tests/support/search_definition_fixture.rs"] pub mod definition;
pub fn p(id:u32,text:&str)->String {format!("<hp:p id='{id}' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p>")}
pub fn source(i:usize)->Result<Vec<u8>,Box<dyn Error>> {
    let body=match i {
        7=>p(1,"K").replace("<hp:t>","<hp:t charStyleIDRef='0'>"),
        9|10=>p(1,"a&#x300;"),11=>p(1,"ab"),12=>p(1,"a"),13=>p(1,"A  B"),14=>p(1,"K<hp:tab width='1' leader='0' type='0'/>Y"),
        15=>p(1,"K").replace("</hp:run>","<hp:ctrl><hp:autoNum num='2' numType='PICTURE'><hp:autoNumFormat type='DIGIT' userChar='' prefixChar='' suffixChar='' supscript='0'/></hp:autoNum></hp:ctrl></hp:run>"),
        16|17=>p(1,"Z")+&p(2,"B")+&p(3,"A"),_=>p(1,"K"),
    };definition::package(&body)
}
pub fn request(i:usize,s:&StoredFixture,bytes:&[u8])->Result<Value,Box<dyn Error>> {
    let mut v=envelope(s,bytes)?;v["schema_version"]=json!(SCHEMAS.get(i).ok_or("family")?);
    v["operation"]=json!({"kind":"replace_literal","query":"K","replacement":"X","case_sensitive":true,"whole_word":false,
        "max_replacements":100,"run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});
    if i<3 {v.as_object_mut().ok_or("request")?.remove("selector");v["scope"]=json!({"kind":"mapped_document","paragraph_handles":[]});}
    if i<2 {v["operation"].as_object_mut().ok_or("operation")?.remove("review_policy");}
    match i {
        4|5=>{v["operation"]["kind"]=json!("replace_regex");v["operation"]["regex"]=json!(true);
            if i==5 {v["operation"]["query"]=json!("^");v["operation"]["insertion_policy"]=json!("right_original_point_else_left_first_empty_text");}},
        6..=8=>{let(kind,axis)=match i {6=>("replace_character_property","run_character_property"),7=>("replace_text_character_style","text_character_style"),_=>("replace_paragraph_style_reference","paragraph_property")};
            v["operation"]=json!({"kind":kind,"query":"K","regex":false,"case_sensitive":true,"whole_word":false,"max_replacements":100,
                "style_filter":{"kind":"declared","filter":{axis:0}},"replacement":{"axis":axis,"declaration_id":1},"review_policy":policy(true,true)});
            if i==8{v["operation"]["extent"]=json!("whole_matched_paragraph_within_scope");}},
        9=>v["operation"]=json!({"kind":"normalize_unicode_scope","form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)}),
        10..=13=>{v["operation"]=json!({"kind":"normalize_unicode_matches","query":"(?s:.+)","regex":true,"case_sensitive":true,"whole_word":false,"max_matches":100,
            "form":"nfc","run_policy":"first_original_run_retain_all_runs","review_policy":policy(true,true)});
            if i>=11 {let op=v["operation"].as_object_mut().ok_or("operation")?;op.remove("form");
                match i {11=>{op.remove("run_policy");op.insert("kind".into(),json!("convert_case_matches"));op.insert("mode".into(),json!("uppercase"));op.insert("case_policy".into(),json!("unicode_default_each_matched_text_group"));},
                    12=>{op.insert("kind".into(),json!("convert_width_matches"));op.insert("mode".into(),json!("fullwidth"));op.insert("width_policy".into(),json!("unicode17_width_pairs_with_kana_pairs"));},
                    _=>{op.insert("kind".into(),json!("normalize_whitespace_matches"));op.insert("whitespace_policy".into(),json!({"text":"ascii_space","tabs":true,"line_breaks":true,"sequence":"collapse_each_matched_sequence","output":{"spaces":{"count":1}}}));}}}},
        14=>v["operation"]=json!({"kind":"replace_text_controls","control_kind":"tab","max_replacements":100,"output":[{"kind":"text","value":"X"}],"review_policy":policy(true,true)}),
        15=>v["operation"]=json!({"kind":"replace_number_controls","control_kind":"auto_number","max_replacements":100,"stored_number":9,"format":{"kind":"preserve"},"review_policy":policy(true,true)}),
        16|17=>v["operation"]=json!({"kind":if i==16{"sort_sibling_paragraphs"}else{"sort_paragraph_groups"},
            "sort_spec":{"direction":"ascending","comparison":"nfc_unicode_scalar_lexicographic","max_comparison_bytes":1048576},"review_policy":policy(false,false)}),
        18|19=>{
            let header=definition::header()?;let catalog=hwpx_package::CharacterStyleCatalogReader::read(header.as_bytes(),Default::default())?;
            let id=catalog.styles.first().ok_or("char0")?.font_refs.hangul;
            let name=&catalog.font_faces.iter().find(|f|f.language==hwpx_package::LanguageSlot::Hangul).ok_or("hangul")?.fonts.get(id as usize).ok_or("font")?.face;
            v["operation"]=json!({"kind":"replace_fonts","query":name,"replacement":"Storage Test Font","regex":false,"case_sensitive":true,"whole_word":false,
                "languages":["hangul"],"axis":"run_property","max_changed_scalars":100,"review_policy":policy(true,true)});
            if i==19{v["operation"]["preview_only"]=json!(false);v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"run_character_property":0}});}
        },
        20|21=>{v["operation"]=json!({"kind":"replace_named_paragraph_styles","query":"Normal","replacement":"Body","regex":false,"case_sensitive":true,"whole_word":false,
            "name_axis":"english_name","max_changed_paragraphs":100,"review_policy":policy(true,true),"preview_only":false});
            if i==21{v["operation"]["style_filter"]=json!({"kind":"declared","filter":{"paragraph_property":0}});}},
        22=>v["operation"]=json!({"kind":"mask_selected_personal_info","mask_policy":"per_original_scalar_preserve_slots","max_changed_components":10000,"review_policy":policy(true,true),"preview_only":false}),
        _=>{},
    }Ok(v)
}
