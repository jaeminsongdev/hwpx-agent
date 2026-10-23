//! New strict review-selector products and20 unchanged v5/v3 cases in one integration binary.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="review_selector_product/actual_import.rs"] mod actual_import;
