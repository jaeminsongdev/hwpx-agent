use super::super::super::SourcePolicyBinding;
use super::{
    APPROVAL_SCHEMA, CLAIMS_SCHEMA, DOMAIN, FormulaIssuerError as Error, MAX_APPROVAL_BYTES,
    MAX_CLAIMS_BYTES,
};
use artifact_service::{ArtifactId, ContentDigest};
use serde::{Deserialize, Deserializer, Serialize};

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct Claims {
    pub schema_version: String,
    pub issuer: String,
    pub key_id: String,
    pub audience: String,
    pub operation: String,
    pub trust_generation: u64,
    #[serde(deserialize_with = "object_only")]
    pub binding: SourcePolicyBinding,
    pub policy_artifact: ArtifactId,
    pub policy_digest: ContentDigest,
    pub issued_at: u64,
    pub not_before: u64,
    pub expires_at: u64,
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Envelope {
    schema_version: String,
    signed_claims: String,
    signature_hex: String,
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
            f.write_str("strict approval object")
        }
        fn visit_map<A: serde::de::MapAccess<'de>>(self, map: A) -> Result<T, A::Error> {
            T::deserialize(serde::de::value::MapAccessDeserializer::new(map))
        }
    }
    d.deserialize_map(MapOnly::<T>(std::marker::PhantomData))
}
fn decode_object<T: for<'de> Deserialize<'de>>(raw: &[u8]) -> Result<T, Error> {
    let mut d = serde_json::Deserializer::from_slice(raw);
    let v = object_only(&mut d).map_err(|_| Error::Payload)?;
    d.end().map_err(|_| Error::Payload)?;
    Ok(v)
}
pub(super) fn encode_claims(claims: &Claims) -> Result<Vec<u8>, Error> {
    let raw = serde_json::to_vec(claims).map_err(|_| Error::Payload)?;
    if raw.is_empty() || raw.len() > MAX_CLAIMS_BYTES {
        return Err(Error::Payload);
    }
    Ok(raw)
}
pub(super) fn signing_bytes(raw: &[u8]) -> Vec<u8> {
    [DOMAIN, raw].concat()
}
pub(super) fn encode_envelope(claims: &Claims, signature: [u8; 64]) -> Result<Vec<u8>, Error> {
    let raw = encode_claims(claims)?;
    let env = Envelope {
        schema_version: APPROVAL_SCHEMA.into(),
        signed_claims: String::from_utf8(raw).map_err(|_| Error::Payload)?,
        signature_hex: hex::encode(signature),
    };
    let bytes = serde_json::to_vec(&env).map_err(|_| Error::Payload)?;
    if bytes.len() > MAX_APPROVAL_BYTES {
        return Err(Error::Payload);
    }
    Ok(bytes)
}
pub(super) fn decode(raw: &[u8]) -> Result<(Claims, Vec<u8>, [u8; 64]), Error> {
    if raw.is_empty() || raw.len() > MAX_APPROVAL_BYTES {
        return Err(Error::Payload);
    }
    let env: Envelope = decode_object(raw)?;
    if env.schema_version != APPROVAL_SCHEMA
        || env.signed_claims.is_empty()
        || env.signed_claims.len() > MAX_CLAIMS_BYTES
        || env.signature_hex.len() != 128
        || !env
            .signature_hex
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(Error::Payload);
    }
    let claims: Claims = decode_object(env.signed_claims.as_bytes())?;
    if claims.schema_version != CLAIMS_SCHEMA {
        return Err(Error::Payload);
    }
    let signature: [u8; 64] = hex::decode(env.signature_hex)
        .map_err(|_| Error::Payload)?
        .try_into()
        .map_err(|_| Error::Payload)?;
    Ok((
        claims,
        signing_bytes(env.signed_claims.as_bytes()),
        signature,
    ))
}
