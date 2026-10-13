"""P179 own-parent CPU/raw system deltas; no child/file workload or foreign PID query."""
import argparse
import ctypes
from ctypes import wintypes as w
import io
import json
import math
import sys
import time
import unittest
from unittest.mock import patch
import conservative_maintenance as c
import weighted_audit_io as evidence
from sql_owned_execution import scoped_path
SELF='tools/p09/pre_go_parent_cpu_observer.py'
TEST='tools/p09/tests/test_pre_go_parent_cpu_observer.py'
DOC='https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes'

class ParentCPUWindows(c.Windows):
    def __init__(self):
        super().__init__()
        fn=self.k.GetProcessTimes
        fn.argtypes=[w.HANDLE]+[ctypes.c_void_p]*4;fn.restype=w.BOOL
        self.own_last=self.own_times()
        allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
        c.require(self.k.GetProcessAffinityMask(self.k.GetCurrentProcess(),ctypes.byref(allowed),ctypes.byref(system))
            and allowed.value==self.mask and self.mask.bit_count()==1
            and self.k.GetPriorityClass(self.k.GetCurrentProcess())==0x4000,'PARENT_READBACK_NOT_EXACT')
    def own_times(self):
        values=[ctypes.c_uint64() for _ in range(4)]
        c.require(self.k.GetProcessTimes(self.k.GetCurrentProcess(),*(ctypes.byref(v) for v in values)),
            'PARENT_CPU_SAMPLE_FAILED')
        return values[2].value,values[3].value
    def sample(self):
        before=self.last;row=super().sample();after=self.last
        own=self.own_times();own_delta=sum(own)-sum(self.own_last);self.own_last=own
        delta=tuple(b-a for a,b in zip(before,after));total=delta[1]+delta[2]
        c.require(len(delta)==3 and all(type(v) is int and v>=0 for v in delta)
            and total>0 and delta[0]<=total and own_delta>=0,'PARENT_CPU_RAW_COUNTER_INVALID')
        value=100*own_delta/total
        c.require(math.isfinite(value) and 0<=value<=100,'PARENT_CPU_RATIO_INVALID')
        row.update(parent_cpu_machine_percent=round(value,6),parent_cpu_delta_100ns=own_delta,
            raw_system_cpu_delta_100ns=dict(idle=delta[0],kernel_including_idle=delta[1],user=delta[2],total=total),
            parent_affinity_mask=self.mask,parent_priority_readback='BelowNormal',
            parent_process_only=True,foreign_Process_query_executed=False)
        return row

def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_pre_go_parent_cpu_observer')
    with patch('subprocess.Popen',side_effect=AssertionError('P179_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P179_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P179_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    c.require(result.wasSuccessful() and result.testsRun==5 and not result.skipped,'PARENT_CPU_CONTRACT5')
    return dict(contract_tests_passed=5)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','observe'),required=True);mode=ap.parse_args().mode
    c.require(c.Path.cwd().resolve()==c.ROOT,'PARENT_CPU_CWD')
    destination=scoped_path(f'implementation/p09/evidence/p09-179-parent-cpu-observer.{mode}-run01.v1.json',fresh=True)
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        parent_ProcessTimes_query_executed=mode=='observe',foreign_Process_query_executed=False,
        child_SQL_native_Hangul_or_Cargo_executed=False,new_sampler_thread_started=False,
        artifact_EXE_read_workload_started=False,original_policy=dict(c.POLICY),GetSystemTimes_official_reference=DOC,
        samples=[],resource_stop_reason=None,cleanup_confirmed=True)
    windows=None;reader=None;hot=0
    try:
        out.update(contracts());windows=ParentCPUWindows() if mode=='observe' else c.Windows()
        def checkpoint():
            nonlocal hot
            row=windows.sample();hot,reason=c.decision(row,hot);out['samples'].append(row)
            c.require(reason is None,reason or 'PARENT_CPU_RESOURCE_STOP')
        reader=evidence.WeightedReader(c.ROOT,checkpoint)
        for n in (SELF,TEST):reader.fresh_pin(n)
        if mode=='observe':
            # Eight completed original half-second observations. No synthetic
            # busy loop, binary scan, arbitrary wait extension or new thread.
            for _ in range(8):time.sleep(c.POLICY['sample_seconds']);checkpoint()
        reader.finish();out.update(source_closing_exact=True,
            state='PASS_OWN_PARENT_CPU_BASELINE_ONLY_NOT_BUILD_OR_CAUSE' if mode=='observe'
                else 'PASS_OWN_PARENT_CPU_FIXTURES_ONLY_NOT_ACTUAL_OR_CAUSE')
        if mode=='observe':out.update(host_CPU_max_percent=max(s['system_cpu_percent'] for s in out['samples']),
            own_parent_CPU_max_percent=max(s['parent_cpu_machine_percent'] for s in out['samples']),
            available_RAM_min_percent=min(s['available_ram_percent'] for s in out['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'PARENT_CPU_REDACTED'
        out['resource_stop_reason']=code if code.replace('_','').isalnum() else 'PARENT_CPU_REDACTED'
        out['state']='FAILED_NOT_ACCEPTED'
    finally:
        if reader is not None:out.update(bound_input_pins=list(reader.snapshots.values()),
            fresh_hashes=reader.final_fresh_hashes,read_passes=reader.read_passes,bytes_read=reader.bytes_read)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','host_CPU_max_percent',
            'own_parent_CPU_max_percent','available_RAM_min_percent','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
