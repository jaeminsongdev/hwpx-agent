"""One fixed readonly audit Job; four observed original600 monitor epochs.

Phase markers are accepted only as an exact prefix from the one owned child.
They do not authorize Native or reset its source/readiness/product clocks.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace as NS
from native011_owned_preparation import failure_record,cleanup_owned

SELF='tools/p09/native011_owned_metadata_audit.py'
TARGET='tools/p09/native011_metadata_audit.py'
STAGES=('construction','opening','metadata','closing')
MARKERS=('source_begin','connect_first_begin','consumer_begin','connect_second_begin')


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_OWNED_METADATA_AUDIT_'+code)


class Monitor:
    def __init__(self,factory):
        self.factory=factory;self.guard=None;self.records=[];self.seen=0;self.stage='construction';self.failed=False
    def start(self):self.guard=self.factory();self.started=time.monotonic();self.guard.acquire()
    def check(self,*args,**kwargs):
        require(not self.failed and self.guard is not None,'NO_STOPPED_MONITOR_REUSE')
        try:return self.guard.check(*args,**kwargs)
        except BaseException:self.failed=True;raise
    def cold_sample_interval(self,*,clock=time.monotonic,sleep=time.sleep):
        # Baseline.__init__ seeds a measured CPU/time pair, not a sample.
        # Original acquire waits .5s. This monitor cannot acquire the child's
        # mutex, so retain that measured first interval without fabricating it.
        if self.guard.samples or getattr(self.guard,'cpu',None) is None:return
        for _ in range(16):
            remaining=self.guard.last+.5-clock()
            if remaining<=0:return
            sleep(min(.05,remaining))
        require(False,'COLD_SAMPLE_CLOCK_DID_NOT_ADVANCE')
    def _release(self):
        if self.guard is None:return
        guard=self.guard;self.guard=None;guard.close();samples=guard.samples
        self.records.append(dict(stage=self.stage,elapsed_seconds=time.monotonic()-self.started,
            cleanup_confirmed=guard.cleanup,original_resource_sample_count=len(samples),
            terminal_resource_samples=[dict(v) for v in samples[-8:]],
            system_CPU_max=max((v['system_cpu_percent'] for v in samples),default=None),
            available_RAM_min=min((v['available_ram_percent'] for v in samples),default=None),
            preparation_policy=guard.preparation_CPU.summary()))
        require(guard.cleanup,'MONITOR_ORIGINAL_GUARD_CLEANUP')
    def accept(self,markers,owned):
        try:
            require(not self.failed,'NO_FAILED_MARKER_RETRY')
            return self._accept(markers,owned)
        except BaseException:self.failed=True;raise
    def _accept(self,markers,owned):
        require(type(markers) is list and self.seen<=len(markers)<=len(MARKERS)
            and markers==list(MARKERS[:len(markers)]),'ONLY_FOUR_EXACT_OBSERVED_PHASE_MARKERS')
        while self.seen<len(markers):
            index=self.seen
            if index:
                require(owned.returncode is None,'NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS')
                owned.observe();self.check(force=True);self._release()
                self.stage=STAGES[index];self.guard=self.factory();self.started=time.monotonic()
                # The child owns the real mutex while running. This monitor
                # samples original guards without taking that child's lease.
                self.cold_sample_interval();self.check(force=True)
            self.seen+=1
    def close(self):self._release()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    require(1<=args.attempt<=8 and 1<=args.generation<=8,'CLOSED_SINGLE_READONLY_AUDIT')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    from owned_sql_job import OwnedSQLJobProcess
    from bounded_process_progress import BoundedProcessCapture
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    def factory():return baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    monitor=Monitor(factory);owned=capture=None;primary=None;q=None;started=time.monotonic()
    output=f'implementation/p09/evidence/p09-361-native011-owned-metadata-audit-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_OWNED_NATIVE011_METADATA_AND_WHOLE_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,owned={'constructor_entered':False,'cleanup':False},automatic_retry=False)
    try:
        monitor.start();q=a.AcceptanceReader(c.ROOT,monitor.check)
        require(not (c.ROOT/output).exists(),'EXCLUSIVE_NEW_OWNED_RECEIPT')
        for name in (SELF,TARGET,'tools/p09/native011_metadata_epochs.py','tools/p09/native011_parent_plan.py',
            'tools/p09/native011_shared_parent.py','tools/p09/native011_metadata_report.py',
            'tools/p09/native011_owned_preparation.py','tools/p09/owned_sql_job.py','tools/p09/bounded_process_progress.py'):
            q.pin(name)
        monitor.check(force=True);monitor.guard.close()
        command=[sys.executable,'-B',str(c.ROOT/TARGET),'--attempt',str(args.attempt),'--generation',str(args.generation)]
        row['owned']['constructor_entered']=True
        owned=OwnedSQLJobProcess(command,windows=monitor.guard.windows,allowed_executables=[sys.executable],
            cwd=c.ROOT,checkpoint=monitor.check,env=dict(os.environ))
        capture=BoundedProcessCapture(owned,output_limit=32768,parse_markers=True)
        deadline=time.monotonic()+2400;announcement=time.monotonic()
        while True:
            markers,_=capture.progress();monitor.accept(markers,owned)
            monitor.check();require(time.monotonic()<deadline,'FOUR_PREPARATION_EPOCHS_TOTAL2400')
            try:stdout,stderr=capture.communicate(timeout=.5)
            except subprocess.TimeoutExpired:
                owned.observe()
                if time.monotonic()-announcement>=15:
                    s=monitor.guard.samples[-1]
                    print(json.dumps(dict(stage=monitor.stage,elapsed_seconds=time.monotonic()-started,
                        system_CPU=s['system_cpu_percent'],available_RAM_percent=s['available_ram_percent'])),flush=True)
                    announcement=time.monotonic()
                continue
            markers,observations=capture.progress();monitor.accept(markers,owned);owned.observe()
            row['owned'].update(exit_code=owned.returncode,markers=markers,marker_observations=observations,
                child_summary=json.loads(stdout.splitlines()[-1]),stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()))
            require(owned.returncode==0,'ACTUAL_READONLY_CHILD_FAILED_NO_RETRY')
            break
        cleanup_owned(owned,capture,row['owned'],None);owned=capture=None
        require(row['owned']['cleanup'] and monitor.seen==4,'FOUR_PHASES_AND_KNOWN_EMPTY_JOB')
        result=row['owned']['child_summary'];proof=a.read_exact(q,result['receipt'])
        require(proof['state']=='PASS_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE'
            and proof['cleanup_confirmed'] and len(proof['epochs'])==4 and proof['process_creation_attempts']==0
            and not proof['actual_Native_Frame_created'] and not proof['actual_product_executed'],
            'EXACT_ACTUAL_METADATA_NOT_NATIVE_OR_PRODUCT')
        for pin in proof['source_pins']:a.exact(q.pin(pin['path']),pin,'ACTUAL_CONSTRUCTION_SOURCE_POSTCHECK')
        q.finish();monitor.check(force=True)
        row.update(state='PASS_OWNED_NATIVE011_ACTUAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE',
            child_receipt=result['receipt'],metadata=proof['metadata'],whole_batch=proof['whole_batch'],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_Native_Frame_or_product_qualified=False,official_accepted_count=158,remaining_cases=91)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,ArithmeticError,subprocess.SubprocessError) as error:
        primary=error;row['failure']=failure_record(error,[] if monitor.guard is None else monitor.guard.samples)
    finally:
        if owned is not None or capture is not None:cleanup_owned(owned,capture,row['owned'],primary)
        elif not row['owned']['constructor_entered']:cleanup_owned(None,None,row['owned'],primary)
        monitor.close();row.update(epochs=monitor.records,
            cleanup=all(r['cleanup_confirmed'] for r in monitor.records) and row['owned']['cleanup'],
            source_pins=[] if q is None else list(q.snapshots.values()),elapsed_seconds=time.monotonic()-started)
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],failure=row.get('failure'),cleanup=row['cleanup'],
            stage=monitor.stage,phases_seen=monitor.seen,elapsed=row['elapsed_seconds'],
            child=row['owned'].get('child_summary'),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
