//! Authenticated private wire -> configured workspace -> trusted product runtime.
//! A saved private preview grants no public result, revision or Native authority.
use super::*;
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use std::fmt;

pub const BOOKMARK_PREVIEW_PROTOCOL: &str = "hwpx-agent.local-companion-private/v5";

/// Server-created binding; JSON cannot select a root or construct this identity.
#[derive(Clone, Eq, PartialEq)]
pub struct BookmarkWorkspaceBinding { config_sha256: String, workspace_id: String }
impl fmt::Debug for BookmarkWorkspaceBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("BookmarkWorkspaceBinding(<redacted>)") }
}
impl BookmarkWorkspaceBinding {
    #[must_use]
    pub fn matches(&self, context: &BookmarkWorkspaceContext<'_>) -> bool {
        self.config_sha256 == context.config_sha256 && self.workspace_id == context.workspace_id
    }
}

/// Constructed only after session, exact envelope, runtime and workspace checks.
pub struct BookmarkWorkspaceContext<'a> {
    config_sha256: &'a str, workspace_id: &'a str, operation_id: &'a str, workflow: &'a LocalWorkflow,
}
impl BookmarkWorkspaceContext<'_> {
    #[must_use] pub fn workflow(&self) -> &LocalWorkflow { self.workflow }
    #[must_use] pub fn operation_id(&self) -> &str { self.operation_id }
}

/// Trusted in-process implementation only. No callback, raw bytes or keys from JSON.
pub trait BookmarkPreviewRuntime {
    fn stage(&self, context: &BookmarkWorkspaceContext<'_>, product_request_json: &[u8], now: u64)
        -> Result<BookmarkPreviewMetadata, DaemonError>;
}

/// Closed, hash-only response. Text, paths, tokens and arbitrary runtime JSON cannot escape.
#[derive(Debug, Serialize)]
pub struct BookmarkPreviewMetadata {
    profile: &'static str, workspace_id: String, operation_id: String, config_sha256: String,
    canonical_request_sha256: String, scoped_request_sha256: String, compiled_plan_sha256: String,
    source_package_sha256: String, preview_package_sha256: String, preview_bytes: u64,
    private_preview_only: bool, public_output_or_revision_adoption_authority: bool,
}
impl BookmarkPreviewMetadata {
    /// # Errors
    /// Rejects invalid/zero identities and sizes; authority is always false.
    pub fn from_staging(context: &BookmarkWorkspaceContext<'_>, canonical: &str, scoped: &str,
        plan: &str, source: &str, preview: &str, bytes: u64) -> Result<Self, DaemonError> {
        if !(1..=MAX_FILE_BYTES_LIMIT).contains(&bytes) || [canonical, scoped, plan, source, preview]
            .iter().any(|v| v.len()!=64 || v.bytes().all(|c| c==b'0')
                || !v.bytes().all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))) {
            return Err(DaemonError::Request);
        }
        Ok(Self { profile:"hwpx-agent.local-bookmark-private-preview/v1", workspace_id:context.workspace_id.to_owned(),
            operation_id:context.operation_id.to_owned(), config_sha256:context.config_sha256.to_owned(),
            canonical_request_sha256:canonical.to_owned(), scoped_request_sha256:scoped.to_owned(),
            compiled_plan_sha256:plan.to_owned(), source_package_sha256:source.to_owned(), preview_package_sha256:preview.to_owned(),
            preview_bytes:bytes, private_preview_only:true, public_output_or_revision_adoption_authority:false })
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct StageParams { workspace_id: String, operation_id: String, product_request_json: String }

impl LocalCompanionConfig {
    /// Host setup only: bind an existing configured workspace, without file writes.
    /// # Errors
    /// Unknown/invalid workspace IDs fail closed.
    pub fn bookmark_preview_binding(&self, workspace_id: &str) -> Result<BookmarkWorkspaceBinding, DaemonError> {
        if !valid_identifier(workspace_id) || !self.workspaces.contains_key(workspace_id) { return Err(DaemonError::Workspace); }
        Ok(BookmarkWorkspaceBinding { config_sha256:self.digest.clone(), workspace_id:workspace_id.to_owned() })
    }
    pub(super) fn stage_bookmark_preview(&self, params: StageParams, runtime: Option<&dyn BookmarkPreviewRuntime>)
        -> Result<Value, DaemonError> {
        let runtime = runtime.ok_or(DaemonError::Request)?;
        if !valid_identifier(&params.workspace_id) || !valid_identifier(&params.operation_id)
            || params.product_request_json.is_empty() || params.product_request_json.len()>MAX_REQUEST_BYTES {
            return Err(DaemonError::Request);
        }
        let workflow = self.workflow(&params.workspace_id)?;
        let context = BookmarkWorkspaceContext { config_sha256:&self.digest, workspace_id:&params.workspace_id,
            operation_id:&params.operation_id, workflow:&workflow };
        let receipt = runtime.stage(&context, params.product_request_json.as_bytes(), current_unix_seconds()?)?;
        // A runtime cannot return metadata bound to another configured context.
        if receipt.config_sha256!=self.digest || receipt.workspace_id!=params.workspace_id
            || receipt.operation_id!=params.operation_id { return Err(DaemonError::Request); }
        serde_json::to_value(receipt).map_err(|_|DaemonError::Request)
    }
}

struct Unique;
impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D:serde::Deserializer<'de>>(d:D)->Result<Self,D::Error>{
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value=Unique;
            fn expecting(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("unique JSON")}
            fn visit_map<M:MapAccess<'de>>(self,mut m:M)->Result<Unique,M::Error>{
                let mut keys=BTreeSet::new();while let Some(k)=m.next_key::<String>()?{
                    if !keys.insert(k){return Err(de::Error::custom("duplicate key"));}m.next_value::<Unique>()?;
                }Ok(Unique)
            }
            fn visit_seq<S:SeqAccess<'de>>(self,mut s:S)->Result<Unique,S::Error>{while s.next_element::<Unique>()?.is_some(){}Ok(Unique)}
            fn visit_bool<E:de::Error>(self,_:bool)->Result<Unique,E>{Ok(Unique)}
            fn visit_i64<E:de::Error>(self,_:i64)->Result<Unique,E>{Ok(Unique)}
            fn visit_u64<E:de::Error>(self,_:u64)->Result<Unique,E>{Ok(Unique)}
            fn visit_f64<E:de::Error>(self,_:f64)->Result<Unique,E>{Ok(Unique)}
            fn visit_str<E:de::Error>(self,_:&str)->Result<Unique,E>{Ok(Unique)}
            fn visit_unit<E:de::Error>(self)->Result<Unique,E>{Ok(Unique)}
        }d.deserialize_any(V)
    }
}
pub(super) fn unique_request(bytes:&[u8])->Result<(),DaemonError>{
    let mut d=serde_json::Deserializer::from_slice(bytes);Unique::deserialize(&mut d).map_err(|_|DaemonError::Request)?;
    d.end().map_err(|_|DaemonError::Request)
}
