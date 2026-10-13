"""Current r04 per-case pipe diagnostic, original360s, never full acceptance.

Keep original unfiltered249 and guards. Use adaptive native queries rather
than reintroducing every-second Process-array collection during diagnosis.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_current_graph_cost as prior
import run_adaptive_source_xml_full as full
import adaptive_host_cpu_sampler as adaptive

p=full.p
old=prior.old
SELF='tools/p09/run_source_xml_stored_cost.py'
TEST='tools/p09/tests/test_source_xml_stored_cost.py'
PARENT=dict(path='implementation/p09/evidence/p09-165-adaptive-source-xml-full.terminal-audit-run01.v1.json',
    bytes=386991,sha256='319ee52b7251ed48272c409daebe4b3470a6803b5aeb1d7cdbd92024c4124eb1')
RUN=4
MAXIMUM_SECONDS=360

def require(ok,code):full.require(ok,'COST_'+code)

def worker(task):
    require(task==old.task_for(RUN),'CURRENT_TASK')
    with patch.object(prior,'RUN',RUN),patch.object(old.s,'observed_call',adaptive.observed_call):
        return prior.worker(task)

def parent_scope(row):
    require(row['state']=='PASS_CURRENT_ADAPTIVE_SOURCE_XML_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
        and row['source_closing_exact'] and row['contract_tests_passed']==97
        and row['current_compiled249_qualified'] and row['current_Rust_input_count']==785
        and row['protected_EXE_inputs_exact']==64 and row['actual_tests_passed'] is None
        and row['original_stop_reason']=='STOP_DURATION_LIMIT' and row['original_run_state']=='STOPPED_NOT_ACCEPTED'
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],
        'CURRENT_STOP_NOT_PASS')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1309);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R04')
    return expected,exe

def contracts():
    prior.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_adaptive_host_cpu_sampler','test_source_xml_product_full','test_adaptive_source_xml_full',
         'test_source_xml_stored_cost'))
    with patch('subprocess.Popen',side_effect=AssertionError('P166_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P166_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P166_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==32 and not result.skipped,'CONTRACT32_PLUS80')
    return dict(contract_tests_run=112,contract_tests_passed=112)

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_STOP_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL249_59')
        contracts()
        for n in (*p.helpers(),SELF,TEST,prior.SELF,prior.TEST,old.SELF,old.TEST,adaptive.SELF,
                'tools/p09/stored_cost_observation.py',PARENT['path'],full.SELF,full.TEST):expected[n]=q.pin(n)
        # Test modules imported by contracts are part of this dispatcher closure.
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=p.c.Path(file).resolve()
                if path.is_relative_to(p.c.ROOT/'tools/p09') and path.suffix=='.py':
                    n=path.relative_to(p.c.ROOT).as_posix();expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run_owned(destination,binding):
    dump=json.dump
    def write(row,stream,**kw):
        row.update(schema_version='hwpx-agent.p09-source-xml-adaptive-case-cost/v1',
            adaptive_native_diagnostic_callback=True,source_xml_stop_closing_pin=PARENT,
            legacy_total_samples_counts_host_polls=True,native_cold_periods_explicitly_not_observed=True,
            actual_adaptive_counts_unverified_without_footer=True,
            source_XML_current_r04_not_previous_r03=True)
        return dump(row,stream,**kw)
    with patch.object(prior,'RUN',RUN),patch.object(prior,'SELF',SELF),patch.object(prior,'PARENT',PARENT), \
            patch.object(old.s,'Capture',adaptive.Capture),patch.object(json,'dump',write):
        return prior.run_owned(destination,binding)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    a=parser.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-166-source-xml-stored-cost.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':return run_owned(destination,load_binding())
    resources=p.s.SQLRuntimeResources();out={};q=None
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,prior.SELF,prior.TEST,old.SELF,old.TEST,adaptive.SELF,
                'tools/p09/stored_cost_observation.py',full.SELF,full.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_CURRENT_SOURCE_XML_ADAPTIVE_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            source_closing_exact=True,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,P09_gate='OPEN',actual_EXE_SQL_native_or_child_started=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=full.s.original.closed_error(e))
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,old.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=full.s.original.closed_error(e))))
        raise SystemExit(2) from None
