"""523: source/product new9+affected6; keep522 observed unit3 without replay or full-closure promotion."""
import json,re,subprocess,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as includes
import character_detail_receipt as old_layout
import search_sql_receipt as layout
SELF='tools/p09/verify_source_field_semantics.py'
OUTPUT='implementation/p09/evidence/p09-361-source-field-semantics523.v1.json'
BASE='implementation/p09/evidence/p09-361-search-lookup515.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-field-semantics522/'
CHANGED={'crates/hwpx-package/src/hyperlink_hwpx.rs':'hyperlink.rs',
    'crates/hwpx-package/src/document_import/fields/semantics.rs':'semantics.rs',
    'crates/product-cli/src/reference_validation_product.rs':'product.rs',
    'crates/product-cli/src/reference_validation_product/source.rs':'source.rs'}
SOURCE='crates/hwpx-package/tests/source_field_meaning_index.rs'
PRODUCT='crates/product-cli/tests/reference_field_semantics_product.rs'
PRIVATE='crates/hwpx-package/src/hyperlink_hwpx/token_window_tests.rs'
CAPTURE='implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx'
FORMULAS='implementation/p06/evidence/target/p06-table-aggregate.current-2020.attempt02.v2.json'

def dependencies(path):
    raw=path.read_bytes();r.c.require(0<len(raw)<=262144,'MEANING522_BOUNDED_DEP_INFO')
    line=raw.decode('utf-8').splitlines()[0];r.c.require(': 'in line,'MEANING522_DEP_INFO_TARGET');result=set()
    for value in line.split(': ',1)[1].split():
        p=Path(value);p=p if p.is_absolute()else r.c.ROOT/p;p=p.resolve()
        r.c.require(p.is_relative_to(r.c.ROOT),'MEANING522_COMPILER_INPUT_IN_WORKSPACE');result.add(p.relative_to(r.c.ROOT).as_posix())
    r.c.require(bool(result),'MEANING522_NONEMPTY_DEP_INFO');return result

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'MEANING522_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None;row=dict(state='FAILED_SOURCE_FIELD_MEANINGS',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_Hancom_COM_SQL_or_Native_started=False,
        official249_or_SQL520_replayed=False,external003_replayed_or_cleanup_changed=False,
        complete_reference_state_flow_update_or_external_approval=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=old_layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='07d8b90bd946b5c90aaaa58cbf9ad23ac6e886af79d708acb4cbe85a127a2ed6','MEANING522_PRIOR_LIBRARY_BASE_PIN')
        names=inventory.inventory(guard)|{SELF,BASE,SOURCE,PRODUCT,PRIVATE,CAPTURE,FORMULAS,
            'crates/hwpx-package/src/document_import/fields/semantics/source_index.rs',
            'crates/product-cli/src/reference_validation_product/source_field_semantics.rs',
            'tools/p09/search_sql_receipt.py',
            'crates/hwpx-package/tests/support/document_import_memo_catalog_fixture.rs',
            'crates/hwpx-package/tests/support/document_import_settings_inputs.rs',
            'implementation/p09/source-archive/p361-field-semantics523/verifier522.py',
            'implementation/p09/evidence/p09-361-source-field-semantics522.v1.json'}|{ARCHIVE+name for name in CHANGED.values()}
        names|=includes.test_inputs((SOURCE,PRODUCT),guard)
        manifest=q.json(FORMULAS);c.require(q.snapshots[FORMULAS]['sha256']=='edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5','MEANING522_ORIGINAL_FORMULA_MANIFEST')
        formula_pins=[]
        for case in manifest['cases']:
            for kind in('input','output'):
                pin=case[kind];names.add(pin['path']);formula_pins.append(pin)
        for path in sorted(names):q.pin(path)
        retained_path='implementation/p09/evidence/p09-361-source-field-semantics522.v1.json'
        retained=layout.unpack(q.json(retained_path))
        c.require(q.snapshots[retained_path]['sha256']=='3718694d6a563dbf3a67ffd3d2ca835fee63593e3a6cf2d93167182b1dae42e1'
            and retained['cleanup']is True and retained['final_fresh_hashes']==0 and retained['steps'][0]['exit_code']==0
            and len(retained['steps'][0]['tests'])==3 and all(status=='ok'for _,status in retained['steps'][0]['tests']),
            'MEANING523_ORIGINAL_UNIT3_OBSERVED_NOT_FULL_SOURCE_CLOSURE')
        for pin in retained['source_pins']:
            actual=q.snapshots['implementation/p09/source-archive/p361-field-semantics523/verifier522.py']if pin['path']==SELF else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'MEANING523_ORIGINAL522_INPUTS_AND_PRODUCT_SOURCES_UNCHANGED')
        row.update(previous_observed_unit_cases=retained['steps'][0]['tests'],previous_unit_cases_replayed=False,
            previous_unit3_full_source_qualification=False)
        for pin in formula_pins:c.require(q.snapshots[pin['path']]['sha256']==pin['sha256']and q.snapshots[pin['path']]['bytes']==pin['bytes'],'MEANING522_ALL16_ORIGINAL_FORMULA_SOURCES_EXACT')
        c.require(len(formula_pins)==16 and q.snapshots[CAPTURE]['sha256']=='feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480','MEANING522_HISTORICAL_HTTPS_SOURCE_EXACT')
        for pin in base['source_pins']:
            if '/src/'not in pin['path']or not pin['path'].startswith('crates/'):continue
            actual=q.snapshots[ARCHIVE+CHANGED[pin['path']]]if pin['path']in CHANGED else q.snapshots[pin['path']]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'MEANING522_UNRELATED_LIBRARY_AND_ORIGINAL_CHANGED_SOURCE_PRESERVED')
        text=q.text('crates/product-cli/src/reference_validation_product/source.rs')
        r.audit.inverse(text.replace('pub(super) fn check_whole_source_field_coverage(','fn check_whole_source_field_coverage('),q.snapshots[ARCHIVE+'source.rs'],'MEANING522_ORIGINAL_V13_API_BODY_UNCHANGED')
        text=q.text('crates/product-cli/src/reference_validation_product.rs').replace('pub mod source_field_semantics;\n','')
        r.audit.inverse(text,q.snapshots[ARCHIVE+'product.rs'],'MEANING522_ORIGINAL_PRODUCT_OPS_UNCHANGED')
        text=q.text('crates/hwpx-package/src/hyperlink_hwpx.rs')
        text=text.replace('#[cfg(test)]#[path="hyperlink_hwpx/token_window_tests.rs"]mod token_window_tests;\n','')
        text=text.replace('element_tokens(document, element_index)?.iter().any(|token| {','document.tokens().iter().any(|token| {')
        start=text.index('// Immutable parser-owned start/end indexes');end=text.index('fn non_namespace_attributes',start);text=text[:start]+text[end:]
        r.audit.inverse(text,q.snapshots[ARCHIVE+'hyperlink.rs'],'MEANING522_ONLY_ORIGINAL_TOKEN_SCAN_WINDOW_CHANGED')
        original=q.text(ARCHIVE+'semantics.rs');text=q.text('crates/hwpx-package/src/document_import/fields/semantics.rs').replace('pub mod source_index;\n','')
        before=original.index('        let mut observations = Vec::new();');after=original.index('        let mut draft =',before)
        start=text.index('        let observations = read_meanings(fields)?;');end=text.index('        let mut draft =',start)
        text=text[:start]+original[before:after]+text[end:]
        start=text.index('fn read_meanings(');end=text.index('fn read_meaning(',start);text=text[:start]+text[end:]
        r.audit.inverse(text,q.snapshots[ARCHIVE+'semantics.rs'],'MEANING522_ORIGINAL_READERS_WORK_CAP_AND_GRAPH_ATTACHMENT_UNCHANGED')
        private=helpers.tests(q,PRIVATE,'hyperlink_hwpx::token_window_tests::')
        core=helpers.tests(q,SOURCE)|{'legacy_meanings::'+name for name in('source_https_tuple_is_typed_without_approval_or_label_inference',
            'malformed_supported_parameter_tuples_reject_not_opaque_success','historical_captured_https_has_actual_target_and_whole_unchanged_graph',
            'nested_supported_link_keeps_unsupported_parent_and_all_source_positions')}
        product=helpers.tests(q,PRODUCT)|{'legacy_source::'+name for name in('actual_package_targets_are_returned_but_not_a_zero_reference_pass',
            'source_field_inventory_rejects_begin_end_and_balanced_pairs_outside_the_body')}
        c.require((len(private),len(core),len(product))==(3,7,8),'MEANING522_NEW12_AND_DIRECTLY_AFFECTED6')
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.301693333880961,'MEANING522_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-source-meaning-scratch523';c.require(not scratch.exists(),'MEANING522_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='SOURCE_MEANING_PREFLIGHT',inputs=len(q.snapshots),new_cases=9,affected_cases=6,unit3_replayed=False,CPU_cap_percent=6.25)),flush=True)
        row['actual_compile_inputs']=[]
        configs=[('hwpx-package','source_field_meaning_index',core,'source_field_meaning_index'),
            ('hwpx-agent-cli','reference_field_semantics_product',product,'reference_field_semantics_product')]
        for package,target,cases,stem in configs:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package]+(['--lib']if target is None else['--test',target])
            args+=['--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(stem,args,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'MEANING522_NO_COMPILER_WARNINGS')
            found=[]
            for path in(c.ROOT/'target/debug/deps').glob(stem+'-*.d'):
                declared=dependencies(path);c.require(declared<=set(q.snapshots),'MEANING522_ALL_ACTUAL_DEPENDENCIES_PREPINNED')
                found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared),all_predeclared=True))
            c.require(len(found)==1,'MEANING523_EXACT_NEW_HOST_DEP_INFO_REQUIRED');row['actual_compile_inputs'].extend(found)
        c.require(not any(scratch.iterdir()),'MEANING522_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_FIELD_MEANING_INDEX_AND_PRODUCT15_NOT_NATIVE_OR_GATE',new_cases=9,directly_affected_cases=6,
            qualified_cases=15,real_historical_formula_sources=16,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'MEANING522_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),resource_samples=samples,
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),diagnostics=s.get('diagnostics',[]),cleanup=s['cleanup'],failed_cases=[name for name,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
