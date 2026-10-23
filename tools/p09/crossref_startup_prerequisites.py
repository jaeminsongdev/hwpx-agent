"""Readonly original startup prerequisites; no launch, COM, document, retry or permission-window action.

Passing every observation is not native/session qualification. The original
startup and fixed-eight host still need their own complete qualified connection.
"""
import crossref_native_startup as startup

PROFILE='hwpx-agent.crossref-startup-prerequisites/readonly-v1'


def inspect(windows,checkpoint,fresh_executable_pin):
    checks={};errors={}
    def observe(name,call,valid):
        checkpoint()
        try:
            value=call();checks[name]=bool(valid(value))
        except ValueError as error:
            code=error.args[0]if error.args else None
            # Resource/reader/unknown failures propagate. Never turn a STOP into a
            # failed checkbox and continue performing further observations.
            if type(code)is not str or not code.startswith(('XREF_NATIVE_STARTUP_','XREF_NATIVE_LIMITS_')):raise
            checks[name]=False;errors[name]=code if code.isascii()and len(code)<=160 and all(c.isupper()or c=='_'for c in code)else'XREF_NATIVE_STARTUP_READONLY_CHECK_REJECTED'
        except OSError:
            checks[name]=False;errors[name]='XREF_NATIVE_STARTUP_READONLY_OS_OBSERVATION_UNAVAILABLE'
    observe('original_resource_policy_shape',lambda:startup.limits.validate_plan(windows),lambda p:type(p)is dict and p['affinity']>0 and p['priority']==0x4000)
    observe('fixed_registered_server',startup.read_registered_command,lambda argv:argv==[startup.limits.EXECUTABLE,'-Automation'])
    observe('fixed_current_executable',fresh_executable_pin,lambda p:type(p)is dict and type(p.get('bytes'))is int
        and p['bytes']==startup.limits.EXECUTABLE_BYTES and p.get('sha256')==startup.limits.EXECUTABLE_SHA)
    processes=None
    def inventory():
        nonlocal processes
        value=startup.hwp_pids(windows,checkpoint)
        if type(value)is not set or any(type(pid)is not int or pid<=0 for pid in value):raise ValueError('XREF_NATIVE_STARTUP_PROCESS_SNAPSHOT_BOUND')
        processes=len(value);return value
    observe('no_preexisting_hwp_process',inventory,lambda p:not p)
    observe('caller_lifecycle_native_safe',lambda:startup.parent_without_prompt_kill(windows),lambda p:type(p)is dict and p.get('job_present')is False)
    checkpoint()
    return dict(profile=PROFILE,checks=checks,closed_errors=errors,preexisting_hwp_processes=processes,
        all_observed_prerequisites_passed=all(checks.values()),failed_prerequisites=sorted(name for name,ok in checks.items()if not ok),
        process_created=False,COM_activated=False,document_opened=False,permission_dialog_requested=False,
        native_startup_qualified=False,fixed_eight_executed=False,P09_complete=False)
