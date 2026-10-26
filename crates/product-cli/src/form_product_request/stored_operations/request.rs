use super::super::{FORM_PRODUCT_REQUEST_SCHEMA, MAX_ENVELOPE_BYTES, UniqueJson};
use super::StoredProductOperationError as Error;
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{ArtifactMetadataRepository, ArtifactScanner, EncryptedBlobStore};
use domain_ir::{DocumentId, IdempotencyKey, PlanId, ProjectId, RevisionId};
use revision_service::{RevisionHead, RevisionRepository};
use serde::{Deserialize, Serialize};
pub const PRODUCT_OPERATION_REQUEST_SCHEMA: &str = "hwpx-agent.product-operation-request/v2";
pub(super) enum Kind {
    BookmarkInsertion(super::bookmark_insertion710::ParsedBookmarkInsertionRequest),
    BookmarkCommands(super::bookmark_commands::ParsedBookmarkCommandRequest),
    HttpsTargets,
    Form,
    TableFormulas(FormulaRequest),
    SearchMutation(super::search_mutations::Family),
    FontPreview,
    NamedStylePreview,
    NamedStyleOptionsPreview,
    PersonalInfoMaskPreview,
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
#[derive(Serialize)]
pub(super) struct Operation {
    kind: OperationKind,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
enum OperationKind {
    RecalculateTableFormulas,
}
impl<'de> Deserialize<'de> for Operation {
    fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct MapOnly;
        impl<'de> serde::de::Visitor<'de> for MapOnly {
            type Value = Operation;
            fn expecting(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                f.write_str("strict operation object")
            }
            fn visit_map<A: serde::de::MapAccess<'de>>(
                self,
                mut map: A,
            ) -> Result<Self::Value, A::Error> {
                let mut kind = None;
                while let Some(key) = map.next_key::<String>()? {
                    if key != "kind" || kind.is_some() {
                        return Err(serde::de::Error::custom("operation field rejected"));
                    }
                    kind = Some(map.next_value::<OperationKind>()?);
                }
                Ok(Operation {
                    kind: kind.ok_or_else(|| serde::de::Error::missing_field("kind"))?,
                })
            }
        }
        deserializer.deserialize_map(MapOnly)
    }
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
        super::bookmark_insertion710::BOOKMARK_INSERTION_PRODUCT_REQUEST_SCHEMA => {
            let request = super::bookmark_insertion710::ParsedBookmarkInsertionRequest::parse(
                raw, super::bookmark_insertion710::BookmarkInsertionProductLimits::standard().map_err(|_|RequestError::Request)?,
            ).map_err(|_|RequestError::Request)?;
            Ok(Kind::BookmarkInsertion(request))
        }
        super::bookmark_commands::BOOKMARK_COMMAND_PRODUCT_REQUEST_SCHEMA => {
            let request = super::bookmark_commands::ParsedBookmarkCommandRequest::parse(
                raw, super::bookmark_commands::BookmarkCommandProductLimits::standard().map_err(|_|RequestError::Request)?,
            ).map_err(|_|RequestError::Request)?;
            Ok(Kind::BookmarkCommands(request))
        }
        super::https_targets::HTTPS_TARGET_PRODUCT_REQUEST_SCHEMA=>{
            super::https_targets::validate_request(raw).map_err(|_|RequestError::Request)?;
            Ok(Kind::HttpsTargets)
        }
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
        super::super::stored_literal_replacement::fonts::options::FONT_OPTIONS_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::fonts::options::preview_mode(raw)?;
            if preview{Ok(Kind::FontPreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::FontOptions))}
        }
        super::super::stored_literal_replacement::named_styles::NAMED_STYLE_PRODUCT_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::named_styles::preview_mode(raw)?;
            if preview{Ok(Kind::NamedStylePreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::NamedStyle))}
        }
        super::super::stored_literal_replacement::named_styles::options::NAMED_STYLE_OPTIONS_REQUEST_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::named_styles::options::preview_mode(raw)?;
            if preview{Ok(Kind::NamedStyleOptionsPreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::NamedStyleOptions))}
        }
        super::super::stored_literal_replacement::personal_info::PERSONAL_INFO_MASK_PRODUCT_SCHEMA=>{
            let preview=super::super::stored_literal_replacement::personal_info::preview_mode(raw)?;
            if preview{Ok(Kind::PersonalInfoMaskPreview)}else{Ok(Kind::SearchMutation(super::search_mutations::Family::PersonalInfoMask))}
        }
        schema => match super::search_mutations::classify(schema) {
            Some(family) => {
                if raw.len() > super::super::stored_literal_replacement::LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES {
                    return Err(RequestError::Limit.into());
                }
                Ok(Kind::SearchMutation(family))
            }
            None => Err(RequestError::Request.into()),
        },
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
