//! Read-only identity/source projection from the original strictly parsed request.
macro_rules! compiler_inventory {
    ($candidate:expr, plain) => { None };
    ($candidate:expr, style) => { Some($candidate.compiler_splices()) };
}
macro_rules! compiler_product {
    ($ty:ident, $($field:ident).+, $inventory:ident) => {
        impl $ty {
            pub(crate) fn compiler_view(&self) -> $crate::form_product_request::stored_operations::compiled_search::CompilationView<'_> {
                let request = &self.$($field).+;
                let receipt = &self.receipt;
                $crate::form_product_request::stored_operations::compiled_search::CompilationView {
                    source: self.candidate.compiler_source(), plan_id: &request.plan_id,
                    project: &request.project_id, key: &request.idempotency_key,
                    revision: &request.base_revision, document: &request.document_id, generation: request.expected_head_generation,
                    capability: receipt.capability_id, raw: &receipt.raw_request_sha256,
                    canonical: &receipt.canonical_request_sha256, scoped: &receipt.scoped_request_sha256,
                    splices: compiler_inventory!(self.candidate, $inventory),
                }
            }
        }
    };
}
