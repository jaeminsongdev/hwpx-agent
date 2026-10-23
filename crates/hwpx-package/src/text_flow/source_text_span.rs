//! Reuse the original text-span reader, not a second control/attribute decoder.
use super::*;

pub(crate) fn read_source_text_span(document:&PreservingXmlDocument,index:usize)->Result<TextSpan,TextFlowError> {
    let node=element(document,index)?;
    require_name(node,"t")?;
    let limits=TextFlowLimits::default();
    let outer=node.outer_span().ok_or(TextFlowError::UnsupportedShape)?;
    if outer.end()-outer.start()>limits.config().input_bytes{return Err(TextFlowError::InputLimit);}
    let end=document.elements().partition_point(|n|n.start_tag_span().start()<outer.end());
    if end.checked_sub(index).is_none_or(|n|n>limits.config().items){return Err(TextFlowError::ItemLimit);}
    let mut state=ReadState::new(limits);
    match read_text_span(document,index,&mut state)? {
        TextRunItem::Text(span)=>Ok(span),
        _=>Err(TextFlowError::UnsupportedShape),
    }
}
