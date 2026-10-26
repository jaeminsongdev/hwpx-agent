//! Atomic point/block target rename plus all admitted same-document CROSSREF links.
//! Cached results are preserved and affected fields marked dirty; no refresh or Native grant.
use super::*;
use super::super::{cached_source::SourceFieldCachedInlines,bookmark_crossref::{SourceBookmarkCrossReferenceBindings,SourceBookmarkResolution,BookmarkCrossReferenceDisplay}};
use crate::{BoundedZipReader,IdIndexLimits,IdRuleProfile,PackageArtifact,PackageGraphLimits,PackagePath,PatchIntent,PatchLimits,PatchText,
    PatchAttributeValue,PreservationRuleProfile,PreservingPatchEngine,PreservingWriter,WriterLimits,WriterError,XmlAttributeSelector,XmlElementSelector,
    XmlElementToken,PreservingXmlDocument};
use crate::document_import::{ImportedSourcePackage,forms::{ImportedDocumentForms,VerifiedFormReconstruction}};
use std::io::Cursor;
const HP:&str=crate::HANCOM_2020_PARAGRAPH_NAMESPACE;
#[derive(Clone,Copy,Debug,Eq,PartialEq,Error)]
pub enum BookmarkRenameError{
    #[error("BOOKMARK_RENAME_SOURCE_REJECTED")]Source,
    #[error("BOOKMARK_RENAME_TARGET_REJECTED")]Target,
    #[error("BOOKMARK_RENAME_NAME_REJECTED")]Name,
    #[error("BOOKMARK_RENAME_COLLISION_REJECTED")]Collision,
    #[error("BOOKMARK_RENAME_NO_CHANGE")]NoChange,
    #[error("BOOKMARK_RENAME_UNSUPPORTED_REFERENCE_FAMILY")]Unsupported,
    #[error("BOOKMARK_RENAME_PARAMETER_PROFILE_REJECTED")]Parameters,
    #[error("BOOKMARK_RENAME_PROTECTION_REJECTED")]Protection,
    #[error("BOOKMARK_RENAME_LIMIT")]Limit,
    #[error("BOOKMARK_RENAME_PATCH_REJECTED")]Patch,
    #[error("BOOKMARK_RENAME_READBACK_REJECTED")]Readback,
    #[error("BOOKMARK_RENAME_PRESERVATION_REJECTED")]Preservation,
}
type E=BookmarkRenameError;
pub struct BookmarkRenameRequest<'a>{pub target_id:&'a LogicalId,pub expected_name_sha256:[u8;32],pub new_name:&'a str}
impl fmt::Debug for BookmarkRenameRequest<'_>{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("BookmarkRenameRequest(<redacted>)")}}
#[derive(Clone,Debug,Eq,PartialEq,Serialize)]
pub struct BookmarkRenameReceipt{
    pub profile:&'static str,pub source_package_sha256:[u8;32],pub output_package_sha256:[u8;32],pub output_bytes:usize,
    pub old_name_sha256:[u8;32],pub new_name_sha256:[u8;32],pub family:SourceBookmarkFamily,pub changed_crossrefs:usize,pub changed_parts:usize,
    pub target_and_all_admitted_refs_rebound:bool,pub command_and_refpath_synchronized:bool,pub affected_fields_marked_dirty:bool,
    pub cache_bytes_preserved_not_refreshed:bool,pub outside_selected_values_exact:bool,
    pub native_refresh_or_execution_publication_revision_authority:bool,
}
pub struct SourceBookmarkRenameCandidate{artifact:PackageArtifact,receipt:BookmarkRenameReceipt}
impl fmt::Debug for SourceBookmarkRenameCandidate{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceBookmarkRenameCandidate(<redacted>; no_execution_authority)")}}
impl SourceBookmarkRenameCandidate{
    #[must_use]pub const fn receipt(&self)->&BookmarkRenameReceipt{&self.receipt}
    /// # Errors
    /// Artifact integrity only. Current service/Native/publication authority is still required by a host.
    pub fn with_verified_bytes<T>(&self,consume:impl FnOnce(&[u8])->T)->Result<T,WriterError>{self.artifact.with_verified_bytes(consume)}
}
#[derive(Clone,Copy)]enum ValueSlot{Attribute(usize),Leaf}
struct Edit{element:usize,slot:ValueSlot,value:String}
fn attribute(node:&XmlElementToken,name:&str)->Result<usize,E>{
    node.attributes().iter().position(|a|a.name().namespace().is_none()&&a.name().local_name()==name).ok_or(E::Parameters)
}
fn add_attr(path:&PackagePath,xml:&PreservingXmlDocument,element:usize,name:&str,value:&str,intents:&mut Vec<PatchIntent>,plans:&mut BTreeMap<PackagePath,Vec<Edit>>)->Result<(),E>{
    let a=attribute(xml.elements().get(element).ok_or(E::Source)?,name)?;
    intents.push(PatchIntent::ReplaceAttribute{target:XmlAttributeSelector::bind(path,xml,element,a).map_err(|_|E::Patch)?,
        value:PatchAttributeValue::Text(PatchText::new(value).map_err(|_|E::Name)?)});
    plans.entry(path.clone()).or_default().push(Edit{element,slot:ValueSlot::Attribute(a),value:value.to_owned()});Ok(())
}
fn leaf(xml:&PreservingXmlDocument,parameter:usize,name:&str,expected:&str)->Result<usize,E>{
    let mut found=None;let mut at=xml.elements().get(parameter).ok_or(E::Source)?.first_child();
    while let Some(i)=at{let n=&xml.elements()[i];at=n.next_sibling();
        if n.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()=="name"&&a.semantic_value()==name){
            if found.is_some()||n.name().namespace()!=Some(HP)||n.name().local_name()!="stringParam"||n.first_child().is_some(){return Err(E::Parameters);}
            let text=xml.source_text(n.content_span().ok_or(E::Parameters)?).map_err(|_|E::Source)?;
            if quick_xml::escape::unescape(text).map_err(|_|E::Parameters)?.as_ref()!=expected{return Err(E::Parameters);}found=Some(i);
        }
    }found.ok_or(E::Parameters)
}
fn add_leaf(path:&PackagePath,xml:&PreservingXmlDocument,element:usize,value:&str,intents:&mut Vec<PatchIntent>,plans:&mut BTreeMap<PackagePath,Vec<Edit>>)->Result<(),E>{
    intents.push(PatchIntent::ReplaceLeafText{target:XmlElementSelector::bind(path,xml,element).map_err(|_|E::Patch)?,value:PatchText::new(value).map_err(|_|E::Limit)?});
    plans.entry(path.clone()).or_default().push(Edit{element,slot:ValueSlot::Leaf,value:value.to_owned()});Ok(())
}
fn sdk(display:BookmarkCrossReferenceDisplay)->SdkCrossReferenceDisplay{match display{
    BookmarkCrossReferenceDisplay::Page=>SdkCrossReferenceDisplay::Page,BookmarkCrossReferenceDisplay::BookmarkName=>SdkCrossReferenceDisplay::BookmarkName,
    BookmarkCrossReferenceDisplay::Content=>SdkCrossReferenceDisplay::Content,BookmarkCrossReferenceDisplay::RelativePosition=>SdkCrossReferenceDisplay::RelativePosition}}
fn command(name:&str,display:SdkCrossReferenceDisplay,link:bool)->Result<SdkCrossReferenceCandidate,E>{
    SdkCrossReferenceCandidate::build(SdkCrossReferenceTarget::Bookmark{exact_source_name:name},display,link).map_err(|_|E::Name)
}
impl SourceBookmarkAuthoringContext<'_>{
    /// # Errors
    /// One fresh original proof, exact target/name and global observed protection checks.
    /// Only the admitted point/block + bookmark CROSSREF field profile is supported.
    pub fn rename_target_and_crossrefs(&self,proof:&VerifiedFormReconstruction<'_>,request:BookmarkRenameRequest<'_>,writer:WriterLimits)
        ->Result<SourceBookmarkRenameCandidate,E>{
        let rebuilt=proof.for_original(self.fields.forms).map_err(|_|E::Source)?;let source=self.fields.forms.source();let fresh=rebuilt.source().original.as_ref();
        source.observe_protection_signals().map_err(|_|E::Protection)?.require_no_observed_document_signals().map_err(|_|E::Protection)?;
        if self.fields.fields().iter().any(|f|!matches!(f.native_kind.as_str(),"BOOKMARK"|"CROSSREF")){return Err(E::Unsupported);}
        self.prepare(request.target_id,SdkCrossReferenceDisplay::BookmarkName,false).map_err(|_|E::Target)?;
        let(name,anchor,family)=if let Some(i)=self.block_ids.get(request.target_id){let b=&self.blocks.as_ref().ok_or(E::Target)?.observations()[*i];
            (b.name(),b.begin_anchor().clone(),SourceBookmarkFamily::Block)
        }else{let b=self.fields.forms.body_structure().bookmarks().iter().find(|b|&b.reference_id==request.target_id).ok_or(E::Target)?;
            (b.name.as_str(),b.source_anchor.clone(),SourceBookmarkFamily::Point)};
        let old_sha:[u8;32]=Sha256::digest(name.as_bytes()).into();if old_sha!=request.expected_name_sha256{return Err(E::Target);}
        if request.new_name==name{return Err(E::NoChange);}
        if request.new_name.len()>self.limits.config().text_bytes{return Err(E::Limit);}
        command(request.new_name,SdkCrossReferenceDisplay::BookmarkName,false)?;
        if self.point_names.contains(request.new_name)||self.blocks.as_ref().is_some_and(|b|b.observations().iter().any(|v|v.name()==request.new_name)){return Err(E::Collision);}
        let mut work=0usize;
        for part in source.parts(){if let Some(xml)=part.xml(){work=work.checked_add(xml.elements().len()).filter(|n|*n<=1_000_000).ok_or(E::Limit)?;
            let flags=crate::document_import::search::replacement::atoms::unicode::plan::guard(xml).map_err(|_|E::Protection)?;
            if flags.iter().any(|v|*v)||xml.elements().iter().any(|n|n.name().namespace()==Some(HP)&&matches!(n.name().local_name(),"insertBegin"|"insertEnd"|"deleteBegin"|"deleteEnd")){return Err(E::Protection);}
        }}
        let bindings=SourceBookmarkCrossReferenceBindings::import(self.fields,self.limits).map_err(|_|E::Unsupported)?;
        let caches=SourceFieldCachedInlines::import(self.fields,self.limits).map_err(|_|E::Source)?;
        let new_sha:[u8;32]=Sha256::digest(request.new_name.as_bytes()).into();let mut intents=Vec::new();let mut plans=BTreeMap::new();let mut expected=BTreeMap::new();
        let mut replacement_bytes=request.new_name.len();if replacement_bytes>self.limits.config().input_bytes{return Err(E::Limit);}
        let selected=source.resolve_anchor(&anchor).map_err(|_|E::Target)?;let target_index=selected.element_index().ok_or(E::Target)?;
        let target_path=selected.part().path().clone();
        add_attr(&target_path,selected.part().xml().ok_or(E::Target)?,target_index,"name",request.new_name,&mut intents,&mut plans)?;
        for (ordinal,binding)in bindings.bindings().iter().enumerate(){
            let selected=matches!(&binding.target,SourceBookmarkResolution::Bound{logical_target_id,..}if logical_target_id==request.target_id);
            if !selected{if binding.exact_target_name_sha256==new_sha{return Err(E::Collision);}continue;}
            let old=command(name,sdk(binding.display),binding.hyperlink)?;let new=command(request.new_name,sdk(binding.display),binding.hyperlink)?;
            if <[u8;32]>::from(Sha256::digest(old.command_for_discovery().as_bytes()))!=binding.command_sha256{return Err(E::Parameters);}
            let range=self.fields.fields().iter().find(|f|f.reference_id==binding.field_reference_id).ok_or(E::Source)?;
            let begin=source.resolve_anchor(&range.begin_anchor).map_err(|_|E::Source)?;
            let parameter=source.resolve_anchor(range.parameter_anchor.as_ref().ok_or(E::Parameters)?).map_err(|_|E::Source)?;
            if begin.part().path()!=parameter.part().path(){return Err(E::Source);}
            let xml=begin.part().xml().ok_or(E::Source)?;let start=begin.element_index().ok_or(E::Source)?;let p=parameter.element_index().ok_or(E::Source)?;
            if xml.elements()[p].parent()!=Some(start){return Err(E::Parameters);}
            let oldpath=format!("{};",old.command_for_discovery().split_once(';').ok_or(E::Parameters)?.0);
            let newpath=format!("{};",new.command_for_discovery().split_once(';').ok_or(E::Parameters)?.0);
            replacement_bytes=replacement_bytes.checked_add(new.command_for_discovery().len()).and_then(|n|n.checked_add(newpath.len())).and_then(|n|n.checked_add(1))
                .filter(|n|*n<=self.limits.config().input_bytes).ok_or(E::Limit)?;
            let c=leaf(xml,p,"Command",old.command_for_discovery())?;let r=leaf(xml,p,"RefPath",&oldpath)?;
            add_attr(begin.part().path(),xml,start,"dirty","1",&mut intents,&mut plans)?;
            add_leaf(begin.part().path(),xml,c,new.command_for_discovery(),&mut intents,&mut plans)?;
            add_leaf(begin.part().path(),xml,r,&newpath,&mut intents,&mut plans)?;
            expected.insert(ordinal,<[u8;32]>::from(Sha256::digest(new.command_for_discovery().as_bytes())));
            if intents.len()>PatchLimits::default().config().max_intents||intents.len().checked_mul(std::mem::size_of::<PatchIntent>()).is_none_or(|n|n>self.limits.config().output_bytes){return Err(E::Limit);}
        }
        for edits in plans.values_mut(){edits.sort_by_key(|e|{let key=match e.slot{ValueSlot::Attribute(a)=>a,ValueSlot::Leaf=>usize::MAX};(e.element,key)});}
        let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;
        let profile=if self.blocks.is_some(){IdRuleProfile::hancom_2020_block_bookmark_v12()}else{crate::document_import::search::replacement::font_profile::select(source,IdRuleProfile::hwpml_2011_shape_v6())};
        let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),profile,IdIndexLimits::default(),PatchLimits::default(),
            PreservationRuleProfile::Hangul2020PreviewTextV2,&intents).map_err(|_|E::Patch)?;
        if patch.added_parts()!=0||patch.changed_parts()!=plans.len()||patch.parts().iter().any(|p|!plans.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}
        let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Patch)?;
        artifact.with_verified_bytes(|bytes|->Result<(),E>{
            let output=ImportedSourcePackage::import(bytes,source.document_id().clone(),Sha256::digest(bytes).into(),source.limits).map_err(|_|E::Readback)?;
            let forms=ImportedDocumentForms::import(output).map_err(|_|E::Readback)?;let fields=ImportedDocumentFields::import(&forms).map_err(|_|E::Readback)?;
            let current=SourceBookmarkAuthoringContext::import(&fields,self.limits).map_err(|_|E::Readback)?;
            let new_target=match family{SourceBookmarkFamily::Block=>current.blocks.as_ref().ok_or(E::Readback)?.by_exact_source_name(request.new_name).map_err(|_|E::Readback)?.field_reference_id().clone(),
                SourceBookmarkFamily::Point=>current.point_ids.iter().find(|(_,n)|**n==request.new_name).map(|(id,_)|(**id).clone()).ok_or(E::Readback)?};
            current.prepare(&new_target,SdkCrossReferenceDisplay::BookmarkName,false).map_err(|_|E::Readback)?;
            let new_anchor=if family==SourceBookmarkFamily::Block{current.blocks.as_ref().ok_or(E::Readback)?.by_exact_source_name(request.new_name).map_err(|_|E::Readback)?.begin_anchor().clone()}
                else{forms.body_structure().bookmarks().iter().find(|b|b.reference_id==new_target).ok_or(E::Readback)?.source_anchor.clone()};
            let resolved=forms.source().resolve_anchor(&new_anchor).map_err(|_|E::Readback)?;
            if resolved.part().path()!=&target_path||resolved.element_index()!=Some(target_index){return Err(E::Readback);}
            let newbindings=SourceBookmarkCrossReferenceBindings::import(&fields,self.limits).map_err(|_|E::Readback)?;
            let newcache=SourceFieldCachedInlines::import(&fields,self.limits).map_err(|_|E::Readback)?;
            if fields.fields().len()!=self.fields.fields().len()||newbindings.bindings().len()!=bindings.bindings().len()||caches.observations().len()!=newcache.observations().len(){return Err(E::Readback);}
            for(a,b)in self.fields.fields().iter().zip(fields.fields()){if a.native_kind!=b.native_kind||a.native_begin_id!=b.native_begin_id||a.inline_start!=b.inline_start||a.inline_end!=b.inline_end{return Err(E::Readback);}}
            for(a,b)in caches.observations().iter().zip(newcache.observations()){if a.cache!=b.cache{return Err(E::Preservation);}}
            for(i,(a,b))in bindings.bindings().iter().zip(newbindings.bindings()).enumerate(){
                if a.display!=b.display||a.hyperlink!=b.hyperlink||b.command_sha256!=expected.get(&i).copied().unwrap_or(a.command_sha256){return Err(E::Readback);}
                if expected.contains_key(&i)&&(!matches!(&b.target,SourceBookmarkResolution::Bound{logical_target_id,..}if logical_target_id==&new_target)||b.exact_target_name_sha256!=new_sha){return Err(E::Readback);}
                if !expected.contains_key(&i)&&(a.exact_target_name_sha256!=b.exact_target_name_sha256||std::mem::discriminant(&a.target)!=std::mem::discriminant(&b.target)){return Err(E::Readback);}
            }
            for(path,edits)in &plans{
                let old=source.parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                let new=forms.source().parts().iter().find(|p|p.path()==path).and_then(|p|p.xml()).ok_or(E::Readback)?;
                if old.elements().len()!=new.elements().len(){return Err(E::Readback);}let(mut before,mut after)=(0,0);
                for edit in edits{let a=&old.elements()[edit.element];let b=&new.elements()[edit.element];
                    let(x,y,value)=match edit.slot{ValueSlot::Attribute(i)=>{let l=a.attributes().get(i).ok_or(E::Readback)?;let r=b.attributes().get(i).ok_or(E::Readback)?;(l.value_span(),r.value_span(),r.semantic_value().to_owned())},
                        ValueSlot::Leaf=>{let l=a.content_span().ok_or(E::Readback)?;let r=b.content_span().ok_or(E::Readback)?;(l,r,quick_xml::escape::unescape(new.source_text(r).map_err(|_|E::Readback)?).map_err(|_|E::Readback)?.into_owned())}};
                    if x.start()<before||y.start()<after||value!=edit.value||!old.with_source_bytes(|l|new.with_source_bytes(|r|l.get(before..x.start())==r.get(after..y.start()))){return Err(E::Preservation);}before=x.end();after=y.end();
                }
                if !old.with_source_bytes(|l|new.with_source_bytes(|r|l.get(before..)==r.get(after..))){return Err(E::Preservation);}
            }Ok(())
        }).map_err(|_|E::Patch)??;
        let receipt=BookmarkRenameReceipt{profile:"hwpx-agent.atomic-bookmark-target-and-crossref-rename/v1",source_package_sha256:source.receipt().source_package_sha256,
            output_package_sha256:artifact.sha256(),output_bytes:artifact.size_bytes(),old_name_sha256:old_sha,new_name_sha256:new_sha,family,changed_crossrefs:expected.len(),changed_parts:plans.len(),
            target_and_all_admitted_refs_rebound:true,command_and_refpath_synchronized:true,affected_fields_marked_dirty:true,cache_bytes_preserved_not_refreshed:true,outside_selected_values_exact:true,
            native_refresh_or_execution_publication_revision_authority:false};
        if serde_json::to_vec(&receipt).map_err(|_|E::Limit)?.len()>self.limits.config().output_bytes{return Err(E::Limit);}Ok(SourceBookmarkRenameCandidate{artifact,receipt})
    }
}
