//! Existing source reader and catalog style binder; no parallel body/field semantics.
use super::{DocumentAssemblyError as Error, ImportedDocumentCatalog};
use crate::document_import::structure::review::{
    ImportedDocumentReviewBodies, ImportedReviewBodyObservation, MAX_BYTES,
    REVIEW_BODY_IMPORT_PROFILE, REVIEW_BODY_IMPORT_SCOPE, ReviewBodyImportError,
    ReviewBodyImportReceipt, bounded_digest, bounded_digest_and_size,
};
use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, PropertyValue};
use serde::Serialize;
use std::fmt;
#[cfg(test)]
mod tests;

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct AssembledReviewBody {
    /// Complete original reader result, including explicit unverified native metadata.
    pub source: ImportedReviewBodyObservation,
    /// Same body with only the existing catalog binder's source-derived style links.
    pub catalog_body: Option<Flow>,
    pub catalog_uses: Vec<super::super::ImportedParagraphCatalogUse>,
    /// The source section relationship, not per-comment author/state or native style acceptance.
    pub memo_catalog_section_id: Option<domain_ir::LogicalId>,
}
impl fmt::Debug for AssembledReviewBody {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("AssembledReviewBody(<redacted>)")
    }
}
pub(super) struct ReviewAssembly {
    bodies: Vec<AssembledReviewBody>,
    source_graph: DocumentGraph,
    source_receipt: ReviewBodyImportReceipt,
    catalog_bodies_sha256: [u8; 32],
}
impl ReviewAssembly {
    pub(super) fn import(catalog: &ImportedDocumentCatalog<'_, '_, '_>) -> Result<Self, Error> {
        let fields = catalog.meanings.fields;
        let source = fields.forms.source();
        let imported = ImportedDocumentReviewBodies::import_bound_fields(fields.forms, fields)?;
        let index: super::super::DefinitionIndex = catalog
            .definitions()
            .iter()
            .map(|d| ((d.kind, d.native_id), d.catalog_id.clone()))
            .collect();
        if index.len() != catalog.definitions().len() {
            return Err(Error::Binding);
        }
        let mut bodies = Vec::new();
        let mut encoded_bytes = 2_usize; // JSON array brackets; each body is streamed once.
        for observation in imported.observations() {
            let mut body = observation.body.clone();
            let mut uses = Vec::new();
            if let Some(body) = &mut body {
                super::super::attach(source, &index, body, &mut uses)?;
            }
            let body = AssembledReviewBody {
                source: observation.clone(),
                catalog_body: body,
                catalog_uses: uses,
                memo_catalog_section_id: if observation.kind == crate::document_import::structure::review::ReviewBodyKind::MemoField {
                    let part = source.resolve_anchor(&observation.marker_anchor).map_err(|_| Error::Binding)?;
                    let section_id = domain_ir::LogicalId::parse(format!("section-{}", part.part().anchor().opaque_handle.as_str())).map_err(|_| Error::Graph)?;
                    if !catalog.memo_uses().iter().any(|v| v.section_id == section_id) { return Err(Error::Binding); }
                    Some(section_id)
                } else { None },
            };
            let (_, size) = bounded_digest_and_size(&body)?;
            encoded_bytes = encoded_bytes
                .checked_add(size)
                .and_then(|n| n.checked_add(usize::from(!bodies.is_empty())))
                .ok_or(ReviewBodyImportError::Budget)?;
            if encoded_bytes > MAX_BYTES {
                return Err(ReviewBodyImportError::Budget.into());
            }
            bodies.push(body);
        }
        Ok(Self {
            catalog_bodies_sha256: bounded_digest(&bodies)?,
            bodies,
            source_graph: imported.graph().clone(),
            source_receipt: imported.receipt().clone(),
        })
    }
    pub(super) fn require_binding(
        &self,
        catalog: &ImportedDocumentCatalog<'_, '_, '_>,
    ) -> Result<(), Error> {
        let fields = catalog.meanings.fields;
        let forms = fields.forms;
        let raw: Vec<_> = self.bodies.iter().map(|b| &b.source).collect();
        if self.source_receipt.source_package_sha256 != catalog.receipt().source_package_sha256
            || self.source_receipt.source_provenance_sha256
                != forms.receipt().source_provenance_sha256
            || self.source_receipt.original_field_graph_sha256 != fields.receipt().graph_sha256
            || self.source_receipt.native_author_time_binding_verified
            || self
                .source_receipt
                .native_visibility_resolution_binding_verified
            || self
                .source_graph
                .canonical_sha256()
                .map_err(|_| Error::Graph)?
                != self.source_receipt.graph_sha256
            || bounded_digest(&raw)? != self.source_receipt.body_observations_sha256
            || bounded_digest(&self.bodies)? != self.catalog_bodies_sha256
        {
            return Err(Error::Binding);
        }
        let original = fields.graph().clone().into_draft();
        let mut review = self.source_graph.clone().into_draft();
        let mut expected_metadata = original.metadata.clone();
        super::insert_new(
            &mut expected_metadata,
            "review_body_import_profile",
            PropertyValue::Text(REVIEW_BODY_IMPORT_PROFILE.into()),
        )?;
        super::insert_new(
            &mut expected_metadata,
            "review_body_import_scope",
            PropertyValue::Text(REVIEW_BODY_IMPORT_SCOPE.into()),
        )?;
        if review.metadata != expected_metadata {
            return Err(Error::Binding);
        }
        review.metadata = original.metadata.clone();
        review.review.clone_from(&original.review);
        if review != original {
            return Err(Error::Binding);
        }
        Ok(())
    }
    pub(super) fn merge(
        &self,
        catalog: &ImportedDocumentCatalog<'_, '_, '_>,
        graph: DocumentGraph,
    ) -> Result<DocumentGraph, Error> {
        self.require_binding(catalog)?;
        if graph.document_id() != catalog.graph().document_id() {
            return Err(Error::Binding);
        }
        // Legacy zero-review outputs stay EXACT, not just visibly equivalent.
        if self.bodies.is_empty() {
            return Ok(graph);
        }
        let original = catalog.meanings.fields.graph().clone().into_draft();
        let mut draft = graph.into_draft();
        if draft.review != original.review {
            return Err(Error::Binding);
        }
        draft.review = self.source_graph.clone().into_draft().review;
        super::insert_new(
            &mut draft.metadata,
            "review_body_import_profile",
            PropertyValue::Text(REVIEW_BODY_IMPORT_PROFILE.into()),
        )?;
        super::insert_new(
            &mut draft.metadata,
            "review_body_import_scope",
            PropertyValue::Text(REVIEW_BODY_IMPORT_SCOPE.into()),
        )?;
        super::insert_new(
            &mut draft.metadata,
            "source_review_catalog_sidecar_sha256",
            PropertyValue::Text(crate::document_import::hex_digest(
                self.catalog_bodies_sha256,
            )),
        )?;
        let mut validation = draft.clone();
        let section = validation.sections.first_mut().ok_or(Error::Graph)?;
        for body in &self.bodies {
            if let Some(body) = &body.catalog_body {
                section.body.children.extend(body.children.clone());
            }
        }
        // Validate all typed review flows/style refs against the COMPLETE existing
        // graph/resources/styles. This disposable graph is not returned or published.
        DocumentGraph::from_draft(validation, DocumentGraphLimits::default())
            .map_err(|_| Error::Graph)?;
        DocumentGraph::from_draft(draft, DocumentGraphLimits::default()).map_err(|_| Error::Graph)
    }
    pub(super) const fn source_receipt(&self) -> &ReviewBodyImportReceipt {
        &self.source_receipt
    }
    pub(super) const fn catalog_bodies_sha256(&self) -> [u8; 32] {
        self.catalog_bodies_sha256
    }
    pub(super) fn into_bodies(self) -> Vec<AssembledReviewBody> {
        self.bodies
    }
}
