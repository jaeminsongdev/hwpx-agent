//! Twelve new stored selector cases plus the unchanged49 affected search/navigation/review cases.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="review_selector_stored/actual_import.rs"] mod actual_import;
