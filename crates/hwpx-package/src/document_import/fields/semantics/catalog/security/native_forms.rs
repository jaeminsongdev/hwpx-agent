//! Native five-family form coverage supplements, never rewrites, original P08 inventory.
use super::{ActiveSecurityImportError, ImportedActiveControlBinding};
use crate::document_import::forms::ImportedDocumentForms;
use crate::{ActiveContentControlKind, ActiveContentDisposition};
use domain_ir::{LogicalId, NativeFormTag, SourceAnchorHandle};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};

#[derive(Clone, Eq, PartialEq, Serialize)]
pub struct ImportedNativeFormSecurityBinding {
    pub source_anchor: SourceAnchorHandle,
    pub node_id: LogicalId,
    pub tag: NativeFormTag,
    pub disposition: ActiveContentDisposition,
    pub command_present: bool,
    /// Original inventory omits checkBtn/radioBtn; never conceal this coverage gap.
    pub in_original_inventory: bool,
}
impl fmt::Debug for ImportedNativeFormSecurityBinding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ImportedNativeFormSecurityBinding(<redacted>)")
    }
}
pub(super) fn bind(
    forms: &ImportedDocumentForms,
    nodes: &BTreeMap<LogicalId, LogicalId>,
    controls: &[ImportedActiveControlBinding],
) -> Result<Vec<ImportedNativeFormSecurityBinding>, ActiveSecurityImportError> {
    let original: BTreeMap<_, _> = controls
        .iter()
        .map(|c| (&c.source_anchor.opaque_handle, c))
        .collect();
    let mut result = Vec::new();
    let mut seen = BTreeSet::new();
    for form in forms.forms() {
        let resolved = forms
            .source()
            .resolve_anchor(&form.source_anchor)
            .map_err(|_| ActiveSecurityImportError::Binding)?;
        let element = resolved
            .element()
            .ok_or(ActiveSecurityImportError::Binding)?;
        let (tag, kind) = match form.tag {
            NativeFormTag::CheckBtn => ("checkBtn", ActiveContentControlKind::FormButton),
            NativeFormTag::RadioBtn => ("radioBtn", ActiveContentControlKind::FormButton),
            NativeFormTag::ComboBox => ("comboBox", ActiveContentControlKind::FormComboBox),
            NativeFormTag::ListBox => ("listBox", ActiveContentControlKind::FormListBox),
            NativeFormTag::Edit => ("edit", ActiveContentControlKind::FormEdit),
        };
        if element.name().local_name() != tag
            || element.name().namespace() != Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
            || nodes.get(&form.source_anchor.opaque_handle) != Some(&form.node_id)
            || !seen.insert(form.source_anchor.opaque_handle.clone())
        {
            return Err(ActiveSecurityImportError::Binding);
        }
        let commands: Vec<_> = element
            .attributes()
            .iter()
            .filter(|a| a.name().local_name() == "command")
            .collect();
        if commands.len() > 1 || commands.iter().any(|a| a.name().namespace().is_some()) {
            return Err(ActiveSecurityImportError::Binding);
        }
        // Keep the original reader's explicit empty-value absence semantics.
        let command = commands
            .first()
            .map(|a| a.semantic_value())
            .filter(|v| !v.is_empty());
        let sha = command
            .map(|v| crate::document_import::hex_digest(Sha256::digest(v.as_bytes()).into()));
        if sha != form.common.command_sha256 {
            return Err(ActiveSecurityImportError::Binding);
        }
        let command_present = command.is_some_and(|v| !v.is_empty());
        let disposition = if command_present {
            ActiveContentDisposition::Quarantine
        } else {
            ActiveContentDisposition::PreserveBlocked
        };
        let inventory = original.get(&form.source_anchor.opaque_handle);
        if let Some(control) = inventory
            && (control.kind != kind
                || control.disposition != disposition
                || control.represented_node_id.as_ref() != Some(&form.node_id))
        {
            return Err(ActiveSecurityImportError::Binding);
        }
        // Missing scanner coverage is allowed ONLY for its two proven omitted tags.
        if inventory.is_none()
            && !matches!(form.tag, NativeFormTag::CheckBtn | NativeFormTag::RadioBtn)
        {
            return Err(ActiveSecurityImportError::Binding);
        }
        result.push(ImportedNativeFormSecurityBinding {
            source_anchor: form.source_anchor.clone(),
            node_id: form.node_id.clone(),
            tag: form.tag,
            disposition,
            command_present,
            in_original_inventory: inventory.is_some(),
        });
    }
    Ok(result)
}
