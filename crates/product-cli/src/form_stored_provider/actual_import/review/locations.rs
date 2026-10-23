//! Fresh original stored review XML/IR locations; no native caret or execution authority.
use super::StoredImportedReviewBodies;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use hwpx_package::document_import::structure::review::locations::{
    ImportedReviewLocations, ReviewLocationReceipt, ReviewSourceLocation,
};
use revision_service::RevisionRepository;
use std::fmt;
use thiserror::Error;

pub struct StoredReviewLocations<'a, 'source> {
    review: &'a StoredImportedReviewBodies<'source>,
    locations: ImportedReviewLocations<'a, 'source>,
}
impl fmt::Debug for StoredReviewLocations<'_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("StoredReviewLocations(<redacted>)")
    }
}
impl<'source> StoredImportedReviewBodies<'source> {
    /// Locate only after original fresh ACL/AEAD/head/scope/quarantine/source validation.
    /// # Errors
    /// Rejects original service/source drift or original XML/IR positional binding failure.
    pub fn locate<'a, R, B, S, V>(
        &'a self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<StoredReviewLocations<'a, 'source>, StoredReviewLocationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        let fresh = self
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        let locations = self
            .imported
            .locate(&fresh.bytes)
            .map_err(|_| StoredReviewLocationError::Binding)?;
        self.verify(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        Ok(StoredReviewLocations {
            review: self,
            locations,
        })
    }
}
impl StoredReviewLocations<'_, '_> {
    /// Cached memory only; not fresh access, caret/visual state or execution authority.
    #[must_use]
    pub fn locations(&self) -> &[ReviewSourceLocation] {
        self.locations.locations()
    }
    #[must_use]
    pub const fn receipt(&self) -> &ReviewLocationReceipt {
        self.locations.receipt()
    }
    /// Rebuild original source/whole review/locations after the original fresh service checks.
    /// # Errors
    /// Rejects original access, ciphertext, head/scope/source or cached positional drift.
    pub fn verify<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<ReviewLocationReceipt, StoredReviewLocationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        let fresh = self
            .review
            .source
            .fresh_source(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        let receipt = self
            .locations
            .verify_source(&fresh.bytes)
            .map_err(|_| StoredReviewLocationError::Binding)?;
        self.review
            .verify(provider, now)
            .map_err(|_| StoredReviewLocationError::Source)?;
        Ok(receipt)
    }
    /// Never presents cached location data to the callback after fresh access/binding rejection.
    /// # Errors
    /// Rejects fresh source/service/whole mapping failure before invoking the callback.
    pub fn with_verified_locations<R, B, S, V, T>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
        consume: impl FnOnce(&[ReviewSourceLocation]) -> T,
    ) -> Result<T, StoredReviewLocationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Ok(consume(self.locations.locations()))
    }
    /// Positions alone never authorize a native comment operation or publication.
    /// # Errors
    /// Always denies the product route after fresh checks.
    pub fn require_current_product_route<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), StoredReviewLocationError>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        self.verify(provider, now)?;
        Err(StoredReviewLocationError::RouteUnqualified)
    }
}
#[derive(Debug, Error, Eq, PartialEq)]
pub enum StoredReviewLocationError {
    #[error("stored_review_location_original_source_rejected")]
    Source,
    #[error("stored_review_location_original_binding_rejected")]
    Binding,
    #[error("stored_review_location_product_route_unqualified")]
    RouteUnqualified,
}
