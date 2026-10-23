//! Exact header resource effects and final body splices, not invented structural owners.
use super::*;
use crate::document_import::ImportedSourcePart;
pub const FONT_EDIT_INVENTORY_PROFILE:&str="hwpx-agent.source-font-edit-inventory/v1";
const MAX_INVENTORY_BYTES:usize=8*1024*1024;

#[derive(Clone,Copy,Debug,Eq,PartialEq,Serialize)]
#[serde(tag="kind",rename_all="snake_case")]
pub enum SourceFontEditKind{
    CharacterPropertyCount{attribute_index:usize,original_items:usize,output_items:usize},
    AppendCharacterProperties{appended_items:usize},
    RunSubtree,
    TextSubtree,
}
impl SourceFontEditKind{
    #[must_use]pub const fn is_body(self)->bool{matches!(self,Self::RunSubtree|Self::TextSubtree)}
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceFontEdit{
    source_part_path:String,source_anchor:SourceAnchorHandle,kind:SourceFontEditKind,
    source_start:usize,source_end:usize,replacement_sha256:[u8;32],replacement_bytes:usize,fragments:usize,
}
impl fmt::Debug for SourceFontEdit{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("SourceFontEdit").field("kind",&self.kind).finish_non_exhaustive()}}
impl SourceFontEdit{
    #[must_use]pub fn source_part_path(&self)->&str{&self.source_part_path}
    #[must_use]pub const fn source_anchor(&self)->&SourceAnchorHandle{&self.source_anchor}
    #[must_use]pub const fn kind(&self)->SourceFontEditKind{self.kind}
    #[must_use]pub const fn source_start(&self)->usize{self.source_start}
    #[must_use]pub const fn source_end(&self)->usize{self.source_end}
    #[must_use]pub const fn replacement_sha256(&self)->[u8;32]{self.replacement_sha256}
    #[must_use]pub const fn replacement_bytes(&self)->usize{self.replacement_bytes}
    #[must_use]pub const fn fragments(&self)->usize{self.fragments}
}
#[derive(Clone,Eq,PartialEq,Serialize)]
pub struct SourceFontEditInventory{
    profile:&'static str,axis:SourceFontStyleAxis,source_package_sha256:[u8;32],output_package_sha256:[u8;32],
    legacy_receipt_sha256:[u8;32],compiled_edits_sha256:[u8;32],edits:Vec<SourceFontEdit>,
    #[serde(skip)]canonical_sha256:[u8;32],
}
impl fmt::Debug for SourceFontEditInventory{fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.debug_struct("SourceFontEditInventory").field("axis",&self.axis).field("edits",&self.edits.len()).finish_non_exhaustive()}}
impl SourceFontEditInventory{
    #[must_use]pub const fn profile(&self)->&'static str{self.profile}
    #[must_use]pub const fn axis(&self)->SourceFontStyleAxis{self.axis}
    #[must_use]pub const fn source_package_sha256(&self)->[u8;32]{self.source_package_sha256}
    #[must_use]pub const fn output_package_sha256(&self)->[u8;32]{self.output_package_sha256}
    #[must_use]pub const fn legacy_receipt_sha256(&self)->[u8;32]{self.legacy_receipt_sha256}
    #[must_use]pub const fn compiled_edits_sha256(&self)->[u8;32]{self.compiled_edits_sha256}
    #[must_use]pub const fn canonical_sha256(&self)->[u8;32]{self.canonical_sha256}
    #[must_use]pub fn edits(&self)->&[SourceFontEdit]{&self.edits}
    pub fn header_effects(&self)->impl Iterator<Item=&SourceFontEdit>{self.edits.iter().filter(|e|!e.kind.is_body())}
    pub fn body_splices(&self)->impl Iterator<Item=&SourceFontEdit>{self.edits.iter().filter(|e|e.kind.is_body())}
}
pub(super) struct Builder{axis:SourceFontStyleAxis,edits:Vec<SourceFontEdit>}
impl Builder{
    pub(super) fn new(axis:SourceFontStyleAxis)->Self{Self{axis,edits:Vec::new()}}
    fn push(&mut self,part:&ImportedSourcePart,element:usize,kind:SourceFontEditKind,start:usize,edit:&Edit,fragments:usize)->Result<(),E>{
        if self.edits.len()>=PatchLimits::default().config().max_intents{return Err(E::Limit);}
        if start>edit.end||edit.bytes.is_empty(){return Err(E::Selection);}
        self.edits.push(SourceFontEdit{source_part_path:part.path().as_str().to_owned(),source_anchor:part.element_anchor(element).ok_or(E::Selection)?.clone(),kind,
            source_start:start,source_end:edit.end,replacement_sha256:Sha256::digest(&edit.bytes).into(),replacement_bytes:edit.bytes.len(),fragments});Ok(())
    }
    pub(super) fn count(&mut self,part:&ImportedSourcePart,element:usize,attribute:usize,before:usize,after:usize,edit:&Edit)->Result<(),E>{
        let node=part.xml().and_then(|x|x.elements().get(element)).ok_or(E::Selection)?;let a=node.attributes().get(attribute).ok_or(E::Selection)?;
        if part.path().as_str()!="Contents/header.xml"||node.name().namespace()!=Some(crate::HANCOM_2020_HEAD_NAMESPACE)||node.name().local_name()!="charProperties"
            ||a.name().namespace().is_some()||a.name().local_name()!="itemCnt"||a.semantic_value().parse::<usize>().ok()!=Some(before)
            ||a.value_span().end()!=edit.end||edit.bytes!=after.to_string().as_bytes()||before>=after||!edit.fragments.is_empty(){return Err(E::Selection);}
        self.push(part,element,SourceFontEditKind::CharacterPropertyCount{attribute_index:attribute,original_items:before,output_items:after},a.value_span().start(),edit,0)
    }
    pub(super) fn append(&mut self,part:&ImportedSourcePart,element:usize,count:usize,edit:&Edit)->Result<(),E>{
        let node=part.xml().and_then(|x|x.elements().get(element)).ok_or(E::Selection)?;let end=node.outer_span().ok_or(E::Selection)?.end();
        if part.path().as_str()!="Contents/header.xml"||node.name().namespace()!=Some(crate::HANCOM_2020_HEAD_NAMESPACE)||node.name().local_name()!="charPr"
            ||edit.end!=end||count==0||!edit.fragments.is_empty(){return Err(E::Selection);}
        self.push(part,element,SourceFontEditKind::AppendCharacterProperties{appended_items:count},end,edit,count)
    }
    pub(super) fn body(&mut self,part:&ImportedSourcePart,element:usize,edit:&Edit)->Result<(),E>{
        let node=part.xml().and_then(|x|x.elements().get(element)).ok_or(E::Selection)?;let outer=node.outer_span().ok_or(E::Selection)?;
        let(kind,name)=match self.axis{SourceFontStyleAxis::RunProperty=>(SourceFontEditKind::RunSubtree,"run"),SourceFontStyleAxis::TextStyle=>(SourceFontEditKind::TextSubtree,"t")};
        if part.path().as_str()=="Contents/header.xml"||node.name().namespace()!=Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)||node.name().local_name()!=name
            ||edit.end!=outer.end()||edit.fragments.is_empty(){return Err(E::Selection);}
        self.push(part,element,kind,outer.start(),edit,edit.fragments.len())
    }
    pub(super) fn finish(mut self,receipt:&SourceFontReplacementReceipt,intents:usize)->Result<SourceFontEditInventory,E>{
        if self.edits.len()!=intents||intents<3||receipt.names.source_package_sha256==[0;32]||receipt.output_package_sha256==[0;32]{return Err(E::Selection);}
        self.edits.sort_by(|a,b|(&a.source_part_path,a.source_start).cmp(&(&b.source_part_path,b.source_start)));
        let(mut counts,mut appends,mut body)=(0usize,0usize,0usize);let mut seen=BTreeSet::new();
        for(i,edit)in self.edits.iter().enumerate(){
            if !seen.insert(&edit.source_anchor.opaque_handle){return Err(E::Selection);}
            if i>0{let p=&self.edits[i-1];if p.source_part_path==edit.source_part_path&&(p.source_end>edit.source_start||p.source_start==edit.source_start){return Err(E::Selection);}}
            match edit.kind{
                SourceFontEditKind::CharacterPropertyCount{original_items,output_items,..}=>{counts+=1;if output_items.checked_sub(original_items)!=Some(receipt.cloned_character_properties){return Err(E::Selection);}},
                SourceFontEditKind::AppendCharacterProperties{appended_items}=>{appends+=1;if appended_items!=receipt.cloned_character_properties{return Err(E::Selection);}},
                SourceFontEditKind::RunSubtree if self.axis==SourceFontStyleAxis::RunProperty=>body+=1,
                SourceFontEditKind::TextSubtree if self.axis==SourceFontStyleAxis::TextStyle=>body+=1,
                _=>return Err(E::Selection),
            }
        }
        if counts!=1||appends!=1||body==0||self.edits.iter().map(|e|&e.source_part_path).collect::<BTreeSet<_>>().len()!=receipt.changed_parts{return Err(E::Selection);}
        let compiled:Vec<_>=self.edits.iter().map(|e|(e.source_part_path.as_str(),e.source_start,e.source_end,e.replacement_sha256)).collect();
        let compiled_edits_sha256=bounded_hash(&compiled)?;if compiled_edits_sha256!=receipt.compiled_edits_sha256{return Err(E::Selection);}
        let mut result=SourceFontEditInventory{profile:FONT_EDIT_INVENTORY_PROFILE,axis:self.axis,source_package_sha256:receipt.names.source_package_sha256,
            output_package_sha256:receipt.output_package_sha256,legacy_receipt_sha256:bounded_hash(receipt)?,compiled_edits_sha256,edits:self.edits,canonical_sha256:[0;32]};
        result.canonical_sha256=bounded_hash(&result)?;Ok(result)
    }
}
fn bounded_hash(value:&impl Serialize)->Result<[u8;32],E>{
    struct Hash{state:Sha256,length:usize}
    impl std::io::Write for Hash{
        fn write(&mut self,bytes:&[u8])->std::io::Result<usize>{self.length=self.length.checked_add(bytes.len()).filter(|n|*n<=MAX_INVENTORY_BYTES).ok_or_else(||std::io::Error::other("font_inventory_limit"))?;
            self.state.update(bytes);Ok(bytes.len())}
        fn flush(&mut self)->std::io::Result<()>{Ok(())}
    }
    let mut writer=Hash{state:Sha256::new(),length:0};serde_json::to_writer(&mut writer,value).map_err(|_|E::Limit)?;Ok(writer.state.finalize().into())
}
