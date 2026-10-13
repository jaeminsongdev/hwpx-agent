"""P185 bounded IO yield near host saturation; all fresh reads/guards retained.

Only disk-read checkpoints yield at CPU >=95. Two distinct existing sampler
windows below95 resume IO. Existing98x4/RAM/commit/600s guards still execute.
No normal-load startup threshold, new sampler, skipped read or time extension.
"""
import io
import json
import math
import sys
import time
import unittest
from unittest.mock import patch
import readonly_parent_file_observation as observation
import verify_weighted_audit_io_r2 as original_tests
c=observation.c
SELF='tools/p09/near_saturation_read_backpressure.py'
TEST='tools/p09/tests/test_near_saturation_read_backpressure.py'
WARNING_PERCENT=95
COOL_SAMPLES=2
MAX_PAUSE_WINDOWS=8

class PressureCheckpoint:
    def __init__(self,base,resources,sleep=time.sleep):
        self.base,self.resources,self.sleep=base,resources,sleep
        self.warning_entries=0;self.pause_windows=0;self.maximum_windows_in_one_entry=0
    def latest(self):
        with self.resources.lock:
            c.require(bool(self.resources.samples),'BACKPRESSURE_NO_ORIGINAL_SAMPLE')
            row=self.resources.samples[-1]
        value=row['system_cpu_percent']
        c.require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=100,'BACKPRESSURE_CPU_INVALID')
        return row,value
    def __call__(self):
        # Every original checkpoint still executes, including IO scope expiry
        # and unchanged host emergency decisions, before looking at pressure.
        self.base();row,value=self.latest()
        if value<WARNING_PERCENT:return
        self.warning_entries+=1;cool=windows=0
        while cool<COOL_SAMPLES:
            c.require(windows<MAX_PAUSE_WINDOWS,'STOP_READ_PRESSURE_NOT_COOLING')
            previous=row
            self.sleep(c.POLICY['sample_seconds']);windows+=1;self.pause_windows+=1
            self.maximum_windows_in_one_entry=max(self.maximum_windows_in_one_entry,windows)
            self.base();row,value=self.latest()
            c.require(row is not previous,'BACKPRESSURE_ORIGINAL_SAMPLE_NOT_ADVANCED')
            cool=cool+1 if value<WARNING_PERCENT else 0
    def summary(self):
        return dict(warning_system_CPU_percent=WARNING_PERCENT,cool_distinct_sample_windows=COOL_SAMPLES,
            maximum_pause_windows_per_entry=MAX_PAUSE_WINDOWS,warning_entries=self.warning_entries,
            completed_pause_windows=self.pause_windows,maximum_observed_pause_windows_in_one_entry=self.maximum_windows_in_one_entry,
            requested_pause_seconds=self.pause_windows*c.POLICY['sample_seconds'],
            original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
            original_sampler_windows_reused=True,new_native_query_or_sampler_thread_started=False,
            original_read_checks_skipped=False)

class PressureReader(observation.ObservedReader):
    def __init__(self,resources,protected=()):
        super().__init__(resources,protected=protected)
        self.pressure=PressureCheckpoint(self.reader.checkpoint,resources)
        self.reader.checkpoint=self.pressure
    def summary(self):
        row=super().summary();row['near_saturation_read_backpressure']=self.pressure.summary();return row

def contracts():
    original_tests.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_near_saturation_read_backpressure')
    with patch('subprocess.Popen',side_effect=AssertionError('P185_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P185_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P185_NO_NEW_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    c.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'BACKPRESSURE_ORIGINAL37_PLUS6')
    return dict(contract_tests_passed=43,all_original_reader_oracles_retained=True)

def main():
    c.require(c.Path.cwd().resolve()==c.ROOT,'BACKPRESSURE_CWD')
    destination=observation.scoped_path('implementation/p09/evidence/p09-185-near-saturation-read-backpressure.light-run01.v1.json',fresh=True)
    resources=observation.OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',actual_backpressured_protected_EXE_workload_executed=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        original_resource_guards_and_rates_and_read_coverage_preserved=True)
    try:
        resources.admit();q=observation.weighted.WeightedLiveReader(resources);out.update(contracts())
        for n in (SELF,TEST,observation.SELF,observation.TEST,original_tests.SELF,
            'tools/p09/weighted_audit_io.py','tools/p09/audit_evidence_io.py','tools/p09/live_sql_evidence_reader.py'):q.pin(n)
        q.finish();out.update(state='PASS_NEAR_SATURATION_READ_BACKPRESSURE_CONTRACT43_ONLY_NOT_WORKLOAD_OR_CAUSE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'BACKPRESSURE_REDACTED_FAILURE'
        import re
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code or '') else 'BACKPRESSURE_REDACTED_FAILURE'
    finally:
        observation.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
