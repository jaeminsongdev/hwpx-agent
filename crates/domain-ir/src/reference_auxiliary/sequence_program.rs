//! Explicit caller-ordered caption arithmetic, shared with the original full
//! auxiliary-state validator. Not native/render order or source authorization.
use super::*;
pub struct CaptionSequenceMember<'a> {
    pub logical_caption_id:&'a LogicalId,pub logical_object_id:&'a LogicalId,
    pub logical_sequence_id:&'a LogicalId,pub section_id:&'a LogicalId,
    pub object_kind:CaptionObjectKind,pub document_order:u64,
}
#[derive(Clone,Eq,PartialEq)]
pub struct ResolvedCaptionSequenceNumber {
    pub logical_caption_id:LogicalId,pub logical_sequence_id:LogicalId,
    pub document_order:u64,pub resolved_number:u32,
}
impl fmt::Debug for CaptionSequenceMember<'_> {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("CaptionSequenceMember(<redacted>; caller_order_not_native_order)")}}
impl fmt::Debug for ResolvedCaptionSequenceNumber {fn fmt(&self,f:&mut fmt::Formatter<'_>)->fmt::Result{f.write_str("ResolvedCaptionSequenceNumber(<redacted>; caller_arithmetic_not_native_counter)")}}
pub(super) struct Counters<'a,K:Ord> {values:BTreeMap<(&'a LogicalId,Option<K>),u32>}
impl<'a,K:Ord> Counters<'a,K> {
    pub(super) fn new()->Self{Self {values:BTreeMap::new()}}
    pub(super) fn next(&mut self,sequence:&'a CaptionSequenceDefinition,section:Option<K>)->Result<u32,ReferenceAuxiliaryError> {
        let counter=self.values.entry((&sequence.logical_sequence_id,section)).or_insert(sequence.start_at);
        let value=*counter;
        // Preserve the original validator's last-item overflow rejection too.
        *counter=counter.checked_add(1).ok_or(ReferenceAuxiliaryError::InvalidCaption)?;Ok(value)
    }
}
/// Applies explicit continuous/per-section policies in explicit document_order.
/// Does not construct an apparently complete auxiliary state from partial data.
/// # Errors
/// Rejects finite limits, invalid/duplicate definitions, members/objects/orders,
/// missing/wrong-kind sequences, invalid text/digests/opaque values and overflow.
pub fn resolve_caption_sequence_numbers(sequences:&[CaptionSequenceDefinition],members:&[CaptionSequenceMember<'_>],limits:ReferenceAuxiliaryLimits)
    ->Result<Vec<ResolvedCaptionSequenceNumber>,ReferenceAuxiliaryError> {
    if sequences.len()>limits.config().items_per_kind||members.len()>limits.config().items_per_kind{return Err(ReferenceAuxiliaryError::InputLimit);}
    let mut definitions=BTreeMap::new();
    for sequence in sequences {
        if definitions.insert(&sequence.logical_sequence_id,sequence).is_some()||sequence.start_at==0
            ||!valid_text(&sequence.label,limits.config().text_bytes,false)||!valid_text(&sequence.separator,limits.config().text_bytes,true){return Err(ReferenceAuxiliaryError::InvalidCaption);}
        require_digest(&sequence.number_style_sha256)?;validate_opaque(&sequence.opaque_properties,limits)?;
    }
    let mut captions=BTreeSet::new();let mut objects=BTreeSet::new();let mut orders=BTreeSet::new();let mut sections=BTreeSet::new();
    let mut ordered=Vec::new();ordered.try_reserve_exact(members.len()).map_err(|_|ReferenceAuxiliaryError::OutputLimit)?;
    for member in members {
        if !captions.insert(member.logical_caption_id)||!objects.insert(member.logical_object_id)||!orders.insert(member.document_order){return Err(ReferenceAuxiliaryError::InvalidCaption);}
        sections.insert(member.section_id);if sections.len()>limits.config().sections{return Err(ReferenceAuxiliaryError::InputLimit);}
        let sequence=*definitions.get(member.logical_sequence_id).ok_or(ReferenceAuxiliaryError::InvalidCaption)?;
        if member.object_kind!=sequence.object_kind{return Err(ReferenceAuxiliaryError::InvalidCaption);}ordered.push((member,sequence));
    }
    ordered.sort_by_key(|(member,_)|member.document_order);let mut counters=Counters::new();let mut output=Vec::new();
    output.try_reserve_exact(ordered.len()).map_err(|_|ReferenceAuxiliaryError::OutputLimit)?;
    for (member,sequence) in ordered {
        let section=match sequence.restart_policy {CaptionRestartPolicy::Continuous=>None,CaptionRestartPolicy::PerSection=>Some(member.section_id)};
        output.push(ResolvedCaptionSequenceNumber {logical_caption_id:member.logical_caption_id.clone(),logical_sequence_id:member.logical_sequence_id.clone(),
            document_order:member.document_order,resolved_number:counters.next(sequence,section)?});
    }Ok(output)
}
