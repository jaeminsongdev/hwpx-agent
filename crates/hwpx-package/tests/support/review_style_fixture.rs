//! The exact explicit-style body used by the qualified selector-style core cases.
#[path="search_definition_fixture.rs"] pub mod definition;
#[path="review_scope_fixture.rs"] mod review;
pub fn body()->String{review::body().replace("<hp:p id='1'>","<hp:p id='1' paraPrIDRef='1' styleIDRef='1'>")
    .replace("<hp:p id='11'>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'>").replace("<hp:p id='12'>","<hp:p id='12' paraPrIDRef='1' styleIDRef='1'>")
    .replacen("<hp:run>","<hp:run charPrIDRef='1'>",1).replace("<hp:p id='11' paraPrIDRef='0' styleIDRef='0'><hp:run>","<hp:p id='11' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'>")
    .replace("<hp:p id='12' paraPrIDRef='1' styleIDRef='1'><hp:run>","<hp:p id='12' paraPrIDRef='1' styleIDRef='1'><hp:run charPrIDRef='1'>")
    .replace("<hp:t>BODY","<hp:t charStyleIDRef='1'>BODY").replace("<hp:t>HIDDEN","<hp:t charStyleIDRef='0'>HIDDEN").replace("<hp:t>MEMO","<hp:t charStyleIDRef='1'>MEMO")}
pub fn package()->Result<Vec<u8>,Box<dyn std::error::Error>>{definition::package(&body())}
pub fn with_body(body:&str)->Result<Vec<u8>,Box<dyn std::error::Error>>{definition::package(body)}
pub fn unstyled_package()->Result<Vec<u8>,Box<dyn std::error::Error>>{review::package()}
