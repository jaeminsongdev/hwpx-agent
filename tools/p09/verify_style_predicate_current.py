"""502: unchanged core19, public source witness1 and unrun stored5; preserve both original failures."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import verify_style_predicate_recovery as witness
prior=witness.prior
r,layout,helpers=prior.r,prior.layout,prior.helpers
SELF='tools/p09/verify_style_predicate_current.py'
OUTPUT='implementation/p09/evidence/p09-361-style-predicate502.v1.json'
SELECTOR,CASE=witness.SELECTOR,witness.CASE
OLD='    let raw=fixture::archive::mutate_part(&original,"Contents/header.xml",|_|fixture::header())?;\n'
NEW='''    let raw=fixture::package(&body())?;
    let section=|bytes:&[u8]|->Result<Vec<u8>,Box<dyn std::error::Error>>{
        let mut reader=hwpx_package::BoundedZipReader::open(std::io::Cursor::new(bytes),Default::default())?;
        let index=reader.entries().iter().position(|e|e.path.as_str()=="Contents/section0.xml").ok_or("section")?;
        Ok(reader.read_entry(index)?)
    };
    assert_eq!(section(&original)?,section(&raw)?);
'''
ADDED=witness.ADDED.replace(OLD,NEW)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'STYLE502_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CURRENT_STYLE_PREDICATES',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,previous19_core_bodies_replayed=False,compiler_warnings_or_private_visibility_suppressed=False,
        full_effective_style_font_resource_search_native_or_execution_qualified=False,original500_501_failures_and_missing_final_closures_preserved=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(prior.OUTPUT));failed=layout.unpack(q.json(witness.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='f56795d3a4f473d75307f9e2d18eeaf058302569a36c041138b3758e1116814a'
            and old['state']=='FAILED_OPERATION_LOCAL_STYLE_PREDICATES'and old['error_code']=='STYLE500_NO_COMPILER_WARNINGS'
            and old['cleanup']is True and old['final_fresh_hashes']==0 and len(old['steps'])==1,'STYLE502_EXACT500_WARNING_FAILURE_PRESERVED')
        c.require(q.snapshots[witness.OUTPUT]['sha256']=='4ee500a7fcfd10ec6ea02d7c87bf8e9a6e4a5462f902744aa7aa381be85bcdf7'
            and failed['state']=='FAILED_STYLE_PREDICATE_WARNING_RECOVERY'and failed['cleanup']is True and failed['final_fresh_hashes']==0
            and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101 and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0603'],'STYLE502_EXACT501_PRE_TEST_PRIVATE_FIXTURE_ACCESS_FAILURE')
        step=old['steps'][0];warnings=step['bounded_output_observation']['safe_warning_locations']
        c.require(step['exit_code']==0 and len(step['tests'])==19 and all(status=='ok'for _,status in step['tests'])
            and len(warnings)==2 and all(w['path']=='crates/hwpx-package/tests/support/review_scope_fixture.rs'for w in warnings)
            and {symbol for w in warnings for symbol in w['symbols']}=={'package','with_body'},'STYLE502_CORE19_OBSERVED_AND_ONLY_UNUSED_FIXTURE_FUNCTIONS')
        for packet in(old,failed):
            for pin in packet['source_pins']:
                if pin['path']!=SELECTOR:c.require(q.pin(pin['path'])==pin,'STYLE502_ALL_ORIGINAL_EXECUTION_INPUTS_AND_19_BODIES_UNCHANGED')
        for path in(SELF,SELECTOR,prior.ARCHIVE+'selector501.rs',prior.ARCHIVE+'runner501.py'):q.pin(path)
        for packet,current,saved in((old,SELECTOR,'selector500.rs'),(old,prior.SELF,'runner500.py'),
            (failed,SELECTOR,'selector501.rs'),(failed,witness.SELF,'runner501.py')):
            pin=next(p for p in packet['source_pins']if p['path']==current);archived=q.snapshots[prior.ARCHIVE+saved]
            c.require((pin['bytes'],pin['sha256'])==(archived['bytes'],archived['sha256']),'STYLE502_ORIGINAL500_501_CODE_AND_RUNNERS_ARCHIVED')
        text=q.text(SELECTOR);c.require(witness.ADDED.count(OLD)==1 and text.count(ADDED)==1,'STYLE502_ONLY_PUBLIC_PACKAGE_AND_READONLY_SECTION_WITNESS')
        r.audit.inverse(text.replace(ADDED,''),q.snapshots[prior.ARCHIVE+'selector500.rs'],'STYLE502_ALL_ORIGINAL_CORE19_BODIES_AND_HELPERS_RESTORED')
        r.audit.inverse(text.replace(NEW,OLD),q.snapshots[prior.ARCHIVE+'selector501.rs'],'STYLE502_NO_PRODUCT_CHANGE_ONLY_TEST_PRIVATE_HELPER_REPLACED')
        row['retained_core_test_names']=[name for name,status in step['tests']];row['retained_core_bodies']=19
        product=helpers.tests(q,prior.PRODUCT,'product_host::detail_axes::predicate_cache::')
        product|={'product_host::detail_axes::'+name for name in('explicit_run_text_named_and_direct_paragraph_axes_are_not_native_precedence',
            'v7_all_four_review_scopes_and_both_style_families_remain_conjunctive',
            'border_definitions::same_hits_different_border_predicates_cannot_reuse_retained_v7_or_v9_cursor')}
        c.require(len(product)==5,'STYLE502_PREVIOUSLY_UNRUN_STORED5')
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.176037330217578,'STYLE502_RAM95_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-style-predicate-scratch502';c.require(not scratch.exists(),'STYLE502_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='STYLE_PREDICATE_CURRENT_PREFLIGHT',inputs=len(q.snapshots),retained_core=19,new_review_case=1,previously_unrun_product=5)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in(('hwpx-package','style_predicate_search',{CASE}),('hwpx-agent-cli','definition_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'STYLE502_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'STYLE502_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'STYLE502_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_OPERATION_LOCAL_STYLE_PREDICATES_RETAINED19_NEW_REVIEW1_STORED5_NOT_NATIVE_OR_GATE',current_qualified_cases=25,
            predicate_memo_entries_maximum=1,predicate_memo_uses_heap=False,predicate_memo_shared_between_operations=False,
            fixed_storage_repeated_20000_calls_evaluate_twice=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'STYLE502_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
