//! Focused v3 product and affected v1/v2/shared-owner cases, never the full stored suite.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="review_literal_product/actual_import.rs"]
mod actual_import;
