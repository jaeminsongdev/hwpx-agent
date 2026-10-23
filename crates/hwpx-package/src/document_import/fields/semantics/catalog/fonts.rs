//! Source-scoped original font definitions and seven-language character links.
//! Declared fonts/embedding/substitution are not platform availability or rendering.
mod source;
pub mod replacement;
pub mod names;
use super::{CatalogImportError, ImportedDocumentCatalog};
use crate::FontFace;
use domain_ir::{DocumentGraph, DocumentGraphLimits, LogicalId, PropertyValue, SourceAnchorHandle};
use serde::{Deserialize, Serialize};
use std::fmt;
use thiserror::Error;
pub const FONT_IMPORT_PROFILE: &str = "hwpx-agent.document-import-font-catalog/partial-v1";
pub const FONT_IMPORT_SCOPE: &str = "original_typed_font_faces_and_actual_seven_language_source_references_not_availability_substitution_metrics_embedding_activation_render_security_or_execution";

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ImportedFontLanguage {
    Hangul,
    Latin,
    Hanja,
    Japanese,
    Other,
    Symbol,
    User,
}
impl ImportedFontLanguage {
    pub(super) const fn name(self) -> &'static str {
        match self {
            Self::Hangul => "hangul",
            Self::Latin => "latin",
            Self::Hanja => "hanja",
            Self::Japanese => "japanese",
            Self::Other => "other",
            Self::Symbol => "symbol",
            Self::User => "user",
        }
    }
}
#[derive(Clone, Eq, PartialEq)]
pub struct ImportedFontDefinition {
    pub font_id: LogicalId,
    pub language: ImportedFontLanguage,
    pub source_anchor: SourceAnchorHandle,
    /// Unchanged original reader output, never inferred platform font metadata.
    pub declared: FontFace,
}
impl fmt::Debug for ImportedFontDefinition {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedFontDefinition(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedCharacterFontLink {
    pub character_property_id: LogicalId,
    pub font_reference_anchor: SourceAnchorHandle,
    pub language: ImportedFontLanguage,
    pub font_id: LogicalId,
}
impl fmt::Debug for ImportedCharacterFontLink {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedCharacterFontLink(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FontCatalogImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_catalog_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub source_links_sha256: [u8; 32],
    pub source_font_groups: usize,
    pub source_font_definitions: usize,
    pub character_font_links: usize,
    pub declarations_with_embedded_flag: usize,
    pub declarations_with_substitute: usize,
    pub declarations_with_type_info: usize,
}
pub struct ImportedDocumentFonts<'a, 'catalog, 'fields, 'source> {
    catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    graph: DocumentGraph,
    definitions: Vec<ImportedFontDefinition>,
    links: Vec<ImportedCharacterFontLink>,
    receipt: FontCatalogImportReceipt,
}
impl fmt::Debug for ImportedDocumentFonts<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedDocumentFonts(<redacted>)")
    }
}
impl<'a, 'catalog, 'fields, 'source> ImportedDocumentFonts<'a, 'catalog, 'fields, 'source> {
    /// Binds original typed font groups/IDs to exact source positions and all actual fontRef axes.
    /// # Errors
    /// Rejects original reader/source/catalog errors, duplicate/dangling/foreign links and finite limits.
    pub fn import(
        catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    ) -> Result<Self, FontCatalogImportError> {
        let mut draft = catalog.graph().clone().into_draft();
        let (definitions, links) = source::bind(catalog, &mut draft.styles)?;
        draft.metadata.insert(
            "font_catalog_import_profile",
            PropertyValue::Text(FONT_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "font_catalog_import_scope",
            PropertyValue::Text(FONT_IMPORT_SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| FontCatalogImportError::Graph)?;
        let receipt = FontCatalogImportReceipt {
            profile: FONT_IMPORT_PROFILE,
            qualification: FONT_IMPORT_SCOPE,
            source_package_sha256: catalog.receipt().source_package_sha256,
            original_catalog_graph_sha256: catalog.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| FontCatalogImportError::Graph)?,
            source_links_sha256: source::digest(&links)?,
            source_font_groups: catalog.character_catalog().font_faces.len(),
            source_font_definitions: definitions.len(),
            character_font_links: links.len(),
            declarations_with_embedded_flag: definitions
                .iter()
                .filter(|d| d.declared.is_embedded)
                .count(),
            declarations_with_substitute: definitions
                .iter()
                .filter(|d| d.declared.substitute.is_some())
                .count(),
            declarations_with_type_info: definitions
                .iter()
                .filter(|d| d.declared.type_info.is_some())
                .count(),
        };
        Ok(Self {
            catalog,
            graph,
            definitions,
            links,
            receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub fn definitions(&self) -> &[ImportedFontDefinition] {
        &self.definitions
    }
    #[must_use]
    pub fn links(&self) -> &[ImportedCharacterFontLink] {
        &self.links
    }
    #[must_use]
    pub const fn receipt(&self) -> &FontCatalogImportReceipt {
        &self.receipt
    }
    /// Original whole source/catalog freshness plus deterministic complete font/graph reconstruction.
    /// # Errors
    /// Rejects any changed source/graph/typed declaration/link/receipt; never rebinds stale fonts.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<FontCatalogImportReceipt, FontCatalogImportError> {
        self.catalog.verify_source(fresh)?;
        let rebuilt = Self::import(self.catalog)?;
        if self.graph != rebuilt.graph
            || self.definitions != rebuilt.definitions
            || self.links != rebuilt.links
            || self.receipt != rebuilt.receipt
        {
            return Err(FontCatalogImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum FontCatalogImportError {
    #[error("font original source/typed catalog rejected")]
    Catalog(#[from] CatalogImportError),
    #[error("font actual source/group/reference binding rejected")]
    Binding,
    #[error("font source catalog work/serialization budget exceeded")]
    Limit,
    #[error("font augmented partial source graph rejected")]
    Graph,
}
