"""New read-only product binding + ten focused tests; never Native or old249 replay."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_inline_receipt567 as layout
import crossref_lossless_receipt610 as receipt
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_native_startup as startup
SELF='tools/p09/verify_bookmark_command_bindings614.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-command-product614-audit001.v1.json'
EXAMPLE='crates/product-cli/examples/p09_bookmark_command_bindings613.rs'
EXE='target/debug/examples/p09_bookmark_command_bindings613.exe'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
PREPARED='implementation/p09/evidence/p09-361-bookmark-binding-corpus613-preparation.v1.json'
CHANGED={'crates/hwpx-package/src/document_import/fields.rs':('fields.rs','pub mod bookmark_crossref;\n'),
    'crates/product-cli/src/reference_validation_product/source_crossref.rs':('source_crossref.rs','pub mod bookmark_bindings;\n')}

def readonly_product(guard,env,row,args):
    owned=capture=None;started=time.monotonic();step=dict(stage='fixed010_readonly_public_product',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<120,'P614_READONLY_PRODUCT_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(line.startswith(('error','warning'))for line in err.splitlines()),'P614_ACTUAL_READONLY_PRODUCT_NO_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='source_bookmark_bindings_derived_from_fixed010_not_native_or_gate'
            and result['actual_native_started']is False and result['existing_native_replayed']is False and result['p09_complete']is False
            and len(result['observations'])==24,'P614_ACTUAL24_RESULT')
        step['product_result']=result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)
    return step['product_result']

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-readonly-product'],'P614_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P614_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=None;started=time.monotonic();row=dict(state='FAILED614_BOOKMARK_SOURCE_BINDINGS',steps=[],own_cpu_selection=selection,
        actual_Hancom_COM_or_Native_started=False,existing_native_probes_or_passed249_tests_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_target_resolution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prepared=layout.unpack(q.json(PREPARED));corpus=q.json(CORPUS)
        c.require(q.snapshots[PREPARED]['sha256']=='5a332a31702ceb4e8e75c0bcfce1e9af19d3b151e353ed922357faff56fd6c49'
            and prepared['state']=='PASS613_FIXED_CAPTURE010_CORPUS_PREPARED_NOT_COMPILED_OR_GATE'
            and prepared['fresh_inputs']==prepared['final_fresh_hashes']==47 and prepared['cleanup']is True,'P614_EXACT_CLOSED613_DATA_NOT_CLI_EXIT_PROMOTION')
        c.require(q.pin(CORPUS)==prepared['corpus']and q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P614_FIXED_CORPUS')
        row['preparation_cli_prefix_exit_defect_preserved_and_source_fixed']=True
        archive='implementation/p09/source-archive/p361-bookmark-binding613/prepare_bookmark_binding_corpus613.py'
        old_pin=next(p for p in prepared['source_pins']if p['path']=='tools/p09/prepare_bookmark_binding_corpus613.py')
        c.require(q.pin(archive)['sha256']==old_pin['sha256'],'P614_ORIGINAL_PREPARATION_SOURCE_ARCHIVED')
        for source,(archive_name,insertion)in CHANGED.items():
            path='implementation/p09/source-archive/p361-bookmark-binding613/'+archive_name
            c.require(q.text(source).replace(insertion,'',1).rstrip()==q.text(path).rstrip(),'P614_ADDITIVE_MODULE_ONLY_WHOLE_ORIGINAL_PARENT_BODY_UNCHANGED')
        names=inventory.inventory(guard)|includes.test_inputs((EXAMPLE,),guard)|{SELF,CORPUS,PREPARED,archive,
            'tools/p09/crossref_lossless_receipt610.py','tools/p09/prepare_bookmark_binding_corpus613.py',
            *['implementation/p09/source-archive/p361-bookmark-binding613/'+value[0]for value in CHANGED.values()]}
        for pin in[corpus['source'],*[pin for case in corpus['cases']for pin in case['artifacts'].values()]]:
            c.require(q.pin(pin['path'])==pin,'P614_FRESH_CAPTURED25_PACKAGES');names.add(pin['path'])
        for name in sorted(names):q.pin(name)
        # Pin consumed010 probe without rebuilding it. The new example has its own name.
        old_probe='target/debug/examples/p09_crossref_capture010_probe.exe';old=q.pin(old_probe)
        c.require(old['bytes']==5152256 and old['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P614_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P614_NO_PREEXISTING_HWP')
        expected={'tests::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(EXAMPLE))}
        c.require(len(expected)==10 and '#[ignore]'not in q.text(EXAMPLE),'P614_TEN_NEW_CASES_NO_SUBSET')
        scratch=c.ROOT/'target/p09-bookmark-bindings614-scratch';c.require(not scratch.exists(),'P614_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        example='p09_bookmark_command_bindings613';common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',example,'--features','p09-installed-format-fixture','--message-format=short']
        print(json.dumps(dict(state='BOOKMARK614_FRESH_SOURCE_PREFLIGHT',inputs=len(q.snapshots),new_cases=10,captured_outputs=24,Native_authorized=False)),flush=True)
        r.harness.run_one('new_bookmark_source_binding10',[r.harness.CARGO,'test',*common,'--',*sorted(expected),'--exact','--test-threads=1'],expected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],expected);c.require(not row['steps'][-1]['diagnostics'],'P614_TEST_NO_WARNINGS')
        r.harness.run_one('new_bookmark_readonly_example_build',[r.harness.CARGO,'build',*common],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P614_BUILD_NO_WARNINGS')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);binary=artifact.pin(EXE);dep='target/debug/examples/'+example+'.d';artifact.pin(dep)
        declared=deps.dependencies(c.ROOT/dep);c.require({EXAMPLE,CORPUS}<=declared and declared<=set(q.snapshots),'P614_ALL_COMPILED_INPUTS_PREPINNED')
        result=readonly_product(guard,env,row,[r.harness.CARGO,'run',*common,'--','--fixed-captured-readonly'])
        c.require(len(result['observations'])==24 and not startup.hwp_pids(guard.windows,guard.check),'P614_NO_HWP_AFTER_ACTUAL_PRODUCT')
        c.require(not any(scratch.iterdir()),'P614_SCRATCH_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_PRODUCT_SOURCE_BOOKMARK_COMMAND_BINDINGS10_AND_CAPTURED24_NOT_NATIVE_OR_GATE',
            new_tests=10,actual_captured_outputs=24,compiled_binary=binary,compiled_input_count=len(declared),
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,public_product_method='read_source_bookmark_crossrefs',
            typed_display_hyperlink_and_source_bookmark_resolution=True,old_source_observation_meanings_or_native_approval_not_promoted=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P614_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(row,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','new_tests','actual_captured_outputs','compiled_binary','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),
                diagnostics=v.get('diagnostics'),locations=v.get('locations'),safe_error_variants=v.get('safe_error_variants'))for v in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())
