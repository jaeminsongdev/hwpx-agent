use domain_ir::{DocumentGraph, DocumentGraphLimits, Flow, Node, Properties};
use hwpx_package::{ActivationKind, ActiveContentControlKind, ActiveContentDisposition,
    ActiveContentError, ActiveContentInventory, ActiveContentLimits, ActiveContentResourceKind,
    ActiveContentSignature, BoundedZipReader, PackageGraph, PackageGraphLimits, PackageLimits,
    document_import::fields::{ImportedDocumentFields, semantics::{ImportedDocumentFieldSemantics,
        catalog::{ImportedDocumentCatalog, security::{ActiveSecurityImportError,
            ImportedDocumentActiveSecurity, NativeSecurityQualification}}}}};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
mod base;
#[path = "support/document_import_security_fixture.rs"]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;

fn actions() -> [ActivationKind; 6] {
    [ActivationKind::Ole, ActivationKind::Multimedia, ActivationKind::EmbeddedExecutable,
        ActivationKind::ScriptMacro, ActivationKind::FormCommand, ActivationKind::ExternalLink]
}
fn without(properties: &Properties, keys: &[&str]) -> Properties {
    let mut result = Properties::new();
    for (key, value) in properties.iter().filter(|(key, _)| !keys.contains(key)) {
        result.insert(key, value.clone());
    }
    result
}
fn restore(flow: &mut Flow) {
    for node in &mut flow.children {
        let common = match node {
            Node::Paragraph(v) => &mut v.common, Node::Table(v) => &mut v.common,
            Node::Equation(v) => &mut v.common, Node::Drawing(v) => &mut v.common,
            Node::Chart(v) => &mut v.common, Node::Field(v) => &mut v.common,
            Node::FormControl(v) => &mut v.common, Node::Break(v) => &mut v.common,
            Node::EmbeddedObject(v) => &mut v.common,
        };
        common.semantics = without(&common.semantics, &["source_active_content_disposition"]);
        match node {
            Node::Table(v) => { for cell in &mut v.cells { restore(&mut cell.body); } }
            Node::Drawing(v) => restore(&mut v.children), _ => (),
        }
    }
}
fn check(bytes: &[u8]) -> Result<(usize, usize, usize), Box<dyn Error>> {
    let forms = base::forms(bytes, "security-source")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    assert_eq!(security.verify_source(bytes)?, *security.receipt());
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    let inventory = ActiveContentInventory::scan(&mut reader, &graph,
        PackageGraphLimits::default(), ActiveContentLimits::default())?;
    assert_eq!(security.inventory(), &inventory);
    assert_eq!(security.controls().len(), inventory.controls().len());
    assert_eq!(security.resources().len(), inventory.resources().len());
    for binding in security.controls() { forms.source().resolve_anchor(&binding.source_anchor)?; }
    for binding in security.resources() { forms.source().resolve_anchor(&binding.source_anchor)?; }
    for action in actions() {
        assert!(matches!(security.require_activation(action),
            Err(ActiveSecurityImportError::Inventory(ActiveContentError::ActivationDenied { action: denied })) if denied == action));
    }
    assert!(!security.receipt().activation_allowed);
    assert_eq!(security.receipt().native_security, NativeSecurityQualification::NotAssessedByActiveContentInventory);
    let mut draft = security.graph().clone().into_draft();
    draft.metadata = without(&draft.metadata, &["active_security_import_profile", "active_security_import_scope"]);
    draft.security_state.properties = without(&draft.security_state.properties,
        &["source_active_inventory_state_sha256", "active_execution_allowed", "native_security_assessment"]);
    for section in &mut draft.sections { restore(&mut section.body); }
    for note in &mut draft.notes { restore(&mut note.body); }
    for resource in &mut draft.resources {
        resource.metadata = without(&resource.metadata, &["source_active_content_kind",
            "source_active_content_disposition", "source_active_binary_signature_check_not_document_signature"]);
    }
    assert_eq!(&DocumentGraph::from_draft(draft, DocumentGraphLimits::default())?, catalog.graph());
    Ok((security.controls().len(), security.receipt().represented_control_bindings, security.resources().len()))
}
#[test]
fn locked_actual36_inventory_source_anchors_full_graph_inverse_and_activation_denial() -> TestResult {
    let corpus = fixture::actual_corpus()?;
    assert_eq!(corpus.len(), 36);
    let mut controls = 0;
    let mut represented = 0;
    for bytes in corpus { let counts = check(&bytes)?; controls += counts.0; represented += counts.1; }
    assert!(controls > 0);
    assert_eq!(controls, represented);
    Ok(())
}
#[test]
fn generated_script_video_ole_are_passive_source_observations_not_native_acceptance() -> TestResult {
    let bytes = fixture::generated(&base::captured()?,
        r#"<hp:p id="1"><hp:run><hp:script>FIXTURE-COMMAND-PRIVATE</hp:script><hp:video videotype="Web" tag="https://fixture.invalid/private"/><hp:ole objectType="EMBEDDED" binaryItemIDRef="ole1" hasMoniker="0"/></hp:run></hp:p>"#, true)?;
    let counts = check(&bytes)?;
    assert_eq!(counts, (3, 0, 1));
    let forms = base::forms(&bytes, "security-source")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    assert_eq!(security.controls().iter().filter(|v| v.disposition == ActiveContentDisposition::Quarantine).count(), 2);
    assert!(security.controls().iter().any(|v| v.kind == ActiveContentControlKind::Ole));
    assert_eq!(security.resources()[0].kind, ActiveContentResourceKind::OpaqueOle);
    assert_eq!(security.resources()[0].payload_signature, ActiveContentSignature::Verified);
    let json = serde_json::to_string(security.receipt())?;
    assert!(!json.contains("FIXTURE-COMMAND"));
    assert!(!json.contains("fixture.invalid"));
    assert!(!format!("{:?}", security.controls()).contains("FIXTURE-COMMAND"));
    Ok(())
}
#[test]
fn fresh_whole_source_drift_is_denied_and_minimal_header_is_not_promoted() -> TestResult {
    let bytes = base::captured()?;
    let forms = base::forms(&bytes, "security-source")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let catalog = ImportedDocumentCatalog::import(&meanings)?;
    let security = ImportedDocumentActiveSecurity::import(&catalog)?;
    let mut drift = bytes;
    drift[0] ^= 1;
    assert!(security.verify_source(&drift).is_err());
    let minimal = base::forms(&base::package("<hp:p id=\"1\"><hp:run><hp:t>fixture</hp:t></hp:run></hp:p>")?, "minimal")?;
    let fields = ImportedDocumentFields::import(&minimal)?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    assert!(ImportedDocumentCatalog::import(&meanings).is_err());
    Ok(())
}
#[test]
fn missing_ole_relationship_and_foreign_active_element_remain_rejected() -> TestResult {
    for body in [
        r#"<hp:p id="1"><hp:run><hp:ole objectType="EMBEDDED" binaryItemIDRef="missing" hasMoniker="0"/></hp:run></hp:p>"#,
        r#"<hp:p id="1"><hp:run><x:script xmlns:x="urn:foreign">fixture</x:script></hp:run></hp:p>"#,
    ] {
        let bytes = fixture::generated(&base::captured()?, body, false)?;
        assert!(check(&bytes).is_err());
    }
    Ok(())
}
