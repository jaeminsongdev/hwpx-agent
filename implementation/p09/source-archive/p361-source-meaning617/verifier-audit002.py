"""Main Source v14/real CLI plus directly affected meaning routes. No Native."""
import json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
SELF='tools/p09/verify_source_meaning617.py'
OUTPUT='implementation/p09/evidence/p09-361-main-source-meaning617-audit002.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-main-source-meaning617-audit002-forensic'
SOURCE='crates/product-cli/tests/reference_source_product.rs'
NEW='crates/product-cli/tests/reference_source_product/field_meanings617.rs'
PRODUCT='crates/product-cli/tests/reference_field_semantics_product.rs'
INTEGRATED='crates/product-cli/tests/bookmark_field_semantics616.rs'
CORE='crates/hwpx-package/tests/source_field_meaning_index.rs'
STRICT='crates/product-cli/examples/p09_bookmark_command_bindings613.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-source-meaning617/'
MODULES={'joined_caption_state':'caption_state.rs','source_note_selection':'note_selection.rs',
    'source_note_style_selection':'note_style_selection.rs','source_heading_targets':'heading_targets.rs'}
def tests(q,path,prefix=''):
    text=q.text(path);r.c.require('#[ignore]'not in text,'P617_NO_IGNORED_TESTS')
    return {prefix+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-main-source-and-cli'],'P617_BOUNDED_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P617_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED617_MAIN_SOURCE_MEANINGS',steps=[],own_cpu_selection=selection,
        Native_Hancom_COM_or_DB_started=False,official249_replayed=False,consumed010_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_target_or_display_qualified=False,
        reference_source_schema='v14',source_unresolved_stages=4,CLI_incomplete_exit=3)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names=inventory.inventory(guard)|includes.test_inputs((SOURCE,PRODUCT,INTEGRATED,CORE,STRICT),guard)|{SELF,NEW,CORPUS,
            'tools/p09/metadata_forensic_retention615.py','tools/p09/crossref_lossless_receipt610.py',
            ARCHIVE+'verifier-audit001.py','implementation/p09/evidence/p09-361-main-source-meaning617-audit001.v1.json'}
        for name in('reference_targets.rs','bookmark_crossref.rs','semantics.rs','source_index.rs','source_field_semantics.rs',
            'source.rs','reference_source_product.rs','reference_field_semantics_product.rs','bookmark_field_semantics616.rs'):
            names.add(ARCHIVE+name)
        names|={ARCHIVE+'source-test-modules/'+name for name in MODULES.values()}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P617_FIXED_CORPUS')
        for pin in[corpus['source'],*[p for case in corpus['cases']for p in case['artifacts'].values()]]:
            c.require(q.pin(pin['path'])==pin,'P617_FIXED010_OUTPUTS');names.add(pin['path'])
        formula='implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json'
        original=q.json(formula);names.add(formula)
        for case in original['cases']:
            for key in('input','output'):
                pin=case[key];actual=q.pin(pin['path']);c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P617_ORIGINAL_FORMULAS16');names.add(pin['path'])
        names.add('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        # Existing Source suite also reads these fixed note fixtures/qualifications.
        names|={'fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json',
            'implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json'}
        for i,file in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'),1):
            names.add('fixtures/target-build/p09-24-note-target-20261002-03/output/'+file)
            for stage in('saved','reopened'):names.add(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{stage}.hwpx')
        for name in sorted(names):q.pin(name)
        # Schema migration changes only exact version assertions in existing Source
        # suites. No old body/assertion was removed to obtain a passing result.
        def previous_schema(text):return text.replace('reference-source-assessment/v14','reference-source-assessment/v13')
        module_line='mod source_field_meanings617 {include!("reference_source_product/field_meanings617.rs");}\n'
        c.require(previous_schema(q.text(SOURCE).replace(module_line,''))==q.text(ARCHIVE+'reference_source_product.rs'),'P617_ORIGINAL_MAIN_SOURCE_TESTS_UNCHANGED_EXCEPT_SCHEMA')
        for name in MODULES.values():c.require(previous_schema(q.text('crates/product-cli/tests/reference_source_product/'+name))==q.text(ARCHIVE+'source-test-modules/'+name),'P617_ORIGINAL_SOURCE_MODULES_ONLY_SCHEMA_CHANGED')
        integrated=previous_schema(q.text(INTEGRATED)).replace('fn main_source_v14_still_reports_all_unresolved_stages','fn main_source_v13_still_reports_all_unresolved_stages')
        c.require(integrated==q.text(ARCHIVE+'bookmark_field_semantics616.rs'),'P617_ORIGINAL616_ALL_ASSERTIONS_PRESERVED')
        product=previous_schema(q.text(PRODUCT)).replace('selection_binds_document_package_and_meaning_and_main_v14_includes_it','selection_binds_document_package_and_meaning_while_legacy_v13_is_unchanged').replace('    assert_eq!(old.field_meanings(),&first);\n','')
        c.require(product==q.text(ARCHIVE+'reference_field_semantics_product.rs'),'P617_ORIGINAL_FIELD_API_ASSERTIONS_PRESERVED_AND_JOIN_ADDED')
        source_tests=tests(q,SOURCE)
        for prefix,name in MODULES.items():source_tests|=tests(q,'crates/product-cli/tests/reference_source_product/'+name,prefix+'::')
        new=tests(q,NEW,'source_field_meanings617::');source_tests|=new
        core=tests(q,CORE)|{'legacy_meanings::'+v for v in('source_https_tuple_is_typed_without_approval_or_label_inference',
            'malformed_supported_parameter_tuples_reject_not_opaque_success','historical_captured_https_has_actual_target_and_whole_unchanged_graph',
            'nested_supported_link_keeps_unsupported_parent_and_all_source_positions')}
        integrated_tests=tests(q,INTEGRATED);product_tests=tests(q,PRODUCT);strict=tests(q,STRICT,'tests::')
        c.require(len(new)==9 and len(source_tests)==79 and tuple(map(len,(core,integrated_tests,product_tests,strict)))==(7,9,6,10),'P617_EXACT_NEW9_AND_AFFECTED_INVENTORY')
        row.update(expected_new_tests=9,expected_main_source_tests=len(source_tests),expected_total_tests=len(source_tests)+32)
        old_probe=q.pin('target/debug/examples/p09_crossref_capture010_probe.exe')
        c.require(old_probe['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P617_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P617_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-main-source617-audit002-scratch';c.require(not scratch.exists(),'P617_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);row['compiled_inputs']=[]
        configs=[('hwpx-agent-cli','--test','reference_source_product',source_tests),
            ('hwpx-agent-cli','--test','reference_field_semantics_product',product_tests),
            ('hwpx-agent-cli','--test','bookmark_field_semantics616',integrated_tests),
            ('hwpx-agent-cli','--example','p09_bookmark_command_bindings613',strict),
            ('hwpx-package','--test','source_field_meaning_index',core)]
        print(json.dumps(dict(state='P617_FRESH_MAIN_SOURCE_PREFLIGHT',inputs=len(q.snapshots),new_tests=9,
            expected_total_tests=row['expected_total_tests'],actual010_outputs=24,real_CLI_new_processes=4,
            CPU_RAM_protection_unchanged=True,package_CLI_codegen_units=2)),flush=True)
        for package,kind,target,cases in configs:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,kind,target]
            if package=='hwpx-agent-cli':args+=['--features','p09-installed-format-fixture']
            # The original 96-argument guard remains unchanged. This one target
            # is the entire suite; do not redundantly pass all 79 names. Exact
            # expected-result set equality still checks every one, without skips.
            selected=[] if target=='reference_source_product'else sorted(cases)
            args+=['--message-format=short','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
                '--config','profile.test.package.hwpx-agent-cli.codegen-units=2','--',*selected,'--exact','--test-threads=1']
            build_begin=time.time_ns();r.harness.run_one(target,args,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P617_NO_WARNINGS')
            directory='target/debug/examples'if kind=='--example'else'target/debug/deps';found=[]
            for path in(c.ROOT/directory).glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P617_ACTUAL_COMPILED_INPUTS_PREPINNED')
                dep=artifact.pin(path.relative_to(c.ROOT).as_posix());image=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix())
                found.append(dict(dep_info=dep,binary=image,dependency_count=len(declared),all_pre_pinned=True))
            c.require(bool(found),'P617_FRESH_COMPILED_DEP_INFO');row['compiled_inputs'].append(dict(target=target,artifacts=found))
            if target=='reference_source_product':
                cli=artifact.pin('target/debug/hwpx-agent-cli.exe');declared=deps.dependencies(c.ROOT/'target/debug/hwpx-agent-cli.d')
                c.require(declared<=set(q.snapshots),'P617_CLI_COMPILED_INPUTS_PREPINNED');row['actual_CLI_binary']=cli
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P617_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P617_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS617_MAIN_SOURCE_V14_FIELD_MEANINGS_AND_ACTUAL_CLI_NOT_NATIVE_OR_GATE',
            total_tests=row['expected_total_tests'],new_tests=9,actual010_outputs=24,formula_sources=16,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,target_inventory_reused_only_exact_original_and_limits=True,
            source_approval_or_complete_validation_qualified=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P617_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P617_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','total_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),
                locations=v.get('locations'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'))for v in row['steps']],
            'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS617_')else 2
if __name__=='__main__':raise SystemExit(main())
