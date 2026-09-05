//! Authenticated, short-lived storage of compiler-issued plans for plan review.
//!
//! This registry is process-local, not a durable plan repository or an execution permit. It has no
//! JSON import of compiled plans, document mutation, UI response, route verification or diff claim.
//! The future renderer must obtain route/dry-run evidence for the exact returned plan digest; a
//! semantic diff with the same before graph alone does not prove this plan produced its after graph.

use std::collections::BTreeMap;
use std::fmt;
use std::io::{self, Write};
use std::sync::Arc;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthContext, AuthMiddleware, AuthScope};
use domain_ir::{CompiledOperationPlan, DocumentGraph};
use serde::{Deserialize, Serialize};
use sha2::{Digest as _, Sha256};
use thiserror::Error;
use zeroize::Zeroizing;

use crate::policy::{PolicyError, ProjectPolicy};
use crate::strict_json::parse_unique_value;

const MAX_ENTRIES: usize = 256;
const MAX_PLAN_BYTES: usize = 1024 * 1024;
const MAX_TOTAL_BYTES: usize = 16 * 1024 * 1024;
const MAX_GRAPH_BYTES: usize = 64 * 1024 * 1024;
const MAX_LIFETIME_SECONDS: u64 = 900;
const MAX_LOOKUP_BYTES: usize = 2_048;

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum StoredPlanError {
    #[error("stored-plan authentication failed")]
    Unauthenticated,
    #[error("stored-plan request is invalid")]
    InvalidRequest,
    #[error("stored-plan configuration is invalid")]
    InvalidConfiguration,
    #[error("stored-plan resource was not found")]
    NotFound,
    #[error("stored-plan access is denied")]
    AccessDenied,
    #[error("stored-plan source has changed")]
    StaleSource,
    #[error("stored-plan identity conflicts with existing state")]
    Conflict,
    #[error("stored-plan capacity is exhausted")]
    CapacityExceeded,
    #[error("stored-plan source is unavailable or inconsistent")]
    SourceUnavailable,
    #[error("stored-plan server clock regressed")]
    ClockRegression,
}

#[derive(Clone, Copy, Debug)]
pub struct StoredPlanLimits {
    entries: usize,
    plan_bytes: usize,
    total_bytes: usize,
    lifetime_seconds: u64,
}

impl StoredPlanLimits {
    /// Creates bounded capacities; serialized bytes are an admission budget, not a heap-size claim.
    ///
    /// # Errors
    /// Rejects zero, inconsistent or above-product capacities.
    pub fn new(
        entries: usize,
        plan_bytes: usize,
        total_bytes: usize,
        lifetime_seconds: u64,
    ) -> Result<Self, StoredPlanError> {
        if !(1..=MAX_ENTRIES).contains(&entries)
            || !(1..=MAX_PLAN_BYTES).contains(&plan_bytes)
            || !(plan_bytes..=MAX_TOTAL_BYTES).contains(&total_bytes)
            || !(1..=MAX_LIFETIME_SECONDS).contains(&lifetime_seconds)
        {
            return Err(StoredPlanError::InvalidConfiguration);
        }
        Ok(Self {
            entries,
            plan_bytes,
            total_bytes,
            lifetime_seconds,
        })
    }

    #[must_use]
    pub const fn product_maximums() -> Self {
        Self {
            entries: MAX_ENTRIES,
            plan_bytes: MAX_PLAN_BYTES,
            total_bytes: MAX_TOTAL_BYTES,
            lifetime_seconds: MAX_LIFETIME_SECONDS,
        }
    }
}

/// Repository receipt for the current authorized source, with an exact graph digest.
/// This does not establish that a package has passed rendering or preservation validation.
pub struct CurrentPlanSource {
    tenant_id: TenantId,
    project_id: String,
    revision_id: String,
    graph_sha256: [u8; 32],
}

impl CurrentPlanSource {
    /// Binds a server-loaded immutable graph to repository identities using bounded hashing.
    ///
    /// # Errors
    /// Rejects malformed public identities and oversized or unserializable graphs. The repository
    /// must first authorize ownership and establish that this is its current revision, not accept
    /// these values or the graph from a public request.
    pub fn from_graph(
        tenant_id: TenantId,
        project_id: impl Into<String>,
        revision_id: impl Into<String>,
        graph: &DocumentGraph,
    ) -> Result<Self, StoredPlanError> {
        let project_id = project_id.into();
        let revision_id = revision_id.into();
        if !public_id(&project_id, "prj_") || !public_id(&revision_id, "rev_") {
            return Err(StoredPlanError::InvalidRequest);
        }
        let (graph_sha256, _) = bounded_hash(graph, MAX_GRAPH_BYTES)?;
        Ok(Self {
            tenant_id,
            project_id,
            revision_id,
            graph_sha256,
        })
    }
}

impl fmt::Debug for CurrentPlanSource {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CurrentPlanSource")
            .finish_non_exhaustive()
    }
}

pub trait PlanSourceRepository: fmt::Debug + Send + Sync {
    /// Reads the current revision through the repository's current source/branch ACL.
    ///
    /// # Errors
    /// Re-check ownership on every call, hide cross-tenant/non-member existence and fail closed
    /// for an unavailable, unsealed or inconsistent source. Returned graph identity is rechecked
    /// against the authenticated scope and compiler receipt by the registry.
    fn current_source(
        &self,
        context: &AuthContext,
        project_id: &str,
    ) -> Result<CurrentPlanSource, StoredPlanError>;
}

/// Internal compiler submission, deliberately not deserializable from a public tool argument.
pub struct CompiledPlanSubmission {
    authorization_header: Zeroizing<String>,
    project_id: String,
    plan: CompiledOperationPlan,
    now_unix_seconds: u64,
}

impl CompiledPlanSubmission {
    /// `now_unix_seconds` must be supplied by the server clock, never a client argument.
    #[must_use]
    pub fn new(
        authorization_header: impl Into<String>,
        project_id: impl Into<String>,
        plan: CompiledOperationPlan,
        now_unix_seconds: u64,
    ) -> Self {
        Self {
            authorization_header: Zeroizing::new(authorization_header.into()),
            project_id: project_id.into(),
            plan,
            now_unix_seconds,
        }
    }
}

impl fmt::Debug for CompiledPlanSubmission {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CompiledPlanSubmission")
            .finish_non_exhaustive()
    }
}

pub struct PlanLookupRequest {
    authorization_header: Zeroizing<String>,
    arguments_json: Zeroizing<Vec<u8>>,
    now_unix_seconds: u64,
}

impl PlanLookupRequest {
    /// Arguments are the exact plan-review render request, with no client-supplied security facts.
    /// `now_unix_seconds` must come from the server clock.
    #[must_use]
    pub fn new(
        authorization_header: impl Into<String>,
        arguments_json: impl Into<Vec<u8>>,
        now_unix_seconds: u64,
    ) -> Self {
        Self {
            authorization_header: Zeroizing::new(authorization_header.into()),
            arguments_json: Zeroizing::new(arguments_json.into()),
            now_unix_seconds,
        }
    }
}

impl fmt::Debug for PlanLookupRequest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("PlanLookupRequest")
            .finish_non_exhaustive()
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LookupArguments {
    schema_version: String,
    client_surface: String,
    locale: String,
    project_id: String,
    source_revision_id: String,
    plan_id: String,
}

struct StoredPlan {
    owner: SubjectDigest,
    plan: CompiledOperationPlan,
    sha256: [u8; 32],
    stored_at: u64,
    expires_at: u64,
}

/// A request-scoped read result for internal renderer use, never an execution authorization.
/// Do not cache this result across requests; its authorization is checked only at lookup time.
pub struct AuthorizedStoredPlan {
    record: Arc<StoredPlan>,
}

impl AuthorizedStoredPlan {
    #[must_use]
    pub fn compiled_plan(&self) -> &CompiledOperationPlan {
        &self.record.plan
    }
    #[must_use]
    pub fn compiled_plan_sha256(&self) -> [u8; 32] {
        self.record.sha256
    }
}

impl fmt::Debug for AuthorizedStoredPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("AuthorizedStoredPlan")
            .finish_non_exhaustive()
    }
}

type PlanKey = (TenantId, String, String);

pub struct StoredPlanRegistry {
    limits: StoredPlanLimits,
    records: BTreeMap<PlanKey, Arc<StoredPlan>>,
    total_bytes: usize,
    observed_now: Option<u64>,
}

impl fmt::Debug for StoredPlanRegistry {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("StoredPlanRegistry")
            .field("limits", &self.limits)
            .field("entry_count", &self.records.len())
            .field("serialized_bytes", &self.total_bytes)
            .field("observed_now", &self.observed_now)
            .finish()
    }
}

impl StoredPlanRegistry {
    #[must_use]
    pub fn new(limits: StoredPlanLimits) -> Self {
        Self {
            limits,
            records: BTreeMap::new(),
            total_bytes: 0,
            observed_now: None,
        }
    }

    /// Stores a compiler-issued plan only after fresh write authorization and source binding.
    /// Existing identities are never replaced and duplicate submissions do not extend lifetimes.
    ///
    /// # Errors
    /// Rejects authentication/ACL/source mismatches, conflicting identities and bounded capacity.
    pub fn insert<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: CompiledPlanSubmission,
    ) -> Result<(), StoredPlanError> {
        self.observe_clock(request.now_unix_seconds)?;
        let context = authenticate(
            auth,
            &request.authorization_header,
            request.now_unix_seconds,
            AuthScope::ProjectWrite,
        )?;
        let plan = request.plan;
        if !public_id(&request.project_id, "prj_")
            || !public_id(plan.plan_id().as_str(), "plan_")
            || !public_id(plan.base_revision().as_str(), "rev_")
        {
            return Err(StoredPlanError::InvalidRequest);
        }
        authorize(policy, &context, &request.project_id, true)?;
        check_source(sources, &context, &request.project_id, &plan)?;
        let (sha256, bytes) = bounded_hash(&plan, self.limits.plan_bytes)?;
        let now = request.now_unix_seconds;
        let expires_at = now
            .checked_add(self.limits.lifetime_seconds)
            .ok_or(StoredPlanError::InvalidRequest)?
            .min(context.expires_at_unix_seconds());
        if expires_at <= now {
            return Err(StoredPlanError::Unauthenticated);
        }
        let key = (
            context.tenant_id(),
            request.project_id,
            plan.plan_id().as_str().to_owned(),
        );
        // An expired record is not a license to reuse its identity during this registry lifetime.
        if let Some(existing) = self.records.get(&key) {
            return Err(if existing.owner == context.subject() {
                StoredPlanError::Conflict
            } else {
                StoredPlanError::NotFound
            });
        }
        if self.records.len() >= self.limits.entries
            || self
                .total_bytes
                .checked_add(bytes)
                .is_none_or(|size| size > self.limits.total_bytes)
        {
            return Err(StoredPlanError::CapacityExceeded);
        }
        self.total_bytes += bytes;
        self.records.insert(
            key,
            Arc::new(StoredPlan {
                owner: context.subject(),
                plan,
                sha256,
                stored_at: now,
                expires_at,
            }),
        );
        Ok(())
    }

    /// Resolves the exact short-lived plan after fresh token, project, owner and current-source checks.
    /// The response is not serializable and does not provide an execution permit or UI assertions.
    ///
    /// # Errors
    /// Rejects invalid/duplicate/extra JSON fields, missing scope, stale plans and all ownership drift.
    pub fn lookup<P: ProjectPolicy, R: PlanSourceRepository>(
        &mut self,
        auth: &mut AuthMiddleware,
        policy: &P,
        sources: &R,
        request: PlanLookupRequest,
    ) -> Result<AuthorizedStoredPlan, StoredPlanError> {
        let PlanLookupRequest {
            authorization_header,
            arguments_json,
            now_unix_seconds,
        } = request;
        self.observe_clock(now_unix_seconds)?;
        let context = authenticate(
            auth,
            &authorization_header,
            now_unix_seconds,
            AuthScope::ProjectRead,
        )?;
        drop(authorization_header);
        let arguments = parse_arguments(&arguments_json)?;
        drop(arguments_json);
        authorize(policy, &context, &arguments.project_id, false)?;
        let key = (
            context.tenant_id(),
            arguments.project_id.clone(),
            arguments.plan_id,
        );
        let record = self.records.get(&key).ok_or(StoredPlanError::NotFound)?;
        if record.owner != context.subject() {
            return Err(StoredPlanError::NotFound);
        }
        if now_unix_seconds < record.stored_at || now_unix_seconds >= record.expires_at {
            return Err(StoredPlanError::NotFound);
        }
        if record.plan.base_revision().as_str() != arguments.source_revision_id {
            return Err(StoredPlanError::StaleSource);
        }
        check_source(sources, &context, &arguments.project_id, &record.plan)?;
        Ok(AuthorizedStoredPlan {
            record: Arc::clone(record),
        })
    }

    fn observe_clock(&mut self, now: u64) -> Result<(), StoredPlanError> {
        if self.observed_now.is_some_and(|previous| now < previous) {
            return Err(StoredPlanError::ClockRegression);
        }
        self.observed_now = Some(now);
        Ok(())
    }
}

fn authenticate(
    auth: &mut AuthMiddleware,
    bearer: &str,
    now: u64,
    scope: AuthScope,
) -> Result<AuthContext, StoredPlanError> {
    let context = auth
        .authenticate_public_mcp(bearer, now, [scope])
        .map_err(|_| StoredPlanError::Unauthenticated)?;
    // A review receipt is not issued beyond exact token expiry even within validator clock skew.
    if context.expires_at_unix_seconds() <= now {
        return Err(StoredPlanError::Unauthenticated);
    }
    Ok(context)
}

fn authorize<P: ProjectPolicy>(
    policy: &P,
    context: &AuthContext,
    project_id: &str,
    write: bool,
) -> Result<(), StoredPlanError> {
    policy
        .authorize_project(context, project_id, write)
        .map_err(|error| match error {
            PolicyError::AccessDenied => StoredPlanError::AccessDenied,
            PolicyError::NotFound => StoredPlanError::NotFound,
            _ => StoredPlanError::SourceUnavailable,
        })
}

fn check_source<R: PlanSourceRepository>(
    sources: &R,
    context: &AuthContext,
    project_id: &str,
    plan: &CompiledOperationPlan,
) -> Result<(), StoredPlanError> {
    let source = sources.current_source(context, project_id)?;
    if source.tenant_id != context.tenant_id() || source.project_id != project_id {
        return Err(StoredPlanError::SourceUnavailable);
    }
    if source.revision_id != plan.base_revision().as_str()
        || source.graph_sha256 != plan.base_graph_sha256()
    {
        return Err(StoredPlanError::StaleSource);
    }
    Ok(())
}

fn parse_arguments(bytes: &[u8]) -> Result<LookupArguments, StoredPlanError> {
    if bytes.len() > MAX_LOOKUP_BYTES {
        return Err(StoredPlanError::InvalidRequest);
    }
    let value = parse_unique_value(bytes).map_err(|()| StoredPlanError::InvalidRequest)?;
    let args: LookupArguments =
        serde_json::from_value(value).map_err(|_| StoredPlanError::InvalidRequest)?;
    if args.schema_version != "hwpx-agent.plan-review-render-request/v1"
        || !matches!(
            args.client_surface.as_str(),
            "chatgpt_web" | "codex_remote" | "codex_local"
        )
        || !valid_locale(&args.locale)
        || !public_id(&args.project_id, "prj_")
        || !public_id(&args.source_revision_id, "rev_")
        || !public_id(&args.plan_id, "plan_")
    {
        return Err(StoredPlanError::InvalidRequest);
    }
    Ok(args)
}

fn public_id(value: &str, prefix: &str) -> bool {
    value.len() <= 124
        && value.strip_prefix(prefix).is_some_and(|tail| {
            (8..=120).contains(&tail.len())
                && tail
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
        })
}

fn valid_locale(value: &str) -> bool {
    if value.len() > 35 {
        return false;
    }
    let mut parts = value.split('-');
    let Some(language) = parts.next() else {
        return false;
    };
    if !(2..=3).contains(&language.len()) || !language.bytes().all(|b| b.is_ascii_lowercase()) {
        return false;
    }
    let mut region = parts.next();
    if let Some(script) = region.filter(|part| part.len() == 4) {
        if !script.as_bytes()[0].is_ascii_uppercase()
            || !script.as_bytes()[1..].iter().all(u8::is_ascii_lowercase)
        {
            return false;
        }
        region = parts.next();
    }
    region.is_none_or(|part| {
        (part.len() == 2 && part.bytes().all(|b| b.is_ascii_uppercase()))
            || (part.len() == 3 && part.bytes().all(|b| b.is_ascii_digit()))
    }) && parts.next().is_none()
}

struct BoundedHasher {
    hash: Sha256,
    bytes: usize,
    limit: usize,
}
impl Write for BoundedHasher {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let size = self
            .bytes
            .checked_add(bytes.len())
            .filter(|size| *size <= self.limit)
            .ok_or_else(|| io::Error::other("stored-plan byte limit"))?;
        self.hash.update(bytes);
        self.bytes = size;
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn bounded_hash(
    value: &impl Serialize,
    limit: usize,
) -> Result<([u8; 32], usize), StoredPlanError> {
    let mut writer = BoundedHasher {
        hash: Sha256::new(),
        bytes: 0,
        limit,
    };
    serde_json::to_writer(&mut writer, value).map_err(|_| StoredPlanError::CapacityExceeded)?;
    Ok((writer.hash.finalize().into(), writer.bytes))
}
