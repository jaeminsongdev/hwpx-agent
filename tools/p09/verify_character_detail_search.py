"""481: 12 new character-detail core/products + 56 directly affected cases, serial original guards."""
import json,posixpath,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout

SELF='tools/p09/verify_character_detail_search.py'
OUTPUT='implementation/p09/evidence/p09-361-character-detail-search481.v1.json'
CORE='crates/hwpx-package/tests/'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/'
DEFS='crates/hwpx-package/src/document_import/search/inspection/definitions.rs'
RESOLVED=DEFS[:-3]+'/resolved.rs'
NEW={DEFS[:-3]+'/details.rs',CORE+'document_import_character_detail_search.rs',CORE+'support/character_detail_fixture.rs',PRODUCT+'character_detail_product.rs',SELF}
PREFIX='actual_import::regex_replacement_product::resolved_style_v9::'
BASE='implementation/p09/evidence/p09-361-catalog-request-recovery471.v1.json'

def tests(q,path,prefix=''):
    text=q.text(path);names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)
    r.c.require(len(names)==len(set(names))and '#[ignore]'not in text,'DETAIL_DISTINCT_ENABLED_TEST_IDENTITIES')
    return {prefix+n for n in names}

def dependencies(path):
    raw=path.read_bytes();r.c.require(0<len(raw)<=131072,'DETAIL_BOUNDED_DEP_INFO')
    line=raw.decode('utf-8').splitlines()[0];r.c.require(': 'in line,'DETAIL_DEP_INFO_TARGET')
    paths={posixpath.normpath(p.replace('\\','/'))for p in line.split(': ',1)[1].split()}
    r.c.require(paths and all(p.startswith('crates/')and '..'not in p.split('/')for p in paths),'DETAIL_ROOT_BOUND_COMPILE_INPUTS')
    return paths

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DETAIL481_IMMUTABLE')
    c.require(not(c.ROOT/'implementation/p09/evidence/p09-361-character-detail-search481-publication-failure.v1.json').exists(),'DETAIL481_CONSUMED_PUBLICATION_FAILURE_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CHARACTER_DETAIL_SEARCH',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,prior_unrelated_suites_replayed=False,
        full_style_cascade_font_substitution_visibility_or_product_route_qualified=False,source_mutation_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='6e4b125c1b2c38eb73766fb53077707b30ccde95862771ee950c1ac41c2550b6','DETAIL_EXACT_PRIOR_SOURCE_PINS')
        old={p['path']:p for p in base['source_pins']}
        names=shared.source_inventory(guard.check)|NEW|{p for p in old if p.startswith(('crates/','fixtures/'))}
        names|={CORE+'document_import_search_definitions.rs',CORE+'document_import_resolved_style_search.rs',CORE+'resolved_style_control_context.rs',
            'crates/product-cli/tests/regex_replacement_product.rs','crates/product-cli/tests/regex_replacement_product/actual_import.rs',
            'crates/product-cli/tests/support/stored_source_fixture.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml'}
        targets=('document_import_character_detail_search','document_import_search_definitions','document_import_resolved_style_search','regex_replacement_product')
        for target in targets:
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                guard.check();names|=dependencies(path)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):q.pin(path)
        parent=PRODUCT+'resolved_style_product.rs';marker='#[path="character_detail_product.rs"] mod character_details;\n'
        c.require(q.text(parent).count(marker)==1,'DETAIL_ONE_CHILD_TEST_MODULE')
        r.audit.inverse(q.text(parent).replace(marker,''),old[parent],'ALL_ORIGINAL_TWENTY_PRODUCT_TEST_BODIES_UNCHANGED')
        core_new=tests(q,CORE+targets[0]+'.rs');explicit=tests(q,CORE+targets[1]+'.rs')
        resolved=tests(q,CORE+targets[2]+'.rs')|tests(q,CORE+'resolved_style_control_context.rs','control_context::')
        product_old=tests(q,parent,PREFIX);product_new=tests(q,PRODUCT+'character_detail_product.rs',PREFIX+'character_details::')
        c.require([len(s)for s in(core_new,explicit,resolved,product_old,product_new)]==[7,10,26,20,5],'DETAIL_NEW12_AFFECTED56_EXACT_CASES')
        configs=[('hwpx-package',targets[0],core_new),('hwpx-package',targets[1],explicit),('hwpx-package',targets[2],resolved),
            ('hwpx-agent-cli',targets[3],product_old|product_new)]
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];required=5+6.036870455636344
        row['memory_admission']=dict(available_ram_percent=available,required_available_percent=required,global_RAM_commit_ceiling_percent=95)
        c.require(available>required,'DETAIL_COMPARABLE_COMPILE_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-character-detail-search-scratch481';c.require(not scratch.exists(),'DETAIL_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='CHARACTER_DETAIL_PREFLIGHT_COMPLETE',new_cases=12,affected_cases=56,inputs=len(q.snapshots),CPU_cap_percent=6.25)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in configs:
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'DETAIL_NO_COMPILER_DIAGNOSTICS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=dependencies(path);c.require(declared<=set(q.snapshots),'DETAIL_ALL_ACTUAL_COMPILE_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'DETAIL_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CHARACTER_DETAIL_CORE_AND_STRICT_STORED_PRODUCTS_NOT_FULL_STYLE_NATIVE_OR_GATE',new_cases=12,affected_cases=56,
            total_executed_cases=68,character_detail_predicate_families=24,language_slots=7,original_product_test_bodies_preserved=True,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'DETAIL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']and row['fresh_inputs']==row['final_fresh_hashes']else 2

if __name__=='__main__':raise SystemExit(main())
