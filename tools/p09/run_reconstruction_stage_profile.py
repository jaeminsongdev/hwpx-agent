"""Complete36 fresh reconstruction numeric diagnostic in unchanged owned Job."""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import bounded_process_progress as bounded
import run_algorithm_dependency_signed_tests as profile
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher
from live_sql_evidence_reader import LiveSQLReader

SELF='tools/p09/run_reconstruction_stage_profile.py'
TEST='tools/p09/tests/test_reconstruction_stage_profile.py'
EXAMPLE='crates/hwpx-package/examples/source_formula_evaluation_probe.rs'
ARCHIVE='implementation/p09/source-archive/p09-149-pre-reconstruction-stage-probe-r18/source-preimages.v1.json'
PARENT={'path':'implementation/p09/evidence/p09-149-signed-call-model.summary-run01.v1.json','bytes':13786,'sha256':'0ad5aef3dd430a934a2086650cddea2cf9c274b8d7634ebcc433474148ba2e4f'}
PRIOR={'path':'implementation/p09/evidence/p09-149-signed-artifact-compute.actual-run01.v1.json','bytes':945216,'sha256':'bb759d82a7075d23e049756b83bddeadfcdc36e7d068f11c4085caff0fdc7529'}
TASK='source-reconstruction-stage-profile'
ARGS=['run','--profile','test','-p','hwpx-package','--example','source_formula_evaluation_probe']
DISPATCH='    if matches!(args.as_slice(), [argument] if argument == "--reconstruction-timing-only") {\n        return reconstruction_timing_probe();\n    }\n'
MARKER='// Pure importer diagnostic only. Every iteration freshly imports the full bytes;'
STAGES={'source_import','forms_import','fresh_complete_reconstruction','forms_graph_canonical_sha256'}
QUAL='PURE_COMPLETE36_RECONSTRUCTION_NOT_SIGNED_SQL_NATIVE_OR_GATE'


def require_duration(seconds):
    c.require(type(seconds) is int and 30<=seconds<=180,'RECONSTRUCTION_FINITE_SCOPE')


def default_body_exact(current,old):
    current=current.replace('\r\n','\n');old=old.replace('\r\n','\n')
    c.require(current.count(DISPATCH)==1 and current.count(MARKER)==1
        and current.count('fn reconstruction_timing_probe(')==1,'RECONSTRUCTION_CLOSED_EXTENSION')
    head=current.split(MARKER,1)[0]
    c.require(head.replace(DISPATCH,'',1).rstrip('\n')==old.rstrip('\n'),'RECONSTRUCTION_ORIGINAL_DEFAULT_BODY_DRIFT')


def unique(pairs):
    result={}
    for key,value in pairs:
        c.require(key not in result,'RECONSTRUCTION_DUPLICATE_KEY');result[key]=value
    return result


def validate(output):
    c.require(isinstance(output,str) and len(output.encode())<=4096,'RECONSTRUCTION_OUTPUT_BUDGET')
    row=json.loads(output,object_pairs_hook=unique)
    expected={'schema_version','qualification','originals','whole_graph_receipts_equal','tamper_denied','formula_targets','source_cell_bindings','stages','runtime_signed_consumer_qualified','product_complete','P09_gate'}
    c.require(type(row) is dict and set(row)==expected and row['schema_version']=='hwpx-agent.p09-reconstruction-stage-timing/v1'
        and row['qualification']==QUAL and row['runtime_signed_consumer_qualified'] is False
        and row['product_complete'] is False and row['P09_gate']=='OPEN','RECONSTRUCTION_OUTPUT_SCOPE')
    for key,count in (('originals',36),('whole_graph_receipts_equal',36),('tamper_denied',36),('formula_targets',16),('source_cell_bindings',128)):
        c.require(type(row[key]) is int and row[key]==count,'RECONSTRUCTION_WHOLE_COVERAGE')
    c.require(type(row['stages']) is dict and set(row['stages'])==STAGES,'RECONSTRUCTION_STAGE_COVERAGE')
    for stage in row['stages'].values():
        c.require(type(stage) is dict and set(stage)=={'calls','total_us','min_us','max_us'}
            and all(type(v) is int and 0<=v<=180000000 for v in stage.values()) and stage['calls']==36
            and stage['min_us']<=stage['max_us']<=stage['total_us']
            and stage['min_us']*36<=stage['total_us']<=stage['max_us']*36,'RECONSTRUCTION_STAGE_BOUNDS')
    return row


def load_binding():
    resources=SQLRuntimeResources();resources.admit();q=LiveSQLReader(resources)
    try:
        c.require(q.pin(PARENT['path'])==PARENT and q.pin(PRIOR['path'])==PRIOR,'RECONSTRUCTION_PARENT_PIN_DRIFT')
        parent=q.json(PARENT['path']);prior=q.json(PRIOR['path']);archive=q.json(ARCHIVE)
        c.require(parent['source_closing_exact'] is True and parent['current_Rust_inputs']==783
            and parent['product_complete'] is False and prior['state']=='STOPPED_NOT_ACCEPTED'
            and prior['stop_reason']=='STOP_DURATION_LIMIT' and prior['cleanup_confirmed'] is True
            and prior['owned_tree_empty'] is True,'RECONSTRUCTION_PARENT_SCOPE')
        expected={p['path']:p for p in prior['source_freeze']}
        c.require(len(expected)==len(prior['source_freeze']) and len(archive['files'])==1,'RECONSTRUCTION_PREIMAGE_SCOPE')
        old=archive['files'][0];raw=base64.b64decode(old['base64'],validate=True)
        old_pin={k:old[k] for k in ('path','bytes','sha256')}
        c.require(old_pin==expected[EXAMPLE] and len(raw)==old['bytes'] and hashlib.sha256(raw).hexdigest()==old['sha256'],'RECONSTRUCTION_PREIMAGE_DRIFT')
        default_body_exact(q.text(EXAMPLE),raw.decode('utf-8'))
        expected[EXAMPLE]=q.pin(EXAMPLE)
        for name,pin in expected.items():c.require(q.pin(name)==pin,'RECONSTRUCTION_UNDECLARED_SOURCE_DRIFT')
        for pin in parent['current_helpers']+parent['support_pins']+parent['archive_pins']:
            c.require(q.pin(pin['path'])==pin,'RECONSTRUCTION_PARENT_SUPPORT_DRIFT');expected[pin['path']]=pin
        for name in (SELF,TEST,ARCHIVE,PARENT['path'],PRIOR['path']):expected[name]=q.pin(name)
        q.finish()
        return expected
    finally:
        c.require(finish_watcher(resources,{}),'STOP_BINDING_WATCHER_CLEANUP_FAILED')


def worker():
    real_call=subprocess.call
    def call(args,**kwargs):
        base=[*ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(c.TARGET)]
        c.require(args[1:]==base and kwargs.get('cwd')==c.ROOT and kwargs.get('stdin')==subprocess.DEVNULL,'RECONSTRUCTION_WORKER_SCOPE')
        env=kwargs['env']
        c.require(all(env.get(k)==v for k,v in {'CARGO_BUILD_JOBS':'1','CARGO_PROFILE_TEST_OPT_LEVEL':'0','CARGO_PROFILE_TEST_CODEGEN_UNITS':'16','CARGO_PROFILE_TEST_DEBUG_ASSERTIONS':'true','CARGO_PROFILE_TEST_OVERFLOW_CHECKS':'true','RUST_TEST_THREADS':'1','RUSTUP_AUTO_INSTALL':'0'}.items()),'RECONSTRUCTION_WORKER_CHECKS')
        config=[value for entry in profile.CONFIG for value in ('--config',entry)]
        return real_call([args[0],*config,*args[1:],'--','--reconstruction-timing-only'],**kwargs)
    with patch.object(c,'TASKS',{TASK:ARGS}),patch.object(subprocess,'call',call):return c.worker(TASK)


def run_owned(destination,expected,seconds):
    require_duration(seconds);original_pins=c.pins;original_capture=bounded.BoundedProcessCapture;dump=json.dump;captures=[]
    class Capture(original_capture):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.profile=None;captures.append(self)
        def communicate(self,timeout):
            output,errors=super().communicate(timeout)
            if self.process.returncode==0:self.profile=validate(output)
            return output,errors
    def pins(checkpoint=None):
        actual=original_pins(checkpoint);current={p['path']:p for p in actual}
        c.require(all(current.get(n)==p for n,p in expected.items()),'RECONSTRUCTION_FRESH_INPUT_DRIFT');return actual
    def write(row,stream,**kwargs):
        value=captures[-1].profile if captures else None
        if row['state']=='PASS_SCOPED_NOT_GATE' and value is None:row.update(state='STOPPED_NOT_ACCEPTED',stop_reason='RECONSTRUCTION_RESULT_MISSING')
        row.update(source_variant='example-only-complete36-reconstruction-profile-r18',stage_profile=value,
            default_example_body_exact_after_closed_extension_removal=True,product_sources_or_original_test_assertions_changed=False,
            test_package_profile_config=list(profile.CONFIG),original_owned_resource_policy_changed=False,
            signed16_current_qualified=False,full249_current_qualified=False,exact_CPU_profiler=False,statistical_speedup_proven=False,product_complete=False,P09_gate='OPEN')
        return dump(row,stream,**kwargs)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:ARGS}),patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins),patch.object(bounded,'BoundedProcessCapture',Capture),patch.object(json,'dump',write):
        return c.run(TASK,destination,seconds)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True);parser.add_argument('--light',action='store_true');parser.add_argument('--maximum-seconds',type=int,default=180);args=parser.parse_args();require_duration(args.maximum_seconds)
    c.require(c.Path.cwd().resolve()==c.ROOT,'RECONSTRUCTION_ROOT_SCOPE')
    kind='light' if args.light else 'actual';destination=scoped_path(f'implementation/p09/evidence/p09-149-reconstruction-stage.{kind}-run{args.run:02}.v1.json',fresh=True)
    if not args.light:return run_owned(destination,load_binding(),args.maximum_seconds)
    from tests.test_reconstruction_stage_profile import ReconstructionStageTests
    resources=SQLRuntimeResources();resources.admit();q=LiveSQLReader(resources)
    row={}
    try:
        freeze=[q.pin(n) for n in (SELF,TEST,EXAMPLE,ARCHIVE,PARENT['path'])]
        with patch('subprocess.Popen',side_effect=AssertionError('RECONSTRUCTION_LIGHT_CHILD_FORBIDDEN')),patch('subprocess.run',side_effect=AssertionError('RECONSTRUCTION_LIGHT_CHILD_FORBIDDEN')),patch('threading.Thread.start',side_effect=AssertionError('RECONSTRUCTION_LIGHT_THREAD_FORBIDDEN')):
            result=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReconstructionStageTests))
        failed=sorted({t.id().split('.')[-1] for t,_ in result.failures+result.errors+result.skipped})
        passed=result.testsRun==10 and result.wasSuccessful() and not result.skipped
        q.finish();row.update(state='PASS_RECONSTRUCTION_CONTRACT_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',tests_run=result.testsRun,tests_passed=result.testsRun-len(failed),failed_tests=failed,source_freeze=freeze,source_closing_exact=True,product_complete=False,P09_gate='OPEN',Cargo_SQL_native_executed=False,IO=q.summary())
    finally:
        row['resource_stop']=resources.reason;finish_watcher(resources,row)
    c.require(row['resource_stop'] is None and row['resource_watcher_cleanup_confirmed'],'RECONSTRUCTION_LIGHT_RESOURCE_STOP')
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}))
    return 0 if passed else 2


if __name__=='__main__':
    if sys.argv[1:]==['--owned-worker','--task',TASK]:raise SystemExit(worker())
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z_]+',str(error)) else 'RECONSTRUCTION_OPERATION_FAILED'
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code}));raise SystemExit(2) from None
