use super::*;
#[allow(dead_code)] #[path="../../../hwpx-package/tests/support/document_import_field_fixture.rs"] pub(crate) mod source_fixture;
mod field_ranges {pub(super) use super::source_fixture as fixture;}
#[path="../form_stored_provider/actual_import/review_selector_stored.rs"] mod review_selector_stored;
#[path="../form_stored_provider/actual_import/source_scope_product.rs"] mod source_scope_product;
#[path="../form_stored_provider/actual_import/source_search.rs"] mod source_search;
#[path="../form_stored_provider/actual_import/source_search_navigation.rs"] mod source_search_navigation;
#[path="../form_stored_provider/actual_import/review_literal_output.rs"] mod review_literal_output;
