"""Affected source-meaning product integration, serial guarded Rust tests only."""
import hashlib,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
SELF='tools/p09/verify_bookmark_semantics616.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-meaning-integration616-audit001.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-meaning616-audit001-forensic'
NEW='crates/product-cli/tests/bookmark_field_semantics616.rs'
CORE='crates/hwpx-package/tests/source_field_meaning_index.rs'
PRODUCT='crates/product-cli/tests/reference_field_semantics_product.rs'
STRICT='crates/product-cli/examples/p09_bookmark_command_bindings613.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-semantics616/'
def tests(q,name,prefix=''):
    text=q.text(name);r.c.require('#[ignore]'not in text,'P616_NO_IGNORES')
    return {prefix+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
def main():
    c,a,s=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--bounded-source-meaning-tests'],'P616_BOUNDED_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P616_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED616_SOURCE_BOOKMARK_MEANING_INTEGRATION',steps=[],own_cpu_selection=selection,
        Native_or_Hancom_or_COM_started=False,official249_replayed=False,consumed010_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_target_or_display_qualified=False,
        source_v13_unresolved_stages=4,full_reference_validation_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names=inventory.inventory(guard)|includes.test_inputs((NEW,CORE,PRODUCT,STRICT),guard)|{SELF,CORPUS,
            'tools/p09/metadata_forensic_retention615.py','tools/p09/crossref_lossless_receipt610.py',
            *{ARCHIVE+n for n in('bookmark_crossref.rs','semantics.rs','source_index.rs','source_field_semantics.rs')}}
        corpus=q.json(CORPUS)
        c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P616_FIXED_CORPUS')
        for pin in[corpus['source'],*[p for case in corpus['cases']for p in case['artifacts'].values()]]:
            c.require(q.pin(pin['path'])==pin,'P616_FIXED010_OUTPUTS');names.add(pin['path'])
        manifest='implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json'
        old=q.json(manifest);names.add(manifest)
        for case in old['cases']:
            for key in('input','output'):
                pin=case[key];c.require(q.pin(pin['path'])==pin,'P616_ORIGINAL_FORMULA16');names.add(pin['path'])
        names.add('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        for name in sorted(names):q.pin(name)
        new=tests(q,NEW);strict=tests(q,STRICT,'tests::');core=tests(q,CORE)|{
            'legacy_meanings::'+v for v in('source_https_tuple_is_typed_without_approval_or_label_inference',
                'malformed_supported_parameter_tuples_reject_not_opaque_success',
                'historical_captured_https_has_actual_target_and_whole_unchanged_graph',
                'nested_supported_link_keeps_unsupported_parent_and_all_source_positions')}
        product=tests(q,PRODUCT)
        c.require(tuple(map(len,(new,strict,core,product)))==(9,10,7,6),'P616_EXACT_AFFECTED32')
        oldprobe='target/debug/examples/p09_crossref_capture010_probe.exe';pin=q.pin(oldprobe)
        c.require(pin['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P616_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P616_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-bookmark-meaning616-audit001-scratch';c.require(not scratch.exists(),'P616_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check)
        configs=[('hwpx-agent-cli','--test','bookmark_field_semantics616',new),
            ('hwpx-agent-cli','--example','p09_bookmark_command_bindings613',strict),
            ('hwpx-package','--test','source_field_meaning_index',core),
            ('hwpx-agent-cli','--test','reference_field_semantics_product',product)]
        row['compiled_inputs']=[]
        print(json.dumps(dict(state='P616_FRESH_PREFLIGHT',inputs=len(q.snapshots),new_tests=9,affected_tests=23,
            actual010_outputs=24,package_CLI_codegen_units=2,CPU_RAM_protection_unchanged=True)),flush=True)
        for package,kind,target,cases in configs:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,kind,target,
                '--features','p09-installed-format-fixture'] if package=='hwpx-agent-cli' else[
                r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,kind,target]
            args+=['--message-format=short','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
                '--config','profile.test.package.hwpx-agent-cli.codegen-units=2','--',*sorted(cases),'--exact','--test-threads=1']
            build_begin=time.time_ns()
            r.harness.run_one(target,args,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases)
            c.require(not row['steps'][-1]['diagnostics'],'P616_NO_WARNINGS')
            directory='target/debug/examples'if kind=='--example'else'target/debug/deps'
            found=[]
            for path in(c.ROOT/directory).glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P616_ACTUAL_COMPILED_INPUTS_PREPINNED')
                dep=artifact.pin(path.relative_to(c.ROOT).as_posix());binary=path.with_suffix('.exe')
                c.require(binary.is_file(),'P616_COMPILED_BINARY_EXISTS')
                image=artifact.pin(binary.relative_to(c.ROOT).as_posix())
                found.append(dict(dep_info=dep,binary=image,dependency_count=len(declared),all_pre_pinned=True))
            c.require(bool(found),'P616_FRESH_COMPILED_DEP_INFO');row['compiled_inputs'].append(dict(target=target,artifacts=found))
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P616_NO_HWP_AFTER')
        c.require(not any(scratch.iterdir()),'P616_EMPTY_SCRATCH');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS616_BOOKMARK_MEANING_GRAPH_INDEX_PUBLIC_API32_NOT_NATIVE_OR_GATE',new_tests=9,
            affected_tests=23,total_tests=32,actual010_outputs=24,formula_sources=16,
            source_meaning_profile='partial-v2',public_field_meaning_schema='v2',main_source_schema_unchanged='v13',
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P616_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P616_FAILURE_RECORDED_BEFORE_ENCODING',error_type=row['error_type'],error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row)
        pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','total_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),
                locations=v.get('locations'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'))for v in row['steps']],
            'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS616_')else 2
if __name__=='__main__':raise SystemExit(main())
