//! Read-only identity/source projection from the original strictly parsed request.
macro_rules! lookup_request_fields {
    ($r:ident,root)=>{&$r};
    ($r:ident,$field:ident)=>{&$r.$field};
}
macro_rules! lookup_request_scoped {
    (normal,$r:ident,$scope:ident)=>{$r.scoped_sha($scope)};
    (atoms,$r:ident,$scope:ident)=>{$r.scoped_sha_profile($scope,LITERAL_TEXT_ATOM_PRODUCT_REQUEST_SCHEMA)};
}
macro_rules! lookup_request_preview {
    (no_preview,$r:ident)=>{false};
    (mutation,$r:ident)=>{$r.operation.preview_only};
}
// Parse with the exact existing family parser; no source, matcher, compiler, key claim or route permit.
macro_rules! search_lookup_product {
    ($ty:ident,$parser:expr,$fields:ident,$profile:ident,$mode:ident)=>{
        impl $ty {
            pub(crate) fn prepare_request_lookup_json<R,B,S,V>(provider:&$crate::form_stored_provider::StoredFormProvider<'_,R,B,S,V>,raw:&[u8])
                ->Result<$crate::form_product_request::stored_operations::compiled_search::request_lookup::PreparedSearchRequestLookup,
                    $crate::form_product_request::stored_operations::compiled_search::request_lookup::SearchRequestLookupError>
            where R:artifact_service::ArtifactMetadataRepository,B:artifact_service::EncryptedBlobStore,S:artifact_service::ArtifactScanner,V:revision_service::RevisionRepository {
                use $crate::form_product_request::stored_operations::compiled_search::request_lookup::{PreparedSearchRequestLookup,SearchRequestLookupError as LookupError};
                let request=($parser)(raw).map_err(|_|LookupError::Request)?;
                if lookup_request_preview!($mode,request){return Err(LookupError::Kind);}
                let view=lookup_request_fields!(request,$fields);
                let scope=provider.source_search_product_scope(&view.project_id,&view.document_id)?;
                let canonical=request.canonical_sha().map_err(|_|LookupError::Request)?;
                let scoped=lookup_request_scoped!($profile,request,scope).map_err(|_|LookupError::Request)?;
                let source=artifact_service::ContentDigest::parse(&view.expected_source_package_sha256).map_err(|_|LookupError::Request)?;
                let head=view.head().map_err(|_|LookupError::Request)?;
                PreparedSearchRequestLookup::bind(provider,&view.project_id,&view.document_id,&view.idempotency_key,&canonical,&scoped,source,head,scope)
            }
        }
    }
}
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
