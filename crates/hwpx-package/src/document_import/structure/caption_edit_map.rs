//! Checked original byte coordinates -> output coordinates. No authority cache,
//! XML reparsing, per-request whole scans or guessed post-edit element ordinals.
use super::{ImportedDocumentStructure,caption_text::CaptionTextOutputError as E,caption_text_batch::PartEdits};
use crate::{PackagePath,document_import::ImportedSourcePart};
use std::collections::BTreeMap;
struct MappedEdit {start:usize,end:usize,new_start:usize,new_end:usize}
pub(super) struct OutputEditMap<'a> {
    parts:BTreeMap<&'a PackagePath,&'a ImportedSourcePart>,edits:BTreeMap<PackagePath,Vec<MappedEdit>>,
}
impl<'a> OutputEditMap<'a> {
    pub fn new(output:&'a ImportedDocumentStructure,parts:&BTreeMap<&PackagePath,PartEdits<'_>>)->Result<Self,E> {
        let mut edits=BTreeMap::new();
        for (path,part) in parts {
            let mut mapped=Vec::new();mapped.try_reserve_exact(part.edits.len()).map_err(|_|E::Limit)?;
            let(mut old,mut new)=(0usize,0usize);
            for edit in &part.edits {
                if edit.start<old||edit.end<edit.start{return Err(E::Selection);}
                let start=new.checked_add(edit.start-old).ok_or(E::Limit)?;
                new=start.checked_add(edit.bytes.len()).ok_or(E::Limit)?;old=edit.end;
                mapped.push(MappedEdit {start:edit.start,end:edit.end,new_start:start,new_end:new});
            }
            edits.insert((*path).clone(),mapped);
        }
        Ok(Self {parts:output.source().parts().iter().map(|p|(p.path(),p)).collect(),edits})
    }
    pub fn original_position(&self,path:&PackagePath,point:usize)->Result<usize,E> {
        let Some(edits)=self.edits.get(path)else{return Ok(point)};
        let after=edits.partition_point(|e|e.end<=point);
        if edits.get(after).is_some_and(|e|e.start<=point){return Err(E::Readback);}
        if let Some(before)=after.checked_sub(1).and_then(|i|edits.get(i)) {
            before.new_end.checked_add(point.checked_sub(before.end).ok_or(E::Readback)?).ok_or(E::Limit)
        }else{Ok(point)}
    }
    pub fn edit_start(&self,path:&PackagePath,start:usize,end:usize)->Result<usize,E> {
        let edits=self.edits.get(path).ok_or(E::Readback)?;
        let i=edits.binary_search_by_key(&(start,end),|e|(e.start,e.end)).map_err(|_|E::Readback)?;Ok(edits[i].new_start)
    }
    pub fn output_element(&self,path:&PackagePath,point:usize)->Result<(&'a ImportedSourcePart,usize),E> {
        let part=*self.parts.get(path).ok_or(E::Readback)?;let xml=part.xml().ok_or(E::Readback)?;
        let i=xml.elements().binary_search_by_key(&point,|e|e.start_tag_span().start()).map_err(|_|E::Readback)?;Ok((part,i))
    }
    pub fn original_element(&self,path:&PackagePath,point:usize)->Result<(&'a ImportedSourcePart,usize),E> {
        self.output_element(path,self.original_position(path,point)?)
    }
}
