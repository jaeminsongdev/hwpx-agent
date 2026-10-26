"""Fixed command/unchanged limited worker envelope; no CLI or Native authority."""
import json
import sys
import crossref_fixed_worker as original

TARGET='implementation/p09/tools/run-block-bookmark-source670-worker.ps1'
SOURCES=(set(original.SOURCES)-{original.TARGET})|{TARGET,
    'implementation/p09/tools/block-bookmark-source645-ports.ps1',
    'implementation/p09/tools/block-bookmark-origin668.ps1',
    'implementation/p09/tools/block-bookmark-selection658.ps1',
    'implementation/p09/tools/block-bookmark-source646-document.ps1',
    'implementation/p09/tools/block-bookmark-source648-channel.ps1',
    'implementation/p09/tools/block-bookmark-source648-flow.ps1',
    'implementation/p09/tools/prepared-bookmark631-ports.ps1',
    'implementation/p09/tools/crossref-capture008-application-binding.ps1'}
RESULT='hwpx-agent.private.block-bookmark-source670-result/v1'

class Worker(original.FixedWorker):
    def _fixed_command(self,reader):
        p=original.prior
        p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'BLOCK670_FIXED_ROOT')
        for path in sorted(SOURCES):reader.pin(path)
        p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'BLOCK670_ORIGINAL_BOOTSTRAP')
        args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(reader.root/TARGET),'-BlockSourceAfterCurrentSession']
        return[sys.executable,'-B',str(reader.root/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

def source_result_notice(value):
    """Use only for this profile. Legacy notice must not hide new failed states."""
    require=original.prior.require
    require(type(value)is dict and value.get('schema_version')==RESULT,'BLOCK670_DISTINCT_RESULT')
    import re
    failed=not(value.get('state')=='block_source_callbacks_returned_semantics_unqualified'
        and value.get('error_code')is None and type(value.get('completed_callback_cases'))is int
        and value['completed_callback_cases']==1 and type(value.get('retained_live_or_uncertain_owners'))is int
        and value['retained_live_or_uncertain_owners']==0 and value.get('native_execution_authorized')is False)
    code=value.get('error_code');case=value.get('case_failure')
    row=dict(state='BLOCK670_RESULT_RECORDED_BEFORE_CLEANUP',worker_failed_or_uncertain=failed,
        worker_error_code=code if type(code)is str and re.fullmatch(r'P09_XREF_(BIND|ROT)_[A-Z0-9_]{1,120}',code)else None,
        cleanup_confirmed=False,rerun_forbidden=True,native_execution_authorized=False,P09_complete=False)
    if type(case)is dict:
        phase=case.get('phase')
        allowed=('prepare_slot','create_save_session','bind_blank_document','seed_document','create_bookmarks','created_save',
            'created_image','created_bind','save_ready_close','save_session_close','create_reopen_session','fresh_created_open',
            'reopened_save','reopened_image','reopen_session_close','final_source_check')
        row['failed_case_phase']=phase if type(phase)is str and phase in allowed else None
        row['parameter_call_failure']=safe_call_failure(case.get('parameter_call_failure'))
    return row

CALL_SITES=frozenset(('bookmark_prepare','get_parameter_set','get_bookmark','get_hset','get_action','get_default',
    'put_name','put_type','put_command','get_name','get_type','get_command','assert_parameters',
    'bookmark_select','select_text','assert_selection','bookmark_execute','execute','bookmark_returned','release_references','origin_set','origin_read','origin_map','unknown'))
EXCEPTION_KINDS=frozenset(('COMException','RuntimeException','MethodInvocationException','SetValueInvocationException',
    'GetValueInvocationException','InvalidOperationException','ArgumentException','OtherException'))

def safe_call_failure(value):
    """All-or-nothing bounded diagnostic projection; never a raw exception."""
    import re
    if type(value)is not dict or set(value)!={'schema_version','call_site','range_index','exception_kind','hresult','rerun_forbidden'}:return None
    if value.get('schema_version')!='hwpx-agent.private.block-bookmark668-call-failure/v1':return None
    if type(value.get('call_site'))is not str or value['call_site']not in CALL_SITES:return None
    if type(value.get('range_index'))is not int or not 1<=value['range_index']<=8:return None
    if type(value.get('exception_kind'))is not str or value['exception_kind']not in EXCEPTION_KINDS:return None
    if type(value.get('hresult'))is not str or not re.fullmatch(r'0x[0-9A-F]{8}',value['hresult']):return None
    if value.get('rerun_forbidden')is not True:return None
    return dict(value)



