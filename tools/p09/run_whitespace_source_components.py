"""24 exact-source whitespace/control cases; retain unchanged patch/product passes without replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_patch_strengthening as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-whitespace-source-components184.v1.json'
PARENT='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
GUARD=PARENT[:-3]+'/unicode/plan.rs'
CORE=PARENT[:-3]+'/whitespace.rs'
PLAN=PARENT[:-3]+'/whitespace/plan.rs'
READBACK=PARENT[:-3]+'/whitespace/readback.rs'
LEXICAL=PARENT[:-3]+'/whitespace/lexical.rs'
TEST='crates/hwpx-package/tests/document_import_whitespace_normalization.rs'
NEW={CORE,PLAN,READBACK,LEXICAL,TEST};CHANGED={PARENT,GUARD}


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    marker='pub mod whitespace;\n';text=q.text(PARENT)
    c.require(text.count(marker)==1,'ONE_ADDITIVE_WHITESPACE_SOURCE_MODULE')
    audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_OLD_ATOM_SEARCH_AND_REPLACEMENT_BODIES_UNCHANGED')
    marker='pub(in crate::document_import::search::replacement::atoms) fn guard('
    text=q.text(GUARD);c.require(text.count(marker)==1,'ONE_SHARED_GUARD_VISIBILITY_ONLY_CHANGE')
    audit.inverse(text.replace(marker,'fn guard('),old[GUARD],'ENTIRE_OLD_GUARD_PROTECTION_TRACKING_AND_NORMALIZATION_BODIES_UNCHANGED')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(names)==len(set(names))==24,'EXACT24_NEW_SOURCE_AND_LEXICAL_TAMPER_CASE_IDENTITIES');return set(names)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_SOURCE_IMMUTABLE_RUN_EXISTS');selection=prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_SOURCE_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,whitespace_current_store_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='8303bfcd1b3456a0f019b939c718ff9967947b42ee099603b6285da0b60f6350'
            and baseline['state']=='PASS_WHITESPACE2_STRENGTHENED41_RETAINED_NOT_SOURCE_COMPILER_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==693 and baseline['total_distinct_cases']==43,'EXACT_PRIOR_WHITESPACE_PATCH_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_WHITESPACE_SOURCE_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_COMPILERS_GUARDS_READBACK_WRITERS_PRODUCTS_TESTS_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        c.require('unicode::plan::guard(xml)'in q.text(PLAN)and 'context.field_intervals(source,fields)'in q.text(PLAN)
            and 'scalar_edges(xml,element,&requested)'in q.text(PLAN)and 'lexical::verify(a,b,&edits)'in q.text(READBACK)
            and 'text_nodes(old)'in q.text(READBACK)and 'source.parts()'in q.text(READBACK),'SHARED_ORIGINAL_GUARDS_SCANNER_INDEPENDENT_SPARSE_BYTES_AND_STABLE_TEXT_CONTAINERS')
        print(json.dumps(dict(state='WHITESPACE_SOURCE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,old_cases_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_exact_original_whitespace_source_and_tamper_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_whitespace_normalization','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        prior.base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_WHITESPACE_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE24_SOURCE_NOT_CURRENT_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,old_patch43_products218_and_unrelated_source_reexecuted=False,shared_guard_body_and_old_readback_unchanged=True,
            explicit_unicode17_whitespace_control_sequence_output_policy=True,exact_sparse_readback_and_stable_text_container_mapping=True,
            next_work='SEARCH023_current_store_and_strict_product_binding_then_remaining_full_P09_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_SOURCE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WHITESPACE_SOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
