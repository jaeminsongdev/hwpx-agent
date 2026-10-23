"""513: keep twenty-nine observed cases; fix only declared target font and execute two."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as inputs
import character_detail_receipt as layout
SELF='tools/p09/verify_search_storage_fonts.py'
OUTPUT='implementation/p09/evidence/p09-361-search-storage513.v1.json'
SCRATCH='target/p09-search-storage-scratch513'
BASE='implementation/p09/evidence/p09-361-search-storage512.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-search-storage511/'
PREFIX='crates/product-cli/src/form_product_request/'
CHANGED={'crates/product-cli/tests/form_stored_provider/actual_import/search_storage_fixture.rs':'fixture512.rs'}
CORE=PREFIX+'stored_operations/compiled_search/routing/storage.rs'
PARENT='crates/product-cli/tests/definition_detail_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_storage_product.rs'
FIXTURE='crates/product-cli/tests/form_stored_provider/actual_import/search_storage_fixture.rs'

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/SCRATCH).exists(),'SEARCH511_FRESH_RUN_AND_SCRATCH_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_COMMON_SEARCH_STORAGE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,external003_replayed_or_cleanup_changed=False,
        operational_SQL_registry_custody_or_native_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e9cd53255bbf4e4d23240a7c3e0a02d6b7222ffab23c9dbba9ac1a2bd3214e5c'
            and old['cleanup']is True and old['fresh_inputs']==981 and old['final_fresh_hashes']==0 and len(old['steps'])==1,'SEARCH513_EXACT512_FAILURE')
        step=old['steps'][0];passed={name for name,status in step['tests']if status=='ok'}
        failed={'product_host::detail_axes::search_storage::family_18_fonts','product_host::detail_axes::search_storage::family_19_font_options'}
        retained=passed|set(old['retained_case_names'])
        c.require(step['exit_code']==101 and len(step['tests'])==23 and len(passed)==21 and old['retained_cases']==8 and len(retained)==29
            and {name for name,status in step['tests']if status!='ok'}==failed,'SEARCH513_RETAIN21_FAMILIES_AND_EIGHT_SAFETY_BODIES')
        names=inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,BASE,CORE,PARENT,TEST,FIXTURE}|{ARCHIVE+name for name in CHANGED.values()}
        names|=inputs.test_inputs((PARENT,),guard)
        for path in sorted(names):q.pin(path)
        for pin in old['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+CHANGED[pin['path']]]
                c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'SEARCH511_CHANGED_INPUT_EXACT510_ARCHIVE')
            else:c.require(q.snapshots[pin['path']]==pin,'SEARCH511_OTHER_LIBRARY_RUNTIME_SOURCE_AND_PREVIOUS_BODIES_UNCHANGED')
        before="            let name=&catalog.font_faces.iter().find(|f|f.language==hwpx_package::LanguageSlot::Hangul).ok_or(\"hangul\")?.fonts.get(id as usize).ok_or(\"font\")?.face;\n            v[\"operation\"]=json!({\"kind\":\"replace_fonts\",\"query\":name,\"replacement\":\"Storage Test Font\",\"regex\":false,\"case_sensitive\":true,\"whole_word\":false,\n"
        after="            let group=catalog.font_faces.iter().find(|f|f.language==hwpx_package::LanguageSlot::Hangul).ok_or(\"hangul\")?;\n            let name=&group.fonts.get(id as usize).ok_or(\"font\")?.face;\n            let target=&group.fonts.iter().find(|font|font.id!=id&&font.face!=*name).ok_or(\"different declared font\")?.face;\n            v[\"operation\"]=json!({\"kind\":\"replace_fonts\",\"query\":name,\"replacement\":target,\"regex\":false,\"case_sensitive\":true,\"whole_word\":false,\n"
        text=q.text(FIXTURE);c.require(text.count(after)==1,'SEARCH513_ONLY_DECLARED_FONT_TARGET_FIX')
        r.audit.inverse(text.replace(after,before),q.snapshots[ARCHIVE+'fixture512.rs'],'SEARCH513_ALL_OTHER_REQUEST_RECIPES_AND_SAFETY_INPUTS_UNCHANGED')
        all_cases=helpers.tests(q,TEST,'product_host::detail_axes::search_storage::');cases=all_cases-retained
        c.require(len(all_cases)==31 and cases==failed,'SEARCH513_CURRENT31_EXECUTE_ONLY_TWO_FONTS')
        row.update(retained_cases=29,retained_case_names=sorted(retained))
        row.update(selected_cases=sorted(cases),tested_mutation_families=23,expected_source_owned_ingest_and_CAS_paths=23,
            unchanged_prior_test_bodies_replayed=False)
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.301693333880961,'SEARCH511_RAM95_LAST_COMPILER_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists(),'SEARCH511_CURRENT_UNIQUE_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='SEARCH_STORAGE_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),families=23,CPU_cap_percent=6.25)),flush=True)
        target='definition_detail_product';command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'SEARCH511_NO_COMPILER_WARNINGS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'SEARCH511_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'SEARCH511_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs']=actual
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_SEARCH_STORAGE_CURRENT31_23_FAMILIES_NOT_NATIVE_OR_GATE',qualified_test_cases=31,source_owned_ingest_and_CAS_paths=23,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SEARCH511_FAILURE_NO_RAW_VALUES')
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
