"""Preserve184 assembly-import failure; qualify the fixed assembly and preallocated output budget."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_whitespace_source_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-whitespace-source-recovery185.v1.json'
ASSEMBLY='#[allow(dead_code)] #[path="support/document_import_review_assembly_fixture.rs"] mod assembly;\n'
OLD_RENDER='''                let output=match &e.output{None=>Vec::new(),Some(TextAtom::Text(t))=>t.as_bytes().to_vec(),
                    Some(TextAtom::Tab{width,leader,tab_type})=>format!("<{prefix}tab width=\\"{width}\\" leader=\\"{leader}\\" type=\\"{tab_type}\\"/>").into_bytes(),
                    Some(TextAtom::LineBreak)=>format!("<{prefix}lineBreak/>").into_bytes()};
'''


def repair(q,old):
    text=q.text(base.TEST);c.require(text.count(ASSEMBLY)==1,'ONE_ADDITIVE_MISSING_ASSEMBLY_IMPORT');text=text.replace(ASSEMBLY,'')
    new='''    assert!(serde_json::from_str::<Text>("\\"all_unicode_controls\\"").is_err());assert!(serde_json::from_str::<Policy>("{}").is_err());
    assert!(serde_json::from_str::<Out>("{\\"spaces\\":{\\"count\\":1,\\"ignored\\":true}}").is_err());Ok(())
'''
    prior='''    assert!(serde_json::from_str::<Text>("\\"all_unicode_controls\\"").is_err());assert!(serde_json::from_str::<Policy>("{}").is_err());Ok(())
'''
    c.require(text.count(new)==1,'ONE_NESTED_UNKNOWN_OUTPUT_FIELD_ASSERTION');audit.inverse(text.replace(new,prior),old[base.TEST],'EXACT184_TESTS_EXCEPT_ASSEMBLY_IMPORT_AND_STRICT_OUTPUT_ASSERTION')
    text=q.text(base.CORE);new='#[serde(rename_all="snake_case",deny_unknown_fields)]\npub enum SourceWhitespaceOutput'
    c.require(text.count(new)==1,'ONE_OUTPUT_ENUM_STRICT_NESTED_FIELDS');audit.inverse(text.replace(new,'#[serde(rename_all="snake_case")]\npub enum SourceWhitespaceOutput'),old[base.CORE],'EXACT184_SOURCE_API_EXCEPT_STRICT_NESTED_OUTPUT')
    text=q.text(base.PLAN);start=text.index('fn lexical_output(');end=text.index('fn append_atom(',start);helper=text[start:end]
    c.require('add(total,size,limit)?;'in helper and helper.index('add(total,size,limit)?;')<helper.index('format!(')
        and 'prefix.len().checked_add'in helper and 'output.len()!=size'in helper,'EXACT_NAMESPACE_NUMERIC_BYTES_BUDGET_BEFORE_FORMAT_ALLOCATION')
    text=text[:start]+text[end:]
    new='    let(mut total_span_bytes,mut lexical_bytes)=(0usize,0usize);\n';c.require(text.count(new)==1,'ONE_JOINT_RENDER_BUDGET');text=text.replace(new,'    let mut total_span_bytes=0usize;\n')
    new='                let output=lexical_output(&e.output,&prefix,&mut lexical_bytes,index.limits.0.result_bytes)?;\n'
    c.require(text.count(new)==1,'ONE_BOUNDED_RENDER_CALL');audit.inverse(text.replace(new,OLD_RENDER),old[base.PLAN],'EXACT184_PLAN_EXCEPT_PREALLOCATION_NAMESPACE_OUTPUT_BUDGET')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WHITESPACE_SOURCE_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WHITESPACE_SOURCE_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,whitespace_current_store_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='98c2d3e7b4e74ae2819beff17c79d3654b26069cbc3be6b8f6a0322c318e61f3'
            and failed['state']=='FAILED_WHITESPACE_SOURCE_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL184_FAILURE_PRESERVED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and not step['tests']and step['cleanup']and step['owned_job']['owned_tree_empty']
            and step['owned_job']['job_handle_closed']and step['bounded_output_observation']['rust_error_codes']==['E0432'],'EXACT184_FIXTURE_IMPORT_ERROR_ZERO_TESTS_TERMINAL_JOB')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.CORE,base.PLAN,base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_OTHER_INPUTS_UNCHANGED_AFTER184')
        repair(q,pins);base.inverse(q,{p['path']:p for p in baseline['source_pins']});cases=base.expected(q)
        print(json.dumps(dict(state='WHITESPACE_SOURCE_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_exact_original_whitespace_source_and_tamper_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_whitespace_normalization','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        base.prior.base.good_step(row['steps'][0],cases);c.require(base.inventory(guard.check)==names,'FINAL_WHITESPACE_SOURCE_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_WHITESPACE24_SOURCE_NOT_CURRENT_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,old_patch43_products218_and_unrelated_source_reexecuted=False,shared_guard_body_and_old_readback_unchanged=True,
            explicit_unicode17_whitespace_control_sequence_output_policy=True,exact_sparse_readback_and_stable_text_container_mapping=True,
            namespace_and_numeric_output_bytes_bounded_before_allocation=True,original184_failure_preserved=True,
            next_work='SEARCH023_current_store_and_strict_product_binding_then_remaining_full_P09_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WHITESPACE_SOURCE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WHITESPACE_SOURCE_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
