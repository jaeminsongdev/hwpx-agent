//! New source insertion cases and only the directly affected original protected-writer suites.
#[path="document_import_regex_insertions.rs"] mod regex_insertions;
#[path="document_import_regex_replacement.rs"] mod regex_v1;
#[path="document_import_search_atom_replacement.rs"] mod atom_literal;
#[path="document_import_search_review_replacement.rs"] mod review_literal;
#[path="document_import_review_selector_replacement.rs"] mod selector_literal;
#[path="patch_text_atom_ranges.rs"] mod atom_ranges;
#[path="patch_leaf_scalar_ranges.rs"] mod leaf_ranges;
