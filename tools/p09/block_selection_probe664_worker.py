"""Fixed command/unchanged limited worker envelope; no CLI or Native authority."""
import json
import sys
import crossref_fixed_worker as original

TARGET='implementation/p09/tools/run-block-selection-probe664-worker.ps1'
SOURCES=(set(original.SOURCES)-{original.TARGET})|{TARGET,
    'implementation/p09/tools/block-bookmark-source645-ports.ps1',
    'implementation/p09/tools/block-bookmark-source653-typed.ps1',
    'implementation/p09/tools/block-bookmark-selection658.ps1',
    'implementation/p09/tools/block-selection-probe662.ps1',
    'implementation/p09/tools/block-selection-probe662-reflection.cs',
    'implementation/p09/tools/block-bookmark-source646-document.ps1',
    'implementation/p09/tools/block-bookmark-source648-channel.ps1',
    'implementation/p09/tools/block-bookmark-source648-flow.ps1',
    'implementation/p09/tools/prepared-bookmark631-ports.ps1',
    'implementation/p09/tools/crossref-capture008-application-binding.ps1'}
RESULT='hwpx-agent.private.block-selection-probe664-result/v1'

class Worker(original.FixedWorker):
    def _fixed_command(self,reader):
        p=original.prior
        p.require(reader.root.resolve()==p.original.c.ROOT.resolve(),'BLOCK664_FIXED_ROOT')
        for path in sorted(SOURCES):reader.pin(path)
        p.require(reader.snapshots[p.original.BOOTSTRAP]['sha256']==p.original.BOOTSTRAP_SHA,'BLOCK664_ORIGINAL_BOOTSTRAP')
        args=[p.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(reader.root/TARGET),'-BlockSourceAfterCurrentSession']
        return[sys.executable,'-B',str(reader.root/p.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]

EXPECTED_STOP='P09_XREF_BIND_BLOCK648_PORT_PROBE_OBSERVATIONS_COMPLETE_NOT_CAPTURE'

def source_result_notice(value):
    original.prior.require(type(value)is dict and value.get('schema_version')==RESULT,'BLOCK664_DISTINCT_RESULT')
    case=value.get('case_failure')
    observed=(value.get('state')=='block_source_callbacks_failed_or_partial'and value.get('error_code')==EXPECTED_STOP
        and value.get('diagnostic_only')is True and value.get('probe_complete')is True
        and value.get('source_capture_executed')is False and value.get('completed_callback_cases')==0
        and type(value.get('completed_callback_cases'))is int and value.get('retained_live_or_uncertain_owners')==0
        and type(value.get('retained_live_or_uncertain_owners'))is int and type(case)is dict
        and case.get('phase')=='create_bookmarks'and case.get('error_code')==EXPECTED_STOP)
    return dict(state='PROBE664_RESULT_RECORDED_BEFORE_CLEANUP',diagnostic_observations_reported=observed,
        worker_failed_or_uncertain=True,intentional_diagnostic_stop_reported=observed,
        cleanup_confirmed=False,source_capture_executed=False,selection_API_qualified=False,
        native_execution_authorized=False,rerun_forbidden=True,P09_complete=False)

