//! Explicit actual review payloads and frozen cached field text; no native semantic claims.
#[allow(dead_code)] #[path="document_import_field_fixture.rs"] mod source;
pub fn run_body()->String {"<hp:t>BODY K K</hp:t><hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='11'><hp:run><hp:t>HIDDEN K K<hp:lineBreak/></hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:ctrl><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'><hp:parameters cnt='0'/><hp:subList><hp:p id='12'><hp:run><hp:t>MEMO K K</hp:t></hp:run></hp:p></hp:subList><hp:metaTag>{&quot;author&quot;:&quot;PRIVATE-AUTHOR&quot;}</hp:metaTag></hp:fieldBegin></hp:ctrl><hp:t>CACHE FROZEN</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL</hp:t>".into()}
pub fn body()->String {format!("<hp:p id='1'><hp:run>{}</hp:run></hp:p>",run_body())}
pub fn package()->Result<Vec<u8>,Box<dyn std::error::Error>> {with_body(&body())}
pub fn with_body(body:&str)->Result<Vec<u8>,Box<dyn std::error::Error>> {source::package(body)}
