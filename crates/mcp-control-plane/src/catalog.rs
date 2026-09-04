use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use auth_middleware::AuthScope;
use jsonschema::Validator;
use serde::Deserialize;
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

const CATALOG_BYTES: &[u8] = include_bytes!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../../protocol/mcp/p15-public-tools-v1.json"
));
pub const CATALOG_SHA256: &str = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001";
const CATALOG_SCHEMA_VERSION: &str = "hwpx-agent.mcp-public-tools/v1";

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum ToolKind {
    CapabilityCheck,
    DocumentPlan,
    DocumentCreate,
    DocumentInspect,
    DocumentEdit,
    DocumentTransform,
    TemplateAnalyze,
    DocumentValidate,
    DocumentRender,
    DocumentExport,
    ProjectCreate,
    ProjectOpen,
    ProjectHistory,
    ProjectCheckpoint,
    ProjectPublish,
    JobGet,
    JobCancel,
    ArtifactGet,
}

impl ToolKind {
    pub const ALL: [Self; 18] = [
        Self::CapabilityCheck,
        Self::DocumentPlan,
        Self::DocumentCreate,
        Self::DocumentInspect,
        Self::DocumentEdit,
        Self::DocumentTransform,
        Self::TemplateAnalyze,
        Self::DocumentValidate,
        Self::DocumentRender,
        Self::DocumentExport,
        Self::ProjectCreate,
        Self::ProjectOpen,
        Self::ProjectHistory,
        Self::ProjectCheckpoint,
        Self::ProjectPublish,
        Self::JobGet,
        Self::JobCancel,
        Self::ArtifactGet,
    ];

    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::CapabilityCheck => "capability_check",
            Self::DocumentPlan => "document_plan",
            Self::DocumentCreate => "document_create",
            Self::DocumentInspect => "document_inspect",
            Self::DocumentEdit => "document_edit",
            Self::DocumentTransform => "document_transform",
            Self::TemplateAnalyze => "template_analyze",
            Self::DocumentValidate => "document_validate",
            Self::DocumentRender => "document_render",
            Self::DocumentExport => "document_export",
            Self::ProjectCreate => "project_create",
            Self::ProjectOpen => "project_open",
            Self::ProjectHistory => "project_history",
            Self::ProjectCheckpoint => "project_checkpoint",
            Self::ProjectPublish => "project_publish",
            Self::JobGet => "job_get",
            Self::JobCancel => "job_cancel",
            Self::ArtifactGet => "artifact_get",
        }
    }

    #[must_use]
    pub fn parse(value: &str) -> Option<Self> {
        Self::ALL.into_iter().find(|kind| kind.name() == value)
    }

    #[must_use]
    pub const fn requires_project_write(self) -> bool {
        !matches!(
            self,
            Self::CapabilityCheck
                | Self::DocumentPlan
                | Self::ProjectOpen
                | Self::ProjectHistory
                | Self::JobGet
                | Self::ArtifactGet
                | Self::ProjectCreate
        )
    }
}

#[derive(Debug, Error)]
pub enum CatalogError {
    #[error("the embedded public tool catalog does not match its pinned digest")]
    DigestMismatch,
    #[error("the embedded public tool catalog is malformed")]
    Malformed,
    #[error("the embedded public tool catalog has an invalid schema")]
    InvalidSchema,
}

#[derive(Deserialize)]
struct RawCatalog {
    schema_version: String,
    descriptor_count: usize,
    tools: Vec<RawTool>,
}

#[derive(Deserialize)]
struct RawTool {
    name: String,
    #[serde(rename = "inputSchema")]
    input_schema: Value,
    #[serde(rename = "outputSchema")]
    output_schema: Value,
    #[serde(rename = "securitySchemes")]
    security_schemes: Vec<RawSecurityScheme>,
}

#[derive(Deserialize)]
struct RawSecurityScheme {
    #[serde(rename = "type")]
    kind: String,
    scopes: Vec<String>,
}

pub(crate) struct CompiledTool {
    input: Validator,
    output: Validator,
    scopes: Vec<AuthScope>,
}

pub(crate) struct ToolCatalog {
    tools: BTreeMap<ToolKind, CompiledTool>,
}

impl ToolCatalog {
    pub(crate) fn load() -> Result<Self, CatalogError> {
        if hex::encode(Sha256::digest(CATALOG_BYTES)) != CATALOG_SHA256 {
            return Err(CatalogError::DigestMismatch);
        }
        let raw: RawCatalog =
            serde_json::from_slice(CATALOG_BYTES).map_err(|_| CatalogError::Malformed)?;
        if raw.schema_version != CATALOG_SCHEMA_VERSION
            || raw.descriptor_count != ToolKind::ALL.len()
            || raw.tools.len() != ToolKind::ALL.len()
        {
            return Err(CatalogError::Malformed);
        }
        let mut tools = BTreeMap::new();
        for (index, descriptor) in raw.tools.into_iter().enumerate() {
            let expected = ToolKind::ALL[index];
            if ToolKind::parse(&descriptor.name) != Some(expected)
                || descriptor.security_schemes.len() != 1
                || descriptor.security_schemes[0].kind != "oauth2"
            {
                return Err(CatalogError::Malformed);
            }
            let mut unique_scopes = BTreeSet::new();
            let mut scopes = Vec::new();
            for value in &descriptor.security_schemes[0].scopes {
                let scope = scope_from_str(value).ok_or(CatalogError::Malformed)?;
                if !unique_scopes.insert(scope) {
                    return Err(CatalogError::Malformed);
                }
                scopes.push(scope);
            }
            if scopes.is_empty() {
                return Err(CatalogError::Malformed);
            }
            let input = jsonschema::validator_for(&descriptor.input_schema)
                .map_err(|_| CatalogError::InvalidSchema)?;
            let output = jsonschema::validator_for(&descriptor.output_schema)
                .map_err(|_| CatalogError::InvalidSchema)?;
            if tools
                .insert(
                    expected,
                    CompiledTool {
                        input,
                        output,
                        scopes,
                    },
                )
                .is_some()
            {
                return Err(CatalogError::Malformed);
            }
        }
        Ok(Self { tools })
    }

    pub(crate) fn get(&self, kind: ToolKind) -> &CompiledTool {
        &self.tools[&kind]
    }

    pub(crate) fn len(&self) -> usize {
        self.tools.len()
    }
}

impl CompiledTool {
    pub(crate) fn input_is_valid(&self, value: &Value) -> bool {
        self.input.is_valid(value)
    }

    pub(crate) fn output_is_valid(&self, value: &Value) -> bool {
        self.output.is_valid(value)
    }

    pub(crate) fn scopes(&self) -> &[AuthScope] {
        &self.scopes
    }
}

impl fmt::Debug for ToolCatalog {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ToolCatalog")
            .field("catalog_sha256", &CATALOG_SHA256)
            .field("tool_count", &self.tools.len())
            .finish()
    }
}

fn scope_from_str(value: &str) -> Option<AuthScope> {
    match value {
        "artifact.read" => Some(AuthScope::ArtifactRead),
        "artifact.write" => Some(AuthScope::ArtifactWrite),
        "job.cancel" => Some(AuthScope::JobCancel),
        "job.submit" => Some(AuthScope::JobSubmit),
        "mirror.sync" => Some(AuthScope::MirrorSync),
        "project.read" => Some(AuthScope::ProjectRead),
        "project.write" => Some(AuthScope::ProjectWrite),
        "retention.manage" => Some(AuthScope::RetentionManage),
        _ => None,
    }
}
