use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::Serialize;
use sha2::{Digest as _, Sha256};
use thiserror::Error;

use crate::{
    AngleMicrodegrees, CapabilityId, ConversionReceipt, HwpUnit, LengthMicrometers, OperationId,
    PlanId, PointMilli, RatioMillionths, RationalInput, ResolvedTarget, RevisionId, Selector,
    SelectorError, SelectorExpectation, SelectorSnapshot, UnitError,
};

pub const OPERATION_PLAN_SCHEMA_VERSION: &str = "hwpx-agent.operation-plan/v2";
pub const CAPABILITY_DEFINITION_SCHEMA_VERSION: &str = "hwpx-agent.capability-definition/v1";

const HARD_MAX_OPERATIONS: usize = 100_000;
const HARD_MAX_CAPABILITY_DEFINITIONS: usize = 100_000;
const HARD_MAX_DEPENDENCIES: usize = 1_000_000;
const HARD_MAX_ARGUMENTS_PER_OPERATION: usize = 4_096;
const HARD_MAX_STRING_BYTES: usize = 1024 * 1024;
const HARD_MAX_TOTAL_ARGUMENT_BYTES: usize = 64 * 1024 * 1024;
const HARD_MAX_SERIALIZED_BYTES: usize = 256 * 1024 * 1024;
const MAX_ARGUMENT_NAME_BYTES: usize = 512;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct OperationPlanLimits {
    pub max_operations: usize,
    pub max_dependencies: usize,
    pub max_arguments_per_operation: usize,
    pub max_string_bytes: usize,
    pub max_total_argument_bytes: usize,
    pub max_serialized_bytes: usize,
}

impl Default for OperationPlanLimits {
    fn default() -> Self {
        Self {
            max_operations: 10_000,
            max_dependencies: 100_000,
            max_arguments_per_operation: 1_024,
            max_string_bytes: 256 * 1024,
            max_total_argument_bytes: 16 * 1024 * 1024,
            max_serialized_bytes: 64 * 1024 * 1024,
        }
    }
}

impl OperationPlanLimits {
    fn validate(self) -> Result<(), OperationPlanError> {
        let valid = self.max_operations > 0
            && self.max_operations <= HARD_MAX_OPERATIONS
            && self.max_dependencies > 0
            && self.max_dependencies <= HARD_MAX_DEPENDENCIES
            && self.max_arguments_per_operation > 0
            && self.max_arguments_per_operation <= HARD_MAX_ARGUMENTS_PER_OPERATION
            && self.max_string_bytes > 0
            && self.max_string_bytes <= HARD_MAX_STRING_BYTES
            && self.max_total_argument_bytes > 0
            && self.max_total_argument_bytes <= HARD_MAX_TOTAL_ARGUMENT_BYTES
            && self.max_serialized_bytes > 0
            && self.max_serialized_bytes <= HARD_MAX_SERIALIZED_BYTES;
        if !valid {
            return Err(OperationPlanError::InvalidLimit);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FailurePolicy {
    #[default]
    Atomic,
    BestEffort,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnsupportedSelectorKind {
    BareTextOffset,
    CursorSession,
    PagePosition,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SelectorDraft {
    pub variants: Vec<Selector>,
    pub unsupported: Option<UnsupportedSelectorKind>,
}

impl SelectorDraft {
    #[must_use]
    pub fn one(selector: Selector) -> Self {
        Self {
            variants: vec![selector],
            unsupported: None,
        }
    }

    #[must_use]
    pub fn unsupported(kind: UnsupportedSelectorKind) -> Self {
        Self {
            variants: Vec::new(),
            unsupported: Some(kind),
        }
    }
}

impl fmt::Debug for SelectorDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("SelectorDraft")
            .field("variant_count", &self.variants.len())
            .field("unsupported", &self.unsupported.is_some())
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NumericUnit {
    Millimeter,
    Point,
    HwpUnit,
    Pixel { dpi: u32 },
    Ratio,
    Percent,
    Degree,
}

#[derive(Clone, Copy, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NumericArgumentDraft {
    pub value: RationalInput,
    pub unit: Option<NumericUnit>,
}

impl fmt::Debug for NumericArgumentDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("NumericArgumentDraft(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "value_type", content = "value", rename_all = "snake_case")]
pub enum ArgumentDraft {
    Text(String),
    Boolean(bool),
    Integer(i64),
    Numeric(NumericArgumentDraft),
}

impl fmt::Debug for ArgumentDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Text(_) => "ArgumentDraft::Text(<redacted>)",
            Self::Boolean(_) => "ArgumentDraft::Boolean(<redacted>)",
            Self::Integer(_) => "ArgumentDraft::Integer(<redacted>)",
            Self::Numeric(_) => "ArgumentDraft::Numeric(<redacted>)",
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArgumentKind {
    Text { max_bytes: usize },
    Boolean,
    Integer { minimum: i64, maximum: i64 },
    Length,
    Typography,
    Ratio,
    Angle,
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DefaultPolicy {
    #[default]
    Fallback,
    Locked,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ArgumentSpec {
    pub kind: ArgumentKind,
    pub required: bool,
    pub default: Option<ArgumentDraft>,
    pub default_policy: DefaultPolicy,
}

impl fmt::Debug for ArgumentSpec {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("ArgumentSpec")
            .field("kind", &self.kind)
            .field("required", &self.required)
            .field("has_default", &self.default.is_some())
            .field("default_policy", &self.default_policy)
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CapabilityDefinitionDraft {
    pub schema_version: String,
    pub capability_id: CapabilityId,
    pub arguments: BTreeMap<String, ArgumentSpec>,
}

impl CapabilityDefinitionDraft {
    #[must_use]
    pub fn new(capability_id: CapabilityId) -> Self {
        Self {
            schema_version: CAPABILITY_DEFINITION_SCHEMA_VERSION.to_owned(),
            capability_id,
            arguments: BTreeMap::new(),
        }
    }
}

impl fmt::Debug for CapabilityDefinitionDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapabilityDefinitionDraft")
            .field("argument_count", &self.arguments.len())
            .finish_non_exhaustive()
    }
}

pub struct CapabilityCatalog {
    definitions: BTreeMap<CapabilityId, CapabilityDefinitionDraft>,
}

impl CapabilityCatalog {
    /// Validates and freezes versioned capability argument/default definitions.
    ///
    /// # Errors
    ///
    /// Rejects wrong versions, duplicate IDs, invalid argument names/specs or defaults.
    pub fn from_drafts(drafts: Vec<CapabilityDefinitionDraft>) -> Result<Self, OperationPlanError> {
        if drafts.len() > HARD_MAX_CAPABILITY_DEFINITIONS {
            return Err(OperationPlanError::LimitExceeded);
        }
        let mut definitions = BTreeMap::new();
        let mut total_default_bytes = 0_usize;
        for draft in drafts {
            if draft.schema_version != CAPABILITY_DEFINITION_SCHEMA_VERSION {
                return Err(OperationPlanError::InvalidCapabilityDefinition);
            }
            if draft.arguments.len() > HARD_MAX_ARGUMENTS_PER_OPERATION {
                return Err(OperationPlanError::LimitExceeded);
            }
            for (name, spec) in &draft.arguments {
                validate_argument_name(name)
                    .map_err(|_| OperationPlanError::InvalidCapabilityDefinition)?;
                validate_argument_spec(spec)?;
                if let Some(default) = &spec.default {
                    total_default_bytes = total_default_bytes
                        .checked_add(name.len())
                        .and_then(|total| total.checked_add(argument_size(default)))
                        .ok_or(OperationPlanError::LimitExceeded)?;
                    if total_default_bytes > HARD_MAX_TOTAL_ARGUMENT_BYTES {
                        return Err(OperationPlanError::LimitExceeded);
                    }
                }
            }
            if definitions
                .insert(draft.capability_id.clone(), draft)
                .is_some()
            {
                return Err(OperationPlanError::DuplicateCapability);
            }
        }
        Ok(Self { definitions })
    }

    fn get(&self, capability_id: &CapabilityId) -> Option<&CapabilityDefinitionDraft> {
        self.definitions.get(capability_id)
    }
}

impl fmt::Debug for CapabilityCatalog {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CapabilityCatalog")
            .field("definition_count", &self.definitions.len())
            .finish()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OperationDraft {
    pub operation_id: OperationId,
    pub capability_id: CapabilityId,
    pub selector: SelectorDraft,
    pub arguments: BTreeMap<String, ArgumentDraft>,
    pub depends_on: Vec<OperationId>,
}

impl fmt::Debug for OperationDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("OperationDraft")
            .field("argument_count", &self.arguments.len())
            .field("dependency_count", &self.depends_on.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OperationPlanDraft {
    pub schema_version: String,
    pub plan_id: PlanId,
    pub base_revision: RevisionId,
    pub failure_policy: Option<FailurePolicy>,
    pub operations: Vec<OperationDraft>,
}

impl OperationPlanDraft {
    #[must_use]
    pub fn new(
        plan_id: PlanId,
        base_revision: RevisionId,
        operations: Vec<OperationDraft>,
    ) -> Self {
        Self {
            schema_version: OPERATION_PLAN_SCHEMA_VERSION.to_owned(),
            plan_id,
            base_revision,
            failure_policy: None,
            operations,
        }
    }
}

impl fmt::Debug for OperationPlanDraft {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("OperationPlanDraft")
            .field("operation_count", &self.operations.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ArgumentSource {
    Caller,
    CapabilityDefault,
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(tag = "value_type", content = "value", rename_all = "snake_case")]
pub enum CanonicalArgumentValue {
    Text(String),
    Boolean(bool),
    Integer(i64),
    LengthMicrometers(LengthMicrometers),
    PointMilli(PointMilli),
    RatioMillionths(RatioMillionths),
    AngleMicrodegrees(AngleMicrodegrees),
}

impl fmt::Debug for CanonicalArgumentValue {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CanonicalArgumentValue(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledArgument {
    source: ArgumentSource,
    value: CanonicalArgumentValue,
    conversion_receipt: Option<ConversionReceipt>,
    value_sha256: [u8; 32],
}

impl CompiledArgument {
    #[must_use]
    pub const fn source(&self) -> ArgumentSource {
        self.source
    }

    #[must_use]
    pub const fn value(&self) -> &CanonicalArgumentValue {
        &self.value
    }

    #[must_use]
    pub const fn conversion_receipt(&self) -> Option<ConversionReceipt> {
        self.conversion_receipt
    }

    #[must_use]
    pub const fn value_sha256(&self) -> [u8; 32] {
        self.value_sha256
    }
}

impl fmt::Debug for CompiledArgument {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("CompiledArgument(<redacted>)")
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledOperation {
    operation_id: OperationId,
    capability_id: CapabilityId,
    target: ResolvedTarget,
    arguments: BTreeMap<String, CompiledArgument>,
    depends_on: Vec<OperationId>,
}

impl CompiledOperation {
    #[must_use]
    pub const fn operation_id(&self) -> &OperationId {
        &self.operation_id
    }

    #[must_use]
    pub const fn target(&self) -> &ResolvedTarget {
        &self.target
    }

    #[must_use]
    pub const fn arguments(&self) -> &BTreeMap<String, CompiledArgument> {
        &self.arguments
    }

    #[must_use]
    pub fn depends_on(&self) -> &[OperationId] {
        &self.depends_on
    }
}

impl fmt::Debug for CompiledOperation {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CompiledOperation")
            .field("argument_count", &self.arguments.len())
            .field("dependency_count", &self.depends_on.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledOperationPlan {
    schema_version: String,
    plan_id: PlanId,
    base_revision: RevisionId,
    base_graph_sha256: [u8; 32],
    failure_policy: FailurePolicy,
    operations: Vec<CompiledOperation>,
}

impl CompiledOperationPlan {
    #[must_use]
    pub fn operations(&self) -> &[CompiledOperation] {
        &self.operations
    }

    /// Emits deterministic compact JSON from the immutable compiled plan.
    ///
    /// # Errors
    ///
    /// Returns a stable serialization error.
    pub fn canonical_json(&self) -> Result<Vec<u8>, OperationPlanError> {
        serde_json::to_vec(self).map_err(|_| OperationPlanError::SerializationFailed)
    }

    /// Hashes deterministic compiled-plan bytes.
    ///
    /// # Errors
    ///
    /// Propagates a stable serialization error.
    pub fn canonical_sha256(&self) -> Result<[u8; 32], OperationPlanError> {
        Ok(Sha256::digest(self.canonical_json()?).into())
    }
}

impl fmt::Debug for CompiledOperationPlan {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("CompiledOperationPlan")
            .field("operation_count", &self.operations.len())
            .finish_non_exhaustive()
    }
}

#[derive(Clone, Copy, Debug, Eq, Error, PartialEq)]
pub enum OperationPlanError {
    #[error("operation-plan limit is invalid")]
    InvalidLimit,
    #[error("operation-plan schema version is unsupported")]
    UnsupportedVersion,
    #[error("operation-plan input exceeds a finite limit")]
    LimitExceeded,
    #[error("operation-plan contains no operation")]
    MissingOperation,
    #[error("operation ID is duplicated")]
    DuplicateOperation,
    #[error("capability ID is duplicated")]
    DuplicateCapability,
    #[error("capability definition is invalid")]
    InvalidCapabilityDefinition,
    #[error("capability definition was not found")]
    CapabilityNotFound,
    #[error("operation dependency is invalid")]
    InvalidDependency,
    #[error("operation dependency graph contains a cycle")]
    Cycle,
    #[error("operation selector is invalid")]
    InvalidSelector,
    #[error("operation selector snapshot is stale")]
    StaleSelector,
    #[error("operation selector did not match")]
    SelectorNotFound,
    #[error("operation selector is ambiguous")]
    SelectorAmbiguous,
    #[error("operation-plan requires explicit resolution")]
    NeedsResolution,
    #[error("operation argument is invalid")]
    InvalidArgument,
    #[error("operation unit conversion failed")]
    UnitConversion,
    #[error("compiled operation-plan serialization failed")]
    SerializationFailed,
}

impl OperationPlanError {
    #[must_use]
    pub const fn code(self) -> &'static str {
        match self {
            Self::InvalidLimit => "operation_plan_invalid_limit",
            Self::UnsupportedVersion => "operation_plan_unsupported_version",
            Self::LimitExceeded => "operation_plan_limit_exceeded",
            Self::MissingOperation => "operation_plan_missing_operation",
            Self::DuplicateOperation => "operation_plan_duplicate_operation",
            Self::DuplicateCapability => "operation_plan_duplicate_capability",
            Self::InvalidCapabilityDefinition => "operation_plan_invalid_capability_definition",
            Self::CapabilityNotFound => "operation_plan_capability_not_found",
            Self::InvalidDependency => "operation_plan_invalid_dependency",
            Self::Cycle => "operation_plan_cycle",
            Self::InvalidSelector => "operation_plan_invalid_selector",
            Self::StaleSelector => "operation_plan_stale_selector",
            Self::SelectorNotFound => "operation_plan_selector_not_found",
            Self::SelectorAmbiguous => "operation_plan_selector_ambiguous",
            Self::NeedsResolution => "operation_plan_needs_resolution",
            Self::InvalidArgument => "operation_plan_invalid_argument",
            Self::UnitConversion => "operation_plan_unit_conversion",
            Self::SerializationFailed => "operation_plan_serialization_failed",
        }
    }
}

pub struct OperationPlanCompiler {
    limits: OperationPlanLimits,
}

impl OperationPlanCompiler {
    /// Creates a compiler after validating all finite bounds.
    ///
    /// # Errors
    ///
    /// Rejects zero or excessive limits.
    pub fn new(limits: OperationPlanLimits) -> Result<Self, OperationPlanError> {
        limits.validate()?;
        Ok(Self { limits })
    }

    /// Compiles a complete plan or returns no compiled output.
    ///
    /// # Errors
    ///
    /// Fails closed on schema, identity, selector, argument/default, unit, dependency, cycle and
    /// serialization errors.
    pub fn compile(
        &self,
        draft: OperationPlanDraft,
        catalog: &CapabilityCatalog,
        snapshot: &SelectorSnapshot,
        expectation: &SelectorExpectation,
    ) -> Result<CompiledOperationPlan, OperationPlanError> {
        self.preflight(&draft, expectation)?;
        let order = Self::topological_order(&draft.operations)?;
        let by_id: BTreeMap<_, _> = draft
            .operations
            .iter()
            .map(|operation| (operation.operation_id.clone(), operation))
            .collect();
        let mut compiled = Vec::with_capacity(draft.operations.len());
        for operation_id in order {
            let operation = by_id
                .get(&operation_id)
                .copied()
                .ok_or(OperationPlanError::InvalidDependency)?;
            let definition = catalog
                .get(&operation.capability_id)
                .ok_or(OperationPlanError::CapabilityNotFound)?;
            let selector = compile_selector(&operation.selector)?;
            let target = snapshot
                .resolve_one(expectation, selector)
                .map_err(map_selector_error)?;
            let arguments = Self::compile_arguments(operation, definition)?;
            let mut dependencies = operation.depends_on.clone();
            dependencies.sort();
            compiled.push(CompiledOperation {
                operation_id: operation.operation_id.clone(),
                capability_id: operation.capability_id.clone(),
                target,
                arguments,
                depends_on: dependencies,
            });
        }
        let result = CompiledOperationPlan {
            schema_version: OPERATION_PLAN_SCHEMA_VERSION.to_owned(),
            plan_id: draft.plan_id,
            base_revision: draft.base_revision,
            base_graph_sha256: expectation.graph_sha256(),
            failure_policy: draft.failure_policy.unwrap_or_default(),
            operations: compiled,
        };
        if result.canonical_json()?.len() > self.limits.max_serialized_bytes {
            return Err(OperationPlanError::LimitExceeded);
        }
        Ok(result)
    }

    fn preflight(
        &self,
        draft: &OperationPlanDraft,
        expectation: &SelectorExpectation,
    ) -> Result<(), OperationPlanError> {
        if draft.schema_version != OPERATION_PLAN_SCHEMA_VERSION {
            return Err(OperationPlanError::UnsupportedVersion);
        }
        if &draft.base_revision != expectation.revision_id() {
            return Err(OperationPlanError::StaleSelector);
        }
        if draft.failure_policy == Some(FailurePolicy::BestEffort) {
            return Err(OperationPlanError::NeedsResolution);
        }
        if draft.operations.is_empty() {
            return Err(OperationPlanError::MissingOperation);
        }
        if draft.operations.len() > self.limits.max_operations {
            return Err(OperationPlanError::LimitExceeded);
        }
        let mut ids = BTreeSet::new();
        let mut dependency_count = 0_usize;
        let mut argument_bytes = 0_usize;
        for operation in &draft.operations {
            if !ids.insert(operation.operation_id.clone()) {
                return Err(OperationPlanError::DuplicateOperation);
            }
            if operation.arguments.len() > self.limits.max_arguments_per_operation {
                return Err(OperationPlanError::LimitExceeded);
            }
            dependency_count = dependency_count
                .checked_add(operation.depends_on.len())
                .ok_or(OperationPlanError::LimitExceeded)?;
            if dependency_count > self.limits.max_dependencies {
                return Err(OperationPlanError::LimitExceeded);
            }
            for (name, value) in &operation.arguments {
                validate_argument_name(name)?;
                argument_bytes = argument_bytes
                    .checked_add(name.len())
                    .and_then(|total| total.checked_add(argument_size(value)))
                    .ok_or(OperationPlanError::LimitExceeded)?;
                if argument_size(value) > self.limits.max_string_bytes
                    || argument_bytes > self.limits.max_total_argument_bytes
                {
                    return Err(OperationPlanError::LimitExceeded);
                }
            }
        }
        Ok(())
    }

    fn topological_order(
        operations: &[OperationDraft],
    ) -> Result<Vec<OperationId>, OperationPlanError> {
        let ids: BTreeSet<_> = operations
            .iter()
            .map(|operation| operation.operation_id.clone())
            .collect();
        let mut indegree: BTreeMap<OperationId, usize> =
            ids.iter().cloned().map(|id| (id, 0)).collect();
        let mut outgoing: BTreeMap<OperationId, BTreeSet<OperationId>> = BTreeMap::new();
        for operation in operations {
            let mut seen = BTreeSet::new();
            for dependency in &operation.depends_on {
                if dependency == &operation.operation_id
                    || !ids.contains(dependency)
                    || !seen.insert(dependency.clone())
                {
                    return Err(OperationPlanError::InvalidDependency);
                }
                let degree = indegree
                    .get_mut(&operation.operation_id)
                    .ok_or(OperationPlanError::InvalidDependency)?;
                *degree = degree
                    .checked_add(1)
                    .ok_or(OperationPlanError::LimitExceeded)?;
                let _ = outgoing
                    .entry(dependency.clone())
                    .or_default()
                    .insert(operation.operation_id.clone());
            }
        }
        let mut ready: BTreeSet<_> = indegree
            .iter()
            .filter_map(|(id, degree)| (*degree == 0).then_some(id.clone()))
            .collect();
        let mut ordered = Vec::with_capacity(operations.len());
        while let Some(next) = ready.pop_first() {
            ordered.push(next.clone());
            if let Some(children) = outgoing.get(&next) {
                for child in children {
                    let degree = indegree
                        .get_mut(child)
                        .ok_or(OperationPlanError::InvalidDependency)?;
                    *degree = degree
                        .checked_sub(1)
                        .ok_or(OperationPlanError::InvalidDependency)?;
                    if *degree == 0 {
                        let _ = ready.insert(child.clone());
                    }
                }
            }
        }
        if ordered.len() != operations.len() {
            return Err(OperationPlanError::Cycle);
        }
        Ok(ordered)
    }

    fn compile_arguments(
        operation: &OperationDraft,
        definition: &CapabilityDefinitionDraft,
    ) -> Result<BTreeMap<String, CompiledArgument>, OperationPlanError> {
        for name in operation.arguments.keys() {
            if !definition.arguments.contains_key(name) {
                return Err(OperationPlanError::InvalidArgument);
            }
        }
        let mut compiled = BTreeMap::new();
        for (name, spec) in &definition.arguments {
            let caller = operation.arguments.get(name);
            let selected = match (caller, &spec.default) {
                (Some(value), Some(default)) if spec.default_policy == DefaultPolicy::Locked => {
                    let caller_value =
                        normalize_argument(value, spec.kind, ArgumentSource::Caller)?;
                    let default_value =
                        normalize_argument(default, spec.kind, ArgumentSource::CapabilityDefault)?;
                    if caller_value.value != default_value.value {
                        return Err(OperationPlanError::NeedsResolution);
                    }
                    Some(caller_value)
                }
                (Some(value), _) => Some(normalize_argument(
                    value,
                    spec.kind,
                    ArgumentSource::Caller,
                )?),
                (None, Some(default)) => Some(normalize_argument(
                    default,
                    spec.kind,
                    ArgumentSource::CapabilityDefault,
                )?),
                (None, None) if spec.required => {
                    return Err(OperationPlanError::NeedsResolution);
                }
                (None, None) => None,
            };
            if let Some(value) = selected {
                let _ = compiled.insert(name.clone(), value);
            }
        }
        Ok(compiled)
    }
}

impl fmt::Debug for OperationPlanCompiler {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("OperationPlanCompiler")
            .field("limits", &self.limits)
            .finish()
    }
}

fn compile_selector(draft: &SelectorDraft) -> Result<&Selector, OperationPlanError> {
    if draft.unsupported.is_some() {
        if !draft.variants.is_empty() {
            return Err(OperationPlanError::InvalidSelector);
        }
        return Err(OperationPlanError::NeedsResolution);
    }
    if draft.variants.len() != 1 {
        return Err(OperationPlanError::InvalidSelector);
    }
    draft
        .variants
        .first()
        .ok_or(OperationPlanError::InvalidSelector)
}

fn map_selector_error(error: SelectorError) -> OperationPlanError {
    match error {
        SelectorError::Stale => OperationPlanError::StaleSelector,
        SelectorError::NotFound => OperationPlanError::SelectorNotFound,
        SelectorError::Ambiguous => OperationPlanError::SelectorAmbiguous,
        SelectorError::LimitExceeded | SelectorError::InvalidLimit => {
            OperationPlanError::LimitExceeded
        }
        SelectorError::InvalidSelector
        | SelectorError::InvalidGraphMetadata
        | SelectorError::SerializationFailed => OperationPlanError::InvalidSelector,
    }
}

fn validate_argument_name(name: &str) -> Result<(), OperationPlanError> {
    if name.is_empty()
        || name.len() > MAX_ARGUMENT_NAME_BYTES
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.'))
    {
        return Err(OperationPlanError::InvalidArgument);
    }
    Ok(())
}

fn validate_argument_spec(spec: &ArgumentSpec) -> Result<(), OperationPlanError> {
    match spec.kind {
        ArgumentKind::Text { max_bytes } if max_bytes == 0 || max_bytes > HARD_MAX_STRING_BYTES => {
            return Err(OperationPlanError::InvalidCapabilityDefinition);
        }
        ArgumentKind::Integer { minimum, maximum } if minimum > maximum => {
            return Err(OperationPlanError::InvalidCapabilityDefinition);
        }
        ArgumentKind::Text { .. }
        | ArgumentKind::Boolean
        | ArgumentKind::Integer { .. }
        | ArgumentKind::Length
        | ArgumentKind::Typography
        | ArgumentKind::Ratio
        | ArgumentKind::Angle => {}
    }
    if let Some(default) = &spec.default {
        normalize_argument(default, spec.kind, ArgumentSource::CapabilityDefault)
            .map_err(|_| OperationPlanError::InvalidCapabilityDefinition)?;
    }
    Ok(())
}

fn normalize_argument(
    draft: &ArgumentDraft,
    kind: ArgumentKind,
    source: ArgumentSource,
) -> Result<CompiledArgument, OperationPlanError> {
    let (value, receipt) = match (draft, kind) {
        (ArgumentDraft::Text(value), ArgumentKind::Text { max_bytes }) => {
            if value.len() > max_bytes
                || value
                    .chars()
                    .any(|character| character.is_control() && !matches!(character, '\n' | '\t'))
            {
                return Err(OperationPlanError::InvalidArgument);
            }
            (CanonicalArgumentValue::Text(value.clone()), None)
        }
        (ArgumentDraft::Boolean(value), ArgumentKind::Boolean) => {
            (CanonicalArgumentValue::Boolean(*value), None)
        }
        (ArgumentDraft::Integer(value), ArgumentKind::Integer { minimum, maximum }) => {
            if value < &minimum || value > &maximum {
                return Err(OperationPlanError::InvalidArgument);
            }
            (CanonicalArgumentValue::Integer(*value), None)
        }
        (ArgumentDraft::Numeric(value), numeric_kind) => {
            let unit = value.unit.ok_or(OperationPlanError::NeedsResolution)?;
            normalize_numeric(value.value, unit, numeric_kind)?
        }
        _ => return Err(OperationPlanError::InvalidArgument),
    };
    let value_sha256 = Sha256::digest(
        serde_json::to_vec(&value).map_err(|_| OperationPlanError::SerializationFailed)?,
    )
    .into();
    Ok(CompiledArgument {
        source,
        value,
        conversion_receipt: receipt,
        value_sha256,
    })
}

fn normalize_numeric(
    value: RationalInput,
    unit: NumericUnit,
    kind: ArgumentKind,
) -> Result<(CanonicalArgumentValue, Option<ConversionReceipt>), OperationPlanError> {
    let converted = match (kind, unit) {
        (ArgumentKind::Length, NumericUnit::Millimeter) => {
            let conversion = LengthMicrometers::from_millimeters(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::LengthMicrometers(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Length, NumericUnit::Point) => {
            let conversion = LengthMicrometers::from_points(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::LengthMicrometers(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Length, NumericUnit::HwpUnit) => {
            if value.denominator() != 1 {
                return Err(OperationPlanError::InvalidArgument);
            }
            let conversion = LengthMicrometers::from_hwp_unit(HwpUnit::from_raw(value.numerator()))
                .map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::LengthMicrometers(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Length, NumericUnit::Pixel { dpi }) => {
            let conversion = LengthMicrometers::from_pixels(value, dpi).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::LengthMicrometers(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Typography, NumericUnit::Point) => {
            let conversion = PointMilli::from_points(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (CanonicalArgumentValue::PointMilli(value), Some(receipt))
        }
        (ArgumentKind::Ratio, NumericUnit::Ratio) => {
            let conversion = RatioMillionths::from_ratio(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::RatioMillionths(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Ratio, NumericUnit::Percent) => {
            let conversion = RatioMillionths::from_percent(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::RatioMillionths(value),
                Some(receipt),
            )
        }
        (ArgumentKind::Angle, NumericUnit::Degree) => {
            let conversion = AngleMicrodegrees::from_degrees(value).map_err(map_unit_error)?;
            let (value, receipt) = conversion.into_parts();
            (
                CanonicalArgumentValue::AngleMicrodegrees(value),
                Some(receipt),
            )
        }
        (
            ArgumentKind::Text { .. }
            | ArgumentKind::Boolean
            | ArgumentKind::Integer { .. }
            | ArgumentKind::Length
            | ArgumentKind::Typography
            | ArgumentKind::Ratio
            | ArgumentKind::Angle,
            _,
        ) => return Err(OperationPlanError::InvalidArgument),
    };
    Ok(converted)
}

const fn map_unit_error(_error: UnitError) -> OperationPlanError {
    OperationPlanError::UnitConversion
}

fn argument_size(argument: &ArgumentDraft) -> usize {
    match argument {
        ArgumentDraft::Text(value) => value.len(),
        ArgumentDraft::Boolean(_) | ArgumentDraft::Integer(_) | ArgumentDraft::Numeric(_) => {
            size_of::<ArgumentDraft>()
        }
    }
}
