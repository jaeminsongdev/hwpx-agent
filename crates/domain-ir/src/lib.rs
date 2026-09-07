#![forbid(unsafe_code)]

mod capability_router;
mod document_graph;
mod identity;
mod operation_plan;
mod selector;
mod semantic_diff;
mod semantic_summary;
mod table_formula;
mod table_grid;
mod table_layout;
mod table_merge_split;
mod table_operations;
mod units;

pub use capability_router::{
    Architecture, BackendHealth, BackendHealthState, BackendKind,
    CAPABILITY_ROUTE_DECISION_SCHEMA_VERSION, CapabilityRouteCatalog, CapabilityRouter,
    CapabilityRouterError, CapabilityRouterLimits, ExactTargetProfile, PolicyScope,
    PreservationImpact, PreservationRequirement, ProtectionState, RegistryTrustState, RouteBinding,
    RouteContext, RouteDecision, RouteRestriction, SignatureImpact, SupportState,
};
pub use document_graph::{
    AccessibilityState, ArtifactRef, BreakKind, BreakNode, ChartNode,
    DOCUMENT_GRAPH_SCHEMA_VERSION, DocumentGraph, DocumentGraphDraft, DocumentGraphError,
    DocumentGraphLimits, DocumentId, DrawingNode, EmbeddedObjectNode, EmbeddedObjectType,
    EquationNode, EquationSource, FieldNode, Flow, FormControlNode, Inline, LogicalId, Node,
    NodeCommon, Note, OpaqueExtension, OpaquePreservation, ParagraphNode, Properties,
    PropertyValue, Provenance, Reference, Resource, ResourceKind, ReviewEntry, Section,
    SecurityState, SourceAnchorHandle, Style, TableCell, TableNode,
};
pub use identity::{
    ArtifactId, BackendId, BackendOpaqueId, BookmarkId, CapabilityId, ChangeId, FieldId,
    IdempotencyKey, IdentityError, LogicalNodeId, MAX_TYPED_ID_BYTES, OperationId, PlanId,
    ProjectId, ResourceId, RevisionId, StyleId, TargetProfileId, TransactionId,
};
pub use operation_plan::{
    ArgumentDraft, ArgumentKind, ArgumentSource, ArgumentSpec,
    CAPABILITY_DEFINITION_SCHEMA_VERSION, CanonicalArgumentValue, CapabilityCatalog,
    CapabilityDefinitionDraft, CompiledArgument, CompiledOperation, CompiledOperationPlan,
    DefaultPolicy, FailurePolicy, NumericArgumentDraft, NumericUnit, OPERATION_PLAN_SCHEMA_VERSION,
    OperationDraft, OperationPlanCompiler, OperationPlanDraft, OperationPlanError,
    OperationPlanLimits, SelectorDraft, UnsupportedSelectorKind,
};
pub use selector::{
    NamedSelectorKind, NodeKind, ResolvedTarget, Selector, SelectorError, SelectorExpectation,
    SelectorLimits, SelectorSnapshot, StructuralPath, StructuralRoot, StructuralStep,
    TextContextAnchor, TextRange,
};
pub use semantic_diff::{
    ChangeCategory, ChangeKind, EntityKind, PathScope, SEMANTIC_DIFF_SCHEMA_VERSION,
    SemanticChange, SemanticDiff, SemanticDiffError, SemanticDiffLimits, SemanticDiffSnapshot,
    SemanticPath,
};
pub use semantic_summary::{
    SemanticDiffSummary, SemanticSummaryCategory, SemanticSummaryError, SemanticSummaryKind,
    SemanticSummaryLimits,
};
pub use table_formula::{
    FormulaAst, FormulaAstDraft, FormulaBinaryOperator, FormulaCache, FormulaCachePolicy,
    FormulaCell, FormulaCellDraft, FormulaCellReference, FormulaDecimal, FormulaError,
    FormulaErrorValue, FormulaExpression, FormulaFunction, FormulaGridDimensions, FormulaGridEdit,
    FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaRange, FormulaReferenceKind,
    FormulaUnaryOperator, FormulaValue, TABLE_FORMULA_SCHEMA_VERSION,
};
pub use table_grid::{
    CellCoordinate, TABLE_GRID_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft,
    TableGridError, TableGridLimitConfig, TableGridLimits,
};
pub use table_layout::{
    CellWidthDeficit, FontMetricEvidence, FontMetricStatus, FontMetricVerification,
    TABLE_LAYOUT_SCHEMA_VERSION, TableCellMeasure, TableColumnConstraint, TableLayoutError,
    TableLayoutLimitConfig, TableLayoutLimits, TableLayoutObjective, TableLayoutPlan,
    TableLayoutProblem, TableLayoutSolver, TableWidthSpec,
};
pub use table_merge_split::{
    ContentPreservationPolicy, TABLE_MERGE_SPLIT_SCHEMA_VERSION, TableCellContent,
    TableContentState, TableContentTransfer, TableMergeSplitError, TableMergeSplitKind,
    TableMergeSplitReceipt, TableMergeSplitResult, TableRegion, TableSplitRequest,
};
pub use table_operations::{
    TABLE_OPERATIONS_SCHEMA_VERSION, TableCellRemap, TableDimensions, TableOperationError,
    TableOperationKind, TableOperationReceipt, TableOperationResult,
};
pub use units::{
    AngleMicrodegrees, Conversion, ConversionReceipt, CoordinateAnchor, CoordinateSpace, HwpUnit,
    LengthMicrometers, PointMilli, Position2D, RatioMillionths, RationalInput, UnitError, UnitKind,
    ZOrder,
};
