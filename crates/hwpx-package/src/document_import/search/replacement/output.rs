use super::*;
use crate::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageGraphLimits,PreservationRuleProfile,PreservingPatchEngine,PreservingWriter};
use crate::document_import::ImportedSourcePackage;
use std::io::Cursor;
pub(super) fn build(source:&ImportedSourcePackage,fresh:&[u8],intents:&[PatchIntent],plans:&BTreeMap<&PackagePath,Vec<PlannedLeaf>>,writer:WriterLimits)->Result<PackageArtifact,E> {
    let artifact=build_artifact(source,fresh,intents,plans,writer)?;
    artifact.with_verified_bytes(|bytes|->Result<(),E>{
        let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let rebuilt=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
        let _=ImportedDocumentFields::import(&rebuilt).map_err(|_|E::Readback)?;
        for (path,leaves) in plans {
            let old=source.parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            let new=rebuilt.source().parts().iter().find(|p|p.path()==*path).and_then(|p|p.xml()).ok_or(E::Readback)?;
            if old.elements().len()!=new.elements().len(){return Err(E::Readback);}
            let mut ordered:Vec<_>=leaves.iter().collect();ordered.sort_by_key(|p|p.element);let(mut before,mut after)=(0,0);
            for plan in ordered {
                let value=plain_leaf(new,plan.element).map_err(|_|E::Readback)?;
                if value!=plan.expected||<[u8;32]>::from(Sha256::digest(value.as_bytes()))!=plan.change.output_text_sha256{return Err(E::Readback);}
                let a=old.elements()[plan.element].content_span().ok_or(E::Readback)?;let b=new.elements()[plan.element].content_span().ok_or(E::Readback)?;
                if !old.with_source_bytes(|old|new.with_source_bytes(|new|old.get(before..a.start())==new.get(after..b.start()))){return Err(E::Preservation);}
                before=a.end();after=b.end();
            }
            if !old.with_source_bytes(|old|new.with_source_bytes(|new|old.get(before..)==new.get(after..))){return Err(E::Preservation);}
        }Ok(())
    }).map_err(|_|E::Writer)??;Ok(artifact)
}
pub(super) fn build_artifact<T>(source:&ImportedSourcePackage,fresh:&[u8],intents:&[PatchIntent],plans:&BTreeMap<&PackagePath,T>,writer:WriterLimits)->Result<PackageArtifact,E> {
    let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),
        super::font_profile::select(source,IdRuleProfile::hwpml_2011_shape_v6()),IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,intents)
        .map_err(|e|E::Patch(e.code()))?;
    if patch.changed_parts()!=plans.len()||patch.added_parts()!=0||patch.parts().iter().any(|p|!plans.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}
    let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;
    Ok(artifact)
}
