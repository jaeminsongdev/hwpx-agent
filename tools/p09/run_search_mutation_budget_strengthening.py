"""One actually affected budget case: positive standard-budget control before tightened rejections."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_mutation_dispatch_recovery as recovery
base=recovery.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-search-mutation-dispatch-budget207.v1.json'
DRIVER='tools/p09/run_search_mutation_budget_strengthening.py'
ADDITION='''        let baseline=Dispatch::prepare_json_with_search_limits(&p,&wire(&v)?,None,Limits::standard()?,4)?;
        baseline.with_verified_bytes(&p,None,5,|_|())?;
'''
CASE=base.PREFIX+'dispatch_server_search_writer_and_number_format_budgets_are_not_dropped'


def inventory(check):return recovery.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_DISPATCH_BUDGET_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_DISPATCH_BUDGET_STRENGTHENING',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,full_search_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        passed=q.json(recovery.OUTPUT)
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='ec970564f5398b801555833e58c0b20e6ec7dd573fe559b064de2100a4115c94'
            and passed['state']=='PASS_COMMON_DISPATCH_RETAINED16_RECOVERED10_NOT_TRANSACTION_NATIVE_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==732,'EXACT206_RECOVERY_AND_COMPLETE_SOURCE_CLOSURE')
        old={p['path']:p for p in passed['source_pins']}
        for name in names-{DRIVER,base.TEST}:c.require(q.snapshots[name]==old[name],'ALL206_PRODUCT_SOURCE_SERVICE_AND_OTHER_TEST_INPUTS_UNCHANGED')
        text=q.text(base.TEST);c.require(text.count(ADDITION)==1,'ONE_POSITIVE_CURRENT_STANDARD_BUDGET_DELIVERY_CONTROL')
        audit.inverse(text.replace(ADDITION,''),old[base.TEST],'ENTIRE26_CASES_UNCHANGED_EXCEPT_POSITIVE_CONTROL_IN_ONE_AFFECTED_BUDGET_CASE')
        base.inverse(q,{p['path']:p for p in q.json(base.prior.OUTPUT)['source_pins']})
        print(json.dumps(dict(state='ONE_ACTUALLY_AFFECTED_BUDGET_CASE_PREFLIGHT',inputs=len(q.snapshots),other25_cases_reexecuted=False)),flush=True)
        harness.run_one('one_strengthened_standard_and_tight_search_writer_auxiliary_budget_case',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,audit.environment(),row,observe_capture=recovery.snapshot)
        tools.good_step(row['steps'][0],{CASE});q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_DISPATCH_BUDGET_POSITIVE_AND_TIGHT_CONTROLS_NOT_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_affected_cases=1,other25_dispatch_cases_reexecuted=False,old292_products_reexecuted=False,distinct_current_dispatch_cases=26,
            dispatched_mutation_families=16,original_form_formula_bodies_inverse_verified=True,original_mutation_product_bodies_unchanged=True,
            next_work='actual_product_transaction_route_manifest_and_durable_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_DISPATCH_BUDGET_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_DISPATCH_BUDGET_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
