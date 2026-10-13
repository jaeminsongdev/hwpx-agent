#![forbid(unsafe_code)]

//! Fail-closed, bounded ZIP reading for HWPX package inspection.
//!
//! This crate never extracts files. [`BoundedZipReader::read_entry`] returns a
//! fully verified in-memory value only after metadata, streaming size, CRC and
//! nested-package checks have succeeded.

mod active_content;
mod asset;
mod basic_shape_hwpx;
mod bookmark_hwpx;
mod character_style;
mod click_here_hwpx;
mod drawing_canvas_hwpx;
mod equation;
mod field_auto_number_hwpx;
mod field_object_caption_hwpx;
mod font_metric_receipt;
mod form_control_hwpx;
mod graph;
mod header_footer;
mod hyperlink_hwpx;
mod id_index;
mod image_hwpx;
mod limits;
mod list_definition;
pub mod native_form_color;
mod native_form_hwpx;
mod native_form_package;
mod native_form_package_lowering;
pub mod native_form_value_output;
mod native_root_manifest;
mod note_hwpx;
mod object_appearance_hwpx;
mod object_caption_insert_hwpx;
mod object_common_properties_hwpx;
mod object_composition_hwpx;
mod object_form_insert_hwpx;
mod object_geometry_hwpx;
mod object_hyperlink_hwpx;
mod object_hyperlink_target;
mod object_remainder_target;
mod page_setup;
mod paragraph_style;
mod patch;
mod path;
mod preservation;
mod preserving_xml;
mod reader;
mod roundtrip;
mod safe_xml;
mod section_columns;
mod shape_points_hwpx;
mod tab_definition;
mod table_cell_style;
mod table_chart_hwpx;
mod table_formula;
mod table_layout;
mod table_pagination;
mod table_placement;
mod table_ruling_hwpx;
mod text_flow;
mod textbox_properties_hwpx;
mod vs0;
mod vs1_layout;
mod writer;

pub use active_content::{
    ACTIVE_CONTENT_PROFILE_ID, ACTIVE_CONTENT_SCHEMA_VERSION, ActivationKind, ActiveContentControl,
    ActiveContentControlKind, ActiveContentDisposition, ActiveContentError, ActiveContentInventory,
    ActiveContentLimitConfig, ActiveContentLimits, ActiveContentPreservationReceipt,
    ActiveContentResource, ActiveContentResourceKind, ActiveContentSignature,
};
pub use asset::{
    ASSET_PIPELINE_PROFILE_ID, ASSET_PIPELINE_SCHEMA_VERSION, AssetDisposition, AssetError,
    AssetLimitConfig, AssetLimits, AssetMedia, AssetPlan, AssetStoreAdapter,
};
pub use basic_shape_hwpx::{
    BASIC_SHAPE_HWPX_PROFILE_ID, BasicShapeHwpxBuilder, BasicShapeHwpxError,
    BasicShapeHwpxLimitConfig, BasicShapeHwpxLimits, BasicShapeHwpxLowered, BasicShapeHwpxLowerer,
    BasicShapeHwpxLoweringReceipt, BasicShapeHwpxPlan, BasicShapeHwpxReadback,
    BasicShapeHwpxReader, BasicShapeHwpxSource,
};
pub use bookmark_hwpx::{
    BOOKMARK_HWPX_PROFILE_ID, BookmarkHwpxBuilder, BookmarkHwpxError, BookmarkHwpxLimitConfig,
    BookmarkHwpxLimits, BookmarkHwpxLowerer, BookmarkHwpxLoweringReceipt, BookmarkHwpxPlan,
    BookmarkHwpxReadback, BookmarkHwpxReader,
};
pub use character_style::{
    BinaryProperty, CHARACTER_STYLE_PROFILE_ID, CharacterEffects, CharacterStyle,
    CharacterStyleCatalog, CharacterStyleCatalogReader, CharacterStyleCatalogWriter,
    CharacterStyleError, CharacterStyleLimitConfig, CharacterStyleLimits,
    CharacterStyleLoweringReceipt, Color, DeduplicatedCharacterStyles, EmphasisMark, FontFace,
    FontFaceGroup, FontFamily, FontType, FontTypeInfo, HANCOM_2020_HEAD_NAMESPACE, LanguageSlot,
    LanguageValues, LineType1, LineType2, Shadow, ShadowType, Strikeout, SubstituteFont, Underline,
    UnderlinePosition,
};
pub use click_here_hwpx::{
    CLICK_HERE_HWPX_PROFILE_ID, ClickHereHwpxBuilder, ClickHereHwpxError, ClickHereHwpxField,
    ClickHereHwpxLimits, ClickHereHwpxLowerer, ClickHereHwpxLoweringReceipt, ClickHereHwpxPlan,
    ClickHereHwpxReadback, ClickHereHwpxReader,
};
pub use drawing_canvas_hwpx::{
    DRAWING_CANVAS_HWPX_PROFILE_ID, DrawingCanvasHwpxBuilder, DrawingCanvasHwpxError,
    DrawingCanvasHwpxLimitConfig, DrawingCanvasHwpxLimits, DrawingCanvasHwpxLowered,
    DrawingCanvasHwpxLowerer, DrawingCanvasHwpxLoweringReceipt, DrawingCanvasHwpxPlan,
    DrawingCanvasHwpxReadback, DrawingCanvasHwpxReader,
};
pub use equation::{
    EQUATION_AUTOMATION_HWPX_PROFILE_ID, EQUATION_HWPX_PROFILE_ID, EQUATION_HWPX_SCHEMA_VERSION,
    EquationColor, EquationExtent, EquationExtentSource, EquationHwpxBuilder, EquationHwpxError,
    EquationHwpxLimitConfig, EquationHwpxLimits, EquationHwpxLowered, EquationHwpxLowerer,
    EquationHwpxLoweringReceipt, EquationHwpxReadback, EquationHwpxReader, EquationHwpxRequest,
    EquationHwpxRequestDraft, EquationHwpxSource, EquationLayout, EquationStyle,
};
pub use field_auto_number_hwpx::{
    FIELD_AUTO_NUMBER_HWPX_PROFILE_ID, FieldAutoNumberHwpxBuilder, FieldAutoNumberHwpxError,
    FieldAutoNumberHwpxLimitConfig, FieldAutoNumberHwpxLimits, FieldAutoNumberHwpxLowerer,
    FieldAutoNumberHwpxLoweringReceipt, FieldAutoNumberHwpxPlan, FieldAutoNumberHwpxReadback,
    FieldAutoNumberHwpxReader,
};
pub use field_object_caption_hwpx::{
    FIELD_OBJECT_CAPTION_HWPX_PROFILE_ID, FieldObjectCaptionHwpxBuilder,
    FieldObjectCaptionHwpxContext, FieldObjectCaptionHwpxError, FieldObjectCaptionHwpxLowerer,
    FieldObjectCaptionHwpxLoweringReceipt, FieldObjectCaptionHwpxPlan,
    FieldObjectCaptionHwpxReadback, FieldObjectCaptionHwpxReader, FieldObjectCaptionHwpxTarget,
};
pub use font_metric_receipt::{
    CURRENT_FONT_METRIC_PROFILE_ID, CurrentFontMetricCell, CurrentFontMetricLimits,
    CurrentFontMetricReceipt, FontMetricReceiptError,
};
pub use form_control_hwpx::{
    FORM_CONTROL_HWPX_PROFILE_ID, FormControlHwpxBuilder, FormControlHwpxError,
    FormControlHwpxLimitConfig, FormControlHwpxLimits, FormControlHwpxLowerer,
    FormControlHwpxLoweringReceipt, FormControlHwpxPlan, FormControlHwpxReadback,
    FormControlHwpxReader,
};
pub use graph::{
    GraphError, MediaType, PackageGraph, PackageGraphLimitConfig, PackageGraphLimits, PartRecord,
    PartRole, Relationship, RelationshipKind,
};
pub use header_footer::{
    FirstPageDisplay, FirstPageVisibility, HEADER_FOOTER_PROFILE_ID, HeaderFooterBody,
    HeaderFooterDefinition, HeaderFooterError, HeaderFooterInline, HeaderFooterKind,
    HeaderFooterLimitConfig, HeaderFooterLimits, HeaderFooterLowerer, HeaderFooterLoweringReceipt,
    HeaderFooterParagraph, HeaderFooterReader, HeaderFooterRun, LineWrap as HeaderFooterLineWrap,
    MasterPageDefinition, MasterPageVariant, PageField, PageFieldKind, PageNumberPlacement,
    PageNumberPosition, PageNumberRestart, PageVariant, SectionPagePolicy,
    TextDirection as HeaderFooterTextDirection, VerticalAlignment as HeaderFooterVerticalAlignment,
};
pub use hyperlink_hwpx::{
    HYPERLINK_HWPX_PROFILE_ID, HyperlinkHwpxBuilder, HyperlinkHwpxError, HyperlinkHwpxLimitConfig,
    HyperlinkHwpxLimits, HyperlinkHwpxLowerer, HyperlinkHwpxLoweringReceipt, HyperlinkHwpxPlan,
    HyperlinkHwpxReadback, HyperlinkHwpxReader,
};
pub use id_index::{
    IdDeclaration, IdIndex, IdIndexError, IdIndexLimitConfig, IdIndexLimits, IdIssueKind, IdKind,
    IdLocation, IdReference, IdRuleProfile, IdValidationIssue, IdValidationReport,
};
pub use image_hwpx::{
    IMAGE_HWPX_PROFILE_ID, IMAGE_HWPX_SCHEMA_VERSION, ImageAssetBinding, ImageCrop, ImageGeometry,
    ImageHwpxBuilder, ImageHwpxError, ImageHwpxLimitConfig, ImageHwpxLimits, ImageHwpxLowered,
    ImageHwpxLowerer, ImageHwpxLoweringReceipt, ImageHwpxReadback, ImageHwpxReader,
    ImageHwpxRequest, ImageHwpxRequestDraft, ImageHwpxSource, ImageLinkMode,
};
pub use limits::{PackageLimitConfig, PackageLimits};
pub use list_definition::{
    BulletDefinition, DeduplicatedListDefinitions, LIST_DEFINITION_PROFILE_ID, ListAlignment,
    ListBinding, ListDefinitionCatalog, ListDefinitionCatalogReader, ListDefinitionCatalogWriter,
    ListDefinitionError, ListDefinitionLimitConfig, ListDefinitionLimits,
    ListDefinitionLoweringReceipt, ListSequenceEngine, ListSequenceItem, ListSequenceKind,
    ListSequenceResult, NumberFormat, NumberingDefinition, NumberingLevel,
    OutlineDefinitionBinding, OutlineDefinitionBindingReader, ParagraphHeadStyle, TextOffsetUnit,
};
pub use native_form_hwpx::{
    NATIVE_FORM_HWPX_PROFILE_ID, NativeFormControlObservation, NativeFormHwpxBuilder,
    NativeFormHwpxError, NativeFormHwpxLimits, NativeFormHwpxLowerer,
    NativeFormHwpxLoweringReceipt, NativeFormHwpxMap, NativeFormHwpxPlan, NativeFormHwpxReadback,
    NativeFormHwpxReader, NativeFormObservedIdentity, NativeFormObservedPayload,
    NativeFormPhysicalAnchor,
};
pub use native_form_package::{
    NATIVE_FORM_PACKAGE_BINDING_PROFILE_ID, NativeFormPackageBindings, NativeFormPackageError,
    NativeFormPackageLimits, NativeFormPackageMap, NativeFormPackagePlan, NativeFormPackagePolicy,
    NativeFormPackageReadback, NativeFormPackageReader, NativeFormPackageSectionMap,
};
pub use native_form_package_lowering::{
    NATIVE_FORM_PACKAGE_OUTPUT_PROFILE_ID, NativeFormPackageLowerer, NativeFormPackageOutput,
    NativeFormPackageOutputError, NativeFormPackageOutputLimits, NativeFormPackageOutputPlan,
    NativeFormPackageOutputReceipt,
};
pub use native_root_manifest::{
    NATIVE_ROOT_MANIFEST_PROFILE_ID, NativeRootManifestError, NativeRootManifestLimits,
    NativeRootManifestOutput, NativeRootManifestPlan, NativeRootManifestPreparer,
    NativeRootManifestPreservation, NativeRootManifestQualification, NativeRootManifestReceipt,
};
pub use note_hwpx::{
    NOTE_HWPX_PROFILE_ID, NoteHwpxBuilder, NoteHwpxError, NoteHwpxLimitConfig, NoteHwpxLimits,
    NoteHwpxLowerer, NoteHwpxLoweringReceipt, NoteHwpxPayloadDigests, NoteHwpxPlan,
    NoteHwpxReadback, NoteHwpxReader,
};
pub use object_appearance_hwpx::{
    OBJECT_APPEARANCE_HWPX_PROFILE_ID, ObjectAppearanceHwpxBuilder, ObjectAppearanceHwpxError,
    ObjectAppearanceHwpxLimitConfig, ObjectAppearanceHwpxLimits, ObjectAppearanceHwpxLowerer,
    ObjectAppearanceHwpxLoweringReceipt, ObjectAppearanceHwpxPlan, ObjectAppearanceHwpxReadback,
    ObjectAppearanceHwpxReader,
};
pub use object_caption_insert_hwpx::{
    OBJECT_CAPTION_INSERT_HWPX_PROFILE_ID, ObjectCaptionInsertHwpxBuilder,
    ObjectCaptionInsertHwpxError, ObjectCaptionInsertHwpxLimitConfig,
    ObjectCaptionInsertHwpxLimits, ObjectCaptionInsertHwpxLowerer,
    ObjectCaptionInsertHwpxLoweringReceipt, ObjectCaptionInsertHwpxPlan,
    ObjectCaptionInsertHwpxReadback, ObjectCaptionInsertHwpxReader,
};
pub use object_common_properties_hwpx::{
    OBJECT_COMMON_PROPERTIES_HWPX_PROFILE_ID, ObjectCommonPropertiesHwpxBuilder,
    ObjectCommonPropertiesHwpxError, ObjectCommonPropertiesHwpxLimitConfig,
    ObjectCommonPropertiesHwpxLimits, ObjectCommonPropertiesHwpxLowerer,
    ObjectCommonPropertiesHwpxLoweringReceipt, ObjectCommonPropertiesHwpxPlan,
    ObjectCommonPropertiesHwpxReadback, ObjectCommonPropertiesHwpxReader,
};
pub use object_composition_hwpx::{
    OBJECT_COMPOSITION_HWPX_PROFILE_ID, ObjectCompositionHwpxBuilder, ObjectCompositionHwpxError,
    ObjectCompositionHwpxLimitConfig, ObjectCompositionHwpxLimits, ObjectCompositionHwpxLowered,
    ObjectCompositionHwpxLowerer, ObjectCompositionHwpxLoweringReceipt, ObjectCompositionHwpxPlan,
    ObjectCompositionHwpxReadback, ObjectCompositionHwpxReader,
};
pub use object_form_insert_hwpx::{
    OBJECT_FORM_INSERT_HWPX_PROFILE_ID, OBJECT_FORM_INSERT_STATIC_EDIT_PROFILE_SHA256,
    ObjectFormInsertHwpxBuilder, ObjectFormInsertHwpxError, ObjectFormInsertHwpxLimitConfig,
    ObjectFormInsertHwpxLimits, ObjectFormInsertHwpxLowerer, ObjectFormInsertHwpxLoweringReceipt,
    ObjectFormInsertHwpxPlan, ObjectFormInsertHwpxReadback, ObjectFormInsertHwpxReader,
};
pub use object_geometry_hwpx::{
    OBJECT_GEOMETRY_HWPX_PROFILE_ID, ObjectGeometryHwpxBuilder, ObjectGeometryHwpxError,
    ObjectGeometryHwpxLimitConfig, ObjectGeometryHwpxLimits, ObjectGeometryHwpxLowerer,
    ObjectGeometryHwpxLoweringReceipt, ObjectGeometryHwpxPlan, ObjectGeometryHwpxReadback,
    ObjectGeometryHwpxReader,
};
pub use object_hyperlink_hwpx::{
    OBJECT_HYPERLINK_HWPX_PROFILE_ID, ObjectHyperlinkHwpxBuilder, ObjectHyperlinkHwpxError,
    ObjectHyperlinkHwpxLimitConfig, ObjectHyperlinkHwpxLimits, ObjectHyperlinkHwpxLowerer,
    ObjectHyperlinkHwpxLoweringReceipt, ObjectHyperlinkHwpxPlan, ObjectHyperlinkHwpxReadback,
    ObjectHyperlinkHwpxReader,
};
pub use object_hyperlink_target::{
    OBJECT_HYPERLINK_CURRENT_TARGET_EXECUTABLE_SHA256, OBJECT_HYPERLINK_CURRENT_TARGET_PROFILE_ID,
    ObjectHyperlinkDirectAdmission, ObjectHyperlinkTargetRoute, ObjectHyperlinkTargetRouteError,
    ObjectHyperlinkTargetRouter,
};
pub use object_remainder_target::{
    OBJECT_REMAINDER_CURRENT_TARGET_EXECUTABLE_SHA256, OBJECT_REMAINDER_CURRENT_TARGET_PROFILE_ID,
    ObjectRemainderCapability, ObjectRemainderDirectAdmission, ObjectRemainderTargetRoute,
    ObjectRemainderTargetRouteError, ObjectRemainderTargetRouter,
};
pub use page_setup::{
    PAGE_SETUP_PROFILE_ID, PageDimensions, PageGutterType, PageMargins, PageOrientation,
    PagePreset, PageSetup, PageSetupError, PageSetupLimitConfig, PageSetupLimits, PageSetupLowerer,
    PageSetupLoweringReceipt, PageSetupMetrics, PageSetupPatchReceipt, PageSetupReader,
};
pub use paragraph_style::{
    AutoSpacing, BorderFill, BorderLine, BorderWidth, BreakSettings, CenterLine, CompatibleHeading,
    CompatibleParagraphLayout, DeduplicatedParagraphStyles, FillBrush, HatchStyle, Heading,
    HeadingType, HorizontalAlignment, HwpValue, LineSpacing, LineSpacingType, LineWrap, Margin,
    MeasurementUnit, PARAGRAPH_STYLE_PROFILE_ID, ParagraphBorder, ParagraphLayout,
    ParagraphReferenceDomains, ParagraphStyle, ParagraphStyleCatalog, ParagraphStyleCatalogReader,
    ParagraphStyleCatalogWriter, ParagraphStyleError, ParagraphStyleLimitConfig,
    ParagraphStyleLimits, ParagraphStyleLoweringReceipt, Slash, SlashType, TextDirection,
    VerticalAlignment, WindowBrush, WordBreak,
};
pub use patch::{
    AddedPart, AllocationHandle, PatchAttributeValue, PatchError, PatchIntent, PatchLimitConfig,
    PatchLimits, PatchPartDisposition, PatchPartRecord, PatchResult, PatchText,
    PreservingPatchEngine, RelationshipAddition, RelationshipSpine, SiblingPosition,
    ValidatedXmlFragment, XmlAttributeSelector, XmlElementSelector, XmlTextSelector,
};
pub use path::PackagePath;
pub use preservation::{
    PartPreservationRecord, PreservationClass, PreservationCounts, PreservationError,
    PreservationReason, PreservationReport, PreservationRuleProfile, TokenPreservationEvidence,
};
pub use preserving_xml::{
    PreservingXmlDocument, PreservingXmlError, XmlAttributeToken, XmlByteSpan, XmlElementToken,
    XmlName, XmlQuoteStyle, XmlToken, XmlTokenKind,
};
pub use reader::{BoundedZipReader, Compression, EntryMetadata, PackageError};
pub use roundtrip::{
    DiagnosticLayer, RecommendedAction, RepairDiagnostic, Repairability, RoundTripError,
    RoundTripEvidence, RoundTripLimits, RoundTripVerifier,
};
pub use safe_xml::SafeXmlError;
pub use section_columns::{
    COLUMN_PROFILE_ID, ColumnDefinition, ColumnLayout, ColumnLineType, ColumnLineWidth,
    ColumnMetrics, ColumnSeparator, ColumnSize, ColumnSizing, ColumnType, SectionBoundary,
    SectionColumnError, SectionColumnLimitConfig, SectionColumnLimits, SectionColumnLowerer,
    SectionColumnLoweringReceipt, SectionColumnPatchReceipt, SectionColumnReader,
    SectionColumnSequence, SectionColumns, SectionCountPatchReceipt,
};
pub use shape_points_hwpx::{
    SHAPE_POINTS_HWPX_PROFILE_ID, ShapePointsHwpxBuilder, ShapePointsHwpxError,
    ShapePointsHwpxLimitConfig, ShapePointsHwpxLimits, ShapePointsHwpxLowerer,
    ShapePointsHwpxLoweringReceipt, ShapePointsHwpxPlan, ShapePointsHwpxReadback,
    ShapePointsHwpxReader,
};
pub use tab_definition::{
    DeduplicatedTabDefinitions, TAB_DEFINITION_PROFILE_ID, TabDefinition, TabDefinitionCatalog,
    TabDefinitionCatalogReader, TabDefinitionCatalogWriter, TabDefinitionError,
    TabDefinitionLimitConfig, TabDefinitionLimits, TabDefinitionLoweringReceipt, TabItem,
    TabPositionUnit, TabStop, TabStopAlignment,
};
pub use table_cell_style::{
    CellMargins, CellProtection, CellTextDirection, CellVerticalAlignment,
    TABLE_CELL_STYLE_HANCOM_2020_PROFILE_ID, TABLE_CELL_STYLE_PROFILE_ID, TableCellStyle,
    TableCellStyleError, TableCellStyleLimitConfig, TableCellStyleLimits, TableCellStyleLowerer,
    TableCellStyleLoweringReceipt, TableCellStyleProfile, TableCellStyleReadback,
    TableCellStyleReader,
};
pub use table_chart_hwpx::{
    TABLE_CHART_HWPX_PROFILE_ID, TABLE_CHART_HWPX_SCHEMA_VERSION, TableChartHwpxBuilder,
    TableChartHwpxError, TableChartHwpxLimitConfig, TableChartHwpxLimits, TableChartHwpxLowered,
    TableChartHwpxLowerer, TableChartHwpxLoweringReceipt, TableChartHwpxReadback,
    TableChartHwpxReader, TableChartHwpxRequest, TableChartHwpxRequestDraft, TableChartHwpxSource,
};
pub use table_formula::{
    TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID, TABLE_FORMULA_HWPX_PROFILE_ID,
    TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID, TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION,
    TABLE_THOUSANDS_HWPX_PROFILE_ID, TABLE_THOUSANDS_HWPX_SCHEMA_VERSION, TableFormulaHwpxError,
    TableFormulaHwpxLimitConfig, TableFormulaHwpxLimits, TableFormulaHwpxLowerer,
    TableFormulaHwpxLoweringReceipt, TableFormulaHwpxReadback, TableFormulaHwpxReader,
    TableNumberFormatHwpxError, TableNumberFormatHwpxLowerer, TableNumberFormatHwpxLoweringReceipt,
    TableNumberFormatHwpxReadback, TableNumberFormatHwpxReader, TableNumberFormatHwpxRequest,
    TableNumberFormatHwpxRequestDraft, TableThousandsHwpxError, TableThousandsHwpxLowerer,
    TableThousandsHwpxLoweringReceipt, TableThousandsHwpxReadback, TableThousandsHwpxReader,
    TableThousandsHwpxRequest, TableThousandsHwpxRequestDraft,
};
pub use table_layout::{
    TABLE_GEOMETRY_HWPX_PROFILE_ID, TABLE_LAYOUT_HWPX_PROFILE_ID, TABLE_LAYOUT_HWPX_PROFILE_ID_V1,
    TableCellSizeReadback, TableGeometryHwpxLowerer, TableGeometryHwpxLoweringReceipt,
    TableInnerMarginReadback, TableLayoutHwpxError, TableLayoutHwpxLimitConfig,
    TableLayoutHwpxLimits, TableLayoutHwpxLowerer, TableLayoutHwpxLoweringReceipt,
    TableLayoutHwpxReadback, TableLayoutHwpxReader,
};
pub use table_pagination::{
    TABLE_PAGINATION_HWPX_PROFILE_ID, TableCaptionHwpxProperties, TableCaptionHwpxTarget,
    TablePaginationHwpxError, TablePaginationHwpxLimitConfig, TablePaginationHwpxLimits,
    TablePaginationHwpxLowerer, TablePaginationHwpxLoweringReceipt, TablePaginationHwpxReadback,
    TablePaginationHwpxReader, TablePaginationHwpxTarget,
};
pub use table_placement::{
    TABLE_PLACEMENT_HWPX_PROFILE_ID, TableAttachmentFlagsHwpxReadback,
    TableFloatingFlagsHwpxReadback, TableOuterMarginsHwpxReadback, TablePlacementHwpxError,
    TablePlacementHwpxLowerer, TablePlacementHwpxLoweringReceipt, TablePlacementHwpxReadback,
    TablePlacementHwpxReader,
};
pub use table_ruling_hwpx::{
    TABLE_ABSOLUTE_REFERENCE_CAPABILITY_ID, TABLE_ABSOLUTE_REFERENCE_HWPX_PROFILE_ID,
    TABLE_ABSOLUTE_REFERENCE_HWPX_SCHEMA_VERSION, TABLE_AGGREGATE_HWPX_PROFILE_ID,
    TABLE_AGGREGATE_HWPX_SCHEMA_VERSION, TABLE_AUTO_FILL_HWPX_PROFILE_ID,
    TABLE_AUTO_FILL_HWPX_SCHEMA_VERSION, TABLE_CREATE_HWPX_PROFILE_ID,
    TABLE_CREATE_HWPX_SCHEMA_VERSION, TABLE_JOIN_HWPX_PROFILE_ID, TABLE_JOIN_HWPX_SCHEMA_VERSION,
    TABLE_MERGE_SPLIT_HWPX_PROFILE_ID, TABLE_MERGE_SPLIT_HWPX_SCHEMA_VERSION,
    TABLE_NESTED_TABLE_HWPX_PROFILE_ID, TABLE_NESTED_TABLE_HWPX_SCHEMA_VERSION,
    TABLE_PROPERTIES_HWPX_PROFILE_ID, TABLE_RULING_HWPX_PROFILE_ID, TABLE_SORT_HWPX_PROFILE_ID,
    TABLE_SORT_HWPX_SCHEMA_VERSION, TABLE_SPLIT_HWPX_PROFILE_ID, TABLE_SPLIT_HWPX_SCHEMA_VERSION,
    TABLE_STRUCTURE_HWPX_PROFILE_ID, TABLE_STRUCTURE_HWPX_SCHEMA_VERSION,
    TABLE_STYLE_HWPX_PROFILE_ID, TABLE_TABLE_TO_TEXT_HWPX_PROFILE_ID,
    TABLE_TABLE_TO_TEXT_HWPX_SCHEMA_VERSION, TABLE_TEXT_TO_TABLE_HWPX_PROFILE_ID,
    TABLE_TEXT_TO_TABLE_HWPX_SCHEMA_VERSION, TABLE_TRANSPOSE_HWPX_PROFILE_ID,
    TABLE_TRANSPOSE_HWPX_SCHEMA_VERSION, TableAbsoluteReferenceHwpxBuilder,
    TableAbsoluteReferenceHwpxError, TableAbsoluteReferenceHwpxLimits,
    TableAbsoluteReferenceHwpxLoweredParts, TableAbsoluteReferenceHwpxLowerer,
    TableAbsoluteReferenceHwpxLoweringReceipt, TableAbsoluteReferenceHwpxPlan,
    TableAbsoluteReferenceHwpxReadback, TableAbsoluteReferenceHwpxReader,
    TableAbsoluteReferenceHwpxRequest, TableAbsoluteReferenceHwpxRequestDraft,
    TableAggregateHwpxBuilder, TableAggregateHwpxError, TableAggregateHwpxLimits,
    TableAggregateHwpxLoweredParts, TableAggregateHwpxLowerer, TableAggregateHwpxLoweringReceipt,
    TableAggregateHwpxPlan, TableAggregateHwpxReadback, TableAggregateHwpxReader,
    TableAggregateHwpxRequest, TableAggregateHwpxRequestDraft, TableAutoFillHwpxBuilder,
    TableAutoFillHwpxError, TableAutoFillHwpxLimits, TableAutoFillHwpxLoweredParts,
    TableAutoFillHwpxLowerer, TableAutoFillHwpxLoweringReceipt, TableAutoFillHwpxPlan,
    TableAutoFillHwpxReadback, TableAutoFillHwpxReader, TableAutoFillHwpxRequest,
    TableAutoFillHwpxRequestDraft, TableCreateHwpxBuilder, TableCreateHwpxError,
    TableCreateHwpxLimits, TableCreateHwpxLoweredParts, TableCreateHwpxLowerer,
    TableCreateHwpxLoweringReceipt, TableCreateHwpxPlan, TableCreateHwpxReadback,
    TableCreateHwpxReader, TableCreateHwpxRequest, TableCreateHwpxRequestDraft,
    TableJoinHwpxBuilder, TableJoinHwpxError, TableJoinHwpxLimits, TableJoinHwpxLoweredParts,
    TableJoinHwpxLowerer, TableJoinHwpxLoweringReceipt, TableJoinHwpxPlan, TableJoinHwpxReadback,
    TableJoinHwpxReader, TableJoinHwpxRequest, TableJoinHwpxRequestDraft,
    TableMergeSplitHwpxBuilder, TableMergeSplitHwpxError, TableMergeSplitHwpxLimits,
    TableMergeSplitHwpxLoweredParts, TableMergeSplitHwpxLowerer,
    TableMergeSplitHwpxLoweringReceipt, TableMergeSplitHwpxOperation,
    TableMergeSplitHwpxPartBinding, TableMergeSplitHwpxPlan, TableMergeSplitHwpxReadback,
    TableMergeSplitHwpxReader, TableMergeSplitHwpxRequest, TableMergeSplitHwpxRequestDraft,
    TableNestedTableHwpxBuilder, TableNestedTableHwpxError, TableNestedTableHwpxLimits,
    TableNestedTableHwpxLoweredParts, TableNestedTableHwpxLowerer,
    TableNestedTableHwpxLoweringReceipt, TableNestedTableHwpxPlan, TableNestedTableHwpxReadback,
    TableNestedTableHwpxReader, TableNestedTableHwpxRequest, TableNestedTableHwpxRequestDraft,
    TablePropertiesHwpxBinding, TablePropertiesHwpxCellValue, TablePropertiesHwpxDiagonalBinding,
    TablePropertiesHwpxError, TablePropertiesHwpxLimits, TablePropertiesHwpxLoweredParts,
    TablePropertiesHwpxLowerer, TablePropertiesHwpxLoweringReceipt, TablePropertiesHwpxPartBinding,
    TablePropertiesHwpxReadback, TablePropertiesHwpxReader, TablePropertiesHwpxTableValue,
    TablePropertiesHwpxValueCatalog, TableRulingHwpxBinding, TableRulingHwpxCellBinding,
    TableRulingHwpxError, TableRulingHwpxLimits, TableRulingHwpxLoweredParts,
    TableRulingHwpxLowerer, TableRulingHwpxLoweringReceipt, TableRulingHwpxReadback,
    TableRulingHwpxReader, TableRulingHwpxStyleCatalog, TableSortHwpxBuilder, TableSortHwpxError,
    TableSortHwpxLimits, TableSortHwpxLoweredParts, TableSortHwpxLowerer,
    TableSortHwpxLoweringReceipt, TableSortHwpxPlan, TableSortHwpxReadback, TableSortHwpxReader,
    TableSortHwpxRequest, TableSortHwpxRequestDraft, TableSplitHwpxBuilder, TableSplitHwpxError,
    TableSplitHwpxLimits, TableSplitHwpxLoweredParts, TableSplitHwpxLowerer,
    TableSplitHwpxLoweringReceipt, TableSplitHwpxPlan, TableSplitHwpxReadback,
    TableSplitHwpxReader, TableSplitHwpxRequest, TableSplitHwpxRequestDraft,
    TableStructureHwpxBuilder, TableStructureHwpxError, TableStructureHwpxLimits,
    TableStructureHwpxLoweredParts, TableStructureHwpxLowerer, TableStructureHwpxLoweringReceipt,
    TableStructureHwpxPlan, TableStructureHwpxReadback, TableStructureHwpxReader,
    TableStructureHwpxRequest, TableStructureHwpxRequestDraft, TableStyleHwpxCellValue,
    TableStyleHwpxError, TableStyleHwpxLimits, TableStyleHwpxLoweredParts, TableStyleHwpxLowerer,
    TableStyleHwpxLoweringReceipt, TableStyleHwpxPartBinding, TableStyleHwpxReadback,
    TableStyleHwpxReader, TableStyleHwpxValueCatalog, TableTableToTextHwpxBuilder,
    TableTableToTextHwpxError, TableTableToTextHwpxLimits, TableTableToTextHwpxLoweredParts,
    TableTableToTextHwpxLowerer, TableTableToTextHwpxLoweringReceipt, TableTableToTextHwpxPlan,
    TableTableToTextHwpxReadback, TableTableToTextHwpxReader, TableTableToTextHwpxRequest,
    TableTableToTextHwpxRequestDraft, TableTextToTableHwpxBuilder, TableTextToTableHwpxError,
    TableTextToTableHwpxLimits, TableTextToTableHwpxLoweredParts, TableTextToTableHwpxLowerer,
    TableTextToTableHwpxLoweringReceipt, TableTextToTableHwpxPlan, TableTextToTableHwpxReadback,
    TableTextToTableHwpxReader, TableTextToTableHwpxRequest, TableTextToTableHwpxRequestDraft,
    TableTransposeHwpxBuilder, TableTransposeHwpxError, TableTransposeHwpxLimits,
    TableTransposeHwpxLoweredParts, TableTransposeHwpxLowerer, TableTransposeHwpxLoweringReceipt,
    TableTransposeHwpxPlan, TableTransposeHwpxReadback, TableTransposeHwpxReader,
    TableTransposeHwpxRequest, TableTransposeHwpxRequestDraft,
};
pub use text_flow::{
    FieldBegin, FieldEnd, FieldType, HANCOM_2020_PARAGRAPH_NAMESPACE, OpaqueTextElement,
    ParagraphChild, TextAtom, TextFlow, TextFlowError, TextFlowLimitConfig, TextFlowLimits,
    TextFlowReader, TextFlowWriter, TextParagraphProperties, TextRun, TextRunItem, TextSpan,
};
pub use textbox_properties_hwpx::{
    TEXTBOX_PROPERTIES_HWPX_PROFILE_ID, TextBoxPropertiesHwpxBuilder, TextBoxPropertiesHwpxError,
    TextBoxPropertiesHwpxLimitConfig, TextBoxPropertiesHwpxLimits, TextBoxPropertiesHwpxLowerer,
    TextBoxPropertiesHwpxLoweringReceipt, TextBoxPropertiesHwpxPlan, TextBoxPropertiesHwpxReadback,
    TextBoxPropertiesHwpxReader,
};
pub use vs0::{
    HANCOM_2020_VS0_MAX_TEXT_BYTES, Hancom2020Vs0Artifact, Hancom2020Vs0Builder, Hancom2020Vs0Error,
};
pub use vs1_layout::{
    HANCOM_2020_DENSE_COLUMN_FLOW_PROFILE_ID, HANCOM_2020_VS1_LAYOUT_MAX_PARAGRAPHS,
    HANCOM_2020_VS1_LAYOUT_MAX_TEXT_BYTES, HANCOM_2020_VS1_LAYOUT_PROFILE_ID,
    Hancom2020ColumnFlowPolicy, Hancom2020Vs1LayoutArtifact, Hancom2020Vs1LayoutBuilder,
    Hancom2020Vs1LayoutDocument, Hancom2020Vs1LayoutError, Hancom2020Vs1LayoutInspection,
};
pub use writer::{
    AtomicPackagePublisher, MetadataDisposition, NormalizedWriter, PackageArtifact,
    PreservingWriter, PublicationReceipt, WriterEntryRecord, WriterError, WriterLimitConfig,
    WriterLimits, WriterMode, WriterReport,
};
