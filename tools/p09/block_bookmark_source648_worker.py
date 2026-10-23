"""Fixed command/unchanged limited worker envelope; no CLI or Native authority."""
import json
import sys
import crossref_fixed_worker as original

TARGET='implementation/p09/tools/run-block-bookmark-source648-worker.ps1'
SOURCES=(set(original.SOURCES)-{original.TARGET})|{TARGET,
    'implementation/p09/tools/block-bookmark-source645-ports.ps1',
    'implementation/p09/tools/block-bookmark-source646-document.ps1',
    'implementation/p09/tools/block-bookmark-source648-channel.ps1',
    'implementation/p09/tools/block-bookmark-source648-flow.ps1',
    'implementation/p09/tools/prepared-bookmark631-ports.ps1',
    'implementation/p09/tools/crossref-capture008-application-binding.ps1'}
RESULT='hwpx-agent.private.block-bookmark-source648-result/v1'

class Worker(original.FixedWorker):
    def _fixed_command(self,reader):
        p=original.prior
        p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'BLOCK648_FIXED_ROOT')
        for path in sorted(SOURCES):reader.pin(path)
        p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'BLOCK648_ORIGINAL_BOOTSTRAP')
        args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(reader.root/TARGET),'-BlockSourceAfterCurrentSession']
        return[sys.executable,'-B',str(reader.root/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

def source_result_notice(value):
    """Use only for this profile. Legacy notice must not hide new failed states."""
    require=original.prior.require
    require(type(value)is dict and value.get('schema_version')==RESULT,'BLOCK648_DISTINCT_RESULT')
    import re
    failed=not(value.get('state')=='block_source_callbacks_returned_semantics_unqualified'
        and value.get('error_code')is None and type(value.get('completed_callback_cases'))is int
        and value['completed_callback_cases']==1 and type(value.get('retained_live_or_uncertain_owners'))is int
        and value['retained_live_or_uncertain_owners']==0 and value.get('native_execution_authorized')is False)
    code=value.get('error_code');case=value.get('case_failure')
    row=dict(state='BLOCK648_RESULT_RECORDED_BEFORE_CLEANUP',worker_failed_or_uncertain=failed,
        worker_error_code=code if type(code)is str and re.fullmatch(r'P09_XREF_(BIND|ROT)_[A-Z0-9_]{1,120}',code)else None,
        cleanup_confirmed=False,rerun_forbidden=True,native_execution_authorized=False,P09_complete=False)
    if type(case)is dict:
        phase=case.get('phase')
        allowed=('prepare_slot','create_save_session','bind_blank_document','seed_document','create_bookmarks','created_save',
            'created_image','created_bind','save_ready_close','save_session_close','create_reopen_session','fresh_created_open',
            'reopened_save','reopened_image','reopen_session_close','final_source_check')
        row['failed_case_phase']=phase if type(phase)is str and phase in allowed else None
    return row
