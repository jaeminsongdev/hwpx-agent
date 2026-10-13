use super::super::{FORM_PRODUCT_REQUEST_SCHEMA, MAX_ENVELOPE_BYTES, UniqueJson};
use super::StoredProductOperationError as Error;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{DocumentId, IdempotencyKey, PlanId, ProjectId, RevisionId};
use revision_service::{RevisionHead, RevisionRepository};
use serde::{Deserialize, Serialize};
pub const PRODUCT_OPERATION_REQUEST_SCHEMA: &str = "hwpx-agent.product-operation-request/v2";
pub(super) enum Kind {
    Form,
    TableFormulas(FormulaRequest),
}
#[derive(Deserialize)]
struct Schema {
    schema_version: String,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(super) struct FormulaRequest {
    pub schema_version: String,
    pub idempotency_key: IdempotencyKey,
    pub project_id: ProjectId,
    pub document_id: DocumentId,
    pub base_revision: RevisionId,
    pub expected_head_generation: u64,
    pub expected_source_package_sha256: String,
    pub plan_id: PlanId,
    pub operation: Operation,
}
#[derive(Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub(super) enum Operation {
    RecalculateTableFormulas,
}

pub(super) fn classify(raw: &[u8]) -> Result<Kind, Error> {
    use super::super::FormProductRequestError as RequestError;
    if raw.is_empty() || raw.len() > MAX_ENVELOPE_BYTES {
        return Err(RequestError::Limit.into());
    }
    let mut deserializer = serde_json::Deserializer::from_slice(raw);
    let _ = UniqueJson::deserialize(&mut deserializer).map_err(|_| RequestError::Request)?;
    deserializer.end().map_err(|_| RequestError::Request)?;
    let schema: Schema = serde_json::from_slice(raw).map_err(|_| RequestError::Request)?;
    match schema.schema_version.as_str() {
        FORM_PRODUCT_REQUEST_SCHEMA => {
            super::super::Request::parse(raw)?;
            Ok(Kind::Form)
        }
        PRODUCT_OPERATION_REQUEST_SCHEMA => {
            let request: FormulaRequest =
                serde_json::from_slice(raw).map_err(|_| RequestError::Request)?;
            if request.expected_head_generation == 0
                || request.document_id.as_str().len() > 1024
                || request.expected_source_package_sha256.len() != 64
                || !request
                    .expected_source_package_sha256
                    .bytes()
                    .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
            {
                return Err(RequestError::Request.into());
            }
            Ok(Kind::TableFormulas(request))
        }
        _ => Err(RequestError::Request.into()),
    }
}
impl FormulaRequest {
    pub(super) fn head(&self) -> Result<RevisionHead, Error> {
        let revision = revision_service::RevisionId::parse(self.base_revision.as_str())
            .map_err(|_| super::super::FormProductRequestError::Head)?;
        RevisionHead::new(Some(revision), self.expected_head_generation)
            .map_err(|_| super::super::FormProductRequestError::Head.into())
    }
    pub(super) fn check<R, B, S, V>(
        &self,
        provider: &StoredFormProvider<'_, R, B, S, V>,
        now: u64,
    ) -> Result<(), Error>
    where
        R: ArtifactMetadataRepository,
        B: EncryptedBlobStore,
        S: ArtifactScanner,
        V: RevisionRepository,
    {
        provider.check_product_binding(
            &self.project_id,
            &self.document_id,
            self.head()?,
            &self.expected_source_package_sha256,
            now,
        )?;
        Ok(())
    }
}
