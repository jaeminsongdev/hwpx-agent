//! Admitted BOOKMARK Prop2 range meaning, distinct from point markers and evaluated fields.
use super::*;
use super::super::{block_bookmarks::{ImportedBlockBookmarks,BlockBookmarkImportError},cached_source::FieldCacheSnapshot};
use domain_ir::ReferenceAuxiliaryLimits;
use sha2::{Digest as _,Sha256};

pub const GRAPH_PROFILE:&str="hwpx-agent.document-import-field-semantics/partial-v4";
pub const GRAPH_SCOPE:&str="source_https_formula_bookmark_crossref_edges_and_bookmark_prop2_ranges_not_native_evaluation_full_import_or_execution";
pub const INDEX_PROFILE:&str="hwpx-agent.source-field-meaning-index/partial-v3";
pub(super) fn zero(value:&usize)->bool{*value==0}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceBlockBookmarkMeaning{
    pub profile:&'static str,pub name_sha256:[u8;32],pub name_utf8_bytes:usize,
    pub begin_fingerprint_sha256:[u8;32],pub end_fingerprint_sha256:[u8;32],
    pub selected_source:FieldCacheSnapshot,
    pub point_marker_equivalent:bool,pub native_evaluation_or_execution_authority:bool,
}
impl fmt::Debug for SourceBlockBookmarkMeaning{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("SourceBlockBookmarkMeaning(<redacted>; source_range_only)")}}
pub(super) fn without_crossrefs(fields:&ImportedDocumentFields<'_>,limits:ReferenceAuxiliaryLimits)
    ->Result<Option<ImportedBlockBookmarks>,FieldSemanticImportError>{
    if !fields.fields().iter().any(|f|f.native_kind=="BOOKMARK"){return Ok(None);}
    match ImportedBlockBookmarks::import(fields,limits){
        Ok(value)=>Ok(Some(value)),
        // Unknown native bookmark profiles remain explicit Unsupported. Invalid
        // anchors/coverage and exhausted budgets never become an empty inventory.
        Err(BlockBookmarkImportError::Unsupported)=>Ok(None),
        Err(BlockBookmarkImportError::Limit)=>Err(FieldSemanticImportError::Limit),
        Err(_)=>Err(FieldSemanticImportError::Binding),
    }
}
pub(super) fn meanings(blocks:Option<&ImportedBlockBookmarks>)->Result<BTreeMap<LogicalId,SourceBlockBookmarkMeaning>,FieldSemanticImportError>{
    let mut rows=BTreeMap::new();if let Some(blocks)=blocks{for b in blocks.observations(){
        let value=SourceBlockBookmarkMeaning{profile:"hwpx-agent.source-bookmark-prop2-range-meaning/v1",
            name_sha256:Sha256::digest(b.name().as_bytes()).into(),name_utf8_bytes:b.name().len(),
            begin_fingerprint_sha256:b.begin_anchor().fingerprint_sha256,end_fingerprint_sha256:b.end_anchor().fingerprint_sha256,
            selected_source:b.selected_source().clone(),point_marker_equivalent:false,native_evaluation_or_execution_authority:false};
        if rows.insert(b.field_reference_id().clone(),value).is_some(){return Err(FieldSemanticImportError::Binding);}
    }}Ok(rows)
}
