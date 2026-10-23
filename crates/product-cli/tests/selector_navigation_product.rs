//! Ten selector-product navigation cases and seven unchanged v1-v4 navigation cases.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="selector_navigation_product/actual_import.rs"] mod actual_import;
