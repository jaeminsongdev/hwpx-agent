"""Preserve230/231 and17 passes; repair two invalid source specimens, original product/parser/ID guards unchanged."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_paragraph_sort_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-paragraph-sort-recovery232.v1.json'
DRIVER='tools/p09/run_source_paragraph_sort_recovery.py'
DIAG='implementation/p09/evidence/p09-361-source-paragraph-sort-diagnosis231.v1.json'
OLD_EMPTY='''    let b="<hp:p id='2'/>";let raw=fixture::package(&(a.to_owned()+b))?;let f=fixture::forms(&raw,"sort-controls")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;assert!(section(&bytes(&out)?)?.contains(&(b.to_owned()+a)));Ok(())
'''
NEW_EMPTY='''    assert!(matches!(hwpx_package::TextFlowReader::read(b"<hp:p xmlns:hp='http://www.hancom.co.kr/hwpml/2011/paragraph' id='2'/>",Default::default()),Err(hwpx_package::TextFlowError::UnsupportedShape)));
    let b=p(2,"");let raw=fixture::package(&(a.to_owned()+&b))?;let f=fixture::forms(&raw,"sort-controls")?;
    let out=sort(&f,&raw,Scope::Document,spec())?;assert!(section(&bytes(&out)?)?.contains(&(b+a)));Ok(())
'''


def inventory(check):return base.inventory(check)|{DRIVER,'tools/p09/inspect_source_paragraph_sort_failures.py'}


def inverse(q,old):
    text=q.text(base.TEST);c.require(text.count(NEW_EMPTY)==1 and text.count('table::paragraph(901,"A")')==2,'TWO_VALID_SPECIMENS_AND_EXACT_EMPTY_SOURCE_REJECTION_ONLY')
    audit.inverse(text.replace(NEW_EMPTY,OLD_EMPTY).replace('table::paragraph(901,"A")','table::paragraph(1,"A")'),old[base.TEST],
        'ALL_OTHER17_CASES_AND_HELPERS_UNCHANGED_TWO_INVALID_SOURCE_FIXTURES_ONLY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SORT_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PARAGRAPH_SORT_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,multi_parent_or_nested_composition_qualified=False,locale_native_order_verified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT);diag=q.json(DIAG)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='72a57c2be2e2e8f0704454ccad91f7e6f417039f33b3465de5d8f6e7ea3ce7be'
            and failed['cleanup']and failed['steps'][0]['exit_code']==101,'EXACT230_SEVENTEEN_PASSES_TWO_INVALID_SPECIMENS_PRESERVED')
        c.require(q.snapshots[DIAG]['sha256']=='3b18175bf9890134a45d73016b79d3c41eb1ab32694fac34d18eedbdb519d5d1'and diag['cleanup']
            and diag['steps'][0]['bounded_output_observation']['closed_static_patch_codes']==['id_index_validation_failed'],
            'EXACT231_ORIGINAL_ID_VALIDATION_OBSERVATION_AND_DIAGNOSTIC_ALLOWLIST_FAILURE_PRESERVED')
        old={p['path']:p for p in failed['source_pins']};diagnosed={p['path']:p for p in diag['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,base.TEST}:c.require(q.snapshots[name]==old.get(name,diagnosed.get(name)),'ALL_PRODUCTION_COMPARATOR_SCOPE_GUARDS_PATCH_WRITER_AND_OTHER_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        all_cases=base.expected(q);previous={n for n,s in failed['steps'][0]['tests']if s=='ok'};cases={n for n,s in failed['steps'][0]['tests']if s!='ok'}
        c.require(len(previous)==17 and len(cases)==2 and previous|cases==all_cases,'EXACT17_RETAINED_AND_ONLY_FAILED_TWO_CURRENT_CASES')
        for record in (failed,diag):
            job=record['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'230_AND231_OWNED_JOBS_TERMINAL_EMPTY_CLOSED')
        print(json.dumps(dict(state='SOURCE_SORT_TWO_CASE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained17=True,current_cases=2,production_unchanged=True)),flush=True)
        harness.run_one('two_valid_blank_and_unique_table_paragraph_specimens_original_guards',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','source_paragraph_sort','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_SIBLING_PARAGRAPH_SORT19_RETAINED17_NOT_FULL_SEARCH021_PRODUCT_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=2,retained_passes=17,distinct_component_cases=19,
            original_product_parser_ID_guard_and_other17_cases_unchanged=True,old17_and_official249_reexecuted=False,
            next_work='multi_parent_nested_group_and_structured_keys_then_current_store_strict_product_request_compiler_and_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SORT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_SORT_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
