use super::super::{FormulaIssuerKey, FormulaIssuerTrust, FormulaIssuerTrustDraft};
use super::{Error, FORMULA_ISSUER_TRUST_SCHEMA, MAX_TRUST_BYTES};
use artifact_service::TenantId;
use revision_service::{
    ProjectId, postgres::source_formula_policy::issuer_registry::FormulaIssuerTrustRecord,
};
use serde::{Deserialize, Deserializer};
use uuid::Uuid;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Payload {
    schema_version: String,
    tenant: TenantId,
    project: ProjectId,
    trust_version: Uuid,
    generation: u64,
    issuer: String,
    valid_from: u64,
    valid_until: u64,
    max_approval_lifetime: u64,
    keys: Vec<ObjectKey>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct WireKey {
    key_id: String,
    public_key_hex: String,
}
struct ObjectKey(WireKey);
impl<'de> Deserialize<'de> for ObjectKey {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        object_only(d).map(Self)
    }
}
fn object_only<'de, D: Deserializer<'de>, T: Deserialize<'de>>(d: D) -> Result<T, D::Error> {
    struct MapOnly<T>(std::marker::PhantomData<T>);
    impl<'de, T: Deserialize<'de>> serde::de::Visitor<'de> for MapOnly<T> {
        type Value = T;
        fn expecting(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            f.write_str("strict trust object")
        }
        fn visit_map<A: serde::de::MapAccess<'de>>(self, map: A) -> Result<T, A::Error> {
            T::deserialize(serde::de::value::MapAccessDeserializer::new(map))
        }
    }
    d.deserialize_map(MapOnly::<T>(std::marker::PhantomData))
}
pub(super) fn decode(
    raw: &[u8],
    row: &FormulaIssuerTrustRecord,
) -> Result<FormulaIssuerTrust, Error> {
    if raw.is_empty() || raw.len() > MAX_TRUST_BYTES {
        return Err(Error::Payload);
    }
    let mut decoder = serde_json::Deserializer::from_slice(raw);
    let p: Payload = object_only(&mut decoder).map_err(|_| Error::Payload)?;
    decoder.end().map_err(|_| Error::Payload)?;
    if p.schema_version != FORMULA_ISSUER_TRUST_SCHEMA
        || p.tenant != row.tenant
        || p.project != row.project
        || p.trust_version != row.version
        || p.generation != row.generation
        || p.issuer != row.issuer
        || p.valid_from != row.valid_from
        || p.valid_until != row.valid_until
        || p.max_approval_lifetime != row.max_approval_lifetime
        || p.keys.is_empty()
        || p.keys.len() > 8
    {
        return Err(Error::Binding);
    }
    let mut keys = Vec::with_capacity(p.keys.len());
    for ObjectKey(k) in p.keys {
        if k.public_key_hex.len() != 64
            || !k
                .public_key_hex
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
        {
            return Err(Error::Payload);
        }
        let key = hex::decode(k.public_key_hex)
            .map_err(|_| Error::Payload)?
            .try_into()
            .map_err(|_| Error::Payload)?;
        keys.push(FormulaIssuerKey::new(k.key_id, key)?);
    }
    FormulaIssuerTrust::new(FormulaIssuerTrustDraft {
        tenant: p.tenant,
        project: p.project,
        issuer: p.issuer,
        generation: p.generation,
        valid_from: p.valid_from,
        valid_until: p.valid_until,
        max_approval_lifetime: p.max_approval_lifetime,
        active_keys: keys,
    })
}
