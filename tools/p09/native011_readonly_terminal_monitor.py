"""Three live monitor epochs, terminal marker, then a known-empty Job audit.

The final marker never rotates a live guard or credits another live epoch.
Original live checks remain active through process exit/capture/cleanup. Only
after the actual Job is empty/closed may a separate audit guard be acquired.
"""
import time

SELF='tools/p09/native011_readonly_terminal_monitor.py'
TEST='tools/p09/tests/test_native011_readonly_terminal_monitor.py'


def require(ok,code):
    if not ok:raise ValueError('READONLY_TERMINAL_MONITOR_'+code)


def monitor_type(original,markers,live_stages):
    require(type(markers) is tuple and len(markers)==4 and len(set(markers))==4
        and type(live_stages) is tuple and len(live_stages)==3,'EXPLICIT_ORIGINAL_PROTOCOL')
    class Monitor(original):
        MARKERS=markers
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.terminal_markers=None;self.terminal_observed_after_exit=None;self.post_cleanup_audit_started=False
        def accept(self,observed,owned):
            try:
                require(not self.failed and not self.post_cleanup_audit_started,'NO_STOPPED_OR_POST_AUDIT_CHILD_REUSE')
                require(type(observed) is list and observed==list(markers[:len(observed)]) and len(observed)<=4,
                    'EXACT_ORIGINAL_MARKER_PREFIX')
                if self.terminal_markers is not None:
                    require(observed==list(markers),'NO_TERMINAL_MARKER_REGRESSION')
                    self.check();return
                if len(observed)<4:return super().accept(observed,owned)
                # Preserve the original failed-child route/error; do not use
                # successful terminal handling for a failed or unknown status.
                require(owned.returncode is None or type(owned.returncode) is int,'ACTUAL_OS_STATUS_TYPE')
                if owned.returncode is not None and owned.returncode!=0:
                    return super().accept(observed,owned)
                if self.seen<3:super().accept(observed[:3],owned)
                require(self.seen==3 and self.stage==live_stages[2],'THREE_REAL_LIVE_PHASES_ALREADY_OBSERVED')
                self.check(force=True)
                self.terminal_markers=tuple(observed)
                self.terminal_observed_after_exit=owned.returncode is not None
            except BaseException:
                self.failed=True;raise
        def start_post_cleanup_audit(self,owned_result):
            try:
                require(not self.failed and not self.post_cleanup_audit_started and self.seen==3
                    and self.terminal_markers==markers,'COMPLETE_ORIGINAL_TERMINAL_CAPTURE_BEFORE_AUDIT')
                job=owned_result['owned_job']
                require(type(owned_result['exit_code']) is int and owned_result['exit_code']==0
                    and owned_result['cleanup'] is True and owned_result['cleanup_errors']==[]
                    and job['owned_tree_empty'] is job['cleanup_confirmed'] is job['job_handle_closed'] is True
                    and job['last_job_accounting']['active_processes']==0
                    and job['last_job_accounting']['owned_processes']==[],
                    'ACTUAL_SUCCESSFUL_EXIT_AND_CLOSED_EMPTY_JOB_BEFORE_AUDIT_GUARD')
                self.check(force=True);self._release()
                require(len(self.records)==3 and tuple(row['stage'] for row in self.records)==live_stages
                    and all(row['cleanup_confirmed'] is True and 0<row['elapsed_seconds']<600 for row in self.records),
                    'ORIGINAL_THREE_LIVE_DEADLINES_NOT_EXTENDED')
                self.stage='terminal_audit';self.started=time.monotonic();self.guard=self.factory()
                self.guard.acquire();self.post_cleanup_audit_started=True
                return self.protocol_evidence()
            except BaseException:
                self.failed=True;raise
        def protocol_evidence(self):
            return dict(original_live_phase_markers_observed=self.seen,terminal_marker_sequence=list(self.terminal_markers or ()),
                terminal_observed_after_process_exit=self.terminal_observed_after_exit,
                post_cleanup_audit_started=self.post_cleanup_audit_started,
                terminal_marker_creates_live_epoch=False,original_Native_or_child_deadline_extended=False,
                audit_guard_acquired_only_after_closed_empty_Job=self.post_cleanup_audit_started,
                actual_Native_or_product_acceptance_qualified=False)
        def terminal_complete(self,owned_result):
            require(not self.failed and self.seen==3 and self.terminal_markers==markers
                and self.post_cleanup_audit_started and self.stage=='terminal_audit'
                and owned_result['cleanup'] is True and type(owned_result['exit_code']) is int
                and owned_result['exit_code']==0,'THREE_LIVE_PHASES_PLUS_POST_CLEANUP_AUDIT_NOT_FOUR_LIVE_PHASES')
    return Monitor


def cleanup_and_audit(owned,capture,owned_result,monitor,cleanup):
    cleanup(owned,capture,owned_result,None)
    return monitor.start_post_cleanup_audit(owned_result)


def main():
    """One tiny actual owned marker fixture, never a Native/product replay."""
    import hashlib
    import json
    import os
    from pathlib import Path
    import re
    import subprocess
    import sys
    from types import SimpleNamespace as NS
    require(not sys.argv[1:],'CLOSED_MARKER_FIXTURE_ONLY_ENTRY')
    sys.dont_write_bytecode=True
    import accept_case112_current_epoch as a,conservative_maintenance as c,prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline,preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_owned_metadata_audit as original
    from native011_owned_preparation import cleanup_owned,failure_record
    from owned_sql_job import OwnedSQLJobProcess
    from bounded_process_progress import BoundedProcessCapture
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    Type=monitor_type(original.Monitor,original.MARKERS,original.STAGES[:3])
    def factory():return baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    monitor=Type(factory);owned=capture=q=None;primary=None;started=time.monotonic()
    output='implementation/p09/evidence/p09-361-native011-current805-terminal-marker-owned-probe001.v1.json'
    row=dict(state='FAILED_ACTUAL_TERMINAL_MARKER_FIXTURE_NOT_NATIVE',owned=dict(constructor_entered=False,cleanup=False),
        GO_authorized=False,accepted_count_delta=0,Native_or_readonly008_or_product_reexecuted=False)
    try:
        require(not(c.ROOT/output).exists(),'EXCLUSIVE_NEW_PROTOCOL_FIXTURE')
        monitor.start();q=a.AcceptanceReader(c.ROOT,monitor.check)
        names=set()
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if type(value) is str and value.endswith('.py'):
                path=Path(value).resolve()
                if path.is_relative_to(c.ROOT):names.add(path.relative_to(c.ROOT).as_posix())
        names.update((SELF,TEST,'tools/p09/native011_readonly_frame_owned.py',
            'tools/p09/tests/test_native011_readonly_frame_owned.py'))
        require(0<len(names)<=96,'BOUNDED_ACTUAL_PROTOCOL_FIXTURE_SOURCES_NOT_NATIVE_UNION')
        for name in sorted(names):q.pin(name)
        monitor.check(force=True);monitor.guard.close()
        child="import sys,time,json\nfor marker in ('source_begin','connect_first_begin','consumer_begin'):\n print('P146_STAGE:'+marker,file=sys.stderr,flush=True);time.sleep(.75)\nprint('P146_STAGE:connect_second_begin',file=sys.stderr,flush=True)\nprint(json.dumps(dict(state='TERMINAL_MARKER_FIXTURE_NO_NATIVE_OR_PRODUCT')),flush=True)\n"
        command=[sys.executable,'-B','-c',child]
        row['owned']['constructor_entered']=True
        owned=OwnedSQLJobProcess(command,windows=monitor.guard.windows,allowed_executables=[sys.executable],
            cwd=c.ROOT,checkpoint=monitor.check,env=dict(os.environ))
        capture=BoundedProcessCapture(owned,output_limit=32768,parse_markers=True)
        deadline=time.monotonic()+20
        while True:
            monitor.check();require(time.monotonic()<deadline,'BOUNDED_MARKER_FIXTURE20')
            owned.observe()
            if monitor.seen<3:
                observed,_=capture.progress()
                # The fixture intentionally delays each real live marker. A
                # missed live phase is still refused; it is never reconstructed.
                monitor.accept(observed[:3],owned)
            try:stdout,stderr=capture.communicate(timeout=.1)
            except subprocess.TimeoutExpired:continue
            owned.observe();require(type(owned.returncode) is int and owned.returncode==0,'ACTUAL_FIXTURE_OS_EXIT0')
            observed,observations=capture.progress()
            require(monitor.seen==3 and monitor.terminal_markers is None,'THREE_REAL_PHASES_BEFORE_FORCED_LATE_FINAL_MARKER')
            before=(monitor.guard,monitor.started,len(monitor.records))
            monitor.accept(observed,owned)
            require(before==(monitor.guard,monitor.started,len(monitor.records)) and monitor.seen==3
                and monitor.terminal_observed_after_exit is True,'ACTUAL_LATE_MARKER_WITHOUT_GUARD_OR_DEADLINE_ROTATION')
            summary=json.loads(stdout.splitlines()[-1])
            require(summary==dict(state='TERMINAL_MARKER_FIXTURE_NO_NATIVE_OR_PRODUCT'),'EXACT_FIXTURE_NOT_NATIVE_SUMMARY')
            row['owned'].update(exit_code=owned.returncode,markers=observed,marker_observations=observations,
                child_summary=summary,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
                stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
            row['forced_actual_exit_before_final_marker_accept']=True
            break
        row['protocol']=cleanup_and_audit(owned,capture,row['owned'],monitor,cleanup_owned)
        owned=capture=None;monitor.terminal_complete(row['owned'])
        q.finish();monitor.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots),'ALL_ACTUAL_PROTOCOL_SOURCE_CLOSING')
        row.update(state='PASS_ACTUAL_TERMINAL_MARKER_EXIT_RACE_AND_POST_CLEANUP_AUDIT_NOT_NATIVE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        primary=error;row['failure']=failure_record(error,[] if monitor.guard is None else monitor.guard.samples)
    finally:
        if owned is not None or capture is not None:cleanup_owned(owned,capture,row['owned'],primary)
        elif not row['owned']['constructor_entered']:cleanup_owned(None,None,row['owned'],primary)
        monitor.close()
        row.update(epochs=monitor.records,cleanup=all(r['cleanup_confirmed'] for r in monitor.records)
            and row['owned']['cleanup'],source_pins=[] if q is None else list(q.snapshots.values()),
            elapsed_seconds=time.monotonic()-started)
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],failure=row.get('failure'),cleanup=row['cleanup'],
            elapsed=row['elapsed_seconds'],fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            actual_OS_exit_code=row['owned'].get('exit_code'),protocol=row.get('protocol'),receipt=pin)))
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
