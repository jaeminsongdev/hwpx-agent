"""Closed prepared-step diagnostics; original transport/cleanup policies unchanged."""
from crossref_native_worker_io import result_notice as original
import re
STEPS={'prepare_slot','create_save_session','candidate_open','candidate_bind','initial_identity','initial_snapshot','initial_image',
    'saved_save','saved_bind','save_session_close','create_reopen_session','fresh_saved_open','reopened_save','reopened_image','reopen_session_close','final_source_check'}
def result_notice(result):
    value=original(result)
    value['worker_failed_or_uncertain']=result.get('state')not in('session_worker_returned','session_worker_closed','block_eight_callbacks_returned_semantics_unqualified')
    # Original session states are adjudicated by the original session transport.
    if result.get('phase')!='fixed_eight':value['worker_failed_or_uncertain']=original(result)['worker_failed_or_uncertain']
    case=result.get('case_failure')
    if type(case)is dict and case.get('phase')in STEPS:value['failed_case_phase']=case['phase']
    return value
