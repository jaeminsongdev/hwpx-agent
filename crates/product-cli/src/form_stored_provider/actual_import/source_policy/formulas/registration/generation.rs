use super::super::{FORMULA_POLICY_SCHEMA, wire::Rule};
use super::{
    FormulaPolicyDecision, FormulaPolicyRegistrationError as Error, SourcePolicyBinding,
    StoredImportedDocumentForms,
};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use revision_service::RevisionRepository;
use std::collections::BTreeMap;

pub(super) fn generate<R, B, S, V>(
    source: &StoredImportedDocumentForms,
    provider: &StoredFormProvider<'_, R, B, S, V>,
    binding: &SourcePolicyBinding,
    decisions: &[FormulaPolicyDecision],
    now: u64,
) -> Result<Vec<u8>, Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
    if decisions.is_empty() || decisions.len() > 4096 {
        return Err(Error::Policy);
    }
    let mut explicit = BTreeMap::new();
    for d in decisions {
        if explicit
            .insert(&d.reference_id, d.allow_recalculation)
            .is_some()
        {
            return Err(Error::Policy);
        }
    }
    let fields = source
        .import_field_ranges(provider, now)
        .map_err(|_| Error::Source)?;
    let meanings = fields
        .import_semantics(provider, now)
        .map_err(|_| Error::Source)?;
    let graph = ContentDigest::parse(&hex::encode(
        meanings
            .graph()
            .canonical_sha256()
            .map_err(|_| Error::Policy)?,
    ))
    .map_err(|_| Error::Policy)?;
    let ranges: BTreeMap<_, _> = fields
        .fields()
        .iter()
        .map(|f| (&f.reference_id, f))
        .collect();
    if ranges.len() != fields.fields().len() {
        return Err(Error::Policy);
    }
    let mut rules = BTreeMap::new();
    for meaning in meanings.observations() {
        if let ImportedFieldMeaning::TableFormula { formula, .. } = &meaning.meaning {
            let field = ranges.get(&meaning.reference_id).ok_or(Error::Policy)?;
            let allow = explicit.get(&meaning.reference_id).ok_or(Error::Policy)?;
            let rule = Rule {
                reference_id: field.reference_id.clone(),
                begin_anchor: field.begin_anchor.clone(),
                end_anchor: field.end_anchor.clone(),
                ast_sha256: ContentDigest::of(
                    &serde_json::to_vec(formula.ast()).map_err(|_| Error::Policy)?,
                ),
                allow_recalculation: *allow,
            };
            if rules.insert(&meaning.reference_id, rule).is_some() {
                return Err(Error::Policy);
            }
        }
    }
    if rules.len() != explicit.len() || rules.is_empty() {
        return Err(Error::Policy);
    }
    meanings.verify(provider, now).map_err(|_| Error::Source)?;
    serde_json::to_vec(
        &serde_json::json!({"schema_version": FORMULA_POLICY_SCHEMA, "binding": binding,
        "meaning_graph_sha256": graph, "targets": rules.into_values().collect::<Vec<_>>() }),
    )
    .map_err(|_| Error::Payload)
}
