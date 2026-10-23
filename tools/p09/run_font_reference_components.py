"""Source font-reference compiler14 only; reuse old successes without replaying them."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_registered_recovery_postgres as latest
shared,c,a,tools,compact,harness,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.harness,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-reference-components300.v1.json'
DRIVER='tools/p09/run_font_reference_components.py'
PARENT='crates/hwpx-package/src/document_import/fields/semantics/catalog/fonts.rs'
CORE=PARENT[:-3]+'/replacement.rs'
TEST='crates/hwpx-package/tests/document_import_font_replacement.rs'
FIXTURES={'crates/hwpx-package/tests/support/document_import_fonts_fixture.rs','crates/hwpx-package/tests/support/document_import_catalog_fixture.rs'}
MANIFEST='implementation/p09/evidence/p09-75-document-import-bookmarks.source-progress.v1.json'
NEW={DRIVER,CORE,TEST};SCRATCH='target/p09-font-reference-scratch-300'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_REFERENCE_IMMUTABLE')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_REFERENCE_COMPONENTS',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,
        actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_or_scoped_product_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);last=compact.unpack(q.json(latest.OUTPUT))
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='5cb52bcd3daa26f9f3de0789ceb7ac28e298f56a29dae6d639eabc775ca10386'and last['cleanup'],'EXACT298_PRIOR_SOURCE_CLOSURE')
        old={p['path']:p for p in last['source_pins']}
        for n in NEW|{PARENT}:q.pin(n)
        marker='pub mod replacement;\n';text=q.text(PARENT)
        c.require(text.count(marker)==1,'ONE_ADDITIVE_FONT_REFERENCE_MODULE')
        audit.inverse(text.replace(marker,''),old[PARENT],'ALL_PRIOR_FONT_IMPORT_AND_FRESHNESS_CODE_UNCHANGED')
        names=latest.components.previous.previous.inventory(guard.check)|NEW|FIXTURES|{PARENT,MANIFEST}
        for n in sorted(names):
            q.pin(n)
            if n not in NEW|FIXTURES|{PARENT,MANIFEST}:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_PROTECTION_PATCH_WRITER_AND_PRODUCT_SOURCES_UNCHANGED')
        frozen=q.json(MANIFEST)
        c.require(q.snapshots[MANIFEST]['sha256']=='dc23091137a2262c9191cd060b923df282f50a25a0bfb16e605705c712953824'and len(frozen['actual_inputs'])==26,'EXACT_ORIGINAL26_INPUT_MANIFEST')
        for entry in frozen['actual_inputs']:
            n=entry['path'];q.pin(n);c.require(q.snapshots[n]['bytes']==entry['bytes']and q.snapshots[n]['sha256']==entry['sha256'],'FROZEN_SOURCE_PACKAGES_UNMODIFIED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        c.require(len(cases)==14,'EXACT14_FONT_REFERENCE_CASES')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_REFERENCE_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_REFERENCE_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),prior249_replayed=False)),flush=True)
        harness.run_one('new_font_reference_source14',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases)
        c.require(not any(scratch.iterdir()),'FONT_REFERENCE_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REFERENCE_SOURCE14_NOT_SCOPED_SEARCH_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=14,official249_and_other_old_suites_replayed=False,source_original_import_repeated=False,
            next_work='bind_font_name_query_and_SearchScopeSelector_without_globally_mutating_shared_unselected_properties')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_REFERENCE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_REFERENCE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
