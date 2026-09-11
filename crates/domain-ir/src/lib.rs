#![forbid(unsafe_code)]

mod capability_router;
mod document_graph;
mod identity;
mod math_ast;
mod object_geometry;
mod operation_plan;
mod selector;
mod semantic_diff;
mod semantic_summary;
mod table_aggregate;
mod table_auto_fill;
mod table_chart;
mod table_formula;
mod table_geometry;
mod table_grid;
mod table_inspector;
mod table_layout;
mod table_merge_split;
mod table_number_format;
mod table_operations;
mod table_pagination;
mod table_partition;
mod table_placement;
mod table_properties;
mod table_ruling;
mod table_sort;
mod table_structure;
mod table_style;
mod table_text_conversion;
mod table_thousands;
mod table_transpose;
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
pub use math_ast::{
    MATH_AST_NORMALIZATION_VERSION, MATH_AST_SCHEMA_VERSION, MathAccent, MathAlignedLine,
    MathAnnotationKind, MathAst, MathAstDraft, MathAstError, MathAstLimitConfig, MathAstLimits,
    MathCase, MathColor, MathCombinatorialKind, MathDelimiter, MathDerivativeKind,
    MathDerivativeVariable, MathExpression, MathFunction, MathGreekLetter, MathLargeOperator,
    MathLetterCase, MathMatrixKind, MathNode, MathOperator, MathSourceSpan, MathStyleHint,
    MathSymbol, MathVariant,
};
pub use object_geometry::{
    OBJECT_GEOMETRY_SCHEMA_VERSION, ObjectAffineMatrix, ObjectAnchor, ObjectComponentGeometry,
    ObjectExtent, ObjectFlip, ObjectGeometryBuilder, ObjectGeometryError,
    ObjectGeometryLimitConfig, ObjectGeometryLimits, ObjectGeometryOperation, ObjectGeometryPlan,
    ObjectGeometryReceipt, ObjectGeometryRequest, ObjectGeometryRequestDraft, ObjectGeometryResult,
    ObjectGeometryState, ObjectGeometryStateDraft, ObjectHeightReference,
    ObjectHorizontalAlignment, ObjectHorizontalReference, ObjectKind, ObjectNumberingType,
    ObjectOuterMargins, ObjectPoint, ObjectPosition, ObjectRotation, ObjectSize, ObjectTextFlow,
    ObjectTextWrap, ObjectTransform, ObjectVerticalAlignment, ObjectVerticalReference,
    ObjectWidthReference, ObjectWrap,
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
pub use table_aggregate::{
    TABLE_AGGREGATE_SCHEMA_VERSION, TableAggregateAxis, TableAggregateBuilder, TableAggregateError,
    TableAggregatePlan, TableAggregateRange, TableAggregateRequest, TableAggregateRequestDraft,
};
pub use table_auto_fill::{
    TABLE_AUTO_FILL_CAPABILITY_ID, TABLE_AUTO_FILL_SCHEMA_VERSION,
    TABLE_AUTO_FILL_SERIES_CAPABILITY_ID, TABLE_AUTO_FILL_SERIES_SCHEMA_VERSION,
    TableAutoFillBuilder, TableAutoFillCellDraft, TableAutoFillDefinition, TableAutoFillError,
    TableAutoFillFormulaPolicy, TableAutoFillLimitConfig, TableAutoFillLimits,
    TableAutoFillMutation, TableAutoFillNumber, TableAutoFillOrder, TableAutoFillPlan,
    TableAutoFillReceipt, TableAutoFillRegion, TableAutoFillRequest, TableAutoFillRequestDraft,
    TableAutoFillSeries, TableAutoFillSeriesDraft, TableAutoFillValue,
};
pub use table_chart::{
    TABLE_CHART_FROM_TABLE_CAPABILITY_ID, TABLE_CHART_SCHEMA_VERSION, TableChartBuilder,
    TableChartCategory, TableChartCell, TableChartCellDraft, TableChartDataPoint, TableChartError,
    TableChartInitialType, TableChartInsertionContext, TableChartLimitConfig, TableChartLimits,
    TableChartPlan, TableChartReceipt, TableChartRegion, TableChartRequest, TableChartRequestDraft,
    TableChartSeries, TableChartSourceState, TableChartSourceStateDraft, TableChartValue,
    TableChartValueOrigin,
};
pub use table_formula::{
    FormulaAst, FormulaAstDraft, FormulaBinaryOperator, FormulaCache, FormulaCachePolicy,
    FormulaCell, FormulaCellDraft, FormulaCellReference, FormulaDecimal, FormulaError,
    FormulaErrorValue, FormulaExpression, FormulaFunction, FormulaGridDimensions, FormulaGridEdit,
    FormulaLimitConfig, FormulaLimits, FormulaNumberFormat, FormulaRange, FormulaReferenceKind,
    FormulaUnaryOperator, FormulaValue, TABLE_FORMULA_SCHEMA_VERSION,
};
pub use table_geometry::{
    TABLE_GEOMETRY_SCHEMA_VERSION, TableGeometryError, TableGeometryLimitConfig,
    TableGeometryLimits, TableGeometryOperation, TableGeometryReceipt, TableGeometryResult,
    TableGeometryState, TableGeometryStateDraft, TableTrackRange,
};
pub use table_grid::{
    CellCoordinate, TABLE_GRID_SCHEMA_VERSION, TableCellSpan, TableGrid, TableGridDraft,
    TableGridError, TableGridLimitConfig, TableGridLimits,
};
pub use table_inspector::{
    ResolvedTableCell, TABLE_INSPECTION_SCHEMA_VERSION, TableCellSelector, TableInspection,
    TableInspectionError, TableInspectionExpectation, TableInspectionLimitConfig,
    TableInspectionLimits, TableInspectionSnapshot, TableSelector,
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
pub use table_number_format::{
    TABLE_NUMBER_FORMAT_CAPABILITY_ID, TABLE_NUMBER_FORMAT_SCHEMA_VERSION,
    TableNumberFormatBuilder, TableNumberFormatCell, TableNumberFormatCellDraft,
    TableNumberFormatError, TableNumberFormatLimitConfig, TableNumberFormatLimits,
    TableNumberFormatPlan, TableNumberFormatReceipt, TableNumberFormatRequest,
    TableNumberFormatRequestDraft, TableNumberFormatState, TableNumberFormatStateDraft,
};
pub use table_operations::{
    TABLE_OPERATIONS_SCHEMA_VERSION, TableCellRemap, TableDimensions, TableOperationError,
    TableOperationKind, TableOperationReceipt, TableOperationResult,
};
pub use table_pagination::{
    CaptionSide, RowSplitEligibility, TABLE_PAGINATION_OBSERVATION_SCHEMA_VERSION,
    TABLE_PAGINATION_SCHEMA_VERSION, TableCaption, TablePage, TablePageItem, TablePageSplitPolicy,
    TablePaginationError, TablePaginationLimitConfig, TablePaginationLimits,
    TablePaginationObservation, TablePaginationPolicy, TablePaginationReceipt, TablePaginationRow,
    TablePaginationValidator,
};
pub use table_partition::{
    PlannedWholeTable, TABLE_JOIN_TABLE_CAPABILITY_ID, TABLE_PARTITION_SCHEMA_VERSION,
    TABLE_SPLIT_TABLE_CAPABILITY_ID, TableJoinSeparatorToken, TablePartitionBuilder,
    TablePartitionCell, TablePartitionCellDraft, TablePartitionError, TablePartitionFormulaPolicy,
    TablePartitionLimitConfig, TablePartitionLimits, TablePartitionState, TablePartitionStateDraft,
    WholeTableJoinPlan, WholeTableJoinReceipt, WholeTableJoinRequest, WholeTableJoinRequestDraft,
    WholeTableSplitPlan, WholeTableSplitReceipt, WholeTableSplitRequest,
    WholeTableSplitRequestDraft,
};
pub use table_placement::{
    TABLE_PLACEMENT_SCHEMA_VERSION, TableAttachmentMode, TableFloatingPlacement,
    TableHorizontalAlignment, TableHorizontalReference, TableOuterMargins, TablePlacementError,
    TablePlacementLimitConfig, TablePlacementLimits, TablePlacementOperation,
    TablePlacementReceipt, TablePlacementResult, TablePlacementState, TablePlacementStateDraft,
    TableTextFlow, TableTextWrap, TableVerticalAlignment, TableVerticalReference,
};
pub use table_properties::{
    TABLE_CELL_BORDER_EACH_CAPABILITY_ID, TABLE_CELL_BORDER_UNIFIED_CAPABILITY_ID,
    TABLE_CELL_DIAGONAL_CAPABILITY_ID, TABLE_PROPERTIES_CAPABILITY_ID,
    TABLE_PROPERTIES_SCHEMA_VERSION, TableBorderEdgeRole, TableCellBorderPatch,
    TableCellBorderState, TableCellPropertyDraft, TableCellPropertyMutation,
    TableCellPropertyValue, TableDiagonalApplyMode, TableDiagonalCenterLine, TableDiagonalPatch,
    TableDiagonalSlash, TableDiagonalSlashType, TableDiagonalValue, TablePropertiesBuilder,
    TablePropertiesError, TablePropertiesLimitConfig, TablePropertiesLimits,
    TablePropertiesOperation, TablePropertiesPlan, TablePropertiesReceipt, TablePropertiesRequest,
    TablePropertiesRequestDraft, TablePropertiesState, TablePropertiesStateDraft,
    TablePropertyDigestPatch, TablePropertyRegion, TableResolvedBorderRoles,
    TableUnifiedBorderPatch, table_diagonal_identity_sha256,
};
pub use table_ruling::{
    TABLE_DRAW_CAPABILITY_ID, TABLE_ERASER_CAPABILITY_ID, TABLE_RULING_SCHEMA_VERSION,
    TableRulingAxis, TableRulingBuilder, TableRulingCell, TableRulingCellDraft,
    TableRulingCellProperties, TableRulingDiagonalDirection, TableRulingEdge, TableRulingError,
    TableRulingFormulaPolicy, TableRulingFrame, TableRulingLimitConfig, TableRulingLimits,
    TableRulingOperation, TableRulingPayloadBlock, TableRulingPlan, TableRulingPlanKind,
    TableRulingPlannedGrid, TableRulingReceipt, TableRulingRequest, TableRulingRequestDraft,
    TableRulingState, TableRulingStateDraft, TableRulingStroke,
};
pub use table_sort::{
    TABLE_SORT_CAPABILITY_ID, TABLE_SORT_SCHEMA_VERSION, TableBlankOrder, TableFormulaMovePolicy,
    TableSortAxis, TableSortBuilder, TableSortCellDraft, TableSortDirection, TableSortError,
    TableSortKey, TableSortLimitConfig, TableSortLimits, TableSortPlan, TableSortReceipt,
    TableSortRegion, TableSortRelocation, TableSortRequest, TableSortRequestDraft, TableSortValue,
    TableTextCollation,
};
pub use table_structure::{
    TABLE_DELETE_COLUMNS_CAPABILITY_ID, TABLE_DELETE_ROWS_CAPABILITY_ID,
    TABLE_INSERT_COLUMNS_CAPABILITY_ID, TABLE_INSERT_ROWS_CAPABILITY_ID,
    TABLE_STRUCTURE_SCHEMA_VERSION, TableStructureBuilder, TableStructureError,
    TableStructureLimitConfig, TableStructureLimits, TableStructureOperation, TableStructurePlan,
    TableStructureReceipt, TableStructureRequest, TableStructureRequestDraft,
};
pub use table_style::{
    TABLE_STYLE_CAPABILITY_ID, TABLE_STYLE_DEFINITION_SCHEMA_VERSION, TABLE_STYLE_SCHEMA_VERSION,
    TableStyleBandPrecedence, TableStyleBanding, TableStyleBuilder, TableStyleCellDraft,
    TableStyleColumnEmphasis, TableStyleDefinition, TableStyleDefinitionDraft, TableStyleError,
    TableStyleLimitConfig, TableStyleLimits, TableStyleMergedCellPolicy, TableStyleMutation,
    TableStylePlan, TableStyleReceipt, TableStyleRegion, TableStyleRequest, TableStyleRequestDraft,
    TableStyleRule,
};
pub use table_text_conversion::{
    TABLE_TABLE_TO_TEXT_CAPABILITY_ID, TABLE_TEXT_CONVERSION_SCHEMA_VERSION,
    TABLE_TEXT_TO_TABLE_CAPABILITY_ID, TableDelimiter, TableLineEnding, TableTextConversionError,
    TableTextConversionLimitConfig, TableTextConversionLimits, TableTextGrid, TableTextGridDraft,
};
pub use table_thousands::{
    TABLE_THOUSANDS_SCHEMA_VERSION, TableThousandsBuilder, TableThousandsError, TableThousandsMode,
    TableThousandsPlan, TableThousandsRequest, TableThousandsRequestDraft,
};
pub use table_transpose::{
    TABLE_TRANSPOSE_CAPABILITY_ID, TABLE_TRANSPOSE_SCHEMA_VERSION, TableTransposeBuilder,
    TableTransposeCell, TableTransposeCellDraft, TableTransposeError, TableTransposeFormulaPolicy,
    TableTransposeLimitConfig, TableTransposeLimits, TableTransposePlan, TableTransposeReceipt,
    TableTransposeRelocation, TableTransposeRequest, TableTransposeRequestDraft,
};
pub use units::{
    AngleMicrodegrees, Conversion, ConversionReceipt, CoordinateAnchor, CoordinateSpace, HwpUnit,
    LengthMicrometers, PointMilli, Position2D, RatioMillionths, RationalInput, UnitError, UnitKind,
    ZOrder,
};
