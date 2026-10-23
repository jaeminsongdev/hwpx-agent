//! Scope v5 plus existing v1-v4/search-navigation cases, not the complete stored suite.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="source_scope_product/actual_import.rs"]
mod actual_import;
