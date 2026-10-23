//! Current executable consumer: locked historical36 plus explicit in-memory fixtures.
use domain_ir::DocumentId;
use hwpx_package::{
    ActivationKind, ActiveContentError,
    document_import::{
        ImportedSourcePackage, SourceImportLimits,
        fields::{
            ImportedDocumentFields,
            semantics::{
                ImportedDocumentFieldSemantics,
                catalog::{
                    ImportedDocumentCatalog,
                    security::{
                        ActiveSecurityImportError, ActiveSecurityImportReceipt,
                        ImportedDocumentActiveSecurity,
                    },
                },
            },
        },
        forms::ImportedDocumentForms,
    },
};
use serde::Serialize;
use sha2::{Digest as _, Sha256};
use std::error::Error;
#[path = "../tests/support/document_import_security_fixture.rs"]
mod fixture;

#[derive(Default, Serialize)]
struct Evidence {
    profile: &'static str,
    historical_inputs: usize,
    generated_inputs: usize,
    original_inventory_controls: usize,
    original_inventory_resources: usize,
    represented_inventory_controls: usize,
    native_form_bindings: usize,
    native_forms_missing_from_original_inventory: usize,
    generated_quarantined_commands: usize,
    denied_actions: usize,
    receipts: Vec<ActiveSecurityImportReceipt>,
}
fn consume(bytes: &[u8], generated: bool, evidence: &mut Evidence) -> Result<(), Box<dyn Error>> {
    let source = ImportedSourcePackage::import(
        bytes,
        DocumentId::parse("active-security-probe")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
    )?;
    let forms = ImportedDocumentForms::import(source)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    if security.verify_source(bytes)? != *security.receipt() {
        return Err("whole fresh security receipt drift".into());
    }
    for binding in security.controls() {
        forms.source().resolve_anchor(&binding.source_anchor)?;
    }
    for binding in security.resources() {
        forms.source().resolve_anchor(&binding.source_anchor)?;
    }
    for binding in security.native_forms() {
        forms.source().resolve_anchor(&binding.source_anchor)?;
    }
    for action in [
        ActivationKind::Ole,
        ActivationKind::Multimedia,
        ActivationKind::EmbeddedExecutable,
        ActivationKind::ScriptMacro,
        ActivationKind::FormCommand,
        ActivationKind::ExternalLink,
    ] {
        if !matches!(security.require_activation(action), Err(ActiveSecurityImportError::Inventory(
            ActiveContentError::ActivationDenied { action: denied })) if denied == action)
        {
            return Err("normal tier activation was not denied".into());
        }
        evidence.denied_actions += 1;
    }
    let receipt = security.receipt();
    if generated {
        evidence.generated_inputs += 1;
        evidence.generated_quarantined_commands += security
            .native_forms()
            .iter()
            .filter(|v| {
                v.command_present
                    && v.disposition == hwpx_package::ActiveContentDisposition::Quarantine
            })
            .count();
    } else {
        evidence.historical_inputs += 1;
        evidence.original_inventory_controls += receipt.source_control_bindings;
        evidence.original_inventory_resources += receipt.source_resource_bindings;
        evidence.represented_inventory_controls += receipt.represented_control_bindings;
        evidence.native_form_bindings += receipt.native_form_bindings;
        evidence.native_forms_missing_from_original_inventory +=
            receipt.native_forms_not_in_original_inventory;
    }
    evidence.receipts.push(receipt.clone());
    Ok(())
}
fn main() -> Result<(), Box<dyn Error>> {
    let corpus = fixture::actual_corpus()?;
    let mut evidence = Evidence {
        profile: "hwpx-agent.document-import-active-security-consumer/partial-v1",
        ..Evidence::default()
    };
    for bytes in &corpus {
        consume(bytes, false, &mut evidence)?;
    }
    let bytes = fixture::generated(
        &corpus[0],
        r#"<hp:p id="1"><hp:run><hp:script>FIXTURE-COMMAND-PRIVATE</hp:script><hp:video videotype="Web" tag="https://fixture.invalid/private"/><hp:ole objectType="EMBEDDED" binaryItemIDRef="ole1" hasMoniker="0"/></hp:run></hp:p>"#,
        true,
    )?;
    consume(&bytes, true, &mut evidence)?;
    for tag in ["checkBtn", "radioBtn", "edit", "comboBox", "listBox"] {
        consume(
            &fixture::command_fixture(&corpus, tag, "FIXTURE-COMMAND-PRIVATE")?,
            true,
            &mut evidence,
        )?;
    }
    consume(
        &fixture::command_fixture(&corpus, "checkBtn", "")?,
        true,
        &mut evidence,
    )?;
    if evidence.historical_inputs != 36
        || evidence.generated_inputs != 7
        || evidence.generated_quarantined_commands != 5
        || evidence.native_forms_missing_from_original_inventory == 0
        || evidence.denied_actions != 43 * 6
    {
        return Err("consumer coverage drift".into());
    }
    println!("{}", serde_json::to_string(&evidence)?);
    Ok(())
}
