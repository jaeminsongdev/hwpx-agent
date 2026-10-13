"""P180 original r07 build with current-parent CPU and bounded protected-file context."""
import argparse
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_xml_capacity_product_r3 as inventory
import pre_go_parent_cpu_observer_r2 as observer
base=inventory.prior.prior
driver=inventory.prior
SELF='tools/p09/build_parent_observed_xml_product.py'
TEST='tools/p09/tests/test_parent_observed_xml_product.py'
LIGHT='implementation/p09/evidence/p09-180-parent-observed-xml-product.light-run01.v1.json'
PREPARATION='implementation/p09/evidence/p09-180-parent-observed-xml-product.preparation-run01.v1.json'
ACTUAL='implementation/p09/evidence/p09-180-parent-observed-xml-product.actual-run01.v1.json'
RAW_RUN=base.run_owned

def helpers():return sorted(set(inventory.helpers())|{SELF,TEST,observer.SELF,observer.TEST,
    'tools/p09/pre_go_parent_cpu_observer.py','tools/p09/tests/test_pre_go_parent_cpu_observer.py',
    'implementation/p09/evidence/p09-178-owned-hash-pressure.actual-run01.v1.json',
    'implementation/p09/evidence/p09-178-owned-hash-pressure.preparation-run01.v1.json',
    'implementation/p09/evidence/p09-179-parent-cpu-observer.light-run01.v1.json',
    'implementation/p09/evidence/p09-179-parent-cpu-observer.observe-run01.v1.json',
    'implementation/p09/evidence/p09-179-parent-cpu-observer.light-r2-run01.v1.json',
    'implementation/p09/evidence/p09-179-parent-cpu-observer.observe-r2-run01.v1.json'})

def contracts():
    inventory.contracts();observer.contracts();sys.path.insert(0,str(base.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_parent_observed_xml_product')
    with patch('subprocess.Popen',side_effect=AssertionError('P180_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P180_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P180_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    base.require(result.wasSuccessful() and result.testsRun==2 and not result.skipped,'CONTRACT262_PLUS7_PLUS2')
    return dict(contract_tests_passed=271,contract_tests_run=271)

def observed_run(destination,binding):
    traces=[];dump=json.dump;original_io=base.weighted;protected={p['path'] for p in binding[1]}
    class TraceReader(original_io.WeightedReader):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.active=None;self.completed=None;self.interrupted=None;traces.append(self)
        def _read(self,name,parse=False):
            self.active=name
            try:
                result=super()._read(name,parse=parse);self.completed=name;return result
            except (ValueError,OSError):self.interrupted=name;raise
            finally:self.active=None
    class IO:
        WeightedReader=TraceReader
        WeightedLiveReader=original_io.WeightedLiveReader
        BINARY_RATE=original_io.BINARY_RATE
        OTHER_RATE=original_io.OTHER_RATE
        resource_tail=staticmethod(original_io.resource_tail)
    def closed_path(name):return name if name in protected and name.endswith('.exe') else None
    def write(row,stream,**kw):
        samples=[s for s in row.get('samples',[]) if 'parent_cpu_machine_percent' in s]
        row.update(parent_ProcessTimes_observation_connected=True,parent_ProcessTimes_query_executed=True,
            foreign_Process_query_executed=False,native_Process_query_executed=True,
            additional_process_query_or_thread=True,additional_observer_thread_started=False,
            additional_Process_query_scope='current_parent_pseudo_handle_only',PC_freeze_cause_qualified=False,
            parent_CPU_observed_samples=len(samples),parent_CPU_max_machine_percent=
                max((s['parent_cpu_machine_percent'] for s in samples),default=None),
            protected_file_read_context=[dict(read_passes=r.read_passes,bytes_read=r.bytes_read,
                last_completed_protected_EXE_path=closed_path(r.completed),interrupted_protected_EXE_path=closed_path(r.interrupted),
                arbitrary_source_paths_or_private_artifact_names_saved=False) for r in traces])
        return dump(row,stream,**kw)
    with patch.object(base.c,'Windows',observer.RAW_PARENT),patch.object(base,'weighted',IO),patch.object(json,'dump',write):
        return RAW_RUN(destination,binding)

def worker(task):return inventory.worker(task)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual'),required=True);mode=ap.parse_args().mode
    base.require(base.c.Path.cwd().resolve()==base.c.ROOT,'P180_CWD')
    if mode=='actual':
        destination=base.s.scoped_path(ACTUAL,fresh=True);base.fresh_scope({})
        with contextlib.ExitStack() as stack:
            for name,value in (('SELF',SELF),('PREPARATION',PREPARATION),('ACTUAL',ACTUAL),('helpers',helpers),('contracts',contracts)):
                stack.enter_context(patch.object(base,name,value))
            stack.enter_context(patch.object(base,'weighted',driver.pressure))
            return observed_run(destination,base.load_binding())
    destination=base.s.scoped_path(LIGHT,fresh=True);resources=base.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        parent_observed_actual_build_executed=False,actual_Cargo_native_SQL_Hangul_or_child_started=False,
        PC_freeze_resolved=False,foreign_Process_query_executed=False)
    try:
        resources.admit();q=driver.pressure.WeightedLiveReader(resources);out.update(contracts())
        for n in helpers():q.pin(n)
        q.finish();out.update(state='PASS_PARENT_OBSERVED_R07_BUILD_CONTRACTS_ONLY_NOT_ACTUAL_OR_CAUSE',source_closing_exact=True,
            compile_recipe=base.recipe(),owned_hash_rates={'binary':1048576,'other':2097152},
            observed_parent_only=True,original_resource_guards_unchanged=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=base.parser.d.original.closed_error(error)
    finally:
        base.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    raise SystemExit(main())
