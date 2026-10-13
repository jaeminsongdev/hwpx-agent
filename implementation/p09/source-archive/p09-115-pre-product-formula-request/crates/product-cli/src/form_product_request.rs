//! Product request, provider scope and actual revision-head preflight.
//! Read-only preflight is NOT a CAS, idempotency claim, signed route or publication.
pub mod stored;
pub mod stored_full_document;

use crate::form_value_operation::{
    FormOperationContext, FormOperationIdentity, FormOperationPreparation, FormOperationReceipt,
    PreparedFormOperation,
};
use domain_ir::{
    DocumentId, IdempotencyKey, PlanId, ProjectId, RevisionId, form_input::FormInputAccessPolicy,
};
use operation_engine::{IdempotencyService, RevisionStreamKey};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{collections::BTreeSet, fmt, io};
use thiserror::Error;

pub const FORM_PRODUCT_REQUEST_SCHEMA: &str = "hwpx-agent.product-form-request/v1";
const MAX_ENVELOPE_BYTES: usize = 2 * 1024 * 1024;
const MAX_INPUT_BYTES: usize = 1024 * 1024;

/// Private provider-owned project/document/full raw source binding, not caller approval.
pub struct FormProductContext<'a> {
    project: ProjectId,
    document: DocumentId,
    source_sha256: String,
    operation: FormOperationContext<'a>,
}
impl fmt::Debug for FormProductContext<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("FormProductContext(<redacted>)")
    }
}
impl<'a> FormProductContext<'a> {
    /// Binds the complete actual package through the original product/SDK reader.
    /// # Errors
    /// Rejects invalid provider identity or package/map/policy binding; no stream is initialized.
    pub fn bind(
        project: ProjectId,
        document: DocumentId,
        source: &'a [u8],
        map: &'a hwpx_package::NativeFormPackageMap,
        policies: &'a [hwpx_package::NativeFormPackagePolicy],
    ) -> Result<Self, FormProductRequestError> {
        if document.as_str().len() > 1024 {
            return Err(FormProductRequestError::Limit);
        }
        let operation = FormOperationContext::bind(source, map, policies)
            .map_err(|_| FormProductRequestError::Source)?;
        Ok(Self {
            project,
            document,
            source_sha256: hex::encode(Sha256::digest(source)),
            operation,
        })
    }
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Request {
    schema_version: String,
    idempotency_key: IdempotencyKey,
    project_id: ProjectId,
    document_id: DocumentId,
    base_revision: RevisionId,
    expected_head_generation: u64,
    expected_source_package_sha256: String,
    plan_id: PlanId,
    form_input: Value,
}
impl fmt::Debug for Request {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ProductFormRequest(<redacted>)")
    }
}
impl Request {
    fn parse(raw: &[u8]) -> Result<Self, FormProductRequestError> {
        if raw.is_empty() || raw.len() > MAX_ENVELOPE_BYTES {
            return Err(FormProductRequestError::Limit);
        }
        let mut deserializer = serde_json::Deserializer::from_slice(raw);
        let _ = UniqueJson::deserialize(&mut deserializer)
            .map_err(|_| FormProductRequestError::Request)?;
        deserializer
            .end()
            .map_err(|_| FormProductRequestError::Request)?;
        let request: Self =
            serde_json::from_slice(raw).map_err(|_| FormProductRequestError::Request)?;
        if request.schema_version != FORM_PRODUCT_REQUEST_SCHEMA
            || request.expected_head_generation == 0
            || request.document_id.as_str().len() > 1024
            || request.expected_source_package_sha256.len() != 64
            || !request
                .expected_source_package_sha256
                .bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
        {
            return Err(FormProductRequestError::Request);
        }
        Ok(request)
    }
    fn stream(&self) -> RevisionStreamKey {
        RevisionStreamKey::new(self.project_id.clone(), self.document_id.clone())
    }
    fn check(
        &self,
        context: &FormProductContext<'_>,
        revisions: &IdempotencyService,
    ) -> Result<(), FormProductRequestError> {
        if self.project_id != context.project
            || self.document_id != context.document
            || self.expected_source_package_sha256 != context.source_sha256
        {
            return Err(FormProductRequestError::ProviderScope);
        }
        let head = revisions
            .head(&self.stream())
            .map_err(|_| FormProductRequestError::Head)?;
        if head.revision_id() != &self.base_revision
            || head.generation() != self.expected_head_generation
        {
            return Err(FormProductRequestError::Head);
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FormProductPreflightReceipt {
    pub schema_version: &'static str,
    pub raw_request_sha256: String,
    pub canonical_request_sha256: String,
    pub scoped_request_sha256: String,
    pub expected_head_generation: u64,
    pub operation: FormOperationReceipt,
    pub qualification: FormProductPreflightQualification,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FormProductPreflightQualification {
    ReadOnlyProviderHeadPreflightOnlyAtomicCasIdempotencyRoutePublicationNativeAndGateUnqualified,
}

/// Non-deserializable preparation bound to a private strict request and current provider head.
pub struct PreparedProductForm {
    request: Request,
    operation: PreparedFormOperation,
    receipt: FormProductPreflightReceipt,
}
impl fmt::Debug for PreparedProductForm {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("PreparedProductForm(<redacted>)")
    }
}
impl PreparedProductForm {
    #[must_use]
    pub const fn receipt(&self) -> &FormProductPreflightReceipt {
        &self.receipt
    }
    /// Memory candidate only; no artifact has been published or authorized.
    #[must_use]
    pub fn candidate_bytes(&self) -> &[u8] {
        self.operation.candidate_bytes()
    }
    /// Checks the real provider/stream head before AND after complete original operation verification.
    /// # Errors
    /// Rejects changed project/document/raw source/head/revision/access/map/policies/output.
    /// The second read is not a lock held across the check and is NOT atomic CAS permission.
    pub fn verify(
        &self,
        fresh: &FormProductContext<'_>,
        revisions: &IdempotencyService,
        access: &FormInputAccessPolicy,
    ) -> Result<FormProductPreflightReceipt, FormProductRequestError> {
        self.request.check(fresh, revisions)?;
        let operation = self
            .operation
            .verify(&fresh.operation, access)
            .map_err(|_| FormProductRequestError::Drift)?;
        self.request.check(fresh, revisions)?;
        if operation != self.receipt.operation
            || self.receipt.schema_version != FORM_PRODUCT_REQUEST_SCHEMA
            || self.receipt.expected_head_generation != self.request.expected_head_generation
            || self.operation.compiled_plan().base_revision() != &self.request.base_revision
            || self.operation.compiled_plan().plan_id() != &self.request.plan_id
            || self.receipt.canonical_request_sha256
                != digest(&bounded(&self.request, MAX_ENVELOPE_BYTES)?)
            || self.receipt.scoped_request_sha256 != scope_digest(&self.request)?
        {
            return Err(FormProductRequestError::Drift);
        }
        Ok(self.receipt.clone())
    }
    /// Consults unchanged actual authority only after the full fresh head/provider preflight.
    /// # Errors
    /// Always denies the current unqualified form scope. No key claim or stream mutation occurs.
    pub fn require_current_product_route(
        &self,
        fresh: &FormProductContext<'_>,
        revisions: &IdempotencyService,
        access: &FormInputAccessPolicy,
    ) -> Result<(), FormProductRequestError> {
        self.verify(fresh, revisions, access)?;
        self.operation
            .require_current_product_route(&fresh.operation, access)
            .map_err(|_| FormProductRequestError::RouteUnqualified)
    }
}

#[derive(Debug)]
pub struct FormProductPreflight;
impl FormProductPreflight {
    /// Actual strict product envelope -> provider/real head checks -> original operation preparation.
    /// # Errors
    /// Rejects duplicate/unknown/coerced/malformed/stale requests and original source/input failures.
    /// Never initializes/claims/commits a stream, creates a manifest or publishes a file.
    pub fn prepare_json(
        context: &FormProductContext<'_>,
        revisions: &IdempotencyService,
        raw: &[u8],
        access: &FormInputAccessPolicy,
    ) -> Result<PreparedProductForm, FormProductRequestError> {
        let request = Request::parse(raw)?;
        request.check(context, revisions)?;
        let input = bounded(&request.form_input, MAX_INPUT_BYTES)?;
        let identity = FormOperationIdentity::new(
            request.document_id.clone(),
            request.base_revision.clone(),
            request.plan_id.clone(),
        )
        .map_err(|_| FormProductRequestError::Request)?;
        let operation =
            FormOperationPreparation::prepare_json(&context.operation, identity, &input, access)
                .map_err(|_| FormProductRequestError::Operation)?;
        request.check(context, revisions)?;
        let receipt=FormProductPreflightReceipt {
            schema_version:FORM_PRODUCT_REQUEST_SCHEMA,raw_request_sha256:digest(raw),
            canonical_request_sha256:digest(&bounded(&request,MAX_ENVELOPE_BYTES)?),
            scoped_request_sha256:scope_digest(&request)?,expected_head_generation:request.expected_head_generation,
            operation:operation.receipt().clone(),qualification:FormProductPreflightQualification::ReadOnlyProviderHeadPreflightOnlyAtomicCasIdempotencyRoutePublicationNativeAndGateUnqualified,
        };
        let prepared = PreparedProductForm {
            request,
            operation,
            receipt,
        };
        prepared.verify(context, revisions, access)?;
        Ok(prepared)
    }
}
fn scope_digest(request: &Request) -> Result<String, FormProductRequestError> {
    Ok(digest(&bounded(
        &(
            FORM_PRODUCT_REQUEST_SCHEMA,
            &request.project_id,
            &request.document_id,
            &request.idempotency_key,
            &request.base_revision,
            request.expected_head_generation,
            &request.expected_source_package_sha256,
            &request.plan_id,
            digest(&bounded(&request.form_input, MAX_INPUT_BYTES)?),
        ),
        MAX_ENVELOPE_BYTES,
    )?))
}
fn digest(raw: &[u8]) -> String {
    hex::encode(Sha256::digest(raw))
}
struct UniqueJson;
impl<'de> Deserialize<'de> for UniqueJson {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct UniqueVisitor;
        impl<'de> serde::de::Visitor<'de> for UniqueVisitor {
            type Value = UniqueJson;
            fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
                f.write_str("unique bounded JSON")
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut map: A,
            ) -> Result<Self::Value, A::Error> {
                let mut keys = BTreeSet::new();
                while let Some(key) = map.next_key::<String>()? {
                    if !keys.insert(key) {
                        return Err(serde::de::Error::custom("duplicate key"));
                    }
                    let _ = map.next_value::<UniqueJson>()?;
                }
                Ok(UniqueJson)
            }
            fn visit_seq<A: serde::de::SeqAccess<'de>>(
                self,
                mut seq: A,
            ) -> Result<Self::Value, A::Error> {
                while seq.next_element::<UniqueJson>()?.is_some() {}
                Ok(UniqueJson)
            }
            fn visit_bool<E: serde::de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_i64<E: serde::de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_u64<E: serde::de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_f64<E: serde::de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_str<E: serde::de::Error>(self, _: &str) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
            fn visit_unit<E: serde::de::Error>(self) -> Result<Self::Value, E> {
                Ok(UniqueJson)
            }
        }
        deserializer.deserialize_any(UniqueVisitor)
    }
}
fn bounded<T: Serialize>(value: &T, limit: usize) -> Result<Vec<u8>, FormProductRequestError> {
    let mut writer = LimitedJson {
        bytes: vec![],
        limit,
    };
    serde_json::to_writer(&mut writer, value).map_err(|_| FormProductRequestError::Limit)?;
    Ok(writer.bytes)
}
struct LimitedJson {
    bytes: Vec<u8>,
    limit: usize,
}
impl io::Write for LimitedJson {
    fn write(&mut self, raw: &[u8]) -> io::Result<usize> {
        let length = self
            .bytes
            .len()
            .checked_add(raw.len())
            .filter(|n| *n <= self.limit)
            .ok_or_else(|| io::Error::other("product request limit"))?;
        self.bytes
            .try_reserve(raw.len())
            .map_err(|_| io::Error::other("product request allocation"))?;
        self.bytes.extend_from_slice(raw);
        debug_assert_eq!(self.bytes.len(), length);
        Ok(raw.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::LimitedJson;
    use std::io::Write as _;
    #[test]
    fn finite_json_writer_rejects_overrun_before_any_partial_append() {
        let mut writer = LimitedJson {
            bytes: vec![],
            limit: 3,
        };
        assert!(writer.write_all(b"abc").is_ok());
        assert!(writer.write_all(b"de").is_err());
        assert_eq!(writer.bytes, b"abc");
    }
    #[test]
    fn finite_json_writer_rejects_first_oversize_without_append() {
        let mut writer = LimitedJson {
            bytes: vec![],
            limit: 1,
        };
        assert!(writer.write_all(b"ab").is_err());
        assert!(writer.bytes.is_empty());
    }
}

#[derive(Debug, Error, Eq, PartialEq)]
pub enum FormProductRequestError {
    #[error("FORM_PRODUCT_REQUEST_LIMIT")]
    Limit,
    #[error("FORM_PRODUCT_REQUEST_REJECTED")]
    Request,
    #[error("FORM_PRODUCT_SOURCE_REJECTED")]
    Source,
    #[error("FORM_PRODUCT_PROVIDER_SCOPE_MISMATCH")]
    ProviderScope,
    #[error("FORM_PRODUCT_CURRENT_REVISION_HEAD_MISMATCH")]
    Head,
    #[error("FORM_PRODUCT_OPERATION_REJECTED")]
    Operation,
    #[error("FORM_PRODUCT_FRESH_PREPARATION_DRIFT")]
    Drift,
    #[error("FORM_PRODUCT_SIGNED_FORM_ROUTE_UNQUALIFIED")]
    RouteUnqualified,
}
