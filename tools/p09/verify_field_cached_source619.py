"""Bounded source-cache reader, Source v15 and fixed captured cache observations."""
import hashlib,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
SELF='tools/p09/verify_field_cached_source619.py'
OUTPUT='implementation/p09/evidence/p09-361-field-cached-source619-audit004.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-field-cached-source619-audit004-forensic'
PRIOR='implementation/p09/evidence/p09-361-field-cached-source619-audit002.v1.json'
EXAMPLE='crates/product-cli/examples/p09_field_cached_source619.rs'
SOURCE='crates/product-cli/tests/reference_source_product.rs'
INTEGRATED='crates/product-cli/tests/bookmark_field_semantics616.rs'
PRODUCT='crates/product-cli/tests/reference_field_semantics_product.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-field-cache619/'
MODULES={'joined_caption_state':'caption_state.rs','source_note_selection':'note_selection.rs',
    'source_note_style_selection':'note_style_selection.rs','source_heading_targets':'heading_targets.rs','source_field_meanings617':'field_meanings617.rs'}
def tests(q,path,prefix=''):
    text=q.text(path);r.c.require('#[ignore]'not in text,'P619_NO_IGNORED_TESTS')
    return {prefix+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
def read_only(guard,env,row,args):
    owned=capture=None;begin=time.monotonic();step=dict(stage='actual_fixed010_cache_observations',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P619_FIXED_OBSERVATION_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(line.startswith(('error','warning'))for line in err.splitlines()),'P619_READONLY_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='source_field_cache619_observed_not_native_or_currentness'
            and len(result['observations'])==24 and len(result['saved_reopened_comparisons'])==8
            and result['actual_native_started']is False and result['cache_currentness_qualified']is False and result['P09_complete']is False,'P619_FIXED24_OBSERVATIONS_NOT_NATIVE')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)
def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-source-cache'],'P619_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P619_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=None;row=dict(state='FAILED619_SOURCE_FIELD_CACHES',steps=[],own_cpu_selection=selection,
        actual_Hancom_COM_Native_or_DB_started=False,official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_display_or_cache_currentness_qualified=False,source_schema='v15',field_meaning_schema_unchanged='v2')
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='e73c50abca08d19f674ada033680cd56d76f43bf00713fd3e7581ccf671cd46c'
            and prior['state']=='FAILED619_SOURCE_FIELD_CACHES'and prior['cleanup']is True
            and prior['error_code']=='P619_NORMAL_BUILD_NO_WARNINGS','P619_FAILED002_WARNING_PRESERVED')
        # Compare prior pins after the single initial read of the unified input
        # set, not a second physical preflight pass of the entire source tree.
        retained={name for step in prior['steps']for name,status in step.get('tests',[])if status=='ok'}|set(prior['retained_unit_tests'])
        c.require(len(retained)==104 and all(step['exit_code']==0 and step['cleanup']is True for step in prior['steps'])
            and not any(status!='ok'for step in prior['steps']for _,status in step.get('tests',[])),'P619_ALL104_PASSED_BEFORE_NORMAL_WARNING')
        names=inventory.inventory(guard)|includes.test_inputs((EXAMPLE,SOURCE,INTEGRATED,PRODUCT),guard)|{SELF,CORPUS,
            'tools/p09/metadata_forensic_retention615.py','tools/p09/crossref_lossless_receipt610.py',PRIOR,
            ARCHIVE+'example-audit001.rs',ARCHIVE+'verifier-audit001.py',ARCHIVE+'example-audit002.rs',ARCHIVE+'verifier-audit002.py',
            ARCHIVE+'verifier-audit003.py','implementation/p09/evidence/p09-361-field-cached-source619-audit003.v1.json'}
        names|={pin['path']for pin in prior['source_pins']}
        names|={ARCHIVE+name for name in('fields.rs','source.rs','reference_source_product.rs','reference_field_semantics_product.rs','bookmark_field_semantics616.rs')}
        names|={ARCHIVE+'source-test-modules/'+name for name in MODULES.values()}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P619_FIXED_CORPUS')
        fixed=[corpus['source'],*[pin for case in corpus['cases']for pin in case['artifacts'].values()]]
        for pin in fixed:names.add(pin['path'])
        formulas='implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json';manifest=q.json(formulas);names.add(formulas)
        formula_pins=[case[k]for case in manifest['cases']for k in('input','output')];names|={pin['path']for pin in formula_pins}
        names.add('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        names|={'fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json','implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json'}
        for i,file in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'),1):
            names.add('fixtures/target-build/p09-24-note-target-20261002-03/output/'+file)
            for stage in('saved','reopened'):names.add(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{stage}.hwpx')
        # One initial physical read per already-known input, followed by exact
        # comparisons from that bound reader; one whole physical final audit.
        # Avoid redundantly repinning the same prior inputs again in this pass.
        for name in sorted(names):
            if name not in q.snapshots:q.pin(name)
        for pin in prior['source_pins']:
            if pin['path']not in(SELF,EXAMPLE):c.require(q.snapshots[pin['path']]==pin,'P619_RETAINED9_COMPILED_INPUTS_IDENTICAL')
        text=q.text(EXAMPLE)
        gated='#[cfg(test)]\nuse hwpx_package::document_import::fields::cached_source::SourceFieldCachedInlines;\n'
        c.require(text.count(gated)==1,'P619_ONLY_TEST_TYPE_IMPORT_GATED')
        text=text.replace(gated,'',1).replace('    SourceImportLimits, fields::cached_source::FieldCacheSnapshot,\n',
            '    SourceImportLimits,\n    fields::cached_source::{FieldCacheSnapshot, SourceFieldCachedInlines},\n')
        c.require(text==q.text(ARCHIVE+'example-audit002.rs'),'P619_ALL_TEST_AND_OBSERVER_BODIES_UNCHANGED_IMPORT_ONLY')
        row.update(retained_tests=sorted(retained),retained_test_count=104,retained_test_bodies_reexecuted=False,prior_failed_receipt=q.snapshots[PRIOR])
        for pin in fixed:c.require(q.snapshots[pin['path']]==pin,'P619_FIXED25_PACKAGES')
        for pin in formula_pins:c.require((q.snapshots[pin['path']]['bytes'],q.snapshots[pin['path']]['sha256'])==(pin['bytes'],pin['sha256']),'P619_FORMULA16_EXACT')
        c.require(q.text('crates/hwpx-package/src/document_import/fields.rs').replace('pub mod cached_source;\n','')==q.text(ARCHIVE+'fields.rs'),'P619_FIELD_PARENT_ONLY_NEW_MODULE')
        text=q.text('crates/product-cli/src/reference_validation_product/source.rs').replace('reference-source-assessment/v15','reference-source-assessment/v14')
        for insertion in('use hwpx_package::document_import::fields::cached_source::{SourceFieldCachedInlines,FieldCachedSourceError};\n',
            '    field_cached_source: SourceFieldCachedInlines,\n','    #[must_use]\n    pub const fn field_cached_source(&self) -> &SourceFieldCachedInlines { &self.field_cached_source }\n',
            '        let field_cached_source=SourceFieldCachedInlines::import(&fields,reference_limits).map_err(|error|match error{\n            FieldCachedSourceError::Limit=>ReferenceSourceError::InputLimit,FieldCachedSourceError::Binding=>ReferenceSourceError::FieldRanges})?;\n',
            '            field_cached_source,\n'):
            c.require(text.count(insertion)==1,'P619_EXACT_SOURCE_CACHE_INSERTION');text=text.replace(insertion,'',1)
        c.require(text==q.text(ARCHIVE+'source.rs'),'P619_OTHER_MAIN_SOURCE_BODY_AND_GUARDS_UNCHANGED')
        for current,old in[(SOURCE,'reference_source_product.rs'),(INTEGRATED,'bookmark_field_semantics616.rs'),(PRODUCT,'reference_field_semantics_product.rs'),
            *[('crates/product-cli/tests/reference_source_product/'+name,'source-test-modules/'+name)for name in MODULES.values()]]:
            c.require(q.text(current).replace('reference-source-assessment/v15','reference-source-assessment/v14')==q.text(ARCHIVE+old),'P619_EXISTING_ASSERTIONS_ONLY_SCHEMA_CHANGED')
        new=tests(q,EXAMPLE,'tests::');source=tests(q,SOURCE)
        for prefix,name in MODULES.items():source|=tests(q,'crates/product-cli/tests/reference_source_product/'+name,prefix+'::')
        integrated=tests(q,INTEGRATED);product=tests(q,PRODUCT)
        c.require(tuple(map(len,(new,source,integrated,product)))==(10,79,9,6),'P619_EXACT104_TESTS')
        c.require(new|source|integrated|product==retained,'P619_ALL104_RETAINED_NO_TESTS_LOST')
        old_probe=q.pin('target/debug/examples/p09_crossref_capture010_probe.exe');c.require(old_probe['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P619_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P619_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-field-cache619-audit004-scratch';c.require(not scratch.exists(),'P619_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);row['compiled_inputs']=[]
        for item in prior['compiled_inputs']:
            for entry in item['artifacts']:
                for key in('dep_info','binary'):c.require(artifact.pin(entry[key]['path'])==entry[key],'P619_RETAINED104_COMPILER_ARTIFACTS_UNCHANGED')
                c.require(deps.dependencies(c.ROOT/entry['dep_info']['path'])<=set(q.snapshots),'P619_RETAINED104_ACTUAL_COMPILER_INPUTS_PINNED')
        row['compiled_inputs']=prior['compiled_inputs']
        example='p09_field_cached_source619';common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--message-format=short',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        print(json.dumps(dict(state='P619_FRESH_PREFLIGHT',inputs=len(q.snapshots),new_tests=10,retained_tests=104,current_tests=0,affected_tests=94,total_tests=104,
            actual010_outputs=24,CPU_RAM_guards_unchanged=True)),flush=True)
        for kind,target,cases in []:
            selected=[]if target=='reference_source_product'else sorted(cases)
            build_begin=time.time_ns();r.harness.run_one(target,[r.harness.CARGO,'test',*common,kind,target,'--',*selected,'--exact','--test-threads=1'],cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P619_NO_WARNINGS')
            directory='target/debug/examples'if kind=='--example'else'target/debug/deps';found=[]
            for path in(c.ROOT/directory).glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P619_ACTUAL_COMPILED_INPUTS_PREPINNED')
                found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
            c.require(bool(found),'P619_FRESH_COMPILER_ARTIFACTS');row['compiled_inputs'].append(dict(target=target,artifacts=found))
        r.harness.run_one('normal_cache_observation_example',[r.harness.CARGO,'build',*common,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P619_NORMAL_BUILD_NO_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({EXAMPLE,CORPUS}<=declared and declared<=set(q.snapshots),'P619_NORMAL_COMPILED_INPUTS_PINNED')
        observed=read_only(guard,env,row,[r.harness.CARGO,'run',*common,'--example',example,'--','--fixed-captured-readonly'])
        row['actual_cache_observations']=observed
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P619_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P619_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS619_SOURCE_CACHE_READER_SOURCE_V15_104_AND_FIXED24_NOT_NATIVE_OR_CURRENTNESS',
            new_tests=10,affected_tests=94,total_tests=104,actual010_outputs=24,compiled_normal_example=binary,
            current_executed_tests=0,retained_test_count=104,normal_build_and_fixed24_executed=True,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,source_cache_and_meaning_separate=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P619_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P619_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        observed=row.get('actual_cache_observations',{})
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','total_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),locations=v.get('locations'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'))for v in row['steps']],
            'captured_observations':len(observed.get('observations',[])),
            'bookmark_name_matches':[v['bookmark_name_cache_matches_decoded_command_target']for v in observed.get('observations',[])if v['bookmark_name_cache_matches_decoded_command_target']is not None],
            'saved_reopened_equal':[v['saved_reopened_selected_cache_equal']for v in observed.get('saved_reopened_comparisons',[])],
            'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS619_')else 2
if __name__=='__main__':raise SystemExit(main())
