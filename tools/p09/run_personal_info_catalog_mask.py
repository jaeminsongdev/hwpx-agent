"""427: original-catalog matched masking source30 + stored20, serial; no Native or commit."""
import hashlib,json,posixpath,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout

OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-mask427.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_mask.py'
BASE='implementation/p09/evidence/p09-361-reference-source-heading-api-closed-inputs424.v1.json'
PREIMAGES={
 'crates/hwpx-package/src/document_import/search/replacement/atoms/personal_info.rs':
    (10918,'dd0cd7ed8d6114f10c0504f0f473ec7d809e1e7c02e88705e019ff8b082b3aa7','pub mod catalog;\n'),
 'crates/hwpx-package/tests/personal_info_mask.rs':
    (18377,'51c73367153cf91a0e4e0e725dda67c0f964da4cb12255156003e72039165f5b','#[path="support/personal_info_catalog_mask.rs"]mod catalog_mask;\n'),
 'crates/product-cli/src/form_stored_provider/actual_import/source_search/personal_info_catalog.rs':
    (13024,'68e9a60a5ba7c4e35e99011ecc147de3d82d68beddb96dd88e797083492cd4d6','pub mod mask;\n'),
 'crates/product-cli/tests/support/personal_info_catalog_stored.rs':
    (17819,'b9b17f109863bbb7eb9e7d15378fca768b296ed7ff09a19d717df7d23a9c9fcc','mod mask{include!("personal_info_catalog_mask_stored.rs");}\n'),
}
CONFIGS=[dict(label='source_catalog_mask30',package='hwpx-package',test='personal_info_mask',prefix='catalog_mask::',count=30,
    source='crates/hwpx-package/tests/support/personal_info_catalog_mask.rs',old_dep='target/debug/deps/personal_info_mask-1d7b4c655844bb59.d'),
 dict(label='stored_catalog_mask20',package='hwpx-agent-cli',test='personal_info_mask_product',prefix='stored_catalog::mask::',count=20,
    source='crates/product-cli/tests/support/personal_info_catalog_mask_stored.rs',old_dep='target/debug/deps/personal_info_mask_product-6a9bb76a1b304e9d.d')]


def dependencies(path,guard):
    guard.check();item=r.c.ROOT/path
    r.c.require(item.is_file()and not item.is_symlink()and path.startswith('target/debug/deps/')and '..'not in path.split('/'),'CATALOG_MASK_FIXED_DEP_INFO')
    raw=item.read_bytes();r.c.require(0<len(raw)<=131072,'CATALOG_MASK_BOUNDED_DEP_INFO')
    line=raw.decode('utf-8').splitlines()[0];r.c.require(': 'in line,'CATALOG_MASK_DEP_TARGET')
    paths=sorted(set(posixpath.normpath(p.replace('\\','/'))for p in line.split(': ',1)[1].split()))
    r.c.require(0<len(paths)<=128 and all(p.startswith('crates/')and '..'not in p.split('/')for p in paths),'CATALOG_MASK_ROOT_BOUND_TEST_INPUTS')
    return paths,dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def compiled_inputs(config,wanted,guard):
    # Inspect only this binary's shallow dep-info set, not target trees or Git.
    seen=[]
    for item in (r.c.ROOT/'target/debug/deps').glob(config['test']+'-*.d'):
        actual,pin=dependencies(item.relative_to(r.c.ROOT).as_posix(),guard)
        if set(actual)==wanted:seen.append(dict(dep_info=pin,dependency_paths=actual))
    r.c.require(bool(seen),'CATALOG_MASK_ACTUAL_COMPILED_TEST_INPUTS_EXACT_DECLARATION')
    return seen


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_MASK427_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_CATALOG_MASK427',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        strict_product_catalog_mask_not_implemented=True,common_compiler_catalog_mask_not_implemented=True,
        source_document_mutation=False,ingest_commit_or_publication=False,whole_package_personal_data_removed=False,
        native_catalog_mask_semantics_or_service_execution_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        unchanged_test_bodies_replayed=False,compiled_test_inputs=[])
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='02032ec7221270aad138ea87ba7297a4eefd25553b4da1f5d0621e34825c7dfe'
            and base['cleanup']is True and base['current_distinct_product_cases']==80,'EXACT424_HEADING_API_VERIFIED_BASELINE_RETAINED')
        old={p['path']:p for p in base['source_pins']}
        expected={};names=r.shared.source_inventory(guard.check)|{DRIVER}
        for config in CONFIGS:
            paths,pin=dependencies(config['old_dep'],guard);wanted=set(paths)|{config['source']}
            expected[config['test']]=wanted;names.update(wanted)
            row['compiled_test_inputs'].append(dict(test=config['test'],baseline_dep_info=pin,expected_dependency_paths=sorted(wanted)))
        # Every loaded verifier module is a current input, without replaying its
        # old tests or scanning receipt history. Include non-Rust fixture bytes.
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):
            pin=q.pin(path)
            if path.startswith('crates/')and path in old and path not in PREIMAGES:c.require(pin==old[path],'ALL_OTHER_CURRENT_PRODUCT_LIBRARY_FIXTURE_AND_GUARD_INPUTS_PRESERVED')
        for path,(size,sha,added)in PREIMAGES.items():
            text=q.text(path);c.require(text.count(added)==1,'ONE_ADDITIVE_CATALOG_MASK_MODULE_EXPORT_OR_TEST_LINK')
            r.audit.inverse(text.replace(added,''),dict(path=path,bytes=size,sha256=sha),'ALL_ORIGINAL_ALGORITHMS_AND_TEST_BODIES_PRESERVED')
        cases={}
        for config in CONFIGS:
            text=q.text(config['source']);found={config['prefix']+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
            c.require(len(found)==config['count']and '#[ignore]'not in text and '#[cfg('not in text,'CATALOG_MASK_EXACT_NEW_CASES_NO_SKIPS')
            cases[config['test']]=found
        scratch=c.ROOT/'target/p09-catalog-mask-scratch-427'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_MASK_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='CATALOG_MASK427_PREFLIGHT',inputs=len(q.snapshots),source=30,stored=20,declared_test_input_count=len(set.union(*expected.values())))),flush=True)
        for config in CONFIGS:
            found=cases[config['test']]
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',config['package'],'--test',config['test'],'--message-format=short','--',*sorted(found),'--test-threads=1']
            r.harness.run_one(config['label'],args,found,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],found);c.require(row['steps'][-1]['diagnostics']==[],'CATALOG_MASK_NEW_CASES_NO_WARNINGS')
            row['compiled_test_inputs'][CONFIGS.index(config)]['actual_after_compile']=compiled_inputs(config,expected[config['test']],guard)
            print(json.dumps(dict(state='CATALOG_MASK427_STEP_PASS',stage=config['label'],cases=len(found))),flush=True)
        c.require(not any(scratch.iterdir()),'CATALOG_MASK_COMPILER_TEMP_EMPTY')
        final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_PERSONAL_INFO_CATALOG_MASK_SOURCE30_STORED20_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_cases=50,source_cases=30,stored_cases=20)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_MASK_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            final_attempted=True
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
