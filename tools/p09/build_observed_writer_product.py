"""P171 fresh r06: validated bounded Cargo progress, unchanged owned guards."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_writer_xml_product as d
import validated_compiler_progress_r2 as progress

c=d.c; s=d.s; b=d.b
SELF='tools/p09/build_observed_writer_product.py'
TEST='tools/p09/tests/test_observed_writer_product.py'
RUN=6
PARENT=dict(path='implementation/p09/evidence/p09-169-writer-xml-product-build.terminal-audit-run01.v1.json',
    bytes=310589,sha256='ff7e1d9dc16d9e26e138bdf58b5e73df7ddf89ac2722588e02c217e5619a28a6')
WRITER_PARENT=dict(d.PARENT)
PASS='PASS_OBSERVED_WRITER_PRODUCT_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
CONTRACT_COUNT=202
RAW_CONTRACTS=d.contracts
RAW_HELPERS=d.helpers
RAW_PARSE=b.parse_build
RAW_COMMAND=b.legacy.stream.run_command
RAW_CAPTURE=b.legacy.original.capture.FullCapture

def require(ok,code):d.require(ok,'OBSERVED_'+code)

def parent_scope(row):
    require(row['state']=='PASS_WRITER_XML_PRODUCT_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE'
        and row['source_closing_exact'] and row['contract_tests_passed']==178
        and row['current_Rust_input_count']==785 and row['current_source_test_count']==249
        and row['current_source_module_instance_count']==59 and row['protected_executables_exact']==65
        and row['writer_xml_delta_closing_pin']==WRITER_PARENT
        and row['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and row['original_source_final_hash_not_retroactively_promoted']
        and not row['current_build_accepted'] and row['resource_stop_reason'] is None
        and row['resource_watcher_cleanup_confirmed']
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','STOP_PARENT_SCOPE')
    expected=s.inputs.inventory(row['bound_input_pins'],1333)
    protected={n:pin for n,pin in expected.items() if n.endswith('.exe')}
    require(len(protected)==65,'PROTECTED65')
    return expected,protected

def progress_command(args,kw,validator):
    require(args[1:]==d.recipe()['argv_without_cargo'],'EXACT_COMMAND')
    # Do not patch b.CargoStream: r2 delegates dynamically to that ORIGINAL class.
    with patch.object(b.legacy.stream,'CargoStream',progress.CargoStream):
        return RAW_COMMAND(args,kw,validator)

def worker(task):
    require(task==b.task_for(RUN),'CLOSED_WORKER')
    with patch.object(b,'TARGET',d.TARGET),patch.object(c,'TARGET',d.TARGET), \
            patch.object(b.legacy.stream,'run_command',progress_command):
        return b.worker(task)

def observe_capture(capture):
    with capture.lock:text=bytes(capture.buffers['stderr']).decode('utf-8',errors='replace')
    return progress.prior.observe(text)

def require_closed(observation):
    require(observation['closing_observed'] and observation['partial_marker_bytes']==0
        and any(r['kind']=='artifact' and r['group']=='product-libtest'
            for r in observation['records']),'COMPLETE_PROGRESS_REQUIRED')

def contracts():
    # Historical r05 fixture contracts keep their own generation while the
    # new binding is r06. Never reinterpret old fixture expectations as r06.
    with patch.object(d,'RUN',5):RAW_CONTRACTS()
    progress.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_writer_product')
    with patch('subprocess.Popen',side_effect=AssertionError('P171_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P171_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P171_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==8 and not result.skipped,'CONTRACT8_PLUS194')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)

def helpers():return sorted(set(RAW_HELPERS())|{SELF,TEST,PARENT['path'],progress.SELF,progress.TEST,
    progress.prior.SELF,progress.prior.TEST,'tools/p09/archive_observed_writer_inputs.py',
    'implementation/p09/source-archive/p09-171-initial-fixture-and-documents-r50/preimages.v1.json',
    'tools/p09/archive_observed_writer_binding_failure.py',
    'implementation/p09/source-archive/p09-171-pre-binding-fixture-fix-r50/preimages.v1.json'})

def load_binding():
    s.scoped_path(d.TARGET.relative_to(c.ROOT).as_posix()+'/debug/deps/form_stored_provider-p152-r06.exe',fresh=True)
    with patch.object(d,'RUN',RUN),patch.object(d,'PARENT',PARENT),patch.object(d,'parent_scope',parent_scope), \
            patch.object(d,'contracts',contracts),patch.object(d,'helpers',helpers):
        return d.load_binding()

def run_owned(destination,binding):
    captures=[];dump=json.dump
    class ObservedCapture(RAW_CAPTURE):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
        def diagnostics(self):
            row=super().diagnostics()
            row['validated_compiler_progress']=observe_capture(self)
            return row
    def validated_parse(output,run,*,require_stream=False):
        result=RAW_PARSE(output,run,require_stream=require_stream)
        require(len(captures)==1,'ONE_PARENT_CAPTURE')
        require_closed(observe_capture(captures[0]))
        return result
    def write(row,stream,**kw):
        if row.get('state')==d.PASS:row['state']=PASS
        row.update(schema_version='hwpx-agent.p09-observed-writer-product-build/v1',
            writer_xml_delta_closing_pin=WRITER_PARENT,previous_build_stop_closing_pin=PARENT,
            bounded_validated_compiler_progress_connected=True,additional_process_query_or_thread=False,
            original_complete_Cargo_validation_preserved=True)
        return dump(row,stream,**kw)
    with patch.object(d,'RUN',RUN),patch.object(d,'SELF',SELF),patch.object(d,'PARENT',PARENT), \
            patch.object(b,'parse_build',validated_parse), \
            patch.object(b.legacy.original.capture,'FullCapture',ObservedCapture),patch.object(json,'dump',write):
        return d.run_owned(destination,binding)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    generation='04' if mode=='light' else '01'
    destination=s.scoped_path(f'implementation/p09/evidence/p09-171-observed-writer-product-build.{mode}-run{generation}.v1.json',fresh=True)
    if mode=='actual':return run_owned(destination,load_binding())
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        for n in helpers():q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_OBSERVED_WRITER_BUILD_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE',
            actual_Cargo_SQL_native_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=d.writer.b.prior.d.original.closed_error(e))))
        raise SystemExit(2) from None
