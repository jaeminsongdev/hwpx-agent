"""496: new detail predicates across explicit product routes and early canonical bound, no old test replay."""
import ast,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import verify_paragraph_detail_search as prior
import character_detail_receipt as layout
r=prior.r
SELF='tools/p09/verify_detail_axes_product.py'
OUTPUT='implementation/p09/evidence/p09-361-detail-axes496.v1.json'
REQUEST='crates/product-cli/src/form_product_request/stored_source_search.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/detail_axes_product.rs'
HOST='crates/product-cli/tests/form_stored_provider/actual_import/definition_detail_product_host.rs'
ROOT='crates/product-cli/tests/definition_detail_product.rs'
FIXTURE='crates/hwpx-package/tests/support/detail_axes_fixture.rs'
ARCHIVE='implementation/p09/source-archive/p361-detail-axes496/source-request-original.rs'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DETAIL_AXES496_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_DETAIL_AXES_PRODUCT_CONNECTION',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,previous495_tests_replayed=False,
        source_mutation_or_publication=False,full_effective_style_native_visibility_or_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        baseline=layout.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='1ed7b079dcf86552cb9ceb13f261d64e9b56583cce9ec2fcb140c0259d2d3291'
            and baseline['state'].startswith('PASS_')and baseline['cleanup']is True and baseline['fresh_inputs']==baseline['final_fresh_hashes']==798,
            'EXACT_PREVIOUS_PARAGRAPH495_NOT_REPLAYED')
        names=prior.inventory(guard)|{SELF,REQUEST,TEST,HOST,ROOT,FIXTURE,ARCHIVE}
        names|={pin['path']for pin in baseline['source_pins']}
        for path in sorted(names):q.pin(path)
        for pin in baseline['source_pins']:
            if pin['path']!=REQUEST:c.require(q.snapshots[pin['path']]==pin,'UNCHANGED_PREVIOUS_CHARACTER_PARAGRAPH_MATCHERS_FIXTURES_GUARDS_AND_PRODUCT_BODY_INPUTS')
        old=next(pin for pin in baseline['source_pins']if pin['path']==REQUEST);saved=q.snapshots[ARCHIVE]
        c.require((old['bytes'],old['sha256'])==(saved['bytes'],saved['sha256']),'EXACT_ORIGINAL_SOURCE_REQUEST_PARSER_ARCHIVED')
        text=q.text(REQUEST);added='request.head()?;request.canonical_sha()?;Ok(request)'
        c.require(text.count(added)==1,'ONE_EARLY_CANONICAL_BOUND_BEFORE_SOURCE_ACCESS')
        r.audit.inverse(text.replace(added,'request.head()?;Ok(request)'),saved,'WHOLE_ORIGINAL_V1_V4_SCHEMA_SOURCE_ACCESS_RESULT_CURSOR_AND_CLOSED_ROUTE_BODY_UNCHANGED')
        cases=prior.prior.tests(q,TEST,'product_host::detail_axes::');c.require(len(cases)==10,'EXACT_TEN_NEW_EXPLICIT_PRODUCT_CONNECTION_CASES')
        ast.parse(q.text(SELF));guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];required=11.139219593950513
        row['memory_admission']=dict(available_ram_percent=available,required_available_percent=required,global_RAM_commit_ceiling_percent=95)
        c.require(available>required,'DETAIL_AXES_COMPARABLE_PREVIOUS_PEAK_PLUS_RAM95_RESERVE')
        scratch=c.ROOT/'target/p09-detail-axes-scratch496';c.require(not scratch.exists(),'DETAIL_AXES_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='DETAIL_AXES_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_product_cases=10,prior36_replayed=False,CPU_cap_percent=6.25)),flush=True)
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','definition_detail_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('explicit_detail_products10',command,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'DETAIL_AXES_NO_COMPILER_DIAGNOSTICS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob('definition_detail_product-*.d'):
            declared=prior.prior.dependencies(path);c.require(declared<=set(q.snapshots),'ALL_ACTUAL_EXPLICIT_DETAIL_TEST_COMPILER_INPUTS_PINNED_BEFORE_RUN')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'DETAIL_AXES_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs']=actual
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_EXPLICIT_DETAIL_V3_V4_V7_PRODUCTS10_EARLY_CANONICAL_BOUND_NOT_NATIVE_OR_GATE',new_product_cases=10,
            character_and_paragraph_predicate_families=51,previous495_bodies_retained_not_reexecuted=True,
            full_original_product_body_inverse_except_early_canonical_preflight=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'DETAIL_AXES_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
