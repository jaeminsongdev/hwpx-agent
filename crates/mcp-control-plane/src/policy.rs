use std::collections::BTreeMap;
use std::fmt;

use artifact_service::{SubjectDigest, TenantId};
use auth_middleware::{AuthContext, TenantRole};
use serde_json::Value;
use thiserror::Error;

use crate::ToolKind;

pub const MAX_POLICY_PROJECTS: usize = 4_096;
pub const MAX_POLICY_MEMBERSHIPS: usize = 16_384;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ProjectAccess {
    Reader,
    Editor,
    Owner,
}

impl ProjectAccess {
    const fn can_write(self) -> bool {
        matches!(self, Self::Editor | Self::Owner)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ProjectPolicyLimits {
    projects: usize,
    memberships: usize,
}

impl ProjectPolicyLimits {
    /// Creates finite in-memory policy limits.
    ///
    /// # Errors
    ///
    /// Rejects zero or above-product-maximum capacities.
    pub fn new(projects: usize, memberships: usize) -> Result<Self, PolicyError> {
        if !(1..=MAX_POLICY_PROJECTS).contains(&projects)
            || !(1..=MAX_POLICY_MEMBERSHIPS).contains(&memberships)
        {
            return Err(PolicyError::InvalidConfiguration);
        }
        Ok(Self {
            projects,
            memberships,
        })
    }

    #[must_use]
    pub const fn product_maximums() -> Self {
        Self {
            projects: MAX_POLICY_PROJECTS,
            memberships: MAX_POLICY_MEMBERSHIPS,
        }
    }
}

#[derive(Clone, Copy, Debug, Error, Eq, PartialEq)]
pub enum PolicyError {
    #[error("project policy configuration is invalid")]
    InvalidConfiguration,
    #[error("project policy record was not found")]
    NotFound,
    #[error("project policy access is denied")]
    AccessDenied,
    #[error("project policy record conflicts with existing state")]
    Conflict,
    #[error("project policy capacity is exhausted")]
    CapacityExceeded,
}

pub trait ToolPolicy: fmt::Debug + Send + Sync {
    /// Authorizes one schema-valid call without producing a document/job/artifact effect.
    ///
    /// # Errors
    ///
    /// Implementations must fail closed on tenant, project, subject or role mismatch.
    fn authorize(
        &self,
        context: &AuthContext,
        tool: ToolKind,
        arguments: &Value,
    ) -> Result<(), PolicyError>;
}

pub struct InMemoryProjectPolicy {
    limits: ProjectPolicyLimits,
    projects: BTreeMap<String, TenantId>,
    memberships: BTreeMap<(String, SubjectDigest), ProjectAccess>,
}

impl InMemoryProjectPolicy {
    #[must_use]
    pub fn new(limits: ProjectPolicyLimits) -> Self {
        Self {
            limits,
            projects: BTreeMap::new(),
            memberships: BTreeMap::new(),
        }
    }

    /// Registers one exact project/tenant binding.
    ///
    /// # Errors
    ///
    /// Rejects malformed IDs, duplicates and exhausted capacity.
    pub fn register_project(
        &mut self,
        project_id: impl Into<String>,
        tenant_id: TenantId,
    ) -> Result<(), PolicyError> {
        let project_id = project_id.into();
        if !is_project_id(&project_id) {
            return Err(PolicyError::InvalidConfiguration);
        }
        if self.projects.contains_key(&project_id) {
            return Err(PolicyError::Conflict);
        }
        if self.projects.len() >= self.limits.projects {
            return Err(PolicyError::CapacityExceeded);
        }
        self.projects.insert(project_id, tenant_id);
        Ok(())
    }

    /// Registers one subject's project membership.
    ///
    /// # Errors
    ///
    /// Rejects unknown projects, duplicates and exhausted capacity.
    pub fn register_membership(
        &mut self,
        project_id: impl Into<String>,
        subject: SubjectDigest,
        access: ProjectAccess,
    ) -> Result<(), PolicyError> {
        let project_id = project_id.into();
        if !self.projects.contains_key(&project_id) {
            return Err(PolicyError::NotFound);
        }
        let key = (project_id, subject);
        if self.memberships.contains_key(&key) {
            return Err(PolicyError::Conflict);
        }
        if self.memberships.len() >= self.limits.memberships {
            return Err(PolicyError::CapacityExceeded);
        }
        self.memberships.insert(key, access);
        Ok(())
    }
}

impl ToolPolicy for InMemoryProjectPolicy {
    fn authorize(
        &self,
        context: &AuthContext,
        tool: ToolKind,
        arguments: &Value,
    ) -> Result<(), PolicyError> {
        if tool == ToolKind::ProjectCreate {
            return if matches!(
                context.tenant_role(),
                TenantRole::Editor | TenantRole::Owner
            ) {
                Ok(())
            } else {
                Err(PolicyError::AccessDenied)
            };
        }
        let project_id = arguments
            .get("project_id")
            .and_then(Value::as_str)
            .ok_or(PolicyError::InvalidConfiguration)?;
        let Some(tenant_id) = self.projects.get(project_id) else {
            return Err(PolicyError::NotFound);
        };
        if *tenant_id != context.tenant_id() {
            return Err(PolicyError::NotFound);
        }
        let Some(access) = self
            .memberships
            .get(&(project_id.to_owned(), context.subject()))
        else {
            return Err(PolicyError::NotFound);
        };
        if tool.requires_project_write() && !access.can_write() {
            return Err(PolicyError::AccessDenied);
        }
        Ok(())
    }
}

impl fmt::Debug for InMemoryProjectPolicy {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("InMemoryProjectPolicy")
            .field("limits", &self.limits)
            .field("project_count", &self.projects.len())
            .field("membership_count", &self.memberships.len())
            .finish()
    }
}

fn is_project_id(value: &str) -> bool {
    let Some(tail) = value.strip_prefix("prj_") else {
        return false;
    };
    (8..=120).contains(&tail.len())
        && tail
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
}
