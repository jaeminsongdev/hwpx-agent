//! Focused source-style product binary; existing tests/fixtures retain their original bodies.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
// Shared fixture exports also serve other product hosts. Only unused fixture exports are allowed here.
#[allow(dead_code,unused_imports,unused_macros)]
#[path="form_stored_provider/actual_import/character_detail_product_host.rs"] mod product_host;
