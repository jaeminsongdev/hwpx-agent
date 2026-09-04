//! Fail-closed MCP handler boundary for the P15 public tool surface.
//!
//! Transport and backend implementations are deliberately outside this crate. Every call follows
//! the same boundary: authenticate, validate input, authorize the tenant/project, dispatch once,
//! validate output, and return a bounded MCP result.

mod catalog;
mod handler;
mod policy;
mod strict_json;

pub use catalog::{CATALOG_SHA256, ToolKind};
pub use handler::{
    AuthorizedToolCall, GatewayError, McpControlPlane, McpToolRequest, McpToolResult,
    ToolServiceGateway,
};
pub use policy::{
    InMemoryProjectPolicy, PolicyError, ProjectAccess, ProjectPolicyLimits, ToolPolicy,
};
