"""505: keep current source24/stored7, execute only the corrected v4/v7 scope witness.

All library/runtime/fixture inputs stay exact504. Restore the full previous test
file to prove no other test/helper changed. Never rerun the 798-request matrix.
"""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import verify_font_definition_recovery as previous
r,layout,prior=previous.r,previous.layout,previous.prior
SELF='tools/p09/verify_font_definition_current.py'
OUTPUT='implementation/p09/evidence/p09-361-font-definition505.v1.json'
TEST=prior.FONT_PRODUCT
ARCHIVE=previous.ARCHIVE
FAILED='product_host::detail_axes::font_definitions::font_filters_keep_v4_explicit_axes_four_review_scopes_and_language_conjunction'
OLD='    assert_eq!(legacy_count(&legacy_data(&legacy(&provider,&old)?,&provider)?)?,6);\n'
NEW='''    let filtered=legacy_data(&legacy(&provider,&old)?,&provider)?;
    let mut plain=old.clone();plain["operation"]=json!({"kind":"find_literal","query":"K","case_sensitive":true,"whole_word":false,"max_results":100});
    let plain=legacy_data(&legacy(&provider,&plain)?,&provider)?;
    let main_count=plain["result"]["matches"].as_array().ok_or("plain mapped matches")?.len();
    // v4 definition compatibility uses the original main-body index, not review-inclusive v7.
    assert_eq!(main_count,2);assert_eq!(legacy_count(&filtered)?,main_count);
'''


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'FONT505_IMMUTABLE_NO_RETRY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CURRENT_FONT_DEFINITION_SCOPE_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,capture003_replayed_or_cleanup_changed=False,
        previous503_504_failures_and_missing_final_fresh_preserved=True,previous31_bodies_replayed=False,
        previous798_request_stored_matrix_replayed=False,font_file_validity_activation_native_or_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='7462f0b46fad93593cfa66f3f0b226e5e504d03fb33dd5525b36226187daffca'
            and old['state']=='FAILED_FONT_REFERENCE_WRITER_RECOVERY'and old['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED'
            and old['cleanup']is True and old['fresh_inputs']==940 and old['final_fresh_hashes']==0 and len(old['steps'])==2,'FONT505_EXACT504_ORIGINAL_FAILURE')
        core_step,stored_step=old['steps'];source={name for name,status in core_step['tests']if status=='ok'}|set(old['retained_search_case_names'])
        stored={name for name,status in stored_step['tests']if status=='ok'}
        c.require(core_step['exit_code']==0 and len(core_step['tests'])==6 and all(status=='ok'for _,status in core_step['tests'])
            and stored_step['exit_code']==101 and len(stored_step['tests'])==8 and len(stored)==7
            and [(name,status)for name,status in stored_step['tests']if status!='ok']==[(FAILED,'FAILED')]
            and stored_step['panic_locations']==['crates/product-cli/tests/form_stored_provider/actual_import/font_definition_product.rs:49:5'],
            'FONT505_CURRENT_WRITER6_AND_PRODUCT7_OBSERVATIONS_NOT_NEW_EXECUTIONS')
        names=prior.inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,ARCHIVE+'product504.rs',ARCHIVE+'runner504.py'}
        names|=prior.inputs.test_inputs((prior.CORE,prior.PRODUCT_HOST),guard)
        for path in sorted(names):q.pin(path)
        for pin in old['source_pins']:
            if pin['path']==TEST:
                saved=q.snapshots[ARCHIVE+'product504.rs'];c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'FONT505_EXACT504_TEST_SOURCE_ARCHIVED')
            else:c.require(q.snapshots[pin['path']]==pin,'FONT505_ALL_OTHER_LIBRARY_GUARDS_FIXTURES_AND_BODIES_UNCHANGED')
        text=q.text(TEST);c.require(text.count(NEW)==1,'FONT505_ONE_SAME_INPUT_UNFILTERED_SCOPE_WITNESS')
        r.audit.inverse(text.replace(NEW,OLD),q.snapshots[ARCHIVE+'product504.rs'],'FONT505_ALL_OTHER_PRODUCT_BODIES_HELPERS_AND_REVIEW_SCOPE_EXPECTATIONS_RESTORED')
        expected_core,expected_stored=prior.cases(q)
        c.require(source==expected_core and stored|{FAILED}==expected_stored and (len(source),len(stored))==(24,7),'FONT505_RETAIN31_EXECUTE_ONE_CURRENT32_SCOPE')
        row.update(retained_source_case_names=sorted(source),retained_source_cases=24,retained_stored_case_names=sorted(stored),retained_stored_cases=7,
            selected_case_names=[FAILED],current_library_and_runtime_byte_exact504=True)
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.176037330217578,'FONT505_RAM95_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-font-definition-scratch505';c.require(not scratch.exists(),'FONT505_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        row['actual_compiled_test_inputs']=[]
        for item in old['actual_compiled_test_inputs']:
            info=artifact.pin(item['dep_info']['path']);c.require(info==item['dep_info']and set(item['dependency_paths'])<=set(q.snapshots),'FONT505_RETAIN_CURRENT_SOURCE_DEP_INFO_AND_INPUTS')
            row['actual_compiled_test_inputs'].append(item)
        c.require(bool(row['actual_compiled_test_inputs']),'FONT505_PREVIOUS_SOURCE_ARTIFACT_REQUIRED')
        print(json.dumps(dict(state='FONT_CURRENT_SCOPE_PREFLIGHT',inputs=len(q.snapshots),retained_source=24,retained_stored=7,execute_one=FAILED,
            large_matrix_replayed=False,CPU_cap_percent=6.25)),flush=True)
        selected={FAILED};target='definition_detail_product'
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',target,'--message-format=short','--',FAILED,'--exact','--test-threads=1']
        r.harness.run_one(target,command,selected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(not row['steps'][-1]['diagnostics'],'FONT505_NO_COMPILER_WARNINGS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            declared=prior.helpers.dependencies(path);c.require(declared<=set(q.snapshots),'FONT505_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'FONT505_CURRENT_STORED_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_FONT_DEFINITIONS_SOURCE24_STORED8_RETAIN31_EXECUTE1_NOT_NATIVE_OR_GATE',current_qualified_cases=32,
            executed_cases=1,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'FONT505_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('panic_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
