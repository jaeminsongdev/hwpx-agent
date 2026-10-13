"""P183 own-parent CPU and closed protected-file context for existing readonly IO.

No new sampler/thread/foreign PID, rate change, cache, removed read or deadline.
The next whole preparation must explicitly select these classes; this probe
does not run that preparation or qualify a product/list/CPU freeze cause.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import pre_go_parent_cpu_observer_r2 as observer
import weighted_audit_io as weighted
from sql_runtime_supervision import SQLRuntimeResources as OriginalResources, finish_watcher
from sql_owned_execution import scoped_path
c=observer.prior.c
SELF='tools/p09/readonly_parent_file_observation.py'
TEST='tools/p09/tests/test_readonly_parent_file_observation.py'

class ObservedResources(OriginalResources):
    def __init__(self):super().__init__(windows=observer.RAW_PARENT())

class TraceReader(weighted.WeightedReader):
    def __init__(self,*args,protected=(),**kw):
        super().__init__(*args,**kw)
        c.require(all(isinstance(n,str) and n.endswith('.exe') for n in protected),'READONLY_EXE_ALLOWLIST_ONLY')
        self.protected=frozenset(protected);self.active=None;self.completed=None;self.interrupted=None
    def _read(self,name,parse=False):
        self.active=name
        try:
            result=super()._read(name,parse=parse);self.completed=name;return result
        except (ValueError,OSError):self.interrupted=name;raise
        finally:self.active=None
    def closed(self,name):return name if name in self.protected else None
    def context(self):
        return dict(last_completed_protected_EXE_path=self.closed(self.completed),
            interrupted_protected_EXE_path=self.closed(self.interrupted),
            arbitrary_source_paths_or_private_artifact_names_saved=False,
            every_original_fresh_read_and_guard_preserved=True)

class ObservedReader(weighted.WeightedLiveReader):
    def __init__(self,resources,protected=()):
        super().__init__(resources)
        self.reader=TraceReader(self.reader.root,self.checkpoint,self.reader.maximum_parse_bytes,protected=protected)
    def summary(self):
        row=super().summary();row['protected_file_read_context']=self.reader.context();return row

def parent_tail(resources):
    with resources.lock:rows=list(resources.samples[-8:]);count=len(resources.samples)
    fields=('time_utc','system_cpu_percent','available_ram_percent','commit_used_percent',
        'parent_cpu_machine_percent','parent_cpu_delta_100ns','raw_system_cpu_delta_100ns',
        'parent_affinity_mask','parent_priority_readback','parent_process_only','foreign_Process_query_executed')
    c.require(all(all(k in r for k in fields) for r in rows),'READONLY_PARENT_SAMPLES_COMPLETE')
    return dict(original_completed_sample_count=count,tail_limit=8,existing_samples_only=True,
        extra_sampler_thread_started=False,foreign_Process_query_executed=False,
        samples=[{k:r[k] for k in fields} for r in rows])

def contracts():
    observer.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_readonly_parent_file_observation')
    with patch('subprocess.Popen',side_effect=AssertionError('P183_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P183_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P183_NO_NEW_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    c.require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'READONLY_OBSERVER_CONTRACT7_PLUS4')
    return dict(contract_tests_passed=11)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','observe'),required=True);mode=ap.parse_args().mode
    c.require(c.Path.cwd().resolve()==c.ROOT,'READONLY_OBSERVER_CWD')
    destination=scoped_path(f'implementation/p09/evidence/p09-183-readonly-parent-file-observation.{mode}-run01.v1.json',fresh=True)
    resources=ObservedResources() if mode=='observe' else OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        whole_listing_preparation_executed=False,protected_EXE_workload_executed=False,
        actual_Cargo_SQL_Hangul_child_or_product_EXE_executed=False,
        own_parent_Process_query_executed=mode=='observe',foreign_Process_query_executed=False,
        additional_sampler_thread_started=False,original_resource_guards_and_rates_preserved=True)
    try:
        resources.admit();q=ObservedReader(resources) if mode=='observe' else weighted.WeightedLiveReader(resources)
        out.update(contracts())
        for n in (SELF,TEST,observer.SELF,observer.TEST):q.pin(n)
        q.finish();out.update(state='PASS_READONLY_PARENT_FILE_PROBE_ONLY_NOT_WHOLE_LISTING_OR_CAUSE' if mode=='observe'
            else 'PASS_READONLY_PARENT_FILE_CONTRACT11_ONLY_NOT_ACTUAL_OR_CAUSE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'READONLY_OBSERVER_REDACTED_FAILURE'
        import re
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code or '') else 'READONLY_OBSERVER_REDACTED_FAILURE'
    finally:
        finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if mode=='observe':out['parent_observation_tail']=parent_tail(resources)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
