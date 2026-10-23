"""Preserve227 and its17 passes; repair prohibited PI fixture without changing the original safe parser."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sibling_permutation_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-sibling-permutation-recovery228.v1.json'
DRIVER='tools/p09/run_sibling_permutation_recovery.py'
ASSERTION='''    assert!(matches!(PreservingXmlDocument::parse(b"<root><?keep yes?></root>"),
        Err(hwpx_package::PreservingXmlError::Safe(hwpx_package::SafeXmlError::ProcessingInstructionForbidden))));
'''


def inventory(check):return base.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PERMUTATION_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SIBLING_PERMUTATION_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,source_sort_or_locale_semantics_verified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='5657dfe281d800f1283ecee64da07cafa03541b2b3e781aa410f5380b51206df'
            and failed['cleanup']and failed['steps'][0]['exit_code']==101,'EXACT227_ORIGINAL_ONE_FIXTURE_FAILURE_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in{DRIVER,base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_AND_OTHER17_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        text=q.text(base.TEST);c.require(text.count(ASSERTION)==1 and text.count('<!--SECOND-->')==2,'EXACT_FORBIDDEN_PI_ASSERTION_AND_TWO_VALID_COMMENT_FIXTURES')
        audit.inverse(text.replace(ASSERTION,'').replace('<!--SECOND-->','<?keep yes?>'),old[base.TEST],
            'ONLY_INVALID_PI_POSITIVE_FIXTURE_REPAIRED_AND_ORIGINAL_PI_REJECTION_ASSERTED')
        original={p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']};base.inverse(q,original)
        all_cases=base.expected(q);previous={n for n,s in failed['steps'][0]['tests']if s=='ok'};cases={n for n,s in failed['steps'][0]['tests']if s!='ok'}
        c.require(len(previous)==17 and len(cases)==1 and previous|cases==all_cases,'EXACT17_PASSES_RETAINED_AND_ONLY_FAILED_ONE_SELECTED')
        job=failed['steps'][0]['owned_job'];c.require(job['owned_tree_empty']and job['cleanup_confirmed']and job['job_handle_closed']
            and job['last_job_accounting']['active_processes']==0,'227_OWNED_JOB_TERMINAL_EMPTY_AND_CLOSED')
        print(json.dumps(dict(state='SIBLING_PERMUTATION_ONE_CASE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained17=True,current_cases=1,production_unchanged=True)),flush=True)
        harness.run_one('one_repaired_gap_fixture_with_exact_original_PI_rejection',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','patch_engine','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_SIBLING_BYTE_PERMUTATION12_AFFECTED_PATCH6_RETAINED17_NOT_SOURCE_SORT_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=1,retained_passes=17,distinct_component_cases=18,
            original_safe_parser_and_production_unchanged=True,old17_cases_and_official249_reexecuted=False,
            next_work='source_bound_SEARCH021_comparator_scope_protection_order_semantics_then_product_request_and_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PERMUTATION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PERMUTATION_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
