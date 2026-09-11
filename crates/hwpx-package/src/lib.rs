#![forbid(unsafe_code)]

//! Fail-closed, bounded ZIP reading for HWPX package inspection.
//!
//! This crate never extracts files. [`BoundedZipReader::read_entry`] returns a
//! fully verified in-memory value only after metadata, streaming size, CRC and
//! nested-package checks have succeeded.

mod asset;
mod character_style;
mod equation;
mod font_metric_receipt;
mod graph;
mod header_footer;
mod id_index;
mod limits;
mod list_definition;
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
mod tab_definition;
mod table_cell_style;
mod table_formula;
mod table_layout;
mod table_pagination;
mod table_placement;
mod table_ruling_hwpx;
mod text_flow;
mod vs0;
mod vs1_layout;
mod writer;

pub use asset::{
    ASSET_PIPELINE_PROFILE_ID, ASSET_PIPELINE_SCHEMA_VERSION, AssetDisposition, AssetError,
    AssetLimitConfig, AssetLimits, AssetMedia, AssetPlan, AssetStoreAdapter,
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
pub use equation::{
    EQUATION_AUTOMATION_HWPX_PROFILE_ID, EQUATION_HWPX_PROFILE_ID, EQUATION_HWPX_SCHEMA_VERSION,
    EquationColor, EquationExtent, EquationExtentSource, EquationHwpxBuilder, EquationHwpxError,
    EquationHwpxLimitConfig, EquationHwpxLimits, EquationHwpxLowered, EquationHwpxLowerer,
    EquationHwpxLoweringReceipt, EquationHwpxReadback, EquationHwpxReader, EquationHwpxRequest,
    EquationHwpxRequestDraft, EquationHwpxSource, EquationLayout, EquationStyle,
};
pub use font_metric_receipt::{
    CURRENT_FONT_METRIC_PROFILE_ID, CurrentFontMetricCell, CurrentFontMetricLimits,
    CurrentFontMetricReceipt, FontMetricReceiptError,
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
pub use id_index::{
    IdDeclaration, IdIndex, IdIndexError, IdIndexLimitConfig, IdIndexLimits, IdIssueKind, IdKind,
    IdLocation, IdReference, IdRuleProfile, IdValidationIssue, IdValidationReport,
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
pub use table_formula::{
    TABLE_CANONICAL_FORMULA_HWPX_PROFILE_ID, TABLE_FORMULA_HWPX_PROFILE_ID, TableFormulaHwpxError,
    TableFormulaHwpxLimitConfig, TableFormulaHwpxLimits, TableFormulaHwpxLowerer,
    TableFormulaHwpxLoweringReceipt, TableFormulaHwpxReadback, TableFormulaHwpxReader,
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
