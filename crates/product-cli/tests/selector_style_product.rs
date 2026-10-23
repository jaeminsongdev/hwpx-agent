//! Twelve new v7 style cases plus33 unchanged legacy search/navigation cases, one binary.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="selector_style_product/actual_import.rs"] mod actual_import;
