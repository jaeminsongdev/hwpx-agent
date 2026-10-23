//! Same-source bookmark graph edges and authenticated stored readback, not Native.
use domain_ir::{
    DocumentGraph, DocumentGraphLimits, DocumentId, Flow, Node, Properties, PropertyValue,
    ReferenceAuxiliaryLimits, RevisionId,
};
use hwpx_agent_cli::form_value_operation::full_document::{
    FullDocumentFormContext, FullDocumentFormError,
};
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    bookmark_crossref::SourceBookmarkResolution,
    semantics::{
        FIELD_SEMANTICS_PROFILE, FIELD_SEMANTICS_SCOPE, ImportedDocumentFieldSemantics,
        ImportedFieldMeaning, evaluation::ImportedSourceFormulaEvaluation,
        source_index::SourceFieldMeaningIndex,
    },
};
use serde_json::Value;
use sha2::{Digest as _, Sha256};
use std::{
    error::Error,
    fs::OpenOptions,
    io::Read,
    path::Path,
    time::{Duration, Instant},
};
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
type TestResult = Result<(), Box<dyn Error>>;
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
fn limits() -> Result<ReferenceAuxiliaryLimits, Box<dyn Error>> {
    Ok(ReferenceAuxiliaryLimits::new(Default::default())?)
}
fn field(id: u32, name: &str, display: u8, hyperlink: bool) -> String {
    let command = format!("?{name};6;{display};{};0", u8::from(hyperlink))
        .replace('&', "&amp;")
        .replace('<', "&lt;");
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='CROSSREF'><hp:parameters cnt='1'><hp:stringParam name='Command'>{command}</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>private unverified cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}'/></hp:ctrl>"
    )
}
fn package(body: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    base::package(&fixture::paragraph(body))
}
fn source() -> Result<Vec<u8>, Box<dyn Error>> {
    package(&format!(
        "{}{}",
        fixture::marker("private-target"),
        field(1, "private-target", 0, false)
    ))
}
fn remove_meanings(flow: &mut Flow) {
    for node in &mut flow.children {
        match node {
            Node::Field(field) => {
                let mut properties = Properties::new();
                for (key, value) in field.properties.iter() {
                    if key != "source_derived_meaning" {
                        properties.insert(key, value.clone());
                    }
                }
                field.properties = properties;
            }
            Node::Table(table) => {
                for cell in &mut table.cells {
                    remove_meanings(&mut cell.body);
                }
            }
            Node::Drawing(drawing) => remove_meanings(&mut drawing.children),
            _ => (),
        }
    }
}
fn exact_delta(
    fields: &ImportedDocumentFields<'_>,
    meanings: &ImportedDocumentFieldSemantics<'_, '_>,
) -> TestResult {
    let original = fields.graph().clone().into_draft();
    let mut changed = meanings.graph().clone().into_draft();
    let bound: std::collections::BTreeSet<_> = meanings
        .observations()
        .iter()
        .filter_map(|item| match &item.meaning {
            ImportedFieldMeaning::BookmarkCrossReference { command }
                if matches!(command.target, SourceBookmarkResolution::Bound { .. }) =>
            {
                Some(&item.reference_id)
            }
            _ => None,
        })
        .collect();
    assert_eq!(original.references.len(), changed.references.len());
    changed.metadata = original.metadata.clone();
    for (old, new) in original.references.iter().zip(&mut changed.references) {
        assert_eq!(old.reference_id, new.reference_id);
        let mut properties = Properties::new();
        for (key, value) in new.properties.iter() {
            if key != "source_derived_meaning" {
                properties.insert(key, value.clone());
            }
        }
        new.properties = properties;
        if !bound.contains(&new.reference_id) {
            assert_eq!(new.target_node_id, old.target_node_id);
        }
        new.target_node_id = old.target_node_id.clone();
    }
    for section in &mut changed.sections {
        remove_meanings(&mut section.body);
    }
    for note in &mut changed.notes {
        remove_meanings(&mut note.body);
    }
    assert_eq!(
        DocumentGraph::from_draft(changed, DocumentGraphLimits::default())?,
        *fields.graph()
    );
    Ok(())
}
fn check_edges(bytes: &[u8], document: &str) -> Result<usize, Box<dyn Error>> {
    let forms = base::forms(bytes, document)?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let before = fields.graph().canonical_sha256()?;
    let meanings = ImportedDocumentFieldSemantics::import(&fields)?;
    let graph = meanings.graph().clone().into_draft();
    let original_graph = fields.graph().clone().into_draft();
    let original_references: std::collections::BTreeMap<_, _> = original_graph
        .references
        .iter()
        .map(|v| (&v.reference_id, v))
        .collect();
    let references: std::collections::BTreeMap<_, _> = graph
        .references
        .iter()
        .map(|v| (&v.reference_id, v))
        .collect();
    let bookmarks: std::collections::BTreeMap<_, _> = forms
        .bookmarks()
        .iter()
        .map(|v| (&v.reference_id, v))
        .collect();
    let mut count = 0;
    for observation in meanings.observations() {
        if let ImportedFieldMeaning::BookmarkCrossReference { command } = &observation.meaning {
            let reference = references
                .get(&observation.reference_id)
                .ok_or("reference")?;
            let original = original_references
                .get(&observation.reference_id)
                .ok_or("original reference")?;
            assert!(original.target_node_id.is_none());
            match &command.target {
                SourceBookmarkResolution::Bound {
                    logical_target_id, ..
                } => {
                    let target = bookmarks.get(logical_target_id).ok_or("bookmark")?;
                    assert_eq!(
                        reference.target_node_id.as_ref(),
                        Some(&target.wrapper_node_id)
                    );
                    count += 1;
                }
                SourceBookmarkResolution::Missing | SourceBookmarkResolution::Ambiguous => {
                    assert!(reference.target_node_id.is_none())
                }
            }
        }
    }
    assert_eq!(meanings.receipt().bound_bookmark_edges, count);
    assert_eq!(
        meanings.receipt().profile,
        "hwpx-agent.document-import-field-semantics/partial-v3"
    );
    let index = SourceFieldMeaningIndex::import(&fields, limits()?)?;
    assert_eq!(index.observations(), meanings.observations());
    assert_eq!(index.receipt().additional_document_graph_clones, 0);
    assert!(
        !index
            .receipt()
            .complete_reference_state_or_external_approval
    );
    let fresh = forms.reconstruct_source_for_verification(bytes)?;
    assert_eq!(meanings.verify_reconstruction(&fresh)?, *meanings.receipt());
    assert_eq!(fields.graph().canonical_sha256()?, before);
    exact_delta(&fields, &meanings)?;
    Ok(count)
}
#[test]
fn all_eight_command_options_create_edges_only_to_original_bookmark_wrappers() -> TestResult {
    for display in 0..4 {
        for hyperlink in [false, true] {
            let bytes = package(&format!(
                "{}{}",
                fixture::marker("private-target"),
                field(1, "private-target", display, hyperlink)
            ))?;
            assert_eq!(check_edges(&bytes, "bookmark-edges")?, 1);
        }
    }
    Ok(())
}
#[test]
fn missing_and_ambiguous_bookmarks_never_create_a_first_match_edge() -> TestResult {
    for markers in [
        String::new(),
        format!(
            "{}{}",
            fixture::marker("private-target"),
            fixture::marker("private-target")
        ),
    ] {
        let bytes = package(&format!(
            "{markers}{}",
            field(1, "private-target", 0, false)
        ))?;
        assert_eq!(check_edges(&bytes, "bookmark-edges")?, 0);
    }
    Ok(())
}
#[test]
fn repeated_field_edges_keep_all_bookmark_and_unrelated_reference_state() -> TestResult {
    let mut body = fixture::marker("private-target");
    for id in 1..=8 {
        body.push_str(&field(id, "private-target", (id % 4) as u8, id % 2 == 0));
    }
    let duplicate = package(&format!("{body}{}", fixture::field()))?;
    assert!(base::forms(&duplicate, "bookmark-edges").is_err());
    // Keep the original duplicate-ID admission rejection, then verify the
    // graph delta for a valid unrelated DATE field with its own native ID.
    body.push_str(
        &fixture::field()
            .replace("id='7'", "id='9'")
            .replace("beginIDRef='7'", "beginIDRef='9'"),
    );
    let bytes = package(&body)?;
    assert_eq!(check_edges(&bytes, "bookmark-edges")?, 8);
    Ok(())
}
#[test]
fn note_and_table_owned_crossrefs_keep_exact_original_target_node_identity() -> TestResult {
    for body in [
        fixture::note(&format!(
            "{}{}",
            fixture::marker("private-target"),
            field(1, "private-target", 0, false)
        )),
        fixture::table(&format!(
            "{}{}",
            fixture::marker("private-target"),
            field(1, "private-target", 0, false)
        )),
    ] {
        assert_eq!(check_edges(&package(&body)?, "bookmark-edges")?, 1);
    }
    Ok(())
}
#[test]
fn source_and_target_drift_and_separate_originals_cannot_rebind_a_retained_edge() -> TestResult {
    let bytes = source()?;
    let forms = base::forms(&bytes, "bookmark-edges")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    let foreign = base::forms(&bytes, "bookmark-edges")?;
    assert!(
        meaning
            .verify_reconstruction(&foreign.reconstruct_source_for_verification(&bytes)?)
            .is_err()
    );
    let changed = package(&format!(
        "{}{}",
        fixture::marker("other-target"),
        field(1, "private-target", 0, false)
    ))?;
    assert!(meaning.verify_source(&changed).is_err());
    let foreign = base::forms(&bytes, "different-document")?;
    let ranges = ImportedDocumentFields::import(&foreign)?;
    let other = ImportedDocumentFieldSemantics::import(&ranges)?;
    assert_ne!(
        meaning.graph().canonical_sha256()?,
        other.graph().canonical_sha256()?
    );
    Ok(())
}
#[test]
fn resolved_source_edges_do_not_evaluate_native_display_or_cached_text() -> TestResult {
    let bytes = source()?;
    let forms = base::forms(&bytes, "bookmark-edges")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    let evaluated = ImportedSourceFormulaEvaluation::import(&meaning)?;
    assert!(evaluated.values().is_empty());
    assert_eq!(evaluated.receipt().non_formula_meanings_not_evaluated, 1);
    exact_delta(&fields, &meaning)?;
    assert!(matches!(
        FullDocumentFormContext::bind(
            meaning.graph(),
            meaning.graph().canonical_sha256()?,
            Sha256::digest(&bytes).into(),
            RevisionId::parse("bookmark-edges")?
        ),
        Err(FullDocumentFormError::Projection)
    ));
    Ok(())
}
#[test]
fn historical_current_future_and_malformed_partial_markers_cannot_grant_full_context() -> TestResult
{
    let bytes = package("<hp:t>plain</hp:t>")?;
    let forms = base::forms(&bytes, "bookmark-edges")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let meaning = ImportedDocumentFieldSemantics::import(&fields)?;
    let mut clean = meaning.graph().clone().into_draft();
    clean.source_profile = None;
    clean.metadata = Properties::new();
    let clean_graph = DocumentGraph::from_draft(clean.clone(), DocumentGraphLimits::default())?;
    assert!(
        FullDocumentFormContext::bind(
            &clean_graph,
            clean_graph.canonical_sha256()?,
            Sha256::digest(&bytes).into(),
            RevisionId::parse("bookmark-edges")?
        )
        .is_ok()
    );
    let values=[("field_semantics_import_profile",PropertyValue::Text("hwpx-agent.document-import-field-semantics/partial-v1".into())),
        ("field_semantics_import_profile",PropertyValue::Text("hwpx-agent.document-import-field-semantics/partial-v2".into())),
        ("field_semantics_import_profile",PropertyValue::Text(FIELD_SEMANTICS_PROFILE.into())),
        ("field_semantics_import_profile",PropertyValue::Text("hwpx-agent.document-import-field-semantics/partial-v999".into())),
        ("field_semantics_import_scope",PropertyValue::Text("source_https_target_and_table_formula_ast_not_approval_evaluation_full_import_or_execution".into())),
        ("field_semantics_import_scope",PropertyValue::Text("source_https_target_table_formula_ast_and_bookmark_crossref_not_native_approval_evaluation_full_import_or_execution".into())),
        ("field_semantics_import_scope",PropertyValue::Text(FIELD_SEMANTICS_SCOPE.into())),
        ("field_semantics_import_scope",PropertyValue::Integer(0))];
    for (key, value) in values {
        let mut partial = clean.clone();
        partial.metadata.insert(key, value);
        let graph = DocumentGraph::from_draft(partial, DocumentGraphLimits::default())?;
        assert!(matches!(
            FullDocumentFormContext::bind(
                &graph,
                graph.canonical_sha256()?,
                Sha256::digest(&bytes).into(),
                RevisionId::parse("bookmark-edges")?
            ),
            Err(FullDocumentFormError::Projection)
        ));
    }
    Ok(())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>, Box<dyn Error>> {
    let name = pin["path"].as_str().ok_or("path")?;
    if !name.starts_with("implementation/p09/evidence/private/")
        || name.contains('\\')
        || name.split('/').any(|v| v == ".." || v.is_empty())
    {
        return Err("path rejected".into());
    }
    let root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("root")?;
    let path = root.join(name);
    for ancestor in path.ancestors().collect::<Vec<_>>().into_iter().rev() {
        let m = ancestor.symlink_metadata()?;
        if m.file_type().is_symlink() {
            return Err("symlink".into());
        }
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt as _;
            if m.file_attributes() & 0x400 != 0 {
                return Err("reparse".into());
            }
        }
    }
    let size = pin["bytes"].as_u64().ok_or("size")?;
    if size == 0 || size > 4194304 || !path.is_file() || path.metadata()?.len() != size {
        return Err("read budget".into());
    }
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file = options.open(path)?;
    let mut bytes = Vec::new();
    let mut chunk = [0; 65536];
    let clock = Instant::now();
    loop {
        let n = file.read(&mut chunk)?;
        if n == 0 {
            break;
        }
        if bytes.len() + n > 4194304 {
            return Err("read budget".into());
        }
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&chunk[..n]);
        if let Some(delay) =
            Duration::from_secs_f64(bytes.len() as f64 / 2097152.).checked_sub(clock.elapsed())
        {
            std::thread::sleep(delay);
        }
    }
    assert_eq!(bytes.len() as u64, size);
    assert_eq!(hex::encode(Sha256::digest(&bytes)), pin["sha256"]);
    Ok(bytes)
}
#[test]
fn actual010_all_twenty_four_outputs_have_expected_same_source_edges_and_unchanged_cache()
-> TestResult {
    assert_eq!(
        hex::encode(Sha256::digest(CORPUS.as_bytes())),
        "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f"
    );
    let corpus: Value = serde_json::from_str(CORPUS)?;
    let mut count = 0;
    for case in corpus["cases"].as_array().ok_or("cases")? {
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let bytes = read_pin(pin)?;
            assert_eq!(
                check_edges(&bytes, "bookmark-edges")?,
                usize::from(stage != "opened")
            );
            assert_eq!(read_pin(pin)?, bytes);
            count += 1;
        }
    }
    assert_eq!(count, 24);
    Ok(())
}
#[allow(dead_code, unused_imports)]
mod stored {
    use super::*;
    include!("support/stored_source_fixture.rs");
    #[test]
    fn authenticated_stored_graph_has_same_edges_and_two_fresh_reads_without_a_head_write()
    -> TestResult {
        let bytes = source()?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let ranges = source.import_field_ranges(&provider, 5)?;
        let meaning = ranges.import_semantics(&provider, 6)?;
        let forms = base::forms(&bytes, "actual-form-document")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let direct = ImportedDocumentFieldSemantics::import(&fields)?;
        assert_eq!(meaning.graph(), direct.graph());
        assert_eq!(meaning.receipt().semantics.bound_bookmark_edges, 1);
        assert_eq!(meaning.receipt().semantics, *direct.receipt());
        let before = stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.download")
            .count();
        assert_eq!(meaning.verify(&provider, 7)?, *meaning.receipt());
        let after = stored
            .metadata
            .audit_events()?
            .iter()
            .filter(|v| v.event == "artifact.download")
            .count();
        assert_eq!(after, before + 2);
        assert_eq!(
            stored
                .revisions
                .head(&stored.revision_context, stored.project, stored.branch)?,
            stored.head
        );
        Ok(())
    }
    #[test]
    fn cached_stored_edge_cannot_bypass_acl_revocation() -> TestResult {
        let stored = StoredFixture::new(&source()?, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let ranges = source.import_field_ranges(&provider, 5)?;
        let meaning = ranges.import_semantics(&provider, 6)?;
        stored.artifacts.set_permissions(
            &stored.owner,
            stored.result,
            stored.reader.subject(),
            BTreeSet::new(),
            7,
        )?;
        assert!(meaning.verify(&provider, 8).is_err());
        assert!(ranges.import_semantics(&provider, 8).is_err());
        Ok(())
    }
    #[test]
    fn cached_stored_edge_cannot_bypass_aead_tamper_or_unverified_scan() -> TestResult {
        let bytes = source()?;
        let stored = StoredFixture::new(&bytes, ArtifactKind::Result, false)?;
        let provider = stored.provider()?;
        let source = provider.import_actual_forms(stored.head, 4)?;
        let ranges = source.import_field_ranges(&provider, 5)?;
        let meaning = ranges.import_semantics(&provider, 6)?;
        stored.blobs.tamper.store(true, Ordering::SeqCst);
        assert!(meaning.verify(&provider, 7).is_err());
        assert!(ranges.import_semantics(&provider, 7).is_err());
        let unverified = StoredFixture::new(&bytes, ArtifactKind::Result, true)?;
        assert!(
            unverified
                .provider()?
                .import_actual_forms(unverified.head, 4)
                .is_err()
        );
        Ok(())
    }
}
