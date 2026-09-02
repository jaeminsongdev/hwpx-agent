#![forbid(unsafe_code)]

mod document_graph;
mod identity;
mod selector;
mod units;

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
    ArtifactId, BackendOpaqueId, BookmarkId, ChangeId, FieldId, IdentityError, LogicalNodeId,
    MAX_TYPED_ID_BYTES, ProjectId, ResourceId, RevisionId, StyleId,
};
pub use selector::{
    NamedSelectorKind, NodeKind, ResolvedTarget, Selector, SelectorError, SelectorExpectation,
    SelectorLimits, SelectorSnapshot, StructuralPath, StructuralRoot, StructuralStep,
    TextContextAnchor, TextRange,
};
pub use units::{
    AngleMicrodegrees, Conversion, ConversionReceipt, CoordinateAnchor, CoordinateSpace, HwpUnit,
    LengthMicrometers, PointMilli, Position2D, RatioMillionths, RationalInput, UnitError, UnitKind,
    ZOrder,
};
