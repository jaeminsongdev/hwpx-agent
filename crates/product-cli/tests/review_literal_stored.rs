//! Dedicated6-case target; source fixture is shared byte-for-byte with the legacy suite.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="review_literal_stored/actual_import.rs"]
mod actual_import;
