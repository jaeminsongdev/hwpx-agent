//! New regex product cases and the16 original selector-product cases, one bounded binary.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[path="regex_replacement_product/actual_import.rs"] mod actual_import;
