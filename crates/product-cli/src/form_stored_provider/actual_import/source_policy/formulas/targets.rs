use super::{StoredFormulaPolicyError as Error, StoredImportedDocumentForms, wire::Payload};
use crate::form_stored_provider::StoredFormProvider;
use artifact_service::{
    ArtifactMetadataRepository, ArtifactScanner, ContentDigest, EncryptedBlobStore,
};
use hwpx_package::document_import::fields::semantics::ImportedFieldMeaning;
use revision_service::RevisionRepository;
use std::collections::{BTreeMap, BTreeSet};
pub(super) fn bind<R, B, S, V>(
    source: &StoredImportedDocumentForms,
    provider: &StoredFormProvider<'_, R, B, S, V>,
    payload: &Payload,
    now: u64,
) -> Result<(ContentDigest, ContentDigest, usize), Error>
where
    R: ArtifactMetadataRepository,
    B: EncryptedBlobStore,
    S: ArtifactScanner,
    V: RevisionRepository,
{
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
            .map_err(|_| Error::Target)?,
    ))
    .map_err(|_| Error::Target)?;
    if graph != payload.meaning_graph_sha256 {
        return Err(Error::Target);
    }
    let ranges: BTreeMap<_, _> = fields
        .fields()
        .iter()
        .map(|f| (&f.reference_id, f))
        .collect();
    let formulas: BTreeMap<_, _> = meanings
        .observations()
        .iter()
        .filter_map(|m| match &m.meaning {
            ImportedFieldMeaning::TableFormula { formula, .. } => Some((&m.reference_id, formula)),
            _ => None,
        })
        .collect();
    if formulas.len() != payload.targets.len() || ranges.len() != fields.fields().len() {
        return Err(Error::Target);
    }
    let mut seen = BTreeSet::new();
    let mut allowed = 0;
    for rule in &payload.targets {
        if !seen.insert(&rule.reference_id) {
            return Err(Error::Target);
        }
        let field = ranges.get(&rule.reference_id).ok_or(Error::Target)?;
        let formula = formulas.get(&rule.reference_id).ok_or(Error::Target)?;
        let ast = ContentDigest::of(&serde_json::to_vec(formula.ast()).map_err(|_| Error::Target)?);
        if rule.begin_anchor != field.begin_anchor
            || rule.end_anchor != field.end_anchor
            || rule.ast_sha256 != ast
        {
            return Err(Error::Target);
        }
        allowed += usize::from(rule.allow_recalculation);
    }
    let sorted: BTreeMap<_, _> = payload
        .targets
        .iter()
        .map(|r| (&r.reference_id, r))
        .collect();
    let binding = ContentDigest::of(&serde_json::to_vec(&sorted).map_err(|_| Error::Target)?);
    meanings.verify(provider, now).map_err(|_| Error::Source)?;
    Ok((graph, binding, allowed))
}
