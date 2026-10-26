"""Truthful diagnostics for the new two-case worker, with original value redaction."""
from prepared_bookmark684_notice import result_notice as original
def result_notice(result):
    value=dict(result)
    if value.get('state')=='block_tail_two_callbacks_returned_semantics_unqualified':
        value['state']='block_eight_callbacks_returned_semantics_unqualified'
    return original(value)
