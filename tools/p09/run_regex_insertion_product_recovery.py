"""Preserve123 output-cap stop; put child after macro definitions, same47 tests with short diagnostics."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_product_components as base
harness,shared,c,a,audit=base.harness,base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-product-recovery124.v1.json'


def snapshot(capture,expected):
    result=base.snapshot(capture,expected)
    with capture.lock:stderr=bytes(capture.buffers['stderr']).decode('utf-8','replace').replace('\\','/')
    result['rust_error_codes']=sorted(set(re.findall(r'\berror\[(E[0-9]{4})\]',stderr)))
    result['macro_not_in_scope_observed']='cannot find macro'in stderr
    result['short_error_locations']=re.findall(r'(?m)^(crates/[A-Za-z0-9_./-]+\.rs):([0-9]+):([0-9]+): error',stderr)[:16]
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_PRODUCT_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.prior.base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_PRODUCT_RECOVERY',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_product_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='30811ec1f348ca5f03dfc13223c4b9f71dc54cfd24f900391cdedbbf4b4fbae0'
            and failed['state']=='FAILED_REGEX_INSERTION_PRODUCT_COMPONENTS'and failed['error_code']=='live_progress_output_limit'and failed['cleanup'],
            'ORIGINAL_OUTPUT_CAP_STOP_AND_UNCONFIRMED_CASE_EXECUTION_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{base.OLD_TEST}:c.require(q.snapshots[name]==old[name],'NO_PRODUCTION_CORE_WRITER_GUARD_NEW_TEST_OR_FIXTURE_CHANGE_AFTER_OUTPUT_STOP')
        include='#[path="regex_insertion_product.rs"] mod insertion_v2;\n';text=q.text(base.OLD_TEST)
        c.require(text.endswith(include)and text.count(include)==1,'CHILD_AFTER_ORIGINAL_MACRO_DEFINITIONS')
        audit.inverse(include+text[:-len(include)],old[base.OLD_TEST],'ONLY_CHILD_DECLARATION_MOVED_FROM_BEFORE_TO_AFTER_ORIGINAL_MACROS')
        base.inverse(q,{p['path']:p for p in previous['source_pins']});cases=base.expected(q)
        print(json.dumps(dict(state='REGEX_INSERTION_PRODUCT_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,affected_cases=29,
            unchanged_output_cap_bytes=32768,only_test_module_order_changed=True)),flush=True)
        harness.run_one('same_forty_seven_products_after_child_macro_scope_fix',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(base.inventory(guard.check)==names,'FINAL_INSERTION_PRODUCT_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_PRODUCT_EIGHTEEN_NEW_TWENTY_NINE_AFFECTED_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=18,affected_product_cases=29,total_executed_cases=47,source_v2_core_and_unaffected_suites_reexecuted=False,
            original_failure_and_production_code_preserved=True,original_v1_stored_product_and_test_whole_file_inverse_verified=True,
            one_proof_one_capture_compiler_owner_transfer_without_reimport=True,current_output_does_not_repeat_query_capture_or_lowering=True,
            strict_v2_policy_in_canonical_and_scoped_request=True,output_or_resource_limit_raised=False,
            next_work='Remaining_effective_style_visibility_full_scope_and_style_control_conversion_then_full_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_PRODUCT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_PRODUCT_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants','bounded_output_observation')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
