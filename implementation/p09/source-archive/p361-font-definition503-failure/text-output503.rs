//! The original preserving build pipeline with explicit text-style/v9, not a relaxed shape profile.
use super::*;
use crate::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageGraphLimits,PreservationRuleProfile,PreservingPatchEngine,PreservingWriter};
use std::io::Cursor;
pub(in crate::document_import::search::replacement::atoms) fn build<T>(source:&ImportedSourcePackage,fresh:&[u8],intents:&[PatchIntent],plans:&BTreeMap<&PackagePath,T>,writer:WriterLimits)->Result<PackageArtifact,E> {
    let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),
        IdRuleProfile::hwpml_2011_text_style_v9(),IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,intents)
        .map_err(|e|E::Patch(e.code()))?;
    if patch.changed_parts()!=plans.len()||patch.added_parts()!=0||patch.parts().iter().any(|p|!plans.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}
    let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
    Ok(artifact)
}
