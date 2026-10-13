//! One source-bound model retaining all qualified catalog branches and formula sidecars.
//! This does not supply missing field meanings, policy/issuer authority or full import admission.
use super::super::evaluation::{
    ImportedSourceFormulaEvaluation, SourceFormulaCellBinding, SourceFormulaEvaluationError,
    SourceFormulaEvaluationReceipt, SourceFormulaValue,
};
use super::fonts::{
    FONT_IMPORT_PROFILE, FONT_IMPORT_SCOPE, FontCatalogImportError, FontCatalogImportReceipt,
    ImportedCharacterFontLink, ImportedDocumentFonts, ImportedFontDefinition,
};
use super::security::{
    ActiveSecurityImportError, ActiveSecurityImportReceipt, ImportedActiveControlBinding,
    ImportedActiveResourceBinding, ImportedDocumentActiveSecurity,
    ImportedNativeFormSecurityBinding,
    settings::{
        ImportedDocumentSectionSettings, ImportedSectionSettings, SectionSettingsImportError,
        SectionSettingsImportReceipt,
    },
};
use super::{CatalogImportError, CatalogImportReceipt, ImportedDocumentCatalog};
use crate::{ActivationKind, ActiveContentError, ActiveContentInventory};
use domain_ir::{DocumentGraph, DocumentGraphLimits, Properties, PropertyValue};
use serde::Serialize;
use std::fmt;
use thiserror::Error;
#[cfg(test)]
mod tests;

pub const DOCUMENT_ASSEMBLY_PROFILE: &str = "hwpx-agent.document-import-assembly/partial-v1";
pub const DOCUMENT_ASSEMBLY_SCOPE: &str = "single_immutable_source_qualified_graph_fonts_security_settings_and_exact_formula_sidecars_not_full_meanings_policy_issuer_native_render_or_execution";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct DocumentAssemblyReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source: CatalogImportReceipt,
    pub fonts: FontCatalogImportReceipt,
    pub security: ActiveSecurityImportReceipt,
    pub settings: SectionSettingsImportReceipt,
    pub formulas: SourceFormulaEvaluationReceipt,
    pub graph_sha256: [u8; 32],
}

// Owning the outputs avoids a self-referential structure and keeps all typed data.
// No caller graphs, deserialization, raw actions or publication capability.
#[derive(Eq, PartialEq)]
struct AssemblyState {
    graph: DocumentGraph,
    fonts: Vec<ImportedFontDefinition>,
    font_links: Vec<ImportedCharacterFontLink>,
    settings: Vec<ImportedSectionSettings>,
    inventory: ActiveContentInventory,
    controls: Vec<ImportedActiveControlBinding>,
    resources: Vec<ImportedActiveResourceBinding>,
    native_forms: Vec<ImportedNativeFormSecurityBinding>,
    formula_values: Vec<SourceFormulaValue>,
    formula_bindings: Vec<SourceFormulaCellBinding>,
    receipt: DocumentAssemblyReceipt,
}
pub struct ImportedDocumentAssembly<'a, 'catalog, 'fields, 'source> {
    catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    state: AssemblyState,
}
impl fmt::Debug for ImportedDocumentAssembly<'_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedDocumentAssembly(<redacted>)")
    }
}
impl<'a, 'catalog, 'fields, 'source> ImportedDocumentAssembly<'a, 'catalog, 'fields, 'source> {
    /// Constructs every branch from the SAME non-deserializable immutable catalog.
    /// # Errors
    /// Rejects any original reader/scanner/formula error, graph conflict or source binding drift.
    pub fn import(
        catalog: &'a ImportedDocumentCatalog<'catalog, 'fields, 'source>,
    ) -> Result<Self, DocumentAssemblyError> {
        let fonts = ImportedDocumentFonts::import(catalog)?;
        let security = ImportedDocumentActiveSecurity::import(catalog)?;
        let settings = ImportedDocumentSectionSettings::import(&security)?;
        let formulas = ImportedSourceFormulaEvaluation::import(catalog.meanings)?;
        let graph = combine(catalog, &fonts, &settings, formulas.receipt())?;
        let receipt = DocumentAssemblyReceipt {
            profile: DOCUMENT_ASSEMBLY_PROFILE,
            qualification: DOCUMENT_ASSEMBLY_SCOPE,
            source: catalog.receipt().clone(),
            fonts: fonts.receipt().clone(),
            security: security.receipt().clone(),
            settings: settings.receipt().clone(),
            formulas: formulas.receipt().clone(),
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| DocumentAssemblyError::Graph)?,
        };
        // Every receipt chain is bound before exposing any model.
        if receipt.fonts.original_catalog_graph_sha256 != receipt.source.graph_sha256
            || receipt.security.original_catalog_graph_sha256 != receipt.source.graph_sha256
            || receipt.settings.original_security_graph_sha256 != receipt.security.graph_sha256
            || receipt.formulas.original_meaning_graph_sha256
                != receipt.source.original_meaning_graph_sha256
            || [
                receipt.fonts.source_package_sha256,
                receipt.security.source_package_sha256,
                receipt.settings.source_package_sha256,
                receipt.formulas.source_package_sha256,
            ]
            .iter()
            .any(|sha| *sha != receipt.source.source_package_sha256)
            || receipt.security.activation_allowed
            || security.inventory().activation_allowed()
        {
            return Err(DocumentAssemblyError::Binding);
        }
        let state = AssemblyState {
            graph,
            fonts: fonts.definitions().to_vec(),
            font_links: fonts.links().to_vec(),
            settings: settings.settings().to_vec(),
            inventory: security.inventory().clone(),
            controls: security.controls().to_vec(),
            resources: security.resources().to_vec(),
            native_forms: security.native_forms().to_vec(),
            formula_values: formulas.values().to_vec(),
            formula_bindings: formulas.source_bindings().to_vec(),
            receipt,
        };
        Ok(Self { catalog, state })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.state.graph
    }
    #[must_use]
    pub fn font_definitions(&self) -> &[ImportedFontDefinition] {
        &self.state.fonts
    }
    #[must_use]
    pub fn font_links(&self) -> &[ImportedCharacterFontLink] {
        &self.state.font_links
    }
    #[must_use]
    pub fn section_settings(&self) -> &[ImportedSectionSettings] {
        &self.state.settings
    }
    #[must_use]
    pub const fn inventory(&self) -> &ActiveContentInventory {
        &self.state.inventory
    }
    #[must_use]
    pub fn active_controls(&self) -> &[ImportedActiveControlBinding] {
        &self.state.controls
    }
    #[must_use]
    pub fn active_resources(&self) -> &[ImportedActiveResourceBinding] {
        &self.state.resources
    }
    #[must_use]
    pub fn native_forms(&self) -> &[ImportedNativeFormSecurityBinding] {
        &self.state.native_forms
    }
    #[must_use]
    pub fn formula_values(&self) -> &[SourceFormulaValue] {
        &self.state.formula_values
    }
    #[must_use]
    pub fn formula_source_bindings(&self) -> &[SourceFormulaCellBinding] {
        &self.state.formula_bindings
    }
    #[must_use]
    pub const fn receipt(&self) -> &DocumentAssemblyReceipt {
        &self.state.receipt
    }
    /// Original inventory authority remains unconditionally passive.
    /// # Errors
    /// Rejects all typed activation actions; never invokes native/UI code.
    pub fn require_activation(&self, action: ActivationKind) -> Result<(), DocumentAssemblyError> {
        self.state.inventory.authorize(action)?;
        Err(DocumentAssemblyError::Binding)
    }
    /// Checks fresh original whole catalog, then every output in the complete assembly.
    /// # Errors
    /// Rejects changed bytes or any cached graph/sidecar/inventory/receipt drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<DocumentAssemblyReceipt, DocumentAssemblyError> {
        self.catalog.verify_source(fresh)?;
        let rebuilt = Self::import(self.catalog)?;
        if self.state != rebuilt.state {
            return Err(DocumentAssemblyError::Binding);
        }
        Ok(self.state.receipt.clone())
    }
}

fn combine(
    catalog: &ImportedDocumentCatalog<'_, '_, '_>,
    fonts: &ImportedDocumentFonts<'_, '_, '_, '_>,
    settings: &ImportedDocumentSectionSettings<'_, '_, '_, '_, '_>,
    formulas: &SourceFormulaEvaluationReceipt,
) -> Result<DocumentGraph, DocumentAssemblyError> {
    let original = catalog.graph().clone().into_draft();
    if settings.graph().document_id() != catalog.graph().document_id()
        || fonts.receipt().source_package_sha256 != catalog.receipt().source_package_sha256
        || settings.receipt().source_package_sha256 != catalog.receipt().source_package_sha256
    {
        return Err(DocumentAssemblyError::Binding);
    }
    let font_graph = fonts.graph().clone().into_draft();
    // Prove the font branch changes only styles and its exact two new markers.
    let mut expected_metadata = original.metadata.clone();
    insert_new(
        &mut expected_metadata,
        "font_catalog_import_profile",
        PropertyValue::Text(FONT_IMPORT_PROFILE.into()),
    )?;
    insert_new(
        &mut expected_metadata,
        "font_catalog_import_scope",
        PropertyValue::Text(FONT_IMPORT_SCOPE.into()),
    )?;
    if font_graph.metadata != expected_metadata {
        return Err(DocumentAssemblyError::Binding);
    }
    let mut inverse = font_graph.clone();
    inverse.styles.clone_from(&original.styles);
    inverse.metadata = original.metadata.clone();
    if inverse != original {
        return Err(DocumentAssemblyError::Binding);
    }
    let mut draft = settings.graph().clone().into_draft();
    // No last-writer-wins merge: reject a settings/security branch that modifies styles.
    if draft.styles != original.styles {
        return Err(DocumentAssemblyError::Binding);
    }
    draft.styles = font_graph.styles;
    insert_new(
        &mut draft.metadata,
        "font_catalog_import_profile",
        PropertyValue::Text(FONT_IMPORT_PROFILE.into()),
    )?;
    insert_new(
        &mut draft.metadata,
        "font_catalog_import_scope",
        PropertyValue::Text(FONT_IMPORT_SCOPE.into()),
    )?;
    insert_new(
        &mut draft.metadata,
        "document_assembly_profile",
        PropertyValue::Text(DOCUMENT_ASSEMBLY_PROFILE.into()),
    )?;
    insert_new(
        &mut draft.metadata,
        "document_assembly_scope",
        PropertyValue::Text(DOCUMENT_ASSEMBLY_SCOPE.into()),
    )?;
    // Bind separately accessible values/cell anchors without overwriting native caches or body text.
    insert_new(
        &mut draft.metadata,
        "source_formula_sidecar_sha256",
        PropertyValue::Text(crate::document_import::hex_digest(
            formulas.values_and_source_bindings_sha256,
        )),
    )?;
    DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
        .map_err(|_| DocumentAssemblyError::Graph)
}
fn insert_new(
    properties: &mut Properties,
    key: &str,
    value: PropertyValue,
) -> Result<(), DocumentAssemblyError> {
    if properties.iter().any(|(existing, _)| existing == key) {
        return Err(DocumentAssemblyError::Binding);
    }
    properties.insert(key, value);
    Ok(())
}
#[derive(Debug, Error)]
pub enum DocumentAssemblyError {
    #[error("assembly original source catalog rejected")]
    Catalog(#[from] CatalogImportError),
    #[error("assembly original font branch rejected")]
    Fonts(#[from] FontCatalogImportError),
    #[error("assembly original active security branch rejected")]
    Security(#[from] ActiveSecurityImportError),
    #[error("assembly original section settings branch rejected")]
    Settings(#[from] SectionSettingsImportError),
    #[error("assembly original source formula branch rejected")]
    Formulas(#[from] SourceFormulaEvaluationError),
    #[error("assembly original passive inventory denies activation")]
    Activation(#[from] ActiveContentError),
    #[error("assembly whole source or branch effect conflict")]
    Binding,
    #[error("assembly original bounded graph validation rejected")]
    Graph,
}
