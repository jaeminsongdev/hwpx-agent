//! Crate-private immutable source borrows, not an alternate authorized byte accessor.
macro_rules! compiler_source {
    ($ty:ident) => {
        impl $ty<'_> {
            pub(crate) fn compiler_source(&self) -> &$crate::form_stored_provider::actual_import::StoredImportedDocumentForms { &self.source }
        }
    };
    ($ty:ident, style) => {
        compiler_source!($ty);
        impl $ty<'_> {
            pub(crate) fn compiler_splices(&self) -> &hwpx_package::document_import::search::replacement::atoms::styles::intents::SourceStyleSpliceInventory { self.output.splice_inventory() }
        }
    };
}
