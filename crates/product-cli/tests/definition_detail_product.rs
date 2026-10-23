//! Focused v3/v4/v7 detail product routes, without the unrelated stored-provider suites.
use domain_ir::DocumentId;
use std::error::Error;
type TestResult=Result<(),Box<dyn Error>>;
include!("support/stored_source_fixture.rs");
#[allow(dead_code,unused_imports,unused_macros)]
#[path="form_stored_provider/actual_import/definition_detail_product_host.rs"] mod product_host;
