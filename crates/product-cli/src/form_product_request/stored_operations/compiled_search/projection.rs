use super::*;
use super::super::search_mutations::SearchMutationReceiptRef as Receipt;
use domain_ir::SourceAnchorHandle;
#[derive(Serialize)]
pub(super) struct Edit<'a>{pub anchor:&'a SourceAnchorHandle,pub subtree:Option<(usize,usize)>}
pub(super) struct Projection<'a>{pub source:[u8;32],pub output:[u8;32],pub receipt_sha:[u8;32],pub inventory_sha:[u8;32],pub domain:&'static str,pub edits:Vec<Edit<'a>>,pub font_resources:Option<super::font_resources::HeaderResources<'a>>}
pub(super) fn collect<'a>(payload:&impl Serialize,source:[u8;32],output:[u8;32],domain:&'static str,
    anchors:impl Iterator<Item=&'a SourceAnchorHandle>)->Result<Projection<'a>,CompiledSearchError>{
    let mut edits=Vec::new();for anchor in anchors{if edits.len()>=MAX_EDITS{return Err(CompiledSearchError::Limit);}edits.push(Edit{anchor,subtree:None});}
    if edits.is_empty(){return Err(CompiledSearchError::Binding);}
    let receipt_sha=bounded_hash(payload,MAX_METADATA_BYTES)?;let inventory_sha=bounded_hash(&(receipt_sha,domain,&edits),MAX_METADATA_BYTES)?;
    Ok(Projection{source,output,receipt_sha,inventory_sha,domain,edits,font_resources:None})
}
pub(super) fn project(candidate:&PreparedStoredSearchMutation)->Result<Projection<'_>,CompiledSearchError>{
    macro_rules! text{($payload:expr,$r:expr,$path:literal)=>{{let p=$payload;let r=$r;collect(p,r.source_package_sha256,r.output_package_sha256,$path,r.changes.iter().map(|e|&e.source_text_anchor))}}}
    match candidate.receipt(){
        Receipt::Literal(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::LiteralAtoms(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::ReviewLiteral(r)=>text!(&r.stored.output,&r.stored.output.output,"output.changes"),
        Receipt::SelectorLiteral(r)=>text!(&r.stored.output,&r.stored.output.body_candidate.output,"body_candidate.output.changes"),
        Receipt::Regex(r)=>text!(&r.stored.output,&r.stored.output.output,"output.changes"),
        Receipt::RegexInsertion(r)=>text!(&r.stored.output,&r.stored.output.output.output,"output.output.changes"),
        Receipt::UnicodeScope(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::UnicodeMatches(r)=>text!(&r.stored.output,&r.stored.output.output,"output.changes"),
        Receipt::Case(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::Width(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::Whitespace(r)=>text!(&r.stored.output,&r.stored.output,"changes"),
        Receipt::ParagraphStyle(r)=>{let p=&r.stored.output;collect(p,p.source_package_sha256,p.output_package_sha256,"changes",p.changes.iter().map(|e|&e.paragraph_anchor))},
        Receipt::NamedStyle(r)=>{let p=&r.stored.output;collect(p,p.source_package_sha256,p.output_package_sha256,"changes",p.changes.iter().map(|e|&e.paragraph_anchor))},
        Receipt::NamedStyleOptions(r)=>{let p=&r.stored.output;let s=p.source();collect(p,s.source_package_sha256,s.output_package_sha256,"changes",s.changes.iter().map(|e|&e.paragraph_anchor))},
        Receipt::PersonalInfoMask(r)=>{
            let i=candidate.personal_info_mask_inventory().ok_or(CompiledSearchError::Binding)?;let r=&r.stored.output;
            let mut p=collect(r,i.source_package_sha256(),i.output_package_sha256(),"selected_mask_text_splices",i.anchors().iter())?;
            if p.receipt_sha!=i.receipt_sha256()||p.source!=r.source_package_sha256||p.output!=r.output_package_sha256{return Err(CompiledSearchError::Binding);}
            p.inventory_sha=i.canonical_sha256();Ok(p)
        },
        Receipt::TextControl(r)=>{let p=&r.stored.output;collect(p,p.source_package_sha256,p.output_package_sha256,"span_changes",p.span_changes.iter().map(|e|&e.source_text_anchor))},
        Receipt::NumberControl(r)=>{let p=&r.stored.output;collect(p,p.source_package_sha256,p.stream.content.output.output_package_sha256,"changes",p.changes.iter().map(|e|&e.source_control_anchor))},
        Receipt::CharacterStyle(r)=>style(candidate,&r.stored.output),
        Receipt::TextStyle(r)=>style(candidate,&r.stored.output),
        Receipt::ParagraphSort(r)=>permutation(candidate,&r.stored.output),
        Receipt::ParagraphSortGroups(r)=>permutation(candidate,&r.stored.output),
        Receipt::Font(r)=>super::font_resources::project(candidate,&r.stored.output),
        Receipt::FontOptions(r)=>{
            let mut p=super::font_resources::project(candidate,r.stored.output.source())?;
            p.receipt_sha=bounded_hash(&r.stored.output,MAX_METADATA_BYTES)?;Ok(p)
        },
    }
}
fn permutation<'a>(candidate:&'a PreparedStoredSearchMutation,payload:&impl Serialize)->Result<Projection<'a>,CompiledSearchError>{
    let inventory=candidate.sort_splices().ok_or(CompiledSearchError::Binding)?;
    let mut p=collect(payload,inventory.source_package_sha256(),inventory.output_package_sha256(),"final_permutation_splices",inventory.splices().iter().map(|e|e.source_anchor()))?;
    if p.receipt_sha!=inventory.legacy_receipt_sha256(){return Err(CompiledSearchError::Binding);}
    for(e,s)in p.edits.iter_mut().zip(inventory.splices()){e.subtree=Some((s.source_start(),s.source_end()));}
    p.inventory_sha=inventory.canonical_sha256();Ok(p)
}
fn style<'a>(candidate:&'a PreparedStoredSearchMutation,payload:&impl Serialize)->Result<Projection<'a>,CompiledSearchError>{
    let inventory=candidate.compiler_view().splices.ok_or(CompiledSearchError::Binding)?;
    let mut p=collect(payload,inventory.source_package_sha256(),inventory.output_package_sha256(),"final_splices",inventory.splices().iter().map(|e|e.source_anchor()))?;
    if p.receipt_sha!=inventory.legacy_receipt_sha256(){return Err(CompiledSearchError::Binding);}
    for(e,s)in p.edits.iter_mut().zip(inventory.splices()){e.subtree=Some((s.source_start(),s.source_end()));}
    p.inventory_sha=inventory.canonical_sha256();Ok(p)
}
