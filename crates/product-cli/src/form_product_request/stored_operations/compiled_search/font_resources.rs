//! Font header effects are shared resources, never fake body nodes or separately repeated edits.
use super::*;
use hwpx_package::document_import::search::replacement::atoms::styles::fonts::{SourceFontReplacementReceipt,SourceFontStyleAxis,
    inventory::{SourceFontEdit,SourceFontEditKind as Kind,FONT_EDIT_INVENTORY_PROFILE}};
pub(super) struct HeaderResources<'a>{count:&'a SourceFontEdit,append:&'a SourceFontEdit}
const RESOURCE_PROFILE:&str="exact_header_effects_once_per_inventory_with_actual_body_owner/v1";
impl HeaderResources<'_>{
    pub(super) fn arguments(&self)->Result<[(&'static str,String);3],CompiledSearchError>{
        // Validate before allocating serialized strings. Shared once per compile, not once per match.
        bounded_hash(self.count,2048)?;bounded_hash(self.append,2048)?;
        Ok([("source_font_header_count_effect_json",serde_json::to_string(self.count).map_err(|_|CompiledSearchError::Compilation)?),
            ("source_font_header_append_effect_json",serde_json::to_string(self.append).map_err(|_|CompiledSearchError::Compilation)?),
            ("source_font_resource_binding_profile",RESOURCE_PROFILE.to_owned())])
    }
}
pub(super) fn project<'a>(candidate:&'a PreparedStoredSearchMutation,receipt:&SourceFontReplacementReceipt)->Result<projection::Projection<'a>,CompiledSearchError>{
    let inventory=candidate.font_inventory().ok_or(CompiledSearchError::Binding)?;let view=candidate.compiler_view();let source=view.source.imported().source();
    if inventory.profile()!=FONT_EDIT_INVENTORY_PROFILE||inventory.source_package_sha256()!=receipt.names.source_package_sha256
        ||inventory.output_package_sha256()!=receipt.output_package_sha256||inventory.axis()!=receipt.axis
        ||inventory.compiled_edits_sha256()!=receipt.compiled_edits_sha256||inventory.legacy_receipt_sha256()!=bounded_hash(receipt,MAX_METADATA_BYTES)?
        ||inventory.canonical_sha256()!=bounded_hash(inventory,MAX_METADATA_BYTES)?{return Err(CompiledSearchError::Binding);}
    let headers:Vec<_>=inventory.header_effects().collect();let [count,append]=headers.as_slice()else{return Err(CompiledSearchError::Binding)};let(count,append)=(*count,*append);
    let Kind::CharacterPropertyCount{attribute_index,original_items,output_items}=count.kind()else{return Err(CompiledSearchError::Binding)};
    if append.kind()!=(Kind::AppendCharacterProperties{appended_items:receipt.cloned_character_properties})
        ||output_items.checked_sub(original_items)!=Some(receipt.cloned_character_properties)
        ||count.replacement_sha256()!=<[u8;32]>::from(Sha256::digest(output_items.to_string().as_bytes())){return Err(CompiledSearchError::Binding);}
    let at=source.resolve_anchor(count.source_anchor()).map_err(|_|CompiledSearchError::Target)?;let item=source.resolve_anchor(append.source_anchor()).map_err(|_|CompiledSearchError::Target)?;
    if at.part().path().as_str()!="Contents/header.xml"||item.part().path()!=at.part().path()||count.source_part_path()!=at.part().path().as_str()
        ||append.source_part_path()!=at.part().path().as_str(){return Err(CompiledSearchError::Target);}
    let container=at.element().ok_or(CompiledSearchError::Target)?;let last=item.element().ok_or(CompiledSearchError::Target)?;
    let attr=container.attributes().get(attribute_index).ok_or(CompiledSearchError::Target)?;let outer=last.outer_span().ok_or(CompiledSearchError::Target)?;
    if container.name().namespace()!=Some(hwpx_package::HANCOM_2020_HEAD_NAMESPACE)||container.name().local_name()!="charProperties"
        ||last.name().namespace()!=Some(hwpx_package::HANCOM_2020_HEAD_NAMESPACE)||last.name().local_name()!="charPr"||last.parent()!=at.element_index()
        ||attr.name().namespace().is_some()||attr.name().local_name()!="itemCnt"||(attr.value_span().start(),attr.value_span().end())!=(count.source_start(),count.source_end())
        ||(append.source_start(),append.source_end())!=(outer.end(),outer.end()){return Err(CompiledSearchError::Target);}
    let mut p=projection::collect(receipt,inventory.source_package_sha256(),inventory.output_package_sha256(),"final_font_body_splices_with_header_resources",inventory.body_splices().map(SourceFontEdit::source_anchor))?;
    for(edit,splice)in p.edits.iter_mut().zip(inventory.body_splices()){
        let expected=match receipt.axis{SourceFontStyleAxis::RunProperty=>Kind::RunSubtree,SourceFontStyleAxis::TextStyle=>Kind::TextSubtree};
        let at=source.resolve_anchor(splice.source_anchor()).map_err(|_|CompiledSearchError::Target)?;
        if splice.kind()!=expected||splice.source_part_path()!=at.part().path().as_str(){return Err(CompiledSearchError::Target);}
        edit.subtree=Some((splice.source_start(),splice.source_end()));
    }
    p.inventory_sha=inventory.canonical_sha256();p.font_resources=Some(HeaderResources{count,append});Ok(p)
}
