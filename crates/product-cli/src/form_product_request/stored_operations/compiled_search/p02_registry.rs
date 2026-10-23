//! Authenticates the exact preserved P02 snapshot. Historical signed claims never authorize routes.
mod base64;
#[cfg(test)]mod tests;
use super::*;
use domain_ir::{Architecture,CapabilityId,ExactTargetProfile,TargetProfileId};
use ring::signature::{ED25519,UnparsedPublicKey};
use serde::Deserialize;
use serde_json::Value;
use std::collections::BTreeMap;
const ENVELOPE_SHA:&str="97c86645a4bf0696474cb6815699a2e4b012f650ae09ef81c582b672580b85e4";
const POLICY_SHA:&str="c96c6f4d4eddecd62dfb4c95badc8f1693a3e4d05c3b3dbc96bf26850212054c";
const KEY_SHA:&str="838f7ce354cb2e284ca8b1e108c4234481b66fdfc0c9d415de43dc7cd3da57f5";
const PAYLOAD_SHA:&str="3958ccc564be09d0f40889287fa4f2db36584596001a7a2b9e8df0ca57a9450f";
const REGISTRY_SHA:&str="986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48";
const MAX_ENVELOPE:usize=64*1024*1024;
const MAX_REGISTRY:usize=32*1024*1024;
pub const PINNED_P02_REGISTRY_PROFILE:&str="hwpx-agent.p09-pinned-p02-registry-evidence/v1";

/// Inputs are bytes, never trust flags, a private signing key or caller-selected executable authority.
pub struct PinnedP02RegistryBytes<'a>{pub envelope:&'a[u8],pub policy:&'a[u8],pub public_key:&'a[u8]}
impl fmt::Debug for PinnedP02RegistryBytes<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PinnedP02RegistryBytes(<redacted>)")}}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(rename_all="snake_case")]
pub enum SignedSupportClaim{VerifiedCurrentTarget,FailedCurrentTarget,BlockedByPolicy,UnverifiedNotRun,Unavailable}
#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
pub struct SignedRegistryCounts{pub bindings:usize,pub candidates:usize,pub unavailable:usize,pub verified_claims:usize,pub failed_claims:usize,pub blocked_claims:usize,pub not_run_claims:usize}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct PinnedP02RegistryReceipt{
    pub profile:&'static str,pub envelope_sha256:[u8;32],pub payload_sha256:[u8;32],pub registry_sha256:[u8;32],
    pub trust_policy_sha256:[u8;32],pub public_key_sha256:[u8;32],pub registry_sequence:u64,pub counts:SignedRegistryCounts,
    pub signature_verified:bool,pub routing_enabled:bool,pub execution_authority:bool,pub runtime_probe_reexecuted:bool,pub current_installed_target_observed:bool,
}
impl fmt::Debug for PinnedP02RegistryReceipt{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("PinnedP02RegistryReceipt").field("counts",&self.counts).field("routing_enabled",&false).finish_non_exhaustive()}}
pub struct PinnedP02RegistryEvidence{receipt:PinnedP02RegistryReceipt,target:ExactTargetProfile,claims:BTreeMap<CapabilityId,SignedSupportClaim>}
impl fmt::Debug for PinnedP02RegistryEvidence{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("PinnedP02RegistryEvidence(<redacted>; historical_snapshot_routing_disabled)")}}
impl PinnedP02RegistryEvidence{
    /// # Errors
    /// Authenticates only the exact preserved, independently checked P02 snapshot and public trust material.
    /// It is not a generic registry promotion API, fresh runtime verification or a mutable/latest registry.
    pub fn verify_pinned_snapshot(input:PinnedP02RegistryBytes<'_>)->Result<Self,PinnedRegistryError>{
        pin(input.policy,64*1024,POLICY_SHA)?;pin(input.public_key,64*1024,KEY_SHA)?;pin(input.envelope,MAX_ENVELOPE,ENVELOPE_SHA)?;
        if input.envelope.len()!=963_624{return Err(PinnedRegistryError::Pin);}
        let policy=strict(input.policy,64*1024)?;let envelope=strict(input.envelope,MAX_ENVELOPE)?;
        object(&envelope,&["schema_version","algorithm","key_id","public_key_sha256","payload_sha256","payload","signature_base64"])?;
        eq(&envelope["schema_version"],"hwpx-agent.signed-automation-registry-envelope/v1")?;eq(&envelope["algorithm"],"Ed25519")?;
        let public=pem(input.public_key)?;let key_id=format!("ed25519-sha256-{}",hex::encode(Sha256::digest(&public)));
        eq(&envelope["key_id"],&key_id)?;eq(&policy["key_id"],&key_id)?;eq(&envelope["public_key_sha256"],KEY_SHA)?;
        let payload=&envelope["payload"];let canonical=crate::form_product_request::bounded(payload,MAX_ENVELOPE).map_err(|_|PinnedRegistryError::Limit)?;
        let payload_sha=hash(&canonical);if hex::encode(payload_sha)!=PAYLOAD_SHA||text(&envelope["payload_sha256"])?!=PAYLOAD_SHA{return Err(PinnedRegistryError::Binding);}
        let signature=base64::decode(text(&envelope["signature_base64"])?,64)?;
        verify_signature(&public,&canonical,&signature)?;
        object(payload,&["schema_version","restricted_derivative","source_registry","target","runtime_evidence","qualification","release_policy","drift_baseline","lineage","provenance"])?;
        eq(&payload["schema_version"],"hwpx-agent.signed-automation-registry-payload/v1")?;
        if payload["restricted_derivative"]!=true{return Err(PinnedRegistryError::Scope);}
        eq(&policy["schema_version"],"hwpx-agent.registry-trust-policy/v1")?;eq(&policy["algorithm"],"Ed25519")?;
        for field in["routing_allowed","production_allowed","provider_allowed","hosted_or_vm_allowed"]{disabled(&policy["scope"][field])?;}
        disabled(&policy["lineage"]["rollback_allowed"])?;
        let release=&payload["release_policy"];disabled(&release["routing_enabled"])?;
        eq(&release["production_release_state"],"disabled")?;eq(&release["provider_release_state"],"disabled")?;
        eq(&release["use_scope"],"personal_noncommercial_local_development")?;eq(&release["target_scope"],"current_pc_exact_identity_only")?;
        let sequence=payload["lineage"]["registry_sequence"].as_u64().filter(|n|*n>=1).ok_or(PinnedRegistryError::Binding)?;
        let minimum=policy["lineage"]["minimum_registry_sequence"].as_u64().ok_or(PinnedRegistryError::Binding)?;
        if sequence<minimum||sequence!=1||!payload["lineage"]["parent_payload_sha256"].is_null(){return Err(PinnedRegistryError::Binding);}
        let target=&payload["target"];
        for field in["profile_id","exact_build","architecture","executable_sha256"]{if target[field]!=policy["target"][field]{return Err(PinnedRegistryError::Target);}}
        let target_profile=ExactTargetProfile::new(TargetProfileId::parse(text(&target["profile_id"])?.to_owned()).map_err(|_|PinnedRegistryError::Target)?,
            text(&target["exact_build"])?,match text(&target["architecture"])?{"x86"=>Architecture::X86,"x64"=>Architecture::X86_64,"arm64"=>Architecture::Arm64,_=>return Err(PinnedRegistryError::Target)})
            .map_err(|_|PinnedRegistryError::Target)?;
        let source=&payload["source_registry"];eq(&source["encoding"],"base64")?;eq(&source["sha256"],REGISTRY_SHA)?;
        let raw_registry=base64::decode(text(&source["bytes_base64"])?,MAX_REGISTRY)?;
        if hex::encode(hash(&raw_registry))!=REGISTRY_SHA{return Err(PinnedRegistryError::Binding);}
        let registry=strict(&raw_registry,MAX_REGISTRY)?;
        for field in["profile_id","product","major_release","exact_build","locale","architecture","profile_sha256"]{
            if registry["target"][field]!=target[field]{return Err(PinnedRegistryError::Target);}
        }
        let qualification=&payload["qualification"];disabled(&qualification["routing_enabled"])?;
        eq(&qualification["state"],"partially_qualified_scoped_current_target")?;
        let rows=qualification["bindings"].as_array().filter(|v|!v.is_empty()&&v.len()<=100_000).ok_or(PinnedRegistryError::Shape)?;
        let original_rows=registry["bindings"].as_array().ok_or(PinnedRegistryError::Shape)?;
        let mut original=BTreeMap::new();
        for row in original_rows{let id=capability(&row["capability_id"])?;if original.insert(id,row).is_some(){return Err(PinnedRegistryError::Binding);}}
        let mut counts=SignedRegistryCounts{bindings:rows.len(),candidates:0,unavailable:0,verified_claims:0,failed_claims:0,blocked_claims:0,not_run_claims:0};
        let mut claims=BTreeMap::new();
        for row in rows{
            disabled(&row["routing_enabled"])?;let id=capability(&row["capability_id"])?;let original=original.get(&id).ok_or(PinnedRegistryError::Binding)?;
            for field in["binding_key","feature_id","capability_id"]{if row[field]!=original[field]{return Err(PinnedRegistryError::Binding);}}
            match text(&row["source_status"])?{"candidate_unverified"=>counts.candidates+=1,"unavailable_with_reason"=>counts.unavailable+=1,_=>return Err(PinnedRegistryError::Shape)}
            let state=match text(&row["runtime_support_state"])?{
                "verified_current_target"=>{counts.verified_claims+=1;SignedSupportClaim::VerifiedCurrentTarget},
                "failed_current_target"=>{counts.failed_claims+=1;SignedSupportClaim::FailedCurrentTarget},
                "blocked_by_policy"=>{counts.blocked_claims+=1;SignedSupportClaim::BlockedByPolicy},
                "unverified_not_run"=>{counts.not_run_claims+=1;SignedSupportClaim::UnverifiedNotRun},"unavailable"=>SignedSupportClaim::Unavailable,
                _=>return Err(PinnedRegistryError::Shape)};
            if claims.insert(id,state).is_some(){return Err(PinnedRegistryError::Binding);}
        }
        if claims.len()!=original.len(){return Err(PinnedRegistryError::Binding);}
        let coverage=&qualification["coverage"];
        for(field,count)in[("binding_count",counts.bindings),("candidate_count",counts.candidates),("unavailable_count",counts.unavailable),
            ("verified_count",counts.verified_claims),("failed_count",counts.failed_claims),("blocked_by_risk_count",counts.blocked_claims),("not_run_count",counts.not_run_claims),("routing_enabled_count",0)]{
            if coverage[field].as_u64()!=u64::try_from(count).ok(){return Err(PinnedRegistryError::Binding);}
        }
        Ok(Self{receipt:PinnedP02RegistryReceipt{profile:PINNED_P02_REGISTRY_PROFILE,envelope_sha256:hash(input.envelope),payload_sha256:payload_sha,
            registry_sha256:hash(&raw_registry),trust_policy_sha256:hash(input.policy),public_key_sha256:hash(input.public_key),registry_sequence:sequence,counts,
            signature_verified:true,routing_enabled:false,execution_authority:false,runtime_probe_reexecuted:false,current_installed_target_observed:false},
            target:target_profile,claims})
    }
    #[must_use]pub const fn receipt(&self)->&PinnedP02RegistryReceipt{&self.receipt}
    #[must_use]pub const fn signed_target(&self)->&ExactTargetProfile{&self.target}
    /// Authenticated historical claim lookup, not a CapabilityRouter SupportState or current probe.
    #[must_use]pub fn signed_claim(&self,capability:&CapabilityId)->Option<SignedSupportClaim>{self.claims.get(capability).copied()}
    /// # Errors
    /// This preserved P02 schema and pinned policy disable every executable route, including its verified claims.
    pub fn require_routing(&self)->Result<(),PinnedRegistryError>{Err(PinnedRegistryError::RoutingDisabled)}
}
impl StoredProductRequest{
    /// # Errors
    /// Closed schema classification, then real authenticated registry policy before any source/candidate work.
    /// The preserved P02 evidence is deliberately non-executable; no fallback to caller trust/support flags.
    pub fn prepare_compiled_search_json_with_pinned_registry<R,B,S,V>(provider:&StoredFormProvider<'_,R,B,S,V>,raw:&[u8],
        limits:SearchMutationLimits,registry:&PinnedP02RegistryEvidence,now:u64)->Result<PreparedCompiledSearchMutation,RegistryBoundSearchError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        if !matches!(request::classify(raw).map_err(CompiledSearchError::from)?,request::Kind::SearchMutation(_)){return Err(CompiledSearchError::Kind.into());}
        registry.require_routing()?;Ok(Self::prepare_compiled_search_json(provider,raw,limits,now)?)
    }
}
fn hash(raw:&[u8])->[u8;32]{Sha256::digest(raw).into()}
fn pin(raw:&[u8],maximum:usize,expected:&str)->Result<(),PinnedRegistryError>{
    if raw.is_empty()||raw.len()>maximum{return Err(PinnedRegistryError::Limit);}
    if hex::encode(hash(raw))!=expected.to_ascii_lowercase(){return Err(PinnedRegistryError::Pin);}Ok(())
}
fn strict(raw:&[u8],maximum:usize)->Result<Value,PinnedRegistryError>{
    if raw.is_empty()||raw.len()>maximum{return Err(PinnedRegistryError::Limit);}
    let mut d=serde_json::Deserializer::from_slice(raw);let _=crate::form_product_request::UniqueJson::deserialize(&mut d).map_err(|_|PinnedRegistryError::Shape)?;
    d.end().map_err(|_|PinnedRegistryError::Shape)?;let value:Value=serde_json::from_slice(raw).map_err(|_|PinnedRegistryError::Shape)?;
    if !value.is_object(){return Err(PinnedRegistryError::Shape);}Ok(value)
}
fn object(value:&Value,keys:&[&str])->Result<(),PinnedRegistryError>{
    let map=value.as_object().ok_or(PinnedRegistryError::Shape)?;
    if map.len()!=keys.len()||keys.iter().any(|k|!map.contains_key(*k)){return Err(PinnedRegistryError::Shape);}Ok(())
}
fn text(v:&Value)->Result<&str,PinnedRegistryError>{v.as_str().ok_or(PinnedRegistryError::Shape)}
fn eq(v:&Value,expected:&str)->Result<(),PinnedRegistryError>{if text(v)?!=expected{return Err(PinnedRegistryError::Binding);}Ok(())}
fn disabled(v:&Value)->Result<(),PinnedRegistryError>{if v!=false{return Err(PinnedRegistryError::Scope);}Ok(())}
fn capability(v:&Value)->Result<CapabilityId,PinnedRegistryError>{CapabilityId::parse(text(v)?.to_owned()).map_err(|_|PinnedRegistryError::Shape)}
fn pem(raw:&[u8])->Result<Vec<u8>,PinnedRegistryError>{
    let text=std::str::from_utf8(raw).map_err(|_|PinnedRegistryError::Encoding)?;
    let body=text.strip_prefix("-----BEGIN PUBLIC KEY-----\n").and_then(|s|s.strip_suffix("-----END PUBLIC KEY-----\n")).ok_or(PinnedRegistryError::Encoding)?;
    let encoded=body.lines().collect::<String>();let der=base64::decode(&encoded,44)?;
    if der.len()!=44||der[..12]!=[0x30,0x2a,0x30,0x05,0x06,0x03,0x2b,0x65,0x70,0x03,0x21,0]{return Err(PinnedRegistryError::Encoding);}Ok(der)
}
fn verify_signature(der:&[u8],payload:&[u8],signature:&[u8])->Result<(),PinnedRegistryError>{
    if der.len()!=44||signature.len()!=64{return Err(PinnedRegistryError::Signature);}
    UnparsedPublicKey::new(&ED25519,&der[12..]).verify(payload,signature).map_err(|_|PinnedRegistryError::Signature)
}
#[derive(Clone,Copy,Debug,Eq,Error,PartialEq)]
pub enum PinnedRegistryError{
    #[error("pinned_p02_registry_input_limit")]Limit,
    #[error("pinned_p02_registry_frozen_identity_rejected")]Pin,
    #[error("pinned_p02_registry_json_shape_rejected")]Shape,
    #[error("pinned_p02_registry_encoding_rejected")]Encoding,
    #[error("pinned_p02_registry_signature_rejected")]Signature,
    #[error("pinned_p02_registry_target_rejected")]Target,
    #[error("pinned_p02_registry_binding_rejected")]Binding,
    #[error("pinned_p02_registry_scope_rejected")]Scope,
    #[error("pinned_p02_registry_routing_disabled")]RoutingDisabled,
}
#[derive(Debug,Error)]
pub enum RegistryBoundSearchError{
    #[error("registry_bound_search_registry_rejected")]Registry(#[from]PinnedRegistryError),
    #[error("registry_bound_search_original_product_rejected")]Product(#[from]CompiledSearchError),
}
