use super::super::{MAX_POLICY_BYTES, SourcePolicyBinding, SourcePolicyVersion};
use super::{FORMULA_POLICY_MEDIA_TYPE, FORMULA_POLICY_SCHEMA, StoredFormulaPolicyError as Error};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactKind, ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
    StorageState, ValidationState,
};
use domain_ir::{LogicalId, SourceAnchorHandle};
use revision_service::RevisionRepository;
use serde::{Deserialize, Deserializer, Serialize};
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct Payload {
    schema_version: String,
    #[serde(deserialize_with = "object_only")]
    binding: SourcePolicyBinding,
    pub meaning_graph_sha256: ContentDigest,
    #[serde(deserialize_with = "object_vec")]
    pub targets: Vec<Rule>,
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(super) struct Rule {
    pub reference_id: LogicalId,
    #[serde(deserialize_with = "object_only")]
    pub begin_anchor: SourceAnchorHandle,
    #[serde(deserialize_with = "object_only")]
    pub end_anchor: SourceAnchorHandle,
    pub ast_sha256: ContentDigest,
    pub allow_recalculation: bool,
}
struct ObjectOnly<T>(T);
impl<'de, T: Deserialize<'de>> Deserialize<'de> for ObjectOnly<T> {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        object_only(d).map(Self)
    }
}
fn object_vec<'de, D, T>(d: D) -> Result<Vec<T>, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    Ok(Vec::<ObjectOnly<T>>::deserialize(d)?
        .into_iter()
        .map(|x| x.0)
        .collect())
}
fn object_only<'de, D, T>(d: D) -> Result<T, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de>,
{
    struct MapOnly<T>(std::marker::PhantomData<T>);
    impl<'de, T: Deserialize<'de>> serde::de::Visitor<'de> for MapOnly<T> {
        type Value = T;
        fn expecting(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.write_str("strict policy object")
        }
        fn visit_map<A: serde::de::MapAccess<'de>>(self, map: A) -> Result<T, A::Error> {
            T::deserialize(serde::de::value::MapAccessDeserializer::new(map))
        }
    }
    d.deserialize_map(MapOnly::<T>(std::marker::PhantomData))
}
pub(super) fn decode(bytes: &[u8], binding: &SourcePolicyBinding) -> Result<Payload, Error> {
    if bytes.is_empty() || bytes.len() > MAX_POLICY_BYTES {
        return Err(Error::Payload);
    }
    let mut d = serde_json::Deserializer::from_slice(bytes);
    let p: Payload = object_only(&mut d).map_err(|_| Error::Payload)?;
    d.end().map_err(|_| Error::Payload)?;
    if p.schema_version != FORMULA_POLICY_SCHEMA
        || p.binding != *binding
        || p.targets.is_empty()
        || p.targets.len() > 4096
    {
        return Err(Error::Payload);
    }
    Ok(p)
}
pub(super) fn read_artifact<R, B, S, V>(
    provider: &StoredFormProvider<'_, R, B, S, V>,
    version: &SourcePolicyVersion,
    now: u64,
) -> Result<Vec<u8>, Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    let d = provider
        .artifacts
        .get_descriptor(provider.artifact_context, version.artifact, now)
        .map_err(|_| Error::Artifact)?;
    if d.artifact_id != version.artifact
        || d.sha256 != version.digest
        || d.kind != ArtifactKind::Evidence
        || d.media_type.as_str() != FORMULA_POLICY_MEDIA_TYPE
        || d.storage_state != StorageState::Available
        || d.validation_state != ValidationState::Verified
        || d.quarantine_reason.is_some()
        || d.size_bytes == 0
        || d.size_bytes > MAX_POLICY_BYTES as u64
    {
        return Err(Error::Artifact);
    }
    let bytes = provider
        .artifacts
        .download(provider.artifact_context, version.artifact, now)
        .map_err(|_| Error::Artifact)?;
    if bytes.len() as u64 != d.size_bytes
        || bytes.is_empty()
        || bytes.len() > MAX_POLICY_BYTES
        || ContentDigest::of(&bytes) != version.digest
    {
        return Err(Error::Artifact);
    }
    Ok(bytes)
}
