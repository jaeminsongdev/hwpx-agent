//! Original page/column readers bound to actual graph sections and complete spine order.
mod source;
use super::{ActiveSecurityImportError, ImportedDocumentActiveSecurity};
use crate::{ColumnDefinition, ColumnMetrics, PageSetup, PageSetupMetrics};
use domain_ir::{DocumentGraph, DocumentGraphLimits, LogicalId, PropertyValue, SourceAnchorHandle};
use serde::Serialize;
use std::fmt;
use thiserror::Error;

pub const SETTINGS_IMPORT_PROFILE: &str = "hwpx-agent.document-import-section-settings/partial-v1";
pub const SETTINGS_IMPORT_SCOPE: &str = "original_page_and_column_readers_actual_spine_header_count_source_bound_not_full_settings_layout_render_security_or_execution";

#[derive(Clone, Eq, PartialEq)]
pub struct ImportedColumnSettings {
    pub source_anchor: SourceAnchorHandle,
    pub definition: ColumnDefinition,
    pub metrics: ColumnMetrics,
}
impl fmt::Debug for ImportedColumnSettings {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedColumnSettings(<redacted>)")
    }
}
#[derive(Clone, Eq, PartialEq)]
pub struct ImportedSectionSettings {
    pub section_id: LogicalId,
    pub source_anchor: SourceAnchorHandle,
    pub section_properties_anchor: SourceAnchorHandle,
    pub page_anchor: SourceAnchorHandle,
    pub page: PageSetup,
    pub metrics: PageSetupMetrics,
    pub columns: Vec<ImportedColumnSettings>,
}
impl fmt::Debug for ImportedSectionSettings {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedSectionSettings(<redacted>)")
    }
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SectionSettingsImportReceipt {
    pub profile: &'static str,
    pub qualification: &'static str,
    pub source_package_sha256: [u8; 32],
    pub original_security_graph_sha256: [u8; 32],
    pub graph_sha256: [u8; 32],
    pub header_source_sha256: [u8; 32],
    pub sections: usize,
    pub page_setups: usize,
    pub column_spans: usize,
    pub section_boundaries: usize,
}
pub struct ImportedDocumentSectionSettings<'a, 'security, 'catalog, 'fields, 'source> {
    security: &'a ImportedDocumentActiveSecurity<'security, 'catalog, 'fields, 'source>,
    graph: DocumentGraph,
    settings: Vec<ImportedSectionSettings>,
    receipt: SectionSettingsImportReceipt,
}
impl fmt::Debug for ImportedDocumentSectionSettings<'_, '_, '_, '_, '_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedDocumentSectionSettings(<redacted>)")
    }
}
impl<'a, 'security, 'catalog, 'fields, 'source>
    ImportedDocumentSectionSettings<'a, 'security, 'catalog, 'fields, 'source>
{
    /// Atomic original reader checks against complete actual source spine and graph.
    /// # Errors
    /// Rejects header/count/page/columns/source/section mismatch; no defaults or fallback.
    pub fn import(
        security: &'a ImportedDocumentActiveSecurity<'security, 'catalog, 'fields, 'source>,
    ) -> Result<Self, SectionSettingsImportError> {
        let original = security.catalog.meanings.fields.forms.source();
        let mut draft = security.graph().clone().into_draft();
        let (settings, header) = source::bind(original, &mut draft.sections)?;
        draft.settings.insert(
            "source_header_section_count",
            PropertyValue::Integer(
                i64::try_from(settings.len()).map_err(|_| SectionSettingsImportError::Binding)?,
            ),
        );
        draft.settings.insert(
            "source_section_order",
            PropertyValue::List(
                settings
                    .iter()
                    .map(|s| PropertyValue::Id(s.section_id.clone()))
                    .collect(),
            ),
        );
        draft.metadata.insert(
            "section_settings_import_profile",
            PropertyValue::Text(SETTINGS_IMPORT_PROFILE.into()),
        );
        draft.metadata.insert(
            "section_settings_import_scope",
            PropertyValue::Text(SETTINGS_IMPORT_SCOPE.into()),
        );
        let graph = DocumentGraph::from_draft(draft, DocumentGraphLimits::default())
            .map_err(|_| SectionSettingsImportError::Graph)?;
        let receipt = SectionSettingsImportReceipt {
            profile: SETTINGS_IMPORT_PROFILE,
            qualification: SETTINGS_IMPORT_SCOPE,
            source_package_sha256: security.receipt().source_package_sha256,
            original_security_graph_sha256: security.receipt().graph_sha256,
            graph_sha256: graph
                .canonical_sha256()
                .map_err(|_| SectionSettingsImportError::Graph)?,
            header_source_sha256: header,
            sections: settings.len(),
            page_setups: settings.len(),
            column_spans: settings.iter().map(|s| s.columns.len()).sum(),
            section_boundaries: settings.len().saturating_sub(1),
        };
        Ok(Self {
            security,
            graph,
            settings,
            receipt,
        })
    }
    #[must_use]
    pub const fn graph(&self) -> &DocumentGraph {
        &self.graph
    }
    #[must_use]
    pub fn settings(&self) -> &[ImportedSectionSettings] {
        &self.settings
    }
    #[must_use]
    pub const fn receipt(&self) -> &SectionSettingsImportReceipt {
        &self.receipt
    }
    /// Original immutable whole-package identity plus full prior fresh reconstruction,
    /// then deterministic settings reconstruction from those same fixed source bytes.
    /// # Errors
    /// Rejects fresh byte/source/previous graph/security or settings/receipt drift.
    pub fn verify_source(
        &self,
        fresh: &[u8],
    ) -> Result<SectionSettingsImportReceipt, SectionSettingsImportError> {
        self.security.verify_source(fresh)?;
        let rebuilt = Self::import(self.security)?;
        if self.graph != rebuilt.graph
            || self.settings != rebuilt.settings
            || self.receipt != rebuilt.receipt
        {
            return Err(SectionSettingsImportError::Binding);
        }
        Ok(self.receipt.clone())
    }
}
#[derive(Debug, Error)]
pub enum SectionSettingsImportError {
    #[error("section settings original fresh security/source rejected")]
    Security(#[from] ActiveSecurityImportError),
    #[error("section settings original page reader rejected")]
    Page(#[from] crate::PageSetupError),
    #[error("section settings original column/count reader rejected")]
    Columns(#[from] crate::SectionColumnError),
    #[error("section settings source/header/spine/graph binding rejected")]
    Binding,
    #[error("section settings bounded graph rejected")]
    Graph,
}
