//! Independent exact original subtree and positional-gap readback after one full output admission.
use super::*;
pub(super) fn output(source:&ImportedSourcePackage,path:&PackagePath,old:&PreservingXmlDocument,spans:&[(usize,usize)],order:&[usize],
    artifact:&PackageArtifact,context:&review::ReviewWriteContext)->Result<(),E> {
    artifact.with_verified_bytes(|bytes|->Result<(),E>{
        let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
        let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;
        let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;context.readback(&forms,&fields)?;
        let new=forms.source().parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
        old.with_source_bytes(|raw|new.with_source_bytes(|out|->Result<(),E>{
            let(mut before,mut after)=(0usize,0usize);
            for(destination,&source)in order.iter().enumerate(){
                let(start,end)=spans[destination];let(a,b)=spans[source];let gap=start.checked_sub(before).ok_or(E::Readback)?;
                let next=after.checked_add(gap).ok_or(E::Limit)?;
                if raw.get(before..start)!=out.get(after..next){return Err(E::Preservation);}
                let stop=next.checked_add(b-a).ok_or(E::Limit)?;
                if raw.get(a..b)!=out.get(next..stop){return Err(E::Readback);}
                before=end;after=stop;
            }
            if raw.get(before..)!=out.get(after..){return Err(E::Preservation);}Ok(())
        }))
    }).map_err(|_|E::Writer)??;Ok(())
}
