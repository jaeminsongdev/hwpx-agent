"""498: referenced border resources through current source/stored routes, bounded serial validation."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import verify_detail_axes_recovery as previous
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import character_detail_receipt as layout
r=previous.r
SELF='tools/p09/verify_border_definition_search.py'
OUTPUT='implementation/p09/evidence/p09-361-border-definition498.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-border-definition498/'
DEFS=helpers.DEFS
DETAIL=DEFS[:-3]+'/details.rs'
PARAGRAPH=DEFS[:-3]+'/paragraph_details.rs'
MODULE=DEFS[:-3]+'/border_details.rs'
PARENT=previous.prior.TEST
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/border_definition_product.rs'
CORE='crates/hwpx-package/tests/document_import_border_definition_search.rs'
FIXTURE='crates/hwpx-package/tests/support/border_definition_fixture.rs'
CHANGED={DEFS:'definitions-original.rs',DETAIL:'details-original.rs',PARAGRAPH:'paragraph-original.rs',PARENT:'product-original.rs'}

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'BORDER498_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_REFERENCED_BORDER_DEFINITIONS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,capture003_probe_or_previous_unaffected_tests_replayed=False,
        full_native_effective_style_visibility_or_execution_qualified=False,source_mutation_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);baseline=layout.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='2a24f6c321a69fa77e605e38a18d5f9eefe89fdab76062c95c58789111594f97'
            and baseline['state'].startswith('PASS_')and baseline['cleanup']is True and baseline['fresh_inputs']==baseline['final_fresh_hashes']==809,
            'EXACT497_CURRENT_INPUT_CLOSURE_RETAINED')
        names=inventory.inventory(guard)|{pin['path']for pin in baseline['source_pins']}|{SELF,MODULE,CORE,PRODUCT,FIXTURE}
        names|={ARCHIVE+name for name in CHANGED.values()}
        for path in sorted(names):q.pin(path)
        for pin in baseline['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+CHANGED[pin['path']]]
                c.require((pin['bytes'],pin['sha256'])==(saved['bytes'],saved['sha256']),'EXACT497_CHANGED_SOURCE_ARCHIVED')
            else:c.require(q.snapshots[pin['path']]==pin,'UNCHANGED497_PRODUCT_ACCESS_GUARDS_REQUEST_PARSER_AND_OTHER_INPUTS')
        r.audit.inverse(q.text(PARENT).replace('#[path="border_definition_product.rs"] mod border_definitions;\n',''),q.snapshots[ARCHIVE+CHANGED[PARENT]],
            'PREVIOUS_TEN_EXPLICIT_PRODUCT_BODIES_AND_SHARED_HELPERS_UNCHANGED')
        core=helpers.tests(q,CORE);product=helpers.tests(q,PRODUCT,'product_host::detail_axes::border_definitions::')
        c.require((len(core),len(product))==(8,5),'NEW_CORE8_STORED5_EXACT_ENABLED_CASES')
        product|={'product_host::detail_axes::'+name for name in('all51_character_and_paragraph_details_reach_explicit_v3_and_v7_matchers',
            'explicit_run_text_named_and_direct_paragraph_axes_are_not_native_precedence','v3_v7_invalid_new_axes_nested_conditions_and_duplicates_deny_before_reads',
            'exact16k_raw_padding_and_canonical_identity_preserve_previous_success_contract')}
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];c.require(available>11.139219593950513,'BORDER498_RAM95_COMPILE_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-border-definition-scratch498';c.require(not scratch.exists(),'BORDER498_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='BORDER_DEFINITION_PREFLIGHT',inputs=len(q.snapshots),new_core=8,new_product=5,affected_product=4,CPU_cap_percent=6.25)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in(('hwpx-package','document_import_border_definition_search',core),('hwpx-agent-cli','definition_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'BORDER498_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'BORDER498_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'BORDER498_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCED_BORDER_CORE8_STORED5_AFFECTED4_NOT_NATIVE_OR_GATE',new_core_cases=8,new_product_cases=5,affected_product_cases=4,
            referenced_resource_predicates=30,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'BORDER498_FAILURE_NO_RAW_VALUES')
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
