"""Declared source styles/control inspection + v2 request; preserve original v1 bodies."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
OUTPUT='implementation/p09/evidence/p09-361-search-inspection-components048.v1.json'
CORE=('document_import_search','document_import_search_scope','document_import_search_inspection')
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
OFFICIAL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/'
DOCS={'docs/04_feature_catalog/03_search.md','docs/04_feature_catalog/contracts/03_search_contracts.md'}


def inventory(check):
    return shared.source_inventory(check)|{PRODUCT}|DOCS|{'crates/hwpx-package/tests/'+n+'.rs' for n in CORE}|{OFFICIAL+n for n in ('runType.cpp','ctrl.cpp','t.cpp')}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_INSPECTION_IMMUTABLE_RUN_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None
    row=dict(state='FAILED_SEARCH_INSPECTION_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,
        effective_style_or_hidden_visibility_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        expected=set();counts=[]
        for name in CORE:
            found=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+name+'.rs')))
            c.require(not expected&found,'DISTINCT_INSPECTION_CORE_NAMES');expected|=found;counts.append(len(found))
        c.require(counts==[24,6,9],'EXACT_NINE_NEW_THIRTY_AFFECTED_CORE_CASES')
        product={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        c.require(len(product)==14,'EXACT_FIVE_NEW_NINE_AFFECTED_PRODUCT_CASES')
        previous=q.json('implementation/p09/evidence/p09-361-scoped-search-product-components045.v1.json')
        old={p['path']:p for p in previous['source_pins']}
        for name in CORE[:2]:
            path='crates/hwpx-package/tests/'+name+'.rs';c.require(q.snapshots[path]==old[path],'ORIGINAL_THIRTY_CORE_TEST_BODIES_UNCHANGED')
        prefix=q.text(PRODUCT).split('// Additive v2 inspection cases;',1)[0]
        c.require(prefix.endswith('\n\n'),'ONE_NEW_SEPARATOR_BEFORE_ADDITIVE_INSPECTION_CASES');prefix=prefix[:-1]
        c.require(old[PRODUCT]['sha256'] in {hashlib.sha256(prefix.encode()).hexdigest(),hashlib.sha256(prefix.replace('\n','\r\n').encode()).hexdigest()},'ORIGINAL_NINE_PRODUCT_TEST_BODIES_EXACT_INVERSE')
        classification=q.text('crates/hwpx-package/src/document_import/search/inspection.rs')
        actual={'Run':set(),'Control':set(),'Text':set()}
        for first,second,name in re.findall(r'\(Site::(Run|Control|Text)(?:\|Site::(Text))?,"([A-Za-z]+)"\)',classification):
            actual[first].add(name)
            if second:actual[second].add(name)
        official_counts={}
        for site,file,omit in (('Run','runType.cpp',{'ctrl','t'}),('Control','ctrl.cpp',set()),('Text','t.cpp',set())):
            declared=set(re.findall(r'OWPML_PARALIST_ADD_REDIRECT_FUNC\(([A-Za-z]+),',q.text(OFFICIAL+file)))-omit
            c.require(actual[site]==declared,'COMPLETE_CACHED_OFFICIAL_TAG_MAP_AND_PARENT_SITE_BINDING');official_counts[site]=len(declared)
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='SEARCH_INSPECTION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),official_tag_sites=official_counts)),flush=True)
        args=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        for name in CORE:args+=['--test',name]
        args+=['--','--test-threads=1']
        harness.run_one('nine_new_and_thirty_affected_source_search_cases',args,expected,guard,env,row)
        harness.run_one('five_v2_and_nine_v1_authenticated_product_cases',[harness.CARGO,'test','--offline','--locked','-j','1',
            '-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_SEARCH_INSPECTION_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_DECLARED_STYLE_STRUCTURAL_CONTROL_NINE_NEW_THIRTY_AFFECTED_FOURTEEN_PRODUCT_NOT_EFFECTIVE_STYLE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_tests=9,affected_core_tests=30,new_product_tests=5,affected_product_tests=9,
            cached_official_tag_site_counts=official_counts,original_thirty_nine_test_bodies_preserved=True,
            unrelated_stored_suites_reexecuted=False,source_api_and_official_queue_reexecuted=False,
            command_line_or_server_route_added=False,idempotency_key_claimed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_INSPECTION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples]
            c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SEARCH_INSPECTION_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
