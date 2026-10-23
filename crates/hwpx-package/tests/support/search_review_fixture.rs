#[allow(dead_code)]
#[path="document_import_field_fixture.rs"] mod source;
pub fn body()->&'static str {"<hp:p id='1'><hp:run><hp:t>BODY K</hp:t><hp:ctrl><hp:hiddenComment><hp:subList id='hidden-list'><hp:p id='11'><hp:run><hp:t>HIDDEN K</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment></hp:ctrl><hp:ctrl><hp:fieldBegin id='17' type='MEMO' editable='0'><hp:subList id='memo-list'><hp:p id='12'><hp:run><hp:t>MEMO K</hp:t></hp:run></hp:p></hp:subList></hp:fieldBegin></hp:ctrl><hp:t>CACHE K</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='17'/></hp:ctrl><hp:t>TAIL</hp:t></hp:run></hp:p>"}
#[allow(dead_code)] // Shared fixture: some integration binaries use only body and with_body.
pub fn package()->Result<Vec<u8>,Box<dyn std::error::Error>> {source::package(body())}
pub fn with_body(body:&str)->Result<Vec<u8>,Box<dyn std::error::Error>> {source::package(body)}
